"""Train one shallow XGBoost on 2019–2023 and score the 2024 holdout.

A provider-year is fraud only when its rolled NPI matches a 10-digit LEIE
NPI whose EXCLTYPE is one of the four locked codes and whose exclusion year
is after the billing year. Training keeps every fraud row and undersamples
clean rows toward nine clean rows per fraud row. The same model is scored
on the real mix. 2024 is not used to fit. Accuracy is not a result.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from scripts.join_labels import earliest_exclusion_years, is_positive_label

REPO_ROOT = Path(__file__).resolve().parents[1]
LEIE_PATH = REPO_ROOT / "data" / "training" / "UPDATED.csv"
ROLLED_DIR = REPO_ROOT / "data" / "rolled"
MODELS_DIR = REPO_ROOT / "models"
MODEL_PATH = MODELS_DIR / "xgb_shallow.json"
NOTE_PATH = MODELS_DIR / "holdout_note.txt"
EXPANDED_MODEL_PATH = MODELS_DIR / "xgb_expanded.json"
EXPANDED_NOTE_PATH = MODELS_DIR / "xgb_expanded_note.txt"
EXPAND_COUNTS_PATH = REPO_ROOT / "data" / "training" / "expand_counts.txt"
TRAINING_FILE = REPO_ROOT / "data" / "training" / "physician_2013_2023.csv"
EXPANDED_YEARS = tuple(range(2013, 2024))

TRAIN_YEARS = (2019, 2020, 2021, 2022, 2023)
HOLDOUT_YEAR = 2024

FEATURE_COLUMNS = (
    "Service count",
    "Beneficiary count",
    "Average charge",
    "Average payment",
    "Charge-to-payment ratio",
    "Top-code share",
    "Specialty",
    "Growth",
)
NUMERIC_FEATURES = (
    "Service count",
    "Beneficiary count",
    "Average charge",
    "Average payment",
    "Charge-to-payment ratio",
    "Top-code share",
    "Growth",
)
EXCLUDED_FROM_FEATURES = ("NPI", "Name", "City", "State", "ZIP", "Year")

MAX_DEPTH = 4
SEED = 1
CLEAN_PER_FRAUD = 9

# Depth and seed are fixed. Every other booster setting stays at the
# installed XGBoost default. This is not a search.
BOOSTER = {
    "max_depth": MAX_DEPTH,
    "random_state": SEED,
}
READ_COLUMNS = ("NPI", "Year", *FEATURE_COLUMNS)


def label_from_columns(
    npis: list[str],
    years: list[str],
    exclusion_years: dict[str, int],
) -> list[int]:
    """Return 1 when the exclusion year is after that row's billing year."""
    labels: list[int] = []
    for npi, year_text in zip(npis, years):
        npi = (npi or "").strip()
        year_text = (year_text or "").strip()
        billing_year = int(year_text) if year_text.isdigit() else None
        matched = exclusion_years.get(npi)
        positive = billing_year is not None and is_positive_label(billing_year, matched)
        labels.append(1 if positive else 0)
    return labels


def label_rows(
    rows: list[dict[str, str]],
    exclusion_years: dict[str, int],
) -> list[int]:
    """Label dict rows with the same rule as label_from_columns."""
    return label_from_columns(
        [(row.get("NPI") or "") for row in rows],
        [(row.get("Year") or "") for row in rows],
        exclusion_years,
    )


def undersample_90_10(
    labels: list[int],
    clean_per_fraud: int = CLEAN_PER_FRAUD,
    seed: int = SEED,
) -> list[int]:
    """Keep every fraud index and sample clean indexes toward clean_per_fraud:1.

    When fewer clean rows exist than the target, every clean row is kept.
    The returned indexes are sorted so the sample order does not depend on
    the RNG draw order.
    """
    fraud = [index for index, label in enumerate(labels) if label == 1]
    clean = [index for index, label in enumerate(labels) if label == 0]
    target = clean_per_fraud * len(fraud)
    if target <= 0 or len(clean) <= target:
        chosen_clean = list(clean)
    else:
        rng = np.random.default_rng(seed)
        drawn = rng.choice(len(clean), size=target, replace=False)
        chosen_clean = [clean[int(position)] for position in drawn]
    return sorted(fraud + chosen_clean)


def feature_frame(frame: pd.DataFrame, categories: list[str]) -> pd.DataFrame:
    """Build the eight feature columns. Missing numbers stay missing.

    Specialty is a fixed category code: known training specialties keep
    their code, and any other text, including blank, becomes missing.
    Name, NPI, city, state, ZIP, and Year are not copied in.
    """
    out = pd.DataFrame(index=frame.index)
    for name in NUMERIC_FEATURES:
        if name in frame.columns:
            out[name] = pd.to_numeric(frame[name], errors="coerce")
        else:
            out[name] = np.nan
    known = {value: float(code) for code, value in enumerate(categories)}
    if "Specialty" in frame.columns:
        text = frame["Specialty"].fillna("").astype(str).str.strip()
    else:
        text = pd.Series("", index=frame.index)
    coded = text.map(known)
    out["Specialty"] = pd.to_numeric(coded, errors="coerce")
    return out.loc[:, list(FEATURE_COLUMNS)]


def training_categories(frame: pd.DataFrame) -> list[str]:
    """Sorted non-blank specialties seen in the training years. Fit once."""
    if "Specialty" not in frame.columns:
        return []
    values = frame["Specialty"].fillna("").astype(str).str.strip()
    return sorted({value for value in values if value != ""})


def top_slice_share(
    scores: list[float],
    labels: list[int],
    percentile: float,
) -> tuple[int, int, float]:
    """Share of fraud rows whose score is at or above a percentile cutoff.

    The cutoff is the given percentile of all scores. Ties at the cutoff
    count as inside the slice. A zero fraud count returns share 0.0 and
    does not divide by zero. percentile is 99 for the top 1% and 95 for
    the top 5%.
    """
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have the same length")
    fraud_count = sum(1 for label in labels if label == 1)
    if not scores or fraud_count == 0:
        return 0, fraud_count, 0.0
    cutoff = float(np.percentile(np.asarray(scores, dtype=float), percentile))
    captured = sum(
        1
        for score, label in zip(scores, labels)
        if label == 1 and score >= cutoff
    )
    return captured, fraud_count, captured / fraud_count


def real_mix_top_shares(
    scores: list[float],
    labels: list[int],
) -> dict[str, tuple[int, int, float]]:
    """Ranking scores on every row. Not accuracy."""
    return {
        "top_1": top_slice_share(scores, labels, 99),
        "top_5": top_slice_share(scores, labels, 95),
    }


def new_classifier() -> XGBClassifier:
    """One shallow classifier. Callers fit it once.

    The only explicit booster settings are max_depth and random_state.
    n_estimators, scale_pos_weight, and early_stopping_rounds stay unset.
    """
    return XGBClassifier(**BOOSTER)


def installed_n_estimators_default() -> int | None:
    """Return the boosting-round count the installed trainer will use.

    XGBClassifier may leave n_estimators unset and still boost
    DEFAULT_N_ESTIMATORS rounds. That count is the installed default.
    None means there is no default to write, and the caller must stop
    rather than pass n_estimators=100 into the constructor.
    """
    classifier = new_classifier()
    if "n_estimators" in BOOSTER:
        return None
    getter = getattr(classifier, "get_num_boosting_rounds", None)
    if not callable(getter):
        return None
    value = getter()
    if value is None:
        return None
    return int(value)


def predict_scores(model: XGBClassifier, features: pd.DataFrame) -> list[float]:
    """Return the positive-class probability for each row."""
    probabilities = model.predict_proba(features)
    return [float(row[1]) for row in probabilities]


def load_labeled_year(
    rolled_path: Path,
    exclusion_years: dict[str, int],
) -> pd.DataFrame:
    """Read one rolled year and attach the fraud label. Does not write the file.

    Only the label key and the eight feature columns are kept. Name, city,
    state, and ZIP are never read in.
    """
    frame = pd.read_csv(
        rolled_path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
        usecols=list(READ_COLUMNS),
    )
    labels = label_from_columns(
        frame["NPI"].tolist(),
        frame["Year"].tolist(),
        exclusion_years,
    )
    out = pd.DataFrame(
        {name: pd.to_numeric(frame[name], errors="coerce") for name in NUMERIC_FEATURES}
    )
    out["Specialty"] = frame["Specialty"].fillna("").astype(str).str.strip()
    out["label"] = labels
    return out


def load_years(
    rolled_dir: Path,
    years: tuple[int, ...],
    exclusion_years: dict[str, int],
) -> pd.DataFrame:
    frames = [
        load_labeled_year(rolled_dir / f"{year}.csv", exclusion_years)
        for year in years
    ]
    return pd.concat(frames, ignore_index=True)


def fit_once(
    features: pd.DataFrame,
    labels: list[int],
) -> XGBClassifier:
    """Fit one shallow model. The caller must not call this twice."""
    model = new_classifier()
    model.fit(features, labels)
    return model


def format_share(name: str, captured: int, fraud_count: int, share: float) -> str:
    return f"{name}: {captured}/{fraud_count} = {share:.6f}"


def write_note(
    path: Path,
    train_fraud: int,
    train_clean_kept: int,
    real_mix: dict[str, tuple[int, int, float]],
    holdout: dict[str, tuple[int, int, float]],
) -> None:
    """Write the holdout shares and the real-mix ranking score. No accuracy."""
    real_top1 = real_mix["top_1"]
    real_top5 = real_mix["top_5"]
    hold_top1 = holdout["top_1"]
    hold_top5 = holdout["top_5"]
    text = (
        "One shallow XGBoost model. max_depth 4. One fit. No second model. No tuning.\n"
        f"Training years: {', '.join(str(year) for year in TRAIN_YEARS)}.\n"
        "Training sample keeps every fraud provider-year and undersamples "
        f"clean rows toward {CLEAN_PER_FRAUD}:1.\n"
        f"Training sample fraud rows: {train_fraud}.\n"
        f"Training sample clean rows: {train_clean_kept}.\n"
        "Real-mix score is the share of 2019-2023 fraud rows in the top slice "
        "of all 2019-2023 scores. It is a ranking score, not a second model.\n"
        f"Real mix {format_share('top 1%', *real_top1)}.\n"
        f"Real mix {format_share('top 5%', *real_top5)}.\n"
        "2024 was not used to fit the model.\n"
        "Share of 2024 fraud rows in the top 1% of all 2024 scores: "
        f"{hold_top1[0]}/{hold_top1[1]} = {hold_top1[2]:.6f}.\n"
        "Share of 2024 fraud rows in the top 5% of all 2024 scores: "
        f"{hold_top5[0]}/{hold_top5[1]} = {hold_top5[2]:.6f}.\n"
        "A 2024 row is fraud only when its NPI matches a 10-digit LEIE NPI "
        "with EXCLTYPE in 1128a1, 1128a3, 1128b6, or 1128b7 and the exclusion "
        "year is after 2024.\n"
    )
    path.write_text(text, encoding="utf-8")


def train_and_write(
    leie_path: Path = LEIE_PATH,
    rolled_dir: Path = ROLLED_DIR,
    models_dir: Path = MODELS_DIR,
    train_years: tuple[int, ...] = TRAIN_YEARS,
    holdout_year: int = HOLDOUT_YEAR,
) -> tuple[Path, Path]:
    """Fit one model on the training years and write the model file and note."""
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / MODEL_PATH.name
    note_path = models_dir / NOTE_PATH.name
    exclusion_years = earliest_exclusion_years(leie_path)
    train = load_years(rolled_dir, train_years, exclusion_years)
    holdout = load_labeled_year(rolled_dir / f"{holdout_year}.csv", exclusion_years)

    labels = [int(value) for value in train["label"].tolist()]
    sample_indexes = undersample_90_10(labels)
    categories = training_categories(train)
    train_features = feature_frame(train, categories)
    sampled_features = train_features.iloc[sample_indexes]
    sampled_labels = [labels[index] for index in sample_indexes]

    model = fit_once(sampled_features, sampled_labels)
    model.get_booster().set_attr(specialty_categories=json.dumps(categories))
    model.save_model(model_path)

    real_scores = predict_scores(model, train_features)
    holdout_features = feature_frame(holdout, categories)
    holdout_scores = predict_scores(model, holdout_features)
    holdout_labels = [int(value) for value in holdout["label"].tolist()]

    train_fraud = sum(sampled_labels)
    train_clean = len(sampled_labels) - train_fraud
    write_note(
        note_path,
        train_fraud=train_fraud,
        train_clean_kept=train_clean,
        real_mix=real_mix_top_shares(real_scores, labels),
        holdout=real_mix_top_shares(holdout_scores, holdout_labels),
    )
    return model_path, note_path


def load_training_file(training_path: Path) -> pd.DataFrame:
    """Read the joined training file. Does not read a 2024 roll."""
    frame = pd.read_csv(
        training_path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
    )
    if "Year" in frame.columns and (frame["Year"] == "2024").any():
        raise ValueError("training file contains a 2024 row")
    numeric = pd.DataFrame(
        {name: pd.to_numeric(frame[name], errors="coerce") for name in NUMERIC_FEATURES}
    )
    numeric["Specialty"] = frame["Specialty"].fillna("").astype(str).str.strip()
    numeric["label"] = pd.to_numeric(frame["label"], errors="coerce").fillna(0).astype(int)
    numeric["NPI"] = frame["NPI"].astype(str)
    numeric["Year"] = frame["Year"].astype(str)
    return numeric


def fit_expanded(
    training_path: Path = TRAINING_FILE,
    model_path: Path = EXPANDED_MODEL_PATH,
    counts_path: Path = EXPAND_COUNTS_PATH,
) -> Path:
    """Fit one expanded model. Does not write xgb_shallow.json or holdout_note.txt.

    Writes the installed n_estimators default before the fit. Stops without
    fitting when that default is missing. Calls fit once.
    """
    default_trees = installed_n_estimators_default()
    counts_path.parent.mkdir(parents=True, exist_ok=True)
    if default_trees is None:
        with counts_path.open("a", encoding="utf-8") as handle:
            handle.write(
                "stop: installed trainer has no n_estimators default; "
                "forcing 100 would add a key the current trainer does not set\n"
            )
        raise SystemExit("no installed n_estimators default; fit not started")
    with counts_path.open("a", encoding="utf-8") as handle:
        handle.write(f"installed_n_estimators_default: {default_trees}\n")

    train = load_training_file(training_path)
    labels = [int(value) for value in train["label"].tolist()]
    sample_indexes = undersample_90_10(labels)
    categories = training_categories(train)
    with counts_path.open("a", encoding="utf-8") as handle:
        handle.write(f"specialty_category_count: {len(categories)}\n")
    features = feature_frame(train, categories)
    sampled_features = features.iloc[sample_indexes]
    sampled_labels = [labels[index] for index in sample_indexes]
    fraud_used = sum(sampled_labels)
    clean_used = len(sampled_labels) - fraud_used
    with counts_path.open("a", encoding="utf-8") as handle:
        handle.write(f"fit_fraud_rows: {fraud_used}\n")
        handle.write(f"fit_clean_rows: {clean_used}\n")

    model = fit_once(sampled_features, sampled_labels)
    model.get_booster().set_attr(specialty_categories=json.dumps(categories))
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(model_path)
    return model_path


def score_expanded(
    model_path: Path = EXPANDED_MODEL_PATH,
    training_path: Path = TRAINING_FILE,
    rolled_dir: Path = ROLLED_DIR,
    leie_path: Path = LEIE_PATH,
    counts_path: Path = EXPAND_COUNTS_PATH,
    note_path: Path = EXPANDED_NOTE_PATH,
    holdout_year: int = HOLDOUT_YEAR,
) -> dict[str, object]:
    """Score the 2024 roll only. Does not fit. Does not write the baseline.

    Categories come from the training frame. Demo NPIs are scored against
    the prior percentiles and recorded as a hit or a miss.
    """
    from xgboost import XGBClassifier as _Loader

    train = load_training_file(training_path)
    categories = training_categories(train)
    exclusion_years = earliest_exclusion_years(leie_path)
    holdout = load_labeled_year(rolled_dir / f"{holdout_year}.csv", exclusion_years)
    model = _Loader()
    model.load_model(model_path)
    scores = predict_scores(model, feature_frame(holdout, categories))
    labels = [int(value) for value in holdout["label"].tolist()]
    shares = real_mix_top_shares(scores, labels)
    top1 = shares["top_1"]
    top5 = shares["top_5"]

    from app.page_logic import percentile_result

    npi_list = pd.read_csv(
        rolled_dir / f"{holdout_year}.csv",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
        usecols=["NPI"],
    )["NPI"].tolist()
    demo_lines = []
    prior = {"1124725817": 99.988902, "1639879034": 99.945258}
    for npi, prior_pct in prior.items():
        matches = [score for score, row_npi in zip(scores, npi_list) if row_npi.strip() == npi]
        if not matches:
            demo_lines.append(f"{npi}: miss (absent from {holdout_year} scores; prior percentile {prior_pct})")
            continue
        rank = percentile_result(matches[0], scores)
        percentile = rank["percentile"]
        # A hit is a new percentile at or above the prior percentile.
        # A lower percentile is a miss and is written as a miss.
        status = "hit" if percentile is not None and percentile >= prior_pct else "miss"
        demo_lines.append(
            f"{npi}: {status} percentile {percentile:.6f} prior {prior_pct}"
        )

    count_line = (
        f"2024 top 1% numerator: {top1[0]}/48 beside 11/48\n"
        f"2024 top 5% numerator: {top5[0]}/48 beside 18/48\n"
    )
    with counts_path.open("a", encoding="utf-8") as handle:
        handle.write(count_line)
        for line in demo_lines:
            handle.write(line + "\n")
    note_path.write_text(
        (
            "Expanded model 2024 score. 2024 was not used to fit.\n"
            f"2024 top 1% numerator: {top1[0]}/48 beside 11/48.\n"
            f"2024 top 5% numerator: {top5[0]}/48 beside 18/48.\n"
            + "\n".join(demo_lines)
            + "\n"
        ),
        encoding="utf-8",
    )
    return {
        "top1": top1[0],
        "top5": top5[0],
        "demo": demo_lines,
    }


def main() -> None:
    """Refuse the shallow writer. The expanded fit is an explicit function call."""
    raise SystemExit(
        "The default path writes models/xgb_shallow.json and refuses to run. "
        "Use fit_expanded to write models/xgb_expanded.json."
    )


if __name__ == "__main__":
    main()

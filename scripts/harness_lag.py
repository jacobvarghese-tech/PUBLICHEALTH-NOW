"""Fit one IsolationForest per specialty on ordinary rows from earlier years.

A row is positive only when scripts.train.label_from_columns says so: the
NPI matches a 10-digit NPI on data/training/UPDATED.csv, EXCLTYPE is one of
the four fraud codes, and the exclusion year is after the billing year.
Same-year and earlier exclusions stay ordinary. Demo NPIs are dropped from
every fit and are not labels.

Each forest uses the opened-page default n_estimators, contamination='auto',
random_state=1, and n_jobs=2. The grade ranks decision_function within
specialty. A lower score is more abnormal. predict is not used to grade.
"""

from __future__ import annotations

import csv
import gc
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from scripts.count_leie import FRAUD_EXCLTYPES
from scripts.join_labels import earliest_exclusion_years, exclusion_year, is_ten_digit_npi
from scripts.train import label_from_columns, top_slice_share

REPO_ROOT = Path(__file__).resolve().parents[1]
LEIE_PATH = REPO_ROOT / "data" / "training" / "UPDATED.csv"
ROLLED_DIR = REPO_ROOT / "data" / "rolled"
MODELS_DIR = REPO_ROOT / "models"
MODEL_PATH = MODELS_DIR / "harness_lag.joblib"
NOTE_PATH = MODELS_DIR / "harness_lag_note.txt"
COUNTS_PATH = MODELS_DIR / "harness_lag_counts.txt"

# Opened https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html
# on 2026-10-22. Signature default: n_estimators=100. The open wins.
PAGE_URL = (
    "https://scikit-learn.org/stable/modules/generated/"
    "sklearn.ensemble.IsolationForest.html"
)
N_ESTIMATORS = 100
CONTAMINATION = "auto"
RANDOM_STATE = 1
N_JOBS = 2
SAMPLE_CAP = 5000
MIN_ORDINARY = 256
DEMO_NPIS = frozenset({"1124725817", "1639879034"})
FEATURE_COLUMNS = (
    "Service count",
    "Beneficiary count",
    "Average charge",
    "Average payment",
    "Charge-to-payment ratio",
    "Top-code share",
    "Growth",
)
READ_COLUMNS = ("NPI", "Year", "Specialty", *FEATURE_COLUMNS)
COUNT_YEARS = (2019, 2020, 2021, 2022, 2023, 2024)
GRADE_YEARS = (2021, 2022, 2023)
SAVED_FIT_BEFORE = 2024
FIRST_BILLING_YEAR = 2013
CODE_ORDER = ("1128a1", "1128a3", "1128b6", "1128b7")
# Prose totals to check before the first fit. A disagreement stops the run.
PROSE_TOTALS = {2023: 93, 2024: 48}
PROSE_BY_CODE = {
    2019: (333, 69, 2, 29),
    2020: (260, 48, 2, 25),
    2021: (195, 33, 2, 21),
    2022: (122, 23, 1, 12),
    2023: (73, 13, 1, 6),
}
CAVEAT_2024 = (
    "2024 has 48 fraud rows under the four-code later-year join, below the "
    "external-validation floor of at least 100 events, ideally 200 or more, "
    "so a 2024 share is not a precise estimate."
)
SAVED_2024_FIGURES = ("11/48", "18/48", "19/48", "48/48")
BLANK_SPECIALTY = ""

# Installed sklearn 1.8 IsolationForest.fit accepts NaN. Missing Growth stays
# missing on that path. If a forest rejects NaN, drop those rows and record
# the drop. Nothing is imputed, and Growth is never filled with 0.
FOREST_ACCEPTS_NAN = True


def forest_kwargs() -> dict:
    """Constructor arguments locked to the opened page and this job."""
    return {
        "n_estimators": N_ESTIMATORS,
        "contamination": CONTAMINATION,
        "random_state": RANDOM_STATE,
        "n_jobs": N_JOBS,
    }


def new_forest() -> IsolationForest:
    return IsolationForest(**forest_kwargs())


def fit_window(grade_year: int) -> tuple[int, ...]:
    """Billing years strictly before the grade year. Never includes the grade year."""
    if grade_year <= FIRST_BILLING_YEAR:
        return ()
    return tuple(range(FIRST_BILLING_YEAR, grade_year))


def assert_fit_window(years: tuple[int, ...], grade_year: int) -> None:
    """Refuse a window that includes the grade year or 2024."""
    if grade_year in years or SAVED_FIT_BEFORE in years:
        raise ValueError(
            f"fit window {years} includes the grade year or {SAVED_FIT_BEFORE}"
        )
    if any(year >= grade_year for year in years):
        raise ValueError(f"fit window {years} is not strictly before {grade_year}")


def drop_demo_npis(
    frame: pd.DataFrame,
    demo_npis: frozenset[str] = DEMO_NPIS,
) -> pd.DataFrame:
    """Remove demo NPIs from a fit frame. They are not labels."""
    if frame.empty or "NPI" not in frame.columns:
        return frame.copy()
    keep = ~frame["NPI"].astype(str).str.strip().isin(demo_npis)
    return frame.loc[keep].copy()


def rows_with_nan(features: pd.DataFrame) -> pd.Series:
    """True where any numeric feature is missing. Does not fill the gap."""
    return features.isna().any(axis=1)


def drop_nan_rows(features: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop rows a forest would reject. Nothing is imputed."""
    mask = rows_with_nan(features)
    dropped = int(mask.sum())
    if dropped == 0:
        return features, 0
    return features.loc[~mask].copy(), dropped


def sample_ordinary(
    ordinary_index: np.ndarray,
    cap: int = SAMPLE_CAP,
    seed: int = RANDOM_STATE,
) -> np.ndarray:
    """Draw at most cap ordinary row positions with a fixed seed.

    The cap is a machine lock. It is not a paper finding. The draw is
    without replacement.
    """
    positions = np.asarray(ordinary_index)
    if len(positions) <= cap:
        return positions.copy()
    rng = np.random.default_rng(seed)
    drawn = rng.choice(len(positions), size=cap, replace=False)
    return positions[np.sort(drawn)]


def specialty_key(value: object) -> str:
    """Blank specialty is its own group. Specialty is not a tree column."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return BLANK_SPECIALTY
    text = str(value).strip()
    if text.lower() == "nan":
        return BLANK_SPECIALTY
    return text


def numeric_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Seven numeric columns. Missing numbers stay missing. Growth is not filled."""
    out = pd.DataFrame(index=frame.index)
    for name in FEATURE_COLUMNS:
        if name in frame.columns:
            out[name] = pd.to_numeric(frame[name], errors="coerce")
        else:
            out[name] = np.nan
    return out.loc[:, list(FEATURE_COLUMNS)]


def prepare_fit_matrix(
    frame: pd.DataFrame,
    accepts_nan: bool = FOREST_ACCEPTS_NAN,
) -> tuple[pd.DataFrame, int]:
    """Numeric matrix for one specialty sample. Drops NaN only when required."""
    features = numeric_features(frame)
    if accepts_nan:
        return features, 0
    return drop_nan_rows(features)


def forests_to_fit(
    ordinary_counts: dict[str, int],
    minimum: int = MIN_ORDINARY,
) -> tuple[list[str], list[str]]:
    """Split specialties into fitted and skipped. Under 256 ordinary rows is skipped."""
    fitted = sorted(
        name for name, count in ordinary_counts.items() if count >= minimum
    )
    skipped = sorted(
        name for name, count in ordinary_counts.items() if count < minimum
    )
    return fitted, skipped


def abnormality_from_decision(scores: np.ndarray) -> np.ndarray:
    """Negate decision_function so a higher number is the flagged end.

    IsolationForest decision_function: the lower, the more abnormal.
    scripts.train.top_slice_share treats a higher number as the flagged end.
    Raw decision_function must not be passed into that helper.
    """
    return -np.asarray(scores, dtype=float)


def within_specialty_slice(
    scores: list[float] | np.ndarray,
    labels: list[int] | np.ndarray,
    percentile: float,
) -> tuple[int, int]:
    """Fraud rows at or above the abnormality percentile. Ties stay inside.

    scores are already abnormality ranks (higher = more abnormal) for one
    specialty. percentile is 99 for the most abnormal 1 percent and 95 for
    the most abnormal 5 percent.
    """
    score_list = [float(value) for value in np.asarray(scores, dtype=float)]
    label_list = [int(value) for value in np.asarray(labels, dtype=int)]
    # Higher score is the flagged end. Callers pass negated decision_function.
    captured, fraud_count, _share = top_slice_share(score_list, label_list, percentile)
    return captured, fraud_count


def year_capture(
    specialty_scores: list[np.ndarray],
    specialty_labels: list[np.ndarray],
) -> dict[str, int]:
    """Add within-specialty 1 percent and 5 percent captures.

    Scores from different specialties are not pooled. A fraud row counts
    only when it was scored. Callers attach the distinct-score count and
    the short-list flag from the raw decision_function values.
    """
    captured_1 = 0
    captured_5 = 0
    fraud_denominator = 0
    for scores, labels in zip(specialty_scores, specialty_labels):
        if len(scores) == 0:
            continue
        abnormality = abnormality_from_decision(scores)
        top_1, fraud_here = within_specialty_slice(abnormality, labels, 99)
        top_5, _ = within_specialty_slice(abnormality, labels, 95)
        captured_1 += top_1
        captured_5 += top_5
        fraud_denominator += fraud_here
    return {
        "fraud_top_1": captured_1,
        "fraud_top_5": captured_5,
        "fraud_denominator": fraud_denominator,
    }


def top_1_list_is_short(score_values: np.ndarray) -> bool:
    """True when the top 1 percent list is short.

    The list is not short when one score value covers half or more of that
    year's scored rows. That case returns False, and the note prints no.
    A diverse year, where no single score covers half, returns True and
    prints yes. An empty score list is not short.
    """
    values = np.asarray(score_values, dtype=float)
    if len(values) == 0:
        return False
    _, counts = np.unique(values, return_counts=True)
    return int(counts.max()) < (len(values) / 2)


def distinct_score_count(score_values: np.ndarray) -> int:
    values = np.asarray(score_values, dtype=float)
    if len(values) == 0:
        return 0
    return int(len(np.unique(values)))


def label_year_frame(
    frame: pd.DataFrame,
    exclusion_years: dict[str, int],
) -> pd.DataFrame:
    """Attach the later-year label. Does not mark a same-year exclusion positive."""
    labels = label_from_columns(
        frame["NPI"].astype(str).tolist(),
        frame["Year"].astype(str).tolist(),
        exclusion_years,
    )
    out = frame.copy()
    out["label"] = labels
    out["Specialty"] = out["Specialty"].map(specialty_key)
    return out


def load_year(path: Path, exclusion_years: dict[str, int]) -> pd.DataFrame:
    """Read one rolled year. Name, city, state, and ZIP are not read in."""
    frame = pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
        usecols=list(READ_COLUMNS),
    )
    return label_year_frame(frame, exclusion_years)


def earliest_exclusion_types(leie_path: Path) -> dict[str, str]:
    """EXCLTYPE of each NPI's earliest qualifying exclusion.

    Same drop rules as earliest_exclusion_years. The recount uses this only
    to split an already-positive row by code.
    """
    chosen: dict[str, tuple[str, int]] = {}
    with leie_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            excltype = (row.get("EXCLTYPE") or "").strip()
            if excltype not in FRAUD_EXCLTYPES:
                continue
            npi = (row.get("NPI") or "").strip()
            if not is_ten_digit_npi(npi):
                continue
            year = exclusion_year((row.get("EXCLDATE") or "").strip())
            if year is None:
                continue
            previous = chosen.get(npi)
            if previous is None or year < previous[1]:
                chosen[npi] = (excltype, year)
    return {npi: pair[0] for npi, pair in chosen.items()}


def recount_year(
    path: Path,
    exclusion_years: dict[str, int],
    type_by_npi: dict[str, str],
) -> dict[str, int]:
    """Count positive rows and the four codes for one billing year.

    A positive row uses label_from_columns. The code is the EXCLTYPE of
    that NPI's earliest qualifying exclusion.
    """
    frame = pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
        usecols=["NPI", "Year"],
    )
    labels = label_from_columns(
        frame["NPI"].tolist(),
        frame["Year"].tolist(),
        exclusion_years,
    )
    counts = {code: 0 for code in CODE_ORDER}
    total = 0
    for npi, label in zip(frame["NPI"].tolist(), labels):
        if label != 1:
            continue
        total += 1
        code = type_by_npi.get((npi or "").strip())
        if code in counts:
            counts[code] += 1
    counts["total"] = total
    return counts


def format_counts(year_counts: dict[int, dict[str, int]]) -> str:
    lines = [
        "Fraud provider-years under the four-code later-year join.",
        "A same-year exclusion is ordinary.",
    ]
    for year in COUNT_YEARS:
        counts = year_counts[year]
        by_code = ", ".join(f"{code}={counts[code]}" for code in CODE_ORDER)
        lines.append(f"{year} total={counts['total']} {by_code}")
    return "\n".join(lines) + "\n"


def prose_disagreements(year_counts: dict[int, dict[str, int]]) -> list[str]:
    """Both the recounted number and the prose number, when they differ."""
    found: list[str] = []
    for year, expected in PROSE_TOTALS.items():
        got = year_counts[year]["total"]
        if got != expected:
            found.append(f"{year} total recounted={got} prose={expected}")
    for year, expected_codes in PROSE_BY_CODE.items():
        got_codes = tuple(year_counts[year][code] for code in CODE_ORDER)
        if got_codes != expected_codes:
            found.append(
                f"{year} by code recounted={got_codes} prose={expected_codes}"
            )
    return found


def ordinary_fit_rows(
    frame: pd.DataFrame,
    demo_npis: frozenset[str] = DEMO_NPIS,
    accepts_nan: bool = FOREST_ACCEPTS_NAN,
) -> tuple[pd.DataFrame, int]:
    """Ordinary rows eligible for a fit. Demo NPIs are gone. NaN drops are counted.

    Positive rows stay out. A same-year exclusion is already ordinary because
    label_from_columns marked it 0.
    """
    kept = drop_demo_npis(frame, demo_npis)
    ordinary = kept.loc[kept["label"] == 0].copy()
    features = numeric_features(ordinary)
    if accepts_nan:
        ordinary = ordinary.copy()
        for name in FEATURE_COLUMNS:
            ordinary[name] = features[name].to_numpy()
        return ordinary, 0
    mask = rows_with_nan(features)
    dropped = int(mask.sum())
    ordinary = ordinary.loc[~mask].copy()
    for name in FEATURE_COLUMNS:
        ordinary[name] = features.loc[~mask, name].to_numpy()
    return ordinary, dropped


class SpecialtyReservoir:
    """One numeric array per specialty. Seed 1. One year, then drop it.

    Algorithm R copies each row while the stream index is still under the
    cap. After the reservoir is full, a row is written to kept[j] only when
    j = floor(U * (index + 1)) is inside the cap. A draw outside the cap
    stays out and is not appended. The year frame is not stored.
    """

    def __init__(self, cap: int = SAMPLE_CAP, seed: int = RANDOM_STATE) -> None:
        self.cap = cap
        self.seed = seed
        self.values: np.ndarray | None = None
        self.columns: list[str] = list(FEATURE_COLUMNS)
        self.seen = 0
        self._rng = np.random.default_rng(seed)

    @property
    def rows(self) -> pd.DataFrame | None:
        if self.values is None:
            return None
        return pd.DataFrame(self.values, columns=self.columns)

    def add(self, frame: pd.DataFrame) -> None:
        if frame.empty:
            return
        incoming = np.array(frame.to_numpy(dtype=float, copy=False), dtype=float, copy=True)
        del frame
        self.values = self._reservoir_of(incoming, start=self.seen)
        self.seen += len(incoming)

    def _reservoir_of(self, incoming: np.ndarray, start: int) -> np.ndarray:
        """Algorithm R. Copy until full, then replace kept[j].

        A draw is taken for every incoming row, including the fill prefix,
        so later rows see the later draws. Fill rows are copied in order.
        Replacement starts only once the stream index reaches the cap.
        A draw past the cap stays out and is not appended.
        """
        count = len(incoming)
        width = incoming.shape[1]
        draws = self._rng.random(count)
        n_fill = int(max(0, min(count, self.cap - start)))
        current = self.values
        if current is None:
            current = np.empty((0, width), dtype=float)
        if n_fill:
            kept = np.empty((len(current) + n_fill, width), dtype=float)
            if len(current):
                kept[: len(current)] = current
            kept[len(current) :] = incoming[:n_fill]
        else:
            kept = np.array(current, dtype=float, copy=True)
        if n_fill < count and len(kept):
            rest = incoming[n_fill:]
            indexes = start + n_fill + np.arange(len(rest), dtype=np.int64)
            slots = np.floor(draws[n_fill:] * (indexes + 1)).astype(np.int64)
            hit = slots < len(kept)
            if hit.any():
                kept[slots[hit]] = rest[hit]
        return kept


def accumulate_samples(
    store: dict[str, SpecialtyReservoir],
    year_frame: pd.DataFrame,
    cap: int = SAMPLE_CAP,
    seed: int = RANDOM_STATE,
) -> None:
    """Add one year's ordinary rows. Each specialty keeps at most cap rows."""
    feature_frame = year_frame.loc[:, list(FEATURE_COLUMNS)]
    for specialty, index in year_frame.groupby("Specialty", sort=False).groups.items():
        name = specialty_key(specialty)
        reservoir = store.get(name)
        if reservoir is None:
            reservoir = SpecialtyReservoir(cap, seed)
            store[name] = reservoir
        reservoir.add(feature_frame.loc[index])


def samples_from_store(
    store: dict[str, SpecialtyReservoir],
) -> tuple[dict[str, pd.DataFrame], dict[str, int]]:
    samples: dict[str, pd.DataFrame] = {}
    seen: dict[str, int] = {}
    for name, reservoir in store.items():
        seen[name] = reservoir.seen
        if reservoir.rows is None or reservoir.rows.empty:
            continue
        samples[name] = reservoir.rows.reset_index(drop=True)
    return samples, seen


def collect_ordinary_samples(
    years: tuple[int, ...],
    exclusion_years: dict[str, int],
    rolled_dir: Path = ROLLED_DIR,
    cap: int = SAMPLE_CAP,
    seed: int = RANDOM_STATE,
    accepts_nan: bool = FOREST_ACCEPTS_NAN,
    demo_npis: frozenset[str] = DEMO_NPIS,
) -> tuple[dict[str, pd.DataFrame], dict[str, int], dict[str, int], list[str], dict[str, int]]:
    """Load one year at a time and keep at most cap ordinary rows per specialty.

    Returns samples, sample counts, NaN drop counts, skipped specialty names,
    and the full ordinary counts before the cap.
    """
    if years:
        assert_fit_window(years, max(years) + 1)
    store: dict[str, SpecialtyReservoir] = {}
    nan_dropped = 0
    for year in years:
        frame = load_year(rolled_dir / f"{year}.csv", exclusion_years)
        ordinary, dropped = ordinary_fit_rows(frame, demo_npis, accepts_nan)
        del frame
        nan_dropped += dropped
        accumulate_samples(store, ordinary, cap, seed)
        del ordinary
        gc.collect()
        print(f"sampled year={year} specialties={len(store)}", flush=True)
    samples, seen = samples_from_store(store)
    sample_counts = {name: len(frame) for name, frame in samples.items()}
    _, skipped = forests_to_fit(seen)
    return samples, sample_counts, {"__total__": nan_dropped}, skipped, seen


def fit_specialty_forests(
    samples: dict[str, pd.DataFrame],
    ordinary_seen: dict[str, int],
    minimum: int = MIN_ORDINARY,
) -> tuple[dict[str, IsolationForest], list[str]]:
    """Fit one forest per specialty with at least minimum ordinary rows.

    A specialty under the minimum is named and skipped even if a sample
    exists. The fit uses the sample, which is at most 5000 rows.
    """
    fitted_names, skipped = forests_to_fit(ordinary_seen, minimum)
    forests: dict[str, IsolationForest] = {}
    for name in fitted_names:
        frame = samples.get(name)
        if frame is None or frame.empty:
            if name not in skipped:
                skipped.append(name)
            continue
        model = new_forest()
        matrix, _ = prepare_fit_matrix(frame, accepts_nan=True)
        model.fit(matrix.to_numpy(dtype=float))
        forests[name] = model
    return forests, sorted(set(skipped))


def score_year(
    frame: pd.DataFrame,
    forests: dict[str, IsolationForest],
) -> dict[str, int | bool]:
    """Score one year within specialty. Unscored fraud rows stay out of the share.

    A specialty with no forest is unscored. predict is not called.
    """
    specialty_scores: list[np.ndarray] = []
    specialty_labels: list[np.ndarray] = []
    all_scores: list[np.ndarray] = []
    fraud_total = int((frame["label"] == 1).sum())
    scored_fraud = 0
    for specialty, group in frame.groupby("Specialty", sort=False):
        name = specialty_key(specialty)
        model = forests.get(name)
        if model is None:
            continue
        features = numeric_features(group)
        scores = np.asarray(
            model.decision_function(features.to_numpy(dtype=float)),
            dtype=float,
        )
        labels = group["label"].to_numpy(dtype=int)
        specialty_scores.append(scores)
        specialty_labels.append(labels)
        all_scores.append(scores)
        scored_fraud += int((labels == 1).sum())
    summary = year_capture(specialty_scores, specialty_labels)
    combined = np.concatenate(all_scores) if all_scores else np.asarray([], dtype=float)
    summary["unscored_fraud_rows"] = fraud_total - scored_fraud
    summary["fraud_rows"] = fraud_total
    summary["distinct_score_count"] = distinct_score_count(combined)
    summary["top_1_list_short"] = top_1_list_is_short(combined)
    summary["scored_rows"] = int(len(combined))
    return summary


def format_grade(year: int, summary: dict[str, int | bool]) -> str:
    short = "yes" if summary["top_1_list_short"] else "no"
    return (
        f"grade {year}: fraud_top_1={summary['fraud_top_1']} "
        f"fraud_top_5={summary['fraud_top_5']} "
        f"fraud_denominator={summary['fraud_denominator']} "
        f"unscored_fraud_rows={summary['unscored_fraud_rows']} "
        f"distinct_score_count={summary['distinct_score_count']} "
        f"top_1_list_short={short}"
    )


def format_note(
    grades: list[str],
    skipped: list[str],
    sample_counts: dict[str, int],
    nan_dropped: int,
    holdout_line: str,
    disagreements: list[str] | None = None,
) -> str:
    """Grades first. The 48-event sentence is printed before any 2024 share."""
    lines = [
        "Plan C label-lag IsolationForest. One configuration. No contamination search.",
        f"Opened page: {PAGE_URL}",
        f"n_estimators={N_ESTIMATORS} is the opened-page default.",
        "contamination='auto'. random_state=1. n_jobs=2.",
        "predict is a +1/-1 label and is not used to grade.",
        "decision_function: the lower, the more abnormal. Scores are negated before the slice.",
        (
            "A more abnormal rank means the billing profile is unusual for that "
            "specialty and resembles providers later excluded for a fraud-type reason."
        ),
        "The 5000-row cap is a machine lock. It is not a paper finding.",
        "The 2021, 2022, and 2023 grade fits are not the saved file.",
        "The saved file is a separate fit on ordinary rows from years strictly before 2024.",
    ]
    if disagreements:
        lines.append("stop: recounted fraud counts disagree with the prose.")
        lines.extend(disagreements)
    if skipped:
        shown = ", ".join(name if name else "(blank)" for name in skipped)
        lines.append(f"skipped specialties under {MIN_ORDINARY} ordinary rows: {shown}")
    else:
        lines.append(f"skipped specialties under {MIN_ORDINARY} ordinary rows: none")
    lines.append(f"nan_rows_dropped_from_fit={nan_dropped}")
    lines.append("sample_counts:")
    for name in sorted(sample_counts):
        label = name if name else "(blank)"
        lines.append(f"  {label}={sample_counts[name]}")
    lines.extend(grades)
    lines.append(CAVEAT_2024)
    lines.append(holdout_line)
    return "\n".join(lines) + "\n"


def format_holdout(summary: dict[str, int | bool]) -> str:
    """2024 capture beside the saved figures. Does not edit other notes."""
    top_1 = summary["fraud_top_1"]
    top_5 = summary["fraud_top_5"]
    denom = summary["fraud_denominator"]
    figures = ", ".join(SAVED_2024_FIGURES)
    return (
        f"2024 top 1 percent capture={top_1}/{denom} "
        f"2024 top 5 percent capture={top_5}/{denom} "
        f"beside saved figures {figures}"
    )


def saved_payload(
    forests: dict[str, IsolationForest],
    sample_counts: dict[str, int],
) -> dict:
    """Specialty name to forest, plus the feature list, sample counts, and seed."""
    return {
        "forests": forests,
        "features": list(FEATURE_COLUMNS),
        "sample_counts": sample_counts,
        "random_state": RANDOM_STATE,
    }


def run(
    rolled_dir: Path = ROLLED_DIR,
    leie_path: Path = LEIE_PATH,
    model_path: Path = MODEL_PATH,
    note_path: Path = NOTE_PATH,
    counts_path: Path = COUNTS_PATH,
) -> None:
    """Recount, grade 2021-2023, save the pre-2024 fit, then score 2024 once."""
    exclusion_years = earliest_exclusion_years(leie_path)
    type_by_npi = earliest_exclusion_types(leie_path)
    year_counts: dict[int, dict[str, int]] = {}
    for year in COUNT_YEARS:
        year_counts[year] = recount_year(
            rolled_dir / f"{year}.csv",
            exclusion_years,
            type_by_npi,
        )
        print(f"recount {year} total={year_counts[year]['total']}", flush=True)
    counts_path.parent.mkdir(parents=True, exist_ok=True)
    counts_path.write_text(format_counts(year_counts), encoding="utf-8")
    disagreements = prose_disagreements(year_counts)
    if disagreements:
        note_path.write_text(
            format_note([], [], {}, 0, "2024 was not scored.", disagreements),
            encoding="utf-8",
        )
        raise SystemExit("recount disagreed with the prose; fit not started")

    grade_lines: list[str] = []
    for grade_year in GRADE_YEARS:
        window = fit_window(grade_year)
        assert_fit_window(window, grade_year)
        samples, _, _, skipped, seen = collect_ordinary_samples(
            window,
            exclusion_years,
            rolled_dir,
        )
        forests, skipped = fit_specialty_forests(samples, seen)
        print(
            f"fit grade={grade_year} forests={len(forests)} skipped={len(skipped)}",
            flush=True,
        )
        year_frame = load_year(rolled_dir / f"{grade_year}.csv", exclusion_years)
        summary = score_year(year_frame, forests)
        grade_lines.append(format_grade(grade_year, summary))
        print(grade_lines[-1], flush=True)
        del year_frame
        del forests
        del samples
        gc.collect()

    save_window = fit_window(SAVED_FIT_BEFORE)
    assert_fit_window(save_window, SAVED_FIT_BEFORE)
    samples, sample_counts, nan_dropped, skipped, seen = collect_ordinary_samples(
        save_window,
        exclusion_years,
        rolled_dir,
    )
    forests, skipped = fit_specialty_forests(samples, seen)
    payload = saved_payload(forests, {name: sample_counts[name] for name in forests})
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(payload, model_path)
    print(f"saved forests={len(forests)}", flush=True)

    holdout = load_year(rolled_dir / f"{SAVED_FIT_BEFORE}.csv", exclusion_years)
    holdout_summary = score_year(holdout, forests)
    holdout_line = format_holdout(holdout_summary)
    note = format_note(
        grade_lines,
        skipped,
        payload["sample_counts"],
        int(nan_dropped.get("__total__", 0)),
        holdout_line,
    )
    caveat_at = note.find(CAVEAT_2024)
    share_at = note.find("2024 top 1 percent")
    if caveat_at < 0 or share_at < 0 or caveat_at > share_at:
        raise RuntimeError("48-event caveat must be printed before any 2024 share")
    note_path.write_text(note, encoding="utf-8")
    print(CAVEAT_2024, flush=True)
    print(holdout_line, flush=True)


if __name__ == "__main__":
    run()

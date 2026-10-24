"""Fit a second forest on a 9:1 undersample of the app labels.

Training years are 2013 through 2023. Every fraud row is kept. Clean rows
are drawn once with clean.sample(n=keep_clean, replace=False, random_state=0).
2024 is scored and is not fit. Labels use the app's four codes, not the
paper's Table 2 codes.

Does not edit scripts/paper_forest.py, scripts/paper_fit.py, or scripts/train.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from paper_forest import (  # noqa: E402
    LEIE_PATH,
    PAPER_FEATURES,
    SCORE_YEARS,
    TRAIN_YEARS,
    app_label,
    design_matrix,
    earliest_exclusion_years,
    label_for_row,
    load_year,
    score_year,
    training_columns,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ROLLED_DIR = REPO_ROOT / "data" / "paper_rolled"
PARTS_DIR = REPO_ROOT / "data" / "paper_rus_parts"
MODEL_PATH = REPO_ROOT / "models" / "paper_forest_rus.joblib"
COUNTS_PATH = REPO_ROOT / "models" / "paper_forest_rus_counts.txt"
SHARE_PATH = REPO_ROOT / "models" / "paper_forest_rus_shares.json"
SCORE_DIR = REPO_ROOT / "data" / "paper_scores_rus"

CLEAN_PER_FRAUD = 9
N_ESTIMATORS = 100
RANDOM_STATE = 0
HOLDOUT_YEAR = 2024
FEATURE_USECOLS = ["provider_type", "nppes_provider_gender", *PAPER_FEATURES]

COUNTS_NOTE = (
    "The app's four codes (1128a1, 1128a3, 1128b6, 1128b7) were used. "
    "The paper's Table 2 codes were not used."
)


def forest_kwargs(n_estimators: int = 100) -> dict:
    """Constructor settings. No max_features and no class_weight."""
    return {
        "n_estimators": n_estimators,
        "random_state": RANDOM_STATE,
        "n_jobs": -1,
    }


def new_forest(n_estimators: int = 100) -> RandomForestClassifier:
    return RandomForestClassifier(**forest_kwargs(n_estimators))


def undersample(frame: pd.DataFrame, clean_per_fraud: int = 9, random_state: int = 0):
    """Keep every fraud row. Draw clean rows without replacement.

    The paper repeats this draw. Each repeat uses a different random_state
    so a different majority-class set is removed. The default seed is 0,
    the same stand-in the first undersampled forest used.
    """
    fraud = frame.loc[frame["fraud"] == 1]
    clean = frame.loc[frame["fraud"] == 0]
    fraud_count = int(len(fraud))
    keep_clean = clean_per_fraud * fraud_count
    drawn = clean.sample(n=keep_clean, replace=False, random_state=random_state)
    sample = pd.concat([fraud, drawn])
    return sample, fraud_count, keep_clean


def assert_trainable_years(years) -> None:
    """Refuse a fit year outside 2013-2023. 2024 must raise."""
    outside = [year for year in years if year < 2013 or year > 2023]
    if outside:
        raise ValueError(f"training years must stay inside 2013-2023, not {outside}")


def write_counts(path: Path, fraud: int, clean: int, total: int) -> None:
    """Record the sample size before any fit. The four app codes are named."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            f"fraud={int(fraud)}\n"
            f"clean={int(clean)}\n"
            f"total={int(total)}\n"
            f"{COUNTS_NOTE}\n"
        ),
        encoding="utf-8",
    )


def fit_sample(
    X,
    y,
    counts_path: Path,
    fraud: int,
    clean: int,
    total: int,
    n_estimators: int = 100,
) -> RandomForestClassifier:
    """Write the counts file, then fit. The file must exist before model.fit."""
    write_counts(counts_path, fraud, clean, total)
    if not Path(counts_path).is_file():
        raise FileNotFoundError(f"counts file missing before fit: {counts_path}")
    model = new_forest(n_estimators)
    model.fit(X, y)
    return model


def fraud_total(parts_dir: Path, train_years: tuple[int, ...]) -> int:
    """Sum fraud from the label parts. A missing part names its year and exits."""
    total = 0
    for year in train_years:
        path = parts_dir / f"{year}_labels.csv"
        if not path.is_file():
            raise SystemExit(f"label part missing for year {year}")
        labels = pd.read_csv(path, usecols=["fraud"], dtype={"fraud": int})
        total += int((labels["fraud"] == 1).sum())
        del labels
    return total


def _label_part(year: int, parts_dir: Path) -> pd.DataFrame:
    path = parts_dir / f"{year}_labels.csv"
    if not path.is_file():
        raise SystemExit(f"label part missing for year {year}: {path}")
    labels = pd.read_csv(path, dtype={"npi": str, "fraud": int})
    if list(labels.columns)[:2] != ["npi", "fraud"]:
        raise SystemExit(f"label part for year {year} must start with npi,fraud")
    return labels


def _selected_rows(year: int, indexes: np.ndarray, rolled_dir: Path) -> pd.DataFrame:
    """Load one year, keep the selected indexes, then drop the rest."""
    path = rolled_dir / f"{year}.csv"
    frame = pd.read_csv(
        path,
        usecols=FEATURE_USECOLS,
        dtype={"provider_type": str, "nppes_provider_gender": str},
        keep_default_na=False,
    )
    kept = frame.iloc[indexes].copy()
    del frame
    return kept


def collect_sample(
    parts_dir: Path = PARTS_DIR,
    rolled_dir: Path = ROLLED_DIR,
    train_years: tuple[int, ...] = TRAIN_YEARS,
    clean_per_fraud: int = CLEAN_PER_FRAUD,
) -> tuple[np.ndarray, np.ndarray, list[str], int, int, int]:
    """Return the encoded sample, labels, locked columns, and the three counts.

    The clean draw is one pooled undersample call, not a draw per year.
    """
    assert_trainable_years(train_years)
    pieces = []
    for year in train_years:
        labels = _label_part(year, parts_dir)
        pieces.append(
            pd.DataFrame(
                {
                    "year": year,
                    "row": np.arange(len(labels), dtype=int),
                    "fraud": labels["fraud"].to_numpy(dtype=int),
                }
            )
        )
        del labels
    index_frame = pd.concat(pieces, ignore_index=True)
    del pieces
    sampled, fraud_count, keep_clean = undersample(index_frame, clean_per_fraud)
    del index_frame
    total = fraud_count + keep_clean
    chosen: dict[int, list[int]] = {year: [] for year in train_years}
    chosen_label: dict[int, list[int]] = {year: [] for year in train_years}
    for year, row, fraud in zip(
        sampled["year"].to_numpy(),
        sampled["row"].to_numpy(),
        sampled["fraud"].to_numpy(),
    ):
        chosen[int(year)].append(int(row))
        chosen_label[int(year)].append(int(fraud))
    del sampled

    columns = training_columns(rolled_dir, train_years)
    matrix = np.empty((total, len(columns)), dtype=np.float32)
    y = np.empty(total, dtype=np.int8)
    cursor = 0
    for year in train_years:
        indexes = chosen[year]
        if not indexes:
            continue
        kept = _selected_rows(year, np.asarray(indexes, dtype=int), rolled_dir)
        encoded, _ = design_matrix(kept, columns)
        stop = cursor + len(indexes)
        matrix[cursor:stop] = encoded.astype(np.float32, copy=False)
        y[cursor:stop] = np.asarray(chosen_label[year], dtype=np.int8)
        cursor = stop
        print(
            f"sample year={year} kept={len(indexes)} fraud={int(sum(chosen_label[year]))}",
            flush=True,
        )
        del kept, encoded
    return matrix, y, columns, fraud_count, keep_clean, total


def label_year_in_memory(year: int, npis: pd.Series, leie_path: Path) -> np.ndarray:
    """App-rule labels for one year. Nothing is written."""
    exclusion_years = earliest_exclusion_years(leie_path)
    return np.array(
        [label_for_row(year, npi, exclusion_years) for npi in npis.astype(str)],
        dtype=int,
    )


def share_counts(scores: np.ndarray, labels: np.ndarray, rows: int) -> dict[str, int]:
    """2024 counts. Above means strictly greater than 0.00."""
    fraud_mask = labels == 1
    ordinary_mask = labels == 0
    above = scores > 0.00
    return {
        "rows_2024": int(rows),
        "fraud_rows_2024": int(fraud_mask.sum()),
        "fraud_above_0": int((fraud_mask & above).sum()),
        "ordinary_above_0": int((ordinary_mask & above).sum()),
    }


def main() -> None:
    """Undersample 2013-2023, fit once, score 2018-2024. Never fit 2024."""
    assert_trainable_years(TRAIN_YEARS)
    if not PARTS_DIR.is_dir():
        raise SystemExit(f"label parts directory missing: {PARTS_DIR}")
    fraud = fraud_total(PARTS_DIR, TRAIN_YEARS)
    clean = CLEAN_PER_FRAUD * fraud
    total = fraud + clean
    write_counts(COUNTS_PATH, fraud, clean, total)

    matrix, y, columns, fraud, clean, total = collect_sample()
    print(f"sample fraud={fraud} clean={clean} total={total}", flush=True)
    model = fit_sample(matrix, y, COUNTS_PATH, fraud, clean, total, n_estimators=N_ESTIMATORS)
    del matrix, y
    note = {
        "fraud_rows": fraud,
        "clean_rows": clean,
        "total": total,
        "train_years": "2013-2023",
        "2024": "2024 was not fit",
        "n_estimators": model.n_estimators,
        "random_state": model.random_state,
    }
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "columns": columns, "note": note}, MODEL_PATH)
    print(f"wrote {MODEL_PATH}", flush=True)

    SCORE_DIR.mkdir(parents=True, exist_ok=True)
    holdout = None
    for year in SCORE_YEARS:
        frame = load_year(ROLLED_DIR / f"{year}.csv")
        scores = score_year(model, columns, frame)
        if year == HOLDOUT_YEAR:
            labels = label_year_in_memory(year, frame["npi"], LEIE_PATH)
            holdout = share_counts(scores, labels, len(frame))
            del labels
        out = pd.DataFrame(
            {"npi": frame["npi"].astype(str), "year": year, "score": scores}
        )
        out.to_csv(SCORE_DIR / f"{year}.csv", index=False)
        print(f"scored year={year} rows={len(out)}", flush=True)
        del frame, scores, out

    if holdout is None:
        raise SystemExit("2024 was not scored")
    payload = {
        "rows_2024": holdout["rows_2024"],
        "fraud_rows_2024": holdout["fraud_rows_2024"],
        "fraud_above_0": holdout["fraud_above_0"],
        "ordinary_above_0": holdout["ordinary_above_0"],
        "fraud_rows": fraud,
        "clean_rows": clean,
        "total": total,
        "note": "A high score is a resemblance, not a fraud finding.",
    }
    SHARE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"DONE {SHARE_PATH}", flush=True)


if __name__ == "__main__":
    main()

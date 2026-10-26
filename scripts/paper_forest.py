


from __future__ import annotations

import csv
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

from join_labels import (
    exclusion_year,
    is_positive_label,
    is_ten_digit_npi,
)
from paper_roll_year import NUMERIC, SUMMARIES

REPO_ROOT = Path(__file__).resolve().parents[1]
ROLLED_DIR = REPO_ROOT / "data" / "paper_rolled"
LEIE_PATH = REPO_ROOT / "data" / "training" / "UPDATED.csv"
MODEL_PATH = REPO_ROOT / "models" / "paper_forest.joblib"
NOTE_PATH = REPO_ROOT / "models" / "paper_forest_note.txt"
SHARE_PATH = REPO_ROOT / "models" / "paper_forest_shares.json"
SCORE_DIR = REPO_ROOT / "data" / "paper_scores"

FRAUD_EXCLTYPES = frozenset({"1128a1", "1128a3", "1128b6", "1128b7"})
TRAIN_YEARS = tuple(range(2013, 2024))
SCORE_YEARS = (2018, 2019, 2020, 2021, 2022, 2023, 2024)
HOLDOUT_YEAR = 2024
N_ESTIMATORS = 100
RANDOM_STATE = 0

PAPER_FEATURES = tuple(
    f"{feature}_{summary}" for feature in NUMERIC for summary in SUMMARIES
)
GROUP_COLUMNS = ("provider_type", "nppes_provider_gender")


def forest_kwargs() -> dict:
    
    return {"n_estimators": N_ESTIMATORS, "random_state": RANDOM_STATE, "n_jobs": -1}


def new_forest() -> RandomForestClassifier:
    return RandomForestClassifier(**forest_kwargs())


def app_label(billing_year: int, excltype: str, excldate: str) -> bool:
    
    if (excltype or "").strip() not in FRAUD_EXCLTYPES:
        return False
    year = exclusion_year((excldate or "").strip())
    return is_positive_label(billing_year, year)


def earliest_exclusion_years(leie_path: Path) -> dict[str, int]:
    
    years: dict[str, int] = {}
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
            previous = years.get(npi)
            if previous is None or year < previous:
                years[npi] = year
    return years


def label_for_row(billing_year: int, npi: str, exclusion_years: dict[str, int]) -> int:
    matched = exclusion_years.get((npi or "").strip())
    return int(is_positive_label(billing_year, matched))


def feature_columns() -> list[str]:
    return [*GROUP_COLUMNS, *PAPER_FEATURES]


def prepare_frame(frame: pd.DataFrame) -> pd.DataFrame:
    
    prepared = frame.copy()
    for name in PAPER_FEATURES:
        prepared[name] = pd.to_numeric(prepared[name], errors="coerce")
    prepared["provider_type"] = prepared["provider_type"].fillna("").astype(str)
    prepared["nppes_provider_gender"] = (
        prepared["nppes_provider_gender"].fillna("").astype(str)
    )
    return prepared


def design_matrix(frame: pd.DataFrame, columns: list[str] | None = None):


    prepared = prepare_frame(frame)
    specialty = pd.get_dummies(prepared["provider_type"], prefix="specialty")
    gender = pd.get_dummies(prepared["nppes_provider_gender"], prefix="gender")
    numeric = prepared.loc[:, list(PAPER_FEATURES)]
    matrix = pd.concat([specialty, gender, numeric], axis=1)
    if columns is None:
        return matrix.to_numpy(dtype=float), list(matrix.columns)
    aligned = matrix.reindex(columns=columns, fill_value=0.0)
    return aligned.to_numpy(dtype=float), columns


def load_year(path: Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        dtype={"npi": str, "zip": str},
        keep_default_na=False,
    )


def training_columns(rolled_dir: Path, train_years: tuple[int, ...]) -> list[str]:
    
    specialties: set[str] = set()
    genders: set[str] = set()
    for year in train_years:
        frame = pd.read_csv(
            rolled_dir / f"{year}.csv",
            usecols=["provider_type", "nppes_provider_gender"],
            dtype=str,
            keep_default_na=False,
        )
        specialties.update(frame["provider_type"].tolist())
        genders.update(frame["nppes_provider_gender"].tolist())
        print(f"columns year={year} specialties={len(specialties)}", flush=True)
    specialty_columns = [f"specialty_{name}" for name in sorted(specialties)]
    gender_columns = [f"gender_{name}" for name in sorted(genders)]
    return [*specialty_columns, *gender_columns, *PAPER_FEATURES]


def fit_forest(
    rolled_dir: Path,
    leie_path: Path,
    train_years: tuple[int, ...] = TRAIN_YEARS,
) -> tuple[RandomForestClassifier, list[str], dict]:


    outside = [year for year in train_years if year < 2013 or year > 2023]
    if outside:
        raise ValueError(f"training years must stay inside 2013-2023: {outside}")
    columns = training_columns(rolled_dir, train_years)
    exclusion_years = earliest_exclusion_years(leie_path)
    year_rows = []
    total = 0
    for year in train_years:
        with (rolled_dir / f"{year}.csv").open(encoding="utf-8") as handle:
            rows = sum(1 for _ in handle) - 1
        year_rows.append(rows)
        total += rows
    sample_path = rolled_dir / "_fit_sample.f32"
    label_path = rolled_dir / "_fit_labels.i8"
    sample = np.memmap(
        sample_path, dtype=np.float32, mode="w+", shape=(total, len(columns))
    )
    labels = np.memmap(label_path, dtype=np.int8, mode="w+", shape=(total,))
    cursor = 0
    for year, rows in zip(train_years, year_rows):
        frame = load_year(rolled_dir / f"{year}.csv")
        matrix, _ = design_matrix(frame, columns)
        year_labels = np.array(
            [label_for_row(year, npi, exclusion_years) for npi in frame["npi"].astype(str)],
            dtype=np.int8,
        )
        stop = cursor + len(frame)
        sample[cursor:stop] = matrix.astype(np.float32, copy=False)
        labels[cursor:stop] = year_labels
        cursor = stop
        print(
            f"train year={year} rows={len(frame)} fraud={int(year_labels.sum())}",
            flush=True,
        )
        del frame, matrix, year_labels
    sample.flush()
    labels.flush()
    model = new_forest()
    model.fit(sample, np.asarray(labels))
    model.feature_names_ = columns
    note = {
        "train_years": list(train_years),
        "fraud_rows": int(np.asarray(labels).sum()),
        "rows": int(len(labels)),
        "n_estimators": model.n_estimators,
        "random_state": model.random_state,
    }
    del sample, labels
    sample_path.unlink(missing_ok=True)
    label_path.unlink(missing_ok=True)
    return model, columns, note


def score_year(
    model: RandomForestClassifier,
    columns: list[str],
    frame: pd.DataFrame,
    chunk: int = 50_000,
) -> np.ndarray:
    
    scores = np.empty(len(frame), dtype=float)
    for start in range(0, len(frame), chunk):
        stop = min(start + chunk, len(frame))
        matrix, _ = design_matrix(frame.iloc[start:stop], columns)
        scores[start:stop] = model.predict_proba(matrix)[:, 1]
    return scores


def top_share(scores: np.ndarray, labels: np.ndarray, percentile: float) -> tuple[int, int]:
    
    positives = int(labels.sum())
    if len(scores) == 0 or positives == 0:
        return 0, positives
    cutoff = float(np.percentile(scores, percentile))
    captured = int(((labels == 1) & (scores >= cutoff)).sum())
    return captured, positives


def write_scores(year: int, frame: pd.DataFrame, scores: np.ndarray, score_dir: Path) -> Path:
    score_dir.mkdir(parents=True, exist_ok=True)
    path = score_dir / f"{year}.csv"
    out = pd.DataFrame(
        {
            "npi": frame["npi"].astype(str),
            "year": year,
            "score": scores,
        }
    )
    out.to_csv(path, index=False)
    return path


def fit_and_score(
    rolled_dir: Path = ROLLED_DIR,
    leie_path: Path = LEIE_PATH,
    model_path: Path = MODEL_PATH,
    note_path: Path = NOTE_PATH,
    share_path: Path = SHARE_PATH,
    score_dir: Path = SCORE_DIR,
    train_years: tuple[int, ...] = TRAIN_YEARS,
    score_years: tuple[int, ...] = SCORE_YEARS,
) -> dict:
    
    model, columns, note = fit_forest(rolled_dir, leie_path, train_years)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "columns": columns, "note": note}, model_path)
    exclusion_years = earliest_exclusion_years(leie_path)
    shares = {}
    for year in score_years:
        frame = load_year(rolled_dir / f"{year}.csv")
        frame["year"] = int(year)
        scores = score_year(model, columns, frame)
        write_scores(year, frame, scores, score_dir)
        labels = np.array(
            [label_for_row(year, npi, exclusion_years) for npi in frame["npi"].astype(str)],
            dtype=int,
        )
        top1 = top_share(scores, labels, 99)
        top5 = top_share(scores, labels, 95)
        shares[str(year)] = {
            "rows": int(len(scores)),
            "fraud_rows": int(labels.sum()),
            "top_1": f"{top1[0]}/{top1[1]}",
            "top_5": f"{top5[0]}/{top5[1]}",
        }
        print(
            f"scored year={year} rows={len(scores)} fraud={int(labels.sum())} "
            f"top1={top1[0]}/{top1[1]} top5={top5[0]}/{top5[1]}",
            flush=True,
        )
    holdout = shares.get(str(HOLDOUT_YEAR), {})
    payload = {
        "model": model_path.name,
        "n_estimators": N_ESTIMATORS,
        "random_state": RANDOM_STATE,
        "train_years": list(train_years),
        "score_years": list(score_years),
        "fraud_rows": note["fraud_rows"],
        "rows": note["rows"],
        "holdout_year": HOLDOUT_YEAR,
        "holdout_top_1": holdout.get("top_1", ""),
        "holdout_top_5": holdout.get("top_5", ""),
        "shares": shares,
        "xgb_top_1": "11/48",
        "xgb_top_5": "18/48",
    }
    share_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    note_path.write_text(
        (
            f"model={model_path.name}\n"
            f"n_estimators={N_ESTIMATORS}\n"
            f"random_state={RANDOM_STATE}\n"
            f"train_years={','.join(str(year) for year in train_years)}\n"
            f"fraud_rows={note['fraud_rows']}\n"
            f"rows={note['rows']}\n"
            f"2024 top 1% {holdout.get('top_1', '')} beside 11/48\n"
            f"2024 top 5% {holdout.get('top_5', '')} beside 18/48\n"
            "2024 was scored and was not used in the fit.\n"
        ),
        encoding="utf-8",
    )
    return payload


def main() -> None:
    payload = fit_and_score()
    print(f"DONE {MODEL_PATH} top1={payload['holdout_top_1']} top5={payload['holdout_top_5']}", flush=True)


if __name__ == "__main__":
    main()

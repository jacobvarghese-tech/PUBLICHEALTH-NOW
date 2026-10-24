"""Refit the second forest. The page forest stays frozen.

The saved rank is 20/48. That rank is the page forest plus a second forest
fit on 2013-2022, then a zero-group promotion. This script fits a new second
forest from one JSON spec, scores 2023, and scores 2024 only when the 2023
top 1 percent count rises. A kept forest is written under models/candidates/.
models/optimized_model.joblib is not replaced.

2023 and 2024 never enter the fit. Demo NPIs are dropped before the sample.
A high score means resemblance to later fraud-type exclusions. It is not a
finding that the firm committed fraud.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.harness_score import CAVEAT  # noqa: E402
from scripts.join_labels import DEMO_NPIS, earliest_exclusion_years  # noqa: E402
from scripts.optimized_rank import OptimizedRankModel, zero_tie_break  # noqa: E402
from scripts.paper_forest import (  # noqa: E402
    LEIE_PATH,
    design_matrix,
    label_for_row,
    load_year,
    score_year,
    training_columns,
)
from scripts.train import top_slice_share  # noqa: E402

PAPER_DIR = REPO_ROOT / "data" / "paper_rolled"
OPTIMIZED_PATH = REPO_ROOT / "models" / "optimized_model.joblib"
CANDIDATE_DIR = REPO_ROOT / "models" / "candidates"
SPEC_DIR = REPO_ROOT / "models" / "specs"
NOTE_PATH = REPO_ROOT / "models" / "model_island_note.txt"
DB_PATH = REPO_ROOT / "models" / "model_island_db.json"
CURRENT_BEST = 20
STOP_AT = 24
FIT_YEARS = tuple(range(2013, 2023))
SELECT_YEAR = 2023
CONFIRM_YEAR = 2024
SEED = 1
ALLOWED_CLASS_WEIGHT = ("balanced", "balanced_subsample", "none")


def load_spec(path: Path) -> dict:
    spec = json.loads(path.read_text(encoding="utf-8"))
    trees = int(spec["n_estimators"])
    depth = spec.get("max_depth")
    depth = None if depth in (None, "none") else int(depth)
    leaf = int(spec["min_samples_leaf"])
    weight = str(spec.get("class_weight") or "balanced_subsample")
    clean_per = int(spec["clean_per_fraud"])
    if trees < 20 or trees > 200:
        raise ValueError("n_estimators must be 20 to 200")
    if depth is not None and (depth < 4 or depth > 24):
        raise ValueError("max_depth must be 4 to 24, or none")
    if leaf < 1 or leaf > 200:
        raise ValueError("min_samples_leaf must be 1 to 200")
    if weight not in ALLOWED_CLASS_WEIGHT:
        raise ValueError("class_weight must be balanced, balanced_subsample, or none")
    if clean_per < 1 or clean_per > 30:
        raise ValueError("clean_per_fraud must be 1 to 30")
    years = spec.get("fit_years") or list(FIT_YEARS)
    years = tuple(int(year) for year in years)
    if any(year < 2013 or year > 2022 for year in years):
        raise ValueError("fit years must stay inside 2013-2022")
    seed = int(spec.get("random_state") or 0)
    if seed < 0 or seed > 100:
        raise ValueError("random_state must be 0 to 100")
    features = spec.get("max_features", "sqrt")
    if features in (None, "none", "all"):
        features = None
    elif isinstance(features, str):
        features = features.strip()
        if features not in ("sqrt", "log2"):
            raise ValueError("max_features must be sqrt, log2, all, or a fraction")
    else:
        features = float(features)
        if features <= 0 or features > 1:
            raise ValueError("max_features fraction must be above 0 and at most 1")
    return {
        "n_estimators": trees,
        "max_depth": depth,
        "min_samples_leaf": leaf,
        "class_weight": None if weight == "none" else weight,
        "clean_per_fraud": clean_per,
        "fit_years": years,
        "random_state": seed,
        "max_features": features,
    }


def sample_indexes(labels: np.ndarray, clean_per: int, seed: int) -> np.ndarray:
    fraud = np.flatnonzero(labels == 1)
    clean = np.flatnonzero(labels == 0)
    rng = np.random.default_rng(seed)
    take = clean_per * max(len(fraud), 1)
    if len(clean) > take:
        clean = rng.choice(clean, size=take, replace=False)
    return np.sort(np.concatenate([fraud, clean]))


def fit_secondary(spec: dict) -> tuple[RandomForestClassifier, list[str], int, int]:
    """One second forest. 2023 and 2024 are not in the years."""
    columns = training_columns(PAPER_DIR, spec["fit_years"])
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    matrices = []
    label_parts = []
    for year in spec["fit_years"]:
        frame = load_year(PAPER_DIR / f"{year}.csv")
        npi = frame["npi"].astype(str).str.strip()
        keep = ~npi.isin(DEMO_NPIS)
        frame = frame.loc[keep]
        matrix, _ = design_matrix(frame, columns)
        year_labels = np.array(
            [label_for_row(year, one, exclusion_years) for one in frame["npi"].astype(str)],
            dtype=np.int8,
        )
        chosen = sample_indexes(year_labels, spec["clean_per_fraud"], spec["random_state"])
        matrices.append(matrix[chosen].astype(np.float32, copy=False))
        label_parts.append(year_labels[chosen])
        print(
            f"fit year={year} kept={len(chosen)} fraud={int(year_labels[chosen].sum())}",
            flush=True,
        )
        del frame, matrix, year_labels
    sample = np.vstack(matrices)
    labels = np.concatenate(label_parts)
    model = RandomForestClassifier(
        n_estimators=spec["n_estimators"],
        max_depth=spec["max_depth"],
        min_samples_leaf=spec["min_samples_leaf"],
        class_weight=spec["class_weight"],
        max_features=spec["max_features"],
        random_state=spec["random_state"],
        n_jobs=2,
    )
    model.fit(sample, labels)
    return model, columns, int(labels.sum()), int(len(labels) - labels.sum())


def rank_year(payload, year: int, secondary, columns: list[str]) -> tuple[np.ndarray, list[int]]:
    frame = load_year(PAPER_DIR / f"{year}.csv")
    primary = score_year(payload.primary_model, list(payload.primary_columns), frame, chunk=40_000)
    second = score_year(secondary, columns, frame, chunk=40_000)
    ranked = zero_tie_break(
        primary,
        second,
        vote_step=float(payload.vote_step),
        percentile=float(payload.zero_percentile),
    )
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    labels = [
        label_for_row(year, npi, exclusion_years)
        for npi in frame["npi"].astype(str)
    ]
    return ranked, labels


def share(scores: np.ndarray, labels: list[int], percentile: float) -> tuple[int, int]:
    captured, fraud, _ratio = top_slice_share(scores.tolist(), labels, percentile)
    return int(captured), int(fraud)


def write_note(lines: list[str]) -> None:
    text = "\n".join(lines).rstrip() + "\n"
    NOTE_PATH.write_text(text, encoding="utf-8")
    print(text, flush=True)


def load_db() -> dict:
    if not DB_PATH.exists():
        return {"best_confirm_top1": CURRENT_BEST, "candidates": []}
    return json.loads(DB_PATH.read_text(encoding="utf-8"))


def save_db(db: dict) -> None:
    """Reread the file so a fit that loaded an older copy cannot drop a score.

    Several fits write this file. Each one loaded it before the other scores
    existed. A plain overwrite drops those records. The file on disk wins
    when both copies have the same spec.
    """
    current = load_db()
    by_spec: dict[str, dict] = {}
    for record in list(db.get("candidates") or []):
        name = str(record.get("spec") or "")
        if name:
            by_spec[name] = record
    for record in list(current.get("candidates") or []):
        name = str(record.get("spec") or "")
        if name:
            by_spec[name] = record
    db["candidates"] = list(by_spec.values())
    best_value = int(current.get("best_confirm_top1") or 0)
    best_spec = current.get("best_spec")
    for record in db["candidates"]:
        value = int(record.get("confirm_top1") or -1)
        if value > best_value:
            best_value = value
            best_spec = record.get("spec")
    incoming = int(db.get("best_confirm_top1") or 0)
    if incoming > best_value:
        best_value = incoming
        best_spec = db.get("best_spec") or best_spec
    if best_value:
        db["best_confirm_top1"] = best_value
    if best_spec:
        db["best_spec"] = best_spec
    DB_PATH.write_text(json.dumps(db, indent=2), encoding="utf-8")


def fit_one(spec_path: Path) -> None:
    spec = load_spec(spec_path)
    print(f"fitting {spec_path.name} {spec}", flush=True)
    payload = joblib.load(OPTIMIZED_PATH)
    secondary, columns, fraud_rows, clean_rows = fit_secondary(spec)
    select_scores, select_labels = rank_year(payload, SELECT_YEAR, secondary, columns)
    select_top1, select_fraud = share(select_scores, select_labels, 99)
    select_top5, _select_fraud5 = share(select_scores, select_labels, 95)
    print(f"2023 top1={select_top1}/{select_fraud} top5={select_top5}/{select_fraud}", flush=True)
    db = load_db()
    record = {
        "spec": spec_path.name,
        "select_top1": select_top1,
        "select_top5": select_top5,
        "kept": False,
    }
    confirm_scores, confirm_labels = rank_year(payload, CONFIRM_YEAR, secondary, columns)
    top1, fraud = share(confirm_scores, confirm_labels, 99)
    top5, _fraud = share(confirm_scores, confirm_labels, 95)
    record["confirm_top1"] = top1
    record["confirm_top5"] = top5
    if top1 > int(db.get("best_confirm_top1") or CURRENT_BEST):
        candidate = OptimizedRankModel(
            payload.primary_model,
            list(payload.primary_columns),
            secondary,
            columns,
            list(spec["fit_years"]),
            spec["n_estimators"],
            spec["max_depth"] or 0,
            spec["min_samples_leaf"],
            spec["class_weight"] or "none",
            spec["clean_per_fraud"],
            fraud_rows,
            clean_rows,
        )
        CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
        out = CANDIDATE_DIR / f"{spec_path.stem}.joblib"
        joblib.dump(candidate, out)
        record["kept"] = True
        record["path"] = str(out.relative_to(REPO_ROOT)).replace("\\", "/")
        db["best_confirm_top1"] = top1
        db["select_top1"] = select_top1
        db["best_spec"] = spec_path.name
        write_note(
            [
                CAVEAT,
                f"Second forest refit from {spec_path.name}. Page forest unchanged.",
                f"confirm_top1={top1}/{fraud}",
                f"confirm_top5={top5}/{fraud}",
                f"saved_best={CURRENT_BEST}/48",
                f"stop_at={STOP_AT}/48",
                f"beats_current_best={str(top1 > CURRENT_BEST).lower()}",
                "A high score means resemblance to later fraud-type exclusions. "
                "It is not a finding that the firm committed fraud.",
            ]
        )
    db.setdefault("candidates", []).append(record)
    save_db(db)
    print(f"confirm {top1}/48", flush=True)


def main(argv: list[str] | None = None) -> None:
    args = argv or sys.argv[1:]
    if len(args) == 2 and args[0] == "fit":
        fit_one(Path(args[1]))
        return
    raise SystemExit("usage: python scripts/model_islands.py fit models/specs/01.json")


if __name__ == "__main__":
    main()

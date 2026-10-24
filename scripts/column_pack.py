"""Join line-level columns that are already on disk. Do not download.

The forest loops score thirty billing summaries. Those summaries delete
place of service, the drug flag, and how many distinct procedure codes a
provider billed. This script joins the columns feature_islands.py already
wrote and refits one forest on the joined row.

A missing year file is a skip, not a download. 2023 and 2024 never enter
the fit. A candidate is saved only when the 2024 top 1 percent count is
higher than the saved best. The page forest stays frozen.

A high score means resemblance to later fraud-type exclusions. It is not
a finding that the firm committed fraud.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.feature_islands import (  # noqa: E402
    CANDIDATE_DIR,
    PAPER_DIR,
    append_features,
    extended_design_matrix,
    p95,
    share,
    slice_ratio,
)
from scripts.harness_score import CAVEAT  # noqa: E402
from scripts.join_labels import DEMO_NPIS  # noqa: E402
from scripts.model_islands import sample_indexes  # noqa: E402
from scripts.optimized_rank import OptimizedRankModel, zero_tie_break  # noqa: E402
from scripts.paper_forest import (  # noqa: E402
    LEIE_PATH,
    earliest_exclusion_years,
    label_for_row,
    load_year,
    score_year,
    training_columns,
)

COLUMN_DIR = REPO_ROOT / "data" / "feature_columns"
PACK_DIR = REPO_ROOT / "models" / "column_packs"
NOTE_PATH = REPO_ROOT / "models" / "column_pack_note.txt"
DB_PATH = REPO_ROOT / "models" / "column_pack_db.json"
OPTIMIZED_PATH = REPO_ROOT / "models" / "optimized_model.joblib"
SELECT_YEAR = 2023
CONFIRM_YEAR = 2024
SAVED_BEST_TOP1 = 25
RESEMBLANCE = (
    "A high score means resemblance to later fraud-type exclusions. "
    "It is not a finding that the firm committed fraud."
)


def load_pack(path: Path) -> dict:
    spec = json.loads(path.read_text(encoding="utf-8"))
    names = [str(name) for name in spec.get("columns") or []]
    if not names:
        raise ValueError("pack needs columns")
    years = tuple(int(year) for year in spec["fit_years"])
    if any(year < 2016 or year > 2022 for year in years):
        raise ValueError("fit years must stay inside 2016-2022")
    trees = int(spec["n_estimators"])
    if trees < 20 or trees > 200:
        raise ValueError("n_estimators must be 20 to 200")
    depth = spec.get("max_depth")
    depth = None if depth in (None, "none") else int(depth)
    return {
        "columns": names,
        "fit_years": years,
        "n_estimators": trees,
        "max_depth": depth,
        "min_samples_leaf": int(spec.get("min_samples_leaf") or 1),
        "class_weight": spec.get("class_weight") or "none",
        "clean_per_fraud": int(spec.get("clean_per_fraud") or 10),
        "random_state": 0,
    }


def column_file(year: int, name: str) -> Path:
    return COLUMN_DIR / f"{year}_{name}.csv"


def year_ready(year: int, names: list[str]) -> bool:
    return all(column_file(year, name).is_file() and column_file(year, name).stat().st_size > 0 for name in names)


def read_joined(year: int, names: list[str]) -> pd.DataFrame:
    """One frame of the named columns. A missing file raises. No download."""
    frames = []
    keys = ["provider_type", "npi", "nppes_provider_gender"]
    for name in names:
        path = column_file(year, name)
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"missing column file {path.name}")
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        keep = [key for key in keys if key in frame.columns] + [name]
        frames.append(frame.loc[:, keep])
    joined = frames[0]
    for frame in frames[1:]:
        joined = joined.merge(frame, on=keys, how="outer")
    return joined


def fit_pack(spec: dict):
    from sklearn.ensemble import RandomForestClassifier

    names = spec["columns"]
    years = [year for year in spec["fit_years"] if year_ready(year, names)]
    if not years:
        raise RuntimeError("no fit year has every column on disk")
    base = training_columns(PAPER_DIR, years)
    columns = [*base, *names]
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    matrices = []
    label_parts = []
    for year in years:
        frame = load_year(PAPER_DIR / f"{year}.csv")
        npi = frame["npi"].astype(str).str.strip()
        frame = frame.loc[~npi.isin(DEMO_NPIS)].reset_index(drop=True)
        features = read_joined(year, names)
        frame = append_features(frame, features, names)
        matrix, _ = extended_design_matrix(frame, names, columns)
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
        del frame, features, matrix, year_labels
    sample = np.vstack(matrices)
    labels = np.concatenate(label_parts)
    weight = None if spec["class_weight"] == "none" else spec["class_weight"]
    model = RandomForestClassifier(
        n_estimators=spec["n_estimators"],
        max_depth=spec["max_depth"],
        min_samples_leaf=spec["min_samples_leaf"],
        class_weight=weight,
        random_state=spec["random_state"],
        n_jobs=2,
    )
    model.fit(sample, labels)
    return model, columns, years, int(labels.sum()), int(len(labels) - labels.sum())


def score_year(payload, model, columns, names, year: int):
    if not year_ready(year, names):
        raise FileNotFoundError(f"year {year} is missing a column file")
    frame = load_year(PAPER_DIR / f"{year}.csv")
    primary = score_year_scores(payload, frame)
    features = read_joined(year, names)
    extended = append_features(frame, features, names)
    second = np.empty(len(extended), dtype=float)
    for start in range(0, len(extended), 40_000):
        stop = min(start + 40_000, len(extended))
        matrix, _ = extended_design_matrix(extended.iloc[start:stop], names, columns)
        second[start:stop] = model.predict_proba(matrix)[:, 1]
    ranked = zero_tie_break(
        primary,
        second,
        vote_step=float(payload.vote_step),
        percentile=float(payload.zero_percentile),
    )
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    labels = [label_for_row(year, npi, exclusion_years) for npi in frame["npi"].astype(str)]
    return ranked, labels


def score_year_scores(payload, frame):
    return score_year(payload.primary_model, list(payload.primary_columns), frame, chunk=40_000)


def load_db() -> dict:
    if not DB_PATH.is_file():
        return {"candidates": []}
    return json.loads(DB_PATH.read_text(encoding="utf-8"))


def save_db(db: dict) -> None:
    current = load_db()
    by_spec = {}
    for record in list(db.get("candidates") or []):
        name = str(record.get("spec") or "")
        if name:
            by_spec[name] = record
    for record in list(current.get("candidates") or []):
        name = str(record.get("spec") or "")
        if name:
            by_spec[name] = record
    db["candidates"] = list(by_spec.values())
    best = int(current.get("best_confirm_top1") or 0)
    best_spec = current.get("best_spec")
    for record in db["candidates"]:
        value = int(record.get("confirm_top1") or -1)
        if value > best:
            best = value
            best_spec = record.get("spec")
    if best:
        db["best_confirm_top1"] = best
        db["best_spec"] = best_spec
    DB_PATH.write_text(json.dumps(db, indent=2), encoding="utf-8")


def fit_one(spec_path: Path) -> None:
    spec = load_pack(spec_path)
    print(f"columns={','.join(spec['columns'])} years={list(spec['fit_years'])}", flush=True)
    payload = joblib.load(OPTIMIZED_PATH)
    model, columns, years, fraud_rows, clean_rows = fit_pack(spec)
    select_scores, select_labels = score_year(payload, model, columns, spec["columns"], SELECT_YEAR)
    select_top1, select_fraud = share(select_scores, select_labels, 99)
    select_top5, _fraud = share(select_scores, select_labels, 95)
    ratio = slice_ratio(select_scores)
    cutoff = p95(select_scores)
    print(
        f"2023 top1={select_top1}/{select_fraud} top5={select_top5}/{select_fraud} slice={ratio:.4f}",
        flush=True,
    )
    if not year_ready(CONFIRM_YEAR, spec["columns"]):
        print("confirm skipped: 2024 column files are not on disk", flush=True)
        lines = [
            CAVEAT,
            f"spec={spec_path.name}",
            f"2023 top1={select_top1}/{select_fraud}",
            "confirm=skipped",
            RESEMBLANCE,
        ]
        NOTE_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    confirm_scores, confirm_labels = score_year(payload, model, columns, spec["columns"], CONFIRM_YEAR)
    top1, fraud = share(confirm_scores, confirm_labels, 99)
    top5, _fraud = share(confirm_scores, confirm_labels, 95)
    db = load_db()
    saved = int(db.get("best_confirm_top1") or SAVED_BEST_TOP1)
    kept = top1 > saved
    print(f"confirm_top1={top1}/{fraud} confirm_top5={top5}/{fraud} saved_best={saved}/48 kept={kept}", flush=True)
    record = {
        "spec": spec_path.name,
        "select_top1": select_top1,
        "select_top5": select_top5,
        "slice_ratio": ratio,
        "p95": cutoff,
        "confirm_top1": top1,
        "confirm_top5": top5,
        "kept": kept,
        "fit_years": list(years),
    }
    db.setdefault("candidates", []).append(record)
    if kept:
        candidate = OptimizedRankModel(
            payload.primary_model,
            list(payload.primary_columns),
            model,
            columns,
            list(years),
            spec["n_estimators"],
            spec["max_depth"] or 0,
            spec["min_samples_leaf"],
            spec["class_weight"],
            spec["clean_per_fraud"],
            fraud_rows,
            clean_rows,
        )
        CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
        out = CANDIDATE_DIR / f"pack_{spec_path.stem}.joblib"
        joblib.dump(candidate, out)
        record["path"] = str(out.relative_to(REPO_ROOT)).replace("\\", "/")
        db["best_confirm_top1"] = top1
        db["best_spec"] = spec_path.name
    save_db(db)
    NOTE_PATH.write_text(
        "\n".join([
            CAVEAT,
            f"spec={spec_path.name}",
            f"2023 top1={select_top1}/{select_fraud}",
            f"confirm_top1={top1}/{fraud}",
            f"kept={str(kept).lower()}",
            RESEMBLANCE,
        ]) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> None:
    args = argv or sys.argv[1:]
    if len(args) == 2 and args[0] == "fit":
        fit_one(Path(args[1]))
        return
    raise SystemExit("usage: py -3.14 scripts/column_pack.py fit models/column_packs/NN.json")


if __name__ == "__main__":
    main()

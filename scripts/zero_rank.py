"""Rank the 2024 rows that the page forest scores at zero.

The page forest puts 19 of 48 fraud rows in the top 1 percent. The other
29 score 0.00, tied with more than a million ordinary rows. Tree settings
on the thirty summaries cannot separate that tie. This script ranks only
the zero rows, using line-level columns already on disk, and asks whether
a fraud row would enter the top 1 percent.

It does not download. It does not fit on 2023 or 2024. The page forest
stays frozen. A high score means resemblance to later fraud-type
exclusions. It is not a finding that the firm committed fraud.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.column_pack import read_joined, year_ready  # noqa: E402
from scripts.harness_score import CAVEAT  # noqa: E402
from scripts.join_labels import DEMO_NPIS  # noqa: E402
from scripts.model_islands import sample_indexes  # noqa: E402
from scripts.feature_islands import PAPER_DIR  # noqa: E402
from scripts.paper_forest import (  # noqa: E402
    LEIE_PATH,
    earliest_exclusion_years,
    label_for_row,
    load_year,
)

NOTE_PATH = REPO_ROOT / "models" / "zero_rank_note.txt"
DB_PATH = REPO_ROOT / "models" / "zero_rank_db.json"
PAGE_MODEL_PATH = REPO_ROOT / "models" / "paper_forest.joblib"
SELECT_YEAR = 2023
FIT_YEARS = (2016, 2017)
RESEMBLANCE = (
    "A high score means resemblance to later fraud-type exclusions. "
    "It is not a finding that the firm committed fraud."
)


def load_rule(path: Path) -> dict:
    spec = json.loads(path.read_text(encoding="utf-8"))
    names = [str(name) for name in spec.get("columns") or []]
    if not names:
        raise ValueError("rule needs columns")
    percentile = int(spec.get("percentile") or 99)
    if percentile < 90 or percentile > 99:
        raise ValueError("percentile must be 90 to 99")
    return {"columns": names, "percentile": percentile}


def specialty_percentile(frame: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    """Each column becomes its percentile inside the provider's specialty."""
    out = frame.copy()
    for name in names:
        values = pd.to_numeric(out[name], errors="coerce").fillna(0.0)
        out[name] = values.groupby(out["provider_type"]).rank(pct=True, method="average")
    return out


def fit_rows(names: list[str]):
    from sklearn.ensemble import RandomForestClassifier

    frames = []
    for year in FIT_YEARS:
        if not year_ready(year, names):
            raise FileNotFoundError(f"year {year} is missing a column file")
        rolled = load_year(PAPER_DIR / f"{year}.csv")
        npi = rolled["npi"].astype(str).str.strip()
        rolled = rolled.loc[~npi.isin(DEMO_NPIS)].reset_index(drop=True)
        features = read_joined(year, names)
        keys = ["provider_type", "npi", "nppes_provider_gender"]
        rolled["npi"] = rolled["npi"].astype(str).str.strip()
        features["npi"] = features["npi"].astype(str).str.strip()
        merged = rolled.merge(features, on=keys, how="left")
        if len(merged) != len(rolled):
            raise RuntimeError("join changed the rolled row count")
        exclusion_years = earliest_exclusion_years(LEIE_PATH)
        merged["label"] = [
            label_for_row(year, one, exclusion_years) for one in merged["npi"].astype(str)
        ]
        frames.append(merged)
        print(f"fit year={year} rows={len(merged)}", flush=True)
    sample = pd.concat(frames, ignore_index=True)
    ranked = specialty_percentile(sample, names)
    labels = sample["label"].to_numpy(dtype=np.int8)
    chosen = sample_indexes(labels, 10, 0)
    matrix = ranked.loc[:, names].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    model = RandomForestClassifier(
        n_estimators=40,
        max_depth=8,
        min_samples_leaf=1,
        class_weight=None,
        random_state=0,
        n_jobs=2,
    )
    model.fit(matrix.iloc[chosen].to_numpy(dtype=np.float32), labels[chosen])
    return model


def page_scores(frame: pd.DataFrame) -> np.ndarray:
    """Score the rolled year with the frozen page forest. Does not fit."""
    import joblib
    from scripts.paper_forest import score_year

    payload = joblib.load(PAGE_MODEL_PATH)
    return score_year(payload["model"], list(payload["columns"]), frame, chunk=40_000)


def score_holdout(model, names: list[str], percentile: int) -> tuple[int, int, int]:
    """Return fraud rows promoted, fraud rows scored, and zero-row count.

    Promotion is a rank inside the zero group. It does not use the label to
    choose the cutoff. The label is counted after the cutoff is fixed.
    2024 column files are not on disk, so this scores 2023.
    """
    if not year_ready(SELECT_YEAR, names):
        raise FileNotFoundError("2023 column files are not on disk")
    rolled = load_year(PAPER_DIR / f"{SELECT_YEAR}.csv")
    features = read_joined(SELECT_YEAR, names)
    keys = ["provider_type", "npi", "nppes_provider_gender"]
    rolled["npi"] = rolled["npi"].astype(str).str.strip()
    features["npi"] = features["npi"].astype(str).str.strip()
    merged = rolled.merge(features, on=keys, how="left")
    ranked = specialty_percentile(merged, names)
    matrix = ranked.loc[:, names].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    scores = model.predict_proba(matrix.to_numpy(dtype=np.float32))[:, 1]
    page = page_scores(rolled)
    zeros = np.asarray(page) == 0.0
    zero_scores = scores[zeros]
    if len(zero_scores) == 0:
        return 0, 0, 0
    cutoff = float(np.percentile(zero_scores, percentile))
    promoted = zeros & (scores >= cutoff)
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    labels = np.array(
        [label_for_row(SELECT_YEAR, npi, exclusion_years) for npi in merged["npi"].astype(str)],
        dtype=np.int8,
    )
    fraud = int(labels.sum())
    captured = int(((labels == 1) & promoted).sum())
    return captured, fraud, int(zeros.sum())


def fit_one(spec_path: Path) -> None:
    spec = load_rule(spec_path)
    print(f"columns={','.join(spec['columns'])} percentile={spec['percentile']}", flush=True)
    model = fit_rows(spec["columns"])
    captured, fraud, zeros = score_holdout(model, spec["columns"], spec["percentile"])
    print(f"2023 zero-group top slice fraud={captured}/{fraud} zeros={zeros}", flush=True)
    db = {"candidates": []}
    if DB_PATH.is_file():
        db = json.loads(DB_PATH.read_text(encoding="utf-8"))
    db.setdefault("candidates", []).append({
        "spec": spec_path.name,
        "select_captured": captured,
        "select_fraud": fraud,
        "zeros": zeros,
        "confirm": "skipped",
    })
    DB_PATH.write_text(json.dumps(db, indent=2), encoding="utf-8")
    NOTE_PATH.write_text(
        "\n".join([
            CAVEAT,
            f"spec={spec_path.name}",
            f"2023 zero-group fraud={captured}/{fraud}",
            "confirm=skipped",
            "2024 column files are not on disk, so this count is the 2023 selection year.",
            RESEMBLANCE,
        ]) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> None:
    args = argv or sys.argv[1:]
    if len(args) == 2 and args[0] == "fit":
        fit_one(Path(args[1]))
        return
    raise SystemExit("usage: py -3.14 scripts/zero_rank.py fit models/zero_rules/NN.json")


if __name__ == "__main__":
    main()

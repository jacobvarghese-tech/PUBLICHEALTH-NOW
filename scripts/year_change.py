"""Rank 2024 rows by how far they moved from their own prior years.

Every current loop scores one year by itself. A provider who looks
ordinary in 2024 can still be unusual against their own 2022 and 2023
billing. This script uses the rolled files already on disk. It does not
download and does not fit a forest. The page forest stays frozen.

The cutoff is the percentile of all 2024 rows. The fraud count is taken
after that cutoff is fixed. A high score means resemblance to later
fraud-type exclusions. It is not a finding that the firm committed fraud.
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

from scripts.feature_islands import PAPER_DIR  # noqa: E402
from scripts.model_islands import LEIE_PATH, share  # noqa: E402
from scripts.paper_forest import earliest_exclusion_years, label_for_row, load_year  # noqa: E402

NOTE_PATH = REPO_ROOT / "models" / "year_change_note.txt"
DB_PATH = REPO_ROOT / "models" / "year_change_db.json"
FIELDS = (
    "line_srvc_cnt_sum",
    "bene_unique_cnt_sum",
    "average_submitted_chrg_amt_mean",
    "average_medicare_payment_amt_mean",
)
BENE_DAY_FIELDS = (
    "bene_day_srvc_cnt_sum",
    "bene_unique_cnt_sum",
)
SPREAD_FIELDS = (
    "line_srvc_cnt_std",
    "bene_unique_cnt_std",
)
MEDIAN_FIELDS = (
    "line_srvc_cnt_median",
    "bene_unique_cnt_median",
)
KEYS = ["provider_type", "npi", "nppes_provider_gender"]
RESEMBLANCE = (
    "A high score means resemblance to later fraud-type exclusions. "
    "It is not a finding that the firm committed fraud."
)


def change_score(current: pd.DataFrame, prior: pd.DataFrame, fields: list[str]) -> np.ndarray:
    """Absolute change from the provider's own prior row, ranked inside specialty."""
    left = current.loc[:, KEYS + fields].copy()
    right = prior.loc[:, KEYS + fields].copy()
    for frame in (left, right):
        frame["npi"] = frame["npi"].astype(str).str.strip()
        for field in fields:
            frame[field] = pd.to_numeric(frame[field], errors="coerce").fillna(0.0)
    merged = left.merge(right, on=KEYS, how="left", suffixes=("", "_prior"))
    if len(merged) != len(left):
        raise RuntimeError("prior join changed the row count")
    pieces = []
    for field in fields:
        prior_values = merged[f"{field}_prior"]
        moved = (merged[field] - prior_values).abs()
        moved = moved.where(prior_values.notna(), 0.0)
        rank = moved.groupby(merged["provider_type"]).rank(pct=True, method="average")
        pieces.append(rank.fillna(0.0).to_numpy(dtype=np.float32))
    return np.vstack(pieces).max(axis=0)


def score_one(fields: list[str], prior_year: int) -> tuple[int, int, int]:
    current = load_year(PAPER_DIR / "2024.csv")
    prior = load_year(PAPER_DIR / f"{prior_year}.csv")
    scores = change_score(current, prior, fields)
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    labels = [label_for_row(2024, npi, exclusion_years) for npi in current["npi"].astype(str)]
    top1, fraud = share(scores, labels, 99)
    top5, _fraud = share(scores, labels, 95)
    return top1, top5, fraud


def main(argv: list[str] | None = None) -> None:
    args = argv or sys.argv[1:]
    prior_year = int(args[0]) if args else 2023
    if prior_year < 2016 or prior_year > 2023:
        raise SystemExit("prior year must be 2016-2023")
    field_sets = [
        list(FIELDS),
        ["line_srvc_cnt_sum", "bene_unique_cnt_sum"],
        ["average_submitted_chrg_amt_mean", "average_medicare_payment_amt_mean"],
        list(BENE_DAY_FIELDS),
        list(SPREAD_FIELDS),
        list(MEDIAN_FIELDS),
    ]
    rows = []
    best = 0
    for fields in field_sets:
        top1, top5, fraud = score_one(fields, prior_year)
        name = "+".join(field.replace("_mean", "").replace("_sum", "") for field in fields)
        print(f"prior={prior_year} fields={name} top1={top1}/{fraud} top5={top5}/{fraud}", flush=True)
        rows.append({"prior_year": prior_year, "fields": fields, "confirm_top1": top1, "confirm_top5": top5})
        best = max(best, top1)
    db = {"candidates": rows}
    if DB_PATH.is_file():
        saved = json.loads(DB_PATH.read_text(encoding="utf-8"))
        db["candidates"] = list(saved.get("candidates") or []) + rows
    DB_PATH.write_text(json.dumps(db, indent=2), encoding="utf-8")
    NOTE_PATH.write_text(
        "\n".join([
            f"prior={prior_year}",
            f"best={best}/48",
            RESEMBLANCE,
        ]) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

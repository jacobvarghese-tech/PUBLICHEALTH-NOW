"""Score a blend of two saved forests on 2024.

The blend is the average of the two ranked scores. This does not fit a
forest and does not replace models/paper_forest.joblib. A high score means
resemblance to later fraud-type exclusions. It is not a finding that the
firm committed fraud.
"""

from pathlib import Path

import joblib

import numpy as np

from scripts.join_labels import earliest_exclusion_years
from scripts.model_islands import LEIE_PATH, PAPER_DIR, share
from scripts.optimized_rank import zero_tie_break
from scripts.paper_forest import label_for_row, load_year, score_year

ROOT = Path(__file__).resolve().parents[1]
LEFT = ROOT / "models" / "candidates" / "357.joblib"
RIGHT = ROOT / "models" / "candidates" / "247.joblib"


def main() -> None:
    frame = load_year(PAPER_DIR / "2024.csv")
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    labels = [
        label_for_row(2024, npi, exclusion_years)
        for npi in frame["npi"].astype(str)
    ]
    left_model = joblib.load(LEFT)
    right_model = joblib.load(RIGHT)
    left = left_model.score_year(PAPER_DIR / "2024.csv")
    right = right_model.score_year(PAPER_DIR / "2024.csv")
    averaged = (left + right) / 2
    top1, fraud = share(averaged, labels, 99)
    top5, _fraud = share(averaged, labels, 95)
    print(f"average 357+247 top1={top1}/{fraud} top5={top5}/{fraud}", flush=True)
    peaked = np.maximum(left, right)
    top1, fraud = share(peaked, labels, 99)
    top5, _fraud = share(peaked, labels, 95)
    cutoff = float(np.percentile(peaked, 99))
    in_slice = int(np.sum(peaked >= cutoff))
    print(
        f"max rank 357+247 top1={top1}/{fraud} top5={top5}/{fraud} "
        f"cutoff={cutoff:.6f} rows_at_or_above={in_slice}",
        flush=True,
    )
    primary = score_year(
        left_model.primary_model,
        list(left_model.primary_columns),
        frame,
        chunk=40_000,
    )
    left_second = score_year(
        left_model.secondary_model,
        list(left_model.secondary_columns),
        frame,
        chunk=40_000,
    )
    right_second = score_year(
        right_model.secondary_model,
        list(right_model.secondary_columns),
        frame,
        chunk=40_000,
    )
    combined = zero_tie_break(primary, np.maximum(left_second, right_second))
    top1, fraud = share(combined, labels, 99)
    top5, _fraud = share(combined, labels, 95)
    print(f"max secondary 357+247 top1={top1}/{fraud} top5={top5}/{fraud}", flush=True)


if __name__ == "__main__":
    main()

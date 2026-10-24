"""Score the max of every saved pair on 2024.

A pair is the higher ranked score of two saved forests. This does not fit
and does not write a model file. A high score means resemblance to later
fraud-type exclusions. It is not a finding that the firm committed fraud.
"""

from itertools import combinations
from pathlib import Path

import joblib
import numpy as np

from scripts.join_labels import earliest_exclusion_years
from scripts.model_islands import LEIE_PATH, PAPER_DIR, share
from scripts.paper_forest import label_for_row, load_year

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "models" / "candidates"
NAMES = ("357.joblib", "247.joblib", "307.joblib", "22.joblib", "17.joblib")


def main() -> None:
    frame = load_year(PAPER_DIR / "2024.csv")
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    labels = [
        label_for_row(2024, npi, exclusion_years)
        for npi in frame["npi"].astype(str)
    ]
    ranks = {name: joblib.load(CANDIDATES / name).score_year(PAPER_DIR / "2024.csv") for name in NAMES}
    for name, scores in ranks.items():
        top1, fraud = share(scores, labels, 99)
        print(f"alone {name} top1={top1}/{fraud}", flush=True)
    best_name = ""
    best_top1 = 0
    for left, right in combinations(NAMES, 2):
        peaked = np.maximum(ranks[left], ranks[right])
        top1, fraud = share(peaked, labels, 99)
        if top1 > best_top1:
            best_top1 = top1
            best_name = f"{left}+{right}"
        print(f"max {left}+{right} top1={top1}/{fraud}", flush=True)
    trio = np.maximum(ranks["357.joblib"], np.maximum(ranks["247.joblib"], ranks["307.joblib"]))
    top1, fraud = share(trio, labels, 99)
    print(f"max 357+247+307 top1={top1}/{fraud}", flush=True)
    print(f"best pair {best_name} top1={best_top1}", flush=True)


if __name__ == "__main__":
    main()

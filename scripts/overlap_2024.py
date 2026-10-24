"""Score the saved forests on 2024 and compare which fraud rows they miss.

This reads models/candidates and the 2024 rolled year. It does not fit and
it does not write a model file.
"""

from pathlib import Path

import joblib
import numpy as np

from scripts.join_labels import earliest_exclusion_years
from scripts.model_islands import LEIE_PATH, PAPER_DIR, share
from scripts.paper_forest import label_for_row, load_year

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "models" / "candidates"
NAMES = ("307.joblib", "357.joblib", "247.joblib", "22.joblib", "17.joblib")


def top_mask(scores: np.ndarray, percentile: float = 99) -> np.ndarray:
    cutoff = float(np.percentile(scores, percentile))
    return scores >= cutoff


def main() -> None:
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    frame = load_year(PAPER_DIR / "2024.csv")
    labels = np.array(
        [label_for_row(2024, npi, exclusion_years) for npi in frame["npi"].astype(str)],
        dtype=np.int8,
    )
    fraud_index = np.flatnonzero(labels == 1)
    print(f"2024 rows={len(labels)} fraud={len(fraud_index)}", flush=True)
    captured: dict[str, set[int]] = {}
    for name in NAMES:
        path = CANDIDATES / name
        payload = joblib.load(path)
        scores = payload.score_year(PAPER_DIR / "2024.csv")
        top1, fraud = share(scores, labels.tolist(), 99)
        mask = top_mask(scores)
        hits = {int(index) for index in fraud_index if mask[index]}
        captured[name] = hits
        print(f"{name} top1={top1}/{fraud} captured={len(hits)}", flush=True)
        del payload, scores
    names = list(captured)
    for left in range(len(names)):
        for right in range(left + 1, len(names)):
            first = captured[names[left]]
            second = captured[names[right]]
            print(
                f"{names[left]} vs {names[right]} both={len(first & second)} "
                f"only_left={len(first - second)} only_right={len(second - first)} "
                f"union={len(first | second)}",
                flush=True,
            )
    union = set.union(*captured.values()) if captured else set()
    print(f"union of saved forests={len(union)} of {len(fraud_index)}", flush=True)


if __name__ == "__main__":
    main()

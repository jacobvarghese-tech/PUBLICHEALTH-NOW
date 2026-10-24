"""Save the max of two saved ranks when it beats the recorded best.

The blend scores a year as the higher of the two saved ranked scores. It
does not fit a forest. models/paper_forest.joblib is not opened for writing.
A high score means resemblance to later fraud-type exclusions. It is not a
finding that the firm committed fraud.
"""

from pathlib import Path

import joblib
import numpy as np

from scripts.join_labels import earliest_exclusion_years
from scripts.model_islands import DB_PATH, LEIE_PATH, PAPER_DIR, load_db, save_db, share
from scripts.paper_forest import label_for_row, load_year

ROOT = Path(__file__).resolve().parents[1]
LEFT_PATH = ROOT / "models" / "candidates" / "357.joblib"
RIGHT_PATH = ROOT / "models" / "candidates" / "247.joblib"
OUT_PATH = ROOT / "models" / "candidates" / "blend_357_247.joblib"


class MaxRankBlend:
    """Higher of two saved ranks. Both objects already contain their forests."""

    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right
        self.parts = ("357.joblib", "247.joblib")

    def score_year(self, path: Path, chunk: int = 40_000) -> np.ndarray:
        left = self.left.score_year(Path(path), chunk=chunk)
        right = self.right.score_year(Path(path), chunk=chunk)
        return np.maximum(left, right)


def main() -> None:
    blend = MaxRankBlend(joblib.load(LEFT_PATH), joblib.load(RIGHT_PATH))
    scores = blend.score_year(PAPER_DIR / "2024.csv")
    frame = load_year(PAPER_DIR / "2024.csv")
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    labels = [
        label_for_row(2024, npi, exclusion_years)
        for npi in frame["npi"].astype(str)
    ]
    top1, fraud = share(scores, labels, 99)
    top5, _fraud = share(scores, labels, 95)
    print(f"blend top1={top1}/{fraud} top5={top5}/{fraud}", flush=True)
    db = load_db()
    best = int(db.get("best_confirm_top1") or 0)
    if top1 <= best:
        print(f"not saved; best is {best}", flush=True)
        return
    joblib.dump(blend, OUT_PATH)
    record = {
        "spec": "blend_357_247.joblib",
        "select_top1": None,
        "select_top5": None,
        "kept": True,
        "confirm_top1": top1,
        "confirm_top5": top5,
        "note": "max of ranked scores from 357 and 247; no new fit",
    }
    db.setdefault("candidates", []).append(record)
    db["best_confirm_top1"] = top1
    db["best_spec"] = "blend_357_247.joblib"
    save_db(db)
    print(f"saved {OUT_PATH.name} best {top1}", flush=True)


if __name__ == "__main__":
    main()

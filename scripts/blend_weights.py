"""Try weights of the two forests that already score 26 of 48.

The saved best is the max of spec 357 and spec 247. This script tries
weighted averages of those two ranked scores. It does not fit and does
not download. A weight is saved only when the 2024 top 1 percent count
is higher than the saved best. The page forest stays frozen.

A high score means resemblance to later fraud-type exclusions. It is not
a finding that the firm committed fraud.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.blend_search import ranked, save_record  # noqa: E402
from scripts.model_islands import DB_PATH, LEIE_PATH, PAPER_DIR, share  # noqa: E402
from scripts.paper_forest import earliest_exclusion_years, label_for_row, load_year  # noqa: E402

NOTE_PATH = REPO_ROOT / "models" / "blend_weights_note.txt"
CANDIDATE_DIR = REPO_ROOT / "models" / "candidates"
WEIGHTS = (0.2, 0.4, 0.5, 0.6, 0.8)
RESEMBLANCE = (
    "A high score means resemblance to later fraud-type exclusions. "
    "It is not a finding that the firm committed fraud."
)


def main() -> None:
    frame = load_year(PAPER_DIR / "2024.csv")
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    labels = [label_for_row(2024, npi, exclusion_years) for npi in frame["npi"].astype(str)]
    left = ranked(joblib.load(CANDIDATE_DIR / "357.joblib"), frame)
    right = ranked(joblib.load(CANDIDATE_DIR / "247.joblib"), frame)
    db = json.loads(DB_PATH.read_text(encoding="utf-8")) if DB_PATH.is_file() else {}
    best = int(db.get("best_confirm_top1") or 26)
    kept = "none"
    for weight in WEIGHTS:
        scores = weight * left + (1.0 - weight) * right
        top1, fraud = share(scores, labels, 99)
        top5, _fraud = share(scores, labels, 95)
        print(f"weight={weight:.1f} top1={top1}/{fraud} top5={top5}/{fraud}", flush=True)
        if top1 > best:
            best = top1
            kept = f"{weight:.1f}"
            out = CANDIDATE_DIR / f"blend_w_{int(weight * 10)}.joblib"
            joblib.dump({"left": "357", "right": "247", "weight": weight}, out)
            save_record(out.name, top1, top5, out)
    rank_sum = np.argsort(np.argsort(left)).astype(float) + np.argsort(np.argsort(right)).astype(float)
    top1, fraud = share(rank_sum, labels, 99)
    top5, _fraud = share(rank_sum, labels, 95)
    print(f"rank_sum top1={top1}/{fraud} top5={top5}/{fraud}", flush=True)
    if top1 > best:
        best = top1
        kept = "rank_sum"
        out = CANDIDATE_DIR / "blend_rank_sum.joblib"
        joblib.dump({"left": "357", "right": "247", "rule": "rank_sum"}, out)
        save_record(out.name, top1, top5, out)
    NOTE_PATH.write_text("\n".join([f"best={best}/48", f"kept={kept}", RESEMBLANCE]) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

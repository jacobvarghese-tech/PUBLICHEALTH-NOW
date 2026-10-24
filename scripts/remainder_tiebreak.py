"""Use prior-year change only on rows the 26-score blend leaves below the cutoff.

Year-over-year change alone placed 4 of 48. This script asks a narrower
question: among 2024 rows that both saved forests leave below the top
1 percent, does the change from 2023 put any fraud row into that slice
without pulling the cutoff down to zero. It does not fit and does not
download. The page forest stays frozen.

A high score means resemblance to later fraud-type exclusions. It is not
a finding that the firm committed fraud.
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.blend_search import ranked  # noqa: E402
from scripts.model_islands import LEIE_PATH, share  # noqa: E402
from scripts.paper_forest import earliest_exclusion_years, label_for_row, load_year  # noqa: E402
from scripts.year_change import (  # noqa: E402
    BENE_DAY_FIELDS,
    FIELDS,
    MEDIAN_FIELDS,
    PAPER_DIR,
    SPREAD_FIELDS,
    change_score,
)

NOTE_PATH = REPO_ROOT / "models" / "remainder_note.txt"
CANDIDATE_DIR = REPO_ROOT / "models" / "candidates"
RESEMBLANCE = (
    "A high score means resemblance to later fraud-type exclusions. "
    "It is not a finding that the firm committed fraud."
)


FIELD_SETS = {
    "main": list(FIELDS),
    "bene_day": list(BENE_DAY_FIELDS),
    "spread": list(SPREAD_FIELDS),
    "median": list(MEDIAN_FIELDS),
}


def main(argv: list[str] | None = None) -> None:
    args = argv or sys.argv[1:]
    prior_year = int(args[0]) if args else 2023
    field_name = args[1] if len(args) > 1 else "main"
    if prior_year < 2016 or prior_year > 2023:
        raise SystemExit("prior year must be 2016-2023")
    if field_name not in FIELD_SETS:
        raise SystemExit("field set must be main, bene_day, spread, or median")
    current = load_year(PAPER_DIR / "2024.csv")
    prior = load_year(PAPER_DIR / f"{prior_year}.csv")
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    labels = [label_for_row(2024, npi, exclusion_years) for npi in current["npi"].astype(str)]
    left = ranked(joblib.load(CANDIDATE_DIR / "357.joblib"), current)
    right = ranked(joblib.load(CANDIDATE_DIR / "247.joblib"), current)
    peaked = np.maximum(left, right)
    cutoff = float(np.percentile(peaked, 99))
    below = peaked < cutoff
    moved = change_score(current, prior, FIELD_SETS[field_name])
    # A row already in the slice keeps its score. A row below gets a score
    # under the cutoff, ordered by how far it moved from its own prior year.
    span = cutoff if cutoff > 0 else 1.0
    promoted = np.where(below, moved * span * 0.5, peaked)
    top1, fraud = share(promoted, labels, 99)
    top5, _fraud = share(promoted, labels, 95)
    base1, _fraud = share(peaked, labels, 99)
    print(
        f"prior={prior_year} fields={field_name} blend={base1}/{fraud} "
        f"remainder top1={top1}/{fraud} top5={top5}/{fraud} cutoff={cutoff:.6f}",
        flush=True,
    )
    NOTE_PATH.write_text(
        "\n".join([
            f"prior={prior_year}",
            f"fields={field_name}",
            f"blend={base1}/{fraud}",
            f"remainder={top1}/{fraud}",
            RESEMBLANCE,
        ]) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

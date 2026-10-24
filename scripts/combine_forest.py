"""Refit the 25/48 forest with line-level columns already on disk.

Spec 357 won on the thirty billing summaries. This script keeps those tree
settings and adds columns from data/feature_columns. It does not download.
A year whose column file is missing is left out of the fit. 2023 and 2024
never enter the fit. The page forest stays frozen.

A candidate is saved only when the 2024 top 1 percent count is higher than
the saved best of 25 of 48. A high score means resemblance to later
fraud-type exclusions. It is not a finding that the firm committed fraud.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.column_pack import fit_one  # noqa: E402

WINNER = REPO_ROOT / "models" / "specs" / "357.json"


def main(argv: list[str] | None = None) -> None:
    args = argv or sys.argv[1:]
    if len(args) == 2 and args[0] == "fit":
        path = Path(args[1])
        spec = json.loads(path.read_text(encoding="utf-8"))
        winner = json.loads(WINNER.read_text(encoding="utf-8"))
        for key in ("n_estimators", "max_depth", "min_samples_leaf", "class_weight", "clean_per_fraud"):
            if spec.get(key) != winner.get(key):
                raise SystemExit(f"{path.name} {key} differs from models/specs/357.json")
        years = [int(year) for year in spec.get("fit_years") or []]
        if any(year < 2016 or year > 2022 for year in years):
            raise SystemExit("fit years must stay inside 2016-2022")
        fit_one(path)
        return
    raise SystemExit("usage: py -3.14 scripts/combine_forest.py fit models/column_packs/NN.json")


if __name__ == "__main__":
    main()

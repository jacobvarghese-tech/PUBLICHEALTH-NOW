"""Blend saved forests on 2024. Does not fit and does not download.

The current best is the max of spec 357 and spec 247. This script tries
the other saved forests against those two. A candidate file is written
only when the 2024 top 1 percent count is higher than the saved best.
The page forest stays frozen.

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

from scripts.model_islands import DB_PATH, LEIE_PATH, PAPER_DIR, share  # noqa: E402
from scripts.optimized_rank import zero_tie_break  # noqa: E402
from scripts.paper_forest import earliest_exclusion_years, label_for_row, load_year, score_year  # noqa: E402

CANDIDATE_DIR = REPO_ROOT / "models" / "candidates"
NOTE_PATH = REPO_ROOT / "models" / "blend_search_note.txt"
SAVED = ("357", "247", "307", "22", "17")
RESEMBLANCE = (
    "A high score means resemblance to later fraud-type exclusions. "
    "It is not a finding that the firm committed fraud."
)


def load_db() -> dict:
    if not DB_PATH.is_file():
        return {"candidates": []}
    return json.loads(DB_PATH.read_text(encoding="utf-8"))


def save_record(name: str, top1: int, top5: int, path: Path) -> None:
    db = load_db()
    db.setdefault("candidates", []).append({
        "spec": name,
        "select_top1": None,
        "select_top5": None,
        "kept": True,
        "confirm_top1": top1,
        "confirm_top5": top5,
        "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "note": "max of ranked scores; no new fit",
    })
    db["best_confirm_top1"] = top1
    db["best_spec"] = name
    DB_PATH.write_text(json.dumps(db, indent=2), encoding="utf-8")


def ranked(model, frame) -> np.ndarray:
    primary = score_year(model.primary_model, list(model.primary_columns), frame, chunk=40_000)
    secondary = score_year(model.secondary_model, list(model.secondary_columns), frame, chunk=40_000)
    return zero_tie_break(primary, secondary)


def score_pair(left_name: str, right_name: str, frame, labels, models: dict) -> tuple[int, int, int]:
    peaked = np.maximum(models[left_name], models[right_name])
    top1, fraud = share(peaked, labels, 99)
    top5, _fraud = share(peaked, labels, 95)
    return top1, top5, fraud


def main(argv: list[str] | None = None) -> None:
    args = argv or sys.argv[1:]
    names = list(SAVED)
    if len(args) == 2:
        names = [args[0], args[1]]
    frame = load_year(PAPER_DIR / "2024.csv")
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    labels = [label_for_row(2024, npi, exclusion_years) for npi in frame["npi"].astype(str)]
    loaded = {}
    models = {}
    for name in names:
        path = CANDIDATE_DIR / f"{name}.joblib"
        if not path.is_file():
            print(f"skip missing {path.name}", flush=True)
            continue
        loaded[name] = joblib.load(path)
        models[name] = ranked(loaded[name], frame)
        print(f"scored {name}", flush=True)
    db = load_db()
    best = int(db.get("best_confirm_top1") or 26)
    best_pair = ""
    for left in list(models):
        for right in list(models):
            if left >= right:
                continue
            top1, top5, fraud = score_pair(left, right, frame, labels, models)
            print(f"max {left}+{right} top1={top1}/{fraud} top5={top5}/{fraud}", flush=True)
            if top1 > best:
                best = top1
                best_pair = f"{left}+{right}"
                out = CANDIDATE_DIR / f"blend_{left}_{right}.joblib"
                joblib.dump({"left": left, "right": right, "rule": "max"}, out)
                save_record(out.name, top1, top5, out)
    lines = [
        f"best={best}/48",
        f"new_pair={best_pair or 'none'}",
        RESEMBLANCE,
    ]
    NOTE_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

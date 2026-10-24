"""Blend each new saved forest into the current best until 6:00 a.m.

A pair is the higher ranked score of the current best and one saved forest.
The pair is saved only when the 2024 top 1 percent count rises. The page
forest is not opened for writing. A high score means resemblance to later
fraud-type exclusions. It is not a finding that the firm committed fraud.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import joblib
import numpy as np

from scripts.work_clock import load_stop
from scripts.join_labels import earliest_exclusion_years
from scripts.model_islands import LEIE_PATH, PAPER_DIR, load_db, save_db, share
from scripts.paper_forest import label_for_row, load_year

CANDIDATES = ROOT / "models" / "candidates"
TRIED_PATH = ROOT / "models" / "grow_tried.json"
WAIT_SECONDS = 120
SKIP_NAMES = {"paper_forest.joblib", "optimized_model.joblib"}


class MaxRankBlend:
    """Higher ranked score of the current best and one saved forest."""

    def __init__(self, left, right, parts: tuple[str, ...]) -> None:
        self.left = left
        self.right = right
        self.parts = parts

    def score_year(self, path: Path, chunk: int = 40_000) -> np.ndarray:
        left = self.left.score_year(Path(path), chunk=chunk)
        right = self.right.score_year(Path(path), chunk=chunk)
        return np.maximum(left, right)


def labels_2024() -> list[int]:
    frame = load_year(PAPER_DIR / "2024.csv")
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    return [
        label_for_row(2024, npi, exclusion_years)
        for npi in frame["npi"].astype(str)
    ]


def tried() -> set[str]:
    if not TRIED_PATH.exists():
        return set()
    payload = json.loads(TRIED_PATH.read_text(encoding="utf-8"))
    return set(payload.get("parts") or [])


def mark_tried(parts: tuple[str, ...]) -> None:
    seen = tried()
    seen.add("+".join(parts))
    TRIED_PATH.write_text(
        json.dumps({"parts": sorted(seen)}, indent=2) + "\n",
        encoding="utf-8",
    )


def parts_of(path: Path, model) -> tuple[str, ...]:
    recorded = getattr(model, "parts", None)
    if recorded:
        return tuple(str(name) for name in recorded)
    return (path.name,)


def new_forests(current_parts: tuple[str, ...]) -> list[Path]:
    found = []
    for path in sorted(CANDIDATES.glob("*.joblib")):
        if path.name in SKIP_NAMES or path.name.startswith("blend_"):
            continue
        if path.name in current_parts:
            continue
        found.append(path)
    return found


def next_untried(current_parts: tuple[str, ...]) -> Path | None:
    seen = tried()
    for path in new_forests(current_parts):
        parts = tuple(sorted(set(current_parts) | {path.name}))
        if "+".join(parts) not in seen:
            return path
    return None


def one_pass(labels: list[int]) -> str:
    """Score one untried pair. Return saved, tried, or waiting."""
    db = load_db()
    best = int(db.get("best_confirm_top1") or 0)
    best_name = str(db.get("best_spec") or "")
    best_path = CANDIDATES / best_name
    if not best_path.exists():
        print(f"STOP missing best {best_name}", flush=True)
        return "stopped"
    current = joblib.load(best_path)
    current_parts = parts_of(best_path, current)
    path = next_untried(current_parts)
    if path is None:
        return "waiting"
    parts = tuple(sorted(set(current_parts) | {path.name}))
    added = joblib.load(path)
    blend = MaxRankBlend(current, added, parts)
    scores = blend.score_year(PAPER_DIR / "2024.csv")
    top1, fraud = share(scores, labels, 99)
    top5, _fraud = share(scores, labels, 95)
    print(f"max {'+'.join(parts)} top1={top1}/{fraud} best={best}", flush=True)
    mark_tried(parts)
    if top1 <= best:
        return "tried"
    out_name = "blend_" + "_".join(name.replace(".joblib", "") for name in parts) + ".joblib"
    out = CANDIDATES / out_name
    joblib.dump(blend, out)
    db.setdefault("candidates", []).append(
        {
            "spec": out_name,
            "select_top1": None,
            "select_top5": None,
            "kept": True,
            "confirm_top1": top1,
            "confirm_top5": top5,
            "note": "max of ranked scores from " + "+".join(parts) + "; no new fit",
        }
    )
    db["best_confirm_top1"] = top1
    db["best_spec"] = out_name
    save_db(db)
    print(f"SAVED {out_name} top1={top1}/{fraud}", flush=True)
    return "saved"


def main() -> None:
    stop = load_stop()
    print(f"clock {stop:%Y-%m-%d %H:%M}", flush=True)
    labels = labels_2024()
    while datetime.now() < stop:
        status = one_pass(labels)
        if status == "stopped":
            return
        if status == "waiting":
            print("WAIT for a new saved forest", flush=True)
            time.sleep(WAIT_SECONDS)
    print("STOP clock", flush=True)


if __name__ == "__main__":
    main()

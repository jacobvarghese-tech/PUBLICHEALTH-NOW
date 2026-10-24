"""Fit the unused neighbors of the current best until the working stop.

One fit at a time. A spec is skipped when the database already has its
confirm_top1. The page forest is not opened for writing. The stop is
6:00 a.m. local on 2026-10-24, read from models/work_clock.json.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.work_clock import load_stop, past_stop

SPEC_DIR = ROOT / "models" / "specs"
DB_PATH = ROOT / "models" / "model_island_db.json"
PYTHON = sys.executable

# Column share each tree sees. sqrt is the already-scored default.
FEATURES = ("log2", 0.3, 0.5, 0.7, "all")


def scored() -> set[str]:
    if not DB_PATH.exists():
        return set()
    db = json.loads(DB_PATH.read_text(encoding="utf-8"))
    return {
        str(row.get("spec") or "")
        for row in db.get("candidates") or []
        if row.get("confirm_top1") is not None
    }


def already_fitting(name: str) -> bool:
    """True when another process already has this spec open."""
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process -Filter \"Name = 'python.exe'\" | "
            "Where-Object { $_.CommandLine -match 'model_islands.py fit' } | "
            "ForEach-Object { $_.CommandLine }",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return name in result.stdout


def next_free_id() -> int:
    used = [int(path.stem) for path in SPEC_DIR.glob("*.json") if path.stem.isdigit()]
    return max(used or [509]) + 1


def write_spec(spec_id: int, features: str | float) -> Path:
    path = SPEC_DIR / f"{spec_id}.json"
    payload = {
        "n_estimators": 20,
        "max_depth": 24,
        "min_samples_leaf": 1,
        "class_weight": "none",
        "clean_per_fraud": 10,
        "fit_years": [2019, 2020, 2021, 2022],
        "max_features": features,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def planned() -> list[Path]:
    spec_id = next_free_id()
    return [write_spec(spec_id + offset, features) for offset, features in enumerate(FEATURES)]


def fit(path: Path) -> int:
    print(f"START {path.name} {datetime.now():%H:%M:%S}", flush=True)
    result = subprocess.run(
        [PYTHON, "scripts/model_islands.py", "fit", str(path.relative_to(ROOT))],
        cwd=ROOT,
    )
    print(f"EXIT {path.name} {result.returncode} {datetime.now():%H:%M:%S}", flush=True)
    return result.returncode


def main() -> None:
    stop = load_stop()
    print(f"clock {stop:%Y-%m-%d %H:%M}", flush=True)
    done = scored()
    while not past_stop():
        nxt = next_unscored(done)
        if nxt is None or already_fitting(nxt.name):
            print("REFILL", flush=True)
            for path in planned():
                if path.name not in done:
                    nxt = path
                    break
        if nxt is None or past_stop() or already_fitting(nxt.name):
            print("STOP clock" if past_stop() else "HELD fit already running", flush=True)
            return
        fit(nxt)
        done = scored()
    print("STOP clock", flush=True)


def next_unscored(done: set[str]) -> Path | None:
    paths = sorted(
        (path for path in SPEC_DIR.glob("*.json") if path.stem.isdigit()),
        key=lambda path: int(path.stem),
    )
    for path in paths:
        if int(path.stem) < 610:
            continue
        if path.name not in done:
            return path
    return None


if __name__ == "__main__":
    main()

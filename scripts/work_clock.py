"""Local working stop for the overnight search.

The contest clocks stay in AGENTS.md. This file is the clock the scoring
loops read. A missing or unreadable file falls back to 6:00 a.m. local
on 2026-10-24.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLOCK_PATH = ROOT / "models" / "work_clock.json"
FALLBACK = datetime(2026, 10, 24, 6, 0, 0)


def load_stop(path: Path | None = None) -> datetime:
    """Return the local stop. A bad file uses the 6:00 a.m. fallback."""
    clock = path or CLOCK_PATH
    try:
        payload = json.loads(clock.read_text(encoding="utf-8"))
        stamp = str(payload["stop_at"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return FALLBACK
    try:
        return datetime.fromisoformat(stamp)
    except ValueError:
        return FALLBACK


def past_stop(now: datetime | None = None, path: Path | None = None) -> bool:
    return (now or datetime.now()) >= load_stop(path)

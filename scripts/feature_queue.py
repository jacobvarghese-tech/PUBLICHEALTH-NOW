"""Fit feature specs 07 through 12, one at a time, until the work clock.

A spec that is already running is left alone. The page forest is not opened
for writing. A high score means resemblance to later fraud-type exclusions.
It is not a finding that the firm committed fraud.
"""

from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.work_clock import load_stop

SPECS = [f"{number:02d}.json" for number in range(7, 13)]


def any_feature_fit() -> bool:
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process -Filter \"Name = 'python.exe'\" | "
            "Where-Object { $_.CommandLine -match 'feature_islands.py fit' } | "
            "ForEach-Object { $_.CommandLine }",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return "feature_islands.py fit" in result.stdout


def already_fitting(name: str) -> bool:
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process -Filter \"Name = 'python.exe'\" | "
            "Where-Object { $_.CommandLine -match 'feature_islands.py fit' } | "
            "ForEach-Object { $_.CommandLine }",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return name in result.stdout


def fit(name: str) -> int:
    print(f"START {name} {datetime.now():%H:%M:%S}", flush=True)
    result = subprocess.run(
        [sys.executable, "-u", "scripts/feature_islands.py", "fit", f"models/feature_specs/{name}"],
        cwd=ROOT,
    )
    print(f"EXIT {name} {result.returncode} {datetime.now():%H:%M:%S}", flush=True)
    return result.returncode


def main() -> None:
    stop = load_stop()
    print(f"clock {stop:%Y-%m-%d %H:%M}", flush=True)
    pending = list(SPECS)
    while pending and datetime.now() < stop:
        if any_feature_fit():
            print(f"WAIT {pending[0]} another feature fit is running", flush=True)
            time.sleep(120)
            continue
        name = pending.pop(0)
        fit(name)
    if datetime.now() >= stop:
        print("STOP clock", flush=True)
        return
    print("STOP feature queue empty", flush=True)


if __name__ == "__main__":
    main()

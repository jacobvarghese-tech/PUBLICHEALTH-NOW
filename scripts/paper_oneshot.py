"""Run the paper comparison fit one year at a time, then fit.

Skips a year whose rolled file and count already exist. Resumes a partial
download. Stops on a byte-count mismatch. Writes models/paper_replicate.json.
Does not edit the saved XGBoost files, data/rolled/, or app/.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from paper_roll_year import record_2012_gap, year_done  # noqa: E402

ROLLED = ROOT / "data" / "paper_rolled"
YEARS = (2013, 2014, 2015)


def run(script: str, args: list[str]) -> None:
    command = [sys.executable, "-u", str(ROOT / "scripts" / script), *args]
    print("RUN " + " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> None:
    record_2012_gap(ROLLED)
    print("gap year=2012 recorded; no data URL invented", flush=True)
    for year in YEARS:
        if year_done(year):
            print(f"skip year={year} already rolled", flush=True)
            continue
        run("paper_roll_year.py", ["--year", str(year)])
        if not year_done(year):
            raise SystemExit(f"year {year} did not write a rolled file")
    run("paper_fit.py", [])
    out = ROOT / "models" / "paper_replicate.json"
    if not out.is_file():
        raise SystemExit("models/paper_replicate.json was not written")
    print(f"DONE {out}", flush=True)


if __name__ == "__main__":
    main()

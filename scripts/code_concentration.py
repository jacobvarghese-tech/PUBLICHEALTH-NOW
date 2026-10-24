"""Score 2024 by how concentrated each provider's procedure codes are.

Distinct code count says how many codes were billed. It does not say
whether the services sat on one code. This script reads the line store
feature_islands.py already built. It does not download. A year whose
store is missing is skipped. The page forest stays frozen.

The cutoff is the percentile of all scored rows. The fraud count is
taken after that cutoff is fixed. A high score means resemblance to
later fraud-type exclusions. It is not a finding that the firm
committed fraud.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.feature_islands import PAPER_DIR, RAW_DIR  # noqa: E402
from scripts.model_islands import LEIE_PATH, share  # noqa: E402
from scripts.paper_forest import earliest_exclusion_years, label_for_row, load_year  # noqa: E402

NOTE_PATH = REPO_ROOT / "models" / "code_concentration_note.txt"
DB_PATH = REPO_ROOT / "models" / "code_concentration_db.json"
RESEMBLANCE = (
    "A high score means resemblance to later fraud-type exclusions. "
    "It is not a finding that the firm committed fraud."
)


def store_path(year: int) -> Path:
    return RAW_DIR / f"feature_island_{year}.sqlite"


def concentration(year: int) -> pd.DataFrame:
    path = store_path(year)
    if not path.is_file():
        raise FileNotFoundError(f"missing line store {path.name}")
    with sqlite3.connect(path) as conn:
        frame = pd.read_sql_query(
            """
            SELECT provider_type, npi, gender AS nppes_provider_gender,
                   SUM(services) AS services,
                   SUM(services * services) AS service_squares,
                   COUNT(DISTINCT hcpcs) AS codes
            FROM lines
            GROUP BY provider_type, npi, gender
            """,
            conn,
        )
    services = pd.to_numeric(frame["services"], errors="coerce").fillna(0.0)
    squares = pd.to_numeric(frame["service_squares"], errors="coerce").fillna(0.0)
    frame["top_code_share"] = np.where(services > 0, squares / (services * services), 0.0)
    frame["codes"] = pd.to_numeric(frame["codes"], errors="coerce").fillna(0.0)
    return frame


def score_year(year: int, field: str) -> tuple[int, int, int]:
    rolled = load_year(PAPER_DIR / f"{year}.csv")
    facts = concentration(year)
    keys = ["provider_type", "npi", "nppes_provider_gender"]
    rolled["npi"] = rolled["npi"].astype(str).str.strip()
    facts["npi"] = facts["npi"].astype(str).str.strip()
    merged = rolled.merge(facts.loc[:, keys + [field]], on=keys, how="left")
    if len(merged) != len(rolled):
        raise RuntimeError("line-store join changed the row count")
    values = pd.to_numeric(merged[field], errors="coerce").fillna(0.0)
    scores = values.groupby(merged["provider_type"]).rank(pct=True, method="average").fillna(0.0)
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    labels = [label_for_row(year, npi, exclusion_years) for npi in merged["npi"].astype(str)]
    top1, fraud = share(scores.to_numpy(dtype=float), labels, 99)
    top5, _fraud = share(scores.to_numpy(dtype=float), labels, 95)
    return top1, top5, fraud


def main(argv: list[str] | None = None) -> None:
    args = argv or sys.argv[1:]
    year = int(args[0]) if args else 2023
    if year < 2016 or year > 2024:
        raise SystemExit("year must be 2016-2024")
    rows = []
    for field in ("top_code_share", "codes"):
        top1, top5, fraud = score_year(year, field)
        print(f"year={year} field={field} top1={top1}/{fraud} top5={top5}/{fraud}", flush=True)
        rows.append({"year": year, "field": field, "top1": top1, "top5": top5, "fraud": fraud})
    db = {"candidates": rows}
    if DB_PATH.is_file():
        saved = json.loads(DB_PATH.read_text(encoding="utf-8"))
        db["candidates"] = list(saved.get("candidates") or []) + rows
    DB_PATH.write_text(json.dumps(db, indent=2), encoding="utf-8")
    best = max(row["top1"] for row in rows)
    NOTE_PATH.write_text(
        "\n".join([
            f"year={year}",
            f"best={best}/{rows[0]['fraud']}",
            RESEMBLANCE,
        ]) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

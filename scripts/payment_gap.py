"""Score a year by the gap between allowed amount and payment.

The line store already has allowed and payment. Specs 09 and 10 named
this gap and never wrote it. This script reads the store. It does not
download. A missing store is a skip. The page forest stays frozen.

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

NOTE_PATH = REPO_ROOT / "models" / "payment_gap_note.txt"
DB_PATH = REPO_ROOT / "models" / "payment_gap_db.json"
RESEMBLANCE = (
    "A high score means resemblance to later fraud-type exclusions. "
    "It is not a finding that the firm committed fraud."
)


def gap_frame(year: int) -> pd.DataFrame:
    path = RAW_DIR / f"feature_island_{year}.sqlite"
    if not path.is_file():
        raise FileNotFoundError(f"missing line store {path.name}")
    with sqlite3.connect(path) as conn:
        frame = pd.read_sql_query(
            """
            SELECT provider_type, npi, gender AS nppes_provider_gender,
                   SUM(allowed) AS allowed,
                   SUM(payment) AS payment,
                   SUM(services) AS services
            FROM lines
            GROUP BY provider_type, npi, gender
            """,
            conn,
        )
    allowed = pd.to_numeric(frame["allowed"], errors="coerce").fillna(0.0)
    payment = pd.to_numeric(frame["payment"], errors="coerce").fillna(0.0)
    services = pd.to_numeric(frame["services"], errors="coerce").fillna(0.0)
    frame["gap_per_service"] = np.where(services > 0, (allowed - payment) / services, 0.0)
    frame["payment_ratio"] = np.where(allowed > 0, payment / allowed, 0.0)
    return frame


def score_year(year: int, field: str) -> tuple[int, int, int]:
    rolled = load_year(PAPER_DIR / f"{year}.csv")
    facts = gap_frame(year)
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
    year = int(args[0]) if args else 2019
    rows = []
    for field in ("gap_per_service", "payment_ratio"):
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
        "\n".join([f"year={year}", f"best={best}/{rows[0]['fraud']}", RESEMBLANCE]) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

"""Count fraud-type rows in the OIG LEIE file saved at data/training/UPDATED.csv.

The four codes are the locked exclusion types from the action plan:
1128a1, 1128a3, 1128b6, 1128b7. The count is every data row with one of
those EXCLTYPE values. Rows are not filtered by NPI.
"""

from __future__ import annotations

import csv
from pathlib import Path

FRAUD_EXCLTYPES = frozenset({"1128a1", "1128a3", "1128b6", "1128b7"})
REQUIRED_COLUMNS = ("NPI", "EXCLTYPE", "EXCLDATE")

REPO_ROOT = Path(__file__).resolve().parents[1]
LEIE_PATH = REPO_ROOT / "data" / "training" / "UPDATED.csv"
COUNT_PATH = REPO_ROOT / "data" / "training" / "leie_fraud_row_count.txt"


def count_fraud_rows(csv_path: Path) -> int:
    """Return the number of data rows whose EXCLTYPE is one of the four codes."""
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        missing = [name for name in REQUIRED_COLUMNS if name not in header]
        if missing:
            raise ValueError(f"UPDATED.csv is missing columns: {', '.join(missing)}")
        return sum(
            1
            for row in reader
            if (row.get("EXCLTYPE") or "").strip() in FRAUD_EXCLTYPES
        )


def write_count_file(csv_path: Path = LEIE_PATH, count_path: Path = COUNT_PATH) -> int:
    """Count the saved LEIE file and write that integer beside it."""
    total = count_fraud_rows(csv_path)
    count_path.write_text(
        (
            "Rows in data/training/UPDATED.csv with EXCLTYPE in "
            "1128a1, 1128a3, 1128b6, 1128b7: "
            f"{total}\n"
        ),
        encoding="utf-8",
    )
    return total


def main() -> None:
    total = write_count_file()
    print(total)


if __name__ == "__main__":
    main()

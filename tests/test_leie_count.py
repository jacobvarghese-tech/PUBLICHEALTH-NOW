"""The saved LEIE file and the written fraud-type count must agree."""

from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path

from scripts.count_leie import (
    COUNT_PATH,
    FRAUD_EXCLTYPES,
    LEIE_PATH,
    count_fraud_rows,
)

BILLING_YEAR_NAMES = ("MUP_PHY", "PHY_R26")


def _independent_count(csv_path: Path) -> int:
    """Recount with the stdlib reader. Does not call count_fraud_rows."""
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return sum(
            1
            for row in reader
            if (row.get("EXCLTYPE") or "").strip() in FRAUD_EXCLTYPES
        )


class LeieDownloadTest(unittest.TestCase):
    def test_updated_csv_is_the_leie_file(self) -> None:
        self.assertTrue(LEIE_PATH.is_file(), f"missing {LEIE_PATH}")
        self.assertGreater(LEIE_PATH.stat().st_size, 1000)
        with LEIE_PATH.open(newline="", encoding="utf-8-sig") as handle:
            header = next(csv.reader(handle))
        for column in ("NPI", "EXCLTYPE", "EXCLDATE"):
            self.assertIn(column, header)

    def test_no_billing_year_file_was_saved(self) -> None:
        # Step 2 must not put a billing-year CSV in the LEIE folder.
        # data/rolled/ is owned by steps 3 and 4, so it is not asserted here.
        root = Path(__file__).resolve().parents[1]
        training = root / "data" / "training"
        names = [path.name for path in training.iterdir()]
        for name in names:
            for marker in BILLING_YEAR_NAMES:
                self.assertNotIn(marker, name)

    def test_written_count_matches_shipped_counter_and_independent_recount(self) -> None:
        self.assertTrue(COUNT_PATH.is_file(), f"missing {COUNT_PATH}")
        text = COUNT_PATH.read_text(encoding="utf-8")
        stated = int(re.search(r":\s*(\d+)\s*$", text).group(1))
        shipped = count_fraud_rows(LEIE_PATH)
        recounted = _independent_count(LEIE_PATH)
        self.assertEqual(stated, shipped)
        self.assertEqual(stated, recounted)
        self.assertGreater(stated, 0)


if __name__ == "__main__":
    unittest.main()

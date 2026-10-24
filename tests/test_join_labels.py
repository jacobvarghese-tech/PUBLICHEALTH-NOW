"""The shipped LEIE join marks a provider-year positive only on the locked rule."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.join_labels import (
    count_fraud_provider_years,
    earliest_exclusion_years,
    is_positive_label,
    write_count_file,
    write_training_file,
)

FRAUD_CODES = ("1128a1", "1128a3", "1128b6", "1128b7")


def _write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


class JoinLabelsTest(unittest.TestCase):
    def test_positive_only_when_exclusion_year_is_after_billing_year(self) -> None:
        self.assertTrue(is_positive_label(2021, 2022))
        self.assertFalse(is_positive_label(2021, 2021))
        self.assertFalse(is_positive_label(2021, 2020))
        self.assertFalse(is_positive_label(2021, None))

    def test_fixture_join_follows_the_four_code_later_year_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            leie = root / "UPDATED.csv"
            rolled_dir = root / "rolled"
            rolled_dir.mkdir()
            # 1111111111 is 1128a1 in 2022, so 2019 and 2020 are positive
            # and 2022 is not. A second 2024 row must not hide the 2022 year
            # or double-count a provider-year.
            # 2222222222 is 1128a3 in 2020: 2019 is positive, 2020 is not.
            # 3333333333 is 1128b6 in 2018: earlier than every billing year.
            # 7777777777 is 1128b6 in 2023: 2020 and 2022 are both positive.
            # 8888888888 is 1128b7 in 2021: 2019 is positive, 2021 is not.
            # 4444444444 is another code. 5555555555 has no rolled row.
            # 6666666666 has no LEIE row. 0, blank, and 123 are not 10-digit NPIs.
            _write_csv(
                leie,
                ["NPI", "EXCLTYPE", "EXCLDATE"],
                [
                    {"NPI": "1111111111", "EXCLTYPE": "1128a1", "EXCLDATE": "20220315"},
                    {"NPI": "1111111111", "EXCLTYPE": "1128b7", "EXCLDATE": "20240601"},
                    {"NPI": "2222222222", "EXCLTYPE": "1128a3", "EXCLDATE": "20200101"},
                    {"NPI": "3333333333", "EXCLTYPE": "1128b6", "EXCLDATE": "20181231"},
                    {"NPI": "7777777777", "EXCLTYPE": "1128b6", "EXCLDATE": "20230701"},
                    {"NPI": "8888888888", "EXCLTYPE": "1128b7", "EXCLDATE": "20211101"},
                    {"NPI": "4444444444", "EXCLTYPE": "1128a2", "EXCLDATE": "20250101"},
                    {"NPI": "5555555555", "EXCLTYPE": "1128a1", "EXCLDATE": "20250101"},
                    {"NPI": "0", "EXCLTYPE": "1128a1", "EXCLDATE": "20250101"},
                    {"NPI": "", "EXCLTYPE": "1128b6", "EXCLDATE": "20250101"},
                    {"NPI": "123", "EXCLTYPE": "1128a3", "EXCLDATE": "20250101"},
                ],
            )
            years = {
                2019: [
                    {"NPI": "1111111111", "Year": "2019"},
                    {"NPI": "2222222222", "Year": "2019"},
                    {"NPI": "3333333333", "Year": "2019"},
                    {"NPI": "8888888888", "Year": "2019"},
                    {"NPI": "6666666666", "Year": "2019"},
                    {"NPI": "0", "Year": "2019"},
                ],
                2020: [
                    {"NPI": "1111111111", "Year": "2020"},
                    {"NPI": "2222222222", "Year": "2020"},
                    {"NPI": "7777777777", "Year": "2020"},
                    {"NPI": "4444444444", "Year": "2020"},
                    {"NPI": "", "Year": "2020"},
                ],
                2021: [
                    {"NPI": "8888888888", "Year": "2021"},
                ],
                2022: [
                    {"NPI": "1111111111", "Year": "2022"},
                    {"NPI": "7777777777", "Year": "2022"},
                    {"NPI": "123", "Year": "2022"},
                ],
            }
            for year, rows in years.items():
                _write_csv(rolled_dir / f"{year}.csv", ["NPI", "Year"], rows)

            exclusion_years = earliest_exclusion_years(leie)
            self.assertEqual(exclusion_years["1111111111"], 2022)
            self.assertNotIn("4444444444", exclusion_years)
            self.assertNotIn("0", exclusion_years)
            self.assertNotIn("", exclusion_years)

            rolled_paths = [
                rolled_dir / f"{year}.csv" for year in (2019, 2020, 2021, 2022)
            ]
            counted = count_fraud_provider_years(rolled_paths, exclusion_years)
            # 1111111111 in 2019 and 2020, 2222222222 in 2019,
            # 7777777777 in 2020 and 2022, 8888888888 in 2019.
            self.assertEqual(counted, 6)

            count_path = root / "fraud_provider_year_count.txt"
            written = write_count_file(
                leie_path=leie,
                rolled_dir=rolled_dir,
                count_path=count_path,
                billing_years=(2019, 2020, 2021, 2022),
            )
            self.assertEqual(written, 6)
            text = count_path.read_text(encoding="utf-8")
            self.assertTrue(text.rstrip().endswith("6"))
            for code in FRAUD_CODES:
                self.assertIn(code, text)

    def test_training_file_drops_2024_demo_npis_and_other_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            leie = root / "UPDATED.csv"
            rolled_dir = root / "rolled"
            rolled_dir.mkdir()
            _write_csv(
                leie,
                ["NPI", "EXCLTYPE", "EXCLDATE"],
                [
                    {"NPI": "1111111111", "EXCLTYPE": "1128a1", "EXCLDATE": "20150101"},
                    {"NPI": "2222222222", "EXCLTYPE": "1128a3", "EXCLDATE": "20140101"},
                    {"NPI": "3333333333", "EXCLTYPE": "1128b6", "EXCLDATE": "20160101"},
                    {"NPI": "4444444444", "EXCLTYPE": "1128a2", "EXCLDATE": "20180101"},
                    {"NPI": "5555555555", "EXCLTYPE": "1128b7", "EXCLDATE": "20130101"},
                    {"NPI": "1124725817", "EXCLTYPE": "1128a1", "EXCLDATE": "20260101"},
                    {"NPI": "12", "EXCLTYPE": "1128a1", "EXCLDATE": "20180101"},
                ],
            )
            years = {
                2013: [
                    {"NPI": "1111111111", "Year": "2013"},
                    {"NPI": "2222222222", "Year": "2013"},
                    {"NPI": "5555555555", "Year": "2013"},
                    {"NPI": "6666666666", "Year": "2013"},
                    {"NPI": "1124725817", "Year": "2013"},
                    {"NPI": "1639879034", "Year": "2013"},
                ],
                2014: [
                    {"NPI": "1111111111", "Year": "2014"},
                    {"NPI": "3333333333", "Year": "2014"},
                    {"NPI": "4444444444", "Year": "2014"},
                ],
            }
            for year, rows in years.items():
                _write_csv(rolled_dir / f"{year}.csv", ["NPI", "Year"], rows)
            # A 2024 roll sits beside the training years and must not be read.
            _write_csv(
                rolled_dir / "2024.csv",
                ["NPI", "Year"],
                [{"NPI": "1111111111", "Year": "2024"}],
            )
            leie_before = leie.read_bytes()
            training = root / "physician.csv"
            counts = root / "expand_counts.txt"
            fraud_rows, clean_rows = write_training_file(
                leie_path=leie,
                rolled_dir=rolled_dir,
                training_path=training,
                counts_path=counts,
                billing_years=(2013, 2014),
            )
            self.assertEqual(leie.read_bytes(), leie_before)
            holdout_text = (rolled_dir / "2024.csv").read_text(encoding="utf-8")
            self.assertIn("2024", holdout_text)
            self.assertIn("1111111111", holdout_text)
            with training.open(encoding="utf-8", newline="") as handle:
                written = list(csv.DictReader(handle))
            years_written = {row["Year"] for row in written}
            self.assertEqual(years_written, {"2013", "2014"})
            npis = {row["NPI"] for row in written}
            self.assertNotIn("1124725817", npis)
            self.assertNotIn("1639879034", npis)
            positives = [row for row in written if row["label"] == "1"]
            self.assertEqual(fraud_rows, len(positives))
            self.assertEqual(clean_rows, len(written) - len(positives))
            for row in positives:
                self.assertEqual(len(row["NPI"]), 10)
                self.assertTrue(row["NPI"].isdigit())
                self.assertIn(row["EXCLTYPE"], FRAUD_CODES)
                self.assertGreater(int(row["exclusion_year"]), int(row["Year"]))
            # 1111111111 is excluded in 2015, so 2013 and 2014 are positive.
            # 2222222222 is excluded in 2014, so 2013 is positive and 2014 is absent.
            # 3333333333 is excluded in 2016, so 2014 is positive.
            # 5555555555 is excluded in 2013, so 2013 is not positive.
            # 4444444444 is another code.
            self.assertEqual(fraud_rows, 4)
            text = counts.read_text(encoding="utf-8")
            self.assertIn("fraud_rows 2013: 2", text)
            self.assertIn("fraud_rows 2014: 2", text)
            self.assertNotIn("4400", text)


if __name__ == "__main__":
    unittest.main()

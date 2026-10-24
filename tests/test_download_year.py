"""The shipped chunked rollup must match the year-CSV column contract."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.download_year import (
    OUTPUT_COLUMNS,
    YEAR_FILES,
    growth_rate,
    prior_rolled_path,
    record_size_mismatch,
    roll_csv,
    write_rolled,
)

HEADER = [
    "Rndrng_NPI",
    "Rndrng_Prvdr_Last_Org_Name",
    "Rndrng_Prvdr_First_Name",
    "Rndrng_Prvdr_City",
    "Rndrng_Prvdr_State_Abrvtn",
    "Rndrng_Prvdr_Zip5",
    "Rndrng_Prvdr_Type",
    "HCPCS_Cd",
    "Place_Of_Srvc",
    "Tot_Srvcs",
    "Tot_Benes",
    "Avg_Sbmtd_Chrg",
    "Avg_Mdcr_Pymt_Amt",
]


def _write_fixture(path: Path) -> None:
    rows = [
        # NPI 1111111111: two HCPCS, two places, unequal service weights.
        # HCPCS 99213 totals 3+1=4 services. HCPCS 36415 totals 1.
        # Weighted charge = (3*100 + 1*40 + 1*10) / 5 = 70.
        # Weighted payment = (3*50 + 1*20 + 1*0) / 5 = 34.
        # Ratio = 70/34. Top-code share = 4/5.
        ["1111111111", "Alpha Lab", "Ann", "Boston", "MA", "02110", "Clinical Laboratory", "99213", "F", "3", "2", "100", "50"],
        ["1111111111", "Alpha Lab", "Ann", "Boston", "MA", "02110", "Clinical Laboratory", "99213", "O", "1", "1", "40", "20"],
        ["1111111111", "Alpha Lab", "Ann", "Boston", "MA", "02110", "Clinical Laboratory", "36415", "F", "1", "4", "10", "0"],
        # NPI 2222222222: one HCPCS, zero payment, so the ratio stays missing.
        ["2222222222", "Beta Clinic", "", "Austin", "TX", "78701", "Internal Medicine", "99214", "O", "2", "2", "80", "0"],
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)


class RollupContractTest(unittest.TestCase):
    def test_fixture_collapses_to_contract_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "fixture.csv"
            _write_fixture(csv_path)
            rows = roll_csv(csv_path, year=2018, chunk_rows=1)
        self.assertEqual([row["NPI"] for row in rows], ["1111111111", "2222222222"])
        self.assertEqual(list(rows[0].keys()), list(OUTPUT_COLUMNS))

        first = rows[0]
        self.assertEqual(first["Name"], "Alpha Lab, Ann")
        self.assertEqual(first["City"], "Boston")
        self.assertEqual(first["State"], "MA")
        self.assertEqual(first["ZIP"], "02110")
        self.assertEqual(first["Specialty"], "Clinical Laboratory")
        self.assertEqual(first["Service count"], 5.0)
        self.assertEqual(first["Beneficiary count"], 7.0)
        self.assertEqual(first["Average charge"], 70.0)
        self.assertEqual(first["Average payment"], 34.0)
        self.assertEqual(first["Charge-to-payment ratio"], 70.0 / 34.0)
        self.assertEqual(first["Top-code share"], 4.0 / 5.0)
        self.assertIsNone(first["Growth"])
        self.assertEqual(first["Year"], 2018)
        self.assertNotIn("Place_Of_Srvc", first)
        self.assertNotIn("HCPCS_Cd", first)
        self.assertNotIn("Exclusion type", first)
        self.assertNotIn("Exclusion date", first)

        second = rows[1]
        self.assertEqual(second["Name"], "Beta Clinic")
        self.assertEqual(second["Service count"], 2.0)
        self.assertEqual(second["Beneficiary count"], 2.0)
        self.assertEqual(second["Average charge"], 80.0)
        self.assertEqual(second["Average payment"], 0.0)
        self.assertIsNone(second["Charge-to-payment ratio"])
        self.assertEqual(second["Top-code share"], 1.0)
        self.assertIsNone(second["Growth"])
        self.assertEqual(second["Year"], 2018)

    def test_2019_growth_uses_shipped_join(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prior_dir = root / "rolled"
            prior_rows = [
                {
                    "NPI": "1111111111",
                    "Name": "Alpha Lab, Ann",
                    "City": "Boston",
                    "State": "MA",
                    "ZIP": "02110",
                    "Specialty": "Clinical Laboratory",
                    "Service count": 4.0,
                    "Beneficiary count": 1.0,
                    "Average charge": 1.0,
                    "Average payment": 1.0,
                    "Charge-to-payment ratio": 1.0,
                    "Top-code share": 1.0,
                    "Growth": None,
                    "Year": 2018,
                },
                {
                    "NPI": "2222222222",
                    "Name": "Beta Clinic",
                    "City": "Austin",
                    "State": "TX",
                    "ZIP": "78701",
                    "Specialty": "Internal Medicine",
                    "Service count": 0.0,
                    "Beneficiary count": 0.0,
                    "Average charge": None,
                    "Average payment": None,
                    "Charge-to-payment ratio": None,
                    "Top-code share": None,
                    "Growth": None,
                    "Year": 2018,
                },
                {
                    "NPI": "9999999999",
                    "Name": "Prior Only",
                    "City": "Denver",
                    "State": "CO",
                    "ZIP": "80202",
                    "Specialty": "Nurse Practitioner",
                    "Service count": 9.0,
                    "Beneficiary count": 9.0,
                    "Average charge": 1.0,
                    "Average payment": 1.0,
                    "Charge-to-payment ratio": 1.0,
                    "Top-code share": 1.0,
                    "Growth": None,
                    "Year": 2018,
                },
            ]
            prior_path, _note = write_rolled(prior_rows, prior_dir, year=2018)
            before = prior_path.read_bytes()
            csv_path = root / "fixture.csv"
            _write_growth_fixture(csv_path)
            rows = roll_csv(csv_path, year=2019, chunk_rows=1, prior_rolled=prior_path)
            after = prior_path.read_bytes()
        self.assertEqual(before, after)
        self.assertEqual(
            [row["NPI"] for row in rows],
            ["1111111111", "2222222222", "3333333333"],
        )
        self.assertEqual(list(rows[0].keys()), list(OUTPUT_COLUMNS))
        matched = rows[0]
        self.assertEqual(matched["Service count"], 5.0)
        self.assertEqual(matched["Beneficiary count"], 7.0)
        self.assertEqual(matched["Average charge"], 70.0)
        self.assertEqual(matched["Average payment"], 34.0)
        self.assertEqual(matched["Charge-to-payment ratio"], 70.0 / 34.0)
        self.assertEqual(matched["Top-code share"], 4.0 / 5.0)
        self.assertEqual(matched["Growth"], growth_rate(5.0, 4.0))
        self.assertEqual(matched["Growth"], 5.0 / 4.0 - 1)
        self.assertEqual(matched["Year"], 2019)

        zero_prior = rows[1]
        self.assertEqual(zero_prior["Service count"], 2.0)
        self.assertEqual(zero_prior["Average payment"], 0.0)
        self.assertIsNone(zero_prior["Charge-to-payment ratio"])
        self.assertIsNone(zero_prior["Growth"])
        self.assertEqual(zero_prior["Year"], 2019)

        absent = rows[2]
        self.assertEqual(absent["Service count"], 3.0)
        self.assertIsNone(absent["Growth"])
        self.assertEqual(absent["Year"], 2019)
        self.assertNotIn("9999999999", [row["NPI"] for row in rows])

    def test_2020_growth_joins_2019_not_2018(self) -> None:
        """2020 Growth uses the 2019 service count. A different 2018 count must not leak in."""
        year_entry = YEAR_FILES[2020]
        self.assertEqual(year_entry["bytes"], 2994090236)
        self.assertEqual(
            year_entry["url"],
            "https://data.cms.gov/sites/default/files/2025-11/"
            "d22b18cd-7726-4bf5-8e9c-3e4587c589a1/"
            "MUP_PHY_R25_P05_V20_D20_Prov_Svc.csv",
        )
        self.assertEqual(year_entry["raw_name"], "MUP_PHY_R25_P05_V20_D20_Prov_Svc.csv")
        self.assertIn(2018, YEAR_FILES)
        self.assertIn(2019, YEAR_FILES)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rolled_dir = root / "rolled"
            prior_2019 = [
                {
                    "NPI": "1111111111",
                    "Name": "Alpha Lab, Ann",
                    "City": "Boston",
                    "State": "MA",
                    "ZIP": "02110",
                    "Specialty": "Clinical Laboratory",
                    "Service count": 4.0,
                    "Beneficiary count": 1.0,
                    "Average charge": 1.0,
                    "Average payment": 1.0,
                    "Charge-to-payment ratio": 1.0,
                    "Top-code share": 1.0,
                    "Growth": 0.25,
                    "Year": 2019,
                },
                {
                    "NPI": "2222222222",
                    "Name": "Beta Clinic",
                    "City": "Austin",
                    "State": "TX",
                    "ZIP": "78701",
                    "Specialty": "Internal Medicine",
                    "Service count": 0.0,
                    "Beneficiary count": 0.0,
                    "Average charge": None,
                    "Average payment": None,
                    "Charge-to-payment ratio": None,
                    "Top-code share": None,
                    "Growth": None,
                    "Year": 2019,
                },
            ]
            # A blank 2019 service count must leave Growth missing.
            prior_2019.append(
                {
                    "NPI": "4444444444",
                    "Name": "Blank Count",
                    "City": "Miami",
                    "State": "FL",
                    "ZIP": "33101",
                    "Specialty": "Family Practice",
                    "Service count": None,
                    "Beneficiary count": 1.0,
                    "Average charge": None,
                    "Average payment": None,
                    "Charge-to-payment ratio": None,
                    "Top-code share": None,
                    "Growth": None,
                    "Year": 2019,
                }
            )
            path_2019, _note = write_rolled(prior_2019, rolled_dir, year=2019)
            older_2018 = [
                {
                    "NPI": "1111111111",
                    "Name": "Alpha Lab, Ann",
                    "City": "Boston",
                    "State": "MA",
                    "ZIP": "02110",
                    "Specialty": "Clinical Laboratory",
                    "Service count": 100.0,
                    "Beneficiary count": 1.0,
                    "Average charge": 1.0,
                    "Average payment": 1.0,
                    "Charge-to-payment ratio": 1.0,
                    "Top-code share": 1.0,
                    "Growth": None,
                    "Year": 2018,
                },
            ]
            path_2018, _older_note = write_rolled(older_2018, rolled_dir, year=2018)
            before_2019 = path_2019.read_bytes()
            before_2018 = path_2018.read_bytes()
            self.assertEqual(prior_rolled_path(2020, rolled_dir), path_2019)
            self.assertNotEqual(prior_rolled_path(2020, rolled_dir), path_2018)

            csv_path = root / "fixture.csv"
            _write_2020_fixture(csv_path)
            rows = roll_csv(csv_path, year=2020, chunk_rows=1, prior_rolled=path_2019)
            after_2019 = path_2019.read_bytes()
            after_2018 = path_2018.read_bytes()

        self.assertEqual(before_2019, after_2019)
        self.assertEqual(before_2018, after_2018)
        self.assertEqual(
            [row["NPI"] for row in rows],
            ["1111111111", "2222222222", "3333333333", "4444444444"],
        )
        self.assertEqual(len(rows), len({row["NPI"] for row in rows}))
        self.assertEqual(list(rows[0].keys()), list(OUTPUT_COLUMNS))

        matched = rows[0]
        self.assertEqual(matched["Service count"], 5.0)
        self.assertEqual(matched["Growth"], 5.0 / 4.0 - 1)
        self.assertNotEqual(matched["Growth"], 5.0 / 100.0 - 1)
        self.assertEqual(matched["Year"], 2020)

        zero_prior = rows[1]
        self.assertEqual(zero_prior["Service count"], 2.0)
        self.assertIsNone(zero_prior["Growth"])
        self.assertEqual(zero_prior["Year"], 2020)

        absent = rows[2]
        self.assertEqual(absent["Service count"], 3.0)
        self.assertIsNone(absent["Growth"])
        self.assertEqual(absent["Year"], 2020)

        blank_prior = rows[3]
        self.assertEqual(blank_prior["Service count"], 6.0)
        self.assertIsNone(blank_prior["Growth"])
        self.assertEqual(blank_prior["Year"], 2020)

    def test_2021_growth_joins_2020_not_2019_or_2018(self) -> None:
        """2021 Growth uses the 2020 service count. Different 2019 and 2018 counts must not leak in."""
        year_entry = YEAR_FILES[2021]
        self.assertEqual(year_entry["bytes"], 3100222715)
        self.assertEqual(
            year_entry["url"],
            "https://data.cms.gov/sites/default/files/2025-11/"
            "bffaf97a-c2ab-4fd7-8718-be90742e3485/"
            "MUP_PHY_R25_P05_V20_D21_Prov_Svc.csv",
        )
        self.assertEqual(year_entry["raw_name"], "MUP_PHY_R25_P05_V20_D21_Prov_Svc.csv")
        self.assertIn(2018, YEAR_FILES)
        self.assertIn(2019, YEAR_FILES)
        self.assertIn(2020, YEAR_FILES)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rolled_dir = root / "rolled"
            prior_2020 = [
                {
                    "NPI": "1111111111",
                    "Name": "Alpha Lab, Ann",
                    "City": "Boston",
                    "State": "MA",
                    "ZIP": "02110",
                    "Specialty": "Clinical Laboratory",
                    "Service count": 4.0,
                    "Beneficiary count": 1.0,
                    "Average charge": 1.0,
                    "Average payment": 1.0,
                    "Charge-to-payment ratio": 1.0,
                    "Top-code share": 1.0,
                    "Growth": 0.25,
                    "Year": 2020,
                },
                {
                    "NPI": "2222222222",
                    "Name": "Beta Clinic",
                    "City": "Austin",
                    "State": "TX",
                    "ZIP": "78701",
                    "Specialty": "Internal Medicine",
                    "Service count": 0.0,
                    "Beneficiary count": 0.0,
                    "Average charge": None,
                    "Average payment": None,
                    "Charge-to-payment ratio": None,
                    "Top-code share": None,
                    "Growth": None,
                    "Year": 2020,
                },
                {
                    "NPI": "4444444444",
                    "Name": "Blank Count",
                    "City": "Miami",
                    "State": "FL",
                    "ZIP": "33101",
                    "Specialty": "Family Practice",
                    "Service count": None,
                    "Beneficiary count": 1.0,
                    "Average charge": None,
                    "Average payment": None,
                    "Charge-to-payment ratio": None,
                    "Top-code share": None,
                    "Growth": None,
                    "Year": 2020,
                },
            ]
            path_2020, _note = write_rolled(prior_2020, rolled_dir, year=2020)
            older_2019 = [
                {
                    "NPI": "1111111111",
                    "Name": "Alpha Lab, Ann",
                    "City": "Boston",
                    "State": "MA",
                    "ZIP": "02110",
                    "Specialty": "Clinical Laboratory",
                    "Service count": 50.0,
                    "Beneficiary count": 1.0,
                    "Average charge": 1.0,
                    "Average payment": 1.0,
                    "Charge-to-payment ratio": 1.0,
                    "Top-code share": 1.0,
                    "Growth": 0.1,
                    "Year": 2019,
                },
            ]
            path_2019, _note_2019 = write_rolled(older_2019, rolled_dir, year=2019)
            older_2018 = [
                {
                    "NPI": "1111111111",
                    "Name": "Alpha Lab, Ann",
                    "City": "Boston",
                    "State": "MA",
                    "ZIP": "02110",
                    "Specialty": "Clinical Laboratory",
                    "Service count": 100.0,
                    "Beneficiary count": 1.0,
                    "Average charge": 1.0,
                    "Average payment": 1.0,
                    "Charge-to-payment ratio": 1.0,
                    "Top-code share": 1.0,
                    "Growth": None,
                    "Year": 2018,
                },
            ]
            path_2018, _note_2018 = write_rolled(older_2018, rolled_dir, year=2018)
            before = {
                path_2020: path_2020.read_bytes(),
                path_2019: path_2019.read_bytes(),
                path_2018: path_2018.read_bytes(),
            }
            self.assertEqual(prior_rolled_path(2021, rolled_dir), path_2020)
            self.assertNotEqual(prior_rolled_path(2021, rolled_dir), path_2019)
            self.assertNotEqual(prior_rolled_path(2021, rolled_dir), path_2018)

            csv_path = root / "fixture.csv"
            _write_2020_fixture(csv_path)
            rows = roll_csv(csv_path, year=2021, chunk_rows=1, prior_rolled=path_2020)
            for path, snapshot in before.items():
                self.assertEqual(path.read_bytes(), snapshot)

        self.assertEqual(
            [row["NPI"] for row in rows],
            ["1111111111", "2222222222", "3333333333", "4444444444"],
        )
        self.assertEqual(len(rows), len({row["NPI"] for row in rows}))
        self.assertEqual(list(rows[0].keys()), list(OUTPUT_COLUMNS))

        matched = rows[0]
        self.assertEqual(matched["Service count"], 5.0)
        self.assertEqual(matched["Growth"], 5.0 / 4.0 - 1)
        self.assertNotEqual(matched["Growth"], 5.0 / 50.0 - 1)
        self.assertNotEqual(matched["Growth"], 5.0 / 100.0 - 1)
        self.assertEqual(matched["Year"], 2021)

        zero_prior = rows[1]
        self.assertEqual(zero_prior["Service count"], 2.0)
        self.assertIsNone(zero_prior["Growth"])
        self.assertEqual(zero_prior["Year"], 2021)

        absent = rows[2]
        self.assertEqual(absent["Service count"], 3.0)
        self.assertIsNone(absent["Growth"])
        self.assertEqual(absent["Year"], 2021)

        blank_prior = rows[3]
        self.assertEqual(blank_prior["Service count"], 6.0)
        self.assertIsNone(blank_prior["Growth"])
        self.assertEqual(blank_prior["Year"], 2021)

    def test_2022_2023_2024_growth_joins_immediate_prior_only(self) -> None:
        """Each later year joins year minus 1. An earlier count sitting beside that file must not leak in."""
        expected = {
            2022: {
                "bytes": 3066783950,
                "url": (
                    "https://data.cms.gov/sites/default/files/2025-11/"
                    "53fb2bae-4913-48dc-a6d4-d8c025906567/"
                    "MUP_PHY_R25_P05_V20_D22_Prov_Svc.csv"
                ),
                "raw_name": "MUP_PHY_R25_P05_V20_D22_Prov_Svc.csv",
            },
            2023: {
                "bytes": 3062332720,
                "url": (
                    "https://data.cms.gov/sites/default/files/2025-04/"
                    "e3f823f8-db5b-4cc7-ba04-e7ae92b99757/"
                    "MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv"
                ),
                "raw_name": "MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv",
            },
            2024: {
                "bytes": 3250282192,
                "url": (
                    "https://data.cms.gov/sites/default/files/2026-05/"
                    "b5ebab5a-f490-418a-9bce-4b9f31419356/"
                    "PHY_R26_P05_V10_D24_Prov_Svc.csv"
                ),
                "raw_name": "PHY_R26_P05_V10_D24_Prov_Svc.csv",
            },
        }
        for year, entry in expected.items():
            self.assertEqual(YEAR_FILES[year]["bytes"], entry["bytes"])
            self.assertEqual(YEAR_FILES[year]["url"], entry["url"])
            self.assertEqual(YEAR_FILES[year]["raw_name"], entry["raw_name"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rolled_dir = root / "rolled"
            # Earlier years sit beside the immediate prior with different counts.
            # They are written first so the immediate prior file is not overwritten.
            decoys = {2018: 100.0, 2019: 80.0, 2020: 60.0}
            for year, services in decoys.items():
                write_rolled(
                    [_prior_row("1111111111", services, year)],
                    rolled_dir,
                    year=year,
                )
            prior_services = {2021: 4.0, 2022: 8.0, 2023: 10.0}
            written: dict[int, Path] = {}
            for year, services in prior_services.items():
                rows = [
                    _prior_row("1111111111", services, year),
                    _prior_row("2222222222", 0.0, year),
                    _prior_row("4444444444", None, year),
                ]
                path, _note = write_rolled(rows, rolled_dir, year=year)
                written[year] = path
            before = {path: path.read_bytes() for path in rolled_dir.glob("*.csv")}

            cases = (
                (2022, written[2021], 4.0, (100.0, 80.0, 60.0)),
                (2023, written[2022], 8.0, (4.0, 60.0, 80.0)),
                (2024, written[2023], 10.0, (8.0, 4.0, 60.0)),
            )
            for year, prior_path, prior_count, leaked in cases:
                self.assertEqual(prior_rolled_path(year, rolled_dir), prior_path)
                self.assertEqual(prior_rolled_path(year, rolled_dir).name, f"{year - 1}.csv")
                csv_path = root / f"fixture_{year}.csv"
                _write_2020_fixture(csv_path)
                rows = roll_csv(csv_path, year=year, chunk_rows=1, prior_rolled=prior_path)
                self.assertEqual(
                    [row["NPI"] for row in rows],
                    ["1111111111", "2222222222", "3333333333", "4444444444"],
                )
                self.assertEqual(len(rows), len({row["NPI"] for row in rows}))
                self.assertEqual(list(rows[0].keys()), list(OUTPUT_COLUMNS))
                matched = rows[0]
                self.assertEqual(matched["Service count"], 5.0)
                self.assertEqual(matched["Growth"], 5.0 / prior_count - 1)
                for other in leaked:
                    self.assertNotEqual(matched["Growth"], 5.0 / other - 1)
                self.assertEqual(matched["Year"], year)
                self.assertEqual(rows[1]["Service count"], 2.0)
                self.assertIsNone(rows[1]["Growth"])
                self.assertEqual(rows[1]["Year"], year)
                self.assertEqual(rows[2]["Service count"], 3.0)
                self.assertIsNone(rows[2]["Growth"])
                self.assertEqual(rows[2]["Year"], year)
                self.assertEqual(rows[3]["Service count"], 6.0)
                self.assertIsNone(rows[3]["Growth"])
                self.assertEqual(rows[3]["Year"], year)

            for path, snapshot in before.items():
                self.assertEqual(path.read_bytes(), snapshot)
            for year in (2018, 2019, 2020, 2021, 2022, 2023):
                self.assertTrue((rolled_dir / f"{year}.csv").is_file())

    def test_2013_growth_stays_blank_and_2014_joins_2013(self) -> None:
        """2013 has no prior year. 2014 Growth is current / 2013 service count - 1."""
        self.assertIsNone(prior_rolled_path(2013, Path(".")))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rolled_dir = root / "rolled"
            csv_2013 = root / "y2013.csv"
            _write_growth_fixture(csv_2013)
            rows_2013 = roll_csv(csv_2013, year=2013, chunk_rows=1, prior_rolled=None)
            self.assertTrue(rows_2013)
            for row in rows_2013:
                self.assertIsNone(row["Growth"])
                self.assertEqual(row["Year"], 2013)
            write_rolled(rows_2013, rolled_dir, year=2013)
            self.assertEqual(prior_rolled_path(2014, rolled_dir).name, "2013.csv")
            self.assertIsNone(prior_rolled_path(2013, rolled_dir))

            # Zero prior service count leaves 2014 Growth blank.
            zero_prior = [
                _prior_row("1111111111", 4.0, 2013),
                _prior_row("2222222222", 0.0, 2013),
            ]
            prior_path, _note = write_rolled(zero_prior, rolled_dir, year=2013)
            csv_2014 = root / "y2014.csv"
            _write_growth_fixture(csv_2014)
            rows_2014 = roll_csv(csv_2014, year=2014, chunk_rows=1, prior_rolled=prior_path)
        by_npi = {row["NPI"]: row for row in rows_2014}
        self.assertEqual(by_npi["1111111111"]["Growth"], 5.0 / 4.0 - 1)
        self.assertIsNone(by_npi["2222222222"]["Growth"])
        self.assertIsNone(by_npi["3333333333"]["Growth"])
        self.assertEqual(by_npi["1111111111"]["Year"], 2014)

    def test_size_mismatch_writes_both_sizes_and_keeps_the_raw_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw.csv"
            raw.write_text("header\n", encoding="utf-8")
            before = raw.read_bytes()
            counts = root / "expand_counts.txt"
            note = record_size_mismatch(
                root / "rolled",
                expected=10,
                received=4,
                year=2013,
                counts_path=counts,
            )
            self.assertTrue(raw.is_file())
            self.assertEqual(raw.read_bytes(), before)
            text = note.read_text(encoding="utf-8")
            self.assertIn("10", text)
            self.assertIn("4", text)
            self.assertIn("expected_bytes=10", counts.read_text(encoding="utf-8"))
            self.assertIn("received_bytes=4", counts.read_text(encoding="utf-8"))
            self.assertFalse((root / "rolled" / "2013.csv").exists())


def _prior_row(npi: str, services: float | None, year: int) -> dict[str, object]:
    return {
        "NPI": npi,
        "Name": "Prior",
        "City": "Boston",
        "State": "MA",
        "ZIP": "02110",
        "Specialty": "Clinical Laboratory",
        "Service count": services,
        "Beneficiary count": 1.0,
        "Average charge": 1.0,
        "Average payment": 1.0,
        "Charge-to-payment ratio": 1.0,
        "Top-code share": 1.0,
        "Growth": None,
        "Year": year,
    }


def _write_growth_fixture(path: Path) -> None:
    rows = [
        ["1111111111", "Alpha Lab", "Ann", "Boston", "MA", "02110", "Clinical Laboratory", "99213", "F", "3", "2", "100", "50"],
        ["1111111111", "Alpha Lab", "Ann", "Boston", "MA", "02110", "Clinical Laboratory", "99213", "O", "1", "1", "40", "20"],
        ["1111111111", "Alpha Lab", "Ann", "Boston", "MA", "02110", "Clinical Laboratory", "36415", "F", "1", "4", "10", "0"],
        ["2222222222", "Beta Clinic", "", "Austin", "TX", "78701", "Internal Medicine", "99214", "O", "2", "2", "80", "0"],
        ["3333333333", "Gamma Office", "Gail", "Seattle", "WA", "98101", "Family Practice", "99213", "F", "3", "3", "20", "10"],
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)


def _write_2020_fixture(path: Path) -> None:
    rows = [
        ["1111111111", "Alpha Lab", "Ann", "Boston", "MA", "02110", "Clinical Laboratory", "99213", "F", "3", "2", "100", "50"],
        ["1111111111", "Alpha Lab", "Ann", "Boston", "MA", "02110", "Clinical Laboratory", "99213", "O", "1", "1", "40", "20"],
        ["1111111111", "Alpha Lab", "Ann", "Boston", "MA", "02110", "Clinical Laboratory", "36415", "F", "1", "4", "10", "0"],
        ["2222222222", "Beta Clinic", "", "Austin", "TX", "78701", "Internal Medicine", "99214", "O", "2", "2", "80", "0"],
        ["3333333333", "Gamma Office", "Gail", "Seattle", "WA", "98101", "Family Practice", "99213", "F", "3", "3", "20", "10"],
        ["4444444444", "Blank Count", "Bea", "Miami", "FL", "33101", "Family Practice", "99213", "F", "6", "2", "30", "15"],
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()

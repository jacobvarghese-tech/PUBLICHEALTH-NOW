"""Drive the shipped paper roll and fit functions from their real start state."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import pandas as pd

from scripts.paper_fit import (
    CLEAN_PER_FRAUD,
    LABEL_PATH,
    LEIE_BYTES,
    PAPER_AUC,
    LabelSizeMismatch,
    end_year,
    ensure_labels,
    fit_and_write,
    forest_kwargs,
    is_indefinite,
    load_labels,
    new_forest,
    normalize_type,
    record_label_mismatch,
    table2_years,
    undersample,
)
from scripts.paper_oneshot import YEARS
from scripts.paper_roll_year import year_done as rolled_year_done
from scripts.paper_roll_year import (
    CMS_2014_BYTES,
    CMS_2015_BYTES,
    NBER_2013_BYTES,
    HeaderMismatch,
    Running,
    SizeMismatch,
    aggregate,
    csv_from_resources,
    download,
    record_2012_gap,
    record_size_mismatch,
    roll_year,
    write_rolled,
)

NBER_HEADER = [
    "cyear",
    "npi",
    "pgender",
    "provider_type",
    "medicare_participation_indicator",
    "plcsrvc",
    "hcpcs_cd",
    "hcpcs_drug_indicator",
    "srvc_cnt",
    "bene_unique_cnt",
    "bene_day_srvc_cnt",
    "average_submitted_chrg_amt",
    "average_medicare_payment_amt",
]
CMS_HEADER = [
    "Rndrng_NPI",
    "Rndrng_Prvdr_Last_Org_Name",
    "Rndrng_Prvdr_First_Name",
    "Rndrng_Prvdr_City",
    "Rndrng_Prvdr_State_Abrvtn",
    "Rndrng_Prvdr_Zip5",
    "Rndrng_Prvdr_Type",
    "HCPCS_Cd",
    "HCPCS_Drug_Ind",
    "Place_Of_Srvc",
    "Rndrng_Prvdr_Mdcr_Prtcptg_Ind",
    "Tot_Srvcs",
    "Tot_Benes",
    "Tot_Bene_Day_Srvcs",
    "Avg_Sbmtd_Chrg",
    "Avg_Mdcr_Pymt_Amt",
]


def _nber_row(
    npi: str,
    gender: str,
    specialty: str,
    hcpcs: str,
    place: str,
    services: str,
    benes: str,
    days: str,
    charge: str,
    payment: str,
    drug: str = "N",
    participate: str = "Y",
) -> list[str]:
    return [
        "2013",
        npi,
        gender,
        specialty,
        participate,
        place,
        hcpcs,
        drug,
        services,
        benes,
        days,
        charge,
        payment,
    ]


class SummaryTest(unittest.TestCase):
    def test_six_summaries_use_observed_values(self) -> None:
        running = Running()
        for value in (1.0, 2.0, 6.0):
            running.add(value)
        mean, total, median, std, low, high = running.row()
        self.assertEqual(mean, 3.0)
        self.assertEqual(total, 9.0)
        self.assertEqual(median, 2.0)
        self.assertAlmostEqual(std, 2.6457513110645907)
        self.assertEqual(low, 1.0)
        self.assertEqual(high, 6.0)

    def test_single_observation_std_is_zero(self) -> None:
        running = Running()
        running.add(4.0)
        row = running.row()
        self.assertEqual(row[2], 4.0)
        self.assertEqual(row[3], 0.0)

    def test_grouping_keys_and_summaries_on_a_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "phys.csv"
            with raw.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(NBER_HEADER)
                writer.writerow(_nber_row("1111111111", "M", "Internal Medicine", "99213", "F", "1", "10", "1", "100", "40"))
                writer.writerow(_nber_row("1111111111", "M", "Internal Medicine", "99214", "O", "3", "30", "5", "200", "80"))
                writer.writerow(_nber_row("1111111111", "M", "Internal Medicine", "J0135", "F", "9", "9", "9", "9", "9", drug="Y"))
                writer.writerow(_nber_row("2222222222", "F", "Cardiology", "99213", "F", "4", "4", "4", "50", "20", participate="N"))
                writer.writerow(_nber_row("0000000000", "M", "Pathology", "88305", "F", "8", "8", "8", "10", "5"))
            groups, source_rows, gender_source = aggregate(raw, 2013)
        self.assertEqual(source_rows, 2)
        self.assertEqual(gender_source, "pgender")
        self.assertEqual(list(groups), [("Internal Medicine", "1111111111", "M")])
        services = groups[("Internal Medicine", "1111111111", "M")]["line_srvc_cnt"].row()
        self.assertEqual(services[0], 2.0)
        self.assertEqual(services[1], 4.0)
        self.assertEqual(services[2], 2.0)
        self.assertGreater(services[3], 0)
        self.assertEqual(services[4], 1.0)
        self.assertEqual(services[5], 3.0)

    def test_missing_pgender_fills_from_nppes_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "cms.csv"
            with raw.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(CMS_HEADER)
                writer.writerow(
                    [
                        "3333333333",
                        "Lab",
                        "Ada",
                        "Miami",
                        "FL",
                        "33101",
                        "Pathology",
                        "88305",
                        "N",
                        "F",
                        "Y",
                        "2",
                        "2",
                        "2",
                        "10",
                        "4",
                    ]
                )
            groups, source_rows, gender_source = aggregate(
                raw, 2014, lookup=lambda npi: "F" if npi == "3333333333" else ""
            )
        self.assertEqual(source_rows, 1)
        self.assertEqual(gender_source, "nppes_2026-10-12")
        self.assertIn(("Pathology", "3333333333", "F"), groups)
        identity = groups[("Pathology", "3333333333", "F")]["_id"]
        self.assertEqual(identity["name"], "Lab, Ada")
        self.assertEqual(identity["city"], "Miami")
        self.assertEqual(identity["state"], "FL")
        self.assertEqual(identity["zip"], "33101")


class DownloadContractTest(unittest.TestCase):
    def test_partial_file_resumes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "year.csv"
            partial = dest.with_suffix(dest.suffix + ".partial")
            partial.write_bytes(b"abc")
            calls: list[tuple[str, int]] = []

            def resume(url: str, path: Path, start: int) -> None:
                calls.append((url, start))
                self.assertEqual(path, partial)
                self.assertGreaterEqual(path.stat().st_size, start)
                self.assertEqual(path.read_bytes(), b"abc")
                with path.open("ab") as handle:
                    handle.write(b"de")

            received = download(
                "http://example.test/year.csv",
                dest,
                5,
                resume=resume,
            )
            self.assertEqual(received, 5)
            self.assertEqual(calls, [("http://example.test/year.csv", 3)])
            self.assertFalse(partial.exists())
            self.assertEqual(dest.read_bytes(), b"abcde")

    def test_size_mismatch_records_both_sizes_and_stops(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            rolled = root / "rolled"
            raw_dir.mkdir()
            partial = raw_dir / "phys2013.csv.partial"
            partial.write_bytes(b"short")

            def resume(url: str, path: Path, start: int) -> None:
                del url, start
                with path.open("ab") as handle:
                    handle.write(b"still-short")

            with self.assertRaises(SizeMismatch) as caught:
                download(
                    "http://example.test/phys2013.csv",
                    raw_dir / "phys2013.csv",
                    100,
                    resume=resume,
                )
            self.assertEqual(caught.exception.expected, 100)
            self.assertEqual(caught.exception.received, len(b"shortstill-short"))
            note = record_size_mismatch(
                2013,
                caught.exception.expected,
                caught.exception.received,
                rolled,
            )
            text = note.read_text(encoding="utf-8")
            self.assertIn("expected_bytes=100", text)
            self.assertIn(f"received_bytes={caught.exception.received}", text)
            self.assertFalse((rolled / "2013.csv").exists())
            self.assertFalse((rolled / "2013.count.txt").exists())

    def test_skip_when_rolled_file_and_count_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rolled = root / "rolled"
            raw_dir = root / "raw"
            rolled.mkdir()
            raw_dir.mkdir()
            (rolled / "2013.csv").write_text("already\n", encoding="utf-8")
            (rolled / "2013.count.txt").write_text(
                "year=2013\ngrouped_rows=4\nreceived_bytes=1\nexpected_bytes=1\n"
                "gender_source=pgender\n",
                encoding="utf-8",
            )
            self.assertTrue(rolled_year_done(2013, rolled))
            path = roll_year(2013, raw_dir=raw_dir, rolled_dir=rolled)
            self.assertEqual(path, rolled / "2013.csv")
            self.assertFalse((raw_dir / "phys2013.csv").exists())

    def test_count_is_written_before_summaries_and_raw_is_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rolled = root / "rolled"
            groups = {
                ("Internal Medicine", "1111111111", "M"): {
                    name: Running()
                    for name in (
                        "line_srvc_cnt",
                        "bene_unique_cnt",
                        "bene_day_srvc_cnt",
                        "average_submitted_chrg_amt",
                        "average_medicare_payment_amt",
                    )
                }
            }
            groups[("Internal Medicine", "1111111111", "M")]["line_srvc_cnt"].add(1.0)
            groups[("Internal Medicine", "1111111111", "M")]["line_srvc_cnt"].add(3.0)
            order: list[str] = []
            original = Path.write_text

            def spy(path: Path, text: str, *args, **kwargs):
                order.append(path.name)
                return original(path, text, *args, **kwargs)

            Path.write_text = spy
            try:
                out = write_rolled(
                    2013,
                    groups,
                    source_rows=2,
                    received=NBER_2013_BYTES,
                    expected=NBER_2013_BYTES,
                    gender_source="pgender",
                    rolled_dir=rolled,
                )
            finally:
                Path.write_text = original
            self.assertEqual(order[0], "2013.count.txt")
            text = (rolled / "2013.count.txt").read_text(encoding="utf-8")
            self.assertIn("grouped_rows=1", text)
            self.assertIn(f"received_bytes={NBER_2013_BYTES}", text)
            self.assertIn(f"expected_bytes={NBER_2013_BYTES}", text)
            self.assertIn("gender_source=pgender", text)
            with out.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["line_srvc_cnt_median"], "2.0")
            self.assertNotEqual(rows[0]["line_srvc_cnt_std"], "")

    def test_2012_gap_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            note = record_2012_gap(Path(tmp))
            text = note.read_text(encoding="utf-8")
            self.assertIn("year=2012", text)
            self.assertIn("skipped", text)
            self.assertIn("not invented", text)

    def test_resources_open_supplies_url_and_a_mismatch_stops(self) -> None:
        """Drive roll_year from a stub resources page. The URL is not invented."""
        opened = {
            "data": [
                {
                    "file_name": "MUP_PHY_R25_P04_V20_D16_Prov_Svc.csv",
                    "file_size": 8,
                    "file_url": "https://data.cms.gov/sites/default/files/opened/MUP_PHY_R25_P04_V20_D16_Prov_Svc.csv",
                }
            ]
        }
        url, expected = csv_from_resources(opened)
        self.assertTrue(url.endswith("MUP_PHY_R25_P04_V20_D16_Prov_Svc.csv"))
        self.assertEqual(expected, 8)

        def opener(page: str) -> str:
            self.assertIn("/dataset/", page)
            self.assertTrue(page.endswith("/resources"))
            return json.dumps(opened)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            rolled = root / "rolled"
            sex = root / "npi_sex.csv"
            raw_dir.mkdir()
            sex.write_text("NPI,nppes_provider_gender\n4444444444,M\n", encoding="utf-8")
            body = b"short"

            def resume(download_url: str, path: Path, start: int) -> None:
                self.assertEqual(download_url, url)
                self.assertEqual(start, 0)
                path.write_bytes(body)

            with self.assertRaises(SizeMismatch) as caught:
                roll_year(
                    2016,
                    raw_dir=raw_dir,
                    rolled_dir=rolled,
                    sex_path=sex,
                    opener=opener,
                    resume=resume,
                )
            note = (rolled / "2016.size.txt").read_text(encoding="utf-8")
            opened_note = (rolled / "2016.resources.txt").read_text(encoding="utf-8")
            self.assertEqual(caught.exception.expected, 8)
            self.assertEqual(caught.exception.received, len(body))
            self.assertIn("expected_bytes=8", note)
            self.assertIn(f"received_bytes={len(body)}", note)
            self.assertIn(f"csv_url={url}", opened_note)
            self.assertIn("opened_bytes=8", opened_note)
            self.assertNotIn("invented", opened_note)
            self.assertFalse((rolled / "2016.csv").exists())

    def test_finished_year_is_skipped_and_partial_resumes_through_roll(self) -> None:
        payload = {
            "data": [
                {
                    "file_name": "year.csv",
                    "file_size": 5,
                    "file_url": "https://data.cms.gov/sites/default/files/opened/year.csv",
                }
            ]
        }

        def opener(_page: str) -> str:
            return json.dumps(payload)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rolled = root / "rolled"
            raw_dir = root / "raw"
            rolled.mkdir()
            raw_dir.mkdir()
            (rolled / "2016.csv").write_text("already\n", encoding="utf-8")
            (rolled / "2016.count.txt").write_text(
                "year=2016\ngrouped_rows=1\n",
                encoding="utf-8",
            )
            calls: list[int] = []

            def resume(url: str, path: Path, start: int) -> None:
                calls.append(start)

            path = roll_year(
                2016,
                raw_dir=raw_dir,
                rolled_dir=rolled,
                opener=opener,
                resume=resume,
            )
            self.assertEqual(path, rolled / "2016.csv")
            self.assertEqual(calls, [])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            rolled = root / "rolled"
            sex = root / "npi_sex.csv"
            raw_dir.mkdir()
            header = ",".join(CMS_HEADER) + "\n"
            row = "4444444444,Lab,Ada,Miami,FL,33101,Pathology,88305,N,F,Y,2,2,2,10,4\n"
            raw = (header + row).encode("utf-8")
            payload["data"][0]["file_size"] = len(raw)
            partial = raw_dir / "year.csv.partial"
            partial.write_bytes(raw[:4])
            sex.write_text("NPI,nppes_provider_gender\n4444444444,F\n", encoding="utf-8")

            def resume(url: str, path: Path, start: int) -> None:
                self.assertEqual(start, 4)
                self.assertEqual(url, payload["data"][0]["file_url"])
                with path.open("ab") as handle:
                    handle.write(raw[start:])

            out = roll_year(
                2016,
                raw_dir=raw_dir,
                rolled_dir=rolled,
                sex_path=sex,
                opener=opener,
                resume=resume,
            )
            self.assertTrue(out.is_file())
            self.assertTrue((rolled / "2016.count.txt").is_file())
            self.assertFalse((raw_dir / "year.csv").exists())
            count = (rolled / "2016.count.txt").read_text(encoding="utf-8")
            self.assertIn("csv_url=" + payload["data"][0]["file_url"], count)
            self.assertIn(f"received_bytes={len(raw)}", count)
            self.assertIn(f"expected_bytes={len(raw)}", count)
            self.assertIn(f"opened_bytes={len(raw)}", count)
            with out.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["name"], "Lab, Ada")
            self.assertEqual(rows[0]["city"], "Miami")
            self.assertEqual(rows[0]["state"], "FL")
            self.assertEqual(rows[0]["zip"], "33101")
            self.assertEqual(rows[0]["nppes_provider_gender"], "F")
            self.assertEqual(rows[0]["line_srvc_cnt_mean"], "2.0")
            self.assertEqual(len([name for name in rows[0] if name.endswith(("_mean", "_sum", "_median", "_std", "_min", "_max"))]), 30)

    def test_missing_header_is_recorded_and_not_guessed(self) -> None:
        payload = {
            "data": [
                {
                    "file_name": "year.csv",
                    "file_size": 13,
                    "file_url": "https://data.cms.gov/sites/default/files/opened/year.csv",
                }
            ]
        }

        def opener(_page: str) -> str:
            return json.dumps(payload)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            rolled = root / "rolled"
            raw_dir.mkdir()

            def resume(url: str, path: Path, start: int) -> None:
                del url, start
                path.write_bytes(b"not,a,header\n")

            with self.assertRaises(HeaderMismatch):
                roll_year(
                    2017,
                    raw_dir=raw_dir,
                    rolled_dir=rolled,
                    opener=opener,
                    resume=resume,
                )
            text = (rolled / "2017.header.txt").read_text(encoding="utf-8")
            self.assertIn("guessed=no", text)
            self.assertIn("missing=", text)
            self.assertFalse((rolled / "2017.csv").exists())

    def test_expected_byte_counts(self) -> None:
        self.assertEqual(NBER_2013_BYTES, 2590718145)
        self.assertEqual(CMS_2014_BYTES, 2905565005)
        self.assertEqual(CMS_2015_BYTES, 2975342985)
        self.assertEqual(YEARS, (2013, 2014, 2015))


class DateRuleTest(unittest.TestCase):
    def test_month_greater_than_6_advances_the_year(self) -> None:
        start = datetime(2008, 1, 1)
        self.assertEqual(end_year(start, 5, None, None), 2013)
        later = datetime(2008, 8, 1)
        self.assertEqual(end_year(later, 5, None, None), 2014)

    def test_earliest_of_end_reinstatement_and_waiver(self) -> None:
        start = datetime(2010, 2, 12)
        waiver = datetime(2013, 1, 1)
        reinstatement = datetime(2014, 7, 1)
        self.assertEqual(end_year(start, 5, reinstatement, waiver), 2013)

    def test_capture_spellings_map_onto_table_2(self) -> None:
        self.assertEqual(normalize_type("1128a1"), "1128a1")
        self.assertEqual(normalize_type("1128(a)(1)"), "1128a1")
        self.assertEqual(normalize_type("1128(c)(3)(G)(i)"), "1128c3gi")
        self.assertEqual(normalize_type("1128(c)(3)(G)(ii)"), "1128c3gii")
        self.assertEqual(table2_years("1128a1"), 5)
        self.assertEqual(table2_years("1128b4"), 5)
        self.assertEqual(table2_years("1128c3gi"), 10)
        self.assertTrue(is_indefinite("1128c3gii"))
        self.assertIsNone(table2_years("1128c3gii"))
        self.assertIsNone(table2_years("1128b6"))
        self.assertIsNone(table2_years("1128b7"))

    def test_indefinite_rows_stay_out_of_the_fraud_class(self) -> None:
        """Drive load_labels on the shipped June 27, 2017 capture.

        The indefinite count must equal the count of indefinite spellings in
        that file. A parenthesized code collapses to the same compact form.
        """
        self.assertTrue(LABEL_PATH.is_file())
        self.assertEqual(LABEL_PATH.stat().st_size, LEIE_BYTES)
        self.assertEqual(LEIE_BYTES, 12069440)
        spellings = _capture_excltypes(LABEL_PATH)
        self.assertIn("1128a1", spellings)
        self.assertIn("1128b4", spellings)
        self.assertNotIn("1128(a)(1)", spellings)
        indefinite_in_file = sum(
            count
            for code, count in spellings.items()
            if is_indefinite(normalize_type(code))
        )
        ends, indefinite = load_labels(LABEL_PATH)
        self.assertEqual(indefinite, indefinite_in_file)
        self.assertNotIn("1128c3gii", {normalize_type(code) for code in spellings})
        self.assertNotIn("1128c3gi", {normalize_type(code) for code in spellings})
        # A compact indefinite row, the form this file would have used, stays out.
        with tempfile.TemporaryDirectory() as tmp:
            extra = Path(tmp) / "plus.csv"
            _append_indefinite(LABEL_PATH, extra)
            extra_ends, extra_indefinite = load_labels(extra)
        self.assertEqual(extra_indefinite, indefinite_in_file + 1)
        self.assertNotIn("2222222222", extra_ends)
        self.assertEqual(table2_years(normalize_type("1128(c)(3)(G)(i)")), 10)

    def test_matching_capture_is_kept(self) -> None:
        """A file the size the June 27, 2017 URL returns is kept, not a mismatch."""
        self.assertTrue(LABEL_PATH.is_file())
        self.assertEqual(LABEL_PATH.stat().st_size, 12069440)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rolled = root / "rolled"
            rolled.mkdir()
            (rolled / "leie.size.txt").write_text("stale\n", encoding="utf-8")
            kept = ensure_labels(LABEL_PATH, rolled_dir=rolled)
        self.assertEqual(kept, LABEL_PATH)
        self.assertTrue(LABEL_PATH.is_file())
        self.assertEqual(LABEL_PATH.stat().st_size, LEIE_BYTES)
        self.assertFalse((rolled / "leie.size.txt").exists())

    def test_wrong_leie_size_records_both_and_stops(self) -> None:
        """A download whose size is not 12069440 records both sizes and stops."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrong = root / "leie.csv"
            payload = b"not-the-june-27-capture"
            wrong.write_bytes(payload)
            with self.assertRaises(LabelSizeMismatch) as caught:
                ensure_labels(wrong, rolled_dir=root / "rolled")
            self.assertEqual(caught.exception.expected, LEIE_BYTES)
            self.assertEqual(caught.exception.received, len(payload))
            self.assertFalse(wrong.exists())
            note = root / "rolled" / "leie.size.txt"
            text = note.read_text(encoding="utf-8")
            self.assertIn(f"expected_bytes={LEIE_BYTES}", text)
            self.assertIn(f"received_bytes={len(payload)}", text)
            self.assertTrue(LABEL_PATH.is_file())
            self.assertEqual(LABEL_PATH.stat().st_size, LEIE_BYTES)
            score = Path(__file__).resolve().parents[1] / "models" / "paper_replicate.json"
            sentinel = root / "score.json"
            sentinel.write_text("{}\n", encoding="utf-8")
            record_label_mismatch(
                LEIE_BYTES,
                len(payload),
                rolled_dir=root / "rolled2",
                out_path=sentinel,
            )
            self.assertFalse(sentinel.exists())
            if score.is_file():
                self.assertGreater(score.stat().st_size, 0)


def _capture_excltypes(path: Path) -> dict[str, int]:
    """Count EXCLTYPE spellings in the shipped June 27, 2017 capture."""
    counts: dict[str, int] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            code = (row.get("EXCLTYPE") or "").strip().strip('"')
            counts[code] = counts.get(code, 0) + 1
    return counts


def _append_indefinite(source: Path, dest: Path) -> None:
    """Copy the capture and add one compact 1128c3gii row, the file's own spelling style."""
    dest.write_bytes(source.read_bytes())
    with dest.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["2222222222", "", "", "", "", "", "", "2222222222", "", "", "", "", "", "1128c3gii", "20100101", "00000000", "00000000", ""])


class UndersampleAndForestTest(unittest.TestCase):
    def _frame(self) -> pd.DataFrame:
        rows = []
        for index in range(12):
            rows.append(
                {
                    "provider_type": "Internal Medicine",
                    "npi": f"{index:010d}",
                    "nppes_provider_gender": "M",
                    "year": 2013,
                    "line_srvc_cnt_mean": float(index + 10),
                    "fraud": 1,
                }
            )
        for index in range(120):
            rows.append(
                {
                    "provider_type": "Cardiology",
                    "npi": f"{1000 + index:010d}",
                    "nppes_provider_gender": "F",
                    "year": 2014,
                    "line_srvc_cnt_mean": float(index),
                    "fraud": 0,
                }
            )
        return pd.DataFrame(rows)

    def test_keeps_every_fraud_row_and_nine_clean_per_fraud(self) -> None:
        sample, fraud_rows, clean_rows = undersample(self._frame())
        self.assertEqual(fraud_rows, 12)
        self.assertEqual(clean_rows, 9 * 12)
        self.assertEqual(int(sample["fraud"].sum()), 12)
        self.assertLessEqual(clean_rows, CLEAN_PER_FRAUD * fraud_rows)

    def test_forest_sets_only_estimators_and_records_the_stand_in(self) -> None:
        kwargs = forest_kwargs()
        self.assertEqual(kwargs["n_estimators"], 100)
        self.assertEqual(kwargs["random_state"], 0)
        self.assertNotIn("max_features", kwargs)
        model = new_forest()
        self.assertEqual(model.n_estimators, 100)
        self.assertEqual(model.random_state, 0)
        self.assertIsNone(model.max_depth)

    def test_fit_writes_the_score_beside_the_paper_cell(self) -> None:
        frame = self._frame()
        ends = {f"{index:010d}": 2014 for index in range(12)}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "paper_replicate.json"
            payload = fit_and_write(frame, ends, indefinite=2, out_path=out)
            written = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(written["paper_auc"], PAPER_AUC)
        self.assertEqual(written["paper_auc"], 0.87302)
        self.assertGreater(written["new_auc"], 0)
        self.assertLessEqual(written["new_auc"], 1)
        self.assertEqual(written["fraud_rows"], 12)
        self.assertEqual(written["clean_rows_kept"], 108)
        self.assertEqual(written["indefinite_rows_left_out"], 2)
        self.assertEqual(written["skipped_year"], 2012)
        self.assertEqual(written["years"], [2013, 2014, 2015])
        self.assertEqual(written["feature_subspace"], "unset")
        self.assertIn("not a paper seed", written["random_state_note"])
        self.assertIn("RepeatedStratifiedKFold", written["cv"])
        self.assertEqual(payload["paper_auc"], 0.87302)


if __name__ == "__main__":
    unittest.main()

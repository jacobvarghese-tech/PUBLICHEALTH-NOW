"""In-memory label rules. Does not load a rolled year and does not fit a forest."""

from __future__ import annotations

import unittest

import numpy as np

from scripts.label_islands import (
    check_codes,
    label_provider_years,
    parse_leie_date,
    slice_width,
)

APP_CODES = ["1128a1", "1128a3", "1128b6", "1128b7"]
APP_SENTENCE = (
    "A provider-year is positive when its NPI matches a 10-digit NPI, "
    "EXCLTYPE is one of those four codes, and the year of EXCLDATE is after "
    "the billing year. The earliest qualifying exclusion counts. Same-year "
    "and earlier exclusions are not positive. A zero date and an 00000000 "
    "date are blank. Blank NPI and 0000000000 do not join."
)


def _app_spec(codes: list[str] | None = None) -> dict:
    return {
        "name": "in_memory",
        "date_rule": "app_year",
        "codes": list(codes or APP_CODES),
        "train_positive": APP_SENTENCE,
    }


def _leie(npi: str, excltype: str, excldate: str, rein: str = "0", waiver: str = "0") -> dict:
    return {
        "NPI": npi,
        "EXCLTYPE": excltype,
        "EXCLDATE": excldate,
        "REINDATE": rein,
        "WAIVERDATE": waiver,
    }


def _year(npi: str, year: int) -> dict:
    return {"npi": npi, "year": year}


class LabelIslandsTest(unittest.TestCase):
    def test_zero_date_is_blank(self) -> None:
        self.assertIsNone(parse_leie_date("0"))
        labels, info = label_provider_years(
            [
                _leie("1111111111", "1128a1", "0"),
                _leie("2222222222", "1128a3", "20200101"),
                _leie("3333333333", "1128b6", "20210101"),
                _leie("4444444444", "1128b7", "20190101"),
                _leie("5555555555", "1128a1", "20220101"),
            ],
            [
                _year("1111111111", 2018),
                _year("2222222222", 2018),
                _year("3333333333", 2018),
                _year("4444444444", 2018),
                _year("5555555555", 2018),
            ],
            _app_spec(),
        )
        self.assertEqual(labels[0], 0)
        self.assertEqual(info["missing_codes"], [])

    def test_eight_zeros_are_blank(self) -> None:
        self.assertIsNone(parse_leie_date("00000000"))
        self.assertIsNone(parse_leie_date(""))
        labels, _info = label_provider_years(
            [
                _leie("1111111111", "1128a1", "00000000"),
                _leie("2222222222", "1128a3", "20200101"),
                _leie("3333333333", "1128b6", "20210101"),
                _leie("4444444444", "1128b7", "20190101"),
                _leie("5555555555", "1128a1", "20220101"),
            ],
            [
                _year("1111111111", 2018),
                _year("2222222222", 2018),
                _year("3333333333", 2018),
                _year("4444444444", 2018),
                _year("5555555555", 2018),
            ],
            _app_spec(),
        )
        self.assertEqual(labels[0], 0)

    def test_same_year_exclusion_is_not_positive(self) -> None:
        labels, _info = label_provider_years(
            [
                _leie("1111111111", "1128a1", "20180601"),
                _leie("2222222222", "1128a3", "20190101"),
                _leie("3333333333", "1128b6", "20200101"),
                _leie("4444444444", "1128b7", "20170101"),
                _leie("5555555555", "1128a1", "20210101"),
            ],
            [
                _year("1111111111", 2018),
                _year("2222222222", 2018),
                _year("3333333333", 2018),
                _year("4444444444", 2018),
                _year("5555555555", 2018),
            ],
            _app_spec(),
        )
        self.assertEqual(labels[0], 0)

    def test_later_year_four_code_row_is_positive(self) -> None:
        labels, _info = label_provider_years(
            [
                _leie("1111111111", "1128a1", "20200601"),
                _leie("2222222222", "1128a3", "20170101"),
                _leie("3333333333", "1128b6", "20180101"),
                _leie("4444444444", "1128b7", "20160101"),
                _leie("5555555555", "1128a2", "20210101"),
            ],
            [
                _year("1111111111", 2018),
                _year("2222222222", 2018),
                _year("3333333333", 2018),
                _year("4444444444", 2018),
                _year("5555555555", 2018),
            ],
            _app_spec(),
        )
        self.assertEqual(labels, [1, 0, 0, 0, 0])

    def test_indefinite_code_is_left_out(self) -> None:
        spec = {
            "name": "indefinite_in_memory",
            "date_rule": "paper_end",
            "codes": ["1128a1", "1128c3gii"],
            "train_positive": (
                "Add the minimum length of the exclusion to the exclusion start "
                "date. The indefinite code is left out of the fraud class."
            ),
        }
        labels, info = label_provider_years(
            [
                _leie("1111111111", "1128c3gii", "20100101"),
                _leie("2222222222", "1128a1", "20100101"),
                _leie("3333333333", "1128a1", "20120101"),
                _leie("4444444444", "1128a1", "0"),
                _leie("5555555555", "1128a1", "00000000"),
            ],
            [
                _year("1111111111", 2018),
                _year("2222222222", 2018),
                _year("3333333333", 2018),
                _year("4444444444", 2018),
                _year("5555555555", 2018),
            ],
            spec,
        )
        self.assertEqual(labels[0], 0)
        self.assertGreaterEqual(info["indefinite_left_out"], 1)
        self.assertEqual(labels[1], 0)

    def test_blank_npi_and_all_zero_npi_do_not_join(self) -> None:
        labels, _info = label_provider_years(
            [
                _leie("", "1128a1", "20200101"),
                _leie("0000000000", "1128a1", "20200101"),
                _leie("1111111111", "1128a1", "20200101"),
                _leie("2222222222", "1128a3", "20190101"),
                _leie("3333333333", "1128b6", "20180101"),
            ],
            [
                _year("", 2018),
                _year("0000000000", 2018),
                _year("1111111111", 2018),
                _year("2222222222", 2018),
                _year("3333333333", 2018),
            ],
            _app_spec(),
        )
        self.assertEqual(labels[0], 0)
        self.assertEqual(labels[1], 0)
        self.assertEqual(labels[2], 1)

    def test_missing_code_checker_names_the_token(self) -> None:
        spec = {
            "name": "missing",
            "date_rule": "paper_end",
            "codes": ["1128a1", "1128c3gii"],
            "train_positive": "paper end date",
        }
        missing = check_codes(spec, {"1128a1", "1128a3"})
        self.assertIn("1128c3gii", missing)
        self.assertEqual(check_codes(spec, {"1128a1", "1128c3gii"}), [])

    def test_demo_npi_is_not_a_label(self) -> None:
        labels, _info = label_provider_years(
            [
                _leie("1124725817", "1128a1", "20200101"),
                _leie("1639879034", "1128a3", "20200101"),
                _leie("1111111111", "1128b6", "20200101"),
                _leie("2222222222", "1128b7", "20170101"),
                _leie("3333333333", "1128a1", "20160101"),
            ],
            [
                _year("1124725817", 2018),
                _year("1639879034", 2018),
                _year("1111111111", 2018),
                _year("2222222222", 2018),
                _year("3333333333", 2018),
            ],
            _app_spec(),
        )
        self.assertEqual(labels[0], 0)
        self.assertEqual(labels[1], 0)
        self.assertEqual(labels[2], 1)

    def test_slice_width_is_the_vote_step_slice(self) -> None:
        """The shipped width is scores strictly above 0.

        A 99th-percentile cutoff on this zero-heavy rank is the zero step, so
        it counts every row and fails a 2 percent cap while the 95th
        percentile stays on 0. The shipped function leaves those zeros out.
        A 2.46 percent vote-step share, the recorded 2023 shape, still fails
        the cap.
        """
        scores = np.zeros(1000, dtype=float)
        scores[-9:] = 0.01
        cutoff = float(np.percentile(scores, 99))
        percentile_share = float(np.sum(scores >= cutoff)) / float(len(scores))
        self.assertEqual(cutoff, 0.0)
        self.assertGreater(percentile_share, 0.02)
        self.assertEqual(float(np.percentile(scores, 95)), 0.0)
        width = slice_width(scores)
        self.assertAlmostEqual(width, 0.009)
        self.assertLess(width, percentile_share)
        self.assertLessEqual(width, 0.02)

        recorded = np.zeros(10000, dtype=float)
        recorded[-246:] = 0.01
        recorded_width = slice_width(recorded)
        self.assertAlmostEqual(recorded_width, 0.0246)
        self.assertGreater(recorded_width, 0.02)
        self.assertEqual(float(np.percentile(recorded, 95)), 0.0)
        self.assertEqual(slice_width(np.array([])), 0.0)
        self.assertEqual(slice_width(np.zeros(4)), 0.0)


if __name__ == "__main__":
    unittest.main()

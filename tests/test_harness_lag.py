"""Fixture checks for the label-lag IsolationForest helpers.

The million-row years are not loaded. Expected counts come from the fixture
and from the shipped functions.
"""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from scripts.harness_lag import (
    DEMO_NPIS,
    FEATURE_COLUMNS,
    MIN_ORDINARY,
    SAMPLE_CAP,
    SAVED_FIT_BEFORE,
    SpecialtyReservoir,
    abnormality_from_decision,
    assert_fit_window,
    drop_demo_npis,
    fit_window,
    forests_to_fit,
    new_forest,
    ordinary_fit_rows,
    prepare_fit_matrix,
    sample_ordinary,
    format_grade,
    score_year,
    top_1_list_is_short,
    within_specialty_slice,
)
from scripts.join_labels import earliest_exclusion_years, is_positive_label
from scripts.train import label_from_columns


def _feature_row(npi: str, year: str, specialty: str, growth: str, marker: str) -> dict[str, str]:
    return {
        "NPI": npi,
        "Year": year,
        "Specialty": specialty,
        "Service count": marker,
        "Beneficiary count": "10",
        "Average charge": "20",
        "Average payment": "10",
        "Charge-to-payment ratio": "2",
        "Top-code share": "0.1",
        "Growth": growth,
    }


class LabelLagRulesTest(unittest.TestCase):
    def test_same_year_and_earlier_are_ordinary(self) -> None:
        exclusion_years = {"1111111111": 2021, "2222222222": 2020, "3333333333": 2022}
        labels = label_from_columns(
            ["1111111111", "2222222222", "3333333333", "4444444444"],
            ["2021", "2021", "2021", "2021"],
            exclusion_years,
        )
        self.assertEqual(labels, [0, 0, 1, 0])
        self.assertFalse(is_positive_label(2021, 2021))
        self.assertFalse(is_positive_label(2021, 2020))
        self.assertTrue(is_positive_label(2021, 2022))

    def test_demo_npis_leave_the_fit(self) -> None:
        frame = pd.DataFrame(
            [
                _feature_row("1124725817", "2019", "Cardiology", "1", "1"),
                _feature_row("1639879034", "2019", "Cardiology", "1", "2"),
                _feature_row("3333333333", "2019", "Cardiology", "1", "3"),
            ]
        )
        frame["label"] = 0
        kept = drop_demo_npis(frame)
        self.assertEqual(kept["NPI"].tolist(), ["3333333333"])
        ordinary, _dropped = ordinary_fit_rows(frame)
        self.assertTrue(set(DEMO_NPIS).isdisjoint(ordinary["NPI"].astype(str)))

    def test_nan_rows_drop_when_the_forest_rejects_nan(self) -> None:
        frame = pd.DataFrame(
            [
                _feature_row("3333333333", "2019", "Cardiology", "", "1"),
                _feature_row("4444444444", "2019", "Cardiology", "1.5", "2"),
            ]
        )
        matrix, dropped = prepare_fit_matrix(frame, accepts_nan=False)
        self.assertEqual(dropped, 1)
        self.assertEqual(len(matrix), 1)
        self.assertFalse(matrix.isna().any().any())
        self.assertNotEqual(float(matrix["Growth"].iloc[0]), 0.0)
        kept, _ = prepare_fit_matrix(frame, accepts_nan=True)
        self.assertEqual(len(kept), 2)
        self.assertTrue(pd.isna(kept["Growth"].iloc[0]))

    def test_specialty_under_256_is_skipped(self) -> None:
        counts = {"Cardiology": 256, "Tiny": 255, "": 10}
        fitted, skipped = forests_to_fit(counts, MIN_ORDINARY)
        self.assertEqual(fitted, ["Cardiology"])
        self.assertEqual(skipped, ["", "Tiny"])

    def test_sample_draw_is_at_most_5000_with_seed_1(self) -> None:
        positions = np.arange(8000)
        drawn = sample_ordinary(positions, SAMPLE_CAP, seed=1)
        self.assertEqual(len(drawn), 5000)
        self.assertEqual(len(drawn), len(set(drawn.tolist())))
        again = sample_ordinary(positions, SAMPLE_CAP, seed=1)
        self.assertTrue(np.array_equal(drawn, again))
        reservoir = SpecialtyReservoir(cap=5, seed=1)
        first = pd.DataFrame({"Service count": np.arange(4, dtype=float)})
        second = pd.DataFrame({"Service count": np.arange(10, 16, dtype=float)})
        reservoir.add(first)
        self.assertIsInstance(reservoir.values, np.ndarray)
        self.assertFalse(hasattr(reservoir, "blocks"))
        reservoir.add(second)
        self.assertLessEqual(len(reservoir.values), 5)
        self.assertEqual(reservoir.seen, 10)
        # Fill copies in order. Replacement starts only after the cap is full.
        # U=[0.8, 0.01] at stream indexes 3 and 4 copies 100 and 101.
        mixed = SpecialtyReservoir(cap=5, seed=1)
        mixed.values = np.array([[0.0], [1.0], [2.0]])
        mixed.seen = 3
        mixed._rng = type(
            "SeqRng",
            (),
            {"random": staticmethod(lambda n: np.array([0.8, 0.01][: int(n)]))},
        )()
        mixed.add(pd.DataFrame({"Service count": np.array([100.0, 101.0])}))
        self.assertEqual(mixed.values[:, 0].tolist(), [0.0, 1.0, 2.0, 100.0, 101.0])
        self.assertEqual(mixed.seen, 5)
        # A first batch larger than the cap copies the first cap rows.
        first_batch = SpecialtyReservoir(cap=3, seed=1)
        first_batch._rng = type(
            "SeqRng",
            (),
            {"random": staticmethod(lambda n: np.array([0.0, 0.1, 0.2, 0.9, 0.95][: int(n)]))},
        )()
        first_batch.add(pd.DataFrame({"Service count": np.array([0.0, 1.0, 2.0, 3.0, 4.0])}))
        self.assertEqual(first_batch.values[:, 0].tolist(), [0.0, 1.0, 2.0])
        self.assertEqual(first_batch.seen, 5)
        # After the reservoir is full, a low draw still writes kept[j].
        full = SpecialtyReservoir(cap=5, seed=1)
        full.values = np.array([[0.0], [1.0], [2.0], [3.0], [4.0]])
        full.seen = 5
        full._rng = type("FixedRng", (), {"random": staticmethod(lambda n: np.full(n, 0.01))})()
        full.add(pd.DataFrame({"Service count": np.array([100.0, 101.0])}))
        self.assertEqual(full.values[0, 0], 101.0)
        self.assertEqual(len(full.values), 5)
        self.assertEqual(full.seen, 7)
        big = SpecialtyReservoir(cap=5, seed=1)
        big.add(pd.DataFrame({"Service count": np.arange(20, dtype=float)}))
        self.assertEqual(len(big.values), 5)
        self.assertEqual(big.seen, 20)

    def test_lower_decision_function_is_more_abnormal_and_ties_stay_inside(self) -> None:
        decision = np.array([0.4, 0.2, 0.2, -0.5, 0.9])
        abnormality = abnormality_from_decision(decision)
        self.assertTrue(np.all(abnormality == -decision))
        labels = np.array([0, 1, 0, 1, 0])
        captured, fraud_count = within_specialty_slice(abnormality, labels, 99)
        self.assertEqual(fraud_count, 2)
        self.assertGreaterEqual(captured, 1)
        tied = np.array([1.0, 1.0, 1.0, 1.0])
        tied_labels = np.array([1, 0, 0, 0])
        captured_ties, _ = within_specialty_slice(tied, tied_labels, 99)
        self.assertEqual(captured_ties, 1)
        graded = score_year(
            pd.DataFrame(
                [
                    {
                        **_feature_row("5555555555", "2021", "Cardiology", "1", "9"),
                        "label": 1,
                    }
                ]
            ),
            {},
        )
        self.assertEqual(graded["fraud_denominator"], 0)
        self.assertEqual(graded["unscored_fraud_rows"], 1)

    def test_fit_window_excludes_the_grade_year_and_2024(self) -> None:
        window = fit_window(2021)
        self.assertNotIn(2021, window)
        self.assertNotIn(SAVED_FIT_BEFORE, window)
        self.assertTrue(all(year < 2021 for year in window))
        assert_fit_window(window, 2021)
        with self.assertRaises(ValueError):
            assert_fit_window((2019, 2020, 2021), 2021)
        with self.assertRaises(ValueError):
            assert_fit_window((2019, 2024), 2025)

    def test_score_year_ranks_without_calling_predict(self) -> None:
        rows = []
        for index in range(20):
            row = _feature_row(f"{index:010d}", "2021", "Cardiology", "0.1", str(index + 1))
            rows.append(row)
        frame = pd.DataFrame(rows)
        frame["label"] = 0
        frame.loc[0, "label"] = 1
        frame.loc[0, "Service count"] = "99999"
        ordinary, dropped = ordinary_fit_rows(frame)
        self.assertEqual(dropped, 0)
        matrix, nan_dropped = prepare_fit_matrix(ordinary, accepts_nan=True)
        self.assertEqual(nan_dropped, 0)
        model = new_forest()
        model.n_estimators = 10
        model.fit(matrix.loc[:, list(FEATURE_COLUMNS)].to_numpy(dtype=float))
        summary = score_year(frame, {"Cardiology": model})
        self.assertEqual(summary["fraud_denominator"], 1)
        self.assertEqual(summary["unscored_fraud_rows"], 0)
        self.assertIn("fraud_top_1", summary)
        # One score covering half or more is not short and prints no.
        # A diverse year is short and prints yes.
        self.assertFalse(top_1_list_is_short(np.array([1.0, 1.0, 0.2])))
        self.assertEqual(
            format_grade(2021, {"top_1_list_short": top_1_list_is_short(np.array([1.0, 1.0, 0.2])), "fraud_top_1": 0, "fraud_top_5": 0, "fraud_denominator": 0, "unscored_fraud_rows": 0, "distinct_score_count": 2}).split("top_1_list_short=")[-1],
            "no",
        )
        self.assertTrue(top_1_list_is_short(np.array([0.1, 0.2, 0.3, 0.4])))
        self.assertEqual(
            format_grade(2021, {"top_1_list_short": top_1_list_is_short(np.array([0.1, 0.2, 0.3, 0.4])), "fraud_top_1": 0, "fraud_top_5": 0, "fraud_denominator": 0, "unscored_fraud_rows": 0, "distinct_score_count": 4}).split("top_1_list_short=")[-1],
            "yes",
        )

    def test_earliest_exclusion_years_is_the_join_helper(self) -> None:
        self.assertTrue(callable(earliest_exclusion_years))


if __name__ == "__main__":
    unittest.main()

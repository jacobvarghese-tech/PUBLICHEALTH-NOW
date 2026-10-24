"""Drive the shipped label helpers and the shipped slice helper.

Same-year and earlier exclusions stay ordinary. Later-year four-code matches
are positive. Demo NPIs are not labels. Ties at the cutoff stay inside the
slice. An unscored fraud row does not count. IsolationForest decision_function
is negated before a higher-is-flagged slice.
"""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.harness_lag import abnormality_from_decision
from scripts.optimized_rank import OptimizedRankModel, zero_tie_break
from scripts.paper_forest import PAPER_FEATURES
from scripts.join_labels import (
    DEMO_NPIS,
    earliest_exclusion_years,
    is_positive_label,
    write_training_file,
)
from scripts.train import label_from_columns, top_slice_share


def _write_leie(path: Path, rows: list[str]) -> None:
    path.write_text(
        "NPI,EXCLTYPE,EXCLDATE\n" + "\n".join(rows) + "\n",
        encoding="utf-8",
    )


class LabelSliceTest(unittest.TestCase):
    def test_later_year_only_and_demo_npis_are_not_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            leie = Path(tmp) / "UPDATED.csv"
            _write_leie(
                leie,
                [
                    "1111111111,1128a1,20250101",
                    "2222222222,1128a3,20240101",
                    "3333333333,1128b6,20230101",
                    "4444444444,1128b7,20260101",
                    "5555555555,1128a2,20260101",
                    "6666666666,1128a1,not-a-date",
                    "12,1128a1,20260101",
                    "1124725817,1128a1,20260101",
                    "1639879034,1128b7,20270101",
                    "1111111111,1128a1,20260101",
                ],
            )
            years = earliest_exclusion_years(leie)

            self.assertEqual(years["1111111111"], 2025)
            self.assertNotIn("5555555555", years)
            self.assertNotIn("6666666666", years)
            self.assertNotIn("12", years)

            npis = [
                "1111111111",
                "1111111111",
                "2222222222",
                "3333333333",
                "4444444444",
                "5555555555",
                "7777777777",
            ]
            billing = ["2024", "2025", "2024", "2024", "2024", "2024", "2024"]
            labels = label_from_columns(npis, billing, years)
            # Later four-code year is positive. Same-year, earlier, other code,
            # and an unmatched NPI stay ordinary.
            self.assertEqual(labels, [1, 0, 0, 0, 1, 0, 0])
            self.assertFalse(is_positive_label(2024, 2024))
            self.assertFalse(is_positive_label(2024, 2023))
            self.assertTrue(is_positive_label(2024, 2025))

            rolled = Path(tmp) / "rolled"
            rolled.mkdir()
            with (rolled / "2013.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["NPI", "Year"])
                writer.writeheader()
                for npi in ("1111111111", "1124725817", "1639879034", "7777777777"):
                    writer.writerow({"NPI": npi, "Year": "2013"})
            training = Path(tmp) / "physician.csv"
            fraud_rows, _clean = write_training_file(
                leie_path=leie,
                rolled_dir=rolled,
                training_path=training,
                counts_path=Path(tmp) / "expand_counts.txt",
                billing_years=(2013,),
            )
            with training.open(encoding="utf-8", newline="") as handle:
                written = list(csv.DictReader(handle))
            written_npis = {row["NPI"] for row in written}
            self.assertTrue(DEMO_NPIS.isdisjoint(written_npis))
            self.assertEqual(fraud_rows, 1)
            self.assertEqual(
                [row["label"] for row in written if row["NPI"] == "1111111111"],
                ["1"],
            )

    def test_ties_stay_inside_and_unscored_fraud_does_not_count(self) -> None:
        scores = [0.2, 0.8, 0.8, 0.1]
        labels = [0, 1, 1, 0]
        captured, fraud_count, share = top_slice_share(scores, labels, 99)
        self.assertEqual((captured, fraud_count, share), (2, 2, 1.0))

        scored_scores = [0.1, 0.4, 0.9]
        scored_labels = [1, 0, 0]
        captured_scored, fraud_scored, _ = top_slice_share(scored_scores, scored_labels, 99)
        self.assertEqual(fraud_scored, 1)
        self.assertEqual(captured_scored, 0)
        # The second fraud row was never scored, so it is not in the denominator.
        self.assertEqual(fraud_scored, sum(scored_labels))

    def test_zero_tie_break_promotes_a_tied_row_and_ignores_a_one_value_score(self) -> None:
        primary = np.array([0.0] * 198 + [0.02, 0.03])
        secondary = np.array([0.1] * 198 + [0.0, 0.0])
        secondary[1] = 0.9
        secondary[2] = 0.9
        ranked = zero_tie_break(primary, secondary, vote_step=0.01, percentile=99)
        self.assertEqual(float(ranked[1]), 0.01)
        self.assertEqual(float(ranked[2]), 0.01)
        self.assertEqual(float(ranked[0]), 0.0)
        # The promoted row is inside a higher-is-flagged slice of the zero group.
        zero_labels = [0] * 198
        zero_labels[1] = 1
        captured, fraud_count, _ = top_slice_share(
            ranked[:198].tolist(),
            zero_labels,
            99,
        )
        self.assertEqual((captured, fraud_count), (1, 1))
        flat = zero_tie_break(primary, np.zeros(len(primary)))
        self.assertTrue(np.array_equal(flat, primary))
        # A tie at the secondary cutoff is promoted as a whole when that
        # keeps the 95th percentile on 0.
        wide = np.zeros(100)
        wide_secondary = np.full(100, 0.1)
        wide_secondary[0] = 0.9
        wide_secondary[1] = 0.9
        wide_ranked = zero_tie_break(wide, wide_secondary, vote_step=0.01, percentile=99)
        self.assertEqual(float(wide_ranked[0]), 0.01)
        self.assertEqual(float(wide_ranked[1]), 0.01)
        self.assertEqual(float(np.percentile(wide_ranked, 95)), 0.0)
        # A tie that would move the 95th percentile off 0 is dropped whole.
        # It is not trimmed one row early.
        tight = np.array([0.0, 0.0, 0.0, 0.0, 0.02])
        tight_secondary = np.array([0.1, 0.9, 0.9, 0.2, 0.0])
        tight_ranked = zero_tie_break(tight, tight_secondary, vote_step=0.01, percentile=75)
        self.assertTrue(np.array_equal(tight_ranked, tight))

    def test_saved_rank_model_scores_a_frame_without_an_outside_score_file(self) -> None:
        class _Stub:
            def __init__(self, value: float) -> None:
                self.value = value
                self.n_estimators = 2

            def predict_proba(self, matrix):
                rows = len(matrix)
                positive = np.full(rows, self.value)
                return np.column_stack([1.0 - positive, positive])

        frame = pd.DataFrame(
            {
                "provider_type": ["Lab", "Lab", "Lab", "Lab"],
                "nppes_provider_gender": ["M", "M", "F", "F"],
            }
        )
        for name in PAPER_FEATURES:
            frame[name] = [1.0, 9.0, 2.0, 3.0]
        columns = ["provider_type", "nppes_provider_gender", *PAPER_FEATURES]
        model = OptimizedRankModel(
            primary_model=_Stub(0.0),
            primary_columns=columns,
            secondary_model=_Stub(0.8),
            secondary_columns=columns,
            fit_years=[2013],
            n_estimators=2,
            max_depth=2,
            min_samples_leaf=1,
            class_weight="balanced_subsample",
            clean_per_fraud=9,
            fraud_rows=1,
            clean_rows=9,
        )
        # A one-value secondary score is not a promotion. The object still
        # scores the frame from the two forests it carries.
        scores = model.score_frame(frame, chunk=2)
        self.assertEqual(len(scores), 4)
        self.assertTrue(np.all(scores == 0.0))
        self.assertIn("OptimizedRankModel", model.parameter_summary())
        self.assertNotIn(2024, model.fit_years)

    def test_isolation_forest_scores_are_negated_before_the_slice(self) -> None:
        decision = np.array([0.4, 0.1, -0.8, 0.2])
        labels = [0, 0, 1, 0]
        raw_captured, raw_fraud, _ = top_slice_share(decision.tolist(), labels, 99)
        self.assertEqual(raw_captured, 0)
        abnormality = abnormality_from_decision(decision)
        self.assertTrue(np.all(abnormality == -decision))
        captured, fraud_count, _ = top_slice_share(abnormality.tolist(), labels, 99)
        self.assertEqual((captured, fraud_count), (1, 1))
        self.assertGreater(float(abnormality[2]), float(abnormality[0]))


if __name__ == "__main__":
    unittest.main()

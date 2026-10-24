"""Helpers for the undersampled forest. No year CSV and no 100-tree fit."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from scripts.paper_forest_rus import (
    app_label,
    assert_trainable_years,
    fit_sample,
    forest_kwargs,
    new_forest,
    undersample,
)


class PaperForestRusTest(unittest.TestCase):
    def test_app_label_four_codes_and_later_year_only(self) -> None:
        self.assertTrue(app_label(2016, "1128a1", "20170101"))
        self.assertTrue(app_label(2016, "1128a3", "20200101"))
        self.assertTrue(app_label(2016, "1128b6", "20170101"))
        self.assertTrue(app_label(2016, "1128b7", "20170101"))
        self.assertFalse(app_label(2016, "1128a1", "20160101"))
        self.assertFalse(app_label(2016, "1128a1", "20150101"))
        self.assertFalse(app_label(2016, "1128b4", "20190101"))
        self.assertFalse(app_label(2016, "", "20190101"))

    def test_undersample_keeps_every_fraud_row_and_seeded_clean_draw(self) -> None:
        frame = pd.DataFrame(
            {
                "fraud": [1, 0, 1] + [0] * 30,
                "value": list(range(33)),
            }
        )
        sample, fraud_count, clean_count = undersample(frame, clean_per_fraud=9)
        self.assertEqual(fraud_count, 2)
        self.assertEqual(clean_count, 18)
        self.assertEqual(int((sample["fraud"] == 1).sum()), 2)
        self.assertEqual(int((sample["fraud"] == 0).sum()), 18)
        fraud_values = set(frame.loc[frame["fraud"] == 1, "value"])
        self.assertEqual(set(sample.loc[sample["fraud"] == 1, "value"]), fraud_values)
        expected = frame.loc[frame.fraud == 0].sample(n=18, replace=False, random_state=0).index
        kept_clean = sample.loc[sample["fraud"] == 0].index
        self.assertEqual(set(kept_clean), set(expected))

    def test_forest_kwargs_omit_max_features_and_class_weight(self) -> None:
        kwargs = forest_kwargs()
        self.assertEqual(kwargs, {"n_estimators": 100, "random_state": 0, "n_jobs": -1})
        self.assertNotIn("max_features", kwargs)
        self.assertNotIn("class_weight", kwargs)
        model = new_forest()
        self.assertEqual(model.n_estimators, 100)
        self.assertEqual(model.random_state, 0)
        self.assertEqual(model.n_jobs, -1)
        self.assertIsNone(model.class_weight)

    def test_fit_sample_writes_counts_before_fit(self) -> None:
        x = np.zeros((4, 2))
        y = np.array([1, 0, 0, 0])
        with tempfile.TemporaryDirectory() as tmp:
            counts_path = Path(tmp) / "paper_forest_rus_counts.txt"

            def _raise(self, X, y, sample_weight=None):
                raise RuntimeError("fit started")

            with patch("sklearn.ensemble.RandomForestClassifier.fit", _raise):
                with self.assertRaises(RuntimeError):
                    fit_sample(x, y, counts_path, fraud=2, clean=18, total=20, n_estimators=2)
            self.assertTrue(counts_path.is_file())
            text = counts_path.read_text(encoding="utf-8")
            self.assertIn("fraud=2", text)
            self.assertIn("clean=18", text)
            self.assertIn("total=20", text)
            self.assertIn(
                "The app's four codes (1128a1, 1128a3, 1128b6, 1128b7) were used.",
                text,
            )
            self.assertIn("The paper's Table 2 codes were not used.", text)

    def test_assert_trainable_years_rejects_2024(self) -> None:
        with self.assertRaises(ValueError) as caught:
            assert_trainable_years((2013, 2024))
        self.assertIn("2024", str(caught.exception))
        assert_trainable_years((2013, 2023))

    def test_tiny_fit_uses_two_trees(self) -> None:
        frame = pd.DataFrame({"fraud": [1, 1, 0, 0], "value": [3.0, 4.0, 0.0, 1.0]})
        sample, fraud_count, clean_count = undersample(frame, clean_per_fraud=1)
        x = sample[["value"]].to_numpy(dtype=float)
        y = sample["fraud"].to_numpy(dtype=int)
        with tempfile.TemporaryDirectory() as tmp:
            counts_path = Path(tmp) / "counts.txt"
            model = fit_sample(
                x,
                y,
                counts_path,
                fraud=fraud_count,
                clean=clean_count,
                total=fraud_count + clean_count,
                n_estimators=2,
            )
        self.assertEqual(model.n_estimators, 2)
        self.assertEqual(model.random_state, 0)
        self.assertIsNone(model.class_weight)


if __name__ == "__main__":
    unittest.main()

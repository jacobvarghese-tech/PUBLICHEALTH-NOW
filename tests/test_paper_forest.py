

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

import joblib
import numpy as np

from scripts.paper_forest import (
    N_ESTIMATORS,
    PAPER_FEATURES,
    RANDOM_STATE,
    app_label,
    fit_and_score,
    new_forest,
)
from scripts.paper_roll_year import rolled_header


def _write_year(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rolled_header())
        writer.writeheader()
        for row in rows:
            full = {name: "" for name in rolled_header()}
            full.update(row)
            for name in PAPER_FEATURES:
                full.setdefault(name, "1")
            writer.writerow(full)


def _row(year: int, npi: str, specialty: str, gender: str, mean: str) -> dict:
    values = {name: mean for name in PAPER_FEATURES}
    values.update(
        {
            "provider_type": specialty,
            "npi": npi,
            "nppes_provider_gender": gender,
            "year": str(year),
            "name": f"Name {npi}",
            "city": "Miami",
            "state": "FL",
            "zip": "33101",
        }
    )
    return values


class ForestContractTest(unittest.TestCase):
    def test_label_rule_requires_code_and_later_year(self) -> None:
        self.assertTrue(app_label(2016, "1128a1", "20170101"))
        self.assertTrue(app_label(2016, "1128a3", "20200101"))
        self.assertTrue(app_label(2016, "1128b6", "20170101"))
        self.assertTrue(app_label(2016, "1128b7", "20170101"))
        self.assertFalse(app_label(2016, "1128a1", "20160101"))
        self.assertFalse(app_label(2016, "1128a1", "20150101"))
        self.assertFalse(app_label(2016, "1128b4", "20190101"))
        self.assertFalse(app_label(2016, "", "20190101"))

    def test_constructor_settings(self) -> None:
        model = new_forest()
        self.assertEqual(model.n_estimators, N_ESTIMATORS)
        self.assertEqual(model.n_estimators, 100)
        self.assertEqual(model.random_state, RANDOM_STATE)
        self.assertEqual(model.random_state, 0)

    def test_fit_excludes_2024_and_scores_it(self) -> None:
        
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rolled = root / "rolled"
            leie = root / "UPDATED.csv"
            with leie.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["NPI", "EXCLTYPE", "EXCLDATE"])
                writer.writerow(["1111111111", "1128a1", "20180101"])
                writer.writerow(["2222222222", "1128b4", "20200101"])
                writer.writerow(["3333333333", "1128a3", "20140101"])
            for year, npi, specialty, gender, mean in (
                (2013, "1111111111", "Internal Medicine", "M", "9"),
                (2014, "2222222222", "Cardiology", "F", "1"),
                (2015, "3333333333", "Pathology", "F", "2"),
                (2024, "4444444444", "Clinical Laboratory", "M", "8"),
            ):
                _write_year(rolled / f"{year}.csv", [_row(year, npi, specialty, gender, mean)])
            payload = fit_and_score(
                rolled_dir=rolled,
                leie_path=leie,
                model_path=root / "paper_forest.joblib",
                note_path=root / "note.txt",
                share_path=root / "shares.json",
                score_dir=root / "scores",
                train_years=(2013, 2014, 2015),
                score_years=(2024,),
            )
            self.assertEqual(payload["train_years"], [2013, 2014, 2015])
            self.assertNotIn(2024, payload["train_years"])
            self.assertEqual(payload["fraud_rows"], 1)
            loaded = joblib.load(root / "paper_forest.joblib")
            model = loaded["model"]
            self.assertEqual(model.n_estimators, 100)
            self.assertEqual(model.random_state, 0)
            self.assertTrue((root / "scores" / "2024.csv").is_file())
            probability = model.predict_proba(np.zeros((1, len(loaded["columns"]))))
            self.assertEqual(probability.shape, (1, 2))
            self.assertGreaterEqual(float(probability[0][1]), 0.0)
            self.assertLessEqual(float(probability[0][1]), 1.0)
            with self.assertRaises(ValueError):
                fit_and_score(
                    rolled_dir=rolled,
                    leie_path=leie,
                    model_path=root / "other.joblib",
                    note_path=root / "other.txt",
                    share_path=root / "other.json",
                    score_dir=root / "other-scores",
                    train_years=(2013, 2024),
                    score_years=(),
                )


if __name__ == "__main__":
    unittest.main()

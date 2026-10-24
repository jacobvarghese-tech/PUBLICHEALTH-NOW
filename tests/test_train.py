"""The shipped trainer keeps every fraud row, fits once, and ranks the holdout."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.train import (
    BOOSTER,
    EXCLUDED_FROM_FEATURES,
    FEATURE_COLUMNS,
    CLEAN_PER_FRAUD,
    feature_frame,
    fit_expanded,
    fit_once,
    label_rows,
    new_classifier,
    real_mix_top_shares,
    top_slice_share,
    training_categories,
    undersample_90_10,
    train_and_write,
)


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    header = [
        "NPI",
        "Name",
        "City",
        "State",
        "ZIP",
        "Specialty",
        "Service count",
        "Beneficiary count",
        "Average charge",
        "Average payment",
        "Charge-to-payment ratio",
        "Top-code share",
        "Growth",
        "Year",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in header})


def _row(npi: str, year: str, specialty: str, service: str, growth: str = "") -> dict[str, str]:
    return {
        "NPI": npi,
        "Name": "Hidden Name",
        "City": "Hidden City",
        "State": "ZZ",
        "ZIP": "00000",
        "Specialty": specialty,
        "Service count": service,
        "Beneficiary count": "10",
        "Average charge": "100",
        "Average payment": "40",
        "Charge-to-payment ratio": "2.5",
        "Top-code share": "0.5",
        "Growth": growth,
        "Year": year,
    }


class TrainHelpersTest(unittest.TestCase):
    def test_label_requires_a_later_exclusion_year(self) -> None:
        rows = [
            {"NPI": "1111111111", "Year": "2021"},
            {"NPI": "1111111111", "Year": "2022"},
            {"NPI": "2222222222", "Year": "2020"},
            {"NPI": "3333333333", "Year": "2019"},
            {"NPI": "0", "Year": "2019"},
            {"NPI": "4444444444", "Year": "2019"},
        ]
        exclusion_years = {
            "1111111111": 2022,
            "2222222222": 2020,
            "3333333333": 2018,
        }
        labels = label_rows(rows, exclusion_years)
        self.assertEqual(labels, [1, 0, 0, 0, 0, 0])

    def test_undersample_keeps_every_fraud_row_and_targets_nine_clean(self) -> None:
        labels = [1, 1] + [0] * 40
        indexes = undersample_90_10(labels, clean_per_fraud=CLEAN_PER_FRAUD, seed=1)
        kept = [labels[index] for index in indexes]
        self.assertEqual(sum(kept), 2)
        self.assertEqual(kept.count(0), 18)
        self.assertEqual(kept.count(0), CLEAN_PER_FRAUD * kept.count(1))
        short = undersample_90_10([1] + [0] * 3, clean_per_fraud=9, seed=1)
        self.assertEqual(len(short), 4)

    def test_features_are_the_eight_named_columns(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "NPI": "1111111111",
                    "Name": "Hidden",
                    "City": "Town",
                    "State": "ZZ",
                    "ZIP": "00000",
                    "Year": "2019",
                    "Specialty": "Lab",
                    "Service count": "12",
                    "Beneficiary count": "",
                    "Average charge": "3.5",
                    "Average payment": "",
                    "Charge-to-payment ratio": "",
                    "Top-code share": "0.2",
                    "Growth": "",
                }
            ]
        )
        categories = training_categories(frame)
        features = feature_frame(frame, categories)
        self.assertEqual(tuple(features.columns), FEATURE_COLUMNS)
        for banned in EXCLUDED_FROM_FEATURES:
            self.assertNotIn(banned, features.columns)
        self.assertTrue(pd.isna(features.loc[0, "Beneficiary count"]))
        self.assertTrue(pd.isna(features.loc[0, "Growth"]))
        self.assertEqual(float(features.loc[0, "Specialty"]), 0.0)
        unknown = feature_frame(
            pd.DataFrame([{"Specialty": "Other", "Service count": "1"}]),
            categories,
        )
        self.assertTrue(pd.isna(unknown.loc[0, "Specialty"]))

    def test_top_slice_share_counts_ties_and_zero_fraud(self) -> None:
        scores = [0.1, 0.2, 0.9, 0.95, 0.99]
        labels = [0, 1, 0, 1, 0]
        captured, fraud_count, share = top_slice_share(scores, labels, 99)
        self.assertEqual(fraud_count, 2)
        self.assertEqual(captured / fraud_count, share)
        self.assertGreaterEqual(share, 0.0)
        self.assertLessEqual(share, 1.0)
        tied_scores = [0.5, 0.5, 0.5, 0.5]
        tied_labels = [1, 0, 1, 0]
        tied_captured, tied_fraud, tied_share = top_slice_share(tied_scores, tied_labels, 99)
        self.assertEqual((tied_captured, tied_fraud, tied_share), (2, 2, 1.0))
        zero_captured, zero_fraud, zero_share = top_slice_share([0.2, 0.8], [0, 0], 95)
        self.assertEqual((zero_captured, zero_fraud, zero_share), (0, 0, 0.0))

    def test_real_mix_scorer_sees_every_row(self) -> None:
        scores = [0.1, 0.4, 0.7, 0.2, 0.9]
        labels = [0, 1, 0, 0, 1]
        shares = real_mix_top_shares(scores, labels)
        self.assertEqual(shares["top_1"][1], 2)
        self.assertEqual(shares["top_5"][1], 2)
        self.assertEqual(shares["top_1"][0] / shares["top_1"][1], shares["top_1"][2])

    def test_one_shallow_fit_on_fixture_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rolled = root / "rolled"
            rolled.mkdir()
            leie = root / "UPDATED.csv"
            with leie.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["NPI", "EXCLTYPE", "EXCLDATE"])
                writer.writeheader()
                writer.writerows(
                    [
                        {"NPI": "1111111111", "EXCLTYPE": "1128a1", "EXCLDATE": "20220601"},
                        {"NPI": "2222222222", "EXCLTYPE": "1128a3", "EXCLDATE": "20250601"},
                        {"NPI": "3333333333", "EXCLTYPE": "1128b6", "EXCLDATE": "20240701"},
                        {"NPI": "4444444444", "EXCLTYPE": "1128a2", "EXCLDATE": "20260101"},
                        {"NPI": "0", "EXCLTYPE": "1128b7", "EXCLDATE": "20260101"},
                    ]
                )
            train_rows = [
                _row("1111111111", "2019", "Lab", "500", "1.2"),
                _row("2222222222", "2019", "Lab", "40", "0.1"),
            ]
            for index in range(30):
                train_rows.append(
                    _row(f"9{index:09d}", "2020", "Clinic", str(10 + index), "0.0")
                )
            _write_csv(rolled / "2019.csv", train_rows[:2])
            _write_csv(rolled / "2020.csv", train_rows[2:])
            holdout_rows = [
                _row("2222222222", "2024", "Lab", "900", "3.0"),
                _row("3333333333", "2024", "Lab", "20", "0.0"),
                _row("4444444444", "2024", "Clinic", "800", "2.0"),
                _row("5555555555", "2024", "Clinic", "15", ""),
            ]
            for index in range(20):
                holdout_rows.append(
                    _row(f"8{index:09d}", "2024", "Clinic", str(index + 1), "0.1")
                )
            _write_csv(rolled / "2024.csv", holdout_rows)

            calls = {"fit": 0}
            original = fit_once

            def _counting_fit(features, labels):
                calls["fit"] += 1
                return original(features, labels)

            import scripts.train as train_module

            train_module.fit_once = _counting_fit
            try:
                model_path, note_path = train_and_write(
                    leie_path=leie,
                    rolled_dir=rolled,
                    models_dir=root / "models",
                    train_years=(2019, 2020),
                    holdout_year=2024,
                )
            finally:
                train_module.fit_once = original

            self.assertEqual(calls["fit"], 1)
            self.assertTrue(model_path.is_file())
            note = note_path.read_text(encoding="utf-8")
            self.assertIn("Training sample fraud rows: 2", note)
            self.assertIn("Training sample clean rows: 18", note)
            self.assertIn("Real mix top 1%:", note)
            self.assertIn("top 1% of all 2024 scores:", note)
            self.assertIn("top 5% of all 2024 scores:", note)
            self.assertNotIn("accuracy", note.lower())
            self.assertNotIn("Accuracy", note)
            model_files = [
                path
                for path in (root / "models").iterdir()
                if path.suffix in {".json", ".ubj", ".bin", ".model"}
            ]
            self.assertEqual(len(model_files), 1)

            reloaded = train_module.new_classifier()
            reloaded.load_model(model_path)
            score = train_module.predict_scores(
                reloaded,
                feature_frame(
                    pd.DataFrame([_row("2222222222", "2024", "Lab", "900", "3.0")]),
                    ["Clinic", "Lab"],
                ),
            )
            self.assertEqual(len(score), 1)
            self.assertGreaterEqual(score[0], 0.0)
            self.assertLessEqual(score[0], 1.0)

    def test_expanded_fit_writes_only_the_expanded_file_and_sets_two_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            training = root / "physician.csv"
            rows = [
                _row("1111111111", "2013", "Lab", "500", "1.2"),
                _row("2222222222", "2014", "Clinic", "40", "0.1"),
            ]
            for index in range(20):
                rows.append(_row(f"9{index:09d}", "2015", "Clinic", str(10 + index), "0.0"))
            header = list(rows[0].keys()) + ["label"]
            with training.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=header)
                writer.writeheader()
                for index, row in enumerate(rows):
                    payload = dict(row)
                    payload["label"] = "1" if index < 2 else "0"
                    writer.writerow(payload)
            calls = {"fit": 0}
            original = fit_once

            def _counting_fit(features, labels):
                calls["fit"] += 1
                return original(features, labels)

            import scripts.train as train_module

            train_module.fit_once = _counting_fit
            shallow = root / "xgb_shallow.json"
            shallow.write_text("baseline", encoding="utf-8")
            before = shallow.read_bytes()
            try:
                written = fit_expanded(
                    training_path=training,
                    model_path=root / "xgb_expanded.json",
                    counts_path=root / "expand_counts.txt",
                )
            finally:
                train_module.fit_once = original
            self.assertEqual(calls["fit"], 1)
            self.assertEqual(written.name, "xgb_expanded.json")
            self.assertFalse((root / "xgb_shallow.json").read_bytes() != before)
            self.assertEqual(shallow.read_bytes(), before)
            self.assertEqual(set(BOOSTER), {"max_depth", "random_state"})
            self.assertEqual(BOOSTER["max_depth"], 4)
            self.assertEqual(BOOSTER["random_state"], 1)
            self.assertNotIn("n_estimators", BOOSTER)
            self.assertNotIn("scale_pos_weight", BOOSTER)
            self.assertNotIn("early_stopping_rounds", BOOSTER)
            model = new_classifier()
            params = model.get_params()
            self.assertEqual(params["max_depth"], 4)
            self.assertEqual(params["random_state"], 1)
            self.assertNotIn("early_stopping_rounds", {key for key, value in params.items() if key in BOOSTER})
            counts = (root / "expand_counts.txt").read_text(encoding="utf-8")
            self.assertIn("installed_n_estimators_default:", counts)
            self.assertIn("fit_fraud_rows: 2", counts)
            self.assertIn("fit_clean_rows: 18", counts)


if __name__ == "__main__":
    unittest.main()

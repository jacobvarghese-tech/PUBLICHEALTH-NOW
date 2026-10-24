"""Feature math on five in-memory lines. No download and no forest fit."""

from __future__ import annotations

import tempfile
import unittest
import unittest.mock
from pathlib import Path

import scripts.feature_islands as feature_islands
from scripts.feature_islands import (
    column_values,
    confirm_best,
    ensure_column,
    fit_one,
    formula_rejected,
    kept_rule,
    loop_already_stopped,
    read_resources,
    release_stop,
    write_note,
)


def _line(**values) -> dict:
    row = {
        "Rndrng_Prvdr_Type": "",
        "Rndrng_NPI": "",
        "nppes_provider_gender": "",
        "Place_Of_Srvc": "",
        "HCPCS_Cd": "",
        "HCPCS_Drug_Ind": "",
        "Rndrng_Prvdr_Mdcr_Prtcptg_Ind": "",
        "Tot_Srvcs": "",
        "Avg_Mdcr_Alowd_Amt": "",
        "Avg_Mdcr_Pymt_Amt": "",
        "Avg_Mdcr_Stdzd_Amt": "",
    }
    row.update(values)
    return row


LINES = [
    _line(
        Rndrng_Prvdr_Type="Internal Medicine",
        Rndrng_NPI="1111111111",
        nppes_provider_gender="M",
        Place_Of_Srvc="F",
        HCPCS_Cd="A",
        HCPCS_Drug_Ind="N",
        Rndrng_Prvdr_Mdcr_Prtcptg_Ind="Y",
        Tot_Srvcs="10",
        Avg_Mdcr_Alowd_Amt="20",
        Avg_Mdcr_Pymt_Amt="10",
        Avg_Mdcr_Stdzd_Amt="12",
    ),
    _line(
        Rndrng_Prvdr_Type="Internal Medicine",
        Rndrng_NPI="1111111111",
        nppes_provider_gender="M",
        Place_Of_Srvc="O",
        HCPCS_Cd="B",
        HCPCS_Drug_Ind="N",
        Rndrng_Prvdr_Mdcr_Prtcptg_Ind="Y",
        Tot_Srvcs="30",
        Avg_Mdcr_Alowd_Amt="40",
        Avg_Mdcr_Pymt_Amt="20",
        Avg_Mdcr_Stdzd_Amt="20",
    ),
    _line(
        Rndrng_Prvdr_Type="Internal Medicine",
        Rndrng_NPI="1111111111",
        nppes_provider_gender="M",
        Place_Of_Srvc="F",
        HCPCS_Cd="A",
        HCPCS_Drug_Ind="Y",
        Rndrng_Prvdr_Mdcr_Prtcptg_Ind="N",
        Tot_Srvcs="5",
        Avg_Mdcr_Alowd_Amt="8",
        Avg_Mdcr_Pymt_Amt="4",
        Avg_Mdcr_Stdzd_Amt="4",
    ),
    _line(
        Rndrng_Prvdr_Type="Internal Medicine",
        Rndrng_NPI="2222222222",
        nppes_provider_gender="F",
        Place_Of_Srvc="O",
        HCPCS_Cd="C",
        HCPCS_Drug_Ind="N",
        Rndrng_Prvdr_Mdcr_Prtcptg_Ind="Y",
        Tot_Srvcs="2",
        Avg_Mdcr_Alowd_Amt="5",
        Avg_Mdcr_Pymt_Amt="5",
        Avg_Mdcr_Stdzd_Amt="5",
    ),
    _line(Rndrng_NPI="", HCPCS_Cd="Z", Place_Of_Srvc="F", Tot_Srvcs="9"),
]


class FeatureColumnTest(unittest.TestCase):
    def test_five_lines(self) -> None:
        spec = {
            "name": "facility_line_share_and_distinct_hcpcs_count",
            "names": [
                "facility_line_share",
                "distinct_hcpcs_count",
                "drug_line_share",
                "nonparticipating_line_share",
                "facility_service_share",
                "services_per_distinct_hcpcs",
                "allowed_minus_payment",
                "facility_share_specialty_rank",
            ],
            "source_columns": ["Place_Of_Srvc", "HCPCS_Cd"],
            "formula": "both",
            "join_keys": ["provider_type", "npi", "nppes_provider_gender"],
            "grain": "provider-year",
        }
        values = column_values(LINES, spec)
        first = values[("Internal Medicine", "1111111111", "M")]
        second = values[("Internal Medicine", "2222222222", "F")]
        self.assertNotIn(("", "", ""), values)
        self.assertAlmostEqual(first["facility_line_share"], 2 / 3)
        self.assertEqual(first["distinct_hcpcs_count"], 2)
        self.assertAlmostEqual(first["drug_line_share"], 1 / 3)
        self.assertAlmostEqual(first["nonparticipating_line_share"], 1 / 3)
        self.assertAlmostEqual(first["facility_service_share"], 15 / 45)
        self.assertAlmostEqual(first["services_per_distinct_hcpcs"], 45 / 2)
        self.assertAlmostEqual(first["allowed_minus_payment"], 34 / 3)
        self.assertEqual(second["facility_line_share"], 0)
        self.assertEqual(second["distinct_hcpcs_count"], 1)
        self.assertEqual(first["facility_share_specialty_rank"], 2)
        self.assertEqual(second["facility_share_specialty_rank"], 1)

    def test_rejected_formula_and_missing_csv_url(self) -> None:
        self.assertTrue(formula_rejected({"formula": "rejected"}))
        self.assertTrue(formula_rejected({"formula": "Rejected: grain"}))
        self.assertFalse(formula_rejected({"formula": "count of Place_Of_Srvc == F"}))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "2017.resources.txt").write_text(
                "year=2017\nopened_bytes=10\n",
                encoding="utf-8",
            )
            with self.assertRaises(RuntimeError) as caught:
                read_resources(2017, root)
            self.assertIn("2017", str(caught.exception))
            self.assertIn("csv_url", str(caught.exception))
            self.assertNotIn("http", str(caught.exception))

    def test_recorded_stop_blocks_another_fit(self) -> None:
        self.assertIsNone(loop_already_stopped({"stops": []}))
        self.assertIsNone(loop_already_stopped({}))
        self.assertEqual(
            loop_already_stopped(
                {"stops": [{"stopped": True, "reason": "size mismatch year=2016"}]}
            ),
            "size mismatch year=2016",
        )
        self.assertIsNone(
            loop_already_stopped(
                {
                    "stops": [
                        {
                            "stopped": True,
                            "reason": "size mismatch year=2016",
                            "cleared": True,
                        }
                    ]
                }
            )
        )

    def test_keep_requires_a_higher_2023_count_and_a_small_zero_step_slice(self) -> None:
        self.assertFalse(kept_rule(93, 0.0246, 0.0, 93))
        self.assertFalse(kept_rule(94, 0.0246, 0.0, 93))
        self.assertFalse(kept_rule(94, 0.02, 0.1, 93))
        self.assertTrue(kept_rule(94, 0.02, 0.0, 93))

    def test_release_stop_clears_only_the_latest_stop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "feature_island_db.json"
            db.write_text(
                '{"stops":[{"stopped":true,"reason":"size mismatch year=2016","expected_bytes":1,"received_bytes":2}]}',
                encoding="utf-8",
            )
            with unittest.mock.patch.object(feature_islands, "DB_PATH", db):
                self.assertTrue(release_stop())
                self.assertFalse(release_stop())
            saved = __import__("json").loads(db.read_text(encoding="utf-8"))
            self.assertTrue(saved["stops"][-1]["cleared"])
            self.assertEqual(saved["stops"][-1]["expected_bytes"], 1)
            self.assertEqual(saved["stops"][-1]["received_bytes"], 2)

    def test_confirm_best_starts_at_the_saved_23(self) -> None:
        self.assertEqual(confirm_best({}), 23)
        self.assertEqual(confirm_best({"best_confirm_top1": 24}), 24)

    def test_note_appends_and_unkept_fit_does_not_build_2024(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            note = root / "feature_island_note.txt"
            db = root / "feature_island_db.json"
            columns = root / "feature_columns"
            columns.mkdir()
            leftover = columns / "2024_drug_line_share.csv"
            leftover.write_text("provider_type,npi,nppes_provider_gender,drug_line_share\n", encoding="utf-8")
            spec_path = root / "03.json"
            spec_path.write_text(
                '{"name":"drug_line_share","formula":"share","source_columns":["HCPCS_Drug_Ind"],'
                '"join_keys":["provider_type","npi","nppes_provider_gender"],"grain":"provider-year"}',
                encoding="utf-8",
            )
            downloads = []

            def refuse_download(*_args, **_kwargs):
                downloads.append("download")
                raise AssertionError("unkept fit downloaded a year")

            with (
                unittest.mock.patch.object(feature_islands, "NOTE_PATH", note),
                unittest.mock.patch.object(feature_islands, "DB_PATH", db),
                unittest.mock.patch.object(feature_islands, "COLUMN_DIR", columns),
                unittest.mock.patch.object(feature_islands, "CANDIDATE_DIR", root / "candidates"),
                unittest.mock.patch.object(feature_islands, "download", refuse_download),
            ):
                write_note(["spec=01.json", "kept=false"])
                write_note(["spec=02.json", "kept=false"])
                text = note.read_text(encoding="utf-8")
                self.assertIn("spec=01.json", text)
                self.assertIn("spec=02.json", text)
                self.assertLess(text.index("spec=01.json"), text.index("spec=02.json"))
                with self.assertRaises(RuntimeError):
                    ensure_column(2024, {"name": "drug_line_share"}, kept=False)
                self.assertFalse(leftover.exists())
                self.assertEqual(downloads, [])

                def fake_grade(*_args, **_kwargs):
                    return None, ["drug_line_share"], 0, 0

                def fake_rank(*_args, **_kwargs):
                    return [0.0, 0.0], [1, 0]

                def fake_confirm(*_args, **_kwargs):
                    return 23, 48, 48

                db.write_text('{"candidates":[],"baseline_select_top1":93}', encoding="utf-8")
                with (
                    unittest.mock.patch.object(feature_islands, "load_feature_spec", return_value={"name": "drug_line_share", "formula": "share"}),
                    unittest.mock.patch.object(feature_islands, "load_forest_spec", return_value={"fit_years": [2016], "n_estimators": 60, "max_depth": 20, "min_samples_leaf": 1, "class_weight": "balanced", "clean_per_fraud": 9}),
                    unittest.mock.patch.object(feature_islands, "column_names", return_value=["drug_line_share"]),
                    unittest.mock.patch.object(feature_islands, "joblib_load", return_value=object()),
                    unittest.mock.patch.object(feature_islands, "ensure_baseline", return_value=93),
                    unittest.mock.patch.object(feature_islands, "fit_secondary", fake_grade),
                    unittest.mock.patch.object(feature_islands, "rank_year", fake_rank),
                    unittest.mock.patch.object(feature_islands, "score_confirm", fake_confirm),
                    unittest.mock.patch.object(feature_islands, "share", return_value=(93, 93)),
                    unittest.mock.patch.object(feature_islands, "slice_ratio", return_value=0.0246),
                    unittest.mock.patch.object(feature_islands, "p95", return_value=0.0),
                ):
                    fit_one(spec_path)
                saved = __import__("json").loads(db.read_text(encoding="utf-8"))
                names = [row["spec"] for row in saved["candidates"]]
                self.assertIn("03.json", names)
                self.assertFalse(saved["candidates"][-1]["kept"])
                self.assertEqual(saved["candidates"][-1]["select_top1"], 93)
                self.assertEqual(saved["candidates"][-1]["confirm_top1"], 23)
                self.assertNotIn("best_confirm_top1", saved)

                def fake_confirm_rise(*_args, **_kwargs):
                    return 24, 48, 48

                with (
                    unittest.mock.patch.object(feature_islands, "load_feature_spec", return_value={"name": "drug_line_share", "formula": "share"}),
                    unittest.mock.patch.object(feature_islands, "load_forest_spec", return_value={"fit_years": [2016], "n_estimators": 60, "max_depth": 20, "min_samples_leaf": 1, "class_weight": "balanced", "clean_per_fraud": 9}),
                    unittest.mock.patch.object(feature_islands, "column_names", return_value=["drug_line_share"]),
                    unittest.mock.patch.object(feature_islands, "joblib_load", return_value=object()),
                    unittest.mock.patch.object(feature_islands, "ensure_baseline", return_value=93),
                    unittest.mock.patch.object(feature_islands, "fit_secondary", fake_grade),
                    unittest.mock.patch.object(feature_islands, "rank_year", fake_rank),
                    unittest.mock.patch.object(feature_islands, "score_confirm", fake_confirm_rise),
                    unittest.mock.patch.object(feature_islands, "share", return_value=(93, 93)),
                    unittest.mock.patch.object(feature_islands, "slice_ratio", return_value=0.0246),
                    unittest.mock.patch.object(feature_islands, "p95", return_value=0.0),
                    unittest.mock.patch.object(
                        feature_islands,
                        "save_candidate",
                        lambda *_args, **_kwargs: root / "candidates" / "feature_03.joblib",
                    ),
                ):
                    fit_one(spec_path)
                risen = __import__("json").loads(db.read_text(encoding="utf-8"))
                self.assertTrue(risen["candidates"][-1]["kept"])
                self.assertEqual(risen["best_confirm_top1"], 24)
                self.assertEqual(risen["best_spec"], "03.json")
                written = note.read_text(encoding="utf-8")
                self.assertIn("spec=03.json", written)
                self.assertIn("spec=01.json", written)
                self.assertLess(written.index("spec=01.json"), written.index("spec=03.json"))
                self.assertFalse((columns / "2024_drug_line_share.csv").exists())
                self.assertEqual(downloads, [])
        self.assertEqual(feature_islands.CANDIDATE_DIR.name, "candidates")
        self.assertEqual(feature_islands.CANDIDATE_DIR.parent.name, "models")


if __name__ == "__main__":
    unittest.main()

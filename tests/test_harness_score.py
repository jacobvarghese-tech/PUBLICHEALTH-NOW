"""The shipped GEPA harness gates the key, locks the eight fields, and splits 2019-2023."""

from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import dspy

from scripts.harness_score import (
    IDENTIFIER_FIELDS,
    INSTRUCTIONS,
    MISSING_KEY_MESSAGE,
    SIGNATURE_INPUTS,
    BillingResemblance,
    api_key_present,
    build_splits,
    main,
    metric,
    print_key_presence,
    require_api_key,
)


class HarnessScoreTest(unittest.TestCase):
    def test_empty_key_stops_without_inventing_a_key(self) -> None:
        with patch.dict(os.environ, {"XAI_API_KEY": ""}):
            captured = io.StringIO()
            with redirect_stdout(captured):
                with self.assertRaises(SystemExit) as raised:
                    require_api_key()
            text = captured.getvalue()
            self.assertIn("XAI_API_KEY", text)
            self.assertEqual(raised.exception.code, 1)
            self.assertEqual(text.strip(), MISSING_KEY_MESSAGE)
            self.assertNotIn("xai-", text.lower())
            captured_main = io.StringIO()
            with redirect_stdout(captured_main):
                with self.assertRaises(SystemExit):
                    main([])
            self.assertIn("set XAI_API_KEY", captured_main.getvalue())
            self.assertNotIn("xai-", captured_main.getvalue().lower())

    def test_presence_check_prints_only_true_or_false(self) -> None:
        with patch.dict(os.environ, {"XAI_API_KEY": ""}):
            self.assertFalse(api_key_present())
            captured = io.StringIO()
            with redirect_stdout(captured):
                print_key_presence()
                main(["--key-present"])
            lines = [line.strip() for line in captured.getvalue().splitlines() if line.strip()]
            self.assertEqual(lines, ["false", "false"])
        with patch.dict(os.environ, {"XAI_API_KEY": "not-a-live-key"}):
            captured = io.StringIO()
            with redirect_stdout(captured):
                print_key_presence()
            self.assertEqual(captured.getvalue().strip(), "true")

    def test_signature_inputs_are_the_eight_billing_fields_in_order(self) -> None:
        self.assertEqual(
            SIGNATURE_INPUTS,
            (
                "Service count",
                "Beneficiary count",
                "Average charge",
                "Average payment",
                "Charge-to-payment ratio",
                "Top-code share",
                "Specialty",
                "Growth",
            ),
        )
        descs = tuple(
            field.json_schema_extra["desc"]
            for field in BillingResemblance.input_fields.values()
        )
        self.assertEqual(descs, SIGNATURE_INPUTS)
        names = set(BillingResemblance.fields)
        for banned in IDENTIFIER_FIELDS:
            self.assertNotIn(banned, names)
            self.assertNotIn(banned.lower(), {name.lower() for name in names})

    def test_metric_accepts_gepa_kwargs_and_returns_score_feedback(self) -> None:
        gold = dspy.Example(label=1)
        pred = dspy.Prediction(resemblance_score="0.8", reason="unusual charge mix")
        out = metric(gold, pred, None, None, None)
        self.assertTrue(hasattr(out, "score") or isinstance(out, float))
        if not isinstance(out, float):
            self.assertGreaterEqual(float(out.score), 0.0)
            self.assertLessEqual(float(out.score), 1.0)
            self.assertTrue(str(out.feedback))
            self.assertNotIn("committed fraud", str(out.feedback).lower())

    def test_goal_prompt_names_the_use_case(self) -> None:
        text = INSTRUCTIONS.lower()
        self.assertIn("resemblance", text)
        self.assertIn("1128a1", text)
        self.assertIn("service count", text)
        self.assertIn("top-code share", text)
        self.assertIn("not a finding", text)
        self.assertEqual(BillingResemblance.instructions, INSTRUCTIONS)

    def test_build_splits_uses_the_full_labeled_pool(self) -> None:
        trainset, valset, counts = build_splits()
        self.assertEqual(counts["train_fraud"] + counts["val_fraud"], counts["pool_fraud"])
        self.assertEqual(counts["train_clean"] + counts["val_clean"], counts["pool_clean"])
        self.assertEqual(counts["pool_fraud"], 1270)
        self.assertEqual(counts["pool_clean"], 11430)
        self.assertEqual(counts["train_fraud"], 1016)
        self.assertEqual(counts["train_clean"], 9144)
        self.assertEqual(counts["val_fraud"], 254)
        self.assertEqual(counts["val_clean"], 2286)
        self.assertEqual(len(trainset), 1016 + 9144)
        self.assertEqual(len(valset), 254 + 2286)
        train_ids = {(ex.npi, ex.year) for ex in trainset}
        val_ids = {(ex.npi, ex.year) for ex in valset}
        self.assertFalse(train_ids.intersection(val_ids))
        years = {ex.year for ex in [*trainset, *valset]}
        self.assertNotIn("2024", years)
        npis = {ex.npi for ex in [*trainset, *valset]}
        self.assertNotIn("1124725817", npis)
        self.assertNotIn("1639879034", npis)
        self.assertEqual(sum(int(ex.label) for ex in trainset), 1016)
        self.assertEqual(sum(int(ex.label) for ex in valset), 254)


if __name__ == "__main__":
    unittest.main()

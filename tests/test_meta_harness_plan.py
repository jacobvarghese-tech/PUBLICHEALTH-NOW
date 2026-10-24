"""The shipped meta-harness plan names the writer, reviewer, and success line."""

from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = REPO_ROOT / "wiki" / "concepts" / "meta-harness-plan.md"
SUCCESS_LINE = "Success line: confirm_top1= as a count out of 48"


class MetaHarnessPlanTest(unittest.TestCase):
    def test_shipped_plan_ends_with_the_success_line(self) -> None:
        text = PLAN_PATH.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(lines[-1], SUCCESS_LINE)
        for heading in (
            "## 1. How to use the plan",
            "## 2. Tool install steps",
            "## 3. The harness contract",
            "## 4. The loop",
            "## 5. The one 2024 score",
            "## 6. Files the later session may create, and files it must not replace",
        ):
            self.assertIn(heading, text)
        self.assertIn("grok-4.5", text)
        self.assertIn("grok-4.7", text)
        self.assertIn("scripts/meta_harness.py", text)
        self.assertIn("harness/", text)
        self.assertIn("models/meta_harness_note.txt", text)
        self.assertIn("proposal_count=20", text)
        self.assertIn("not a `run_loop` argument", text)
        self.assertIn("beats_current_best", text)
        self.assertIn("pip install openai", text)
        self.assertIn("pip install shap", text)
        self.assertIn("pip install lime", text)
        self.assertIn("pip install ripgrep-rs", text)
        self.assertIn("pip install rank-bm25", text)
        self.assertIn("Do not invent `pip install eli5`", text)
        self.assertIn(
            "Keep only when the 2023 top 1 percent fraud count rises",
            text,
        )
        self.assertIn(
            "int(child top1_captured) > int(parent top1_captured)",
            text,
        )
        self.assertIn("at most 2 percent of the selection rows", text)
        self.assertIn("does not call `run_loop`", text)
        self.assertIn("score_source", text)
        self.assertIn("slice_stats", text)
        self.assertNotIn("applies that stricter rule to the returned stats", text)
        self.assertNotIn("calls the existing `run_loop`", text)
        self.assertNotIn("imports `run_loop` and passes", text)
        self.assertIn("resemblance to later fraud-type exclusions", text)
        denial = "the firm committed fraud"
        self.assertGreaterEqual(text.lower().count(denial), 1)
        self.assertGreaterEqual(
            text.lower().count("it is not a finding that the firm committed fraud"),
            1,
        )
        self.assertGreaterEqual(
            text.lower().count("no claim that the firm committed fraud"),
            1,
        )
        self.assertIn("Do not attribute 11/48 and 18/48 to `data/paper_scores/2024.csv`", text)
        self.assertIn("The agent does not edit that file", text)
        key = __import__("os").environ.get("XAI_API_KEY", "")
        if key:
            self.assertNotIn(key, text)


if __name__ == "__main__":
    unittest.main()

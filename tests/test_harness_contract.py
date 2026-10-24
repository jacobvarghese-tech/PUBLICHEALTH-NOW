"""Contract for the shipped harness/score_rows.py tie-break.

The parent computes paper_score and tree_score. A non-zero paper_score
comes back unchanged. A zero paper_score comes back as 0 or one page-forest
vote step above 0. The scored file does not import, open a file, or read
an identifier. This test drives the file on disk and the parent checker.
It does not score a year and it does not keep a proposal.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from scripts.meta_harness import compile_score_rows, reject_reason, run_harness

REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = REPO_ROOT / "harness" / "score_rows.py"
VOTE_STEP = 0.01


def _row(paper: float, tree: float, specialty: str = "Internal Medicine") -> dict:
    return {
        "Service count": 100.0,
        "Beneficiary count": 40.0,
        "Average charge": 80.0,
        "Average payment": 40.0,
        "Charge-to-payment ratio": 2.0,
        "Top-code share": 0.4,
        "Specialty": specialty,
        "Growth": 0.1,
        "tree_score": tree,
        "paper_score": paper,
    }


class HarnessContractTest(unittest.TestCase):
    def test_shipped_file_keeps_nonzero_paper_and_steps_zeros(self) -> None:
        source = HARNESS_PATH.read_text(encoding="utf-8")
        self.assertIsNone(reject_reason(source))
        fn = compile_score_rows(source)
        rows = [
            _row(0.19, 0.01),
            _row(0.01, 0.99),
            _row(0.0, 0.80, "Clinical Laboratory"),
            _row(0.0, 0.00, "Internal Medicine"),
            _row(0.04, 0.00),
        ]
        scored = run_harness(fn, rows)
        self.assertEqual(len(scored), len(rows))
        self.assertEqual(scored[0], 0.19)
        self.assertEqual(scored[1], 0.01)
        self.assertEqual(scored[4], 0.04)
        for index in (2, 3):
            self.assertIn(scored[index], (0.0, VOTE_STEP))
        for index, row in enumerate(rows):
            if row["paper_score"] > 0:
                self.assertEqual(scored[index], float(row["paper_score"]))

    def test_import_open_and_identifier_reads_are_rejected(self) -> None:
        illegal = {
            "import": "import math\ndef score_rows(rows):\n    return []\n",
            "from": "from os import path\ndef score_rows(rows):\n    return []\n",
            "open": "def score_rows(rows):\n    open('x')\n    return []\n",
            "import_call": "def score_rows(rows):\n    return [__import__('os')]\n",
            "npi": "def score_rows(rows):\n    return [row['NPI'] for row in rows]\n",
            "name": "def score_rows(rows):\n    return [row['Name'] for row in rows]\n",
            "city": "def score_rows(rows):\n    return [row['City'] for row in rows]\n",
            "state": "def score_rows(rows):\n    return [row['State'] for row in rows]\n",
            "zip": "def score_rows(rows):\n    return [row['ZIP'] for row in rows]\n",
            "year": "def score_rows(rows):\n    return [row['Year'] for row in rows]\n",
        }
        for name, source in illegal.items():
            self.assertIsNotNone(reject_reason(source), name)

    def test_shipped_source_has_no_import_open_or_identifier(self) -> None:
        source = HARNESS_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        banned = {"npi", "name", "city", "state", "zip", "year"}
        for node in ast.walk(tree):
            self.assertNotIsInstance(node, (ast.Import, ast.ImportFrom))
            if isinstance(node, ast.Name):
                self.assertNotIn(node.id.lower(), banned)
            if isinstance(node, ast.Attribute):
                self.assertNotIn(node.attr.lower(), banned)
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                self.assertNotIn(node.value.lower(), banned)


if __name__ == "__main__":
    unittest.main()

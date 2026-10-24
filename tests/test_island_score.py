"""Island scorer rejects illegal files and keeps the seed note shape."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.harness_score import CAVEAT
from scripts.island_score import (
    CURRENT_BEST,
    STOP_AT,
    compile_score_rows,
    island_path,
    reject_reason,
    should_keep,
    zero_mass_holds,
)


SEED = island_path(1).read_text(encoding="utf-8")


class IslandScoreTest(unittest.TestCase):
    def test_seed_matches_the_zero_tie_rule(self) -> None:
        self.assertIsNone(reject_reason(SEED))
        fn = compile_score_rows(SEED)
        rows = [
            {"paper_score": 0.02, "secondary_score": 0.1, "zero_cutoff": 0.5, "vote_step": 0.01},
            {"paper_score": 0.0, "secondary_score": 0.8, "zero_cutoff": 0.5, "vote_step": 0.01},
            {"paper_score": 0.0, "secondary_score": 0.2, "zero_cutoff": 0.5, "vote_step": 0.01},
            {"paper_score": 0.0, "secondary_score": 0.5, "zero_cutoff": float("inf"), "vote_step": 0.01},
        ]
        self.assertEqual(fn(rows), [0.02, 0.01, 0.0, 0.0])

    def test_import_open_and_identifier_reads_are_rejected(self) -> None:
        illegal = {
            "import": "import math\ndef score_rows(rows):\n    return []\n",
            "open": "def score_rows(rows):\n    open('x')\n    return []\n",
            "npi": "def score_rows(rows):\n    return [row['NPI'] for row in rows]\n",
            "year": "def score_rows(rows):\n    return [float(row['Year']) for row in rows]\n",
        }
        for name, source in illegal.items():
            self.assertIsNotNone(reject_reason(source), name)

    def test_keep_needs_a_higher_count_and_a_zero_top_five(self) -> None:
        short = {"top1_captured": 8, "top1_slice": 10, "rows": 1000}
        self.assertTrue(should_keep(short, 7, [0.0] * 96 + [0.01] * 4))
        self.assertFalse(should_keep(short, 8, [0.0] * 96 + [0.01] * 4))
        wide = {"top1_captured": 9, "top1_slice": 30, "rows": 1000}
        self.assertFalse(should_keep(wide, 7, [0.0] * 96 + [0.01] * 4))
        self.assertFalse(zero_mass_holds([0.01] * 100))
        self.assertFalse(should_keep(short, 7, [0.01] * 100))

    def test_note_names_the_count_and_the_caveat(self) -> None:
        note = Path("models/island_note.txt")
        if not note.exists():
            self.skipTest("seed gate has not written the note yet")
        text = note.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(CAVEAT))
        self.assertIn("confirm_top1=", text)
        self.assertIn(f"saved_best={CURRENT_BEST}/48", text)
        self.assertIn(f"stop_at={STOP_AT}/48", text)
        self.assertIn("not a finding that the firm committed fraud", text)


if __name__ == "__main__":
    unittest.main()

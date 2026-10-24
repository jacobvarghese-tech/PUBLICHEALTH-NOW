"""The meta harness rejects illegal files and keeps only a real selection gain."""

from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from scripts.meta_harness import (
    MISSING_KEY_MESSAGE,
    compile_score_rows,
    reject_reason,
    run_loop,
)


SEED = '''
def score_rows(rows):
    return [float(row["paper_score"]) for row in rows]
'''.strip() + "\n"


def _rows() -> tuple[list[dict], list[int]]:
    rows = []
    labels = [1] + [0] * 99
    for index, label in enumerate(labels):
        paper = 0.90 if index in (1, 2) else 0.20
        if index == 0:
            paper = 0.80
        rows.append(
            {
                "Service count": float(index),
                "Specialty": "Lab",
                "tree_score": 0.1,
                "paper_score": paper,
            }
        )
    return rows, labels


class MetaHarnessTest(unittest.TestCase):
    def test_seed_returns_paper_score(self) -> None:
        self.assertIsNone(reject_reason(SEED))
        fn = compile_score_rows(SEED)
        scored = fn([{"paper_score": 0.2, "tree_score": 0.9}])
        self.assertEqual(scored, [0.2])

    def test_import_open_and_identifier_reads_are_rejected(self) -> None:
        illegal = {
            "import": "import math\ndef score_rows(rows):\n    return []\n",
            "open": "def score_rows(rows):\n    open('x')\n    return []\n",
            "npi": "def score_rows(rows):\n    return [row['NPI'] for row in rows]\n",
            "year": "def score_rows(rows):\n    return [row['Year'] for row in rows]\n",
        }
        for name, source in illegal.items():
            self.assertIsNotNone(reject_reason(source), name)

    def test_missing_paper_score_uses_zero(self) -> None:
        import tempfile
        from pathlib import Path

        import pandas as pd

        from scripts import meta_harness

        with tempfile.TemporaryDirectory() as folder:
            table = pd.DataFrame({"npi": ["1"], "year": ["2023"], "score": [0.4]})
            table.to_csv(Path(folder) / "2023.csv", index=False)
            frame = pd.DataFrame({"NPI": ["1", "2"], "Year": ["2023", "2023"]})
            with patch.object(meta_harness, "PAPER_SCORE_DIR", Path(folder)):
                scores = meta_harness.paper_scores_for(frame)
        self.assertEqual(scores, [0.4, 0.0])

    def test_missing_key_exits_before_proposal_1(self) -> None:
        from scripts.meta_harness import main

        with patch.dict(os.environ, {"XAI_API_KEY": ""}):
            captured = io.StringIO()
            with redirect_stdout(captured):
                with self.assertRaises(SystemExit) as raised:
                    main([])
            text = captured.getvalue()
            self.assertEqual(raised.exception.code, 1)
            self.assertIn(MISSING_KEY_MESSAGE, text)
            self.assertNotIn("proposal=1", text)

    def test_stubbed_loop_keeps_a_gain_and_counts_a_reject(self) -> None:
        rows, labels = _rows()
        calls = {"n": 0}

        def proposer(parent: str, note: str) -> tuple[str, str, str]:
            calls["n"] += 1
            step = calls["n"]
            if step == 1:
                source = "import os\ndef score_rows(rows):\n    return [0.0]\n"
            elif step == 2:
                raise RuntimeError("proposer boom")
            elif step == 3:
                source = (
                    "def score_rows(rows):\n"
                    "    out = []\n"
                    "    for row in rows:\n"
                    "        score = float(row['paper_score'])\n"
                    "        if row.get('Service count') == 0.0:\n"
                    "            score = score + 0.2\n"
                    "        else:\n"
                    "            score = score - 0.2\n"
                    "        out.append(score)\n"
                    "    return out\n"
                )
            else:
                source = (
                    "def score_rows(rows):\n"
                    "    return [float(row['paper_score']) for row in rows]\n"
                )
            return source, f"stub-{step}", f"id-{step}"

        loop = run_loop(
            rows,
            labels,
            key="not-printed",
            seed_source=SEED,
            proposer=proposer,
            proposal_count=4,
        )
        self.assertEqual(len(loop["proposals"]), 4)
        self.assertIn("import", loop["proposals"][0]["error"])
        self.assertIn("boom", loop["proposals"][1]["error"])
        self.assertTrue(loop["proposals"][2]["kept"])
        self.assertFalse(loop["proposals"][3]["kept"])
        self.assertGreater(float(loop["best"]["fitness"]), float(loop["seed"]["fitness"]))
        self.assertIn("lost to its parent", loop["note"])


if __name__ == "__main__":
    unittest.main()

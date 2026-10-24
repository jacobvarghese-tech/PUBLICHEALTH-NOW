"""The shipped RankEvolve gates reject illegal functions and keep only a real gain."""

from __future__ import annotations

import io
import os
import random
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import numpy as np

from scripts.rank_evolve import (
    MAX_ADJUSTMENT,
    MISSING_KEY_MESSAGE,
    SEED_SOURCE,
    beats_xgboost,
    check_adjustment_cap,
    compile_score_row,
    list_fitness,
    reject_reason,
    run_loop,
    seed_score_row,
    should_keep,
    slice_stats,
)


def _frame(tree_scores: list[float], labels: list[int]) -> tuple[list[dict], list[float], list[int]]:
    rows = [{"Service count": float(index), "Specialty": "Lab"} for index, _score in enumerate(tree_scores)]
    return rows, list(tree_scores), list(labels)


class RankEvolveUnitTest(unittest.TestCase):
    def test_seed_returns_the_given_tree_score(self) -> None:
        self.assertEqual(seed_score_row({"Service count": 3}, 0.42), 0.42)
        self.assertIsNone(reject_reason(SEED_SOURCE))
        compiled = compile_score_row(SEED_SOURCE)
        self.assertEqual(compiled({"Growth": None}, -0.2), -0.2)
        self.assertIsNone(check_adjustment_cap(compiled, [{"Service count": 1}], [0.5]))

    def test_import_open_and_identifier_reads_are_rejected(self) -> None:
        illegal = {
            "import": "import math\ndef score_row(features, tree_score):\n    return tree_score\n",
            "open": "def score_row(features, tree_score):\n    open('x')\n    return tree_score\n",
            "npi": "def score_row(features, tree_score):\n    return features['NPI']\n",
            "name": "def score_row(features, tree_score):\n    return features.get('Name', tree_score)\n",
            "city": "def score_row(features, tree_score):\n    return features['City']\n",
            "state": "def score_row(features, tree_score):\n    return features['State']\n",
            "zip": "def score_row(features, tree_score):\n    return features['ZIP']\n",
            "year": "def score_row(features, tree_score):\n    return features['Year']\n",
        }
        for name, source in illegal.items():
            reason = reject_reason(source)
            self.assertIsNotNone(reason, name)

    def test_adjustment_above_cap_is_rejected(self) -> None:
        source = (
            "def score_row(features, tree_score):\n"
            f"    return tree_score + {MAX_ADJUSTMENT + 0.01}\n"
        )
        self.assertIsNone(reject_reason(source))
        fn = compile_score_row(source)
        reason = check_adjustment_cap(fn, [{"Service count": 1.0}], [0.2])
        self.assertIsNotNone(reason)
        self.assertIn("0.15", reason or "")

    def test_fitness_and_keep_rule(self) -> None:
        scores = [0.9, 0.1, 0.1, 0.1]
        labels = [1, 0, 0, 0]
        stats = slice_stats(scores, labels)
        fitness = list_fitness(scores, labels)
        self.assertEqual(fitness, stats["top1_captured"] - 0.25 * stats["extra_slice_rows"])
        wide = dict(stats)
        wide["top1_slice"] = 3
        wide["rows"] = 4
        self.assertFalse(should_keep(fitness + 1, fitness, wide))
        tight = dict(stats)
        tight["top1_slice"] = 1
        tight["rows"] = 100
        self.assertFalse(should_keep(fitness, fitness, tight))
        self.assertTrue(should_keep(fitness + 0.01, fitness, tight))
        tree = dict(tight)
        tree["top1_captured"] = int(tight["top1_captured"])
        winner = dict(tight)
        winner["top1_captured"] = int(tight["top1_captured"]) + 1
        self.assertTrue(beats_xgboost(winner, tree))
        self.assertFalse(beats_xgboost(winner, winner))
        fat = dict(winner)
        fat["top1_slice"] = 5
        fat["rows"] = 100
        self.assertFalse(beats_xgboost(fat, tree))

    def test_missing_key_exits_before_proposal_1(self) -> None:
        from scripts.rank_evolve import main

        with patch.dict(os.environ, {"XAI_API_KEY": ""}):
            captured = io.StringIO()
            with redirect_stdout(captured):
                with self.assertRaises(SystemExit) as raised:
                    main([])
            text = captured.getvalue()
            self.assertEqual(raised.exception.code, 1)
            self.assertIn(MISSING_KEY_MESSAGE, text)
            self.assertNotIn("proposal=1", text)
            self.assertNotIn("xai-", text.lower())

    def test_stubbed_loop_records_20_and_keeps_only_a_gain(self) -> None:
        trees = [0.80, 0.90, 0.90] + [0.20] * 97
        labels = [1, 0, 0] + [0] * 97
        rows, trees, labels = _frame(trees, labels)
        calls = {"n": 0, "notes": []}

        def proposer(parent: str, other_best: str, other_random: str, note: str) -> tuple[str, str, str]:
            calls["n"] += 1
            calls["notes"].append(note)
            step = calls["n"]
            source = "def score_row(features, tree_score):\n    return tree_score\n"
            if step == 1:
                source = "import os\ndef score_row(features, tree_score):\n    return tree_score\n"
            elif step == 2:
                raise RuntimeError("proposer boom")
            elif step == 3:
                source = "def score_row(features, tree_score):\n    return tree_score - 0.05\n"
            elif step == 4:
                source = (
                    "def score_row(features, tree_score):\n"
                    "    bump = 0.15 if features.get('Service count') == 0.0 else -0.15\n"
                    "    return tree_score + bump\n"
                )
            return source, f"stub-model-{step}", f"stub-id-{step}"

        loop = run_loop(
            rows,
            trees,
            labels,
            rows,
            trees,
            labels,
            key="not-printed",
            proposer=proposer,
            proposal_count=20,
            rng=random.Random(1),
        )
        self.assertEqual(len(loop["proposals"]), 20)
        self.assertEqual(calls["n"], 20)
        self.assertEqual(loop["proposals"][0]["response_id"], "stub-id-1")
        self.assertEqual(loop["proposals"][3]["response_model"], "stub-model-4")
        self.assertIn("import", loop["proposals"][0]["error"])
        self.assertIn("boom", loop["proposals"][1]["error"])
        self.assertIn("Proposal 2", calls["notes"][2])
        self.assertTrue(any(item.get("kept") for item in loop["proposals"]))
        self.assertIn("def score_row", loop["best"]["source"])
        self.assertGreater(float(loop["best"]["fitness"]), float(loop["seed"]["fitness"]))
        losing = [item for item in loop["proposals"] if item["proposal"] == 3][0]
        self.assertFalse(losing["kept"])
        from scripts.rank_evolve import draw_indexes

        fraud = np.arange(2)
        clean = np.arange(2, 12)
        chosen = draw_indexes(fraud, clean, None, 5, 1)
        self.assertEqual(len(chosen), 2 + 10)
        self.assertTrue(set(fraud).issubset(set(int(value) for value in chosen)))


if __name__ == "__main__":
    unittest.main()

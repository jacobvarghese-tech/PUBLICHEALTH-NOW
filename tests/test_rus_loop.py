"""The undersample loop copies the parent and redraws clean rows.

No year CSV is loaded and no forest is fit.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.paper_forest_rus import undersample
from scripts.rus_loop import CLEAN_PER_FRAUD, STOP_ABOVE, copy_parent, draw_indexes


class RusLoopTest(unittest.TestCase):
    def test_stop_is_above_26_of_48(self) -> None:
        self.assertEqual(STOP_ABOVE, 26)
        self.assertEqual(CLEAN_PER_FRAUD, 9)

    def test_repeat_draw_changes_the_clean_rows(self) -> None:
        frame = pd.DataFrame({"fraud": [1, 1] + [0] * 40, "value": list(range(42))})
        first, fraud_count, clean_count = undersample(frame, clean_per_fraud=9, random_state=1)
        second, _, _ = undersample(frame, clean_per_fraud=9, random_state=2)
        self.assertEqual(fraud_count, 2)
        self.assertEqual(clean_count, 18)
        self.assertEqual(set(first.loc[first["fraud"] == 1, "value"]), {0, 1})
        self.assertEqual(set(second.loc[second["fraud"] == 1, "value"]), {0, 1})
        self.assertNotEqual(
            set(first.loc[first["fraud"] == 0, "value"]),
            set(second.loc[second["fraud"] == 0, "value"]),
        )

    def test_default_seed_matches_the_first_forest(self) -> None:
        frame = pd.DataFrame({"fraud": [1, 0, 0, 0, 0], "value": [9, 1, 2, 3, 4]})
        sample, _, _ = undersample(frame, clean_per_fraud=1)
        expected = frame.loc[frame["fraud"] == 0].sample(n=1, replace=False, random_state=0)
        self.assertEqual(
            set(sample.loc[sample["fraud"] == 0, "value"]),
            set(expected["value"]),
        )

    def test_draw_keeps_every_fraud_row_in_each_year(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parts = Path(tmp)
            for year, fraud_at in ((2016, 0), (2017, 2)):
                rows = ["npi,fraud"]
                for index in range(6):
                    rows.append(f"{1000000000 + index},{1 if index == fraud_at else 0}")
                (parts / f"{year}_labels.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
            with patch("scripts.rus_loop.CLEAN_PER_FRAUD", 2):
                chosen, fraud_count, keep_clean = draw_indexes(parts, (2016, 2017), 1)
        self.assertEqual(fraud_count, 2)
        self.assertEqual(keep_clean, 4)
        self.assertIn(0, chosen[2016])
        self.assertIn(2, chosen[2017])
        self.assertEqual(sum(len(rows) for rows in chosen.values()), 6)

    def test_copy_parent_leaves_the_source_in_place(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "22.joblib"
            source.write_bytes(b"parent-bytes")
            dest = root / "copy" / "parent.joblib"
            copied = copy_parent(source, dest)
            self.assertEqual(copied.read_bytes(), b"parent-bytes")
            self.assertTrue(source.is_file())
            self.assertEqual(source.read_bytes(), b"parent-bytes")

    def test_loop_stops_when_the_count_clears_26(self) -> None:
        from scripts import rus_loop

        calls = []

        def _round(payload, round_seed, db):
            calls.append(round_seed)
            top1 = 22 if round_seed == 1 else 27
            db.setdefault("rounds", []).append({"round": round_seed, "confirm_top1": top1})
            db["best_confirm_top1"] = top1
            return top1

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parent = root / "parent.joblib"
            parent.write_bytes(b"copied")
            with (
                patch.object(rus_loop, "copy_parent", return_value=parent),
                patch.object(rus_loop, "load_parent", return_value=object()),
                patch.object(rus_loop, "load_db", return_value={"rounds": [], "best_confirm_top1": 22}),
                patch.object(rus_loop, "save_db"),
                patch.object(rus_loop, "run_round", side_effect=_round),
                patch.object(rus_loop, "PARENT_COPY", parent),
            ):
                best = rus_loop.run_loop(5)
        self.assertEqual(calls, [1, 2])
        self.assertEqual(best, 27)
        self.assertGreater(best, STOP_ABOVE)


if __name__ == "__main__":
    unittest.main()

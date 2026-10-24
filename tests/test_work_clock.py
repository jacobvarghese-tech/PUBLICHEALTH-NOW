"""The working stop is 6:00 a.m. local, including when the file is missing."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from scripts.work_clock import FALLBACK, load_stop, past_stop


class WorkClockTest(unittest.TestCase):
    def test_file_on_disk_is_six_am(self) -> None:
        stop = load_stop()
        self.assertEqual(stop, datetime(2026, 10, 24, 6, 0, 0))

    def test_missing_file_falls_back_to_six_am(self) -> None:
        missing = Path(tempfile.gettempdir()) / "work_clock_missing.json"
        if missing.exists():
            missing.unlink()
        self.assertEqual(load_stop(missing), FALLBACK)
        self.assertEqual(FALLBACK, datetime(2026, 10, 24, 6, 0, 0))

    def test_unreadable_file_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            bad = Path(folder) / "work_clock.json"
            bad.write_text("{", encoding="utf-8")
            self.assertEqual(load_stop(bad), FALLBACK)
            bad.write_text(json.dumps({"tz": "local"}), encoding="utf-8")
            self.assertEqual(load_stop(bad), FALLBACK)

    def test_past_stop_uses_the_same_clock(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            clock = Path(folder) / "work_clock.json"
            clock.write_text(
                json.dumps({"stop_at": "2026-10-24T06:00:00"}),
                encoding="utf-8",
            )
            self.assertFalse(past_stop(datetime(2026, 10, 24, 5, 59, 0), clock))
            self.assertTrue(past_stop(datetime(2026, 10, 24, 6, 0, 0), clock))


if __name__ == "__main__":
    unittest.main()

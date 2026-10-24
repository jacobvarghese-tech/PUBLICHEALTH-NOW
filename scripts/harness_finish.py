"""Score the saved harness. Does not start a new search."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.harness_rank import (  # noqa: E402
    CAVEAT,
    CONFIRM_CLEAN_PER,
    CONFIRM_YEAR,
    HARNESS_PATH,
    NOTE_PATH,
    SEED,
    load_year_frame,
    model_scores,
    rank_shares,
    require_key,
    sample_frame,
    score_frame,
    short_list_ok,
    write_note,
)


def main() -> int:
    key = require_key()
    payload = json.loads(HARNESS_PATH.read_text(encoding="utf-8"))
    instruction = payload["instruction"]
    confirm = sample_frame(
        load_year_frame((CONFIRM_YEAR,)),
        fraud_cap=None,
        clean_per=CONFIRM_CLEAN_PER,
        seed=SEED,
    )
    scores, _ = score_frame(instruction, confirm, key)
    labels = [int(value) for value in confirm["label"].tolist()]
    stats = rank_shares(scores, labels)
    baselines = model_scores(confirm)
    xgb = rank_shares(baselines["xgboost"], labels)
    beat = stats["top1_captured"] > xgb["top1_captured"] and short_list_ok(stats)
    text = (
        "Saved harness scored after the search. No new search was started.\n"
        f"student={payload['student_model']}\n"
        f"reflection={payload['reflection_model']}\n"
        f"{CAVEAT}\n"
        "Confirmation is a 2024 subsample: every fraud row and "
        f"{CONFIRM_CLEAN_PER} clean rows per fraud row, seed {SEED}. "
        "It is not the full 1.21 million-row year.\n"
        f"confirm_top1={stats['top1_captured']}/{stats['top1_fraud']}\n"
        f"confirm_top5={stats['top5_captured']}/{stats['top5_fraud']}\n"
        f"confirm_top1_slice={stats['top1_slice']}/{stats['rows']}\n"
        f"confirm_short_list={short_list_ok(stats)}\n"
        f"same_rows_xgboost_top1={xgb['top1_captured']}/{xgb['top1_fraud']}\n"
        f"same_rows_xgboost_top5={xgb['top5_captured']}/{xgb['top5_fraud']}\n"
        f"same_rows_xgboost_top1_slice={xgb['top1_slice']}/{xgb['rows']}\n"
        f"beats_xgboost_on_same_rows={beat}\n"
        "The paper forest was not scored on these rows. Its saved model uses "
        "paper summary columns that are not in this eight-field frame.\n"
        "Saved full-year figures, not this subsample: XGBoost 11/48 and 18/48. "
        "Paper forest 19/48 and 48/48.\n"
        "A high score means resemblance to later fraud-type exclusions. "
        "It is not a finding that the firm committed fraud.\n"
    )
    write_note(text)
    print(f"wrote {NOTE_PATH.name}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

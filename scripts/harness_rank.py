"""One-shot optimized scoring harness for the control trials.

Search years are 2019-2022. Selection year is 2023. Confirmation year is
2024 and is scored once after the search stops.

A high score means the billing profile resembles providers later excluded
for a fraud-type reason. This is not a finding that the firm committed fraud.
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path

import joblib

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.harness_score import (  # noqa: E402
    CAVEAT,
    FIELD_MAP,
    INSTRUCTIONS,
    SIGNATURE_INPUTS,
    field_text,
    is_rate_limit,
    parse_score,
)
from scripts.join_labels import DEMO_NPIS, earliest_exclusion_years  # noqa: E402
from scripts.train import (  # noqa: E402
    FEATURE_COLUMNS,
    LEIE_PATH,
    ROLLED_DIR,
    SEED,
    feature_frame,
    label_from_columns,
    top_slice_share,
    training_categories,
)

SEARCH_YEARS = (2019, 2020, 2021, 2022)
SELECTION_YEAR = 2023
CONFIRM_YEAR = 2024
GEPA_SEARCH_FRAUD = 12
GEPA_SELECT_FRAUD = 8
GEPA_CLEAN_PER = 1
RANK_SELECT_FRAUD = 30
RANK_CLEAN_PER = 9
CONFIRM_CLEAN_PER = 5
MAX_METRIC_CALLS = 80
MAX_PROPOSALS = 12
STUDENT_MODEL = "grok-4.5"
REFLECTION_MODEL = "grok-4.6"
API_BASE = "https://api.x.ai/v1"
NOTE_PATH = REPO_ROOT / "models" / "harness_rank_note.txt"
HARNESS_PATH = REPO_ROOT / "models" / "harness_rank.json"
READ_COLUMNS = ("NPI", "Year", *FEATURE_COLUMNS)

OBJECTIVE = (
    "Rewrite the scoring instruction so more later-excluded provider-years "
    "land in the top 1 percent of selection-year scores. A high score means "
    "resemblance to later fraud-type exclusions. It is not a finding that "
    "the firm committed fraud."
)
BACKGROUND = (
    "Inputs are eight billing fields only. Do not add NPI, name, city, state, "
    "ZIP, or year. Do not tell the scorer to say anyone committed fraud. "
    "The number being maximized is the count of selection-year fraud rows "
    "in the top 1 percent. A top 1 percent slice that holds most of the rows "
    "is a failed list."
)


def require_key() -> str:
    key = os.getenv("XAI_API_KEY")
    if key is None or key.strip() == "":
        print("set XAI_API_KEY")
        raise SystemExit(1)
    return key


def load_year_frame(years: tuple[int, ...]) -> pd.DataFrame:
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    frames: list[pd.DataFrame] = []
    for year in years:
        path = ROLLED_DIR / f"{year}.csv"
        frame = pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8",
            usecols=list(READ_COLUMNS),
        )
        frame["NPI"] = frame["NPI"].astype(str).str.strip()
        frame["Year"] = frame["Year"].astype(str).str.strip()
        frame = frame[~frame["NPI"].isin(DEMO_NPIS)]
        labels = label_from_columns(
            frame["NPI"].tolist(),
            frame["Year"].tolist(),
            exclusion_years,
        )
        frame = frame.copy()
        frame["label"] = labels
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def sample_frame(
    frame: pd.DataFrame,
    fraud_cap: int | None,
    clean_per: int,
    seed: int,
) -> pd.DataFrame:
    """Cap fraud first, then keep clean_per clean rows for each kept fraud row."""
    rng = np.random.default_rng(seed)
    fraud = frame.index[frame["label"] == 1].to_numpy()
    clean = frame.index[frame["label"] == 0].to_numpy()
    if fraud_cap is not None and len(fraud) > fraud_cap:
        fraud = rng.choice(fraud, size=fraud_cap, replace=False)
    clean_target = clean_per * max(len(fraud), 1)
    if len(clean) > clean_target:
        clean = rng.choice(clean, size=clean_target, replace=False)
    chosen = np.sort(np.concatenate([fraud, clean])) if len(fraud) or len(clean) else fraud
    return frame.iloc[chosen].reset_index(drop=True)


def row_payload(row: pd.Series) -> dict[str, str | int]:
    payload: dict[str, str | int] = {
        FIELD_MAP[name]: field_text(row.get(name, "")) for name in SIGNATURE_INPUTS
    }
    payload["label"] = int(row["label"])
    payload["npi"] = field_text(row.get("NPI", ""))
    payload["year"] = field_text(row.get("Year", ""))
    return payload


def chat_score(instruction: str, example: dict, key: str) -> tuple[float, str]:
    print("score_call", flush=True)
    from openai import OpenAI

    client = OpenAI(api_key=key, base_url=API_BASE)
    user = "\n".join(
        f"{name}: {example[FIELD_MAP[name]]}" for name in SIGNATURE_INPUTS
    )
    delay = 5.0
    last: BaseException | None = None
    for _ in range(8):
        try:
            response = client.chat.completions.create(
                model=STUDENT_MODEL,
                temperature=0,
                extra_body={"reasoning_effort": "high"},
                messages=[
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": user},
                ],
            )
            text = response.choices[0].message.content or ""
            score = parse_score(text)
            return score, text[:240]
        except Exception as exc:  # noqa: BLE001 — retry rate limits only
            last = exc
            if not is_rate_limit(exc):
                raise
            time.sleep(delay)
            delay = min(delay * 2.0, 60.0)
    if last is not None:
        raise last
    raise RuntimeError("score call failed")


def rank_shares(scores: list[float], labels: list[int]) -> dict[str, int]:
    top1 = top_slice_share(scores, labels, 99)
    top5 = top_slice_share(scores, labels, 95)
    cutoff = float(np.percentile(np.asarray(scores, dtype=float), 99)) if scores else 0.0
    in_slice = sum(1 for score in scores if score >= cutoff)
    return {
        "top1_captured": top1[0],
        "top1_fraud": top1[1],
        "top5_captured": top5[0],
        "top5_fraud": top5[1],
        "top1_slice": in_slice,
        "rows": len(scores),
    }


def model_scores(frame: pd.DataFrame) -> dict[str, list[float]]:
    """Score the same rows with the saved trees. Does not fit."""
    from xgboost import XGBClassifier

    categories = training_categories(
        pd.read_csv(
            REPO_ROOT / "data" / "training" / "physician_2013_2023.csv",
            dtype=str,
            keep_default_na=False,
            encoding="utf-8",
            usecols=["Specialty"],
        )
    )
    features = feature_frame(frame, categories)
    booster = XGBClassifier()
    booster.load_model(REPO_ROOT / "models" / "xgb_shallow.json")
    xgb_scores = [float(row[1]) for row in booster.predict_proba(features)]
    return {"xgboost": xgb_scores}


def share_line(name: str, scores: list[float], labels: list[int]) -> str:
    stats = rank_shares(scores, labels)
    return (
        f"{name}_top1={stats['top1_captured']}/{stats['top1_fraud']}\n"
        f"{name}_top5={stats['top5_captured']}/{stats['top5_fraud']}\n"
        f"{name}_top1_slice={stats['top1_slice']}/{stats['rows']}\n"
        f"{name}_short_list={short_list_ok(stats)}\n"
    )


def short_list_ok(stats: dict[str, int]) -> bool:
    if stats["rows"] == 0:
        return False
    return stats["top1_slice"] <= max(1, int(stats["rows"] * 0.02))


def score_frame(instruction: str, frame: pd.DataFrame, key: str) -> tuple[list[float], list[str]]:
    scores: list[float] = []
    reasons: list[str] = []
    for _, row in frame.iterrows():
        score, reason = chat_score(instruction, row_payload(row), key)
        scores.append(score)
        reasons.append(reason)
    return scores, reasons


def write_note(text: str) -> None:
    NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTE_PATH.write_text(text, encoding="utf-8")
    print(text, flush=True)


def save_harness(text: str) -> None:
    HARNESS_PATH.write_text(
        json.dumps(
            {
                "student_model": STUDENT_MODEL,
                "reflection_model": REFLECTION_MODEL,
                "api_base": API_BASE,
                "instruction": text,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    raw = HARNESS_PATH.read_text(encoding="utf-8")
    key = os.getenv("XAI_API_KEY") or ""
    if key and key in raw:
        HARNESS_PATH.write_text(raw.replace(key, ""), encoding="utf-8")


def main() -> int:
    key = require_key()
    search_all = load_year_frame(SEARCH_YEARS)
    selection_all = load_year_frame((SELECTION_YEAR,))
    search = sample_frame(search_all, GEPA_SEARCH_FRAUD, GEPA_CLEAN_PER, SEED)
    selection = sample_frame(selection_all, GEPA_SELECT_FRAUD, GEPA_CLEAN_PER, SEED)
    if (search["Year"] == str(CONFIRM_YEAR)).any() or (
        selection["Year"] == str(CONFIRM_YEAR)
    ).any():
        raise SystemExit("2024 entered the search")
    if set(search["NPI"]).intersection(DEMO_NPIS) or set(selection["NPI"]).intersection(DEMO_NPIS):
        raise SystemExit("demo NPI entered the search")

    header = (
        "One-shot harness rank.\n"
        f"search_years={','.join(str(year) for year in SEARCH_YEARS)}\n"
        f"search_rows={len(search)} search_fraud={int((search['label'] == 1).sum())}\n"
        f"selection_year={SELECTION_YEAR} selection_rows={len(selection)} "
        f"selection_fraud={int((selection['label'] == 1).sum())}\n"
        f"student={STUDENT_MODEL}\nreflection={REFLECTION_MODEL}\n"
        f"max_metric_calls={MAX_METRIC_CALLS}\n"
        "2024 is confirmation and is not in the search.\n"
    )
    write_note(header)

    import gepa.optimize_anything as oa
    from gepa.optimize_anything import EngineConfig, GEPAConfig, ReflectionConfig

    search_rows = [row_payload(row) for _, row in search.iterrows()]
    selection_rows = [row_payload(row) for _, row in selection.iterrows()]

    def evaluator(candidate: str, example: dict) -> tuple[float, dict]:
        score, reason = chat_score(str(candidate), example, key)
        label = int(example["label"])
        feedback = (
            f"Gold label {label}. Predicted resemblance {score:.3f}. "
            f"Reason excerpt: {reason}"
        )
        return score, {"feedback": feedback, "label": label}

    reflection = ReflectionConfig(
        reflection_lm=f"openai/{REFLECTION_MODEL}",
        reflection_lm_kwargs={
            "api_base": API_BASE,
            "api_key": key,
            "temperature": 0.7,
            "reasoning_effort": "high",
        },
        reflection_minibatch_size=3,
    )
    config = GEPAConfig(
        engine=EngineConfig(
            max_metric_calls=MAX_METRIC_CALLS,
            max_candidate_proposals=MAX_PROPOSALS,
            seed=SEED,
            parallel=False,
            raise_on_exception=True,
        ),
        reflection=reflection,
    )
    result = oa.optimize_anything(
        seed_candidate=INSTRUCTIONS,
        evaluator=evaluator,
        dataset=search_rows,
        valset=selection_rows,
        objective=OBJECTIVE,
        background=BACKGROUND,
        config=config,
    )
    best = result.best_candidate
    instruction = best if isinstance(best, str) else json.dumps(best)
    save_harness(instruction)

    rank_selection = sample_frame(
        selection_all, RANK_SELECT_FRAUD, RANK_CLEAN_PER, SEED
    )
    select_scores, _ = score_frame(instruction, rank_selection, key)
    select_stats = rank_shares(
        select_scores, [int(value) for value in rank_selection["label"].tolist()]
    )
    select_line = (
        f"selection_top1={select_stats['top1_captured']}/{select_stats['top1_fraud']}\n"
        f"selection_top5={select_stats['top5_captured']}/{select_stats['top5_fraud']}\n"
        f"selection_top1_slice={select_stats['top1_slice']}/{select_stats['rows']}\n"
        f"selection_short_list={short_list_ok(select_stats)}\n"
    )

    confirm = sample_frame(
        load_year_frame((CONFIRM_YEAR,)),
        fraud_cap=None,
        clean_per=CONFIRM_CLEAN_PER,
        seed=SEED,
    )
    confirm_scores, _ = score_frame(instruction, confirm, key)
    confirm_stats = rank_shares(
        confirm_scores, [int(value) for value in confirm["label"].tolist()]
    )
    labels = [int(value) for value in confirm["label"].tolist()]
    baselines = model_scores(confirm)
    xgb = rank_shares(baselines["xgboost"], labels)
    beat = (
        confirm_stats["top1_captured"] > xgb["top1_captured"]
        and short_list_ok(confirm_stats)
    )
    confirm_line = (
        f"{CAVEAT}\n"
        "Confirmation is a 2024 subsample: every fraud row and "
        f"{CONFIRM_CLEAN_PER} clean rows per fraud row, seed {SEED}. "
        "It is not the full 1.21 million-row year.\n"
        f"confirm_top1={confirm_stats['top1_captured']}/{confirm_stats['top1_fraud']}\n"
        f"confirm_top5={confirm_stats['top5_captured']}/{confirm_stats['top5_fraud']}\n"
        f"confirm_top1_slice={confirm_stats['top1_slice']}/{confirm_stats['rows']}\n"
        f"confirm_short_list={short_list_ok(confirm_stats)}\n"
        + share_line("same_rows_xgboost", baselines["xgboost"], labels)
        + f"beats_xgboost_on_same_rows={beat}\n"
        + "The paper forest was not scored on these rows. Its saved model "
        + "uses paper summary columns that are not in this eight-field frame.\n"
        "Saved full-year figures, not this subsample: XGBoost 11/48 and 18/48. "
        "Paper forest 19/48 and 48/48.\n"
        "A high score means resemblance to later fraud-type exclusions. "
        "It is not a finding that the firm committed fraud.\n"
    )
    write_note(header + select_line + confirm_line + f"saved={HARNESS_PATH.name}\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        raise

"""Score one billing row with an xAI/DSPy GEPA program.

A high score means the billing profile resembles providers later excluded
for a fraud-type reason. This is not a finding that the firm committed fraud.
"""

from __future__ import annotations

import faulthandler
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path

faulthandler.enable()

import dspy
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.join_labels import DEMO_NPIS, earliest_exclusion_years
from scripts.train import (
    CLEAN_PER_FRAUD,
    FEATURE_COLUMNS,
    HOLDOUT_YEAR,
    LEIE_PATH,
    ROLLED_DIR,
    SEED,
    TRAIN_YEARS,
    label_from_columns,
    undersample_90_10,
)

MODELS_DIR = REPO_ROOT / "models"
MODEL_PATH = MODELS_DIR / "harness_gepa.json"
NOTE_PATH = MODELS_DIR / "harness_gepa_note.txt"
API_BASE = "https://api.x.ai/v1"
STUDENT_MODEL = "openai/grok-4.20-0309-non-reasoning"
REFLECTION_MODEL = "openai/grok-4.3"
MISSING_KEY_MESSAGE = "set XAI_API_KEY"
CAVEAT = (
    "2024 has 48 fraud rows, below the published external-validation floor of "
    "100 events, so shares are not a precise estimate."
)

SIGNATURE_INPUTS = (
    "Service count",
    "Beneficiary count",
    "Average charge",
    "Average payment",
    "Charge-to-payment ratio",
    "Top-code share",
    "Specialty",
    "Growth",
)
IDENTIFIER_FIELDS = ("NPI", "Name", "City", "State", "ZIP", "Year")
FIELD_MAP = {
    "Service count": "service_count",
    "Beneficiary count": "beneficiary_count",
    "Average charge": "average_charge",
    "Average payment": "average_payment",
    "Charge-to-payment ratio": "charge_to_payment_ratio",
    "Top-code share": "top_code_share",
    "Specialty": "specialty",
    "Growth": "growth",
}
INPUT_KEYS = tuple(FIELD_MAP[name] for name in SIGNATURE_INPUTS)
READ_COLUMNS = ("NPI", "Year", *FEATURE_COLUMNS)
POOL_FRAUD = 1270
POOL_CLEAN = 11430
VAL_FRACTION = 0.2

INSTRUCTIONS = """You score one Medicare Part B provider-year from eight billing fields.

Goal: output how much this billing profile resembles providers who were later excluded from federal health programs for a fraud-type LEIE reason (1128a1, 1128a3, 1128b6, or 1128b7), with the exclusion year after this billing year. Same-year and earlier exclusions are not the gold pattern.

Inputs, in this order: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth.
Specialty is a string such as Clinical Laboratory.
Growth is this year's service count divided by the prior year's service count, minus 1. Growth is missing when there is no prior row or the prior service count is 0.
A blank or missing number stays missing. Do not invent a fill-in.
NPI, name, city, state, ZIP, and year identify the row. They are not inputs. Do not treat geography or identity as evidence.

Outputs:
- resemblance_score: a number from 0 to 1. 0 is an ordinary billing mix. 1 is a mix that closely matches later fraud-type exclusions. Use the middle of the range when the signals conflict or fields are missing.
- reason: one or two short sentences that name the billing fields you used.

How to read the fields:
- Service count vs beneficiary count: very high services per beneficiary can look like mill-style volume; a low pair is ordinary.
- Average charge vs average payment, and the charge-to-payment ratio: a large gap or an extreme ratio is more typical of later-excluded profiles than a modest ratio.
- Top-code share: a profile concentrated on one or two codes is more typical of later-excluded labs and similar specialties than a spread mix.
- Growth: a sharp jump in services, when present, adds resemblance; missing growth is not a clean-bill signal.
- Specialty: judge volume and concentration against that specialty. A clinical laboratory with huge volume and high top-code share is a different pattern than the same numbers for family practice.

A high score means resemblance to later fraud-type exclusions. It is not a finding that the firm committed fraud. Do not write that anyone committed fraud, billed illegally, or should be excluded."""


class BillingResemblance(dspy.Signature):
    """Resemblance to later fraud-type exclusions. Not a fraud finding."""

    service_count: str = dspy.InputField(desc="Service count")
    beneficiary_count: str = dspy.InputField(desc="Beneficiary count")
    average_charge: str = dspy.InputField(desc="Average charge")
    average_payment: str = dspy.InputField(desc="Average payment")
    charge_to_payment_ratio: str = dspy.InputField(desc="Charge-to-payment ratio")
    top_code_share: str = dspy.InputField(desc="Top-code share")
    specialty: str = dspy.InputField(desc="Specialty")
    growth: str = dspy.InputField(desc="Growth")
    resemblance_score: str = dspy.OutputField(desc="resemblance score in 0 to 1")
    reason: str = dspy.OutputField(desc="short reason")


BillingResemblance.instructions = INSTRUCTIONS


class BillingScorer(dspy.Module):
    """One Predict wrapper over the eight billing fields."""

    def __init__(self) -> None:
        super().__init__()
        self.predict = dspy.Predict(BillingResemblance)

    def forward(self, **kwargs):
        inputs = {key: kwargs[key] for key in INPUT_KEYS}
        return self.predict(**inputs)


def api_key_present() -> bool:
    key = os.getenv("XAI_API_KEY")
    return bool(key and key.strip())


def print_key_presence() -> None:
    print("true" if api_key_present() else "false")


def require_api_key() -> str:
    key = os.getenv("XAI_API_KEY")
    if key is None or key.strip() == "":
        print(MISSING_KEY_MESSAGE)
        raise SystemExit(1)
    return key


def field_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and np.isnan(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "<na>"}:
        return ""
    return text


def parse_score(value: object) -> float:
    text = field_text(value)
    if not text:
        return 0.0
    number = None
    token = ""
    for char in text:
        if char.isdigit() or char in ".-":
            token += char
        elif token:
            break
    if token and token not in {".", "-", "-."}:
        try:
            number = float(token)
        except ValueError:
            number = None
    if number is None:
        return 0.0
    if number > 1.0 and number <= 100.0:
        number = number / 100.0
    return float(min(1.0, max(0.0, number)))


def metric(gold, pred, trace=None, pred_name=None, pred_trace=None):
    predicted = parse_score(getattr(pred, "resemblance_score", None))
    label = int(getattr(gold, "label", 0) or 0)
    quality = 1.0 - abs(predicted - label)
    reason = field_text(getattr(pred, "reason", ""))
    if label == 1:
        feedback = (
            f"Gold is a later fraud-type exclusion. Predicted resemblance "
            f"{predicted:.3f}. Reason: {reason}. Higher resemblance is better."
        )
    else:
        feedback = (
            f"Gold is not a later fraud-type exclusion. Predicted resemblance "
            f"{predicted:.3f}. Reason: {reason}. Lower resemblance is better."
        )
    return dspy.Prediction(score=float(quality), feedback=feedback)


def load_labeled_years(
    rolled_dir: Path = ROLLED_DIR,
    leie_path: Path = LEIE_PATH,
    years: tuple[int, ...] = TRAIN_YEARS,
) -> pd.DataFrame:
    """Load 2019-2023 rolled rows and label them with the existing join.

    Demo NPIs are dropped. Year 2024 is not read. Name, city, state, and ZIP
    are never read in.
    """
    if HOLDOUT_YEAR in years:
        raise ValueError("2024 is holdout and is not a training year")
    exclusion_years = earliest_exclusion_years(leie_path)
    frames: list[pd.DataFrame] = []
    for year in years:
        path = rolled_dir / f"{year}.csv"
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
        frame = frame[frame["Year"] != str(HOLDOUT_YEAR)]
        labels = label_from_columns(
            frame["NPI"].tolist(),
            frame["Year"].tolist(),
            exclusion_years,
        )
        frame = frame.copy()
        frame["label"] = labels
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def pool_indexes(labels: list[int], seed: int = SEED) -> list[int]:
    return undersample_90_10(labels, clean_per_fraud=CLEAN_PER_FRAUD, seed=seed)


def val_count(n: int, fraction: float = VAL_FRACTION) -> int:
    """Keep a distinct val slice and put every other pool row in train."""
    if n < 2:
        raise ValueError("need at least two rows to split train and val")
    held = int(round(n * fraction))
    held = min(max(held, 1), n - 1)
    return held


def split_pool_indexes(
    pool: pd.DataFrame,
    seed: int = SEED,
) -> tuple[list[int], list[int], dict[str, int]]:
    """Use the full undersampled 2019-2023 pool. Seed 1. Val is 20%."""
    fraud = [int(index) for index in pool.index[pool["label"] == 1].tolist()]
    clean = [int(index) for index in pool.index[pool["label"] == 0].tolist()]
    rng = np.random.default_rng(seed)
    fraud_order = [fraud[int(position)] for position in rng.permutation(len(fraud))]
    clean_order = [clean[int(position)] for position in rng.permutation(len(clean))]
    val_fraud_n = val_count(len(fraud_order))
    val_clean_n = val_count(len(clean_order))
    train_fraud_n = len(fraud_order) - val_fraud_n
    train_clean_n = len(clean_order) - val_clean_n
    train = fraud_order[:train_fraud_n] + clean_order[:train_clean_n]
    val = (
        fraud_order[train_fraud_n : train_fraud_n + val_fraud_n]
        + clean_order[train_clean_n : train_clean_n + val_clean_n]
    )
    counts = {
        "train_fraud": train_fraud_n,
        "train_clean": train_clean_n,
        "val_fraud": val_fraud_n,
        "val_clean": val_clean_n,
        "pool_fraud": int((pool["label"] == 1).sum()),
        "pool_clean": int((pool["label"] == 0).sum()),
    }
    return train, val, counts


def example_from_row(row: pd.Series | dict) -> dspy.Example:
    getter = row.get if hasattr(row, "get") else lambda key, default="": row[key]
    kwargs = {FIELD_MAP[name]: field_text(getter(name, "")) for name in SIGNATURE_INPUTS}
    kwargs["label"] = int(getter("label", 0) or 0)
    kwargs["npi"] = field_text(getter("NPI", ""))
    kwargs["year"] = field_text(getter("Year", ""))
    return dspy.Example(**kwargs).with_inputs(*INPUT_KEYS)


def build_splits(
    rolled_dir: Path = ROLLED_DIR,
    leie_path: Path = LEIE_PATH,
    seed: int = SEED,
) -> tuple[list[dspy.Example], list[dspy.Example], dict[str, int]]:
    """Return trainset, valset, and the four split counts from the existing join."""
    labeled = load_labeled_years(rolled_dir=rolled_dir, leie_path=leie_path, years=TRAIN_YEARS)
    labels = [int(value) for value in labeled["label"].tolist()]
    kept = pool_indexes(labels, seed=seed)
    pool = labeled.iloc[kept].reset_index(drop=True)
    train_idx, val_idx, counts = split_pool_indexes(pool, seed=seed)
    overlap = set(train_idx).intersection(val_idx)
    if overlap:
        raise ValueError("trainset and valset must be distinct")
    train_frame = pool.iloc[train_idx]
    val_frame = pool.iloc[val_idx]
    if (train_frame["Year"] == str(HOLDOUT_YEAR)).any() or (
        val_frame["Year"] == str(HOLDOUT_YEAR)
    ).any():
        raise ValueError("2024 entered a fit set")
    train_npis = set(train_frame["NPI"].tolist())
    val_npis = set(val_frame["NPI"].tolist())
    if train_npis.intersection(DEMO_NPIS) or val_npis.intersection(DEMO_NPIS):
        raise ValueError("demo NPIs entered a fit set")
    trainset = [example_from_row(row) for _, row in train_frame.iterrows()]
    valset = [example_from_row(row) for _, row in val_frame.iterrows()]
    return trainset, valset, counts


def write_split_note(path: Path, counts: dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        "Full 2019-2023 labeled pool at 9 clean per fraud, seed 1. "
        "Every pool row is in train or val. 2024 is holdout.\n"
        f"pool_fraud={counts['pool_fraud']}\n"
        f"pool_clean={counts['pool_clean']}\n"
        f"train_fraud={counts['train_fraud']}\n"
        f"train_clean={counts['train_clean']}\n"
        f"val_fraud={counts['val_fraud']}\n"
        f"val_clean={counts['val_clean']}\n"
        f"{CAVEAT}\n"
        "Saved XGBoost figures to sit beside later: 11/48 top 1% and 18/48 top 5%.\n"
        "Paper-style forest figures: 19/48 top 1% and 48/48 top 5%.\n"
        "2024 is holdout, not fit. This run does not score the 2024 roll through the LM.\n"
    )
    path.write_text(text, encoding="utf-8")


def write_goal_program(path: Path = MODEL_PATH) -> Path:
    """Write the Predict program with the goal prompt. No API call."""
    path.parent.mkdir(parents=True, exist_ok=True)
    student = BillingScorer()
    student.save(str(path))
    redact_secrets(path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    predict = saved.get("predict") or {}
    signature = predict.get("signature") or {}
    signature["instructions"] = INSTRUCTIONS
    predict["signature"] = signature
    predict["lm"] = None
    saved["predict"] = predict
    path.write_text(json.dumps(saved, indent=2) + "\n", encoding="utf-8")
    redact_secrets(path)
    return path


def append_holdout_note(path: Path) -> None:
    extra = (
        f"{CAVEAT}\n"
        "Saved XGBoost figures to sit beside later: 11/48 top 1% and 18/48 top 5%.\n"
        "Paper-style forest figures: 19/48 top 1% and 48/48 top 5%.\n"
        "2024 is holdout, not fit. This run does not score the 2024 roll through the LM.\n"
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(extra)


def print_split_counts(counts: dict[str, int]) -> None:
    print(f"train_fraud={counts['train_fraud']}")
    print(f"train_clean={counts['train_clean']}")
    print(f"val_fraud={counts['val_fraud']}")
    print(f"val_clean={counts['val_clean']}")


def make_student_lm() -> dspy.LM:
    return dspy.LM(
        STUDENT_MODEL,
        api_key=os.getenv("XAI_API_KEY"),
        api_base=API_BASE,
    )


def make_reflection_lm() -> dspy.LM:
    return dspy.LM(
        REFLECTION_MODEL,
        api_key=os.getenv("XAI_API_KEY"),
        api_base=API_BASE,
    )


def is_rate_limit(exc: BaseException) -> bool:
    text = str(exc).lower()
    return "rate" in text or "429" in text or "too many requests" in text


def call_with_retry(fn, attempts: int = 12, delay: float = 10.0):
    last: BaseException | None = None
    for _ in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — retry only rate limits
            last = exc
            if not is_rate_limit(exc):
                raise
            time.sleep(delay)
            delay = min(delay * 2.0, 120.0)
    if last is not None:
        raise last
    raise RuntimeError("retry loop exited without a result")


def example_inputs(row: pd.Series | dict | dspy.Example) -> dict[str, str]:
    if isinstance(row, dspy.Example):
        return {key: field_text(row.get(key, "")) for key in INPUT_KEYS}
    getter = row.get if hasattr(row, "get") else lambda key, default="": row[key]
    return {FIELD_MAP[name]: field_text(getter(name, getter(FIELD_MAP[name], ""))) for name in SIGNATURE_INPUTS}


def last_call_model_and_stream(lm: dspy.LM) -> tuple[str, bool]:
    history = getattr(lm, "history", None) or []
    if not history:
        model = str(getattr(lm, "model", STUDENT_MODEL))
        return model, False
    rec = history[-1]
    model = ""
    stream = False
    if isinstance(rec, dict):
        model = str(rec.get("model") or rec.get("kwargs", {}).get("model") or "")
        kwargs = rec.get("kwargs") or {}
        stream = bool(kwargs.get("stream", False) or rec.get("stream", False))
    if not model:
        model = str(getattr(lm, "model", STUDENT_MODEL))
    return model, stream


def score_row(row: dict | pd.Series, program: dspy.Module | None = None) -> tuple[float, str]:
    """Score one provider-year from the eight billing fields."""
    require_api_key()
    lm = make_student_lm()
    dspy.configure(lm=lm)
    if program is None:
        program = BillingScorer()
        if MODEL_PATH.is_file():
            program.load(str(MODEL_PATH))
    pred = program(**example_inputs(row))
    return parse_score(getattr(pred, "resemblance_score", None)), field_text(
        getattr(pred, "reason", "")
    )


def smoke_call(example: dspy.Example, program: dspy.Module, lm: dspy.LM) -> tuple[float, str]:
    dspy.configure(lm=lm)
    pred = call_with_retry(lambda: program(**example_inputs(example)))
    score = parse_score(getattr(pred, "resemblance_score", None))
    reason = field_text(getattr(pred, "reason", ""))
    model, stream = last_call_model_and_stream(lm)
    print(f"smoke_model={model}")
    print(f"smoke_stream={stream}")
    if "grok-4.20-0309-non-reasoning" in str(model) and stream is False:
        print("smoke used grok-4.20-0309-non-reasoning and did not stream")
    print(f"smoke_score={score}")
    print(f"smoke_reason={reason}")
    return score, reason


def redact_secrets(path: Path) -> None:
    """Drop key-shaped fields from the saved JSON without printing any secret."""
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            for key in list(obj):
                lowered = str(key).lower()
                if lowered in {"api_key", "authorization", "xai_api_key", "bearer"}:
                    obj[key] = None
                else:
                    walk(obj[key])
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    key = os.getenv("XAI_API_KEY") or ""
    text = path.read_text(encoding="utf-8")
    if key and key in text:
        path.write_text(text.replace(key, ""), encoding="utf-8")


def compile_and_save(
    trainset: list[dspy.Example],
    valset: list[dspy.Example],
) -> Path:
    require_api_key()
    student_lm = make_student_lm()
    reflection_lm = make_reflection_lm()
    dspy.configure(lm=student_lm)
    student = BillingScorer()
    optimizer = dspy.GEPA(
        metric=metric,
        reflection_lm=reflection_lm,
        max_metric_calls=2000,
    )
    compiled = call_with_retry(
        lambda: optimizer.compile(student, trainset=trainset, valset=valset)
    )
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    compiled.save("models/harness_gepa.json")
    redact_secrets(MODEL_PATH)
    return MODEL_PATH


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--key-present"]:
        print_key_presence()
        return 0
    if args == ["--setup"]:
        trainset, valset, counts = build_splits()
        print_split_counts(counts)
        write_split_note(NOTE_PATH, counts)
        write_goal_program(MODEL_PATH)
        print(f"train_examples={len(trainset)}")
        print(f"val_examples={len(valset)}")
        print(f"saved={MODEL_PATH}")
        return 0
    require_api_key()
    trainset, valset, counts = build_splits()
    print_split_counts(counts)
    write_split_note(NOTE_PATH, counts)
    student_lm = make_student_lm()
    dspy.configure(lm=student_lm)
    student = BillingScorer()
    smoke_ex = next(
        example
        for example in [*valset, *trainset]
        if field_text(example.get("npi", "")) not in DEMO_NPIS
    )
    smoke_call(smoke_ex, student, student_lm)
    sys.stdout.flush()
    sys.stderr.flush()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, force=True)
    try:
        compile_and_save(trainset, valset)
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        raise
    print(CAVEAT)
    print(f"saved={MODEL_PATH}")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

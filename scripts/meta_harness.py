"""Let an agent rewrite harness/score_rows.py. The parent keeps the score.

Search years are 2019-2022. Selection year is 2023 and decides what is
kept. Confirmation year is 2024 and is scored once after proposal 12.

The agent may edit only harness/score_rows.py. A candidate that imports a
module, opens a file, or reads NPI, name, city, state, ZIP, or year is
rejected before it is scored. Frozen tree and page-forest scores are
computed by the parent and passed in.

A high score means the billing profile resembles providers later excluded
for a fraud-type reason. This is not a finding that the firm committed fraud.
"""

from __future__ import annotations

import ast
import json
import os
import random
import re
import sys
import time
import traceback
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.harness_score import CAVEAT, is_rate_limit  # noqa: E402
from scripts.join_labels import DEMO_NPIS, earliest_exclusion_years  # noqa: E402
from scripts.rank_evolve import (  # noqa: E402
    beats_xgboost,
    feature_dicts,
    list_fitness,
    load_year_frame,
    sample_frame,
    should_keep,
    slice_stats,
    tree_scores_for,
)
from scripts.train import FEATURE_COLUMNS, LEIE_PATH, SEED  # noqa: E402

SEARCH_YEARS = (2019, 2020, 2021, 2022)
SELECTION_YEAR = 2023
CONFIRM_YEAR = 2024
CLEAN_PER_FRAUD = 9
CONFIRM_CLEAN_PER = 5
PROPOSAL_COUNT = 12
PROPOSER_MODEL = "grok-4.6"
REASONING_EFFORT = "high"
API_BASE = "https://api.x.ai/v1"
MISSING_KEY_MESSAGE = "set XAI_API_KEY"
NOTE_PATH = REPO_ROOT / "models" / "meta_harness_note.txt"
HARNESS_PATH = REPO_ROOT / "harness" / "score_rows.py"
PAPER_SCORE_DIR = REPO_ROOT / "data" / "paper_scores"
BANNED_READS = ("NPI", "Name", "City", "State", "ZIP", "Year")
IMPORT_NAMES = frozenset({"import", "__import__", "importlib", "reload"})
OPEN_NAMES = frozenset({"open", "file"})
SAFE_BUILTINS = {
    "float": float,
    "int": int,
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "len": len,
    "str": str,
    "bool": bool,
    "dict": dict,
    "list": list,
    "tuple": tuple,
    "sum": sum,
    "sorted": sorted,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "any": any,
    "all": all,
    "True": True,
    "False": False,
    "None": None,
}


def require_key() -> str:
    key = os.getenv("XAI_API_KEY")
    if key is None or key.strip() == "":
        print(MISSING_KEY_MESSAGE)
        raise SystemExit(1)
    return key


def _name_text(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _constant_text(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""


def reject_reason(source: str) -> str | None:
    """Reject an import, a file open, an identifier read, or a missing score_rows."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return f"syntax error: {exc.msg}"
    banned_lower = {name.lower() for name in BANNED_READS}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return "import is not allowed"
        if isinstance(node, ast.Call):
            called = _name_text(node.func)
            if called in IMPORT_NAMES or called in OPEN_NAMES:
                return f"{called} is not allowed"
        if isinstance(node, ast.Attribute) and node.attr.lower() in banned_lower:
            return f"read of {node.attr} is not allowed"
        if isinstance(node, ast.Name) and node.id.lower() in banned_lower:
            return f"read of {node.id} is not allowed"
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.lower() in banned_lower:
                return f"read of {node.value} is not allowed"
        if isinstance(node, ast.Subscript):
            key = _constant_text(node.slice)
            if key.lower() in banned_lower:
                return f"read of {key} is not allowed"
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "score_rows"
    ]
    if len(functions) != 1:
        return "source must define exactly one score_rows function"
    args = [arg.arg for arg in functions[0].args.args]
    if args != ["rows"]:
        return "score_rows must take rows"
    return None


def compile_score_rows(source: str) -> Callable:
    reason = reject_reason(source)
    if reason is not None:
        raise ValueError(reason)
    namespace: dict = {"__builtins__": SAFE_BUILTINS}
    exec(source, namespace, namespace)  # noqa: S102 — imports and opens already rejected
    fn = namespace.get("score_rows")
    if not callable(fn):
        raise ValueError("score_rows was not defined")
    return fn


def paper_scores_for(frame: pd.DataFrame) -> list[float]:
    """Page-forest scores already written under data/paper_scores. No fit."""
    by_year: dict[str, dict[str, float]] = {}
    for year in sorted(set(frame["Year"].astype(str))):
        path = PAPER_SCORE_DIR / f"{year}.csv"
        table = pd.read_csv(path, dtype={"npi": str, "year": str})
        by_year[year] = {
            str(npi).strip(): float(score)
            for npi, score in zip(table["npi"], table["score"])
        }
    scores: list[float] = []
    for npi, year in zip(frame["NPI"].astype(str), frame["Year"].astype(str)):
        found = by_year.get(year, {}).get(npi.strip())
        if found is None:
            print(f"paper score missing npi={npi.strip()} year={year}; using 0", flush=True)
            found = 0.0
        scores.append(found)
    return scores


def harness_rows(
    features: list[dict],
    tree_scores: list[float],
    paper_scores: list[float],
) -> list[dict]:
    """Eight billing fields plus the two frozen scores. No identifier."""
    rows: list[dict] = []
    for features_row, tree_score, paper_score in zip(features, tree_scores, paper_scores):
        row = dict(features_row)
        row["tree_score"] = float(tree_score)
        row["paper_score"] = float(paper_score)
        rows.append(row)
    return rows


def run_harness(fn: Callable, rows: list[dict]) -> list[float]:
    scored = fn(rows)
    if not isinstance(scored, list) or len(scored) != len(rows):
        raise ValueError("score_rows must return one float per row")
    out = [float(value) for value in scored]
    if not all(np.isfinite(value) for value in out):
        raise ValueError("score is not a finite number")
    return out


def score_source(
    source: str,
    rows: list[dict],
    labels: list[int],
) -> tuple[Callable | None, dict | None, float | None, str | None, list[float] | None]:
    reason = reject_reason(source)
    if reason is not None:
        return None, None, None, reason, None
    try:
        fn = compile_score_rows(source)
        scores = run_harness(fn, rows)
    except Exception as exc:  # noqa: BLE001 — the error is the next note
        return None, None, None, f"{type(exc).__name__}: {exc}", None
    stats = slice_stats(scores, labels)
    return fn, stats, list_fitness(scores, labels), None, scores


def extract_source(text: str) -> str:
    fenced = re.findall(r"```(?:python)?\s*([\s\S]*?)```", text)
    blob = fenced[-1] if fenced else text
    match = re.search(r"def score_rows\s*\(.*", blob, flags=re.S)
    if match is None:
        return blob.strip() + "\n"
    return match.group(0).strip() + "\n"


def propose_source(
    parent: str,
    note: str,
    key: str,
    proposer: Callable | None = None,
) -> tuple[str, str, str]:
    """Ask grok-4.6 for the next harness file. A stub is for the loop test."""
    if proposer is not None:
        proposed = proposer(parent, note)
        if isinstance(proposed, tuple):
            return str(proposed[0]), str(proposed[1]), str(proposed[2])
        return str(proposed), "", ""
    from openai import OpenAI

    client = OpenAI(api_key=key, base_url=API_BASE)
    system = (
        "You own one Python file. It must define score_rows(rows). "
        "Each row is a dict with eight billing fields plus tree_score and "
        "paper_score. tree_score is the frozen shallow XGBoost probability. "
        "paper_score is the frozen page-forest score. Return a list of "
        "floats, one per row, same order. Higher means more resemblance to "
        "later fraud-type exclusions. Do not say the firm committed fraud. "
        "You may combine the two frozen scores and the eight fields. "
        "Do not import a module. Do not open a file. Do not read NPI, name, "
        "city, state, ZIP, or year. Reply with the whole file."
    )
    user = f"Current file:\n{parent}\n\nNote from the last attempt:\n{note}\n"
    delay = 5.0
    last: BaseException | None = None
    for _ in range(8):
        try:
            response = client.chat.completions.create(
                model=PROPOSER_MODEL,
                temperature=0.7,
                extra_body={"reasoning_effort": REASONING_EFFORT},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            text = response.choices[0].message.content or ""
            model = str(getattr(response, "model", "") or "")
            reply_id = str(getattr(response, "id", "") or "")
            return extract_source(text), model, reply_id
        except Exception as exc:  # noqa: BLE001
            last = exc
            if not is_rate_limit(exc):
                raise
            time.sleep(delay)
            delay = min(delay * 2.0, 60.0)
    if last is not None:
        raise last
    raise RuntimeError("proposer call failed")


def scrub(text: str, key: str) -> str:
    if key and key in text:
        return text.replace(key, "")
    return text


def write_harness(source: str, key: str) -> None:
    HARNESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    HARNESS_PATH.write_text(scrub(source, key), encoding="utf-8")


def write_note(text: str, key: str) -> None:
    NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTE_PATH.write_text(scrub(text, key), encoding="utf-8")
    print(scrub(text, key), flush=True)


def missed_rows(scores: list[float], labels: list[int], rows: list[dict], limit: int = 8) -> list[dict]:
    if not scores:
        return []
    cutoff = float(np.percentile(np.asarray(scores, dtype=float), 99))
    missed = []
    for score, label, row in zip(scores, labels, rows):
        if label == 1 and score < cutoff:
            missed.append({name: row.get(name) for name in (*FEATURE_COLUMNS, "tree_score", "paper_score")})
        if len(missed) >= limit:
            break
    return missed


def format_stats(stats: dict, fitness: float) -> str:
    return (
        f"top1={int(stats['top1_captured'])}/{int(stats['top1_fraud'])} "
        f"top5={int(stats['top5_captured'])}/{int(stats['top5_fraud'])} "
        f"slice={int(stats['top1_slice'])}/{int(stats['rows'])} "
        f"fitness={fitness:.4f}"
    )


def run_loop(
    select_rows: list[dict],
    select_labels: list[int],
    key: str,
    seed_source: str,
    proposer: Callable | None = None,
    proposal_count: int = PROPOSAL_COUNT,
    rng: random.Random | None = None,
) -> dict:
    """Score the seed on selection, then run exactly proposal_count proposals."""
    draw = rng if rng is not None else random.Random(SEED)
    _fn, stats, fitness, error, scores = score_source(seed_source, select_rows, select_labels)
    if error is not None or stats is None or fitness is None:
        raise RuntimeError(f"seed failed selection scoring: {error}")
    seed = {"source": seed_source, "stats": stats, "fitness": fitness, "kept": False}
    best = dict(seed)
    note = (
        "Seed scored on the 2023 selection file before proposal 1. "
        + format_stats(stats, fitness)
        + ". Missed selection fraud rows: "
        + json.dumps(missed_rows(scores or [], select_labels, select_rows))
        + ". No proposal has run."
    )
    print(note, flush=True)
    proposals: list[dict] = []
    parent = seed_source
    parent_fitness = fitness
    for step in range(1, proposal_count + 1):
        record: dict = {"proposal": step, "kept": False, "source": "", "error": ""}
        try:
            source, response_model, response_id = propose_source(parent, note, key, proposer)
        except Exception as exc:  # noqa: BLE001
            record["error"] = f"{type(exc).__name__}: {exc}"
            record["response_model"] = ""
            record["response_id"] = ""
            note = f"Proposal {step} proposer error: {record['error']}"
            print(
                f"proposal={step} kept=False response_model= response_id= {note}",
                flush=True,
            )
            proposals.append(record)
            continue
        record["source"] = source
        record["response_model"] = response_model
        record["response_id"] = response_id
        flat = " ".join(source.split())
        _child, child_stats, child_fitness, child_error, child_scores = score_source(
            source, select_rows, select_labels
        )
        if child_error is not None or child_stats is None or child_fitness is None:
            record["error"] = child_error or "score failed"
            note = f"Proposal {step} error: {record['error']}\nSource:\n{source}"
            print(
                f"proposal={step} kept=False response_model={response_model} "
                f"response_id={response_id} {note.splitlines()[0]}",
                flush=True,
            )
            print(f"score_rows={flat}", flush=True)
            proposals.append(record)
            continue
        record["stats"] = child_stats
        record["fitness"] = child_fitness
        if should_keep(child_fitness, parent_fitness, child_stats):
            record["kept"] = True
            note = (
                f"Proposal {step} kept. Selection {format_stats(child_stats, child_fitness)}. "
                f"Parent fitness {parent_fitness:.4f}. "
                f"Missed selection fraud rows: "
                f"{json.dumps(missed_rows(child_scores or [], select_labels, select_rows))}"
            )
            parent = source
            parent_fitness = child_fitness
            if child_fitness > float(best["fitness"]) or not best.get("kept"):
                best = dict(record)
        else:
            note = (
                f"Proposal {step} lost to its parent. Selection "
                f"{format_stats(child_stats, child_fitness)}. "
                f"Parent fitness {parent_fitness:.4f}. Not kept. "
                f"Missed selection fraud rows: "
                f"{json.dumps(missed_rows(child_scores or [], select_labels, select_rows))}"
            )
        print(
            f"proposal={step} kept={record['kept']} response_model={response_model} "
            f"response_id={response_id} {note.splitlines()[0]}",
            flush=True,
        )
        print(f"score_rows={flat}", flush=True)
        proposals.append(record)
        _ = draw.random()
    if len(proposals) != proposal_count:
        raise RuntimeError(f"expected {proposal_count} proposals, recorded {len(proposals)}")
    return {"seed": seed, "proposals": proposals, "best": best, "note": note}


def render_note(loop: dict, confirm_stats: dict, paper_stats: dict, tree_stats: dict, beat_paper: bool) -> str:
    seed = loop["seed"]
    kept = [item for item in loop["proposals"] if item.get("kept")]
    reply_ids = [str(item.get("response_id") or "") for item in loop["proposals"]]
    models = [str(item.get("response_model") or "") for item in loop["proposals"] if item.get("response_model")]
    lines = [
        "Meta harness. The agent rewrote harness/score_rows.py. The parent scored it.",
        f"proposer={PROPOSER_MODEL}",
        f"response_model={models[0] if models else ''}",
        "response_ids=" + ",".join(reply_ids),
        f"reasoning_effort={REASONING_EFFORT}",
        f"api_base={API_BASE}",
        f"proposals={len(loop['proposals'])}",
        f"selection_seed_top1={int(seed['stats']['top1_captured'])}/{int(seed['stats']['top1_fraud'])}",
        f"selection_seed_top1_slice={int(seed['stats']['top1_slice'])}/{int(seed['stats']['rows'])}",
        f"selection_seed_fitness={float(seed['fitness']):.4f}",
        f"kept_count={len(kept)}",
        CAVEAT,
        "Confirmation is a 2024 subsample: every fraud row and "
        f"{CONFIRM_CLEAN_PER} clean rows per fraud row, seed {SEED}. "
        "It is not the full 1.21 million-row year.",
        f"confirm_top1={int(confirm_stats['top1_captured'])}/{int(confirm_stats['top1_fraud'])}",
        f"same_rows_paper_top1={int(paper_stats['top1_captured'])}/{int(paper_stats['top1_fraud'])}",
        f"same_rows_xgboost_top1={int(tree_stats['top1_captured'])}/{int(tree_stats['top1_fraud'])}",
        f"beats_paper_on_same_rows={beat_paper}",
        "The optimized model was not scored here. Its saved full-year figure is 20/48.",
        "A high score means resemblance to later fraud-type exclusions. "
        "It is not a finding that the firm committed fraud.",
    ]
    return "\n".join(lines) + "\n"


def load_sample(years: tuple[int, ...], clean_per: int) -> pd.DataFrame:
    print(f"loading {years}", flush=True)
    return sample_frame(load_year_frame(years), fraud_cap=None, clean_per=clean_per, seed=SEED)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--loop-only" in args:
        return 0
    key = require_key()
    if "--key-present" in args:
        print("true")
        return 0
    selection = load_sample((SELECTION_YEAR,), CLEAN_PER_FRAUD)
    search = load_sample(SEARCH_YEARS, CLEAN_PER_FRAUD)
    if (search["Year"] == str(CONFIRM_YEAR)).any() or (selection["Year"] == str(CONFIRM_YEAR)).any():
        raise SystemExit("2024 entered the search")
    select_features = feature_dicts(selection)
    select_labels = [int(value) for value in selection["label"].tolist()]
    print("scoring frozen models on selection", flush=True)
    select_trees = tree_scores_for(selection)
    select_paper = paper_scores_for(selection)
    select_rows = harness_rows(select_features, select_trees, select_paper)
    seed_source = HARNESS_PATH.read_text(encoding="utf-8")
    loop = run_loop(select_rows, select_labels, key, seed_source)
    write_harness(str(loop["best"]["source"]), key)
    print("loading 2024 confirmation", flush=True)
    confirm = load_sample((CONFIRM_YEAR,), CONFIRM_CLEAN_PER)
    confirm_rows = harness_rows(
        feature_dicts(confirm),
        tree_scores_for(confirm),
        paper_scores_for(confirm),
    )
    confirm_labels = [int(value) for value in confirm["label"].tolist()]
    winner = compile_score_rows(str(loop["best"]["source"]))
    confirm_scores = run_harness(winner, confirm_rows)
    confirm_stats = slice_stats(confirm_scores, confirm_labels)
    paper_stats = slice_stats([float(row["paper_score"]) for row in confirm_rows], confirm_labels)
    tree_stats = slice_stats([float(row["tree_score"]) for row in confirm_rows], confirm_labels)
    beat_paper = beats_xgboost(confirm_stats, paper_stats)
    write_note(render_note(loop, confirm_stats, paper_stats, tree_stats, beat_paper), key)
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

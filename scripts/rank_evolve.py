"""Evolve one capped scoring function over the fraud list.

Search years are 2019-2022. Selection year is 2023 and decides what is
kept. Confirmation year is 2024 and is scored once after proposal 20.

The seed returns the frozen shallow XGBoost score. A proposal may add one
adjustment whose absolute value is at most 0.15. A function that imports a
module, opens a file, or reads NPI, name, city, state, ZIP, or year is
rejected before it is scored.

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
import textwrap
import time
import traceback
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.harness_score import CAVEAT  # noqa: E402
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
CLEAN_PER_FRAUD = 9
CONFIRM_CLEAN_PER = 5
MAX_ADJUSTMENT = 0.15
MAX_SLICE_SHARE = 0.02
ISLANDS = 2
PROPOSAL_COUNT = 20
PROPOSER_MODEL = "grok-4.6"
REASONING_EFFORT = "high"
API_BASE = "https://api.x.ai/v1"
MISSING_KEY_MESSAGE = "set XAI_API_KEY"
NOTE_PATH = REPO_ROOT / "models" / "rank_evolve_note.txt"
SCORE_PATH = REPO_ROOT / "models" / "rank_evolve_score.py"
XGB_PATH = REPO_ROOT / "models" / "xgb_shallow.json"
READ_COLUMNS = ("NPI", "Year", *FEATURE_COLUMNS)
BANNED_READS = ("NPI", "Name", "City", "State", "ZIP", "Year")
IMPORT_NAMES = frozenset({"import", "__import__", "importlib", "reload"})
OPEN_NAMES = frozenset({"open", "file"})

SEED_SOURCE = textwrap.dedent(
    '''\
    def score_row(features: dict, tree_score: float) -> float:
        """Return the frozen shallow XGBoost score. Change nothing."""
        return tree_score
    '''
).strip() + "\n"


def require_key() -> str:
    """Return the environment key. Print only the missing-key line."""
    key = os.getenv("XAI_API_KEY")
    if key is None or key.strip() == "":
        print(MISSING_KEY_MESSAGE)
        raise SystemExit(1)
    return key


def seed_score_row(features: dict, tree_score: float) -> float:
    """Shipped seed. Returns the frozen tree score and changes nothing."""
    return tree_score


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
    """Reject a function that imports, opens a file, or reads an identifier.

    The check runs before scoring. A syntax error is also a rejection.
    """
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
        if isinstance(node, ast.FunctionDef) and node.name == "score_row"
    ]
    if len(functions) != 1:
        return "source must define exactly one score_row function"
    if len(tree.body) != 1:
        return "source must contain only the score_row function"
    score_fn = functions[0]
    args = [arg.arg for arg in score_fn.args.args]
    if args != ["features", "tree_score"]:
        return "score_row must take features and tree_score"
    return None


def adjustment_reason(fn: Callable, features: dict, tree_score: float) -> str | None:
    """Reject a call whose result moves more than 0.15 from the tree score."""
    try:
        scored = float(fn(features, tree_score))
    except Exception as exc:  # noqa: BLE001 — the error is the next note
        return f"{type(exc).__name__}: {exc}"
    if not np.isfinite(scored):
        return "score is not a finite number"
    if abs(scored - float(tree_score)) > MAX_ADJUSTMENT + 1e-12:
        return f"absolute adjustment {abs(scored - float(tree_score)):.6f} exceeds 0.15"
    return None


def check_adjustment_cap(
    fn: Callable,
    feature_rows: list[dict],
    tree_scores: list[float],
) -> str | None:
    """Score every row and reject the first adjustment above 0.15."""
    for features, tree_score in zip(feature_rows, tree_scores):
        reason = adjustment_reason(fn, features, tree_score)
        if reason is not None:
            return reason
    return None


def compile_score_row(source: str) -> Callable:
    """Compile a rejected-clean source into score_row. No imports, no files."""
    reason = reject_reason(source)
    if reason is not None:
        raise ValueError(reason)
    safe_builtins = {
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
        "True": True,
        "False": False,
        "None": None,
    }
    namespace: dict = {"__builtins__": safe_builtins}
    exec(source, namespace, namespace)  # noqa: S102 — source already rejected imports and opens
    fn = namespace.get("score_row")
    if not callable(fn):
        raise ValueError("score_row was not defined")
    return fn


def slice_stats(scores: list[float], labels: list[int]) -> dict[str, int | float]:
    """Top 1 percent fraud count, slice size, and extra rows past 1 percent."""
    captured, fraud_count, _share = top_slice_share(scores, labels, 99)
    top5 = top_slice_share(scores, labels, 95)
    rows = len(scores)
    if scores:
        cutoff = float(np.percentile(np.asarray(scores, dtype=float), 99))
        in_slice = sum(1 for score in scores if score >= cutoff)
    else:
        in_slice = 0
    target = rows * 0.01
    extra = max(0, in_slice - target)
    return {
        "top1_captured": captured,
        "top1_fraud": fraud_count,
        "top5_captured": top5[0],
        "top5_fraud": top5[1],
        "top1_slice": in_slice,
        "rows": rows,
        "extra_slice_rows": extra,
    }


def list_fitness(scores: list[float], labels: list[int]) -> float:
    """top_1_percent_fraud_count - 0.25 * extra_slice_rows."""
    stats = slice_stats(scores, labels)
    return float(stats["top1_captured"]) - 0.25 * float(stats["extra_slice_rows"])


def slice_within_cap(stats: dict[str, int | float]) -> bool:
    """True when the top 1 percent slice holds at most 2 percent of the rows."""
    rows = int(stats["rows"])
    if rows == 0:
        return False
    return int(stats["top1_slice"]) <= rows * MAX_SLICE_SHARE


def should_keep(
    child_fitness: float,
    parent_fitness: float,
    child_stats: dict[str, int | float],
) -> bool:
    """Keep only a strict selection-fitness gain with a slice of at most 2 percent."""
    return child_fitness > parent_fitness and slice_within_cap(child_stats)


def beats_xgboost(winner_stats: dict[str, int | float], tree_stats: dict[str, int | float]) -> bool:
    """True only when the winner catches more fraud rows and the slice stays capped."""
    return (
        int(winner_stats["top1_captured"]) > int(tree_stats["top1_captured"])
        and slice_within_cap(winner_stats)
    )


def load_year_frame(years: tuple[int, ...]) -> pd.DataFrame:
    """Read rolled years, drop demo NPIs, and attach the later-exclusion label."""
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


def draw_indexes(
    fraud_index: np.ndarray,
    clean_index: np.ndarray,
    fraud_cap: int | None,
    clean_per: int,
    seed: int,
) -> np.ndarray:
    """Same draw as the rank harness: cap fraud, then clean_per clean rows, seed 1."""
    rng = np.random.default_rng(seed)
    fraud = np.asarray(fraud_index)
    clean = np.asarray(clean_index)
    if fraud_cap is not None and len(fraud) > fraud_cap:
        fraud = rng.choice(fraud, size=fraud_cap, replace=False)
    clean_target = clean_per * max(len(fraud), 1)
    if len(clean) > clean_target:
        clean = rng.choice(clean, size=clean_target, replace=False)
    if len(fraud) or len(clean):
        return np.sort(np.concatenate([np.asarray(fraud), np.asarray(clean)]))
    return np.asarray(fraud)


def sample_frame(
    frame: pd.DataFrame,
    fraud_cap: int | None,
    clean_per: int,
    seed: int,
) -> pd.DataFrame:
    """Keep every fraud row, or a cap, then clean_per clean rows per kept fraud row."""
    chosen = draw_indexes(
        frame.index[frame["label"] == 1].to_numpy(),
        frame.index[frame["label"] == 0].to_numpy(),
        fraud_cap,
        clean_per,
        seed,
    )
    if len(chosen) == 0:
        return frame.iloc[0:0].reset_index(drop=True)
    return frame.loc[chosen].reset_index(drop=True)


def _labeled_chunk(
    chunk: pd.DataFrame,
    exclusion_years: dict[str, int],
) -> tuple[pd.DataFrame, np.ndarray]:
    """Drop demo NPIs and return the chunk with a 0/1 label array."""
    npi = chunk["NPI"].astype(str).str.strip()
    year_text = chunk["Year"].astype(str).str.strip()
    keep = ~npi.isin(DEMO_NPIS)
    chunk = chunk.loc[keep].copy()
    if chunk.empty:
        return chunk, np.empty(0, dtype=int)
    npi = npi.loc[keep]
    year_text = year_text.loc[keep]
    chunk["NPI"] = npi.to_numpy()
    chunk["Year"] = year_text.to_numpy()
    labels = np.asarray(
        label_from_columns(npi.tolist(), year_text.tolist(), exclusion_years),
        dtype=int,
    )
    return chunk, labels


def _chunk_reader(path: Path):
    return pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
        usecols=list(READ_COLUMNS),
        chunksize=250_000,
    )


def sample_years(
    years: tuple[int, ...],
    fraud_cap: int | None,
    clean_per: int,
    seed: int,
    rolled_dir: Path = ROLLED_DIR,
    leie_path: Path = LEIE_PATH,
) -> pd.DataFrame:
    """Read each year in chunks and keep the rows sample_frame would keep.

    The reset index matches load_year_frame: demo NPIs dropped, years
    concatenated, index restarted at 0. The draw uses that index, so the
    2024 clean rows match the harness subsample for the same seed.
    """
    exclusion_years = earliest_exclusion_years(leie_path)
    fraud_parts: list[pd.DataFrame] = []
    fraud_at: list[int] = []
    clean_at: list[int] = []
    cursor = 0
    for year in years:
        print(f"scan year={year}", flush=True)
        for chunk in _chunk_reader(rolled_dir / f"{year}.csv"):
            labeled, labels = _labeled_chunk(chunk, exclusion_years)
            count = len(labeled)
            if count == 0:
                continue
            positions = np.arange(cursor, cursor + count)
            fraud_mask = labels == 1
            if bool(fraud_mask.any()):
                part = labeled.loc[fraud_mask].copy()
                part["label"] = 1
                fraud_parts.append(part)
                fraud_at.extend(int(value) for value in positions[fraud_mask])
            clean_at.extend(int(value) for value in positions[labels == 0])
            cursor += count
    fraud_index = np.asarray(fraud_at, dtype=np.int64)
    clean_index = np.asarray(clean_at, dtype=np.int64)
    chosen = draw_indexes(fraud_index, clean_index, fraud_cap, clean_per, seed)
    fraud_set = set(int(value) for value in fraud_index)
    clean_wanted = np.asarray(
        [int(value) for value in chosen if int(value) not in fraud_set],
        dtype=np.int64,
    )
    drawn: dict[int, dict] = {}
    cursor = 0
    want_at = 0
    if len(clean_wanted):
        for year in years:
            for chunk in _chunk_reader(rolled_dir / f"{year}.csv"):
                labeled, labels = _labeled_chunk(chunk, exclusion_years)
                count = len(labeled)
                if count == 0:
                    continue
                start = cursor
                stop = cursor + count
                while want_at < len(clean_wanted) and clean_wanted[want_at] < start:
                    want_at += 1
                hits = []
                scan = want_at
                while scan < len(clean_wanted) and clean_wanted[scan] < stop:
                    hits.append(int(clean_wanted[scan] - start))
                    scan += 1
                if hits:
                    part = labeled.iloc[hits].copy()
                    part["label"] = 0
                    for offset, row in zip(hits, part.to_dict(orient="records")):
                        drawn[start + offset] = row
                    want_at = scan
                cursor = stop
                if want_at >= len(clean_wanted):
                    break
            if want_at >= len(clean_wanted):
                break
    fraud_rows = (
        pd.concat(fraud_parts, ignore_index=True).to_dict(orient="records")
        if fraud_parts
        else []
    )
    fraud_by_pos = {position: row for position, row in zip(fraud_at, fraud_rows)}
    ordered = []
    for position in chosen:
        key = int(position)
        row = fraud_by_pos.get(key, drawn.get(key))
        if row is not None:
            ordered.append(row)
    frame = pd.DataFrame(ordered)
    if frame.empty:
        return pd.DataFrame(columns=[*READ_COLUMNS, "label"])
    return frame.reset_index(drop=True)


def tree_scores_for(frame: pd.DataFrame) -> list[float]:
    """Positive-class probability from the frozen shallow model. Does not fit."""
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
    booster.load_model(XGB_PATH)
    return [float(row[1]) for row in booster.predict_proba(features)]


def feature_dicts(frame: pd.DataFrame) -> list[dict]:
    """Eight billing fields only. Identifiers stay out of the candidate."""
    rows: list[dict] = []
    for _, row in frame.iterrows():
        payload: dict = {}
        for name in FEATURE_COLUMNS:
            text = "" if row.get(name) is None else str(row.get(name)).strip()
            if name == "Specialty":
                payload[name] = text
            else:
                try:
                    payload[name] = float(text) if text != "" else None
                except ValueError:
                    payload[name] = None
        rows.append(payload)
    return rows


def apply_scores(
    fn: Callable,
    feature_rows: list[dict],
    tree_scores: list[float],
) -> list[float]:
    """Run the candidate. The tree score is computed outside the function."""
    return [float(fn(features, tree_score)) for features, tree_score in zip(feature_rows, tree_scores)]


def missed_rows(
    scores: list[float],
    labels: list[int],
    feature_rows: list[dict],
    limit: int = 8,
) -> list[dict]:
    """Fraud rows below the top 1 percent cutoff, eight fields only."""
    if not scores:
        return []
    cutoff = float(np.percentile(np.asarray(scores, dtype=float), 99))
    missed = [
        features
        for score, label, features in zip(scores, labels, feature_rows)
        if label == 1 and score < cutoff
    ]
    return missed[:limit]


def format_stats(stats: dict[str, int | float], fitness: float) -> str:
    return (
        f"top1={int(stats['top1_captured'])}/{int(stats['top1_fraud'])} "
        f"top5={int(stats['top5_captured'])}/{int(stats['top5_fraud'])} "
        f"slice={int(stats['top1_slice'])}/{int(stats['rows'])} "
        f"fitness={fitness:.4f}"
    )


def scrub(text: str, key: str) -> str:
    """Drop the API key if it ever lands in a note or a saved function."""
    if key and key in text:
        return text.replace(key, "")
    return text


def write_score(source: str, key: str) -> None:
    SCORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCORE_PATH.write_text(scrub(source, key), encoding="utf-8")


def write_note(text: str, key: str) -> None:
    NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTE_PATH.write_text(scrub(text, key), encoding="utf-8")
    print(scrub(text, key), flush=True)


def parent_source(
    island: int,
    islands: list[list[dict]],
    rng: random.Random,
) -> tuple[str, float, int]:
    """Half the time the island's best, half a random kept function.

    The proposer also sees the other island's best and one random kept
    function. That second view is built in propose_source, not here.
    """
    kept = islands[island]
    best = max(kept, key=lambda item: float(item["fitness"]))
    if rng.random() < 0.5:
        chosen = best
    else:
        chosen = rng.choice(kept)
    return str(chosen["source"]), float(chosen["fitness"]), island


def other_views(island: int, islands: list[list[dict]], rng: random.Random) -> tuple[str, str]:
    other = islands[1 - island]
    best = max(other, key=lambda item: float(item["fitness"]))
    random_kept = rng.choice(other)
    return str(best["source"]), str(random_kept["source"])


def extract_function(text: str) -> str:
    """Pull a score_row def out of a model reply. A fence is optional."""
    fenced = re.findall(r"```(?:python)?\s*([\s\S]*?)```", text)
    blob = fenced[-1] if fenced else text
    match = re.search(r"def score_row\s*\(.*?(?=\ndef |\Z)", blob, flags=re.S)
    if match is None:
        return blob.strip() + "\n"
    return match.group(0).strip() + "\n"


def reply_meta(response: object) -> tuple[str, str]:
    """Return the response model id and response id. Empty when the stub has none."""
    model = str(getattr(response, "model", "") or "")
    reply_id = str(getattr(response, "id", "") or "")
    return model, reply_id


def propose_source(
    parent: str,
    other_best: str,
    other_random: str,
    note: str,
    key: str,
    proposer: Callable | None = None,
) -> tuple[str, str, str]:
    """Ask grok-4.6 for one score_row. A stub proposer is for the loop test.

    The return is the extracted function, the response model id, and the
    response id. Those two ids come from the API reply, not from a constant.
    """
    if proposer is not None:
        proposed = proposer(parent, other_best, other_random, note)
        if isinstance(proposed, tuple):
            source, model, reply_id = proposed
            return str(source), str(model), str(reply_id)
        return str(proposed), "", ""
    from openai import OpenAI

    from scripts.harness_score import is_rate_limit

    client = OpenAI(api_key=key, base_url=API_BASE)
    system = (
        "You write one Python function named score_row. "
        "It takes features (a dict of eight billing fields) and tree_score "
        "(a float, the frozen shallow XGBoost score). It returns one float. "
        "Higher means more resemblance to later fraud-type exclusions. "
        "It must not say the firm committed fraud. "
        "Add one adjustment. Use at most one if, and no loop. "
        "abs(result - tree_score) must be at most 0.15 on every row. "
        "Do not import a module. Do not open a file. Do not read NPI, name, "
        "city, state, ZIP, or year. Reply with the function only."
    )
    user = (
        f"Parent function:\n{parent}\n\n"
        f"Other island best:\n{other_best}\n\n"
        f"Other island random kept function:\n{other_random}\n\n"
        f"Note from the last attempt:\n{note}\n"
    )
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
            model, reply_id = reply_meta(response)
            return extract_function(text), model, reply_id
        except Exception as exc:  # noqa: BLE001 — retry rate limits, then hand the error back
            last = exc
            if not is_rate_limit(exc):
                raise
            time.sleep(delay)
            delay = min(delay * 2.0, 60.0)
    if last is not None:
        raise last
    raise RuntimeError("proposer call failed")


def score_candidate(
    source: str,
    feature_rows: list[dict],
    tree_scores: list[float],
    labels: list[int],
) -> tuple[Callable | None, dict[str, int | float] | None, float | None, str | None, list[float] | None]:
    """Reject, then score once. An error string is the next note."""
    reason = reject_reason(source)
    if reason is not None:
        return None, None, None, reason, None
    try:
        fn = compile_score_row(source)
    except Exception as exc:  # noqa: BLE001
        return None, None, None, f"{type(exc).__name__}: {exc}", None
    try:
        scores = apply_scores(fn, feature_rows, tree_scores)
    except Exception as exc:  # noqa: BLE001
        return None, None, None, f"{type(exc).__name__}: {exc}", None
    for scored, tree_score in zip(scores, tree_scores):
        if not np.isfinite(scored):
            return None, None, None, "score is not a finite number", None
        if abs(float(scored) - float(tree_score)) > MAX_ADJUSTMENT + 1e-12:
            delta = abs(float(scored) - float(tree_score))
            return None, None, None, f"absolute adjustment {delta:.6f} exceeds 0.15", None
    stats = slice_stats(scores, labels)
    fitness = list_fitness(scores, labels)
    return fn, stats, fitness, None, scores


def run_loop(
    search_rows: list[dict],
    search_trees: list[float],
    search_labels: list[int],
    select_rows: list[dict],
    select_trees: list[float],
    select_labels: list[int],
    key: str,
    proposer: Callable | None = None,
    seed_source: str = SEED_SOURCE,
    proposal_count: int = PROPOSAL_COUNT,
    rng: random.Random | None = None,
) -> dict:
    """Score the seed on selection, then run exactly proposal_count proposals.

    A rejected proposal counts. An error becomes the next note. The loop
    does not stop because a function loses to its parent.
    """
    draw = rng if rng is not None else random.Random(SEED)
    seed_fn, seed_stats, seed_fitness, seed_error, seed_select_scores = score_candidate(
        seed_source, select_rows, select_trees, select_labels
    )
    if seed_error is not None or seed_fn is None or seed_stats is None or seed_fitness is None:
        raise RuntimeError(f"seed failed selection scoring: {seed_error}")
    search_stats = {"top1_captured": 0, "top1_fraud": len(search_labels), "top5_captured": 0, "top5_fraud": len(search_labels), "top1_slice": 0, "rows": len(search_labels), "extra_slice_rows": 0.0}
    search_fitness = 0.0
    if search_rows:
        search_scores = apply_scores(seed_fn, search_rows, search_trees)
        search_stats = slice_stats(search_scores, search_labels)
        search_fitness = list_fitness(search_scores, search_labels)
    seed_missed = missed_rows(seed_select_scores or [], select_labels, select_rows)
    seed_record = {
        "source": seed_source,
        "fitness": seed_fitness,
        "stats": seed_stats,
        "search_fitness": search_fitness,
        "search_stats": search_stats,
        "island": 0,
        "proposal": 0,
    }
    islands: list[list[dict]] = [[dict(seed_record)], [dict(seed_record)]]
    proposals: list[dict] = []
    note = (
        "Seed scored on the 2023 selection file before proposal 1. "
        + format_stats(seed_stats, seed_fitness)
        + ". Search "
        + format_stats(search_stats, search_fitness)
        + ". Missed selection fraud rows (eight fields): "
        + json.dumps(seed_missed)
        + ". No proposal has run."
    )
    print(note, flush=True)
    best = dict(seed_record)
    best["kept"] = False
    for step in range(1, proposal_count + 1):
        island = (step - 1) % ISLANDS
        parent, parent_fitness, _parent_island = parent_source(island, islands, draw)
        other_best, other_random = other_views(island, islands, draw)
        record: dict = {
            "proposal": step,
            "island": island,
            "parent_fitness": parent_fitness,
            "kept": False,
            "source": "",
            "error": "",
        }
        try:
            source, response_model, response_id = propose_source(
                parent, other_best, other_random, note, key, proposer
            )
        except Exception as exc:  # noqa: BLE001 — send the error as the next note
            record["error"] = f"{type(exc).__name__}: {exc}"
            record["response_model"] = ""
            record["response_id"] = ""
            note = f"Proposal {step} proposer error: {record['error']}"
            print(
                f"proposal={step} kept=False response_model= response_id= {note.splitlines()[0]}",
                flush=True,
            )
            print("score_row=", flush=True)
            proposals.append(record)
            continue
        record["source"] = source
        record["response_model"] = response_model
        record["response_id"] = response_id
        flat_source = " ".join(source.split())
        _fn, stats, fitness, error, select_scores = score_candidate(
            source, select_rows, select_trees, select_labels
        )
        if error is not None or stats is None or fitness is None:
            record["error"] = error or "score failed"
            note = f"Proposal {step} error: {record['error']}\nSource:\n{source}"
            print(
                f"proposal={step} kept=False response_model={response_model} "
                f"response_id={response_id} {note.splitlines()[0]}",
                flush=True,
            )
            print(f"score_row={flat_source}", flush=True)
            proposals.append(record)
            continue
        record["stats"] = stats
        record["fitness"] = fitness
        if should_keep(fitness, parent_fitness, stats):
            if search_rows:
                search_fn_scores = apply_scores(_fn, search_rows, search_trees)
                record["search_stats"] = slice_stats(search_fn_scores, search_labels)
                record["search_fitness"] = list_fitness(search_fn_scores, search_labels)
            else:
                record["search_stats"] = search_stats
                record["search_fitness"] = search_fitness
            record["kept"] = True
            islands[island].append(record)
            if fitness > float(best["fitness"]) or not best.get("kept"):
                best = dict(record)
            missed = missed_rows(select_scores or [], select_labels, select_rows)
            note = (
                f"Proposal {step} kept. Selection {format_stats(stats, fitness)}. "
                f"Parent fitness {parent_fitness:.4f}. "
                f"Search {format_stats(record['search_stats'], record['search_fitness'])}. "
                f"Missed fraud rows (eight fields): {json.dumps(missed)}"
            )
        else:
            missed = missed_rows(select_scores or [], select_labels, select_rows)
            note = (
                f"Proposal {step} lost to its parent. Selection {format_stats(stats, fitness)}. "
                f"Parent fitness {parent_fitness:.4f}. Not kept. "
                f"Missed selection fraud rows (eight fields): {json.dumps(missed)}"
            )
        print(
            f"proposal={step} kept={record['kept']} response_model={response_model} "
            f"response_id={response_id} {note.splitlines()[0]}",
            flush=True,
        )
        print(f"score_row={flat_source}", flush=True)
        proposals.append(record)
    if len(proposals) != proposal_count:
        raise RuntimeError(f"expected {proposal_count} proposals, recorded {len(proposals)}")
    return {
        "seed": seed_record,
        "islands": islands,
        "proposals": proposals,
        "best": best,
        "note": note,
    }


def confirmation_frame() -> pd.DataFrame:
    """Every 2024 fraud row plus 5 clean rows per fraud row, seed 1."""
    return sample_years(
        (CONFIRM_YEAR,),
        fraud_cap=None,
        clean_per=CONFIRM_CLEAN_PER,
        seed=SEED,
    )


def render_note(
    loop: dict,
    confirm_stats: dict[str, int | float],
    xgb_stats: dict[str, int | float],
    beat: bool,
) -> str:
    """Caveat first, then the three required lines. MAP-Elites skip is recorded."""
    seed = loop["seed"]
    kept = [item for item in loop["proposals"] if item.get("kept")]
    models = [str(item.get("response_model") or "") for item in loop["proposals"]]
    reply_ids = [str(item.get("response_id") or "") for item in loop["proposals"]]
    seen_models = [model for model in models if model]
    lines = [
        "RankEvolve-style scorer search. The function itself is the scorer.",
        f"proposer={PROPOSER_MODEL}",
        f"response_model={seen_models[0] if seen_models else ''}",
        "response_ids=" + ",".join(reply_ids),
        f"reasoning_effort={REASONING_EFFORT}",
        f"api_base={API_BASE}",
        "islands=2",
        f"proposals={len(loop['proposals'])}",
        "Parent sampling: half the time the island's best, half a random kept function. "
        "The proposer also sees the other island's best and one random kept function.",
        "The paper's MAP-Elites grid and island migration were skipped. "
        "Twenty proposals do not fill a 12 by 12 grid.",
        f"selection_seed_top1={int(seed['stats']['top1_captured'])}/{int(seed['stats']['top1_fraud'])}",
        f"selection_seed_top1_slice={int(seed['stats']['top1_slice'])}/{int(seed['stats']['rows'])}",
        f"selection_seed_fitness={float(seed['fitness']):.4f}",
        f"kept_count={len(kept)}",
        CAVEAT,
        "Confirmation is a 2024 subsample: every fraud row and "
        f"{CONFIRM_CLEAN_PER} clean rows per fraud row, seed {SEED}. "
        "It is not the full 1.21 million-row year.",
        f"confirm_top1={int(confirm_stats['top1_captured'])}/{int(confirm_stats['top1_fraud'])}",
        f"same_rows_xgboost_top1={int(xgb_stats['top1_captured'])}/{int(xgb_stats['top1_fraud'])}",
        f"beats_xgboost_on_same_rows={beat}",
        "A high score means resemblance to later fraud-type exclusions. "
        "It is not a finding that the firm committed fraud.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--loop-only" in args:
        return 0
    key = require_key()
    if "--key-present" in args:
        print("true")
        return 0
    print("loading 2023 selection file", flush=True)
    selection = sample_years((SELECTION_YEAR,), fraud_cap=None, clean_per=CLEAN_PER_FRAUD, seed=SEED)
    print(
        f"selection_rows={len(selection)} selection_fraud={int((selection['label'] == 1).sum())}",
        flush=True,
    )
    print("loading 2019-2022 search file", flush=True)
    search = sample_years(SEARCH_YEARS, fraud_cap=None, clean_per=CLEAN_PER_FRAUD, seed=SEED)
    print(
        f"search_rows={len(search)} search_fraud={int((search['label'] == 1).sum())}",
        flush=True,
    )
    if (search["Year"] == str(CONFIRM_YEAR)).any() or (selection["Year"] == str(CONFIRM_YEAR)).any():
        raise SystemExit("2024 entered the search")
    if set(search["NPI"]).intersection(DEMO_NPIS) or set(selection["NPI"]).intersection(DEMO_NPIS):
        raise SystemExit("demo NPI entered the search")
    search_rows = feature_dicts(search)
    select_rows = feature_dicts(selection)
    search_labels = [int(value) for value in search["label"].tolist()]
    select_labels = [int(value) for value in selection["label"].tolist()]
    search_trees = tree_scores_for(search)
    select_trees = tree_scores_for(selection)
    print("scoring frozen tree", flush=True)
    loop = run_loop(
        search_rows,
        search_trees,
        search_labels,
        select_rows,
        select_trees,
        select_labels,
        key,
    )
    write_score(str(loop["best"]["source"]), key)
    confirm = confirmation_frame()
    confirm_rows = feature_dicts(confirm)
    confirm_labels = [int(value) for value in confirm["label"].tolist()]
    confirm_trees = tree_scores_for(confirm)
    winner = compile_score_row(str(loop["best"]["source"]))
    winner_scores = apply_scores(winner, confirm_rows, confirm_trees)
    confirm_stats = slice_stats(winner_scores, confirm_labels)
    xgb_stats = slice_stats(confirm_trees, confirm_labels)
    beat = beats_xgboost(confirm_stats, xgb_stats)
    write_note(render_note(loop, confirm_stats, xgb_stats, beat), key)
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

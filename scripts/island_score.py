"""Score island harnesses against the saved 22/48 rank.

The parent owns the count. An island writes harness/islands/NN/score_rows.py
and nothing else. This script freezes paper_score, secondary_score, and
zero_cutoff from models/candidates/22.joblib, then calls score_rows.
It does not fit a forest.

The seed gate scores the seed file on the full 2024 paper year before any
other island runs. The saved rank is 22/48. A different numerator means the
frozen fields do not match that file.

Every island is then scored on the full 2024 year. The 2023 sample tied
every earlier edit, so it is no longer a keep gate. The stop line is 30/48.

A high score means the billing profile resembles providers later excluded
for a fraud-type reason. This is not a finding that the firm committed fraud.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Callable

import joblib
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.harness_score import CAVEAT  # noqa: E402
from scripts.join_labels import DEMO_NPIS, earliest_exclusion_years  # noqa: E402
from scripts.paper_forest import label_for_row, load_year, score_year  # noqa: E402
from scripts.rank_evolve import slice_stats  # noqa: E402
from scripts.train import (  # noqa: E402
    FEATURE_COLUMNS,
    LEIE_PATH,
    ROLLED_DIR,
    SEED,
    feature_frame,
    top_slice_share,
    training_categories,
)

SELECTION_YEAR = 2023
CONFIRM_YEAR = 2024
CLEAN_PER_FRAUD = 9
CURRENT_BEST = 22
STOP_AT = 30
MAX_SLICE_SHARE = 0.02
VOTE_STEP = 0.01
ZERO_PERCENTILE = 99
NOTE_PATH = REPO_ROOT / "models" / "island_note.txt"
DB_PATH = REPO_ROOT / "models" / "island_db.json"
OPTIMIZED_PATH = REPO_ROOT / "models" / "candidates" / "22.joblib"
PAPER_DIR = REPO_ROOT / "data" / "paper_rolled"
ISLAND_ROOT = REPO_ROOT / "harness" / "islands"
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
BILLING_FIELDS = FEATURE_COLUMNS
FROZEN_FIELDS = ("paper_score", "secondary_score", "tree_score", "zero_cutoff", "vote_step")


def island_path(island_id: int) -> Path:
    return ISLAND_ROOT / f"{island_id:02d}" / "score_rows.py"


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


def run_harness(fn: Callable, rows: list[dict]) -> list[float]:
    scored = fn(rows)
    if not isinstance(scored, list) or len(scored) != len(rows):
        raise ValueError("score_rows must return one float per row")
    out = [float(value) for value in scored]
    if not all(np.isfinite(value) for value in out):
        raise ValueError("score is not a finite number")
    return out


def load_optimized():
    return joblib.load(OPTIMIZED_PATH)


def paper_year(year: int) -> pd.DataFrame:
    return load_year(PAPER_DIR / f"{year}.csv")


def forest_pair(frame: pd.DataFrame, payload) -> tuple[np.ndarray, np.ndarray]:
    """Page-forest score and the 2013-2022 forest score. Does not fit."""
    primary = score_year(payload.primary_model, list(payload.primary_columns), frame, chunk=40_000)
    secondary = score_year(
        payload.secondary_model, list(payload.secondary_columns), frame, chunk=40_000
    )
    return primary, secondary


def zero_cutoff_value(primary: np.ndarray, secondary: np.ndarray, payload) -> float:
    """The cutoff zero_tie_break would use, or inf when that promotion is dropped."""
    from scripts.optimized_rank import zero_tie_break

    primary = np.asarray(primary, dtype=float)
    secondary = np.asarray(secondary, dtype=float)
    ranked = zero_tie_break(
        primary,
        secondary,
        vote_step=float(payload.vote_step),
        percentile=float(payload.zero_percentile),
    )
    zeros = primary == 0
    if not np.any(zeros) or not np.any(ranked[zeros] > 0):
        return float("inf")
    promoted = secondary[zeros & (ranked > 0)]
    return float(np.min(promoted))


def year_labels(frame: pd.DataFrame) -> list[int]:
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    labels: list[int] = []
    for npi, year in zip(frame["npi"].astype(str), frame["year"].astype(str)):
        billing = int(year) if str(year).strip().isdigit() else 0
        labels.append(label_for_row(billing, npi.strip(), exclusion_years))
    return labels


def billing_lookup(year: int) -> dict[str, dict]:
    """Eight billing fields by NPI. Identifiers stay in this map's keys only."""
    frame = pd.read_csv(
        ROLLED_DIR / f"{year}.csv",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
        usecols=["NPI", *FEATURE_COLUMNS],
    )
    lookup: dict[str, dict] = {}
    for row in frame.itertuples(index=False):
        npi = str(row[0]).strip()
        if npi in lookup:
            continue
        payload: dict = {}
        for name, value in zip(FEATURE_COLUMNS, row[1:]):
            text = "" if value is None else str(value).strip()
            if name == "Specialty":
                payload[name] = text
            else:
                try:
                    payload[name] = float(text) if text != "" else None
                except ValueError:
                    payload[name] = None
        lookup[npi] = payload
    return lookup


def tree_lookup(year: int) -> dict[str, float]:
    """Frozen shallow-tree probability by NPI. Does not fit."""
    from xgboost import XGBClassifier

    frame = pd.read_csv(
        ROLLED_DIR / f"{year}.csv",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
        usecols=["NPI", *FEATURE_COLUMNS],
    )
    frame = frame.drop_duplicates("NPI")
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
    scores = booster.predict_proba(features)[:, 1]
    return {
        str(npi).strip(): float(score)
        for npi, score in zip(frame["NPI"].astype(str), scores)
    }


def build_rows(
    frame: pd.DataFrame,
    primary: np.ndarray,
    secondary: np.ndarray,
    cutoff: float,
    vote_step: float,
    billing: dict[str, dict] | None = None,
    trees: dict[str, float] | None = None,
) -> list[dict]:
    """Island rows. NPI is used to attach fields, then dropped."""
    rows: list[dict] = []
    empty = {name: None for name in FEATURE_COLUMNS}
    empty["Specialty"] = ""
    for npi, paper, second in zip(frame["npi"].astype(str), primary, secondary):
        key = npi.strip()
        row = dict(billing.get(key, empty) if billing else empty)
        row["paper_score"] = float(paper)
        row["secondary_score"] = float(second)
        row["tree_score"] = float(trees.get(key, 0.0)) if trees else 0.0
        row["zero_cutoff"] = float(cutoff)
        row["vote_step"] = float(vote_step)
        rows.append(row)
    return rows


def score_source(
    source: str,
    rows: list[dict],
    labels: list[int],
) -> tuple[dict | None, str | None, list[float] | None]:
    reason = reject_reason(source)
    if reason is not None:
        return None, reason, None
    try:
        fn = compile_score_rows(source)
        scores = run_harness(fn, rows)
    except Exception as exc:  # noqa: BLE001 — the error is the next note
        return None, f"{type(exc).__name__}: {exc}", None
    return slice_stats(scores, labels), None, scores


def zero_mass_holds(scores: list[float]) -> bool:
    if not scores:
        return False
    return float(np.percentile(np.asarray(scores, dtype=float), 95)) <= 0.0


def slice_within_cap(stats: dict) -> bool:
    rows = int(stats["rows"])
    if rows == 0:
        return False
    return int(stats["top1_slice"]) <= rows * MAX_SLICE_SHARE


def should_keep(child_stats: dict, parent_captured: int, child_scores: list[float]) -> bool:
    return (
        int(child_stats["top1_captured"]) > int(parent_captured)
        and slice_within_cap(child_stats)
        and zero_mass_holds(child_scores)
    )


def write_note(lines: list[str]) -> None:
    text = "\n".join(lines).rstrip() + "\n"
    NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTE_PATH.write_text(text, encoding="utf-8")
    print(text, flush=True)


def load_db() -> dict:
    if not DB_PATH.exists():
        return {"islands": {}, "best_confirm_top1": 0, "stalls": 0}
    return json.loads(DB_PATH.read_text(encoding="utf-8"))


def save_db(db: dict) -> None:
    DB_PATH.write_text(json.dumps(db, indent=2), encoding="utf-8")


def seed_gate() -> dict:
    """Score island 1 on the full 2024 paper year. Stop unless the count is 20/48."""
    payload = load_optimized()
    frame = paper_year(CONFIRM_YEAR)
    print(f"seed gate year={CONFIRM_YEAR} rows={len(frame)}", flush=True)
    primary, secondary = forest_pair(frame, payload)
    from scripts.optimized_rank import zero_tie_break

    ranked = zero_tie_break(
        primary,
        secondary,
        vote_step=float(payload.vote_step),
        percentile=float(payload.zero_percentile),
    )
    labels = year_labels(frame)
    direct_top1, fraud, _share = top_slice_share(ranked.tolist(), labels, 99)
    direct_top5, _, _top5_share = top_slice_share(ranked.tolist(), labels, 95)
    print(f"saved rank on this year top1={direct_top1}/{fraud} top5={direct_top5}/{fraud}", flush=True)
    cutoff = zero_cutoff_value(primary, secondary, payload)
    rows = build_rows(frame, primary, secondary, cutoff, float(payload.vote_step))
    source = island_path(1).with_name("seed_score_rows.py").read_text(encoding="utf-8")
    stats, error, scores = score_source(source, rows, labels)
    if error is not None or stats is None or scores is None:
        raise SystemExit(f"seed harness failed: {error}")
    if not np.allclose(scores, ranked, rtol=0.0, atol=1e-12):
        raise SystemExit("island 1 does not match zero_tie_break")
    captured = int(stats["top1_captured"])
    top5 = int(stats["top5_captured"])
    lines = [
        CAVEAT,
        "Seed gate. Island 1 scored on the full 2024 paper year before generation 1.",
        f"rows={int(stats['rows'])}",
        f"top1_slice={int(stats['top1_slice'])}",
        f"confirm_top1={captured}/{int(stats['top1_fraud'])}",
        f"confirm_top5={top5}/{int(stats['top5_fraud'])}",
        f"saved_best={CURRENT_BEST}/48",
        f"stop_at={STOP_AT}/48",
        f"beats_current_best={str(captured > CURRENT_BEST).lower()}",
        "A high score means resemblance to later fraud-type exclusions. "
        "It is not a finding that the firm committed fraud.",
    ]
    write_note(lines)
    if captured != CURRENT_BEST or fraud != 48:
        raise SystemExit(f"seed gate expected {CURRENT_BEST}/48 and scored {captured}/{fraud}")
    if not zero_mass_holds(scores):
        raise SystemExit("seed gate moved the 95th percentile off the zero step")
    db = load_db()
    db["seed_confirm_top1"] = captured
    db["best_confirm_top1"] = max(int(db.get("best_confirm_top1") or 0), captured)
    db["stop_at"] = STOP_AT
    seed_copy = island_path(1).with_name("seed_score_rows.py")
    seed_copy.write_text(source, encoding="utf-8")
    db["seed_source"] = "harness/islands/01/seed_score_rows.py"
    db["islands"] = {
        "01": {
            "confirm_top1": captured,
            "source": "harness/islands/01/score_rows.py",
        }
    }
    save_db(db)
    print(f"seed gate passed {captured}/48", flush=True)
    return stats


def selection_bundle(payload) -> tuple[list[dict], list[int]]:
    """2023 sample: every fraud row, 9 clean per fraud, seed 1, demo NPIs dropped."""
    frame = paper_year(SELECTION_YEAR)
    labels = np.asarray(year_labels(frame), dtype=int)
    npi = frame["npi"].astype(str).str.strip()
    keep = ~npi.isin(DEMO_NPIS)
    frame = frame.loc[keep].reset_index(drop=True)
    labels = labels[keep.to_numpy()]
    fraud_at = np.flatnonzero(labels == 1)
    clean_at = np.flatnonzero(labels == 0)
    rng = np.random.default_rng(SEED)
    take_clean = CLEAN_PER_FRAUD * len(fraud_at)
    if len(clean_at) > take_clean:
        drawn = rng.choice(len(clean_at), size=take_clean, replace=False)
        clean_at = clean_at[drawn]
    chosen = np.sort(np.concatenate([fraud_at, clean_at]))
    frame = frame.iloc[chosen].reset_index(drop=True)
    labels = labels[chosen]
    print(f"selection rows={len(frame)} fraud={int(labels.sum())}", flush=True)
    primary, secondary = forest_pair(frame, payload)
    cutoff = zero_cutoff_value(primary, secondary, payload)
    billing = billing_lookup(SELECTION_YEAR)
    trees = tree_lookup(SELECTION_YEAR)
    rows = build_rows(
        frame,
        primary,
        secondary,
        cutoff,
        float(payload.vote_step),
        billing,
        trees,
    )
    return rows, [int(value) for value in labels]


def kept_path(island_id: int) -> Path:
    return island_path(island_id).with_name("kept_score_rows.py")


def restore_rejected(island_id: int) -> None:
    """Put the last kept file back so the next generation does not edit a reject."""
    path = island_path(island_id)
    kept = kept_path(island_id)
    seed = island_path(1).with_name("seed_score_rows.py")
    if kept.exists():
        path.write_text(kept.read_text(encoding="utf-8"), encoding="utf-8")
    elif seed.exists():
        path.write_text(seed.read_text(encoding="utf-8"), encoding="utf-8")


def snapshot_kept(island_id: int, source: str) -> None:
    kept_path(island_id).write_text(source, encoding="utf-8")


def read_island(island_id: int) -> str | None:
    path = island_path(island_id)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def review_rejects(island_id: int) -> str | None:
    """A missing critic file is a reject. The three critic files must say pass."""
    for critic in (16, 17, 18):
        path = ISLAND_ROOT / "reviews" / f"{critic}-{island_id:02d}.json"
        if not path.exists():
            return f"missing review {critic}"
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("verdict") != "pass":
            return f"review {critic} rejected"
    return None


def score_generation() -> None:
    """Score islands 1-15 on the full 2024 year. No 2023 keep gate.

    The seed gate must already have written models/island_db.json. Forests
    are scored once. Each island only reorders those frozen scores.
    """
    db = load_db()
    if int(db.get("seed_confirm_top1") or 0) != CURRENT_BEST:
        raise SystemExit(f"seed gate has not passed {CURRENT_BEST}/48")
    if int(db.get("best_confirm_top1") or 0) >= STOP_AT:
        print(f"already at {db['best_confirm_top1']}/48", flush=True)
        return
    payload = load_optimized()
    frame = paper_year(CONFIRM_YEAR)
    primary, secondary = forest_pair(frame, payload)
    cutoff = zero_cutoff_value(primary, secondary, payload)
    rows = build_rows(frame, primary, secondary, cutoff, float(payload.vote_step))
    labels = year_labels(frame)
    del frame, primary, secondary
    best = int(db.get("best_confirm_top1") or CURRENT_BEST)
    gained = False
    generation: list[dict] = []
    for island_id in range(1, 16):
        source = read_island(island_id)
        record = {"island": island_id, "kept": False}
        if source is None:
            record["error"] = "missing score_rows.py"
            generation.append(record)
            continue
        if island_id != 1:
            blocked = review_rejects(island_id)
            if blocked is not None:
                record["error"] = blocked
                print(f"island {island_id:02d} {blocked}", flush=True)
                restore_rejected(island_id)
                generation.append(record)
                continue
        stats, error, scores = score_source(source, rows, labels)
        if error is not None or stats is None or scores is None:
            record["error"] = error
            print(f"island {island_id:02d} rejected {error}", flush=True)
            restore_rejected(island_id)
            generation.append(record)
            continue
        captured = int(stats["top1_captured"])
        record["confirm_top1"] = captured
        record["top1_slice"] = int(stats["top1_slice"])
        if captured <= best:
            record["error"] = "2024 count did not rise"
            print(f"island {island_id:02d} confirm {captured}/48 not above {best}", flush=True)
            restore_rejected(island_id)
            generation.append(record)
            continue
        record["kept"] = True
        gained = True
        snapshot_kept(island_id, source)
        best = captured
        db["best_confirm_top1"] = captured
        db["best_island"] = f"{island_id:02d}"
        db.setdefault("islands", {})[f"{island_id:02d}"] = {
            "confirm_top1": captured,
            "source": f"harness/islands/{island_id:02d}/score_rows.py",
        }
        write_confirm_note(stats, island_id)
        print(f"island {island_id:02d} kept confirm {captured}/48", flush=True)
        generation.append(record)
        del scores
    db["stalls"] = 0 if gained else int(db.get("stalls") or 0) + 1
    db["last_generation"] = generation
    save_db(db)
    print(
        f"generation done best={db.get('best_confirm_top1')}/48 stalls={db.get('stalls')}",
        flush=True,
    )


def confirm_source(source: str) -> tuple[dict | None, str | None, list[float] | None]:
    payload = load_optimized()
    frame = paper_year(CONFIRM_YEAR)
    primary, secondary = forest_pair(frame, payload)
    cutoff = zero_cutoff_value(primary, secondary, payload)
    rows = build_rows(frame, primary, secondary, cutoff, float(payload.vote_step))
    labels = year_labels(frame)
    return score_source(source, rows, labels)


def write_confirm_note(stats: dict, island_id: int) -> None:
    captured = int(stats["top1_captured"])
    lines = [
        CAVEAT,
        f"Kept island {island_id:02d} on a 2023 rise, then scored the full 2024 year once.",
        f"rows={int(stats['rows'])}",
        f"top1_slice={int(stats['top1_slice'])}",
        f"confirm_top1={captured}/{int(stats['top1_fraud'])}",
        f"confirm_top5={int(stats['top5_captured'])}/{int(stats['top5_fraud'])}",
        f"saved_best={CURRENT_BEST}/48",
        f"stop_at={STOP_AT}/48",
        f"beats_current_best={str(captured > CURRENT_BEST).lower()}",
        "A high score means resemblance to later fraud-type exclusions. "
        "It is not a finding that the firm committed fraud.",
    ]
    write_note(lines)


def main(argv: list[str] | None = None) -> None:
    command = (argv or sys.argv[1:])[:1]
    if command == ["seed"]:
        seed_gate()
        return
    if command == ["generation"]:
        score_generation()
        return
    raise SystemExit("usage: python scripts/island_score.py seed|generation")


if __name__ == "__main__":
    main()

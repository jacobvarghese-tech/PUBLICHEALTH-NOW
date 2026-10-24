"""Copy the current best ranker and redraw the paper's clean sample.

The parent is models/candidates/22.joblib, the highest full-year count on
disk: 22 of 48. Each round copies that ranker's page forest and settings,
keeps every fraud row, and draws clean rows without replacement at nine
clean rows per fraud row. The paper repeats that draw because each repeat
removes a different majority-class set. The draw seed is the round number.
2023 and 2024 never enter the fit.

The stop is a 2024 top 1 percent count above 26 of 48. The paper publishes
an AUC of 0.87302, not a count out of 48. 26 of 48 is the count this loop
is told to clear. A high score means resemblance to later fraud-type
exclusions. It is not a finding that the firm committed fraud.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.harness_score import CAVEAT  # noqa: E402
from scripts.join_labels import DEMO_NPIS, earliest_exclusion_years  # noqa: E402
from scripts.model_islands import share  # noqa: E402
from scripts.optimized_rank import OptimizedRankModel, zero_tie_break  # noqa: E402
from scripts.paper_forest import (  # noqa: E402
    LEIE_PATH,
    design_matrix,
    label_for_row,
    load_year,
    score_year,
    training_columns,
)
from scripts.paper_forest_rus import undersample  # noqa: E402

PAPER_DIR = REPO_ROOT / "data" / "paper_rolled"
PARTS_DIR = REPO_ROOT / "data" / "paper_rus_parts"
PARENT_PATH = REPO_ROOT / "models" / "candidates" / "22.joblib"
COPY_DIR = REPO_ROOT / "models" / "rus_loop"
PARENT_COPY = COPY_DIR / "parent.joblib"
NOTE_PATH = COPY_DIR / "note.txt"
DB_PATH = COPY_DIR / "db.json"
CANDIDATE_DIR = COPY_DIR / "candidates"
SELECT_YEAR = 2023
CONFIRM_YEAR = 2024
CLEAN_PER_FRAUD = 9
STOP_ABOVE = 26
MAX_ROUNDS = 10
PAPER_AUC = 0.87302
RESEMBLANCE = (
    "A high score means resemblance to later fraud-type exclusions. "
    "It is not a finding that the firm committed fraud."
)


def copy_parent(source: Path = PARENT_PATH, dest: Path = PARENT_COPY) -> Path:
    """Copy the current best ranker before any draw. The source stays put."""
    if not source.is_file():
        raise FileNotFoundError(f"parent ranker missing: {source}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return dest


def load_parent(path: Path = PARENT_COPY):
    payload = joblib.load(path)
    if not isinstance(payload, OptimizedRankModel):
        raise TypeError(f"{path} is not an OptimizedRankModel")
    years = tuple(int(year) for year in payload.fit_years)
    if any(year < 2013 or year > 2022 for year in years):
        raise ValueError(f"parent fit years must stay inside 2013-2022: {years}")
    return payload


def _part_rows(parts_dir: Path, year: int) -> int:
    path = parts_dir / f"{year}_labels.csv"
    with path.open(encoding="utf-8") as handle:
        return sum(1 for _ in handle) - 1


def draw_indexes(
    parts_dir: Path,
    years: tuple[int, ...],
    round_seed: int,
) -> tuple[dict[int, np.ndarray], int, int]:
    """One pooled draw. Every fraud row stays. Clean rows are drawn once.

    The paper's sampler is random undersampling without replacement. Each
    repeat uses a different seed so the discarded clean rows change.
    """
    pieces = []
    for year in years:
        path = parts_dir / f"{year}_labels.csv"
        if not path.is_file():
            raise FileNotFoundError(f"label part missing for year {year}: {path}")
        labels = pd.read_csv(path, usecols=["fraud"], dtype={"fraud": int})
        pieces.append(
            pd.DataFrame(
                {
                    "year": int(year),
                    "row": np.arange(len(labels), dtype=int),
                    "fraud": labels["fraud"].to_numpy(dtype=int),
                }
            )
        )
        del labels
    index_frame = pd.concat(pieces, ignore_index=True)
    del pieces
    sampled, fraud_count, keep_clean = undersample(
        index_frame,
        clean_per_fraud=CLEAN_PER_FRAUD,
        random_state=int(round_seed),
    )
    del index_frame
    chosen: dict[int, np.ndarray] = {}
    for year in years:
        rows = sampled.loc[sampled["year"] == int(year), "row"].to_numpy(dtype=int)
        chosen[int(year)] = np.sort(rows)
    return chosen, int(fraud_count), int(keep_clean)


def fit_copy(payload, indexes: dict[int, np.ndarray], round_seed: int):
    """Fit one forest on the copied settings and this round's draw."""
    years = tuple(int(year) for year in payload.fit_years)
    columns = training_columns(PAPER_DIR, years)
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    matrices = []
    label_parts = []
    fraud_rows = 0
    clean_rows = 0
    for year in years:
        frame = load_year(PAPER_DIR / f"{year}.csv")
        chosen = indexes[year]
        part_rows = _part_rows(PARTS_DIR, year)
        if part_rows != len(frame):
            raise ValueError(
                f"year {year} label part has {part_rows} rows "
                f"and the roll has {len(frame)} rows"
            )
        npi = frame["npi"].astype(str).str.strip()
        eligible = ~npi.isin(DEMO_NPIS)
        # chosen holds label-part row numbers. Drop a demo NPI by that number.
        chosen = chosen[eligible.to_numpy()[chosen]]
        kept = frame.iloc[chosen]
        matrix, _ = design_matrix(kept, columns)
        year_labels = np.array(
            [
                label_for_row(year, one, exclusion_years)
                for one in kept["npi"].astype(str)
            ],
            dtype=np.int8,
        )
        matrices.append(matrix.astype(np.float32, copy=False))
        label_parts.append(year_labels)
        fraud_rows += int(year_labels.sum())
        clean_rows += int(len(year_labels) - int(year_labels.sum()))
        print(
            f"round={round_seed} year={year} kept={len(chosen)} "
            f"fraud={int(year_labels.sum())}",
            flush=True,
        )
        del frame, kept, matrix, year_labels
    sample = np.vstack(matrices)
    labels = np.concatenate(label_parts)
    weight = payload.class_weight
    if weight in ("", "none", None):
        weight = None
    model = RandomForestClassifier(
        n_estimators=int(payload.n_estimators),
        max_depth=int(payload.max_depth) or None,
        min_samples_leaf=int(payload.min_samples_leaf),
        class_weight=weight,
        random_state=0,
        n_jobs=2,
    )
    model.fit(sample, labels)
    return model, columns, fraud_rows, clean_rows


def rank_year(payload, year: int, secondary, columns: list[str]):
    frame = load_year(PAPER_DIR / f"{year}.csv")
    primary = score_year(
        payload.primary_model,
        list(payload.primary_columns),
        frame,
        chunk=40_000,
    )
    second = score_year(secondary, columns, frame, chunk=40_000)
    ranked = zero_tie_break(
        primary,
        second,
        vote_step=float(payload.vote_step),
        percentile=float(payload.zero_percentile),
    )
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    labels = [
        label_for_row(year, npi, exclusion_years)
        for npi in frame["npi"].astype(str)
    ]
    return ranked, labels


def write_note(lines: list[str]) -> None:
    text = "\n".join(lines).rstrip() + "\n"
    NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTE_PATH.write_text(text, encoding="utf-8")
    print(text, flush=True)


def load_db() -> dict:
    if not DB_PATH.exists():
        return {"rounds": [], "best_confirm_top1": 22, "stop_above": STOP_ABOVE}
    return json.loads(DB_PATH.read_text(encoding="utf-8"))


def save_db(db: dict) -> None:
    DB_PATH.write_text(json.dumps(db, indent=2) + "\n", encoding="utf-8")


def run_round(payload, round_seed: int, db: dict) -> int:
    years = tuple(int(year) for year in payload.fit_years)
    indexes, fraud_count, keep_clean = draw_indexes(PARTS_DIR, years, round_seed)
    print(
        f"round={round_seed} draw fraud={fraud_count} clean={keep_clean} "
        f"ratio=90:10",
        flush=True,
    )
    secondary, columns, fraud_rows, clean_rows = fit_copy(payload, indexes, round_seed)
    select_scores, select_labels = rank_year(payload, SELECT_YEAR, secondary, columns)
    select_top1, select_fraud = share(select_scores, select_labels, 99)
    select_top5, _select_top5_fraud = share(select_scores, select_labels, 95)
    print(
        f"round={round_seed} 2023 top1={select_top1}/{select_fraud} "
        f"top5={select_top5}/{select_fraud}",
        flush=True,
    )
    confirm_scores, confirm_labels = rank_year(payload, CONFIRM_YEAR, secondary, columns)
    top1, fraud = share(confirm_scores, confirm_labels, 99)
    top5, _top5_fraud = share(confirm_scores, confirm_labels, 95)
    saved = int(db.get("best_confirm_top1") or 22)
    beats = top1 > saved
    clears = top1 > STOP_ABOVE
    record = {
        "round": int(round_seed),
        "seed": int(round_seed),
        "fraud_rows": fraud_rows,
        "clean_rows": clean_rows,
        "select_top1": select_top1,
        "select_top5": select_top5,
        "confirm_top1": top1,
        "confirm_top5": top5,
        "beats_parent": beats,
        "clears_stop": clears,
    }
    if beats or clears:
        candidate = OptimizedRankModel(
            payload.primary_model,
            list(payload.primary_columns),
            secondary,
            columns,
            list(payload.fit_years),
            int(payload.n_estimators),
            int(payload.max_depth),
            int(payload.min_samples_leaf),
            payload.class_weight or "none",
            CLEAN_PER_FRAUD,
            fraud_rows,
            clean_rows,
        )
        CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
        out = CANDIDATE_DIR / f"round_{round_seed:02d}.joblib"
        joblib.dump(candidate, out)
        record["path"] = str(out.relative_to(REPO_ROOT)).replace("\\", "/")
        if beats:
            db["best_confirm_top1"] = top1
            db["best_round"] = int(round_seed)
            db["best_path"] = record["path"]
    db.setdefault("rounds", []).append(record)
    save_db(db)
    write_note(
        [
            CAVEAT,
            f"Parent copy: {PARENT_COPY.relative_to(REPO_ROOT).as_posix()}",
            "Paper sampler: random undersampling, every fraud row kept, "
            "clean rows drawn without replacement at 9 per fraud row.",
            f"Paper published score: RF100 90:10 AUC {PAPER_AUC}.",
            f"Stop when the 2024 top 1 percent count is above {STOP_ABOVE}/48.",
            f"round={round_seed} seed={round_seed}",
            f"confirm_top1={top1}/{fraud}",
            f"confirm_top5={top5}/{fraud}",
            f"select_top1={select_top1}/{select_fraud}",
            f"saved_best={db.get('best_confirm_top1')}/48",
            f"clears_stop={str(clears).lower()}",
            RESEMBLANCE,
        ]
    )
    print(f"round={round_seed} confirm {top1}/48", flush=True)
    return top1


def run_loop(max_rounds: int = MAX_ROUNDS) -> int:
    copy_parent()
    payload = load_parent()
    db = load_db()
    db["paper_auc"] = PAPER_AUC
    db["stop_above"] = STOP_ABOVE
    db["parent"] = "models/candidates/22.joblib"
    db["parent_copy"] = "models/rus_loop/parent.joblib"
    save_db(db)
    best = int(db.get("best_confirm_top1") or 22)
    done = {int(row["round"]) for row in db.get("rounds") or []}
    for round_seed in range(1, max_rounds + 1):
        if best > STOP_ABOVE:
            print(f"stop best={best}/48 above {STOP_ABOVE}/48", flush=True)
            return best
        if round_seed in done:
            continue
        top1 = run_round(payload, round_seed, db)
        best = max(best, top1)
    print(f"finished {max_rounds} rounds best={best}/48", flush=True)
    return best


def main(argv: list[str] | None = None) -> None:
    args = argv if argv is not None else sys.argv[1:]
    if args and args[0] == "loop":
        rounds = int(args[1]) if len(args) > 1 else MAX_ROUNDS
        run_loop(rounds)
        return
    if len(args) == 2 and args[0] == "round":
        copy_parent()
        payload = load_parent()
        run_round(payload, int(args[1]), load_db())
        return
    raise SystemExit(
        "usage: python scripts/rus_loop.py loop [rounds] | python scripts/rus_loop.py round N"
    )


if __name__ == "__main__":
    main()

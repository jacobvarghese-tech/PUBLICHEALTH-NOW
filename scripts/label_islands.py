"""Refit the second forest on one label spec. The page forest stays frozen.

The training label comes from the spec. 2023 is graded with that same label.
2024 is scored only after a keep, and its numerator stays on the app rule in
data/training/UPDATED.csv. models/optimized_model.joblib is not replaced.

A high score means resemblance to later fraud-type exclusions. It is not a
finding that the firm committed fraud.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.join_labels import DEMO_NPIS, is_ten_digit_npi  # noqa: E402
from scripts.model_islands import sample_indexes  # noqa: E402
from scripts.optimized_rank import OptimizedRankModel, zero_tie_break  # noqa: E402
from scripts.paper_fit import add_years, end_year, parse_date  # noqa: E402
from scripts.paper_forest import (  # noqa: E402
    LEIE_PATH,
    design_matrix,
    load_year,
    score_year,
    training_columns,
)
from scripts.train import top_slice_share  # noqa: E402

PAPER_DIR = REPO_ROOT / "data" / "paper_rolled"
OPTIMIZED_PATH = REPO_ROOT / "models" / "optimized_model.joblib"
CANDIDATE_DIR = REPO_ROOT / "models" / "candidates"
FOREST_SPEC_PATH = REPO_ROOT / "models" / "specs" / "22.json"
NOTE_PATH = REPO_ROOT / "models" / "label_island_note.txt"
DB_PATH = REPO_ROOT / "models" / "label_island_db.json"
SELECT_YEAR = 2023
CONFIRM_YEAR = 2024
APP_CODES = ("1128a1", "1128a3", "1128b6", "1128b7")
TABLE2_LENGTHS = {
    "1128a1": 5,
    "1128a2": 5,
    "1128a3": 5,
    "1128b4": 5,
    "1128c3gi": 10,
}
INDEFINITE_CODE = "1128c3gii"
ALLOWED_LEIE = {
    "data/training/UPDATED.csv": REPO_ROOT / "data" / "training" / "UPDATED.csv",
    "data/paper_rolled/leie_20170627.csv": PAPER_DIR / "leie_20170627.csv",
}
CAVEAT_2024 = (
    "2024 has 48 fraud rows under the app rule, below the published "
    "external-validation floor of 100 events, so shares are not a precise estimate."
)
RESEMBLANCE = (
    "A high score means resemblance to later fraud-type exclusions. "
    "It is not a finding that the firm committed fraud."
)
PAPER_RULE_UNCOUNTED = "different class, uncounted, missing token 1128c3gi"
MISSING_PAPER_TOKEN = "1128c3gi"


def parse_leie_date(value) -> tuple[int, int] | None:
    """Year and month of an eight-digit YYYYMMDD date, or None when blank.

    "0", "00000000", "", and any value that is not eight digits are blank.
    A zero date is not a real date. This is the blank check paper_fit.parse_date
    misses for "0", which is not eight digits and must not be padded.
    """
    text = "" if value is None else str(value).strip().strip('"')
    if text in ("", "0", "00000000") or len(text) != 8 or not text.isdigit():
        return None
    parsed = parse_date(text)
    if parsed is None:
        return None
    return parsed.year, parsed.month


def _cell(row: dict, *names: str) -> str:
    for name in names:
        if name in row and row[name] is not None:
            return str(row[name]).strip().strip('"')
    folded = {str(key).lower(): value for key, value in row.items()}
    for name in names:
        value = folded.get(name.lower())
        if value is not None:
            return str(value).strip().strip('"')
    return ""


def _npi(row: dict) -> str:
    return _cell(row, "NPI", "npi")


def _year(row: dict) -> int | None:
    text = _cell(row, "year", "Year")
    if not text.isdigit():
        return None
    return int(text)


def _codes(spec: dict) -> list[str]:
    return [str(code).strip() for code in spec.get("codes") or []]


def _sentence(spec: dict) -> str:
    return str(spec.get("train_positive") or "")


def label_function_name(spec: dict) -> str:
    """Short name of the sentence the spec trains on. Structured phrases win."""
    if str(spec.get("date_rule") or "") == "paper_end":
        return "paper_end"
    text = _sentence(spec).lower()
    if "exactly one qualifying" in text or "two or more qualifying" in text:
        return "exactly_one_qualifying"
    if "latest qualifying" in text:
        return "latest_exclusion"
    if "at least two years after" in text:
        return "gap_two_years"
    rein = "not after the year of reindate" in text or "not after reindate" in text
    waiver = "not after the year of waiverdate" in text or "not after waiverdate" in text
    if rein and waiver:
        return "both_cutoffs"
    if rein:
        return "reinstatement_cutoff"
    if waiver:
        return "waiver_cutoff"
    return "app_year_earliest"


def _qualifying(row: dict, codes: set[str]) -> bool:
    return _cell(row, "EXCLTYPE") in codes


def _exclusion_year(row: dict) -> int | None:
    parsed = parse_leie_date(_cell(row, "EXCLDATE"))
    if parsed is None:
        return None
    return parsed[0]


def _cutoff_year(row: dict, column: str) -> int | None:
    parsed = parse_leie_date(_cell(row, column))
    if parsed is None:
        return None
    return parsed[0]


def _passes_cutoffs(row: dict, billing_year: int, function: str) -> bool:
    """A year after a real cutoff date is not positive. A blank cutoff does not cut."""
    if function in ("reinstatement_cutoff", "both_cutoffs"):
        rein = _cutoff_year(row, "REINDATE")
        if rein is not None and billing_year > rein:
            return False
    if function in ("waiver_cutoff", "both_cutoffs"):
        waiver = _cutoff_year(row, "WAIVERDATE")
        if waiver is not None and billing_year > waiver:
            return False
    return True


def _paper_end_year(row: dict) -> int | None:
    """Table 2 finite length added to EXCLDATE, then the paper month/year rule.

    Indefinite 1128c3gii has no numeric length and returns None. A blank start
    date returns None. A blank waiver and a blank reinstatement do not move
    the end date. paper_fit.end_year is the only end-year rule.
    """
    code = _cell(row, "EXCLTYPE")
    if code == INDEFINITE_CODE:
        return None
    length = TABLE2_LENGTHS.get(code)
    if length is None:
        return None
    start = parse_date(_cell(row, "EXCLDATE"))
    if start is None or parse_leie_date(_cell(row, "EXCLDATE")) is None:
        return None
    return end_year(
        start,
        length,
        parse_date(_cell(row, "REINDATE")),
        parse_date(_cell(row, "WAIVERDATE")),
    )


def label_provider_years(
    leie_rows: list[dict],
    year_rows: list[dict],
    spec: dict,
) -> tuple[list[int], dict]:
    """0/1 labels aligned to year_rows, plus the small info dict.

    Pure: the rows are already in memory. Does not read a rolled CSV and
    does not fit. Demo NPIs are not labels. Blank NPI and 0000000000 do not
    join. A zero date and an 00000000 date are blank.
    """
    function = label_function_name(spec)
    codes = set(_codes(spec))
    info = {
        "indefinite_left_out": 0,
        "multi_row_left_out": 0,
        "missing_codes": [],
        "label_function": function,
    }
    grouped: dict[str, list[dict]] = {}
    for row in leie_rows:
        npi = _npi(row)
        if not is_ten_digit_npi(npi) or npi == "0000000000":
            continue
        if _cell(row, "EXCLTYPE") == INDEFINITE_CODE:
            info["indefinite_left_out"] += 1
            continue
        if not _qualifying(row, codes):
            continue
        if function == "paper_end":
            if _paper_end_year(row) is None:
                continue
        elif _exclusion_year(row) is None:
            continue
        grouped.setdefault(npi, []).append(row)

    if function == "exactly_one_qualifying":
        left_out = [npi for npi, rows in grouped.items() if len(rows) >= 2]
        info["multi_row_left_out"] = len(left_out)
        for npi in left_out:
            del grouped[npi]

    labels: list[int] = []
    for row in year_rows:
        npi = _npi(row)
        billing = _year(row)
        if npi in DEMO_NPIS or billing is None or npi not in grouped:
            labels.append(0)
            continue
        matches = grouped[npi]
        if function == "paper_end":
            ends = [year for year in (_paper_end_year(one) for one in matches) if year is not None]
            positive = any(billing < year for year in ends)
        else:
            dated = [(one, _exclusion_year(one)) for one in matches]
            dated = [(one, year) for one, year in dated if year is not None]
            if not dated:
                labels.append(0)
                continue
            if function == "latest_exclusion":
                chosen, chosen_year = max(dated, key=lambda item: item[1])
            else:
                chosen, chosen_year = min(dated, key=lambda item: item[1])
            if function == "gap_two_years":
                positive = chosen_year >= billing + 2
            else:
                positive = chosen_year > billing
            if positive and not _passes_cutoffs(chosen, billing, function):
                positive = False
        labels.append(1 if positive else 0)
    return labels, info


def app_rule_spec() -> dict:
    """The 2024 numerator. Four codes, exclusion year after the billing year."""
    return {
        "name": "app_rule",
        "date_rule": "app_year",
        "codes": list(APP_CODES),
        "train_positive": (
            "A provider-year is positive when its NPI matches a 10-digit NPI, "
            "EXCLTYPE is one of those four codes, and the year of EXCLDATE is "
            "after the billing year. The earliest qualifying exclusion counts. "
            "Same-year and earlier exclusions are not positive."
        ),
    }


def check_codes(spec: dict, present: set[str]) -> list[str]:
    """Name every spec code the file does not contain. Does not invent a token.

    Does not open a rolled year file. present is the EXCLTYPE set the caller
    already counted, or a fake header counter in a test.
    """
    missing = [code for code in _codes(spec) if code not in present]
    return missing


def excltype_counts(leie_path: Path) -> dict[str, int]:
    """Count EXCLTYPE tokens in one LEIE file. Does not open a rolled year."""
    counts: dict[str, int] = {}
    with leie_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            code = _cell(row, "EXCLTYPE")
            if code:
                counts[code] = counts.get(code, 0) + 1
    return counts


def resolve_leie(spec: dict) -> Path:
    key = str(spec.get("leie_file") or "").replace("\\", "/")
    path = ALLOWED_LEIE.get(key)
    if path is None:
        raise ValueError(
            "leie_file must be data/training/UPDATED.csv or "
            "data/paper_rolled/leie_20170627.csv"
        )
    return path


def load_spec(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_forest_spec() -> dict:
    spec = json.loads(FOREST_SPEC_PATH.read_text(encoding="utf-8"))
    years = tuple(int(year) for year in spec["fit_years"])
    if years != tuple(range(2016, 2023)):
        raise ValueError("models/specs/22.json fit years must be 2016 through 2022")
    return {
        "n_estimators": 60,
        "max_depth": 20,
        "min_samples_leaf": 1,
        "class_weight": "balanced",
        "clean_per_fraud": 9,
        "fit_years": years,
        "random_state": 0,
    }


def read_leie_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_note(lines: list[str]) -> None:
    text = "\n".join(lines).rstrip() + "\n"
    NOTE_PATH.write_text(text, encoding="utf-8")
    print(text, flush=True)


def load_db() -> dict:
    if not DB_PATH.exists():
        return {"best_select_top1": 0, "candidates": []}
    return json.loads(DB_PATH.read_text(encoding="utf-8"))


def save_db(db: dict) -> None:
    DB_PATH.write_text(json.dumps(db, indent=2) + "\n", encoding="utf-8")


def reject(spec_path: Path, spec: dict, reason: str, missing: list[str]) -> None:
    """Record a rejected spec and exit. Does not fit and does not download."""
    db = load_db()
    db.setdefault("candidates", []).append(
        {
            "spec": spec_path.name,
            "name": spec.get("name"),
            "date_rule": spec.get("date_rule"),
            "label_function": label_function_name(spec) if spec else "",
            "select_top1": None,
            "kept": False,
            "missing_codes": missing,
            "reason": reason,
        }
    )
    save_db(db)
    write_note(
        [
            f"rejected {spec_path.name}",
            reason,
            RESEMBLANCE,
        ]
    )
    raise SystemExit(reason)


def year_labels(frame, year: int, leie_rows: list[dict], spec: dict) -> list[int]:
    year_rows = [
        {"npi": npi, "year": year} for npi in frame["npi"].astype(str).str.strip()
    ]
    labels, _info = label_provider_years(leie_rows, year_rows, spec)
    return labels


def slice_width(scores: np.ndarray) -> float:
    """Vote-step slice under zero_tie_break, divided by the year row count.

    The top 1 percent is the share of scores strictly above 0. A zero stays
    outside. A 99th-percentile cutoff on a zero-heavy rank lands on the zero
    step and counts about the top 5 percent, so that cutoff is not used.
    """
    scores = np.asarray(scores, dtype=float)
    if len(scores) == 0:
        return 0.0
    return float(np.sum(scores > 0.0)) / float(len(scores))


def fit_secondary(spec: dict, leie_rows: list[dict], forest: dict):
    """One second forest. 2023 and 2024 are not in the years. n_jobs=2."""
    from sklearn.ensemble import RandomForestClassifier

    columns = training_columns(PAPER_DIR, forest["fit_years"])
    matrices = []
    label_parts = []
    for year in forest["fit_years"]:
        frame = load_year(PAPER_DIR / f"{year}.csv")
        npi = frame["npi"].astype(str).str.strip()
        frame = frame.loc[~npi.isin(DEMO_NPIS)]
        matrix, _ = design_matrix(frame, columns)
        labels = np.array(year_labels(frame, year, leie_rows, spec), dtype=np.int8)
        chosen = sample_indexes(labels, forest["clean_per_fraud"], forest["random_state"])
        matrices.append(matrix[chosen].astype(np.float32, copy=False))
        label_parts.append(labels[chosen])
        print(
            f"fit year={year} kept={len(chosen)} fraud={int(labels[chosen].sum())}",
            flush=True,
        )
        del frame, matrix, labels
    sample = np.vstack(matrices)
    labels = np.concatenate(label_parts)
    model = RandomForestClassifier(
        n_estimators=forest["n_estimators"],
        max_depth=forest["max_depth"],
        min_samples_leaf=forest["min_samples_leaf"],
        class_weight=forest["class_weight"],
        random_state=forest["random_state"],
        n_jobs=2,
    )
    model.fit(sample, labels)
    return model, columns, int(labels.sum()), int(len(labels) - labels.sum())


def rank_year(payload, year: int, secondary, columns: list[str], leie_rows, spec):
    frame = load_year(PAPER_DIR / f"{year}.csv")
    primary = score_year(payload.primary_model, list(payload.primary_columns), frame, chunk=40_000)
    second = score_year(secondary, columns, frame, chunk=40_000)
    ranked = zero_tie_break(
        primary,
        second,
        vote_step=float(payload.vote_step),
        percentile=float(payload.zero_percentile),
    )
    labels = year_labels(frame, year, leie_rows, spec)
    return ranked, labels


def share(scores: np.ndarray, labels: list[int], percentile: float) -> tuple[int, int]:
    captured, fraud, _ratio = top_slice_share(scores.tolist(), labels, percentile)
    return int(captured), int(fraud)


def paper_rule_2024_line(leie_rows: list[dict]) -> str:
    """A paper-rule 2024 count is a different class. Do not invent 1128c3gi."""
    present = {_cell(row, "EXCLTYPE") for row in leie_rows}
    if MISSING_PAPER_TOKEN not in present:
        return f"paper_rule_2024={PAPER_RULE_UNCOUNTED}"
    return "paper_rule_2024=different class"


def fit_one(spec_path: Path) -> None:
    spec = load_spec(spec_path)
    if str(spec.get("date_rule") or "") == "rejected":
        reason = str(spec.get("reason") or spec.get("train_positive") or "date_rule rejected")
        reject(spec_path, spec, reason, list(spec.get("missing_codes") or []))
    try:
        leie_path = resolve_leie(spec)
    except ValueError as exc:
        reject(spec_path, spec, str(exc), [])
        return
    present = set(excltype_counts(leie_path))
    missing = check_codes(spec, present)
    if missing:
        reason = "missing token " + ", ".join(missing)
        reject(spec_path, spec, reason, missing)
        return
    if str(spec.get("date_rule")) == "paper_end" and MISSING_PAPER_TOKEN in _codes(spec):
        if MISSING_PAPER_TOKEN not in present:
            reject(spec_path, spec, f"missing token {MISSING_PAPER_TOKEN}", [MISSING_PAPER_TOKEN])
            return

    forest = load_forest_spec()
    leie_rows = read_leie_rows(leie_path)
    print(f"fitting {spec_path.name} label={label_function_name(spec)}", flush=True)
    payload = joblib_load(OPTIMIZED_PATH)
    secondary, columns, fraud_rows, clean_rows = fit_secondary(spec, leie_rows, forest)
    select_scores, select_labels = rank_year(
        payload, SELECT_YEAR, secondary, columns, leie_rows, spec
    )
    select_top1, select_fraud = share(select_scores, select_labels, 99)
    width = slice_width(select_scores)
    percentile_95 = float(np.percentile(select_scores, 95))
    print(
        f"2023 top1={select_top1}/{select_fraud} slice={width:.4f} p95={percentile_95}",
        flush=True,
    )
    db = load_db()
    previous = int(db.get("best_select_top1") or 0)
    kept = (
        select_top1 > previous
        and width <= 0.02
        and percentile_95 == 0.0
    )
    record = {
        "spec": spec_path.name,
        "name": spec.get("name"),
        "date_rule": spec.get("date_rule"),
        "label_function": label_function_name(spec),
        "select_top1": select_top1,
        "select_fraud": select_fraud,
        "slice_width": width,
        "percentile_95": percentile_95,
        "kept": kept,
    }
    lines = [
        f"spec={spec_path.name}",
        f"label_function={label_function_name(spec)}",
        f"date_rule={spec.get('date_rule')}",
        f"2023 top1={select_top1}/{select_fraud}",
        f"slice_width={width:.6f}",
        f"percentile_95={percentile_95}",
        f"previous_keep={previous}",
        f"kept={str(kept).lower()}",
    ]
    if kept:
        confirm_rows = read_leie_rows(LEIE_PATH)
        confirm_scores, confirm_labels = rank_year(
            payload, CONFIRM_YEAR, secondary, columns, confirm_rows, app_rule_spec()
        )
        top1, fraud = share(confirm_scores, confirm_labels, 99)
        record["confirm_top1"] = top1
        record["confirm_fraud"] = fraud
        candidate = OptimizedRankModel(
            payload.primary_model,
            list(payload.primary_columns),
            secondary,
            columns,
            list(forest["fit_years"]),
            forest["n_estimators"],
            forest["max_depth"] or 0,
            forest["min_samples_leaf"],
            forest["class_weight"] or "none",
            forest["clean_per_fraud"],
            fraud_rows,
            clean_rows,
        )
        CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
        out = CANDIDATE_DIR / f"label_{spec_path.stem}.joblib"
        joblib_dump(candidate, out)
        record["path"] = str(out.relative_to(REPO_ROOT)).replace("\\", "/")
        db["best_select_top1"] = select_top1
        db["best_spec"] = spec_path.name
        lines.extend(
            [
                CAVEAT_2024,
                f"confirm_top1={top1}/{fraud}",
                paper_rule_2024_line(confirm_rows),
                RESEMBLANCE,
            ]
        )
    else:
        lines.append(RESEMBLANCE)
    db.setdefault("candidates", []).append(record)
    save_db(db)
    write_note(lines)


def joblib_load(path: Path):
    import joblib

    return joblib.load(path)


def joblib_dump(payload, path: Path) -> None:
    import joblib

    joblib.dump(payload, path)


def main(argv: list[str] | None = None) -> None:
    args = argv or sys.argv[1:]
    if len(args) == 2 and args[0] == "fit":
        fit_one(Path(args[1]))
        return
    raise SystemExit("usage: py -3.14 scripts/label_islands.py fit models/label_specs/NN.json")


if __name__ == "__main__":
    main()

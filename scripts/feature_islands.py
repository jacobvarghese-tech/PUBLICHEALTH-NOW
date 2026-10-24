"""Append one feature column and refit the second forest. The page forest stays frozen.

The second forest is models/specs/22.json. Fit years are 2016-2022. 2023 is
the keep year. Every legal fit also scores 2024. A candidate is saved only
when that 2024 top 1 percent count is higher than the saved best of 23 of 48.
A rejected formula or a review verdict of reject exits before any download.

A high score means resemblance to later fraud-type exclusions. It is not a
finding that the firm committed fraud.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.harness_score import CAVEAT  # noqa: E402
from scripts.join_labels import DEMO_NPIS  # noqa: E402
from scripts.model_islands import sample_indexes  # noqa: E402
from scripts.optimized_rank import OptimizedRankModel, zero_tie_break  # noqa: E402
from scripts.paper_forest import (  # noqa: E402
    LEIE_PATH,
    design_matrix,
    earliest_exclusion_years,
    label_for_row,
    load_year,
    score_year,
    training_columns,
)
from scripts.paper_roll_year import (  # noqa: E402
    SEX_PATH,
    HeaderMismatch,
    SizeMismatch,
    download,
    load_sex,
    number,
    sex_lookup,
)
from scripts.train import top_slice_share  # noqa: E402

PAPER_DIR = REPO_ROOT / "data" / "paper_rolled"
RAW_DIR = REPO_ROOT / "data" / "raw"
COLUMN_DIR = REPO_ROOT / "data" / "feature_columns"
OPTIMIZED_PATH = REPO_ROOT / "models" / "optimized_model.joblib"
CANDIDATE_DIR = REPO_ROOT / "models" / "candidates"
FOREST_SPEC_PATH = REPO_ROOT / "models" / "specs" / "22.json"
SPEC_DIR = REPO_ROOT / "models" / "feature_specs"
REVIEW_DIR = SPEC_DIR / "reviews"
NOTE_PATH = REPO_ROOT / "models" / "feature_island_note.txt"
DB_PATH = REPO_ROOT / "models" / "feature_island_db.json"
SELECT_YEAR = 2023
CONFIRM_YEAR = 2024
SAVED_BEST_TOP1 = 23
FIT_YEARS = tuple(range(2016, 2023))
REQUIRED_KEYS = ("name", "source_columns", "formula", "join_keys", "grain")
JOIN_KEYS = ("provider_type", "npi", "nppes_provider_gender")
HEADER_REQUIRED = ("Rndrng_NPI", "Rndrng_Prvdr_Type")
EMPTY_NPI = "0000000000"
RESEMBLANCE = (
    "A high score means resemblance to later fraud-type exclusions. "
    "It is not a finding that the firm committed fraud."
)
FORMULA_NAMES = (
    "facility_line_share",
    "facility_service_share",
    "drug_line_share",
    "drug_service_share",
    "nonparticipating_line_share",
    "distinct_hcpcs_count",
    "facility_distinct_hcpcs_count",
    "services_per_distinct_hcpcs",
    "allowed_minus_payment",
    "standardized_over_payment",
    "facility_share_specialty_rank",
)


def column_names(spec: dict) -> list[str]:
    """Spec 12 names two columns. Every other spec names one."""
    named = spec.get("names")
    if named:
        return [str(name) for name in named]
    return [str(spec["name"])]


def _text(row: dict, name: str) -> str:
    return (row.get(name) or "").strip().strip('"')


def _flag(row: dict, name: str) -> str:
    return _text(row, name).upper()


def _provider_key(row: dict) -> tuple[str, str, str] | None:
    npi = _text(row, "Rndrng_NPI")
    if npi == "" or npi == EMPTY_NPI:
        return None
    gender = _text(row, "nppes_provider_gender").upper()
    if gender not in ("M", "F"):
        gender = ""
    return (_text(row, "Rndrng_Prvdr_Type"), npi, gender)


def _blank_bucket() -> dict:
    return {
        "lines": 0,
        "facility_lines": 0,
        "drug_lines": 0,
        "nonparticipating_lines": 0,
        "services": 0.0,
        "facility_services": 0.0,
        "drug_services": 0.0,
        "services_seen": False,
        "hcpcs": set(),
        "facility_hcpcs": set(),
        "gaps": [],
        "stdzd": [],
        "payments": [],
    }


def _add_line(bucket: dict, row: dict) -> None:
    bucket["lines"] += 1
    place = _flag(row, "Place_Of_Srvc")
    drug = _flag(row, "HCPCS_Drug_Ind")
    participating = _flag(row, "Rndrng_Prvdr_Mdcr_Prtcptg_Ind")
    code = _text(row, "HCPCS_Cd")
    services = number(row.get("Tot_Srvcs") or "")
    if place == "F":
        bucket["facility_lines"] += 1
        if services is not None:
            bucket["facility_services"] += services
        if code:
            bucket["facility_hcpcs"].add(code)
    if drug == "Y":
        bucket["drug_lines"] += 1
        if services is not None:
            bucket["drug_services"] += services
    if participating != "Y":
        bucket["nonparticipating_lines"] += 1
    if code:
        bucket["hcpcs"].add(code)
    if services is not None:
        bucket["services"] += services
        bucket["services_seen"] = True
    allowed = number(row.get("Avg_Mdcr_Alowd_Amt") or "")
    payment = number(row.get("Avg_Mdcr_Pymt_Amt") or "")
    standardized = number(row.get("Avg_Mdcr_Stdzd_Amt") or "")
    if allowed is not None and payment is not None:
        bucket["gaps"].append(allowed - payment)
    if standardized is not None and payment is not None:
        bucket["stdzd"].append(standardized)
        bucket["payments"].append(payment)


def _share(part: float, whole: float) -> float:
    if whole == 0:
        return 0.0
    return part / whole


def _values_for(bucket: dict, names: list[str]) -> dict[str, float]:
    lines = bucket["lines"]
    codes = len(bucket["hcpcs"])
    values = {
        "facility_line_share": _share(bucket["facility_lines"], lines),
        "facility_service_share": _share(bucket["facility_services"], bucket["services"])
        if bucket["services_seen"]
        else 0.0,
        "drug_line_share": _share(bucket["drug_lines"], lines),
        "drug_service_share": _share(bucket["drug_services"], bucket["services"])
        if bucket["services_seen"]
        else 0.0,
        "nonparticipating_line_share": _share(bucket["nonparticipating_lines"], lines),
        "distinct_hcpcs_count": float(codes),
        "facility_distinct_hcpcs_count": float(len(bucket["facility_hcpcs"])),
        "services_per_distinct_hcpcs": _share(bucket["services"], codes)
        if bucket["services_seen"]
        else 0.0,
        "allowed_minus_payment": (
            float(np.mean(bucket["gaps"])) if bucket["gaps"] else 0.0
        ),
        "standardized_over_payment": _share(
            float(np.mean(bucket["stdzd"])) if bucket["stdzd"] else 0.0,
            float(np.mean(bucket["payments"])) if bucket["payments"] else 0.0,
        ),
    }
    return {name: float(values[name]) for name in names if name != "facility_share_specialty_rank"}


def _average_ranks(shares: list[float]) -> list[float]:
    """Rank 1 is the lowest share. Ties take the average rank."""
    order = sorted(range(len(shares)), key=lambda index: shares[index])
    ranks = [0.0] * len(shares)
    start = 0
    while start < len(order):
        stop = start + 1
        while stop < len(order) and shares[order[stop]] == shares[order[start]]:
            stop += 1
        average = (start + 1 + stop) / 2.0
        for index in order[start:stop]:
            ranks[index] = average
        start = stop
    return ranks


def column_values(lines: list[dict], spec: dict) -> dict[tuple[str, str, str], dict[str, float]]:
    """lines are raw CMS dicts already gender-filled with key nppes_provider_gender.

    Returns one dict of column name to number per provider-year key.
    Drug lines and non-participating lines stay in. Empty NPI and
    0000000000 are dropped. Rank uses only the lines in this call.
    """
    names = column_names(spec)
    buckets: dict[tuple[str, str, str], dict] = {}
    order: list[tuple[str, str, str]] = []
    for row in lines:
        key = _provider_key(row)
        if key is None:
            continue
        bucket = buckets.get(key)
        if bucket is None:
            bucket = _blank_bucket()
            buckets[key] = bucket
            order.append(key)
        _add_line(bucket, row)
    out = {key: _values_for(buckets[key], names) for key in order}
    if "facility_share_specialty_rank" in names:
        by_type: dict[str, list[tuple[str, str, str]]] = {}
        for key in order:
            by_type.setdefault(key[0], []).append(key)
        for keys in by_type.values():
            shares = [
                _share(buckets[key]["facility_lines"], buckets[key]["lines"]) for key in keys
            ]
            for key, rank in zip(keys, _average_ranks(shares)):
                out[key]["facility_share_specialty_rank"] = float(rank)
    return out


def load_feature_spec(path: Path) -> dict:
    spec = json.loads(path.read_text(encoding="utf-8"))
    missing = [key for key in REQUIRED_KEYS if key not in spec]
    if missing:
        raise ValueError(f"feature spec missing {', '.join(missing)}")
    return spec


def load_forest_spec() -> dict:
    """models/specs/22.json only. The tree settings are not retuned."""
    spec = json.loads(FOREST_SPEC_PATH.read_text(encoding="utf-8"))
    years = tuple(int(year) for year in spec["fit_years"])
    if years != FIT_YEARS:
        raise ValueError("models/specs/22.json fit years must be 2016 through 2022")
    if int(spec["n_estimators"]) != 60 or int(spec["max_depth"]) != 20:
        raise ValueError("models/specs/22.json tree settings are frozen")
    if int(spec["min_samples_leaf"]) != 1 or str(spec["class_weight"]) != "balanced":
        raise ValueError("models/specs/22.json tree settings are frozen")
    if int(spec["clean_per_fraud"]) != 9:
        raise ValueError("models/specs/22.json clean_per_fraud must be 9")
    return {
        "n_estimators": 60,
        "max_depth": 20,
        "min_samples_leaf": 1,
        "class_weight": "balanced",
        "clean_per_fraud": 9,
        "fit_years": years,
        "random_state": 0,
    }


def formula_rejected(spec: dict) -> bool:
    formula = str(spec.get("formula") or "").strip().lower()
    return formula == "rejected" or formula.startswith("rejected")


def review_path(spec_path: Path) -> Path:
    return REVIEW_DIR / f"{spec_path.stem}.json"


def review_rejected(spec_path: Path) -> str | None:
    path = review_path(spec_path)
    if not path.is_file():
        return None
    review = json.loads(path.read_text(encoding="utf-8"))
    if str(review.get("verdict") or "").strip().lower() == "reject":
        return str(review.get("reason") or "review verdict reject")
    return None


def write_note(lines: list[str]) -> None:
    """Append one spec or stop. A later write must not erase earlier counts."""
    block = "\n".join(lines).rstrip()
    NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    prior = NOTE_PATH.read_text(encoding="utf-8") if NOTE_PATH.is_file() else ""
    if prior.strip():
        text = prior.rstrip() + "\n\n" + block + "\n"
    else:
        text = block + "\n"
    NOTE_PATH.write_text(text, encoding="utf-8")
    print(block + "\n", flush=True)


def load_db() -> dict:
    if not DB_PATH.exists():
        return {"candidates": []}
    return json.loads(DB_PATH.read_text(encoding="utf-8"))


def save_db(db: dict) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.write_text(json.dumps(db, indent=2) + "\n", encoding="utf-8")


def record_skip(spec_path: Path, spec: dict, reason: str) -> None:
    """A rejected spec does not download and does not fit."""
    db = load_db()
    db.setdefault("candidates", []).append(
        {
            "spec": spec_path.name,
            "name": spec.get("name"),
            "select_top1": None,
            "select_top5": None,
            "slice_ratio": None,
            "p95": None,
            "kept": False,
            "reason": reason,
            "skipped": True,
        }
    )
    save_db(db)
    write_note(
        [
            f"skipped {spec_path.name}",
            reason,
            CAVEAT,
            RESEMBLANCE,
        ]
    )


def read_resources(year: int, rolled_dir: Path = PAPER_DIR) -> tuple[str, int]:
    """csv_url and opened_bytes from that year's resources file. No invented URL."""
    path = rolled_dir / f"{year}.resources.txt"
    values: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    url = values.get("csv_url") or ""
    if not url:
        raise RuntimeError(f"csv_url missing for year {year}")
    opened = values.get("opened_bytes") or ""
    if not opened.isdigit():
        raise RuntimeError(f"opened_bytes missing for year {year}")
    return url, int(opened)


def record_stop(year: int, reason: str, extra: dict | None = None) -> None:
    """Write a stop to the note and the db. Does not guess a column or a URL."""
    db = load_db()
    record = {"year": year, "stopped": True, "reason": reason}
    if extra:
        record.update(extra)
    db.setdefault("stops", []).append(record)
    save_db(db)
    lines = [f"stopped year={year}", reason]
    if extra:
        for key, value in extra.items():
            lines.append(f"{key}={value}")
    lines.extend([CAVEAT, RESEMBLANCE])
    write_note(lines)


def raw_name(url: str, year: int) -> str:
    name = url.rstrip("/").rsplit("/", 1)[-1]
    if not name.lower().endswith(".csv"):
        name = f"{year}_Prov_Svc.csv"
    return name


def clear_other_raw(keep: Path) -> None:
    """Delete leftover yearly CSVs from an interrupted run of this script.

    The destination and its partial stay, so a resume can continue.
    """
    if not RAW_DIR.is_dir():
        return
    keep_names = {keep.name, keep.with_suffix(keep.suffix + ".partial").name}
    for path in RAW_DIR.iterdir():
        if not path.is_file() or path.name in keep_names:
            continue
        lowered = path.name.lower()
        yearly = "prov_svc" in lowered or lowered.startswith("phys")
        if lowered.endswith(".csv") and yearly:
            path.unlink()
        if lowered.endswith(".csv.partial") and yearly:
            path.unlink()


def required_header(spec: dict) -> list[str]:
    names = [_text({"_": name}, "_") or str(name) for name in spec.get("source_columns") or []]
    needed = list(HEADER_REQUIRED)
    for name in names:
        if name and name not in needed:
            needed.append(name)
    return needed


def missing_header(header: list[str], needed: list[str]) -> list[str]:
    present = {name.strip().strip('"') for name in header}
    return [name for name in needed if name not in present]


def open_gender_lookup():
    """NPI to M/F from data/nppes/npi_sex.csv. Reused across years in one run."""
    db_path = RAW_DIR / "feature_island_sex.sqlite"
    if not db_path.is_file():
        load_sex(db_path, SEX_PATH)
    return sex_lookup(db_path), db_path


def _column_store(path: Path) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute(
        """
        CREATE TABLE lines (
            provider_type TEXT NOT NULL,
            npi TEXT NOT NULL,
            gender TEXT NOT NULL,
            place TEXT,
            drug TEXT,
            participating TEXT,
            hcpcs TEXT,
            services TEXT,
            allowed TEXT,
            payment TEXT,
            standardized TEXT
        )
        """
    )
    return conn


def stream_column_file(raw_path: Path, year: int, spec: dict, lookup) -> None:
    """Stream one raw year into data/feature_columns/YEAR_NAME.csv.

    Lines are spilled to SQLite so a full CMS year is not held in RAM.
    The written numbers are column_values on each provider's lines.
    """
    names = column_names(spec)
    needed = required_header(spec)
    store_path = RAW_DIR / f"feature_island_{year}.sqlite"
    conn = _column_store(store_path)
    try:
        with raw_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            header = [name.strip().strip('"') for name in (reader.fieldnames or [])]
            missing = missing_header(header, needed)
            if missing:
                raise HeaderMismatch(year, missing)
            batch = []
            seen = 0
            for row in reader:
                npi = _text(row, "Rndrng_NPI")
                if npi == "" or npi == EMPTY_NPI:
                    continue
                gender = lookup(npi)
                if gender not in ("M", "F"):
                    gender = ""
                batch.append(
                    (
                        _text(row, "Rndrng_Prvdr_Type"),
                        npi,
                        gender,
                        _text(row, "Place_Of_Srvc"),
                        _text(row, "HCPCS_Drug_Ind"),
                        _text(row, "Rndrng_Prvdr_Mdcr_Prtcptg_Ind"),
                        _text(row, "HCPCS_Cd"),
                        _text(row, "Tot_Srvcs"),
                        _text(row, "Avg_Mdcr_Alowd_Amt"),
                        _text(row, "Avg_Mdcr_Pymt_Amt"),
                        _text(row, "Avg_Mdcr_Stdzd_Amt"),
                    )
                )
                seen += 1
                if len(batch) >= 50_000:
                    conn.executemany("INSERT INTO lines VALUES (?,?,?,?,?,?,?,?,?,?,?)", batch)
                    batch = []
                if seen % 500_000 == 0:
                    conn.commit()
                    print(f"year={year} source_rows={seen}", flush=True)
            if batch:
                conn.executemany("INSERT INTO lines VALUES (?,?,?,?,?,?,?,?,?,?,?)", batch)
            conn.commit()
        write_columns_from_store(conn, year, spec, names)
    finally:
        conn.close()
        store_path.unlink(missing_ok=True)


def write_columns_from_store(
    conn: sqlite3.Connection,
    year: int,
    spec: dict,
    names: list[str],
) -> Path:
    """Group the spilled lines and call column_values once per provider."""
    COLUMN_DIR.mkdir(parents=True, exist_ok=True)
    path = COLUMN_DIR / f"{year}_{spec['name']}.csv"
    write_names = list(names)
    if "facility_share_specialty_rank" in names and "facility_line_share" not in names:
        write_names = ["facility_line_share", *names]
    write_spec = dict(spec)
    write_spec["names"] = write_names
    fieldnames = [*JOIN_KEYS, *write_names]
    query = (
        "SELECT provider_type, npi, gender, place, drug, participating, hcpcs, "
        "services, allowed, payment, standardized FROM lines "
        "ORDER BY provider_type, npi, gender"
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        current = None
        lines: list[dict] = []

        def emit() -> None:
            if current is None or not lines:
                return
            values = column_values(lines, write_spec)
            key = (
                lines[0]["Rndrng_Prvdr_Type"],
                lines[0]["Rndrng_NPI"],
                lines[0]["nppes_provider_gender"],
            )
            payload = values.get(key) or {name: 0.0 for name in write_names}
            writer.writerow(
                {
                    "provider_type": key[0],
                    "npi": key[1],
                    "nppes_provider_gender": key[2],
                    **{name: payload.get(name, 0.0) for name in write_names},
                }
            )

        for record in conn.execute(query):
            row = {
                "Rndrng_Prvdr_Type": record[0],
                "Rndrng_NPI": record[1],
                "nppes_provider_gender": record[2] or "",
                "Place_Of_Srvc": record[3] or "",
                "HCPCS_Drug_Ind": record[4] or "",
                "Rndrng_Prvdr_Mdcr_Prtcptg_Ind": record[5] or "",
                "HCPCS_Cd": record[6] or "",
                "Tot_Srvcs": record[7] or "",
                "Avg_Mdcr_Alowd_Amt": record[8] or "",
                "Avg_Mdcr_Pymt_Amt": record[9] or "",
                "Avg_Mdcr_Stdzd_Amt": record[10] or "",
            }
            key = (record[0], record[1], record[2] or "")
            if current is not None and key != current:
                emit()
                lines = []
            current = key
            lines.append(row)
        emit()
    if "facility_share_specialty_rank" in names:
        _rewrite_specialty_ranks(path, names)
    print(f"column year={year} path={path.name}", flush=True)
    return path


def _rewrite_specialty_ranks(path: Path, names: list[str]) -> None:
    """Rank is within the year, not within one provider's spilled lines."""
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    shares = pd.to_numeric(frame["facility_line_share"], errors="coerce").fillna(0.0)
    ranks = pd.Series(0.0, index=frame.index)
    for indexes in frame.groupby("provider_type").groups.values():
        ordered = list(indexes)
        values = [float(shares.loc[index]) for index in ordered]
        for index, rank in zip(ordered, _average_ranks(values)):
            ranks.loc[index] = rank
    frame["facility_share_specialty_rank"] = ranks
    if "facility_line_share" not in names:
        frame = frame.drop(columns=["facility_line_share"])
    frame.to_csv(path, index=False)


def column_path(year: int, spec: dict) -> Path:
    return COLUMN_DIR / f"{year}_{spec['name']}.csv"


def ensure_column(year: int, spec: dict, *, kept: bool = False) -> Path:
    """Build the year column file when it is missing. One raw year at a time.

    2024 is downloaded only when the caller passes kept=True. fit_one does
    that for every legal spec so the finish loop can score 2024. A call
    with kept=False still removes a leftover 2024 column and does not download.
    """
    path = column_path(year, spec)
    if year == CONFIRM_YEAR and not kept:
        path.unlink(missing_ok=True)
        raise RuntimeError("2024 column is built only after a keep")
    if path.is_file() and path.stat().st_size > 0:
        return path
    try:
        url, expected = read_resources(year)
    except RuntimeError as exc:
        record_stop(year, str(exc))
        raise SystemExit(str(exc)) from exc
    dest = RAW_DIR / raw_name(url, year)
    clear_other_raw(dest)
    lookup = None
    try:
        received = download(url, dest, expected)
        if received != expected:
            raise SizeMismatch(expected, received)
        lookup, _db_path = open_gender_lookup()
        try:
            stream_column_file(dest, year, spec, lookup)
        finally:
            lookup.close()
            lookup = None
    except SizeMismatch as mismatch:
        record_stop(
            year,
            f"size mismatch year={year}",
            {"expected_bytes": mismatch.expected, "received_bytes": mismatch.received},
        )
        raise SystemExit(
            f"size mismatch year={year} expected={mismatch.expected} received={mismatch.received}"
        ) from mismatch
    except HeaderMismatch as mismatch:
        record_stop(
            year,
            f"header mismatch year={year} missing={', '.join(mismatch.missing)}",
            {"missing": ",".join(mismatch.missing)},
        )
        column_path(year, spec).unlink(missing_ok=True)
        raise SystemExit(str(mismatch)) from mismatch
    except Exception:
        column_path(year, spec).unlink(missing_ok=True)
        raise
    finally:
        if dest.is_file():
            dest.unlink()
        partial = dest.with_suffix(dest.suffix + ".partial")
        if partial.is_file():
            partial.unlink()
    return path


def append_features(frame: pd.DataFrame, columns: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    """Join on provider_type, npi, and gender. A missing feature fills 0."""
    out = frame.copy()
    out["npi"] = out["npi"].astype(str).str.strip()
    out["provider_type"] = out["provider_type"].fillna("").astype(str)
    out["nppes_provider_gender"] = out["nppes_provider_gender"].fillna("").astype(str)
    extra = columns.copy()
    extra["npi"] = extra["npi"].astype(str).str.strip()
    extra["provider_type"] = extra["provider_type"].fillna("").astype(str)
    extra["nppes_provider_gender"] = extra["nppes_provider_gender"].fillna("").astype(str)
    keep = ["provider_type", "npi", "nppes_provider_gender", *names]
    extra = extra.loc[:, [name for name in keep if name in extra.columns]]
    extra = extra.drop_duplicates(list(JOIN_KEYS), keep="last")
    for name in names:
        extra[name] = pd.to_numeric(extra[name], errors="coerce")
    merged = out.merge(extra, on=list(JOIN_KEYS), how="left")
    if len(merged) != len(out):
        raise RuntimeError("feature join changed the rolled row count")
    for name in names:
        merged[name] = merged[name].fillna(0.0)
    return merged


def extended_design_matrix(
    frame: pd.DataFrame,
    names: list[str],
    columns: list[str] | None = None,
):
    """Paper dummies and summaries, then the new numeric column(s)."""
    matrix, base = design_matrix(frame, None if columns is None else _base_columns(columns, names))
    extra = frame.loc[:, list(names)].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    stacked = np.column_stack([matrix, extra.to_numpy(dtype=float)])
    extended = [*base, *names]
    if columns is None:
        return stacked, extended
    aligned = pd.DataFrame(stacked, columns=extended).reindex(columns=columns, fill_value=0.0)
    return aligned.to_numpy(dtype=float), columns


def _base_columns(columns: list[str], names: list[str]) -> list[str]:
    extra = set(names)
    return [name for name in columns if name not in extra]


def fit_secondary(spec: dict, forest: dict, feature_names: list[str]):
    """One second forest. 2023 and 2024 never enter the fit. n_jobs=2."""
    from sklearn.ensemble import RandomForestClassifier

    base = training_columns(PAPER_DIR, forest["fit_years"])
    columns = [*base, *feature_names]
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    matrices = []
    label_parts = []
    for year in forest["fit_years"]:
        ensure_column(year, spec)
        frame = load_year(PAPER_DIR / f"{year}.csv")
        npi = frame["npi"].astype(str).str.strip()
        frame = frame.loc[~npi.isin(DEMO_NPIS)].reset_index(drop=True)
        features = pd.read_csv(column_path(year, spec), dtype=str, keep_default_na=False)
        frame = append_features(frame, features, feature_names)
        matrix, _ = extended_design_matrix(frame, feature_names, columns)
        year_labels = np.array(
            [label_for_row(year, one, exclusion_years) for one in frame["npi"].astype(str)],
            dtype=np.int8,
        )
        chosen = sample_indexes(year_labels, forest["clean_per_fraud"], 0)
        matrices.append(matrix[chosen].astype(np.float32, copy=False))
        label_parts.append(year_labels[chosen])
        print(
            f"fit year={year} kept={len(chosen)} fraud={int(year_labels[chosen].sum())}",
            flush=True,
        )
        del frame, features, matrix, year_labels
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


def rank_year(
    payload,
    year: int,
    secondary,
    columns: list[str],
    names: list[str],
    spec: dict,
    *,
    kept: bool = False,
):
    """Page forest scores the rolled frame. The second forest sees the new column.

    kept=True lets a 2024 column stay. The default still removes a leftover
    2024 file when the caller has not asked to score that year.
    """
    frame = load_year(PAPER_DIR / f"{year}.csv")
    primary = score_year(
        payload.primary_model, list(payload.primary_columns), frame, chunk=40_000
    )
    ensure_column(year, spec, kept=kept)
    features = pd.read_csv(column_path(year, spec), dtype=str, keep_default_na=False)
    extended = append_features(frame, features, names)
    second = score_extended(secondary, columns, extended, names)
    ranked = zero_tie_break(
        primary,
        second,
        vote_step=float(payload.vote_step),
        percentile=float(payload.zero_percentile),
    )
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    labels = [
        label_for_row(year, npi, exclusion_years) for npi in frame["npi"].astype(str)
    ]
    return ranked, labels


def score_extended(model, columns: list[str], frame: pd.DataFrame, names: list[str], chunk: int = 40_000):
    scores = np.empty(len(frame), dtype=float)
    for start in range(0, len(frame), chunk):
        stop = min(start + chunk, len(frame))
        matrix, _ = extended_design_matrix(frame.iloc[start:stop], names, columns)
        scores[start:stop] = model.predict_proba(matrix)[:, 1]
    return scores


def share(scores: np.ndarray, labels: list[int], percentile: float) -> tuple[int, int]:
    captured, fraud, _ratio = top_slice_share(scores.tolist(), labels, percentile)
    return int(captured), int(fraud)


def slice_ratio(scores: np.ndarray) -> float:
    """Top 1 percent slice size divided by the year row count."""
    if len(scores) == 0:
        return 0.0
    cutoff = float(np.percentile(np.asarray(scores, dtype=float), 99))
    return float(np.sum(np.asarray(scores, dtype=float) >= cutoff)) / float(len(scores))


def p95(scores: np.ndarray) -> float:
    if len(scores) == 0:
        return 0.0
    return float(np.percentile(np.asarray(scores, dtype=float), 95))


def baseline_rank(payload, forest: dict) -> tuple[np.ndarray, list[int]]:
    """Frozen page forest plus a spec-22 second forest with no new column."""
    from sklearn.ensemble import RandomForestClassifier

    columns = training_columns(PAPER_DIR, forest["fit_years"])
    exclusion_years = earliest_exclusion_years(LEIE_PATH)
    matrices = []
    label_parts = []
    for year in forest["fit_years"]:
        frame = load_year(PAPER_DIR / f"{year}.csv")
        npi = frame["npi"].astype(str).str.strip()
        frame = frame.loc[~npi.isin(DEMO_NPIS)]
        matrix, _ = design_matrix(frame, columns)
        year_labels = np.array(
            [label_for_row(year, one, exclusion_years) for one in frame["npi"].astype(str)],
            dtype=np.int8,
        )
        chosen = sample_indexes(year_labels, forest["clean_per_fraud"], 0)
        matrices.append(matrix[chosen].astype(np.float32, copy=False))
        label_parts.append(year_labels[chosen])
        print(
            f"baseline year={year} kept={len(chosen)} fraud={int(year_labels[chosen].sum())}",
            flush=True,
        )
        del frame, matrix, year_labels
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
    frame = load_year(PAPER_DIR / f"{SELECT_YEAR}.csv")
    primary = score_year(
        payload.primary_model, list(payload.primary_columns), frame, chunk=40_000
    )
    second = score_year(model, columns, frame, chunk=40_000)
    ranked = zero_tie_break(
        primary,
        second,
        vote_step=float(payload.vote_step),
        percentile=float(payload.zero_percentile),
    )
    year_labels = [
        label_for_row(SELECT_YEAR, npi, exclusion_years) for npi in frame["npi"].astype(str)
    ]
    return ranked, year_labels


def ensure_baseline(payload, forest: dict, db: dict) -> int:
    if db.get("baseline_select_top1") is not None:
        return int(db["baseline_select_top1"])
    scores, labels = baseline_rank(payload, forest)
    top1, fraud = share(scores, labels, 99)
    db["baseline_select_top1"] = top1
    db["baseline_select_fraud"] = fraud
    save_db(db)
    print(f"baseline_select_top1={top1}/{fraud}", flush=True)
    return top1


def previous_keep(db: dict) -> int | None:
    if db.get("best_select_top1") is None:
        return None
    return int(db["best_select_top1"])


def kept_rule(select_top1: int, ratio: float, percentile_95: float, previous: int) -> bool:
    return select_top1 > previous and ratio <= 0.02 and percentile_95 == 0.0


def loop_already_stopped(db: dict) -> str | None:
    """A recorded size or URL stop blocks the next download until it is cleared.

    release_stop writes cleared=true on that stop. A later stop still blocks.
    """
    stops = db.get("stops") or []
    if not stops:
        return None
    last = stops[-1]
    if not last.get("stopped") or last.get("cleared"):
        return None
    return str(last.get("reason") or "stopped")


def release_stop(db: dict | None = None) -> bool:
    """Clear the latest stop after the live file size was checked by hand.

    The 2016 resources page and a range request both still say 3,051,491,999
    bytes. The 3,077,063,327 byte download was longer than that file. This
    does not change opened_bytes and does not invent a URL.
    """
    db = load_db() if db is None else db
    stops = db.get("stops") or []
    if not stops or not stops[-1].get("stopped") or stops[-1].get("cleared"):
        return False
    stops[-1]["cleared"] = True
    stops[-1]["cleared_reason"] = (
        "live Content-Range matches opened_bytes; the longer download was not the file"
    )
    save_db(db)
    return True


def confirm_best(db: dict) -> int:
    saved = db.get("best_confirm_top1")
    if saved is None:
        return SAVED_BEST_TOP1
    return int(saved)


def score_confirm(payload, spec, secondary, columns, names, forest) -> tuple[int, int, int]:
    """Build the 2024 column and return top 1 percent, top 5 percent, and fraud count."""
    ensure_column(CONFIRM_YEAR, spec, kept=True)
    confirm_scores, confirm_labels = rank_year(
        payload, CONFIRM_YEAR, secondary, columns, names, spec, kept=True
    )
    top1, fraud = share(confirm_scores, confirm_labels, 99)
    top5, _fraud = share(confirm_scores, confirm_labels, 95)
    return top1, top5, fraud


def fit_one(spec_path: Path) -> None:
    stopped = loop_already_stopped(load_db())
    if stopped:
        raise SystemExit(f"loop already stopped: {stopped}")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if formula_rejected(spec):
        reason = str(spec.get("formula") or "rejected")
        record_skip(spec_path, spec, reason)
        raise SystemExit(reason)
    review_reason = review_rejected(spec_path)
    if review_reason is not None:
        record_skip(spec_path, spec, review_reason)
        raise SystemExit(review_reason)
    spec = load_feature_spec(spec_path)
    forest = load_forest_spec()
    names = column_names(spec)
    unknown = [name for name in names if name not in FORMULA_NAMES]
    if unknown:
        raise ValueError(f"unknown formula name {', '.join(unknown)}")
    print(f"fitting {spec_path.name} columns={','.join(names)}", flush=True)
    payload = joblib_load(OPTIMIZED_PATH)
    db = load_db()
    baseline = ensure_baseline(payload, forest, db)
    secondary, columns, fraud_rows, clean_rows = fit_secondary(spec, forest, names)
    select_scores, select_labels = rank_year(
        payload, SELECT_YEAR, secondary, columns, names, spec
    )
    select_top1, select_fraud = share(select_scores, select_labels, 99)
    select_top5, _select_fraud5 = share(select_scores, select_labels, 95)
    ratio = slice_ratio(select_scores)
    percentile_95 = p95(select_scores)
    prior = previous_keep(db)
    bar = baseline if prior is None else prior
    select_kept = kept_rule(select_top1, ratio, percentile_95, bar)
    print(
        f"2023 top1={select_top1}/{select_fraud} top5={select_top5}/{select_fraud} "
        f"slice={ratio:.4f} p95={percentile_95} select_kept={select_kept}",
        flush=True,
    )
    top1, top5, fraud = score_confirm(payload, spec, secondary, columns, names, forest)
    saved_best = confirm_best(db)
    kept = top1 > saved_best
    print(
        f"confirm_top1={top1}/{fraud} confirm_top5={top5}/{fraud} "
        f"saved_best={saved_best}/48 kept={kept}",
        flush=True,
    )
    record = {
        "spec": spec_path.name,
        "name": spec.get("name"),
        "select_top1": select_top1,
        "select_top5": select_top5,
        "slice_ratio": ratio,
        "p95": percentile_95,
        "select_kept": select_kept,
        "kept": kept,
        "baseline_select_top1": baseline,
        "confirm_top1": top1,
        "confirm_top5": top5,
        "saved_best": saved_best,
    }
    lines = [
        CAVEAT,
        f"spec={spec_path.name}",
        f"name={spec.get('name')}",
        f"2023 top1={select_top1}/{select_fraud}",
        f"2023 top5={select_top5}/{select_fraud}",
        f"slice_ratio={ratio:.6f}",
        f"p95={percentile_95}",
        f"baseline_select_top1={baseline}",
        f"previous_keep={bar}",
        f"select_kept={str(select_kept).lower()}",
        f"confirm_top1={top1}/{fraud}",
        f"confirm_top5={top5}/{fraud}",
        f"saved_best={saved_best}/48",
        f"kept={str(kept).lower()}",
        RESEMBLANCE,
    ]
    db.setdefault("candidates", []).append(record)
    if kept:
        out = save_candidate(
            payload, secondary, columns, forest, fraud_rows, clean_rows, spec_path
        )
        record["path"] = _relative_path(out)
        db["best_confirm_top1"] = top1
        db["best_spec"] = spec_path.name
        db["best_select_top1"] = select_top1
    save_db(db)
    write_note(lines)


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def save_candidate(payload, secondary, columns, forest, fraud_rows, clean_rows, spec_path: Path) -> Path:
    """Write the kept second forest beside the frozen page forest."""
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
    out = CANDIDATE_DIR / f"feature_{spec_path.stem}.joblib"
    joblib_dump(candidate, out)
    return out


def joblib_load(path: Path):
    import joblib

    return joblib.load(path)


def joblib_dump(payload, path: Path) -> None:
    import joblib

    joblib.dump(payload, path)


def main(argv: list[str] | None = None) -> None:
    args = argv or sys.argv[1:]
    if len(args) == 1 and args[0] == "release-stop":
        cleared = release_stop()
        print(f"released={str(cleared).lower()}", flush=True)
        return
    if len(args) == 2 and args[0] == "fit":
        fit_one(Path(args[1]))
        return
    raise SystemExit(
        "usage: py -3.14 scripts/feature_islands.py fit models/feature_specs/NN.json"
        " | release-stop"
    )


if __name__ == "__main__":
    main()

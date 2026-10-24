"""Join the June 27, 2017 LEIE capture and fit the paper comparison forest.

Keeps Table 2 exclusion types. Leaves indefinite 1128(c)(3)(g)(ii) out of
the fraud class. Undersamples clean rows to 9 per fraud row. Fits
RandomForestClassifier with n_estimators=100 only. random_state=0 is a
labeled stand-in, not a paper seed. No feature-subspace size is set.
Does not edit the saved XGBoost files or data/training/UPDATED.csv.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RepeatedStratifiedKFold, cross_val_score

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from paper_roll_year import record_2012_gap, record_size_mismatch  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
ROLLED_DIR = REPO_ROOT / "data" / "paper_rolled"
LABEL_PATH = REPO_ROOT / "data" / "paper_rolled" / "leie_20170627.csv"
OUT_PATH = REPO_ROOT / "models" / "paper_replicate.json"
LEIE_URL = (
    "https://web.archive.org/web/20170627194828id_/"
    "https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv"
)
# Size the June 27, 2017 Wayback URL returns. The page's 2,814,802 figure is not that object.
LEIE_BYTES = 12069440

# Compact spellings as written in the capture (1128a1, not 1128(a)(1)), plus
# the parenthesized and c3g forms the same statute uses.
LENGTHS = {
    "1128a1": 5,
    "1128a2": 5,
    "1128a3": 5,
    "1128b4": 5,
    "1128c3gi": 10,
    "1128c3g1": 10,
    "1128c3gi1": 10,
}
INDEFINITE_CODES = frozenset(
    {
        "1128c3gii",
        "1128c3g2",
        "1128c3gii2",
    }
)
PAPER_AUC = 0.87302
CLEAN_PER_FRAUD = 9
YEARS = (2013, 2014, 2015)
GAPS = [
    "2012 procedure-level file was not opened",
    "2014 and 2015 gender comes from the October 12, 2026 NPPES snapshot",
    "LEIE file is the June 27, 2017 capture (12069440 bytes), not a named author download",
    "that capture contains no 1128(c)(3)(g)(i) or 1128(c)(3)(g)(ii) rows",
    "random_state=0 is not a paper seed",
    "fraud count need not match 1409",
]


def normalize_type(value: str) -> str:
    """Collapse parentheses, spaces, and case so both file spellings match Table 2."""
    return (
        (value or "")
        .strip()
        .strip('"')
        .lower()
        .replace("(", "")
        .replace(")", "")
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
    )


def table2_years(code: str) -> int | None:
    """Return the minimum exclusion length, or None when the code is not Table 2.

    Indefinite 1128(c)(3)(g)(ii) is not a length. Callers count those rows and
    leave them out of the fraud class.
    """
    if code in INDEFINITE_CODES:
        return None
    return LENGTHS.get(code)


def is_indefinite(code: str) -> bool:
    return code in INDEFINITE_CODES


def parse_date(value: str):
    text = (value or "").strip()
    if text in ("", "00000000") or len(text) != 8 or not text.isdigit():
        return None
    return datetime.strptime(text, "%Y%m%d")


def add_years(start: datetime, years: int) -> datetime:
    try:
        return start.replace(year=start.year + years)
    except ValueError:
        return start.replace(year=start.year + years, day=28)


def end_year(start: datetime, years: int, reinstatement, waiver) -> int:
    """Minimum exclusion length, then the earliest month/year among end, reinstatement, and waiver.

    A month greater than 6 advances the end year. The claims year is fraud
    when it is prior to that end year.
    """
    end = add_years(start, years)
    candidates = [end]
    for other in (reinstatement, waiver):
        if other is not None:
            candidates.append(other)
    chosen = min(candidates)
    return chosen.year + (1 if chosen.month > 6 else 0)


def load_labels(path: Path = LABEL_PATH) -> tuple[dict[str, int], int]:
    ends: dict[str, int] = {}
    indefinite = 0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            npi = (row.get("NPI") or "").strip().strip('"')
            if len(npi) != 10 or not npi.isdigit() or npi == "0000000000":
                continue
            code = normalize_type(row.get("EXCLTYPE") or "")
            if is_indefinite(code):
                indefinite += 1
                continue
            years = table2_years(code)
            if years is None:
                continue
            start = parse_date(row.get("EXCLDATE") or "")
            if start is None:
                continue
            year = end_year(
                start,
                years,
                parse_date(row.get("REINDATE") or ""),
                parse_date(row.get("WAIVERDATE") or ""),
            )
            current = ends.get(npi)
            if current is None or year > current:
                ends[npi] = year
    return ends, indefinite


class LabelSizeMismatch(Exception):
    """The LEIE file is not the June 27, 2017 capture."""

    def __init__(self, expected: int, received: int) -> None:
        self.expected = expected
        self.received = received
        super().__init__(f"LEIE size mismatch expected={expected} received={received}")


def record_label_mismatch(
    expected: int,
    received: int,
    rolled_dir: Path = ROLLED_DIR,
    out_path: Path | None = None,
    label_path: Path | None = None,
) -> Path:
    """Write both sizes and stop. A wrong-size download is not used as labels.

    The note is leie.size.txt so a physician year file is not deleted.
    A score is removed only when this call names that file. The default
    models/paper_replicate.json is left alone so a fixture mismatch cannot
    delete a finished fit.
    """
    rolled_dir.mkdir(parents=True, exist_ok=True)
    note = rolled_dir / "leie.size.txt"
    note.write_text(
        (
            "Size mismatch for the June 27, 2017 LEIE capture. Fit not finished.\n"
            f"expected_bytes={expected}\n"
            f"received_bytes={received}\n"
        ),
        encoding="utf-8",
    )
    if label_path is not None and label_path.is_file() and label_path.stat().st_size != expected:
        label_path.unlink()
    if out_path is not None and out_path.is_file():
        out_path.unlink()
    return note


def ensure_labels(path: Path = LABEL_PATH, rolled_dir: Path = ROLLED_DIR) -> Path:
    """Keep the file when it is the size the June 27, 2017 URL returns.

    A different size is recorded (both expected and received) and the run stops.
    A matching file is kept and is not a mismatch.
    """
    stale = rolled_dir / "leie.size.txt"
    false_note = rolled_dir / "20170627.size.txt"
    if path.is_file() and path.stat().st_size == LEIE_BYTES:
        if stale.is_file():
            stale.unlink()
        if false_note.is_file():
            false_note.unlink()
        return path
    if path.is_file() and path.stat().st_size != LEIE_BYTES:
        received = path.stat().st_size
        record_label_mismatch(LEIE_BYTES, received, rolled_dir, label_path=path)
        raise LabelSizeMismatch(LEIE_BYTES, received)
    path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "curl.exe",
            "--fail",
            "--location",
            "--retry",
            "5",
            "--retry-all-errors",
            "--output",
            str(path),
            LEIE_URL,
        ]
    )
    if completed.returncode != 0 or not path.is_file():
        raise SystemExit(f"LEIE download failed: {LEIE_URL}")
    received = path.stat().st_size
    if received != LEIE_BYTES:
        record_label_mismatch(LEIE_BYTES, received, rolled_dir, label_path=path)
        raise LabelSizeMismatch(LEIE_BYTES, received)
    if stale.is_file():
        stale.unlink()
    return path


def label_frame(frame: pd.DataFrame, ends: dict[str, int]) -> pd.DataFrame:
    """Fraud when the claims year is prior to the exclusion end year."""
    labeled = frame.copy()
    end_series = labeled["npi"].astype(str).map(ends)
    labeled["fraud"] = (labeled["year"] < end_series.fillna(0)).astype(int)
    return labeled


def undersample(frame: pd.DataFrame, clean_per_fraud: int = CLEAN_PER_FRAUD):
    """Keep every fraud row. Undersample only clean rows."""
    fraud = frame[frame["fraud"] == 1]
    clean = frame[frame["fraud"] == 0]
    keep_clean = min(len(clean), clean_per_fraud * len(fraud))
    chosen = (
        clean.sample(n=keep_clean, random_state=0) if keep_clean else clean.iloc[0:0]
    )
    sample = pd.concat([fraud, chosen], ignore_index=True)
    return sample, int(len(fraud)), int(keep_clean)


def feature_matrix(sample: pd.DataFrame):
    """Specialty and gender as one-hot columns. No feature-subspace size."""
    specialty = pd.get_dummies(
        sample["provider_type"].fillna("").astype(str), prefix="specialty"
    )
    gender = pd.get_dummies(
        sample["nppes_provider_gender"].fillna("").astype(str), prefix="gender"
    )
    numeric = sample.drop(
        columns=["provider_type", "npi", "nppes_provider_gender", "year", "fraud"]
    )
    x = np.column_stack(
        [specialty.to_numpy(dtype=float), gender.to_numpy(dtype=float), numeric.to_numpy(dtype=float)]
    )
    y = sample["fraud"].to_numpy(dtype=int)
    return x, y


def forest_kwargs() -> dict:
    """Only n_estimators=100 plus the labeled stand-in. No feature-subspace size."""
    return {"n_estimators": 100, "random_state": 0, "n_jobs": -1}


def new_forest() -> RandomForestClassifier:
    """random_state=0 is a labeled stand-in, not a paper seed.

    max_features is left unset so no feature-subspace size is passed.
    """
    return RandomForestClassifier(**forest_kwargs())


def score_auc(model: RandomForestClassifier, x, y) -> np.ndarray:
    splitter = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=0)
    return cross_val_score(model, x, y, cv=splitter, scoring="roc_auc")


def build_payload(
    new_auc: float,
    auc_std: float,
    fraud_rows: int,
    clean_rows_kept: int,
    indefinite: int,
) -> dict:
    return {
        "paper_cell": "RF100 90:10",
        "paper_auc": PAPER_AUC,
        "new_auc": new_auc,
        "auc_std": auc_std,
        "fraud_rows": fraud_rows,
        "clean_rows_kept": clean_rows_kept,
        "indefinite_rows_left_out": indefinite,
        "leie_bytes": LEIE_BYTES,
        "leie_capture": "2017-06-27",
        "years": list(YEARS),
        "skipped_year": 2012,
        "n_estimators": 100,
        "random_state_stand_in": 0,
        "random_state_note": "labeled stand-in, not a paper seed",
        "feature_subspace": "unset",
        "cv": "RepeatedStratifiedKFold n_splits=5 n_repeats=10 scoring=roc_auc",
        "gaps": list(GAPS),
    }


def load_years(rolled_dir: Path = ROLLED_DIR) -> pd.DataFrame:
    frames = []
    for year in YEARS:
        path = rolled_dir / f"{year}.csv"
        if not path.is_file():
            raise SystemExit(f"missing rolled year: {path}")
        frames.append(pd.read_csv(path, dtype={"npi": str}))
    return pd.concat(frames, ignore_index=True)


def fit_and_write(
    frame: pd.DataFrame,
    ends: dict[str, int],
    indefinite: int,
    out_path: Path = OUT_PATH,
) -> dict:
    labeled = label_frame(frame, ends)
    sample, fraud_rows, clean_rows = undersample(labeled)
    print(
        f"kept_fraud={fraud_rows} kept_clean={clean_rows} "
        f"indefinite_rows_left_out={indefinite}",
        flush=True,
    )
    x, y = feature_matrix(sample)
    model = new_forest()
    scores = score_auc(model, x, y)
    payload = build_payload(
        float(scores.mean()),
        float(scores.std()),
        fraud_rows,
        clean_rows,
        indefinite,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2), flush=True)
    return payload


def main() -> None:
    record_2012_gap(ROLLED_DIR)
    try:
        ensure_labels(LABEL_PATH)
    except LabelSizeMismatch as mismatch:
        print(
            f"STOP leie expected_bytes={mismatch.expected} "
            f"received_bytes={mismatch.received}",
            flush=True,
        )
        raise SystemExit(2) from mismatch
    ends, indefinite = load_labels(LABEL_PATH)
    frame = load_years(ROLLED_DIR)
    fit_and_write(frame, ends, indefinite, OUT_PATH)


if __name__ == "__main__":
    main()

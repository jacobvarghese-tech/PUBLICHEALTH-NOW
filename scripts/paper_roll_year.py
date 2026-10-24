"""Stream one physician year into the paper's grouped table.

Group by specialty, NPI, gender, and year. Aggregate over HCPCS and place
of service. Write the grouped row count, then the six summaries of the five
numeric fields. Keep name, city, state, and ZIP on the rolled row. Delete
the raw CSV after the rolled file and the count exist.

2013 NBER columns are the paper names. Later CMS columns are the names in
data/nppes/column_map.txt. Gender on a CMS file comes from
data/nppes/npi_sex.csv. A file that has pgender uses that column. A file
without pgender is filled from NPPES and the substitute is recorded.

2013, 2014, and 2015 already have opened URLs. 2016 through 2024 open that
year's CMS resources page before any download and record the CSV URL and
byte count from that open. A header that does not match the known map is
recorded and not guessed. A partial download resumes. A size that disagrees
with the opened byte count is written beside the year and stops the run.
A missing 2012 file is a recorded gap, not a stop.
"""

from __future__ import annotations

import argparse
import csv
import heapq
import json
import sqlite3
import statistics
import subprocess
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
ROLLED_DIR = REPO_ROOT / "data" / "paper_rolled"
SEX_PATH = REPO_ROOT / "data" / "nppes" / "npi_sex.csv"

NBER_2013_URL = "http://data.nber.org/cms/providercharge/2013/phys2013.csv"
NBER_2013_BYTES = 2590718145
CMS_2014_URL = (
    "https://data.cms.gov/sites/default/files/2025-11/"
    "6700f86d-d2e5-4f2d-9dcb-8c30412768ff/"
    "MUP_PHY_R25_P04_V20_D14_Prov_Svc.csv"
)
CMS_2014_BYTES = 2905565005
CMS_2015_URL = (
    "https://data.cms.gov/sites/default/files/2025-11/"
    "14954ce3-4c43-43df-97e9-2c0437d7b43c/"
    "MUP_PHY_R25_P04_V20_D15_Prov_Svc.csv"
)
CMS_2015_BYTES = 2975342985

# Dataset version ids from the opened provider-and-service API docs page.
# A year still opens its own resources page. These ids are not CSV URLs.
CMS_DATASET_IDS = {
    2016: "7918e22a-fbfb-4a07-9f59-f8aab2b757d4",
    2017: "85bf3c9c-2244-490d-ad7d-c34e4c28f8ea",
    2018: "fb6d9fe8-38c1-4d24-83d4-0b7b291000b2",
    2019: "867b8ac7-ccb7-4cc9-873d-b24340d89e32",
    2020: "c957b49e-1323-49e7-8678-c09da387551d",
    2021: "31dc2c47-f297-4948-bfb4-075e1bec3a02",
    2022: "e650987d-01b7-4f09-b75e-b0b075afbf98",
    2023: "0e9f2f2b-7bf9-451a-912c-e02e654dd725",
    2024: "335e5f35-eca6-482d-87b3-f99883e213e3",
}
RESOURCES_URL = "https://data.cms.gov/data-api/v1/dataset/{dataset_id}/resources"
ROLL_YEARS = (2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024)

YEARS = {
    2013: {
        "url": NBER_2013_URL,
        "bytes": NBER_2013_BYTES,
        "layout": "nber",
        "raw_name": "phys2013.csv",
    },
    2014: {
        "url": CMS_2014_URL,
        "bytes": CMS_2014_BYTES,
        "layout": "cms",
        "raw_name": "MUP_PHY_R25_P04_V20_D14_Prov_Svc.csv",
    },
    2015: {
        "url": CMS_2015_URL,
        "bytes": CMS_2015_BYTES,
        "layout": "cms",
        "raw_name": "MUP_PHY_R25_P04_V20_D15_Prov_Svc.csv",
    },
}
for _year, _dataset_id in CMS_DATASET_IDS.items():
    YEARS[_year] = {
        "dataset_id": _dataset_id,
        "layout": "cms",
        "resources_url": RESOURCES_URL.format(dataset_id=_dataset_id),
    }

NBER_FIELDS = {
    "npi": "npi",
    "provider_type": "provider_type",
    "gender": "pgender",
    "hcpcs": "hcpcs_cd",
    "place": "plcsrvc",
    "line_srvc_cnt": "srvc_cnt",
    "bene_unique_cnt": "bene_unique_cnt",
    "bene_day_srvc_cnt": "bene_day_srvc_cnt",
    "average_submitted_chrg_amt": "average_submitted_chrg_amt",
    "average_medicare_payment_amt": "average_medicare_payment_amt",
    "drug": "hcpcs_drug_indicator",
    "participate": "medicare_participation_indicator",
}
CMS_FIELDS = {
    "npi": "Rndrng_NPI",
    "provider_type": "Rndrng_Prvdr_Type",
    "last_org": "Rndrng_Prvdr_Last_Org_Name",
    "first_name": "Rndrng_Prvdr_First_Name",
    "city": "Rndrng_Prvdr_City",
    "state": "Rndrng_Prvdr_State_Abrvtn",
    "zip": "Rndrng_Prvdr_Zip5",
    "gender": None,
    "hcpcs": "HCPCS_Cd",
    "place": "Place_Of_Srvc",
    "line_srvc_cnt": "Tot_Srvcs",
    "bene_unique_cnt": "Tot_Benes",
    "bene_day_srvc_cnt": "Tot_Bene_Day_Srvcs",
    "average_submitted_chrg_amt": "Avg_Sbmtd_Chrg",
    "average_medicare_payment_amt": "Avg_Mdcr_Pymt_Amt",
    "drug": "HCPCS_Drug_Ind",
    "participate": "Rndrng_Prvdr_Mdcr_Prtcptg_Ind",
}
IDENTITY = ("name", "city", "state", "zip")
NUMERIC = (
    "line_srvc_cnt",
    "bene_unique_cnt",
    "bene_day_srvc_cnt",
    "average_submitted_chrg_amt",
    "average_medicare_payment_amt",
)
SUMMARIES = ("mean", "sum", "median", "std", "min", "max")
GENDER_NPPES = "nppes_2026-10-12"
GENDER_PGENDER = "pgender"
SKIP_2012 = (
    "year=2012\n"
    "status=skipped\n"
    "reason=no original 2012 procedure-level file was opened\n"
    "data_url=not invented\n"
)


class SizeMismatch(Exception):
    """Download length disagrees with the opened byte count."""

    def __init__(self, expected: int, received: int) -> None:
        self.expected = expected
        self.received = received
        super().__init__(f"size mismatch expected={expected} received={received}")


class HeaderMismatch(Exception):
    """The opened header does not match the known CMS or NBER map."""

    def __init__(self, year: int, missing: list[str]) -> None:
        self.year = year
        self.missing = missing
        super().__init__(
            f"header mismatch year={year} missing={', '.join(missing)}"
        )


def year_done(year: int, rolled_dir: Path = ROLLED_DIR) -> bool:
    """A finished year has a non-empty rolled CSV and a grouped-row count."""
    rolled = rolled_dir / f"{year}.csv"
    count = rolled_dir / f"{year}.count.txt"
    if not (rolled.is_file() and rolled.stat().st_size > 0 and count.is_file()):
        return False
    text = count.read_text(encoding="utf-8")
    return "grouped_rows=" in text and "grouped_rows=\n" not in text


def record_2012_gap(rolled_dir: Path = ROLLED_DIR) -> Path:
    """Write the missing-2012 gap. Does not stop the later years."""
    rolled_dir.mkdir(parents=True, exist_ok=True)
    note = rolled_dir / "2012.gap.txt"
    note.write_text(SKIP_2012, encoding="utf-8")
    return note


def resources_url(year: int) -> str:
    """The CMS resources page for one dataset id. Not a CSV URL."""
    dataset_id = CMS_DATASET_IDS[year]
    return RESOURCES_URL.format(dataset_id=dataset_id)


def open_resources(year: int, opener=None) -> dict:
    """Open that year's resources page and return the body. Does not invent a URL."""
    url = resources_url(year)
    fetch = opener or _fetch_resources
    body = fetch(url)
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    return json.loads(body)


def _fetch_resources(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "paper-roll-year"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read().decode("utf-8")


def csv_from_resources(payload: dict) -> tuple[str, int]:
    """Read the primary CSV URL and byte count from an opened resources payload.

    Accepts the file_url/file_size shape and the downloadURL/fileSize shape.
    A payload with no CSV URL raises. The caller must not invent one.
    """
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise RuntimeError("opened resources page has no data list")
    csv_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("file_name") or row.get("name") or "")
        url = str(row.get("file_url") or row.get("downloadURL") or "")
        size = row.get("file_size")
        if size is None:
            size = row.get("fileSize")
        if url.lower().endswith(".csv") or name.lower().endswith(".csv"):
            csv_rows.append((name, url, size))
    primary = [
        item
        for item in csv_rows
        if "Prov_Svc" in item[0] or "provider and service" in item[0].lower()
    ]
    chosen = primary[0] if primary else (csv_rows[0] if csv_rows else None)
    if chosen is None or not chosen[1] or chosen[2] is None:
        raise RuntimeError("opened resources page has no CSV URL and byte count")
    return chosen[1], int(chosen[2])


def record_opened_resources(
    year: int,
    url: str,
    expected: int,
    rolled_dir: Path = ROLLED_DIR,
) -> Path:
    """Write the CSV URL and byte count from the page that was just opened."""
    rolled_dir.mkdir(parents=True, exist_ok=True)
    note = rolled_dir / f"{year}.resources.txt"
    note.write_text(
        (
            f"year={year}\n"
            f"resources_url={resources_url(year)}\n"
            f"csv_url={url}\n"
            f"opened_bytes={expected}\n"
        ),
        encoding="utf-8",
    )
    return note


def record_header_mismatch(
    year: int,
    missing: list[str],
    header: list[str],
    rolled_dir: Path = ROLLED_DIR,
) -> Path:
    """Record a header that does not match the known map. Do not guess columns."""
    rolled_dir.mkdir(parents=True, exist_ok=True)
    note = rolled_dir / f"{year}.header.txt"
    shown = ", ".join(header[:12])
    note.write_text(
        (
            f"Header mismatch for {year}. Rolled file not finished.\n"
            f"missing={', '.join(missing)}\n"
            f"header={shown}\n"
            "guessed=no\n"
        ),
        encoding="utf-8",
    )
    rolled = rolled_dir / f"{year}.csv"
    count = rolled_dir / f"{year}.count.txt"
    if rolled.exists():
        rolled.unlink()
    if count.exists():
        count.unlink()
    return note


def record_size_mismatch(
    year: int,
    expected: int,
    received: int,
    rolled_dir: Path = ROLLED_DIR,
) -> Path:
    """Write both sizes beside the year and leave no finished rolled table.

    Callers must not continue to a later year or the fit after this note.
    """
    rolled_dir.mkdir(parents=True, exist_ok=True)
    note = rolled_dir / f"{year}.size.txt"
    note.write_text(
        (
            f"Size mismatch for {year}. Rolled file not finished.\n"
            f"expected_bytes={expected}\n"
            f"received_bytes={received}\n"
        ),
        encoding="utf-8",
    )
    rolled = rolled_dir / f"{year}.csv"
    count = rolled_dir / f"{year}.count.txt"
    if rolled.exists():
        rolled.unlink()
    if count.exists():
        count.unlink()
    return note


def download(url: str, dest: Path, expected: int, resume=None) -> int:
    """Resume dest.partial, then rename only when the byte count matches.

    A complete dest of the expected size is not fetched again. A size that
    disagrees raises SizeMismatch and leaves the partial file in place.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size == expected:
        return expected
    partial = dest.with_suffix(dest.suffix + ".partial")
    if dest.is_file() and not partial.is_file():
        dest.replace(partial)
    start = partial.stat().st_size if partial.is_file() else 0
    if start > expected:
        raise SizeMismatch(expected, start)
    if start < expected:
        (resume or _resume)(url, partial, start)
    received = partial.stat().st_size if partial.is_file() else 0
    if received != expected:
        raise SizeMismatch(expected, received)
    partial.replace(dest)
    return received


def _resume(url: str, partial: Path, start: int) -> None:
    """Append from the partial file's current size. curl -C - refuses a non-206 reply.

    The offset is read from the file so a retry continues at the new size.
    start is the size the caller already observed; a shorter file is a bug.
    """
    have = partial.stat().st_size if partial.is_file() else 0
    if have < start:
        raise RuntimeError(f"partial shrank from {start} to {have}")
    command = [
        "curl.exe",
        "--fail",
        "--location",
        "--retry",
        "8",
        "--retry-all-errors",
        "--retry-delay",
        "10",
        "--continue-at",
        "-",
        "--output",
        str(partial),
        url,
    ]
    completed = subprocess.run(command)
    if completed.returncode != 0:
        raise RuntimeError(f"download failed with status {completed.returncode}")


def load_sex(db_path: Path, sex_path: Path = SEX_PATH) -> None:
    if db_path.is_file():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE sex (npi TEXT PRIMARY KEY, gender TEXT)")
    with sex_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = (
            (
                (row.get("NPI") or "").strip(),
                (row.get("nppes_provider_gender") or "").strip(),
            )
            for row in reader
        )
        conn.executemany(
            "INSERT OR REPLACE INTO sex (npi, gender) VALUES (?, ?)", rows
        )
    conn.commit()
    conn.close()


def sex_lookup(db_path: Path):
    conn = sqlite3.connect(db_path)
    cache: dict[str, str] = {}

    def get(npi: str) -> str:
        found = cache.get(npi)
        if found is not None:
            return found
        row = conn.execute("SELECT gender FROM sex WHERE npi = ?", (npi,)).fetchone()
        value = row[0] if row else ""
        if len(cache) < 200_000:
            cache[npi] = value
        return value

    def close() -> None:
        conn.close()

    get.close = close  # type: ignore[attr-defined]
    return get


def number(text: str) -> float | None:
    value = (text or "").strip().strip('"')
    if value == "":
        return None
    return float(value)


def choose_fields(header: list[str]) -> tuple[dict[str, str | None], str]:
    """Use pgender when the header has it. Otherwise fill gender from NPPES.

    A header that matches neither known map raises. Callers record that
    mismatch and do not guess a column.
    """
    names = {name.strip().strip('"') for name in header}
    if "pgender" in names and "hcpcs_cd" in names:
        return dict(NBER_FIELDS), GENDER_PGENDER
    if "Rndrng_NPI" in names:
        return dict(CMS_FIELDS), GENDER_NPPES
    raise RuntimeError(
        "header has neither pgender and hcpcs_cd nor Rndrng_NPI: "
        + ", ".join(header[:8])
    )


def missing_columns(header: list[str], fields: dict[str, str | None]) -> list[str]:
    """Required source names that are absent from the opened header."""
    names = {name.strip().strip('"') for name in header}
    return [name for name in fields.values() if name and name not in names]


def provider_name(last_org: str, first: str) -> str:
    """Join last-or-org and first name the way a search box would show them."""
    last_org = (last_org or "").strip().strip('"')
    first = (first or "").strip().strip('"')
    if last_org and first:
        return f"{last_org}, {first}"
    return last_org or first


class Running:
    """One numeric feature inside one provider-year group.

    Mean, sum, minimum, and maximum are running totals. The observed values
    stay only until median and the sample standard deviation are written.
    A single observation has standard deviation 0, matching the paper's
    replacement of the sample-standard-deviation NA.
    """

    __slots__ = ("n", "total", "low", "high", "values")

    def __init__(self) -> None:
        self.n = 0
        self.total = 0.0
        self.low = 0.0
        self.high = 0.0
        self.values: list[float] = []

    def add(self, value: float) -> None:
        if self.n == 0:
            self.low = value
            self.high = value
        else:
            if value < self.low:
                self.low = value
            if value > self.high:
                self.high = value
        self.n += 1
        self.total += value
        self.values.append(value)

    def row(self) -> list[float | str]:
        if self.n == 0:
            return ["", "", "", "", "", ""]
        mean = self.total / self.n
        median = statistics.median(self.values)
        std = statistics.stdev(self.values) if self.n > 1 else 0.0
        self.values = []
        return [mean, self.total, median, std, self.low, self.high]


def _identity_from_row(row: dict, fields: dict[str, str | None]) -> dict[str, str]:
    """Name, city, state, and ZIP. An NBER file has none of these columns."""
    if not fields.get("city"):
        return {"name": "", "city": "", "state": "", "zip": ""}
    return {
        "name": provider_name(
            row.get(fields["last_org"]) or "",
            row.get(fields["first_name"]) or "",
        ),
        "city": (row.get(fields["city"]) or "").strip().strip('"'),
        "state": (row.get(fields["state"]) or "").strip().strip('"'),
        "zip": (row.get(fields["zip"]) or "").strip().strip('"'),
    }


def _group_store(db_path: Path) -> sqlite3.Connection:
    """One row per provider-year group. Values stay only until the summaries are written."""
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute(
        """
        CREATE TABLE groups (
            provider_type TEXT NOT NULL,
            npi TEXT NOT NULL,
            gender TEXT NOT NULL,
            name TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            PRIMARY KEY (provider_type, npi, gender)
        )
        """
    )
    value_columns = ", ".join(f"{name} TEXT" for name in NUMERIC)
    count_columns = ", ".join(f"{name}_n INTEGER" for name in NUMERIC)
    conn.execute(
        f"CREATE TABLE running (provider_type TEXT, npi TEXT, gender TEXT, {count_columns}, {value_columns})"
    )
    return conn


def aggregate(
    raw_path: Path,
    year: int,
    lookup=None,
    store_path: Path | None = None,
) -> tuple[dict[tuple[str, str, str], dict] | sqlite3.Connection, int, str]:
    """Group one raw CSV. Returns groups, source-row count, and gender source.

    Each group holds the six running summaries and the first name, city,
    state, and ZIP seen for that specialty, NPI, and gender. A store_path
    spills observed values to SQLite and returns that connection instead of
    an in-memory dict. The summary math is the same either way.
    """
    if store_path is not None:
        return _aggregate_to_store(raw_path, year, lookup, store_path)
    groups: dict[tuple[str, str, str], dict] = {}
    source_rows = 0
    with raw_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = [name.strip().strip('"') for name in (reader.fieldnames or [])]
        fields, gender_source = choose_fields(header)
        if gender_source == GENDER_NPPES and lookup is None:
            raise RuntimeError("NPPES gender fill requested without a lookup")
        missing = missing_columns(header, fields)
        if missing:
            raise HeaderMismatch(year, missing)
        for row in reader:
            kept = _keep_source_row(row, fields, lookup)
            if kept is None:
                continue
            key, identity, values = kept
            bucket = groups.get(key)
            if bucket is None:
                bucket = {name: Running() for name in NUMERIC}
                bucket["_id"] = identity
                groups[key] = bucket
            for name, value in values:
                bucket[name].add(value)
            source_rows += 1
            if source_rows % 500_000 == 0:
                print(
                    f"year={year} source_rows={source_rows} groups={len(groups)}",
                    flush=True,
                )
    return groups, source_rows, gender_source


def _keep_source_row(row: dict, fields: dict, lookup):
    """One source row that survives the paper filters, or None."""
    npi = (row.get(fields["npi"]) or "").strip().strip('"')
    hcpcs = (row.get(fields["hcpcs"]) or "").strip().strip('"')
    if npi == "" or npi == "0000000000" or hcpcs == "":
        return None
    if (row.get(fields["drug"]) or "").strip().strip('"').upper() == "Y":
        return None
    if (row.get(fields["participate"]) or "").strip().strip('"').upper() != "Y":
        return None
    if fields["gender"]:
        gender = (row.get(fields["gender"]) or "").strip().strip('"').upper()
    else:
        gender = lookup(npi)
    if gender not in ("M", "F"):
        gender = ""
    key = ((row.get(fields["provider_type"]) or "").strip().strip('"'), npi, gender)
    identity = _identity_from_row(row, fields)
    values = []
    for name in NUMERIC:
        value = number(row.get(fields[name]) or "")
        if value is not None:
            values.append((name, value))
    return key, identity, values


def _flush_open_groups(conn: sqlite3.Connection, open_groups: dict) -> None:
    """Write one running row per open group. Values are joined text, then dropped from RAM."""
    if not open_groups:
        return
    identities = []
    rows = []
    for (provider_type, npi, gender), bucket in open_groups.items():
        if bucket.get("_new"):
            identity = bucket["_id"]
            identities.append(
                (
                    provider_type,
                    npi,
                    gender,
                    identity["name"],
                    identity["city"],
                    identity["state"],
                    identity["zip"],
                )
            )
        counts = [bucket[name].n for name in NUMERIC]
        packed = [
            ",".join(str(value) for value in bucket[name].values) for name in NUMERIC
        ]
        rows.append((provider_type, npi, gender, *counts, *packed))
        for name in NUMERIC:
            bucket[name].values = []
    if identities:
        conn.executemany(
            "INSERT OR IGNORE INTO groups VALUES (?,?,?,?,?,?,?)",
            identities,
        )
    placeholders = ", ".join("?" for _ in range(3 + len(NUMERIC) * 2))
    conn.executemany(f"INSERT INTO running VALUES ({placeholders})", rows)
    conn.commit()
    open_groups.clear()


def _aggregate_to_store(
    raw_path: Path,
    year: int,
    lookup,
    store_path: Path,
) -> tuple[sqlite3.Connection, int, str]:
    """Same filters as aggregate. Open groups flush to SQLite so RAM stays bounded."""
    conn = _group_store(store_path)
    source_rows = 0
    open_groups: dict[tuple[str, str, str], dict] = {}
    with raw_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = [name.strip().strip('"') for name in (reader.fieldnames or [])]
        fields, gender_source = choose_fields(header)
        if gender_source == GENDER_NPPES and lookup is None:
            raise RuntimeError("NPPES gender fill requested without a lookup")
        missing = missing_columns(header, fields)
        if missing:
            conn.close()
            raise HeaderMismatch(year, missing)
        for row in reader:
            kept = _keep_source_row(row, fields, lookup)
            if kept is None:
                continue
            key, identity, values = kept
            bucket = open_groups.get(key)
            if bucket is None:
                if len(open_groups) >= 80_000:
                    _flush_open_groups(conn, open_groups)
                bucket = {name: Running() for name in NUMERIC}
                bucket["_id"] = identity
                bucket["_new"] = True
                open_groups[key] = bucket
            for name, value in values:
                bucket[name].add(value)
            source_rows += 1
            if source_rows % 500_000 == 0:
                print(
                    f"year={year} source_rows={source_rows} open={len(open_groups)}",
                    flush=True,
                )
    _flush_open_groups(conn, open_groups)
    conn.commit()
    return conn, source_rows, gender_source


def _summarize_store(conn: sqlite3.Connection):
    """Yield one grouped row. Summary math matches Running.row, including a split group."""
    identity = {
        (provider_type, npi, gender): (name or "", city or "", state or "", zip or "")
        for provider_type, npi, gender, name, city, state, zip in conn.execute(
            "SELECT provider_type, npi, gender, name, city, state, zip FROM groups"
        )
    }
    count_names = [f"{name}_n" for name in NUMERIC]
    selected = ", ".join(["provider_type", "npi", "gender", *count_names, *NUMERIC])
    width = len(NUMERIC)
    current = None
    parts: list[tuple] = []

    def emit():
        if current is None:
            return None
        name, city, state, zip = identity.get(current, ("", "", "", ""))
        derived: list[float | str] = []
        for index in range(width):
            running = Running()
            for part in parts:
                count = part[index] or 0
                packed = part[width + index] or ""
                if count and packed:
                    for piece in packed.split(","):
                        running.add(float(piece))
            derived.extend(running.row())
        return (*current, name, city, state, zip, derived)

    for row in conn.execute(f"SELECT {selected} FROM running ORDER BY provider_type, npi, gender"):
        key = (row[0], row[1], row[2])
        if current is not None and key != current:
            yielded = emit()
            if yielded is not None:
                yield yielded
            parts = []
        current = key
        parts.append(row[3:])
    yielded = emit()
    if yielded is not None:
        yield yielded


def count_text(
    year: int,
    source_rows: int,
    grouped_rows: int,
    received: int,
    expected: int,
    gender_source: str,
    csv_url: str = "",
) -> str:
    """The count file. Opened URL and both byte counts sit beside the row counts."""
    lines = [
        f"year={year}",
        f"source_rows={source_rows}",
        f"grouped_rows={grouped_rows}",
        f"received_bytes={received}",
        f"expected_bytes={expected}",
        f"opened_bytes={expected}",
        f"gender_source={gender_source}",
    ]
    if csv_url:
        lines.append(f"csv_url={csv_url}")
    return "\n".join(lines) + "\n"


def feature_names() -> list[str]:
    return [f"{feature}_{summary}" for feature in NUMERIC for summary in SUMMARIES]


def rolled_header() -> list[str]:
    return [
        "provider_type",
        "npi",
        "nppes_provider_gender",
        "year",
        "name",
        "city",
        "state",
        "zip",
        *feature_names(),
    ]


def _grouped_count(groups) -> int:
    if isinstance(groups, sqlite3.Connection):
        return groups.execute("SELECT COUNT(*) FROM groups").fetchone()[0]
    return len(groups)


def write_rolled(
    year: int,
    groups,
    source_rows: int,
    received: int,
    expected: int,
    gender_source: str,
    rolled_dir: Path = ROLLED_DIR,
    csv_url: str = "",
) -> Path:
    """Write the grouped-row count before the six-summary table."""
    rolled_dir.mkdir(parents=True, exist_ok=True)
    grouped_rows = _grouped_count(groups)
    count_path = rolled_dir / f"{year}.count.txt"
    count_path.write_text(
        count_text(
            year,
            source_rows,
            grouped_rows,
            received,
            expected,
            gender_source,
            csv_url,
        ),
        encoding="utf-8",
    )
    out_path = rolled_dir / f"{year}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(rolled_header())
        if isinstance(groups, sqlite3.Connection):
            rows = _summarize_store(groups)
        else:
            rows = _summarize_memory(groups)
        written = 0
        for provider_type, npi, gender, name, city, state, zip, derived in rows:
            writer.writerow(
                [provider_type, npi, gender, year, name, city, state, zip, *derived]
            )
            written += 1
            if written % 100_000 == 0:
                print(f"year={year} wrote={written}", flush=True)
    return out_path


def _summarize_memory(groups: dict):
    for (provider_type, npi, gender), bucket in groups.items():
        identity = bucket.get("_id") or {"name": "", "city": "", "state": "", "zip": ""}
        derived: list[float | str] = []
        for feature in NUMERIC:
            derived.extend(bucket[feature].row())
        yield (
            provider_type,
            npi,
            gender,
            identity.get("name", ""),
            identity.get("city", ""),
            identity.get("state", ""),
            identity.get("zip", ""),
            derived,
        )


def resolve_download(
    year: int,
    opener=None,
    rolled_dir: Path = ROLLED_DIR,
) -> tuple[str, int, str]:
    """Return CSV URL, opened byte count, and raw file name.

    2013-2015 use the URL already opened for those years. 2016-2024 open
    that year's resources page first and record what that open returned.
    A page with no CSV URL raises. Nothing here invents a URL.
    """
    spec = YEARS[year]
    if spec.get("url") and spec.get("bytes") and spec.get("raw_name"):
        return spec["url"], int(spec["bytes"]), spec["raw_name"]
    payload = open_resources(year, opener=opener)
    url, expected = csv_from_resources(payload)
    record_opened_resources(year, url, expected, rolled_dir)
    print(
        f"opened year={year} csv_url={url} opened_bytes={expected}",
        flush=True,
    )
    raw_name = url.rstrip("/").rsplit("/", 1)[-1]
    if not raw_name.lower().endswith(".csv"):
        raise RuntimeError(f"opened URL is not a CSV: {url}")
    return url, expected, raw_name


def roll_year(
    year: int,
    delete_raw: bool = True,
    raw_dir: Path = RAW_DIR,
    rolled_dir: Path = ROLLED_DIR,
    sex_path: Path = SEX_PATH,
    opener=None,
    resume=None,
) -> Path:
    if year_done(year, rolled_dir):
        print(f"skip year={year} already rolled", flush=True)
        return rolled_dir / f"{year}.csv"
    url, expected, raw_name = resolve_download(year, opener=opener, rolled_dir=rolled_dir)
    raw_path = raw_dir / raw_name
    try:
        received = download(url, raw_path, expected, resume=resume)
    except SizeMismatch as mismatch:
        record_size_mismatch(
            year, mismatch.expected, mismatch.received, rolled_dir
        )
        raise
    if received != expected:
        record_size_mismatch(year, expected, received, rolled_dir)
        raise SizeMismatch(expected, received)
    lookup = None
    header = _peek_header(raw_path)
    try:
        fields, gender_source = choose_fields(header)
        missing = missing_columns(header, fields)
        if missing:
            raise HeaderMismatch(year, missing)
    except (HeaderMismatch, RuntimeError) as error:
        missing = error.missing if isinstance(error, HeaderMismatch) else [str(error)]
        record_header_mismatch(year, missing, header, rolled_dir)
        raise HeaderMismatch(year, missing) from error
    if gender_source == GENDER_NPPES:
        sex_db = raw_dir / "npi_sex.sqlite"
        if not sex_db.is_file():
            load_sex(sex_db, sex_path)
        lookup = sex_lookup(sex_db)
    store_path = raw_dir / f"{year}.groups.sqlite"
    sorted_path = raw_dir / f"{year}.by_npi.csv"
    try:
        _sort_by_npi(raw_path, sorted_path, fields)
        groups, source_rows, gender_source = aggregate(sorted_path, year, lookup)
    except HeaderMismatch as error:
        record_header_mismatch(year, error.missing, header, rolled_dir)
        raise
    try:
        out_path = write_rolled(
            year,
            groups,
            source_rows,
            received,
            expected,
            gender_source,
            rolled_dir,
            csv_url=url,
        )
    finally:
        if isinstance(groups, sqlite3.Connection):
            groups.close()
        if store_path.is_file():
            store_path.unlink()
        if sorted_path.is_file():
            sorted_path.unlink()
    if lookup is not None and hasattr(lookup, "close"):
        lookup.close()
    if delete_raw and raw_path.is_file() and year_done(year, rolled_dir):
        raw_path.unlink()
    return out_path


def _sort_by_npi(raw_path: Path, sorted_path: Path, fields: dict) -> None:
    """Sort the raw CSV by NPI so one provider's rows are contiguous.

    Chunks are sorted in memory and merged. The NPI column is parsed, so a
    quoted field does not shift the key. A finished sorted file is kept.
    """
    npi_name = fields["npi"] or "npi"
    if sorted_path.is_file() and sorted_path.stat().st_size > 0:
        with sorted_path.open(newline="", encoding="utf-8-sig") as handle:
            first = next(csv.reader(handle), [])
        if npi_name in {name.strip().strip('"') for name in first}:
            print(f"sorted file already present {sorted_path}", flush=True)
            return
        sorted_path.unlink()
    chunk_dir = sorted_path.parent / f"{sorted_path.stem}.chunks"
    if chunk_dir.exists():
        for child in chunk_dir.iterdir():
            child.unlink()
    else:
        chunk_dir.mkdir(parents=True)
    with raw_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = [name.strip().strip('"') for name in next(reader)]
        index = header.index(npi_name)
        chunk: list[tuple[str, list[str]]] = []
        chunk_paths: list[Path] = []

        def flush() -> None:
            if not chunk:
                return
            chunk.sort(key=lambda item: item[0])
            path = chunk_dir / f"{len(chunk_paths):04d}.csv"
            with path.open("w", newline="", encoding="utf-8") as out:
                writer = csv.writer(out)
                for _key, row in chunk:
                    writer.writerow(row)
            chunk_paths.append(path)
            chunk.clear()
            print(f"sort chunks={len(chunk_paths)}", flush=True)

        for row in reader:
            key = row[index].strip().strip('"') if index < len(row) else ""
            chunk.append((key, row))
            if len(chunk) >= 400_000:
                flush()
        flush()
    handles = [path.open(newline="", encoding="utf-8") for path in chunk_paths]
    readers = [csv.reader(handle) for handle in handles]
    pending: list[tuple[str, int, list[str]]] = []
    for slot, reader in enumerate(readers):
        row = next(reader, None)
        if row is not None:
            key = row[index].strip().strip('"') if index < len(row) else ""
            pending.append((key, slot, row))
    heapq.heapify(pending)
    with sorted_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        written = 0
        while pending:
            key, slot, row = heapq.heappop(pending)
            del key
            writer.writerow(row)
            written += 1
            if written % 1_000_000 == 0:
                print(f"merge wrote={written}", flush=True)
            nxt = next(readers[slot], None)
            if nxt is not None:
                nxt_key = nxt[index].strip().strip('"') if index < len(nxt) else ""
                heapq.heappush(pending, (nxt_key, slot, nxt))
    for handle in handles:
        handle.close()
    for path in chunk_paths:
        path.unlink()
    chunk_dir.rmdir()


def _peek_header(raw_path: Path) -> list[str]:
    with raw_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        return next(reader)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True, choices=sorted(YEARS))
    parser.add_argument("--keep-raw", action="store_true")
    args = parser.parse_args()
    try:
        path = roll_year(args.year, delete_raw=not args.keep_raw)
    except SizeMismatch as mismatch:
        print(
            f"STOP year={args.year} expected_bytes={mismatch.expected} "
            f"received_bytes={mismatch.received}",
            flush=True,
        )
        raise SystemExit(2) from mismatch
    except HeaderMismatch as mismatch:
        print(
            f"STOP year={args.year} header missing={', '.join(mismatch.missing)}",
            flush=True,
        )
        raise SystemExit(3) from mismatch
    print(path)


if __name__ == "__main__":
    main()

"""Download one CMS provider-and-service year and roll it to one row per NPI.

Year, CSV URL, and expected byte count are arguments. Source rows are one
rendering NPI, one HCPCS code, and one place of service. The rollup
collapses those to a provider-year using the column contract in
wiki/concepts/action-plan.md. Growth is this year's service count divided
by the prior rolled year's service count, minus 1. A year with no prior
table, including 2018, leaves Growth missing.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from collections import defaultdict
from pathlib import Path

# Defaults keep a no-argument launch on the 2018 path.
YEAR = 2018
EXPECTED_BYTES = 3125246884
CSV_URL = (
    "https://data.cms.gov/sites/default/files/2025-11/"
    "5669eafb-f0b3-4dc5-be6d-abc09b480c2e/"
    "MUP_PHY_R25_P04_V20_D18_Prov_Svc.csv"
)

YEAR_FILES = {
    2018: {
        "url": CSV_URL,
        "bytes": EXPECTED_BYTES,
        "raw_name": "MUP_PHY_R25_P04_V20_D18_Prov_Svc.csv",
    },
    2019: {
        "url": (
            "https://data.cms.gov/sites/default/files/2025-11/"
            "7befba27-752e-47a8-a76c-6c6d4f74f2e3/"
            "MUP_PHY_R25_P04_V20_D19_Prov_Svc.csv"
        ),
        "bytes": 3176102801,
        "raw_name": "MUP_PHY_R25_P04_V20_D19_Prov_Svc.csv",
    },
    2020: {
        "url": (
            "https://data.cms.gov/sites/default/files/2025-11/"
            "d22b18cd-7726-4bf5-8e9c-3e4587c589a1/"
            "MUP_PHY_R25_P05_V20_D20_Prov_Svc.csv"
        ),
        "bytes": 2994090236,
        "raw_name": "MUP_PHY_R25_P05_V20_D20_Prov_Svc.csv",
    },
    2021: {
        "url": (
            "https://data.cms.gov/sites/default/files/2025-11/"
            "bffaf97a-c2ab-4fd7-8718-be90742e3485/"
            "MUP_PHY_R25_P05_V20_D21_Prov_Svc.csv"
        ),
        "bytes": 3100222715,
        "raw_name": "MUP_PHY_R25_P05_V20_D21_Prov_Svc.csv",
    },
    2022: {
        "url": (
            "https://data.cms.gov/sites/default/files/2025-11/"
            "53fb2bae-4913-48dc-a6d4-d8c025906567/"
            "MUP_PHY_R25_P05_V20_D22_Prov_Svc.csv"
        ),
        "bytes": 3066783950,
        "raw_name": "MUP_PHY_R25_P05_V20_D22_Prov_Svc.csv",
    },
    2023: {
        "url": (
            "https://data.cms.gov/sites/default/files/2025-04/"
            "e3f823f8-db5b-4cc7-ba04-e7ae92b99757/"
            "MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv"
        ),
        "bytes": 3062332720,
        "raw_name": "MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv",
    },
    2024: {
        "url": (
            "https://data.cms.gov/sites/default/files/2026-05/"
            "b5ebab5a-f490-418a-9bce-4b9f31419356/"
            "PHY_R26_P05_V10_D24_Prov_Svc.csv"
        ),
        "bytes": 3250282192,
        "raw_name": "PHY_R26_P05_V10_D24_Prov_Svc.csv",
    },
}

SOURCE_COLUMNS = (
    "Rndrng_NPI",
    "Rndrng_Prvdr_Last_Org_Name",
    "Rndrng_Prvdr_First_Name",
    "Rndrng_Prvdr_City",
    "Rndrng_Prvdr_State_Abrvtn",
    "Rndrng_Prvdr_Zip5",
    "Rndrng_Prvdr_Type",
    "HCPCS_Cd",
    "Place_Of_Srvc",
    "Tot_Srvcs",
    "Tot_Benes",
    "Avg_Sbmtd_Chrg",
    "Avg_Mdcr_Pymt_Amt",
)

OUTPUT_COLUMNS = (
    "NPI",
    "Name",
    "City",
    "State",
    "ZIP",
    "Specialty",
    "Service count",
    "Beneficiary count",
    "Average charge",
    "Average payment",
    "Charge-to-payment ratio",
    "Top-code share",
    "Growth",
    "Year",
)

CHUNK_ROWS = 100_000
DOWNLOAD_CHUNK = 8 * 1024 * 1024

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
ROLLED_DIR = DATA_DIR / "rolled"


def provider_name(last_org: str, first: str) -> str:
    """Join last-or-org and first name the way a search box would show them."""
    last_org = (last_org or "").strip()
    first = (first or "").strip()
    if last_org and first:
        return f"{last_org}, {first}"
    return last_org or first


def _blank_number(value: str) -> float:
    text = (value or "").strip()
    if text == "":
        return 0.0
    return float(text)


class NpiAccum:
    """Running sums for one rendering NPI across chunks."""

    __slots__ = (
        "name",
        "city",
        "state",
        "zip5",
        "specialty",
        "service_count",
        "beneficiary_count",
        "charge_weight",
        "payment_weight",
        "hcpcs_services",
    )

    def __init__(self) -> None:
        self.name = ""
        self.city = ""
        self.state = ""
        self.zip5 = ""
        self.specialty = ""
        self.service_count = 0.0
        self.beneficiary_count = 0.0
        self.charge_weight = 0.0
        self.payment_weight = 0.0
        self.hcpcs_services: dict[str, float] = defaultdict(float)

    def add(self, row: dict[str, str]) -> None:
        if not self.name and not self.city:
            self.name = provider_name(
                row.get("Rndrng_Prvdr_Last_Org_Name", ""),
                row.get("Rndrng_Prvdr_First_Name", ""),
            )
            self.city = (row.get("Rndrng_Prvdr_City") or "").strip()
            self.state = (row.get("Rndrng_Prvdr_State_Abrvtn") or "").strip()
            self.zip5 = (row.get("Rndrng_Prvdr_Zip5") or "").strip()
            self.specialty = (row.get("Rndrng_Prvdr_Type") or "").strip()
        services = _blank_number(row.get("Tot_Srvcs", ""))
        self.service_count += services
        self.beneficiary_count += _blank_number(row.get("Tot_Benes", ""))
        self.charge_weight += services * _blank_number(row.get("Avg_Sbmtd_Chrg", ""))
        self.payment_weight += services * _blank_number(row.get("Avg_Mdcr_Pymt_Amt", ""))
        code = (row.get("HCPCS_Cd") or "").strip()
        self.hcpcs_services[code] += services

    def finish(self, year: int) -> dict[str, object]:
        services = self.service_count
        if services:
            avg_charge = self.charge_weight / services
            avg_payment = self.payment_weight / services
            top = max(self.hcpcs_services.values()) if self.hcpcs_services else 0.0
            top_share = top / services
        else:
            avg_charge = None
            avg_payment = None
            top_share = None
        if avg_payment:
            ratio = avg_charge / avg_payment
        else:
            ratio = None
        return {
            "NPI": None,
            "Name": self.name,
            "City": self.city,
            "State": self.state,
            "ZIP": self.zip5,
            "Specialty": self.specialty,
            "Service count": services,
            "Beneficiary count": self.beneficiary_count,
            "Average charge": avg_charge,
            "Average payment": avg_payment,
            "Charge-to-payment ratio": ratio,
            "Top-code share": top_share,
            "Growth": None,
            "Year": year,
        }


def read_header_line(csv_path: Path) -> str:
    """Return the header line the reader will use, without inventing columns."""
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        header = handle.readline()
    return header.rstrip("\r\n")


def write_header_file(csv_path: Path, year: int, training_dir: Path | None = None) -> Path:
    """Write the header line this script just read. Does not invent a map."""
    training_dir = training_dir or (DATA_DIR / "training")
    training_dir.mkdir(parents=True, exist_ok=True)
    header_path = training_dir / f"header_{year}.txt"
    header_path.write_text(read_header_line(csv_path) + "\n", encoding="utf-8")
    return header_path


def header_can_roll(header_line: str) -> bool:
    """True when the header line this script wrote contains every source column."""
    names = next(csv.reader([header_line]))
    return all(name in names for name in SOURCE_COLUMNS)


def accumulate_csv(csv_path: Path, chunk_rows: int = CHUNK_ROWS) -> dict[str, NpiAccum]:
    """Read a year CSV in chunks and return one accumulator per Rndrng_NPI.

    Place of service is read so a source row is not treated as a
    provider-year. It is not kept. HCPCS is used only for top-code share.
    """
    accum: dict[str, NpiAccum] = {}
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        missing = [name for name in SOURCE_COLUMNS if name not in header]
        if missing:
            raise ValueError(f"{csv_path.name} is missing columns: {', '.join(missing)}")
        seen = 0
        for row in reader:
            npi = (row.get("Rndrng_NPI") or "").strip()
            if npi == "":
                continue
            bucket = accum.get(npi)
            if bucket is None:
                bucket = NpiAccum()
                accum[npi] = bucket
            bucket.add(row)
            seen += 1
            if chunk_rows and seen % chunk_rows == 0:
                # Rows are folded as they are read. The modulus is the
                # chunk boundary the contract requires; no batch is held.
                continue
    return accum


def growth_rate(current_services: float, prior_services: float | None) -> float | None:
    """Return current / prior - 1, or missing when prior is absent or 0."""
    if prior_services is None or prior_services == 0:
        return None
    return current_services / prior_services - 1


def load_prior_service_counts(rolled_path: Path) -> dict[str, float]:
    """Read only NPI and service count from a prior rolled file. Never writes it."""
    counts: dict[str, float] = {}
    with rolled_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if "NPI" not in (reader.fieldnames or []) or "Service count" not in (reader.fieldnames or []):
            raise ValueError(f"{rolled_path.name} is missing NPI or Service count")
        for row in reader:
            npi = (row.get("NPI") or "").strip()
            if npi == "":
                continue
            text = (row.get("Service count") or "").strip()
            counts[npi] = float(text) if text else 0.0
    return counts


def apply_growth(
    rows: list[dict[str, object]],
    prior_counts: dict[str, float] | None,
) -> list[dict[str, object]]:
    """Set Growth from a prior service-count map. None leaves every Growth missing."""
    if prior_counts is None:
        for row in rows:
            row["Growth"] = None
        return rows
    for row in rows:
        prior = prior_counts.get(str(row["NPI"]))
        services = row["Service count"]
        current = float(services) if services is not None else 0.0
        row["Growth"] = growth_rate(current, prior)
    return rows


def roll_csv(
    csv_path: Path,
    year: int = YEAR,
    chunk_rows: int = CHUNK_ROWS,
    prior_rolled: Path | None = None,
) -> list[dict[str, object]]:
    """Read a year CSV in chunks and return one contract row per Rndrng_NPI."""
    accum = accumulate_csv(csv_path, chunk_rows=chunk_rows)
    rows: list[dict[str, object]] = []
    for npi in sorted(accum):
        finished = accum[npi].finish(year)
        finished["NPI"] = npi
        rows.append(finished)
    prior_counts = load_prior_service_counts(prior_rolled) if prior_rolled else None
    return apply_growth(rows, prior_counts)


def write_rolled(rows: list[dict[str, object]], rolled_dir: Path, year: int = YEAR) -> tuple[Path, Path]:
    """Write the rolled table and a sidecar with its row count and column names."""
    ordered = [row for _npi, row in sorted((str(row["NPI"]), row) for row in rows)]
    return _write_rows(ordered, rolled_dir, year=year)


def write_rolled_accum(
    accum: dict[str, NpiAccum],
    rolled_dir: Path,
    year: int = YEAR,
    prior_counts: dict[str, float] | None = None,
) -> tuple[Path, Path]:
    """Stream one finished row per NPI and write the sidecar only after the file."""
    def _iter():
        for npi in sorted(accum):
            finished = accum[npi].finish(year)
            finished["NPI"] = npi
            prior = None if prior_counts is None else prior_counts.get(npi)
            finished["Growth"] = None if prior_counts is None else growth_rate(
                float(finished["Service count"] or 0.0),
                prior,
            )
            yield finished

    return _write_rows(_iter(), rolled_dir, year=year)


def _write_rows(rows, rolled_dir: Path, year: int) -> tuple[Path, Path]:
    rolled_dir.mkdir(parents=True, exist_ok=True)
    rolled_path = rolled_dir / f"{year}.csv"
    note_path = rolled_dir / f"{year}.note.txt"
    count = 0
    with rolled_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(OUTPUT_COLUMNS), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(_format_row(row))
            count += 1
    columns = ", ".join(OUTPUT_COLUMNS)
    note_path.write_text(
        (
            f"File: {rolled_path.name}\n"
            f"Row count: {count}\n"
            f"Columns: {columns}\n"
        ),
        encoding="utf-8",
    )
    return rolled_path, note_path


def _format_row(row: dict[str, object]) -> dict[str, str]:
    formatted: dict[str, str] = {}
    for name in OUTPUT_COLUMNS:
        value = row.get(name)
        if value is None or value == "":
            formatted[name] = ""
        elif isinstance(value, float):
            formatted[name] = repr(value)
        else:
            formatted[name] = str(value)
    return formatted


def download_csv(url: str, dest: Path, expected_bytes: int) -> int:
    """Stream the CSV to dest with curl and return the received byte count.

    Does not roll the file. A size mismatch is the caller's stop.
    expected_bytes is checked by the caller, not used to truncate the file.
    """
    del expected_bytes
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    subprocess.run(
        [
            "curl.exe",
            "--fail",
            "--location",
            "--output",
            str(dest),
            "--retry",
            "5",
            "--retry-all-errors",
            "--retry-delay",
            "5",
            url,
        ],
        check=True,
    )
    return dest.stat().st_size


def record_size_mismatch(
    rolled_dir: Path,
    expected: int,
    received: int,
    year: int = YEAR,
    counts_path: Path | None = None,
) -> Path:
    """Write both sizes and leave no finished rolled table.

    Also appends both sizes to the expand-counts file. The raw CSV is left
    in place. Callers must not continue after this note is written.
    """
    rolled_dir.mkdir(parents=True, exist_ok=True)
    note = rolled_dir / f"{year}.size.txt"
    note.write_text(
        (
            f"Size mismatch for {year}. Rolled file not finished.\n"
            f"Expected bytes: {expected}\n"
            f"Received bytes: {received}\n"
        ),
        encoding="utf-8",
    )
    counts_path = counts_path or (REPO_ROOT / "data" / "training" / "expand_counts.txt")
    counts_path.parent.mkdir(parents=True, exist_ok=True)
    with counts_path.open("a", encoding="utf-8") as handle:
        handle.write(
            (
                f"size mismatch {year}: expected_bytes={expected} "
                f"received_bytes={received}\n"
            )
        )
    rolled = rolled_dir / f"{year}.csv"
    sidecar = rolled_dir / f"{year}.note.txt"
    if rolled.exists():
        rolled.unlink()
    if sidecar.exists():
        sidecar.unlink()
    return note


def raw_name_for(year: int, url: str) -> str:
    known = YEAR_FILES.get(year)
    if known and known["url"] == url:
        return str(known["raw_name"])
    return f"{year}_Prov_Svc.csv"


def prior_rolled_path(year: int, rolled_dir: Path) -> Path | None:
    """Return the previous year's rolled file when it exists. Never creates it.

    2013 is the first year of this file family, so it has no prior. 2014–2018
    join the year just written when that file is already on disk. Later years
    keep the same year-minus-one rule.
    """
    if year <= 2013:
        return None
    candidate = rolled_dir / f"{year - 1}.csv"
    if candidate.is_file():
        return candidate
    return None


def register_year(year: int, url: str, expected_bytes: int) -> None:
    """Add one year to YEAR_FILES only while that year is running.

    Years already listed keep their opened URL, byte count, and raw name.
    """
    if year in YEAR_FILES:
        return
    raw_name = url.rstrip("/").rsplit("/", 1)[-1]
    YEAR_FILES[year] = {
        "url": url,
        "bytes": expected_bytes,
        "raw_name": raw_name,
    }


def append_expand_count(line: str, counts_path: Path | None = None) -> Path:
    """Append one count line before the next step starts."""
    path = counts_path or (DATA_DIR / "training" / "expand_counts.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line if line.endswith("\n") else line + "\n")
    return path


def recompute_growth(
    year: int,
    rolled_dir: Path | None = None,
    training_dir: Path | None = None,
) -> int:
    """Rewrite Growth on one rolled year from the prior year's service counts.

    Uses growth_rate and apply_growth. Does not download. Does not touch any
    other year. Returns the non-missing Growth count.
    """
    rolled_dir = rolled_dir or ROLLED_DIR
    training_dir = training_dir or (DATA_DIR / "training")
    current_path = rolled_dir / f"{year}.csv"
    prior_path = prior_rolled_path(year, rolled_dir)
    if prior_path is None:
        raise FileNotFoundError(f"no prior rolled year for {year}")
    prior_counts = load_prior_service_counts(prior_path)
    numeric = {
        "Service count",
        "Beneficiary count",
        "Average charge",
        "Average payment",
        "Charge-to-payment ratio",
        "Top-code share",
    }
    rows: list[dict[str, object]] = []
    with current_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            parsed: dict[str, object] = {}
            for name in OUTPUT_COLUMNS:
                text = (row.get(name) or "").strip()
                if name in numeric:
                    parsed[name] = float(text) if text else None
                elif name == "Year" and text.isdigit():
                    parsed[name] = int(text)
                else:
                    parsed[name] = text
            current_text = (row.get("Service count") or "").strip()
            current = float(current_text) if current_text else 0.0
            npi = (row.get("NPI") or "").strip()
            parsed["Growth"] = growth_rate(current, prior_counts.get(npi))
            rows.append(parsed)
    write_rolled(rows, rolled_dir, year=year)
    filled = sum(1 for row in rows if row.get("Growth") is not None)
    append_expand_count(
        f"non_missing_growth {year}: {filled}",
        training_dir / "expand_counts.txt",
    )
    return filled


def run_year(
    url: str = CSV_URL,
    expected_bytes: int = EXPECTED_BYTES,
    year: int = YEAR,
    raw_dir: Path | None = None,
    rolled_dir: Path | None = None,
    training_dir: Path | None = None,
    delete_raw: bool = True,
) -> Path:
    """Download one year, check the size, roll on a match, then delete the raw CSV.

    A size mismatch writes both sizes and leaves the raw file. It does not
    roll and does not continue. The header line actually read is written
    before the roll. If that header cannot be rolled, the run stops and the
    raw file stays.
    """
    raw_dir = raw_dir or (DATA_DIR / "raw")
    rolled_dir = rolled_dir or ROLLED_DIR
    training_dir = training_dir or (DATA_DIR / "training")
    register_year(year, url, expected_bytes)
    raw_path = raw_dir / raw_name_for(year, url)
    print(f"year={year}", flush=True)
    print(f"url={url}", flush=True)
    print(f"expected_bytes={expected_bytes}", flush=True)
    received = download_csv(url, raw_path, expected_bytes)
    print(f"received_bytes={received}", flush=True)
    if received != expected_bytes:
        note = record_size_mismatch(rolled_dir, expected_bytes, received, year)
        print(f"size_mismatch_note={note}", flush=True)
        print(f"raw_kept={raw_path.exists()}", flush=True)
        raise SystemExit(
            f"size mismatch: expected {expected_bytes}, received {received}"
        )
    header_path = write_header_file(raw_path, year, training_dir)
    header_line = header_path.read_text(encoding="utf-8").rstrip("\r\n")
    print(f"header={header_path}", flush=True)
    if not header_can_roll(header_line):
        raise SystemExit(
            f"cannot roll the header just written for {year}: {header_path}"
        )
    accum = accumulate_csv(raw_path)
    prior_path = prior_rolled_path(year, rolled_dir)
    prior_counts = load_prior_service_counts(prior_path) if prior_path else None
    rolled_path, note_path = write_rolled_accum(
        accum,
        rolled_dir,
        year=year,
        prior_counts=prior_counts,
    )
    provider_rows = int(note_path.read_text(encoding="utf-8").split("Row count: ")[1].splitlines()[0])
    growth_filled = 0
    if prior_counts is not None:
        with rolled_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            growth_filled = sum(1 for row in reader if (row.get("Growth") or "").strip() != "")
    count_line = f"provider_rows {year}: {provider_rows}"
    if prior_counts is not None:
        count_line += f"\nnon_missing_growth {year}: {growth_filled}"
    append_expand_count(count_line, training_dir / "expand_counts.txt")
    if delete_raw:
        raw_path.unlink()
    print(f"rolled={rolled_path}", flush=True)
    print(f"provider_rows={provider_rows}", flush=True)
    print(f"raw_deleted={not raw_path.exists()}", flush=True)
    return rolled_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download one CMS provider-and-service year and roll it."
    )
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--bytes", type=int, required=True, dest="expected_bytes")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    rolled = run_year(
        url=args.url,
        expected_bytes=args.expected_bytes,
        year=args.year,
    )
    print(rolled)


if __name__ == "__main__":
    main()

"""Join LEIE exclusions to rolled provider-years and count fraud labels.

A provider-year is one row of a rolled file. It is positive only when its
NPI matches a 10-digit LEIE NPI whose EXCLTYPE is 1128a1, 1128a3, 1128b6,
or 1128b7, and whose exclusion year (the YYYY of EXCLDATE) is after that
row's billing year. An NPI with more than one qualifying exclusion uses
the earliest exclusion year, and the provider-year is counted once.
"""

from __future__ import annotations

import csv
from pathlib import Path

from scripts.count_leie import FRAUD_EXCLTYPES

REPO_ROOT = Path(__file__).resolve().parents[1]
LEIE_PATH = REPO_ROOT / "data" / "training" / "UPDATED.csv"
ROLLED_DIR = REPO_ROOT / "data" / "rolled"
COUNT_PATH = REPO_ROOT / "data" / "training" / "fraud_provider_year_count.txt"
BILLING_YEARS = (2019, 2020, 2021, 2022, 2023)

REQUIRED_LEIE_COLUMNS = ("NPI", "EXCLTYPE", "EXCLDATE")
REQUIRED_ROLLED_COLUMNS = ("NPI", "Year")


def is_ten_digit_npi(value: str) -> bool:
    """True when value is exactly ten digits. Zero and blanks are not NPIs."""
    return len(value) == 10 and value.isdigit()


def exclusion_year(excldate: str) -> int | None:
    """Return the YYYY of an eight-digit YYYYMMDD date, or None."""
    if len(excldate) != 8 or not excldate.isdigit():
        return None
    return int(excldate[:4])


def is_positive_label(billing_year: int, matched_exclusion_year: int | None) -> bool:
    """Positive only when a qualifying exclusion year is after the billing year.

    Callers pass the earliest qualifying exclusion year for the matched NPI,
    or None when the NPI has no qualifying LEIE row. Same-year and earlier
    exclusions are not positive.
    """
    if matched_exclusion_year is None:
        return False
    return matched_exclusion_year > billing_year


def earliest_exclusion_years(leie_path: Path) -> dict[str, int]:
    """Map each 10-digit NPI to its earliest qualifying exclusion year.

    Qualifying rows have EXCLTYPE in the four locked codes and an eight-digit
    EXCLDATE. Other codes, missing NPIs, and non-10-digit NPIs are dropped.
    A later second exclusion does not replace an earlier one.
    """
    years: dict[str, int] = {}
    with leie_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        missing = [name for name in REQUIRED_LEIE_COLUMNS if name not in header]
        if missing:
            raise ValueError(f"LEIE file is missing columns: {', '.join(missing)}")
        for row in reader:
            excltype = (row.get("EXCLTYPE") or "").strip()
            if excltype not in FRAUD_EXCLTYPES:
                continue
            npi = (row.get("NPI") or "").strip()
            if not is_ten_digit_npi(npi):
                continue
            year = exclusion_year((row.get("EXCLDATE") or "").strip())
            if year is None:
                continue
            previous = years.get(npi)
            if previous is None or year < previous:
                years[npi] = year
    return years


def count_fraud_provider_years(
    rolled_paths: list[Path],
    exclusion_years: dict[str, int],
) -> int:
    """Count rolled rows whose billing year is before that NPI's exclusion year.

    Each rolled row is one provider-year and is counted at most once, even
    when the NPI has more than one qualifying LEIE row.
    """
    total = 0
    for path in rolled_paths:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            header = reader.fieldnames or []
            missing = [name for name in REQUIRED_ROLLED_COLUMNS if name not in header]
            if missing:
                raise ValueError(f"{path.name} is missing columns: {', '.join(missing)}")
            for row in reader:
                npi = (row.get("NPI") or "").strip()
                year_text = (row.get("Year") or "").strip()
                if not year_text.isdigit():
                    continue
                billing_year = int(year_text)
                if is_positive_label(billing_year, exclusion_years.get(npi)):
                    total += 1
    return total


TRAINING_YEARS = tuple(range(2013, 2024))
DEMO_NPIS = frozenset({"1124725817", "1639879034"})
TRAINING_PATH = REPO_ROOT / "data" / "training" / "physician_2013_2023.csv"
EXPAND_COUNTS_PATH = REPO_ROOT / "data" / "training" / "expand_counts.txt"

# Columns copied from a rolled provider-year. Exclusion type and year are
# attached only so a later check can confirm the positive rule. They are
# not model features.
TRAINING_COLUMNS = (
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
    "label",
    "EXCLTYPE",
    "exclusion_year",
)


def exclusion_type_and_year(leie_path: Path) -> dict[str, tuple[str, int]]:
    """Map each 10-digit NPI to the EXCLTYPE of its earliest qualifying exclusion.

    Same drop rules as earliest_exclusion_years. The type is the type on the
    earliest qualifying row, so a later second code does not replace it.
    """
    chosen: dict[str, tuple[str, int]] = {}
    with leie_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        missing = [name for name in REQUIRED_LEIE_COLUMNS if name not in header]
        if missing:
            raise ValueError(f"LEIE file is missing columns: {', '.join(missing)}")
        for row in reader:
            excltype = (row.get("EXCLTYPE") or "").strip()
            if excltype not in FRAUD_EXCLTYPES:
                continue
            npi = (row.get("NPI") or "").strip()
            if not is_ten_digit_npi(npi):
                continue
            year = exclusion_year((row.get("EXCLDATE") or "").strip())
            if year is None:
                continue
            previous = chosen.get(npi)
            if previous is None or year < previous[1]:
                chosen[npi] = (excltype, year)
    return chosen


def write_training_file(
    leie_path: Path = LEIE_PATH,
    rolled_dir: Path = ROLLED_DIR,
    training_path: Path = TRAINING_PATH,
    counts_path: Path = EXPAND_COUNTS_PATH,
    billing_years: tuple[int, ...] = TRAINING_YEARS,
    demo_npis: frozenset[str] = DEMO_NPIS,
) -> tuple[int, int]:
    """Join rolled 2013–2023 to UPDATED.csv and write the training file.

    Does not read a 2024 roll. Does not write UPDATED.csv. Demo NPIs are
    dropped. A row is positive only under the four-code later-year rule.
    Writes the fraud-row count for each billing year and the clean-row count
    before any fit. Returns (fraud_rows, clean_rows).
    """
    if 2024 in billing_years:
        raise ValueError("2024 is not a training year")
    rolled_paths = [rolled_dir / f"{year}.csv" for year in billing_years]
    missing = [str(path) for path in rolled_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing rolled files: " + ", ".join(missing))
    chosen = exclusion_type_and_year(leie_path)
    fraud_by_year = {year: 0 for year in billing_years}
    clean_rows = 0
    training_path.parent.mkdir(parents=True, exist_ok=True)
    with training_path.open("w", newline="", encoding="utf-8") as out_handle:
        writer = csv.DictWriter(out_handle, fieldnames=list(TRAINING_COLUMNS), extrasaction="ignore")
        writer.writeheader()
        for year, path in zip(billing_years, rolled_paths):
            with path.open(newline="", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    npi = (row.get("NPI") or "").strip()
                    if npi in demo_npis:
                        continue
                    year_text = (row.get("Year") or "").strip()
                    if not year_text.isdigit() or int(year_text) != year:
                        continue
                    match = chosen.get(npi)
                    matched_year = match[1] if match else None
                    positive = is_positive_label(year, matched_year)
                    written = {name: (row.get(name) or "") for name in TRAINING_COLUMNS}
                    written["NPI"] = npi
                    written["Year"] = year_text
                    written["label"] = "1" if positive else "0"
                    if positive and match is not None:
                        written["EXCLTYPE"] = match[0]
                        written["exclusion_year"] = str(match[1])
                        fraud_by_year[year] += 1
                    else:
                        written["EXCLTYPE"] = ""
                        written["exclusion_year"] = ""
                        clean_rows += 1
                    writer.writerow(written)
    fraud_rows = sum(fraud_by_year.values())
    lines = [f"fraud_rows {year}: {fraud_by_year[year]}" for year in billing_years]
    lines.append(f"training_fraud_rows: {fraud_rows}")
    lines.append(f"training_clean_rows: {clean_rows}")
    counts_path.parent.mkdir(parents=True, exist_ok=True)
    with counts_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return fraud_rows, clean_rows


def write_count_file(
    leie_path: Path = LEIE_PATH,
    rolled_dir: Path = ROLLED_DIR,
    count_path: Path = COUNT_PATH,
    billing_years: tuple[int, ...] = BILLING_YEARS,
) -> int:
    """Join the saved LEIE file to the named rolled years and write the count."""
    rolled_paths = [rolled_dir / f"{year}.csv" for year in billing_years]
    missing = [str(path) for path in rolled_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing rolled files: " + ", ".join(missing))
    total = count_fraud_provider_years(
        rolled_paths,
        earliest_exclusion_years(leie_path),
    )
    year_list = ", ".join(str(year) for year in billing_years)
    count_path.write_text(
        (
            "Fraud provider-years in rolled "
            f"{year_list} whose NPI matches a 10-digit LEIE NPI with "
            "EXCLTYPE in 1128a1, 1128a3, 1128b6, 1128b7 and an exclusion "
            f"year after the billing year: {total}\n"
        ),
        encoding="utf-8",
    )
    return total


def main() -> None:
    total = write_count_file()
    print(total)


if __name__ == "__main__":
    main()

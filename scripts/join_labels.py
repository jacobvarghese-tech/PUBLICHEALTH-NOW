


from __future__ import annotations

import csv
from pathlib import Path

FRAUD_EXCLTYPES = frozenset({"1128a1", "1128a3", "1128b6", "1128b7"})

REPO_ROOT = Path(__file__).resolve().parents[1]
LEIE_PATH = REPO_ROOT / "data" / "training" / "UPDATED.csv"
ROLLED_DIR = REPO_ROOT / "data" / "rolled"
COUNT_PATH = REPO_ROOT / "data" / "training" / "fraud_provider_year_count.txt"
BILLING_YEARS = (2019, 2020, 2021, 2022, 2023)

REQUIRED_LEIE_COLUMNS = ("NPI", "EXCLTYPE", "EXCLDATE")
REQUIRED_ROLLED_COLUMNS = ("NPI", "Year")


def is_ten_digit_npi(value: str) -> bool:
    
    return len(value) == 10 and value.isdigit()


def exclusion_year(excldate: str) -> int | None:
    
    if len(excldate) != 8 or not excldate.isdigit():
        return None
    return int(excldate[:4])


def is_positive_label(billing_year: int, matched_exclusion_year: int | None) -> bool:


    if matched_exclusion_year is None:
        return False
    return matched_exclusion_year > billing_year


def earliest_exclusion_years(leie_path: Path) -> dict[str, int]:


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

"""Build an NPI to sex-code lookup from the October 2026 NPPES ZIP.

The 2013-2015 CMS physician headers on disk have no gender column.
This script reads the dissemination ZIP, writes the header it finds,
and keeps NPI plus the sex-code column. Codes stay M, F, or blank.
"""

from __future__ import annotations

import argparse
import csv
import io
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NPPES_DIR = REPO_ROOT / "data" / "nppes"
DEFAULT_ZIP = NPPES_DIR / "NPPES_Data_Dissemination_October_2026_V2.zip"
HEADER_PATH = NPPES_DIR / "nppes_header.txt"
LOOKUP_PATH = NPPES_DIR / "npi_sex.csv"
NOTE_PATH = NPPES_DIR / "npi_sex.note.txt"

ZIP_URL = (
    "https://download.cms.gov/nppes/NPPES_Data_Dissemination_October_2026_V2.zip"
)
FILE_DATE = "2026-10-12"
LISTED_SIZE = "1,106.00 MB"

NPI_NAMES = ("NPI",)
SEX_NAMES = (
    "Provider Sex Code",
    "Provider Gender Code",
    "Entity Sex Code",
)


def pick_column(fieldnames: list[str], candidates: tuple[str, ...]) -> str | None:
    folded = {name.casefold(): name for name in fieldnames}
    for candidate in candidates:
        found = folded.get(candidate.casefold())
        if found:
            return found
    return None


def main_csv_name(archive: zipfile.ZipFile) -> str:
    names = [
        info.filename
        for info in archive.infolist()
        if info.filename.lower().endswith(".csv") and not info.is_dir()
    ]
    if not names:
        raise ValueError("ZIP contains no CSV")
    # The monthly dissemination has one large provider file and small
    # other-name files. The provider file is the largest CSV.
    return max(names, key=lambda name: archive.getinfo(name).file_size)


def write_lookup(zip_path: Path) -> dict[str, int]:
    NPPES_DIR.mkdir(parents=True, exist_ok=True)
    counts = {"rows": 0, "M": 0, "F": 0, "blank": 0, "other": 0}
    with zipfile.ZipFile(zip_path) as archive:
        csv_name = main_csv_name(archive)
        with archive.open(csv_name) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(text)
            fieldnames = list(reader.fieldnames or [])
            HEADER_PATH.write_text(",".join(fieldnames) + "\n", encoding="utf-8")
            npi_col = pick_column(fieldnames, NPI_NAMES)
            sex_col = pick_column(fieldnames, SEX_NAMES)
            if npi_col is None or sex_col is None:
                raise ValueError(
                    f"{csv_name} header has no usable NPI or sex column. "
                    f"Wrote {HEADER_PATH.name}."
                )
            with LOOKUP_PATH.open("w", newline="", encoding="utf-8") as out:
                writer = csv.writer(out)
                writer.writerow(["NPI", "nppes_provider_gender"])
                for row in reader:
                    npi = (row.get(npi_col) or "").strip()
                    if len(npi) != 10 or not npi.isdigit() or npi == "0000000000":
                        continue
                    sex = (row.get(sex_col) or "").strip().upper()
                    if sex not in ("M", "F"):
                        if sex == "":
                            counts["blank"] += 1
                        else:
                            counts["other"] += 1
                        sex = ""
                    else:
                        counts[sex] += 1
                    writer.writerow([npi, sex])
                    counts["rows"] += 1
    note = "\n".join(
        [
            f"Source: {ZIP_URL}",
            f"Listed file date: {FILE_DATE}",
            f"Listed size: {LISTED_SIZE}",
            f"ZIP bytes: {zip_path.stat().st_size}",
            f"CSV inside ZIP: {csv_name}",
            f"NPI column: {npi_col}",
            f"Sex column: {sex_col}",
            "Mapped to: nppes_provider_gender",
            "Codes kept: M, F, blank. No unknown code was invented.",
            "Snapshot is later than the 2013-2015 physician files.",
            f"Rows: {counts['rows']}",
            f"M: {counts['M']}",
            f"F: {counts['F']}",
            f"Blank: {counts['blank']}",
            f"Other codes blanked: {counts['other']}",
            "",
        ]
    )
    NOTE_PATH.write_text(note, encoding="utf-8")
    counts["csv_name"] = csv_name
    counts["npi_col"] = npi_col
    counts["sex_col"] = sex_col
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    args = parser.parse_args()
    if not args.zip.is_file():
        raise SystemExit(f"Missing ZIP: {args.zip}")
    counts = write_lookup(args.zip)
    print(
        f"rows={counts['rows']} M={counts['M']} F={counts['F']} "
        f"blank={counts['blank']} other={counts['other']} "
        f"sex_column={counts['sex_col']}"
    )


if __name__ == "__main__":
    main()

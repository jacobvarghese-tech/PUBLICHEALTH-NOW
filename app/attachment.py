


from __future__ import annotations

import csv
import io
import re
import statistics
from email.parser import BytesParser
from email.policy import default
from pathlib import Path

from app.page_logic import FEATURE_FIELDS, YEARS, is_blank

MAX_BYTES = 48 * 1024 * 1024
CMS_COLUMNS = {
    "npi": "Rndrng_NPI",
    "specialty": "Rndrng_Prvdr_Type",
    "gender": "Rndrng_Prvdr_Gndr",
    "line_srvc_cnt": "Tot_Srvcs",
    "bene_unique_cnt": "Tot_Benes",
    "bene_day_srvc_cnt": "Tot_Bene_Day_Srvcs",
    "average_submitted_chrg_amt": "Avg_Sbmtd_Chrg",
    "average_medicare_payment_amt": "Avg_Mdcr_Pymt_Amt",
}
PAPER_COLUMNS = {
    "npi": "npi",
    "specialty": "provider_type",
    "gender": "nppes_provider_gender",
    "line_srvc_cnt": "line_srvc_cnt",
    "bene_unique_cnt": "bene_unique_cnt",
    "bene_day_srvc_cnt": "bene_day_srvc_cnt",
    "average_submitted_chrg_amt": "average_submitted_chrg_amt",
    "average_medicare_payment_amt": "average_medicare_payment_amt",
}
MEASURES = (
    "line_srvc_cnt",
    "bene_unique_cnt",
    "bene_day_srvc_cnt",
    "average_submitted_chrg_amt",
    "average_medicare_payment_amt",
)
SUMMARY_NAMES = ("mean", "sum", "median", "std", "min", "max")
NPI_PATTERN = re.compile(r"\d{10}")
SEX_PATH = Path(__file__).resolve().parents[1] / "data" / "nppes" / "npi_sex.csv"


def parse_upload(content_type: str, body: bytes) -> tuple[str, bytes]:
    

    if len(body) > MAX_BYTES:
        raise ValueError("the attachment is larger than 48 MB")
    if "multipart/form-data" not in (content_type or "").lower():
        raise ValueError("choose an attachment")
    header = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
    message = BytesParser(policy=default).parsebytes(header + body)
    if not message.is_multipart():
        raise ValueError("choose an attachment")
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if name != "attachment":
            continue
        filename = part.get_filename() or ""
        payload = part.get_payload(decode=True) or b""
        if payload == b"":
            raise ValueError("the attachment is empty")
        if len(payload) > MAX_BYTES:
            raise ValueError("the attachment is larger than 48 MB")
        return filename, payload
    raise ValueError("choose an attachment")


def clean_npi(value: object) -> str:
    text = "" if is_blank(value) else str(value)
    digits = "".join(character for character in text if character.isdigit())
    if len(digits) != 10 or digits == "0000000000":
        raise ValueError("enter a 10-digit NPI")
    return digits


def gender_for_npi(npi: str, sex_path: Path = SEX_PATH) -> str:



    if not sex_path.is_file():
        return ""
    with sex_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            row_npi = "".join(character for character in str(row.get("NPI") or "") if character.isdigit())
            if row_npi < npi:
                continue
            if row_npi > npi:
                break
            gender = str(row.get("nppes_provider_gender") or "").strip().upper()
            return gender if gender in ("M", "F") else ""
    return ""


def clean_year(value: object) -> int | None:
    text = "" if is_blank(value) else str(value).strip()
    if text == "":
        return None
    if text not in {str(year) for year in YEARS}:
        raise ValueError("year must be 2018 through 2024")
    return int(text)


def _number(value: object) -> float | None:
    text = "" if value is None else str(value).strip().strip('"')
    if text == "":
        return None
    cleaned = text.replace(",", "").replace("$", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return format(value, "f").rstrip("0").rstrip(".")


def _summaries(values: list[float]) -> dict[str, str]:
    if not values:
        return {name: "" for name in SUMMARY_NAMES}
    std = statistics.stdev(values) if len(values) > 1 else 0.0
    packed = {
        "mean": statistics.fmean(values),
        "sum": sum(values),
        "median": statistics.median(values),
        "std": std,
        "min": min(values),
        "max": max(values),
    }
    return {name: _format_number(number) for name, number in packed.items()}


def _header_map(header: list[str]) -> dict[str, str] | None:
    names = {name.strip().strip('"') for name in header}
    if CMS_COLUMNS["npi"] in names and CMS_COLUMNS["line_srvc_cnt"] in names:
        return dict(CMS_COLUMNS)
    if PAPER_COLUMNS["npi"] in names and PAPER_COLUMNS["line_srvc_cnt"] in names:
        return dict(PAPER_COLUMNS)
    if "npi" in {name.lower() for name in names}:
        folded = {name.lower(): name for name in names}
        return {key: folded.get(column.lower(), column) for key, column in PAPER_COLUMNS.items()}
    return None


def _row_year(row: dict, header: list[str]) -> str:
    for name in header:
        if name.strip().lower() in ("year", "year_key"):
            return str(row.get(name) or "").strip()
    return ""


def roll_provider_rows(text: str, npi: str, year: int | None) -> dict[str, str] | None:
    

    sample = text.lstrip("\ufeff")
    if not sample or sample[0] not in ("R", "n", "N", '"'):
        return None
    reader = csv.DictReader(io.StringIO(sample))
    if not reader.fieldnames:
        return None
    columns = _header_map(list(reader.fieldnames))
    if columns is None:
        return None
    buckets: dict[str, list[float]] = {name: [] for name in MEASURES}
    specialty = ""
    gender = ""
    seen = 0
    for row in reader:
        row_npi = "".join(character for character in str(row.get(columns["npi"]) or "") if character.isdigit())
        if row_npi != npi:
            continue
        row_year = _row_year(row, list(reader.fieldnames))
        if year is not None and row_year not in ("", str(year)):
            continue
        seen += 1
        specialty = specialty or str(row.get(columns["specialty"]) or "").strip().strip('"')
        gender = gender or str(row.get(columns["gender"]) or "").strip().strip('"')
        for measure in MEASURES:
            value = _number(row.get(columns[measure]))
            if value is not None:
                buckets[measure].append(value)
    if seen == 0:
        return None
    fields = {name: None for name in FEATURE_FIELDS}
    fields["Specialty"] = specialty or None
    gender = gender.strip().upper()
    if gender not in ("M", "F"):
        gender = gender_for_npi(npi)
    fields["Gender"] = gender or None
    for measure, values in buckets.items():
        packed = _summaries(values)
        for summary, value in packed.items():
            fields[f"{measure}_{summary}"] = value or None
    return fields


def attachment_notes(filename: str, payload: bytes) -> str:
    

    lowered = filename.lower()
    if lowered.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip")):
        return f"Attachment name: {filename}"
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        return f"Attachment name: {filename}"
    if "\x00" in text:
        return f"Attachment name: {filename}"
    clipped = text.strip()
    if len(clipped) > 12000:
        clipped = clipped[:12000]
    return f"Attachment name: {filename}\n{clipped}"


def fields_from_attachment(
    filename: str,
    payload: bytes,
    npi: str,
    year: int | None,
    client=None,
) -> dict[str, str | None]:
    

    from app.extract import extract_fields

    provider = clean_npi(npi)
    notes = attachment_notes(filename, payload)
    rolled = None
    if notes.startswith("Attachment name:") and "\n" in notes:
        rolled = roll_provider_rows(notes.split("\n", 1)[1], provider, year)
    if rolled is not None:
        return rolled
    prompt = (
        f"The provider id is NPI {provider}. "
        "Copy model fields for that provider only. "
        "Ignore every other provider in the attachment. "
        f"{notes}"
    )
    return extract_fields("model", prompt, client=client)

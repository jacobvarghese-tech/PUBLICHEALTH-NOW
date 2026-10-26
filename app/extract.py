


from __future__ import annotations

import json
import os
import re
from typing import Any

from app.page_logic import FEATURE_FIELDS, YEARS, is_blank

API_BASE = "https://api.x.ai/v1"
EXTRACT_MODEL = "grok-4.7"
MISSING_KEY_MESSAGE = "Set XAI_API_KEY on the server, then try again."
MAX_NOTES = 12000

SEARCH_FIELDS = ("query", "year")
MODEL_FIELDS = FEATURE_FIELDS

SEARCH_GUIDE = (
    "query is the provider name, city, or 10-digit NPI to type into search. "
    "year is one of 2018, 2019, 2020, 2021, 2022, 2023, 2024."
)
MODEL_GUIDE = (
    "Specialty is the provider specialty. Gender is M, F, or the word written in the notes. "
    "line_srvc_cnt is services per procedure code. bene_unique_cnt is unique beneficiaries. "
    "bene_day_srvc_cnt is beneficiary service days. average_submitted_chrg_amt is the submitted charge. "
    "average_medicare_payment_amt is the Medicare payment. "
    "Each of those five measures has mean, sum, median, std, min, and max."
)


def extract_schema(kind: str) -> dict[str, Any]:
    if kind == "search":
        properties = {
            "query": {"type": ["string", "null"]},
            "year": {"type": ["string", "null"], "enum": [str(year) for year in YEARS] + [None]},
        }
        required = list(SEARCH_FIELDS)
    elif kind == "model":
        properties = {name: {"type": ["string", "null"]} for name in MODEL_FIELDS}
        required = list(MODEL_FIELDS)
    else:
        raise ValueError(f"unknown extract kind: {kind}")
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def extract_instructions(kind: str) -> str:
    fields = SEARCH_FIELDS if kind == "search" else MODEL_FIELDS
    guide = SEARCH_GUIDE if kind == "search" else MODEL_GUIDE
    names = ", ".join(fields)
    return (
        "Copy only facts that are written in the notes. "
        "Use null for every field the notes do not state. "
        "Do not estimate, average, or invent a number. "
        "Do not say a provider committed fraud. "
        f"Return these fields: {names}. {guide}"
    )


def _clean_text(value: object) -> str | None:
    if is_blank(value):
        return None
    text = str(value).strip()
    return text or None


def _clean_year(value: object) -> str | None:
    text = _clean_text(value)
    if text is None:
        return None
    match = re.search(r"20(?:18|19|2[0-4])", text)
    if match is None:
        return None
    return match.group(0)


def _clean_number(value: object) -> str | None:
    text = _clean_text(value)
    if text is None:
        return None
    cleaned = text.replace(",", "").replace("$", "").replace("%", "")
    try:
        number = float(cleaned)
    except ValueError:
        return None
    if number.is_integer():
        return str(int(number))
    return format(number, "f").rstrip("0").rstrip(".")


def clean_fields(kind: str, raw: object) -> dict[str, str | None]:
    source = raw if isinstance(raw, dict) else {}
    if kind == "search":
        return {
            "query": _clean_text(source.get("query")),
            "year": _clean_year(source.get("year")),
        }
    cleaned: dict[str, str | None] = {}
    for name in MODEL_FIELDS:
        if name in ("Specialty", "Gender"):
            cleaned[name] = _clean_text(source.get(name))
        else:
            cleaned[name] = _clean_number(source.get(name))
    return cleaned


def parse_model_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("the model did not return fields")
    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("the model did not return fields")
    return parsed


def output_text(response: object) -> str:
    text = getattr(response, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text
    chunks: list[str] = []
    for item in getattr(response, "output", None) or []:
        for block in getattr(item, "content", None) or []:
            piece = getattr(block, "text", None)
            if isinstance(piece, str):
                chunks.append(piece)
    return "\n".join(chunks)


def extract_fields(kind: str, notes: str, client: Any | None = None) -> dict[str, str | None]:
    

    if kind not in ("search", "model"):
        raise ValueError(f"unknown extract kind: {kind}")
    clipped = (notes or "").strip()
    if clipped == "":
        raise ValueError("paste the notes first")
    if len(clipped) > MAX_NOTES:
        clipped = clipped[:MAX_NOTES]
    if client is None:
        key = os.getenv("XAI_API_KEY")
        if not key:
            raise RuntimeError(MISSING_KEY_MESSAGE)
        from openai import OpenAI

        client = OpenAI(api_key=key, base_url=API_BASE)
    response = client.responses.create(
        model=EXTRACT_MODEL,
        input=[
            {"role": "system", "content": extract_instructions(kind)},
            {"role": "user", "content": clipped},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": f"{kind}_fields",
                "schema": extract_schema(kind),
                "strict": True,
            }
        },
    )
    return clean_fields(kind, parse_model_json(output_text(response)))

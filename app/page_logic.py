


from __future__ import annotations



PAPER_NUMERIC = (
    "line_srvc_cnt_mean",
    "line_srvc_cnt_sum",
    "line_srvc_cnt_median",
    "line_srvc_cnt_std",
    "line_srvc_cnt_min",
    "line_srvc_cnt_max",
    "bene_unique_cnt_mean",
    "bene_unique_cnt_sum",
    "bene_unique_cnt_median",
    "bene_unique_cnt_std",
    "bene_unique_cnt_min",
    "bene_unique_cnt_max",
    "bene_day_srvc_cnt_mean",
    "bene_day_srvc_cnt_sum",
    "bene_day_srvc_cnt_median",
    "bene_day_srvc_cnt_std",
    "bene_day_srvc_cnt_min",
    "bene_day_srvc_cnt_max",
    "average_submitted_chrg_amt_mean",
    "average_submitted_chrg_amt_sum",
    "average_submitted_chrg_amt_median",
    "average_submitted_chrg_amt_std",
    "average_submitted_chrg_amt_min",
    "average_submitted_chrg_amt_max",
    "average_medicare_payment_amt_mean",
    "average_medicare_payment_amt_sum",
    "average_medicare_payment_amt_median",
    "average_medicare_payment_amt_std",
    "average_medicare_payment_amt_min",
    "average_medicare_payment_amt_max",
)
FEATURE_FIELDS = ("Specialty", "Gender", *PAPER_NUMERIC)

RESEMBLANCE = "Resembles later exclusions."
YEARS = (2018, 2019, 2020, 2021, 2022, 2023, 2024)
DEMO_NPIS = ("1124725817", "1639879034")


def is_blank(value: object) -> bool:
    
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def missing_features(row: dict) -> list[str]:
    
    return [name for name in FEATURE_FIELDS if is_blank(row.get(name))]


def is_incomplete(row: dict) -> bool:


    if row.get("stored_score") is True and not is_blank(row.get("score")):
        return False
    return any(is_blank(row.get(name)) for name in PAPER_NUMERIC)


def search_rows(rows: list[dict], query: str, limit: int = 20) -> list[dict]:


    needle = (query or "").strip().lower()
    if needle == "":
        return []
    found: list[dict] = []
    for row in rows:
        name = str(row.get("Name") or "").lower()
        city = str(row.get("City") or "").lower()
        npi = str(row.get("NPI") or "").lower()
        if needle in name or needle in city or needle in npi:
            found.append(row)
            if len(found) >= limit:
                break
    return found


def percentile_result(score: float | None, scores: list[float]) -> dict:


    if not scores or score is None:
        return {
            "percentile": None,
            "outside_top_1": None,
            "outside_top_5": None,
            "at_or_below": 0,
            "n": len(scores),
            "cutoff": None,
        }
    cutoff = _percentile_cutoff(scores, 99)
    at_or_below = sum(1 for value in scores if value <= score)
    percentile = 100.0 * at_or_below / len(scores)
    return {
        "percentile": percentile,
        "outside_top_1": score < cutoff,
        "outside_top_5": score < _percentile_cutoff(scores, 95),
        "at_or_below": at_or_below,
        "n": len(scores),
        "cutoff": cutoff,
    }


def _percentile_cutoff(scores: list[float], percentile: float) -> float:
    
    ordered = sorted(float(value) for value in scores)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (percentile / 100.0)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def format_percentile(result: dict, year: int | None = None) -> str:
    if year is None:
        year = 2024
    percentile = result.get("percentile")
    if percentile is None:
        return f"No {year} scores are loaded, so this percentile is not available."
    text = (
        f"{year} percentile: {percentile:.6f} "
        f"({result['at_or_below']}/{result['n']})."
    )
    if result.get("outside_top_5"):
        text += " This result is outside the top 5%."
    return text

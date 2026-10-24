"""Pure helpers for the Medicare Fraud Flagger page.

These functions do not open the rolled files or the model. The server calls
them after it has rows and scores in memory.
"""

from __future__ import annotations

# Specialty, gender, and the thirty paper numeric summaries. A blank in any
# of these leaves the row incomplete. Name, city, state, and ZIP are not features.
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

RESEMBLANCE = "A high score is a resemblance, not a fraud finding."
YEARS = (2018, 2019, 2020, 2021, 2022, 2023, 2024)
DEMO_NPIS = ("1124725817", "1639879034")


def is_blank(value: object) -> bool:
    """True when a feature was left empty. Zero is a real value."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def missing_features(row: dict) -> list[str]:
    """Feature names that are blank. Blanks are not filled in."""
    return [name for name in FEATURE_FIELDS if is_blank(row.get(name))]


def is_incomplete(row: dict) -> bool:
    """A typed row is incomplete when specialty, gender, or a paper summary is blank.

    A stored row that already has a forest score keeps that score. Gender may
    stay blank, as it does for an organization with no NPPES sex. The blank
    is still listed in missing_features, and a typed blank is still incomplete.
    """
    if row.get("stored_score") is True and not is_blank(row.get("score")):
        return False
    return bool(missing_features(row))


def search_rows(rows: list[dict], query: str, limit: int = 20) -> list[dict]:
    """Return stored rows whose name, city, or NPI contains the query.

    Matching is case-insensitive. An empty query returns no rows. Name,
    city, and NPI are each enough on their own.
    """
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
    """Rank one score among all scores. Higher scores get a higher percentile.

    The percentile is 100 times the share of scores less than or equal to
    this score. The top-5% cutoff is the 95th percentile of all scores,
    using the same linear interpolation as numpy.percentile. A tie at that
    cutoff counts as inside the top 5%. An empty score list does not divide
    by zero.
    """
    if not scores or score is None:
        return {
            "percentile": None,
            "outside_top_5": None,
            "at_or_below": 0,
            "n": len(scores),
            "cutoff": None,
        }
    cutoff = _percentile_cutoff(scores, 95)
    at_or_below = sum(1 for value in scores if value <= score)
    percentile = 100.0 * at_or_below / len(scores)
    return {
        "percentile": percentile,
        "outside_top_5": score < cutoff,
        "at_or_below": at_or_below,
        "n": len(scores),
        "cutoff": cutoff,
    }


def _percentile_cutoff(scores: list[float], percentile: float) -> float:
    """Linear percentile. Same values as numpy.percentile's default method."""
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
    """Page text for one year's rank, including the outside-top-5% line."""
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

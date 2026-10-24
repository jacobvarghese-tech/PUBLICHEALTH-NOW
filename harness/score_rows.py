"""Seed harness. The parent calls score_rows. The agent may rewrite this file.

frozen scores are already computed. tree_score is the shallow XGBoost
probability. paper_score is the page-forest score. Both are floats.
features holds the eight billing fields and nothing else.

Return one float per row, same order, same length. Higher means more
resemblance to later fraud-type exclusions. Do not say the firm committed
fraud. Do not import a module. Do not open a file. Do not read NPI, name,
city, state, ZIP, or year.
"""


def score_rows(rows: list[dict]) -> list[float]:
    """Return the page-forest score. The shallow tree is available and unused."""
    return [float(row["paper_score"]) for row in rows]

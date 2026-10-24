"""Seed island. The parent calls score_rows. An island may rewrite this file.

paper_score, secondary_score, zero_cutoff, and vote_step are already computed.
Return one float per row, same order, same length. Higher means more
resemblance to later fraud-type exclusions. Do not say the firm committed
fraud. Do not import a module. Do not open a file. Do not read NPI, name,
city, state, ZIP, or year.
"""


def score_rows(rows):
    """Keep a page-forest score above zero. Promote a zero when the second score clears the cutoff."""
    out = []
    for row in rows:
        paper = float(row["paper_score"])
        if paper > 0.0:
            out.append(paper)
            continue
        secondary = float(row["secondary_score"])
        cutoff = float(row["zero_cutoff"])
        step = float(row["vote_step"])
        if secondary >= cutoff and cutoff != float("inf"):
            out.append(step)
        else:
            out.append(0.0)
    return out

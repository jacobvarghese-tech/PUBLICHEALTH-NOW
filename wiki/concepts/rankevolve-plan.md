---
type: concept
title: RankEvolve plan
updated: 2026-10-22
tags: [app, model, planning]
sources:
  - https://arxiv.org/abs/2602.16932
  - https://arxiv.org/html/2602.16932v1
  - https://github.com/jmnian/RankEvolve
  - models/harness_rank_note.txt
  - models/xgb_shallow.json
  - scripts/train.py
---

# RankEvolve plan

Filed 2026-10-22. Do this after school. Do not start it from this page. The page model stays.

The prompt harness lost. On the same 288-row 2024 subsample it caught 1 of 48 fraud rows in the top 1 percent. The shallow tree caught 3 of 48. That note is `models/harness_rank_note.txt`. Another instruction rewrite is not this plan.

RankEvolve is the shape that fits. It evolves a scoring function as Python, grades that function on a list, and scores a held-out set only after search stops. Paper: https://arxiv.org/abs/2602.16932. The paper's own repo is https://github.com/jmnian/RankEvolve. Do not clone it and do not run `uv sync`. Its evaluator is a search-engine index. This app's evaluator is the fraud list.

## What gets written

One new script, `scripts/rank_evolve.py`. One note, `models/rank_evolve_note.txt`. One kept function, `models/rank_evolve_score.py`. None of those files exist yet.

The candidate is one function:

```python
def score_row(features: dict, tree_score: float) -> float:
    ...
```

`features` holds the eight billing fields. `tree_score` is the frozen shallow XGBoost score for that row. The function returns one number. Higher means more resemblance to later fraud-type exclusions. It must not say the firm committed fraud.

The seed function returns `tree_score` and changes nothing. A mutation may add one capped adjustment. The absolute adjustment is at most 0.15. A function that imports a module, opens a file, or reads NPI, name, city, state, ZIP, or year is rejected before it is scored.

## The three trials

| Trial | Years | Who may read it | Fraud rows |
| --- | --- | --- | --- |
| Search | 2019–2022 | The proposer, after each list score | Part of the 1,270 |
| Selection | 2023 | The keep rule only | 93 |
| Confirmation | 2024 | Nobody until the search stops | 48 |

Sample clean rows at 9 per fraud row, seed 1, inside the search file and the selection file. Drop demo NPIs `1124725817` and `1639879034`. The confirmation file is every 2024 fraud row plus 5 clean rows per fraud row, the same subsample as `models/harness_rank_note.txt`, so the new score can sit beside 1/48 and 3/48.

A row is positive only when the exclusion year is after the billing year and `EXCLTYPE` is `1128a1`, `1128a3`, `1128b6`, or `1128b7`.

## Fitness

One number, from the whole list, not from one row:

`fitness = top_1_percent_fraud_count - 0.25 * extra_slice_rows`

`extra_slice_rows` is how many rows sit in the top 1 percent slice beyond 1 percent of the list. A function that piles rows into the slice gets a lower fitness even if it catches more fraud rows. This is the app's version of the paper's list metric. The paper uses `0.8 * Recall@100 + 0.2 * nDCG@10` on search datasets. Those datasets are not this repo. Do not copy that formula.

The proposer sees the selection fitness, the top 5 percent count, and the fraud rows that missed, with their eight fields. It does not see 2024.

## Search loop

This is a small copy of the paper's loop, sized for one afternoon. The paper uses 3 islands, a 12 by 12 grid, migration every 20 steps, and programs of about 300 lines. That size is for a search-engine task. This plan uses:

- 2 islands.
- A parent picked from the current island: half the time the best function, half the time a random kept function.
- The proposer also sees the other island's best function and one random kept function.
- Exactly 20 proposals. A rejected proposal still counts. The search does not stop after two quiet rounds.
- A proposal that raises an error is sent back as the next note. It is not kept. The next proposal still runs.
- A proposal is kept only when its selection fitness is strictly higher than the function it was edited from, and the top 1 percent slice holds at most 2 percent of the selection rows.
- After proposal 20, score the best kept function. If none was kept, score the seed. Then score 2024 once.
- The proposer is `grok-4.6` with `reasoning_effort` high. The base URL is `https://api.x.ai/v1`. The key is `XAI_API_KEY`. No student scoring call. The function itself is the scorer.

The paper's MAP-Elites grid and island migration are skipped. Twenty proposals do not fill a 12 by 12 grid. Write that skip in the note.

## After school

1. Create `scripts/rank_evolve.py` with the seed function, the whitelist, and the list fitness. Do not call the API in this step.
2. Score the seed on the 2023 selection file. Record the top 1 percent count and the slice size. If this number is missing, do not start proposals.
3. Run exactly 20 proposals. Do not stop early because a round failed to beat the parent.
4. After proposal 20, score the best kept function once on the 2024 subsample. If none was kept, score the seed. Score the shallow model on those same rows again.
5. Write `models/rank_evolve_note.txt` with `confirm_top1=`, `same_rows_xgboost_top1=`, and `beats_xgboost_on_same_rows=`. Print the 48-event caveat before those shares.

`beats_xgboost_on_same_rows` is true only when the winner's top 1 percent count is higher than the tree's count on those same rows and the slice stays at or under 2 percent of the subsample.

## What this plan does not do

- It does not edit `app/`.
- It does not replace `models/xgb_shallow.json` or `models/paper_forest.joblib`.
- It does not rerun `scripts/harness_rank.py`.
- It does not download a file.
- It does not score the paper forest on the eight-field frame. That model uses a different column set.
- It does not treat a higher one-row score as a win.

The full-year tree figures stay where they are: 11/48 and 18/48 for the shallow model, 19/48 and 48/48 for the paper forest. Those are not the win test. The win test is the same 288-row subsample.

## Unverified

- The RankEvolve GitHub tree was not cloned. The loop above is taken from the paper's HTML, then cut to 2 islands and 20 proposals.
- No opened paper reports a top 1 percent fraud count for a Medicare billing ranker. The fitness formula is a project choice.
- The shallow tree's 3/48 was measured on this subsample on 2026-10-22. The seed step must measure it again before the first proposal.

## Goal prompt

Paste this as one message:

`/goal Do wiki/concepts/rankevolve-plan.md before I get home. Create scripts/rank_evolve.py, models/rank_evolve_score.py, and models/rank_evolve_note.txt. The seed function returns the frozen shallow XGBoost score and changes nothing. A proposal may add one adjustment whose absolute value is at most 0.15. Reject any function that imports a module, opens a file, or reads NPI, name, city, state, ZIP, or year. Score the seed on the 2023 selection file before the first proposal. Then run exactly 20 proposals. A rejected proposal counts. Do not stop after two quiet rounds, a crash, a rate limit, or a function that loses to its parent. Send the error back as the next note and continue until proposal 20 exists. The proposer is grok-4.6 with reasoning_effort high, through https://api.x.ai/v1, using XAI_API_KEY from the environment. Do not print the key. After proposal 20, score the best kept function once on the same 2024 subsample as models/harness_rank_note.txt. If no proposal was kept, score the seed. Score models/xgb_shallow.json on those same rows. Write confirm_top1=, same_rows_xgboost_top1=, and beats_xgboost_on_same_rows= in models/rank_evolve_note.txt. Print the 48-event caveat before those shares. beats_xgboost_on_same_rows is true only when the winner catches more fraud rows in the top 1 percent than the tree on those same rows and the slice holds at most 2 percent of the subsample. Do not edit app/. Do not replace models/xgb_shallow.json or models/paper_forest.joblib. Do not rerun scripts/harness_rank.py. Do not clone a repo. Do not download a file. Finish only when the note has all three lines. A missing line means you are not done.`

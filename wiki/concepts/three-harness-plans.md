---
type: concept
title: Three harness plans
updated: 2026-10-22
tags: [app, model, planning]
sources:
  - wiki/queries/three-harness-plans-prompt.md
  - models/holdout_note.txt
  - models/paper_forest_note.txt
  - scripts/train.py
  - https://otexts.com/fpp3/toolbox.html#sec-tscv
  - https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html
  - https://xgboost.readthedocs.io/en/stable/python/python_api.html
  - https://www.law.cornell.edu/uscode/text/42/1320a-7
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC4738418/
  - https://arxiv.org/html/2305.03403v5
  - https://github.com/automl/CAAFE/blob/main/caafe/run_llm_code.py
  - https://arxiv.org/abs/2503.14434
  - https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html
---

# Three harness plans

Compiled 2026-10-22. The research run that was supposed to write this page was the stock `deep-research` runner, `wf_01a1617174fc77d09a2134d78512041a`. It finished Partial. [[three harness plans prompt]] says that runner caps the split and drops a step that is not itself a verified claim. That is what happened. The report named methods and left the three plans under Unverified. This page is the checklist that run did not write.

A step below is executable. A line under Unverified is not a step. This page does not fit a model and does not edit `app/`. The page model stays until a later session compares a finished note with the saved page score.

One night runs one plan. Do not run all three fits in the same parent. The parent of that night coordinates. It does not fit. It does not score a million-row year inside the search. It does not call an LLM once per 2024 row.

## What every plan shares

Each plan is a loop. Fit on billing years strictly before the grade year. Grade that year. Keep the candidate only when the grade moves. Stop after two grade years in a row with no gain. 2024 is scored once after the stop. It never enters a fit or a grade.

The textbook name for that split is evaluation on a rolling forecasting origin. The training set consists only of observations that occurred prior to the observation that forms the test set. The direct URL `https://otexts.com/fpp3/tscv.html` returned HTTP 403. The same section is `https://otexts.com/fpp3/toolbox.html#sec-tscv`. That page does not mention billing years. Mapping the rule onto 2021, 2022, and 2023 is a project lock.

The grade is the share of that year's fraud rows in the top 1 percent and the top 5 percent of that year's real-mix scores, plus whether the top 1 percent list is short. The XGBoost API page does not name a top-slice metric. Do not take one from that page. `scripts/harness_score.py` already computes this share. Reuse it. Do not invent a second metric.

A row is positive only when its NPI matches a 10-digit NPI on `data/training/UPDATED.csv`, `EXCLTYPE` is `1128a1`, `1128a3`, `1128b6`, or `1128b7`, and the year of `EXCLDATE` is after the billing year. Same-year and earlier exclusions are not positive. 1128(a) is mandatory exclusion. 1128(b) is permissive exclusion. Statute: https://www.law.cornell.edu/uscode/text/42/1320a-7. That page's headings cover those duties. It does not print the tokens `1128(a)(1)` or `1128(b)(6)`.

2024 has 48 fraud rows under that join. 48 is below the external-validation floor of at least 100 events, ideally 200 or more, so a 2024 share is not a precise estimate. Floor: Collins, Ogundimu, and Altman, Statistics in Medicine, 2016, https://pmc.ncbi.nlm.nih.gov/articles/PMC4738418/. Print that caveat in the note before any 2024 share.

Saved 2024 figures a later report sits beside, already in the notes:

| Model | Top 1% | Top 5% | File |
| --- | --- | --- | --- |
| Shallow XGBoost | 11/48 | 18/48 | `models/holdout_note.txt` |
| Paper forest | 19/48 | 48/48 | `models/paper_forest_note.txt` |

The paper forest's 48/48 top 5 percent share includes every 2024 fraud row. It is not a short list. A candidate that puts every fraud row in the top 5 percent by giving almost every row the same score fails the short-list rule. A move of one or two 2024 events does not switch the page.

A high score means the billing profile resembles providers later excluded for a fraud-type reason. Each script prints that sentence. It must not say the firm committed fraud. `AGENTS.md` requires decent and respectful content. It does not contain the high-score sentence. That sentence is a page lock from `app/page_logic.py` and the harness notes.

Demo NPIs `1124725817` and `1639879034` are not labels. They never enter a fit. Do not invent a district, a school, a home address, a parent email, or a 9-digit ZIP. Do not add Part D. Do not download a CMS file or an LEIE file. Do not add city, state, ZIP, NPI, or name as a model input. GEPA, MIPROv2, OPRO, Harness2, HarnessPro, and PRISM are not one of these three plans.

Model inputs a proposal may read, in this order, from `FEATURE_COLUMNS` in `scripts/train.py`: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth. The live page model is a separate file. It also uses specialty, gender, and thirty paper summaries. Do not treat that page feature list as these eight fields.

Counted fraud rows, order `1128a1`, `1128a3`, `1128b6`, `1128b7`: 2019 is 333, 69, 2, 29. 2020 is 260, 48, 2, 25. 2021 is 195, 33, 2, 21. 2022 is 122, 23, 1, 12. 2023 is 73, 13, 1, 6. 2023 total is 93. 2024 total is 48. These counts are on [[model reliability]]. They are prose there, not a raw count file. A label agent confirms them from the rolled year and `data/training/UPDATED.csv` before the loop starts. If a recounted year disagrees, stop and record both counts.

## Plan A — year-holdout

Script: `scripts/harness_year.py`. Note: `models/harness_year_note.txt`. Model: `models/harness_year.json`. None of those files exist yet.

Classifier: one `XGBClassifier`, `max_depth` 4, `random_state` 1. Those two settings are already in `scripts/train.py`. Do not grid-search. The seed is a local lock. It is not on the XGBoost page.

Early stopping: `early_stopping_rounds` requires at least one item in `eval_set`, and the last `eval_set` entry is the one that stops training. The eval set is the grade year, and that year is 2021, 2022, or 2023. It is never 2024. If a grade year is also inside the fit, the split is wrong. Fit years are strictly before the grade year.

Group rule, if a fold is used inside a fit window: each group appears exactly once in the test set across all folds, and the number of distinct groups must be at least the number of folds. https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html. The group is NPI, because the same provider has several year rows. That page does not name NPI. Mapping the group to NPI is a project lock.

Grade years, in order: 2021, then 2022, then 2023. Keep a candidate only when that year's top 1 percent numerator rises and the top 1 percent list stays short. Two grade years in a row with no gain end the loop. 2024 is one local score after the stop, written once, beside 11/48 and 18/48, with the 48-event caveat.

A later page switch is a different session. It needs a 2023 top 1 percent numerator that beats the prior candidate by more than a few events, a short 2023 top 1 percent list, and that single 2024 report. "More than a few events" is a prompt instruction. It is not a number in an opened paper. Use more than 2 events, and write that choice in the note.

### Overnight split

The later coding session spawns 16 subagents. The parent does not fit.

| Agent | Writes | Does not write |
| --- | --- | --- |
| 1–12 | One count file for one billing year, 2013 through 2024 | Any other file |
| 13 | `scripts/harness_year.py` | A model |
| 14 | The loop, only after the twelve count files and the script exist | `app/`, the page model |
| 15 | `models/harness_year_note.txt` as the loop writes grade shares | A second model |
| 16 | The 2024 report after the stop | A fit |

Agents 1–12 each write one count file and no other file. The count file records fraud rows under the four-code later-year rule. The loop agent refits on years before the grade year, writes the grade shares, and stops after two grade years with no gain. Agent 16 scores 2024 once. That score is not a fit.

Start line, one new session, after this page is the plan:

`/goal Do Plan A of wiki/concepts/three-harness-plans.md. Spawn 16 subagents. Do not fit in the parent. Write scripts/harness_year.py, models/harness_year.json, and models/harness_year_note.txt. Grade 2021, then 2022, then 2023. Stop after two grade years with no gain. Score 2024 once after the stop and print the 48-event caveat before that share. Do not edit app/. Do not replace the page model. Do not download a file.`

## Plan B — feature-code

Script: `scripts/harness_features.py`. Kept code: `models/harness_features_code.py`. Note: `models/harness_features_note.txt`. None of those files exist yet.

Loop, from CAAFE: the model writes Python that adds columns, the code runs, a downstream classifier is scored on the transformed validation set, and the code is kept only when that score beats the prior one. If a generated block raises an error, that error is passed back for the next generation. Parsed Python is limited to an operation whitelist that excludes imports and arbitrary function calls. A direct call is rejected when the name is missing from the allowed functions: `sum`, `min`, `max`, `abs`, `round`, `len`, `str`, `int`, `float`, `bool`, `list`, `dict`, `set`, `tuple`, `enumerate`, `zip`, `range`, `sorted`, and `reversed`. `open`, `eval`, and `exec` are absent from that list. The whitelist is in the CAAFE repository checker, `caafe/run_llm_code.py`. The paper describes the whitelist. It does not name `open`, `eval`, and `exec`.

LLM-FE is a wider evolutionary search over a diverse pool. It is not this loop. Keep the single-candidate keep. Do not install a package in the research sense of this plan. The coding night may import pandas and numpy only.

The downstream classifier is one frozen `XGBClassifier`, `max_depth` 4, `random_state` 1. Eight billing fields only, plus a column the kept code adds. At most 10 proposals overnight. Each proposal is graded on 2023 top 1 percent and top 5 percent capture, and on whether the top 1 percent list is short. A proposal that does not beat the prior candidate is discarded. Two failures in a row end the loop.

The grade window is 2023. The fit window is years strictly before 2023. If the booster's eval set is 2023, the fit must not use 2023 labels. Write both file names into `models/harness_features_note.txt` before the first proposal. 2024 is scored once after the loop stops.

A within-year specialty rank is computed from that year's rows only. A rank that uses 2024 rows to transform a 2023 row is leakage. A proposal may add a column computed only from the eight fields. It may not add NPI, name, city, state, ZIP, or year as a model input. It may not read a file, open a socket, or import a module outside pandas and numpy.

The overnight loop may replace `models/harness_features_code.py`. It must not edit `app/`, `models/paper_forest.joblib`, `models/xgb_shallow.json`, or `data/rolled/`.

### Overnight split

The later coding session spawns 16 subagents. Fifteen agents each own one proposal family and write no other agent's file:

1. Services per beneficiary.
2. Log of service count.
3. Charge minus payment.
4. Within-year specialty rank of service count.
5. Within-year specialty rank of charge-to-payment ratio.
6. Within-year specialty rank of top-code share.
7. Growth times top-code share.
8. Missing-growth indicator.
9. Specialty string left as a category.
10. A pair interaction of average charge and top-code share.
11. A cap on extreme ratios.
12. A rank of beneficiary count within specialty.
13. A services-per-beneficiary rank within specialty.
14. A payment-to-charge residual.
15. A two-column specialty volume rank.

Agent 16 writes `scripts/harness_features.py` and runs the loop only after those proposals exist as text. The loop executes one proposal at a time, grades it, and keeps or discards it. Two failures stop the night. The 10-proposal cap still applies. Extra families wait.

Start line:

`/goal Do Plan B of wiki/concepts/three-harness-plans.md. Spawn 16 subagents. Do not fit in the parent. Write scripts/harness_features.py, models/harness_features_code.py, and models/harness_features_note.txt. Grade on 2023 only. Fit on years before 2023. At most 10 proposals. Stop after two failures. Score 2024 once after the stop. Do not edit app/, models/paper_forest.joblib, models/xgb_shallow.json, or data/rolled/. Do not execute generated code that fails the whitelist.`

## Plan C — label-lag

Script: `scripts/harness_lag.py`. Model: `models/harness_lag.joblib`. Note: `models/harness_lag_note.txt`. None of those files exist yet.

Score: `IsolationForest`. `contamination` is `'auto'` or a float. The default is `'auto'`. `'auto'` sets the threshold as in the original paper. A float must be in `(0, 0.5]`. The default changed from `0.1` to `'auto'` in version 0.22. https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html. One excerpt of the 0.22 docs quoted `[0, 0.5]`. Use the current page: `(0, 0.5]`.

`decision_function` and `score_samples` are the anomaly scores. Lower means more abnormal. `predict` is a +1/−1 inlier label. The grade uses a rank, not `predict`.

The score is fit on ordinary rows from years before the grade year, within specialty, and graded by how many later-excluded rows land in that year's top 1 percent and top 5 percent. It is kept only if 2023 capture rises and the top 1 percent list stays short. Grade years, in order: 2021, then 2022, then 2023. Two grade years with no gain stop the loop. 2024 is one report after the stop.

A 2024 row is fraud only when the exclusion year is after 2024 under the four codes. A 2024 positive can only be a 2025 or 2026 exclusion, because the LEIE on disk runs through 2026. That is a shorter window, not a change in the four-code definition. Do not mark a same-year exclusion as positive to fatten the grade year.

The page has one resemblance score. Plan C does not ship a forest score plus an anomaly score plus an LLM reason as three numbers. If a blend is required, it is one number written in `scripts/harness_lag.py`, chosen on 2023, and frozen before the 2024 report. Do not edit the page.

### Overnight split

The later coding session spawns 16 subagents. The parent runs the loop only after the twelve count files and the script exist.

| Agent | Writes | Check |
| --- | --- | --- |
| 1 | `scripts/harness_lag.py` | No fit in this agent |
| 2–13 | One specialty-count file for one billing year, 2013 through 2024 | No other file |
| 14 | Skeptic note | No pre-2024 fit contains a 2024 row |
| 15 | Skeptic note | Demo NPIs are absent from the fit |
| 16 | Skeptic note | The note prints the 48-event caveat before any 2024 share |

Two grade years with no gain stop the night.

Start line:

`/goal Do Plan C of wiki/concepts/three-harness-plans.md. Spawn 16 subagents. Do not fit in the parent. Write scripts/harness_lag.py, models/harness_lag.joblib, and models/harness_lag_note.txt. Use a rank from decision_function or score_samples, not predict. Grade 2021, then 2022, then 2023. Stop after two grade years with no gain. Score 2024 once after the stop. One score only. Do not edit the page. Do not download a file.`

## What no plan may edit

Until a later session compares a finished note with the page score:

- `app/`
- `models/paper_forest.joblib`
- `models/xgb_shallow.json`
- `data/rolled/`
- `models/holdout_note.txt`
- `models/paper_forest_note.txt`

A plan may replace only its own model file and its own note. Plan A may replace `models/harness_year.json`. Plan B may replace `models/harness_features_code.py`. Plan C may replace `models/harness_lag.joblib`.

## Unverified

These are not steps.

- The research run did not open `scripts/harness_year.py`, `scripts/harness_features.py`, or `scripts/harness_lag.py`. They are not on disk. This page names them. It does not create them.
- No opened protocol file states the 14-plus-2 split, the 15 proposal families, or the 12-plus-3-skeptic split. Those splits are the prompt's assignment, copied here so a later night has an owner for each file.
- "More than a few events" is not a number in an opened paper. This page sets that bar at more than 2 events and says so.
- The Cornell page does not print `1128(a)(1)`, `1128(a)(3)`, `1128(b)(6)`, or `1128(b)(7)` as headings.
- The GroupKFold page does not name NPI.
- The XGBoost page does not name a top 1 percent metric, and it does not name `random_state` 1.
- Year-by-type counts for 2019–2023 appear as prose on [[model reliability]]. A label agent recounts them before a fit.
- Python 3.14.4 and about 16 GB RAM were measured on 2026-10-17 in [[build decisions]], as 15.8 GB. They were not remeasured for this page.
- Demo NPIs were not re-checked against the LEIE in the research run.
- The IsolationForest float range `(0, 0.5]` is the current stable page. A 0.22 excerpt quoted `[0, 0.5]`.
- The live page model does not use only the eight billing fields. It also uses specialty, gender, and thirty paper summaries. Switching the page is out of this plan.

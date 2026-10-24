---
type: query
title: Three harness plans prompt
updated: 2026-10-22
tags: [query, app, model]
sources:
  - https://otexts.com/fpp3/tscv.html
  - https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html
  - https://xgboost.readthedocs.io/en/stable/python/python_api.html
  - https://arxiv.org/abs/2305.03403
  - https://github.com/automl/CAAFE
  - https://arxiv.org/abs/2503.14434
  - https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC4738418/
  - https://www.law.cornell.edu/uscode/text/42/1320a-7
  - models/holdout_note.txt
  - models/paper_forest_note.txt
  - wiki/concepts/model-reliability.md
---

# Three harness plans prompt

## Question

What prompt, and what runner, produces three separate overnight action plans for the year-holdout harness, the feature-code harness, and the label-lag harness, with at least 16 agents in the research run and at least 16 agents in each later coding night?

## Answer

Do not pass this to `/deep-research`. That runner caps the split at 6 questions when `args.breadth` is in range, and an out-of-range breadth stays at 4. Each question then returns at most 6 claims, and a later pass drops a step that is not itself a verified claim. Sixteen questions would be merged or dropped.

The runner is the project workflow `three-harness-plans` at `.grok/workflows/three-harness-plans.rhai`. It fields 16 research agents, one question each, then 16 skeptics. A finding enters a step only after a second agent opens the cited page or file. A smoke check of that workflow passed on 2026-10-21. The smoke check used canned host results. It did not open a page, and it did not start the 16 agents.

Run it as `/three-harness-plans` or `/workflow three-harness-plans`. The research run writes a report. It does not fit a model, and it does not edit `app/`.

The later coding night is a different session. That session is the coordinator. It spawns at least 16 subagents and does not fit in the parent. The assignment for those 16 is inside questions 5, 10, and 14. One night runs one plan. Do not run all three fits in the same parent.

Each plan is a loop: fit on years before the grade year, grade that year, keep the candidate only when the grade moves, stop after two grade years with no gain. 2024 is scored once after the stop. It never enters a fit or a grade. The page model stays until a later session.

The prompt the 16 agents execute, one question each:

```
You are one of sixteen research agents. Your only question is the one assigned to you below. Open the page before you cite it. Open a local file before you quote it. Prefer a primary paper, a documentation page, a statute, or a file in this workspace. Do not cite a page you did not open. Do not invent a URL, a parameter name, a count, or a model id. If the page is blocked or the fact is absent, mark that question still open and say what you opened. A filled finding must include the URL or file path, the value a later coder will type, and a short quote. This run writes no model and edits no app file.

The product is Medicare Fraud Flagger. A person looks up a provider or types eight billing numbers. The score is a review flag: the billing profile resembles providers later excluded for a fraud-type reason. The page must not say the firm committed fraud.

Write three separate action plans. Do not merge them into one script. Each plan is an overnight train, grade, and improve loop. The parent of that night coordinates at least 16 subagents and does not fit in the parent. 2024 is one local score after the loop stops. The page model stays.

Plan A is the year-holdout harness. Plan B is the feature-code harness. Plan C is the label-lag harness.

1. Plan A, protocol only. Open https://otexts.com/fpp3/tscv.html and quote the rolling-origin rule that training observations must come from before the test origin. Map that onto this table: fit only on billing years strictly before the grade year. The inner loop grades 2021, then 2022, then 2023. 2024 is scored once after the loop stops and never enters a fit or a grade. Also open https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html and quote that each group appears in only one test fold. The group is NPI, because the same provider has several year rows. Return the script scripts/harness_year.py, the note models/harness_year_note.txt, the model models/harness_year.json, and a stop rule: two grade years in a row with no gain ends the loop.

2. Plan A, booster settings only. Open https://xgboost.readthedocs.io/en/stable/python/python_api.html and quote early_stopping_rounds and eval_set. State that early stopping requires an eval set and that the last eval set is the one that stops training. Map that onto a grade year that is not 2024. Name one XGBClassifier, max_depth 4, and a seed. Do not grid-search. The grade metric is the share of grade-year fraud rows in the top 1 percent and the top 5 percent of that year's real-mix scores, plus whether the top 1 percent list is short. If the page does not name a top-slice metric, say so and do not invent one.

3. Plan A, label timing and the 100-event floor only. Open https://www.law.cornell.edu/uscode/text/42/1320a-7 and quote that 1128(a)(1) and 1128(a)(3) are mandatory and that 1128(b)(6) and 1128(b)(7) are permissive. Open https://pmc.ncbi.nlm.nih.gov/articles/PMC4738418/ and quote the external-validation floor of at least 100 events, ideally 200 or more. The local join already counts 93 fraud rows in 2023 and 48 in 2024. The plan must print that 48 is below that floor, so a 2024 share is not a precise estimate. A row is positive only when EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7 and the exclusion year is after the billing year. Same-year and earlier exclusions are not positive.

4. Plan A, local files and the keep rule only. Open models/holdout_note.txt and models/paper_forest_note.txt. Quote the saved 2024 shares: XGBoost 11/48 top 1 percent and 18/48 top 5 percent, paper forest 19/48 and 48/48. The overnight loop may replace models/harness_year.json. It must not replace the page model. A later page switch needs a 2023 top 1 percent numerator that beats the prior candidate by more than a few events, a short 2023 top 1 percent list, and a single 2024 report beside 11/48 and 18/48. A move of one or two 2024 events does not switch the page. Demo NPIs 1124725817 and 1639879034 are not labels.

5. Plan A, overnight agent split only. The later coding session spawns at least 16 subagents and does not fit in the parent. One agent labels each billing year 2013 through 2024 from files already on disk. One agent writes scripts/harness_year.py. One agent runs the loop only after the label counts exist. That is 14 label agents plus 2. Each label agent writes one count file and no other file. The loop agent refits on years before the grade year, writes the grade shares, and stops after two grade years with no gain. 2024 is the last agent's report, not a fit. Do not download a CMS file.

6. Plan B, feature-code loop only. Open https://arxiv.org/abs/2305.03403 and https://github.com/automl/CAAFE. Quote the iteration: the model writes Python that adds columns, the code runs, a downstream classifier is scored, and the code is kept only when validation improves. Quote the error feedback path and the AST whitelist that blocks open, eval, and exec. Map that onto one frozen XGBClassifier, eight billing fields only, at most 10 proposals overnight, each graded on 2023 top 1 percent and top 5 percent capture and on whether the top 1 percent list is short. A proposal that does not beat the prior candidate is discarded. Two failures in a row end the loop. The script is scripts/harness_features.py. The kept code is models/harness_features_code.py. The note is models/harness_features_note.txt. Do not execute generated code in this research run.

7. Plan B, allowed transforms only. Open scripts/train.py and quote FEATURE_COLUMNS. The eight fields are Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, and Growth. A proposal may add a column computed only from those fields, including a within-year specialty rank. It may not add NPI, name, city, state, ZIP, or year as a model input. It may not read a file, open a socket, or import a module outside pandas and numpy. Open https://arxiv.org/abs/2503.14434 only to confirm that an evolutionary code search is a wider variant. If that page is blocked, leave LLM-FE open and keep the CAAFE loop. Do not install a package in this research run.

8. Plan B, leakage and the grade year only. A within-year specialty rank must be computed from that year's rows only. A rank that uses 2024 rows to transform a 2023 row is leakage. The feature loop grades on 2023. It does not fit on 2023 labels if the booster's eval set is 2023. State which file is the fit window and which file is the grade window, and write both into models/harness_features_note.txt before the first proposal. 2024 is scored once after the loop stops. Demo NPIs 1124725817 and 1639879034 never enter a proposal or a fit.

9. Plan B, keep rule and page lock only. Open models/holdout_note.txt. The baseline beside the new code is 11/48 and 18/48 on 2024, and the paper forest is 19/48 and 48/48. The overnight loop may replace models/harness_features_code.py. It must not edit app/, models/paper_forest.joblib, models/xgb_shallow.json, or data/rolled/. A later page switch needs a 2023 gain larger than a few events, a short 2023 top 1 percent list, and one 2024 report with the 48-event caveat. A high score means resemblance to later fraud-type exclusions. The script must not say the firm committed fraud.

10. Plan B, overnight agent split only. The later coding session spawns at least 16 subagents. Fifteen agents each own one proposal family and write no other agent's file: services per beneficiary, log of service count, charge minus payment, within-year specialty rank of service count, within-year specialty rank of charge-to-payment ratio, within-year specialty rank of top-code share, growth times top-code share, missing-growth indicator, specialty string left as a category, a pair interaction of average charge and top-code share, a cap on extreme ratios, a rank of beneficiary count within specialty, a services-per-beneficiary rank within specialty, a payment-to-charge residual, and a two-column specialty volume rank. Agent 16 writes scripts/harness_features.py and runs the loop only after those proposals exist as text. The loop executes one proposal at a time, grades it, and keeps or discards it. Two failures stop the night.

11. Plan C, label-lag score only. Open https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html and quote contamination, including the auto default and the float range (0, 0.5]. State that decision_function and score_samples are the ranking outputs, and that predict is a thresholded label. This plan uses a rank, not predict. The score is fit on ordinary rows from years before the grade year, within specialty, and graded by how many later-excluded rows land in that year's top 1 percent and top 5 percent. It is kept only if 2023 capture rises and the top 1 percent list stays short. One score on the page. The script is scripts/harness_lag.py. The model is models/harness_lag.joblib. The note is models/harness_lag_note.txt.

12. Plan C, why the lag exists only. Open models/holdout_note.txt and wiki/concepts/model-reliability.md. Quote that a 2024 row can be positive only for a 2025 or 2026 exclusion because the LEIE on disk runs through 2026, and that this is a shorter window, not a change in the four-code definition. Keep the 100-event caveat on the 48-row 2024 report. The loop grades 2021, 2022, and 2023 in order. Two grade years with no gain stop the loop. 2024 is one report after the stop. Do not mark a same-year exclusion as positive to fatten the grade year.

13. Plan C, one score and the blend lock only. The page has one resemblance score. Plan C does not ship a forest score plus an anomaly score plus an LLM reason as three numbers. If a blend is required, it is one number written in scripts/harness_lag.py, chosen on 2023, and frozen before the 2024 report. The paper forest's 2024 top 5 percent share of 48/48 is not a usable short list. A candidate that puts every fraud row in the top 5 percent by giving almost every row the same score fails the short-list rule. Do not edit the page.

14. Plan C, overnight agent split only. The later coding session spawns at least 16 subagents. One agent writes scripts/harness_lag.py. Twelve agents each take one billing year from 2013 through 2024 and write a specialty-count file only. Three skeptics check that no pre-2024 fit contains a 2024 row, that demo NPIs 1124725817 and 1639879034 are absent from the fit, and that the note prints the 48-event caveat before any 2024 share. The parent runs the loop only after the twelve count files and the script exist. Two grade years with no gain stop the night. Do not download a file.

15. Shared locks. Open AGENTS.md and quote the rule that the app must be decent and that a high score is not a fraud finding. Each script must print that a high score means resemblance to later fraud-type exclusions and must not say the firm committed fraud. Do not invent a district, a school, a home address, a parent email, or a 9-digit ZIP. Do not add Part D. Do not download beneficiary-level claims. Do not add city, state, ZIP, NPI, or name as model inputs. The page model stays until a later session. GEPA, MIPROv2, OPRO, Harness2, HarnessPro, and PRISM are not one of these three plans.

16. Shared overnight stop and the 16-agent floor. The research run uses 16 questions, one agent each, then 16 skeptics. The later coding night also uses at least 16 subagents, assigned in questions 5, 10, and 14. The parent does not fit, does not score a million-row year inside the search, and does not call an LLM once per 2024 row. A full 2024 pass is a local score after the loop stops, written once, with the 100-event caveat. Name the three notes: models/harness_year_note.txt, models/harness_features_note.txt, and models/harness_lag_note.txt. A plan that cannot name its script, its grade years, its stop rule, and its keep rule stays open. Do not merge the three plans into one script.

Measured facts. Counted in this workspace. Use them. Do not re-estimate them.

- One row is one rendering NPI for one calendar year.
- Features a model may read, in this order: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth.
- A row is fraud only when its NPI matches a 10-digit NPI on data/training/UPDATED.csv, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the year of EXCLDATE is after the billing year.
- 2019-2023 pool used by the shallow fit: 1,270 fraud rows and 11,430 clean rows at 9 clean per fraud, seed 1. Year fraud counts in that window, in order 1128a1, 1128a3, 1128b6, 1128b7: 2019 is 333, 69, 2, 29. 2020 is 260, 48, 2, 25. 2021 is 195, 33, 2, 21. 2022 is 122, 23, 1, 12. 2023 is 73, 13, 1, 6. 2023 total is 93. 2024 total is 48.
- Saved XGBoost 2024 shares: 11/48 top 1 percent, 18/48 top 5 percent. Paper forest 2024 shares: 19/48 and 48/48. The 48/48 top 5 percent share is not a short list.
- Demo NPIs 1124725817 and 1639879034 are not labels.
- Machine: Windows, Python 3.14.4, about 16 GB RAM. Rolled years are about 1.06 million to 1.21 million rows. An LLM call per 2024 row will not finish.

Output of the research run. Three plans, in this order. Each step must also be a finding a second agent opened, or it stays under Unverified.

- Plan A. Script, grade years, stop rule, 16-agent split, keep rule, 2024 report.
- Plan B. Script, proposal cap, whitelist, grade year, stop rule, 16-agent split, keep rule, 2024 report.
- Plan C. Script, rank output, grade years, stop rule, 16-agent split, one-score lock, keep rule, 2024 report.
- Shared locks. What no plan may edit. What no plan may say on the page.
- Unverified. A page that did not open, a parameter the docs did not name, a count a local file did not contain.
```

## Citations

- [[harness action-plan prompt]]
- [[model reliability]]
- [[scope]]
- Student request on 2026-10-21 for one research prompt that writes three overnight train-grade-improve plans, with at least 16 agents in the research run and in the later coding night.
- https://otexts.com/fpp3/tscv.html
- https://arxiv.org/abs/2305.03403
- https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html

## What this changes in the wiki

Filed the prompt and the 16-agent workflow. The stock runner was used anyway on 2026-10-21 and finished Partial without writing the plans. The checklist is [[three harness plans]]. That page was filed on 2026-10-22. No model was fit. `app/` was not edited. The page model stays.

---
type: query
title: Model reliability research prompt
updated: 2026-10-18
tags: [query, app, model]
sources: []
---

# Model reliability research prompt

## Question

What prompt should the deep-research run use so the report can say which changes would make the trained XGBoost model more reliable, and which changes would break the locks?

## Answer

The model already exists. `models/xgb_shallow.json` is one fit, max depth 4, 100 trees, eight features. Training used 1,270 fraud rows and 11,430 clean rows from 2019–2023. The same model, scored on every 2019–2023 row, put 475/1,270 fraud rows in the top 1% and 918/1,270 in the top 5%. The 2024 holdout put 11/48 in the top 1% and 18/48 in the top 5%. That drop is the reliability problem. The workflow keeps only claims a second pass can verify, so the prompt asks for published methods, official file rules, and a keep-or-drop call on each change. When the report returns, file the standing note at `wiki/concepts/model-reliability.md`. Do not reopen the product idea. Do not treat a cited AUC as a score this model has earned.

The prompt to pass as `args.query`:

```
Write a reliability checklist for the XGBoost model already trained in Medicare Fraud Flagger. The report will be reopened while one person decides which changes to make. Every sentence should be a change a coder can apply, a check a coder can run, or a reason to leave the current model alone. Do not write a strategy essay. Do not reopen the product idea. Do not recommend a second algorithm.

Write the report in this order, and skip a section only when no verified fact supports it:

1. How to use this note. Three to five sentences. Name the reliability gap in the numbers below, the critical path of checks, and the changes that are not on that path.
2. Diagnosis. One table. Each row is one possible cause of the gap. Columns: cause, what in this build would have to be true for that cause to matter, the check that would confirm or kill it, and whether the check can be run on files this project already has.
3. Ranked changes. Number them so a later session can say "apply change 3." Each change has: what to change, which file owns it, what it must not change, the published or official source, the expected effect on the 2024 top 1% and top 5% shares, and Done when. Rank by how directly the source supports the change for this exact setup. A change with no source goes under Unverified, not into the ranking.
4. Leave alone. Changes that sound like reliability work and would break a lock below. One sentence each, with the lock they break.
5. Unverified. Facts you could not confirm. A guess is not a change.
6. Sources. The URL you opened, next to the diagnosis row or change it supports.

Measured, 2026-10-17. Treat these as the current model. Do not invent a better score for it.

- One XGBClassifier, saved at models/xgb_shallow.json. max_depth 4. random_state 1. Every other booster setting is the XGBoost 3.4.1 default. n_estimators resolved to 100 trees. One fit. No search. No second model. No scale_pos_weight. No early stopping. No calibration.
- Features, in this order: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth. Specialty is an integer code from a sorted list of training-year specialty strings. A blank or unseen specialty is missing, not zero. Missing numbers stay missing. Name, NPI, city, state, ZIP, and Year are not features.
- Growth is this year's service count divided by the prior year's service count, minus 1. It is missing when the provider has no prior rolled row, or when the prior service count is 0. 2018 exists only so 2019 can have Growth. 2018 is not a training year.
- A row is one rendering NPI for one calendar year, rolled up from Medicare Physician & Other Practitioners by Provider and Service. A source row is one NPI, one HCPCS code, and one place of service. Service count and dollars are summed. Average charge and average payment are totals divided by service count. Charge-to-payment ratio is average charge divided by average payment, and is missing when average payment is 0. Top-code share is the largest HCPCS service count divided by the year's service count. Beneficiary count is taken from the source rows and is not a sum of patients across codes. Specialty is the provider type on the source rows.
- Labels: a provider-year is fraud only when its NPI matches a 10-digit NPI on the HHS OIG LEIE, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the year of EXCLDATE is after the billing year. Same-year and earlier exclusions are not positive. An NPI with more than one qualifying exclusion uses the earliest year. The LEIE file on disk contains exclusion dates through 2026, so a 2024 row can be positive only for an exclusion in 2025 or 2026. License actions and other exclusion types are not labels.
- Train on 2019-2023. Keep every fraud row. Undersample clean rows to 9 clean per fraud, seed 1. Training sample: 1270 fraud, 11430 clean. Score the real mix with the same model. Real mix: 475/1270 in the top 1%, 918/1270 in the top 5%. Hold out 2024. Do not fit on 2024. 2024 holdout: 11/48 in the top 1%, 18/48 in the top 5%. The cutoff is the percentile of all scores that year. Ties at the cutoff count as inside the slice. Accuracy is not a result.
- The page score is the positive-class probability. The page percentile is that probability's rank among stored rows for the same year. A high score means the billing profile resembles providers later excluded for a fraud-type reason. The page must not say the firm committed fraud.
- Demo rows are not labels. Prince Laboratories Limited Liability Company, NPI 1124725817, 2024 percentile 99.988902 (1207339/1207473). Reliable Results Labs Inc, NPI 1639879034, 2024 percentile 99.945258 (1206812/1207473). Both are inside the top 5%. Neither is on the LEIE. Do not train on them. Do not hide a later miss.
- Machine: Windows, Python 3.14.4, xgboost 3.4.1, pandas, numpy. Workspace: C:\Users\Jacob\Downloads\congressional app. About 16 GB RAM. Rolled years are CSV, about 1.06 million to 1.21 million rows each. Do not store a home address, a school name, a parent email, or a 9-digit ZIP in that folder.

Locks. Treat these as given. If a source conflicts with one, put the conflict under Unverified and keep the lock.

- One model. Do not add a second algorithm, an ensemble, or a comparison model. A recommended change is a change to this XGBoost fit, its labels, its eight features, or its evaluation. A random forest is the 2018 paper's best learner. It is not a change to make.
- Do not tune a grid. A change may name one setting and the value the source supports. It may not say "search depths 3 through 8."
- Do not add a feature the student cannot explain in a three-minute demo. Do not add city, state, ZIP, NPI, or name as features. Do not download beneficiary-level claims.
- Do not mark a row positive because of an exclusion in or before that billing year.
- Do not use accuracy, precision, or a dollar-savings claim as the result. The result stays the share of fraud rows in the top 1% and the top 5%.
- Do not reopen the medically-unnecessary-test label hunt. Do not add Part D. DMEPOS is a 2.0 item. Name it only if a source says the physician-file rollup cannot see a fraud type that dominates the 2024 labels.
- Do not look for a downloadable model. Train any revised fit from the files already in this workspace.
- The 2018 paper's AUC of about 0.873 is a comparison point. It is not a target this build has to hit, and it is not evidence that this model will reach it.

File owners. A change must name one owner. Two changes must not be told to edit the same file in one step.

- labels: may edit scripts/join_labels.py and data/training/. Must not edit data/rolled/, models/, or app/.
- model: may edit scripts/train.py and models/. Must not edit data/rolled/ or app/.
- data: may edit scripts/download_year.py only if a change is a rollup bug. Must not re-download a year unless the current rolled column is wrong. Must not edit app/ or models/.
- page: may edit app/ only to print a new holdout number or a new disclaimer. Must not retrain.
- notes: may edit wiki/concepts/model-reliability.md after the report returns. Must not edit scripts/ or models/.

Research these questions. Prefer the primary page. Cite only a URL you opened. If a column, a parameter, or a paper result cannot be verified, leave it under Unverified.

1. Evaluation. For a fraud ranker with about 0.04% positives, what does a drop from 475/1270 in the top 1% on the training years to 11/48 on the next year mean? Separate three cases with published definitions: the model memorized the training providers, the 2024 positive count is too small to read, and the label rule changed the class between the two windows. What confidence interval or uncertainty statement is standard for a capture rate of 11 out of 48? What minimum positive count in the holdout year do the sources treat as readable? Cite the method, not a blog summary.

2. Labels. Bauder and Khoshgoftaar, Health Information Science and Systems, 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/ . Extract only their join rule, their exclusion types, their exclusion-period rule, their years, their class mix, and their best result. Where does this build match that paper, and where does it differ? Then open the current OIG LEIE data dictionary or download page. Confirm the column names NPI, EXCLTYPE, EXCLDATE, and any reinstatement or waiver date column. State whether a provider who was excluded and later reinstated should stay a positive for billing years before the exclusion. State whether 1128(b)(6) and 1128(b)(7) are the same kind of label as 1128(a)(1) and 1128(a)(3), in the words of the statute or the LEIE page. Do not invent a new exclusion-type list.

3. Features and leakage. Which of the eight features can leak the label or duplicate another feature? Charge-to-payment ratio is computed from average charge and average payment. Specialty is an arbitrary integer code. Growth is missing for a large share of rows. Beneficiary count is not summed across HCPCS codes. For each, say whether a published Medicare-fraud paper treats that construction as valid, harmful, or unstated. Look specifically for peer-provider normalization within specialty and year, and for whether raw service count and raw dollars are used without a peer baseline. If a source recommends a within-specialty ratio, say whether that ratio can replace one of the eight features without adding a ninth.

4. Fit settings. For XGBoost 3.x on a table with missing values, a rare positive class, and no validation set inside the training years, which single default is a known reliability problem? Cover missing-value direction, scale_pos_weight versus row undersampling, the default of 100 trees with no early stopping, and probability versus rank. Recommend at most one setting change, with the value, and say what the 2024 holdout would have to show before that change is kept. If the sources say the current undersampling already matches the published 90:10 setup, say that and recommend no setting change.

5. What not to trust. Find published warnings about Medicare fraud models trained on the LEIE or on public use files. Include label lag, providers who keep billing after exclusion, organization NPIs versus individual NPIs, and the difference between a high AUC on a balanced test mix and capture in the real mix. State which of those warnings already apply to the 11/48 and 18/48 numbers.

Done when:

- Diagnosis names the 475/1270 versus 11/48 drop and says which causes can be checked without a new download.
- Each ranked change names one owner, one file, and a Done when line that includes a new 2024 top 1% and top 5% note.
- Leave alone includes any change that adds a second model, tunes a grid, uses accuracy, or trains on the two demo NPIs.
- No URL appears unless you opened it. A guessed paper result is an unverified item.

Return verified facts only. A guessed parameter is a failed change.
```

## Citations

- Student request on 2026-10-18 for a deep-research prompt that would make the underlying XGBoost model more reliable.
- [[scope]]
- [[xgboost viable]]
- [[good flag]]
- [[action-plan prompt]]
- `models/holdout_note.txt`
- `scripts/train.py`
- `scripts/join_labels.py`

## What this changes in the wiki

Filed the prompt. The standing reliability note does not exist until a research report is compiled into `wiki/concepts/model-reliability.md`. The model lock on [[scope]] is unchanged.

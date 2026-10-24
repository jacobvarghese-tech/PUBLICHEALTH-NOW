---
type: query
title: Reliability apply prompt
updated: 2026-10-18
tags: [query, app, model]
sources:
  - models/holdout_note.txt
---

# Reliability apply prompt

## Question

What prompt should the next coding session use so it applies the reliability research without inventing a new fit?

## Answer

The research run `deep-research` (`wf_01a14d6caeab7ba081cfd74ad6d6ce32`) finished Partial on 2026-10-18. Nineteen of twenty-two claims were kept. The report body passed citation checks. It named one ranked change: print the holdout-size caveat beside the stored shares. It named no booster value, no replacement feature, and no new exclusion list. The 9-clean-per-fraud undersample already matches the published 90:10 mix, so no booster setting is on the path.

The reliability gap stays the stored drop from 475/1270 in the top 1% on 2019–2023 to 11/48 in the top 1% on 2024, with 18/48 in the top 5%. Forty-eight events sit below the Collins, Ogundimu, and Altman floor of at least 100 events, ideally 200 or more. That floor is the closest published readability rule. It is not a theorem that 48 capture events are unreadable for every metric. The report refused a confidence interval for 11/48.

The prompt to hand the next session:

```
Apply the verified reliability checklist to Medicare Fraud Flagger. Do the diagnosis checks first. Apply the one ranked page change only if those checks leave the saved fit standing. Do not invent a second change. Do not refit.

Workspace: C:\Users\Jacob\Downloads\congressional app
Python: 3.14.4. xgboost 3.4.1. About 16 GB RAM.
Research run: deep-research, wf_01a14d6caeab7ba081cfd74ad6d6ce32, finished Partial, 19 of 22 claims kept. Treat that report as the source of the checks and the one change. A sentence in that report that sits under Unverified is not a change.

Current fit. Treat these numbers as measured. Do not invent a better score.

- models/xgb_shallow.json. One XGBClassifier. max_depth 4. random_state 1. Every other booster setting is the XGBoost 3.4.1 default. n_estimators resolved to 100 trees. One fit. No search. No second model. No scale_pos_weight. No early stopping. No calibration.
- Features, in this order: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth. Specialty is an integer code from a sorted list of training-year specialty strings. A blank or unseen specialty is missing, not zero. Missing numbers stay missing. Name, NPI, city, state, ZIP, and Year are not features.
- Train on 2019-2023. Keep every fraud row. Undersample clean rows to 9 clean per fraud, seed 1. Training sample: 1270 fraud, 11430 clean.
- Score the real mix with the same model. Real mix: 475/1270 in the top 1%, 918/1270 in the top 5%.
- Hold out 2024. Do not fit on 2024. 2024 holdout: 11/48 in the top 1%, 18/48 in the top 5%. The cutoff is the percentile of all scores that year. Ties at the cutoff count as inside the slice. Accuracy is not a result.
- A 2024 row is fraud only when its NPI matches a 10-digit LEIE NPI, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the exclusion year is after 2024. The LEIE on disk contains dates through 2026, so a 2024 row can be positive only for an exclusion in 2025 or 2026. That shorter window is not, by itself, a changed class definition.
- The page score is the positive-class probability. The page percentile is that probability's rank among stored rows for the same year. A high score means the billing profile resembles providers later excluded for a fraud-type reason. The page must not say the firm committed fraud.
- Demo rows are not labels. Prince Laboratories Limited Liability Company, NPI 1124725817, 2024 percentile 99.988902 (1207339/1207473). Reliable Results Labs Inc, NPI 1639879034, 2024 percentile 99.945258 (1206812/1207473). Both are inside the top 5%. Neither is on the LEIE. Do not train on them. Do not hide a later miss.

Work in this order. Stop when a check fails the condition written on that step. Do not start step 6 while step 2, 3, or 4 is still open.

1. Confirm the saved fit is the one these numbers describe. Read models/holdout_note.txt and the feature list in scripts/train.py. Confirm max_depth 4, 100 trees, the eight features in the order above, training sample 1270 and 11430, real mix 475/1270 and 918/1270, and holdout 11/48 and 18/48. If any of those differ, stop and write the difference. Do not retrain to make them match.

2. Kill or keep "memorized training providers." Read scripts/train.py and scripts/download_year.py. Confirm name, NPI, city, state, ZIP, and year are not features. Confirm Growth is this year's service count divided by the prior year's service count, minus 1, and is missing when there is no prior rolled row or the prior service count is 0. Confirm Charge-to-payment ratio is average charge divided by average payment, missing when average payment is 0, and that both averages come from rolled service, charge, and payment fields. If both hold, write "memorization not established" and go on. Do not add a feature to test this.

3. Kill or keep "2024 positive count too small to read." Count the 2024 fraud rows that sit behind the stored 11/48 and 18/48. Use the join already in scripts/join_labels.py and the files already on disk. Do not download a year. If the count is 48, write that 48 is below the external-validation floor of at least 100 events, ideally 200 or more, so neither 2024 share is a precise estimate. That floor is from Collins, Ogundimu, and Altman, Statistics in Medicine, 2016, https://pmc.ncbi.nlm.nih.gov/articles/PMC4738418/. It is the closest published readability rule. It is not a theorem that 48 capture events are unreadable for every metric. Do not publish a Wilson interval, a Clopper-Pearson interval, or any other interval for 11/48. The research run dropped that claim. If the count is not 48, stop and write the count you found. Do not refit.

4. Kill or keep "label rule changed the class." Read scripts/join_labels.py and models/holdout_note.txt. Confirm 2019-2023 and 2024 use the same four codes (1128a1, 1128a3, 1128b6, 1128b7) and the same rule that the exclusion year must be strictly after the billing year. If both hold, write "definition change killed" and go on. Do not refit because 2024 can be positive only for a 2025 or 2026 exclusion. That is a shorter window, not a shown change in the class definition.

5. Tabulate EXCLTYPE on fraud rows in each window, from the LEIE already at data/training/UPDATED.csv. Do not download a new list. First confirm the header contains NPI, EXCLTYPE, EXCLDATE, REINDATE, WAIVERDATE, and WVRSTATE. If a named column is absent, write that and do not invent it. Then count fraud rows by EXCLTYPE for 2019-2023 and for 2024. 1128(a)(1) and 1128(a)(3) are mandatory exclusions. 1128(b)(6) and 1128(b)(7) are permissive exclusions. Statute: https://www.law.cornell.edu/uscode/text/42/1320a-7. If the mix of those two groups is similar across the two windows, write "mixed-class cause killed." If the mix differs sharply, write the two counts and stop before any label edit. Do not change the four-code list. Do not add a reinstatement rule. Reinstated people are absent from this file, and that absence does not say whether billing years before exclusion should stay positive. Do not mark a row positive for an exclusion in or before that billing year. The payment ban in 42 CFR § 1001.1901 covers items furnished on or after the exclusion effective date. It is not a license to label those earlier billing years a different way.

6. Apply the one ranked change, and only this change. Owner: page. Files: app/about.html, and tests/test_page.py only as far as the about-page assertion. Do not edit scripts/train.py, scripts/join_labels.py, scripts/download_year.py, models/, data/rolled/, or data/training/.

   Print the holdout-size caveat beside the stored shares. Keep the stored numbers. The about page already says: "Of the 2024 fraud rows, 11/48 are in the top 1% of 2024 scores and 18/48 are in the top 5%." Add, next to that sentence, that 48 fraud rows are below the published external-validation floor of at least 100 events, ideally 200 or more, so those two shares are not a precise estimate of next-year capture. Keep the sentence that a high score is a resemblance, not a fraud finding. Do not say the firm committed fraud. Do not retrain. Expected effect on the 2024 top 1% share and the 2024 top 5% share: none.

   Done when all of these are true:
   - app/about.html still prints 11/48 and 18/48.
   - The same page prints the 100-event floor and says the two shares are not a precise estimate.
   - models/xgb_shallow.json is byte-for-byte unchanged.
   - data/rolled/ is unchanged.
   - python -m unittest tests.test_page tests.test_train passes.
   - A local boot of python app/server.py serves /about.html with that caveat. Read the served HTML. A file read alone is not the check.

7. Write the standing note at wiki/concepts/model-reliability.md from the checks you actually ran. Include the diagnosis results, the EXCLTYPE counts, the one page change, and the leave-alone list below. Update wiki/index.md and append wiki/log.md. Do not edit scripts/ or models/ in this step.

Leave alone. Each of these sounds like reliability work and breaks a lock.

- Do not add a random forest, an ensemble, or a comparison model to chase an AUC of 0.87302. That breaks the one-model lock. That AUC is not a target for this fit.
- Do not grid-search depth or any other booster argument. That breaks the no-grid lock.
- Do not report accuracy, precision, or dollars saved. Do not drop ties-at-the-cutoff from the top 1% and top 5% shares. That breaks the result lock.
- Do not train on NPI 1124725817 or NPI 1639879034. Do not hide a later miss on either row. Demo rows are not labels.
- Do not fit on 2024. That breaks the holdout lock.
- Do not mark a row positive for an exclusion in or before that billing year. That breaks the label-timing lock.
- Do not add city, state, ZIP, NPI, or name as features. Do not download beneficiary-level claims. That breaks the feature lock.
- Do not add Part D or DMEPOS. No verified source says the physician-file rollup misses a fraud type that dominates the 2024 labels.
- Do not search for a downloadable model. Train any later fit from the files already in this workspace.
- Do not change the resolved 100 trees. Do not turn on early stopping. early_stopping_rounds defaults to None and requires an eval_set this training run does not have.
- Do not set scale_pos_weight away from its default of 1. The negative-to-positive formula is only a typical value to consider. The 9-clean-per-fraud undersample already matches the published 90:10 majority-to-minority setup. Leave that undersample unchanged.
- Do not replace learned missing-value directions with one fixed direction. Missing numbers already stay missing.
- Do not recode beneficiary count into a distinct-patient total across codes. The source field is distinct only for one rendering NPI, one HCPCS code, and one place of service. The shipped rollup adds Tot_Benes across source rows. Leave that construction as it is.
- Do not add a within-specialty peer ratio. Do not drop raw service count, raw beneficiary count, average charge, or average payment to make room for one. Do not drop the charge-to-payment ratio, top-code share, or growth. Absence from a published feature table is not a harm finding, and no measured 2024 share exists for a refit without them.
- Do not change specialty from the sorted-list integer code to one-hot encoding.
- Do not swap the page probability for another score type.
- Do not drop organizational NPIs. The rolled CSV columns are NPI, Name, City, State, ZIP, Specialty, Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Growth, Year. There is no entity-code column. Do not re-download a year to get one.
- Do not store a home address, a school name, a parent email, or a 9-digit ZIP in this folder.

Unverified. Do not turn any of these into a step.

- A confidence interval for 11/48.
- The 2018 paper's join rule, exclusion-type list, exclusion-period rule, year range, or class mix. The methods page was blocked. The 90:10 match is a class-mix match, not a tested XGBoost parameter.
- Whether a reinstated provider should stay positive for billing years before the exclusion.
- Whether individual versus organizational NPIs caused the drop.
- Any booster value, replacement feature, or new exclusion list. No verified source named one. There is no change 2.

Report back with: the result of steps 2 through 5 in one short table, whether step 6 was applied, the hash of models/xgb_shallow.json before and after, and the test command result. If you stopped early, say which step stopped you and the count or difference you found.
```

## Citations

- Student request on 2026-10-18 for a coding prompt based on the reliability research.
- [[model reliability prompt]]
- Research run `deep-research`, `wf_01a14d6caeab7ba081cfd74ad6d6ce32`, scratch report, status Partial, 19 of 22 claims kept.
- `models/holdout_note.txt`
- `app/about.html`
- `data/rolled/2024.note.txt`

## What this changes in the wiki

Filed the coding prompt. The standing note `wiki/concepts/model-reliability.md` is still unwritten until a session runs the checks. The model lock on [[scope]] is unchanged. No script or model file was edited.

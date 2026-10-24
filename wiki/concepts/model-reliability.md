---
type: concept
title: Model reliability
updated: 2026-10-18
tags: [app, model]
sources:
  - wiki/queries/reliability-apply-prompt.md
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC4738418/
  - https://www.law.cornell.edu/uscode/text/42/1320a-7
---

# Model reliability

Checked 2026-10-18 against the files on disk. The research run was `deep-research`, `wf_01a14d6caeab7ba081cfd74ad6d6ce32`, finished Partial, 19 of 22 claims kept. That report named one ranked change. A sentence under Unverified was not applied.

The saved fit still stands. `models/xgb_shallow.json` is one `XGBClassifier`, max depth 4, 100 trees, eight features in the locked order. Training sample is 1270 fraud and 11430 clean. Real mix is 475/1270 in the top 1% and 918/1270 in the top 5%. 2024 holdout is 11/48 in the top 1% and 18/48 in the top 5%. The model file was not refit. SHA-256 before and after this check: `5A215FB6D4995C59AF0528C9427D3B29A430E6AE5B3D1893262572357D8D5531`.

## Diagnosis

| Check | Result |
| --- | --- |
| Saved fit matches the stored numbers | Confirmed. Holdout note, feature list, and the saved trees agree. |
| Memorized training providers | Memorization not established. Name, NPI, city, state, ZIP, and year are not features. Growth is this year's service count divided by the prior year's service count, minus 1, and is missing when there is no prior rolled row or the prior service count is 0. Charge-to-payment ratio is average charge divided by average payment, missing when average payment is 0. Both averages come from the rolled service, charge, and payment fields. |
| 2024 positive count too small to read | Kept. The join on the files already on disk counts 48 fraud rows in 2024. 48 is below the external-validation floor of at least 100 events, ideally 200 or more, so neither 2024 share is a precise estimate. That floor is from Collins, Ogundimu, and Altman, Statistics in Medicine, 2016, https://pmc.ncbi.nlm.nih.gov/articles/PMC4738418/. It is the closest published readability rule. It is not a theorem that 48 capture events are unreadable for every metric. No interval was published for 11/48. |
| Label rule changed the class | Definition change killed. 2019–2023 and 2024 use the same four codes, 1128a1, 1128a3, 1128b6, and 1128b7, and the same rule that the exclusion year must be strictly after the billing year. A 2024 row can be positive only for a 2025 or 2026 exclusion because the LEIE on disk runs through 2026. That is a shorter window, not a shown change in the class definition. |

## EXCLTYPE counts

The LEIE header at `data/training/UPDATED.csv` contains NPI, EXCLTYPE, EXCLDATE, REINDATE, WAIVERDATE, and WVRSTATE. Counts are fraud rows, joined with the same rule as `scripts/join_labels.py`. The type is the earliest qualifying exclusion for that NPI. 1128(a)(1) and 1128(a)(3) are mandatory exclusions. 1128(b)(6) and 1128(b)(7) are permissive exclusions. Statute: https://www.law.cornell.edu/uscode/text/42/1320a-7.

| Window | 1128a1 | 1128a3 | 1128b6 | 1128b7 | Mandatory | Permissive | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2019–2023 | 983 | 186 | 8 | 93 | 1169 | 101 | 1270 |
| 2024 | 38 | 8 | 0 | 2 | 46 | 2 | 48 |

Mandatory rows are 1169/1270 in the training window and 46/48 in 2024. Permissive rows are 101/1270 and 2/48. The mix of those two groups is similar across the two windows. Mixed-class cause killed. The four-code list was not changed. No reinstatement rule was added.

Year detail for 2019–2023: 2019 is 333, 69, 2, 29. 2020 is 260, 48, 2, 25. 2021 is 195, 33, 2, 21. 2022 is 122, 23, 1, 12. 2023 is 73, 13, 1, 6. Order is 1128a1, 1128a3, 1128b6, 1128b7.

## The one page change

Owner: page. `app/about.html` still prints 11/48 and 18/48. Next to that sentence it now says that 48 fraud rows are below the published external-validation floor of at least 100 events, ideally 200 or more, so those two shares are not a precise estimate of next-year capture. The resemblance sentence remains. The page does not say the firm committed fraud. Expected effect on the 2024 top 1% share and the 2024 top 5% share: none.

`tests/test_page.py` asserts the floor phrase and "not a precise estimate" on the about page. `python -m unittest tests.test_page tests.test_train` passed, 16 tests. A local boot of `python app/server.py` on port 8767 served `/about.html` with 11/48, 18/48, the 100-event floor, and the sentence that the two shares are not a precise estimate. `data/rolled/` was not edited.

## Leave alone

Each of these sounds like reliability work and breaks a lock.

- Do not add a random forest, an ensemble, or a comparison model to chase an AUC of 0.87302. That breaks the one-model lock. That AUC is not a target for this fit.
- Do not grid-search depth or any other booster argument. That breaks the no-grid lock.
- Do not report accuracy, precision, or dollars saved. Do not drop ties-at-the-cutoff from the top 1% and top 5% shares. That breaks the result lock.
- Do not train on NPI 1124725817 or NPI 1639879034. Do not hide a later miss on either row. Demo rows are not labels.
- Do not fit on 2024. That breaks the holdout lock.
- Do not mark a row positive for an exclusion in or before that billing year. That breaks the label-timing lock.
- Do not add city, state, ZIP, NPI, or name as features. Do not download beneficiary-level claims. That breaks the feature lock.
- Do not add Part D or DMEPOS. No verified source says the physician-file rollup misses a fraud type that dominates the 2024 labels.
- Do not search for a downloadable model. Train any later fit from the files already in this workspace.
- Do not change the resolved 100 trees. Do not turn on early stopping. `early_stopping_rounds` defaults to None and requires an eval set this training run does not have.
- Do not set `scale_pos_weight` away from its default of 1. The negative-to-positive formula is only a typical value to consider. The 9-clean-per-fraud undersample already matches the published 90:10 majority-to-minority setup. Leave that undersample unchanged.
- Do not replace learned missing-value directions with one fixed direction. Missing numbers already stay missing.
- Do not recode beneficiary count into a distinct-patient total across codes. The source field is distinct only for one rendering NPI, one HCPCS code, and one place of service. The shipped rollup adds Tot_Benes across source rows. Leave that construction as it is.
- Do not add a within-specialty peer ratio. Do not drop raw service count, raw beneficiary count, average charge, or average payment to make room for one. Do not drop the charge-to-payment ratio, top-code share, or growth. Absence from a published feature table is not a harm finding, and no measured 2024 share exists for a refit without them.
- Do not change specialty from the sorted-list integer code to one-hot encoding.
- Do not swap the page probability for another score type.
- Do not drop organizational NPIs. The rolled CSV columns are NPI, Name, City, State, ZIP, Specialty, Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Growth, Year. There is no entity-code column. Do not re-download a year to get one.
- Do not store a home address, a school name, a parent email, or a 9-digit ZIP in this folder.

## Unverified

These were not turned into a step.

- A confidence interval for 11/48.
- The 2018 paper's join rule, exclusion-type list, exclusion-period rule, year range, or class mix. The methods page was blocked. The 90:10 match is a class-mix match, not a tested XGBoost parameter.
- Whether a reinstated provider should stay positive for billing years before the exclusion.
- Whether individual versus organizational NPIs caused the drop.
- Any booster value, replacement feature, or new exclusion list. No verified source named one. There is no change 2.

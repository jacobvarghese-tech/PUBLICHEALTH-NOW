---
type: query
title: Expanded retrain action-plan prompt
updated: 2026-10-18
tags: [query, app, model]
sources:
  - models/holdout_note.txt
  - handoff-firm-flagging.md
  - handoff-label-shortage.md
  - wiki/queries/full-retrain-action-plan-prompt.md
---

# Expanded retrain action-plan prompt

## Question

What prompt should the research run use so the report is an action plan for one new XGBoost model trained on the older physician years, the recovered exclusions, and the other counted label piles, with at least 12 agents?

## Answer

The student wants that model. The approximation to replace, not to cite as a join, is about 4,400 fraud rows, up from 1,270. Disk size and the contest clock are not constraints. A new model file is allowed. `models/xgb_shallow.json` stays the baseline until a keep rule passes.

The stock `/deep-research` runner cannot field 12 research agents. `args.breadth` is ignored unless it is from 2 to 6, and an out-of-range value leaves the split at 4. Verification is two agents, plus one planner and one writer. Pass the prompt below only to a runner that keeps all 12 questions. Do not pass `args.breadth` 12 to `/deep-research`.

The prompt to pass as the query:

```
I need an action plan a later session can execute to fit one new XGBoost model. The training set is the current 2019-2023 physician join, plus every counted pile that was left out of that fit: physician years 2013-2018, recovered exclusions that left the live file, training-year DMEPOS rows where a file exists, and any new exclusion rows in the monthly supplements that match the same four codes. Hold out 2024. A new model file is allowed. Disk size and calendar time are not constraints. RAM is about 16 GB, so each multi-gigabyte CSV is downloaded, rolled in chunks, counted, and deleted before the next year starts. Write a plan a coder can apply. Cite a primary source for every URL, byte size, column name, and label rule. A claim with no opened source goes under Unverified, not into a step.

This run uses at least 12 agents. The 12 questions below are the split. Copy them. Do not merge two years onto one agent. Do not drop a year because a neighboring year looks similar. Each year has its own dataset id and its own folder id. Verification agents are extra. They do not replace any of the 12.

The audience is one person who can download CMS files, edit scripts, and fit a new XGBoost model. They will not read a literature survey. They need ordered steps, exact file URLs, a count to write before each next step, and a keep-or-discard rule for the new fit.

The 12 questions:

1. 2013 physician file only. Open the dataset-resources JSON for Medicare Physician & Other Practitioners by Provider and Service, data year 2013. Return the full CSV URL, the byte size, and the header columns needed to rebuild Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, and Growth. Confirm whether 2013 is the first year of this file family. Do not open 2014.

2. 2014 physician file only. Open that year's own dataset-resources JSON. Return the full CSV URL, including the folder id, the byte size, and the header. Do not reuse the 2013 folder id. Do not open 2015.

3. 2015 physician file only. Same outputs, from that year's own resources JSON. Do not copy a folder id from another year.

4. 2016 physician file only. Same outputs, from that year's own resources JSON.

5. 2017 physician file only. Same outputs, from that year's own resources JSON. Also name the column that can rebuild 2018 Growth by joining on the rendering NPI.

6. DMEPOS referring files for training years only. Open the dataset-resources JSON for Medicare DMEPOS by Referring Provider and Service. For each year 2013 through 2023, return the CSV URL and byte size, or say that year was not listed on a page you opened. The join key is Rfrg_NPI. Name the columns that can rebuild the eight features. 2024 is the holdout. Its URL is already known and is not a training file.

7. DMEPOS supplier files for training years only. Open the dataset-resources JSON for Medicare DMEPOS by Supplier and Service. For each year 2013 through 2023, return the CSV URL and byte size, or say that year was not listed. The join key is Suplr_NPI. Do not treat it as the same key as Rfrg_NPI. Name the columns that can rebuild the eight features. Growth may be missing. 2024 is the holdout.

8. Recovered exclusions. Open the OIG LEIE download page, the monthly-supplements page, and Social Security Act section 1128, including subsection (g). Decide whether a billing year before the exclusion stays a valid positive after the person is reinstated and dropped from the current UPDATED.csv. The local recovered file is C:\Users\Jacob\AppData\Local\Temp\label_hunt\leie_recovered.csv. It is not in the repo. Confirm the columns a join would need. Do not invent a count. The counts already measured are in the facts below.

9. Newly gained exclusions. Open the monthly exclusion supplements for the months still published, not the reinstatement files. State the URL pattern, which months you opened, and whether rows with EXCLTYPE 1128a1, 1128a3, 1128b6, or 1128b7 appear. A reinstatement row, including EXCLTYPE 1128a2, is not a positive. State whether any opened supplement row can label a billing year already on disk that the current UPDATED.csv does not already label.

10. Rows with no NPI. Open the NPPES downloadable-file documentation and the public API field list. State whether any bulk file can exact-match the 28,494 fraud-type LEIE rows that have no 10-digit NPI, and whether date of birth is in that file. A 40-search API sample is not a bulk file. If no such file exists, the plan skips this pile. Do not add an LLM step that assigns NPIs.

11. Fit settings. Open scripts/train.py in this workspace and the XGBoost parameter page closest to version 3.4.1. State the settings that stay the same when the training years become 2013-2023: one XGBClassifier, max_depth 4, random_state 1, other booster settings at the 3.4.1 default, 100 trees, one fit, no search, no scale_pos_weight, no early stopping. State how Specialty is rebuilt from the sorted specialty strings of the new training years only, and how Growth stays missing when the prior year is absent or the prior service count is 0.

12. Holdout and exclusions from the training file. Open the label rule in scripts/join_labels.py and the 2024 notes already in this workspace. State what the new training file must not contain: billing year 2024, NPI 1124725817, NPI 1639879034, a year in or after the exclusion year, a year after reinstatement, license-revocation LEIE codes, Part D rows, and DOJ, False Claims Act, or corporate-integrity-agreement names. Those last three stay off the positive class unless an opened source gives a counted incremental yield after deduplicating against the LEIE, and even then they go under a separate optional step, not into the default fit.

Source rules. Prefer the CMS dataset-resources JSON, the CSV URL that returns the file, the OIG LEIE page, the statute, the local script, and the XGBoost documentation. Deprioritize SEO explainers, vendor blogs, and Wikipedia. Open the resources JSON or the CSV header before you cite a URL, a byte size, or a column name. If a page is blocked, say so and do not reconstruct the URL from a citation or from a neighboring year's folder id. Do not cite a page you did not open.

Measured facts. Counted in this workspace on 2026-10-18. Use them. Do not re-estimate them. The figure of about 4,400 fraud rows is an approximation from a later chat. It is not a join. Do not put it in a step. Replace it with the count each step writes.

- Saved baseline, do not overwrite: models/xgb_shallow.json. SHA-256 5A215FB6D4995C59AF0528C9427D3B29A430E6AE5B3D1893262572357D8D5531. One XGBClassifier, max_depth 4, random_state 1, other booster settings at the XGBoost 3.4.1 default, 100 trees, one fit. No search. No scale_pos_weight. No early stopping.
- Features, in order: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth. Specialty is an integer code from a sorted list of training-year specialty strings. Missing numbers stay missing. Name, NPI, city, state, ZIP, and Year are not features.
- Current training years 2019-2023. Every fraud row kept. Clean rows undersampled to 9 per fraud row, seed 1. Training sample: 1,270 fraud rows and 11,430 clean rows.
- A row is fraud only when its NPI matches a 10-digit LEIE NPI, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the exclusion year is after the billing year. Same-year and earlier exclusions are not positive. Years after a reinstatement are not positive.
- 2024 was not used to fit. 2024 has 1,207,473 provider-years and 48 fraud rows. Capture: 11 of 48 in the top 1%, 18 of 48 in the top 5%.
- Fraud provider-years already joined, current LEIE, exclusion year after billing year: 2018=541, 2019=433, 2020=335, 2021=251, 2022=158, 2023=93, 2024=48. Unique NPIs in 2019-2023: 464. Unique NPIs in 2018-2023: 589. 2018 is rolled and unused for training. Growth in 2018 is missing because 2017 is not rolled.
- Wayback snapshots of UPDATED.csv from 2022 through January 2026 recovered 282 fraud-type NPIs missing from the current file. Ten are 1128(b)(7). None are 1128(b)(6). Joined extras, exclusion year after billing year: 2018=16, 2019=10, 2020=4, 2021=4, 2022=1, 2023=1, 2024=0. Combined 2018-2023 extra rows: 36. Combined extra unique NPIs: 16. Combined 2019-2023 extra rows: 20. The other 266 of the 282 do not appear in the 2018-2024 physician rolls.
- Physician files already rolled: data/rolled/2018.csv through 2024.csv. Raw yearly service files for 2018-2024 are on disk. 2013-2017 are not downloaded.
- 2013 file facts already opened, confirm before download: MUP_PHY_R25_P04_V20_D13_Prov_Svc.csv, 2,909,942,471 bytes, https://data.cms.gov/sites/default/files/2025-11/bf4231f9-ec7f-4189-afc3-ba5d53b8bd12/MUP_PHY_R25_P04_V20_D13_Prov_Svc.csv. 2014-2017 filenames and byte sizes were opened. Their full URLs were not transcribed. Do not invent those URLs. 2014 is MUP_PHY_R25_P04_V20_D14_Prov_Svc.csv, 2,905,565,005 bytes. 2015 is D15_Prov_Svc.csv, 2,975,342,985 bytes. 2016 is D16_Prov_Svc.csv, 3,051,491,999 bytes. 2017 is D17_Prov_Svc.csv, 3,086,599,908 bytes.
- LEIE on disk: data/training/UPDATED.csv. 32,790 fraud-type rows. 4,296 have a 10-digit NPI. 28,494 do not. Of the no-NPI rows, 27,359 are people with first and last name, 1,135 are businesses, 26,623 have a date of birth. Public NPPES does not publish date of birth. A live sample of the NPPES API on 2026-10-18 returned 0 unique matches in 40 company searches and 1 unique match in 40 person searches.
- Watched-code DMEPOS, not a full join: catheter codes A4351-A4353, 2021-2024, 22,550 referring NPIs, 3 fraud-type matches. Supplier file, 2,225 NPIs, 0 matches. Fifty-five skin-substitute Q codes, 1,564 NPIs, 2 matches. Those searches added 5 unique fraud-type NPIs, all billed before the exclusion year, all absent from the rolled physician files.
- Opened 2024 DMEPOS files, holdout only: referring https://data.cms.gov/sites/default/files/2026-07/1ae6eac7-c8a5-4f1c-a82e-617f4bb65a5f/mup_dme_ry26_p05_v10_dy24_rfrhpr.csv, 559,665,948 bytes. Supplier https://data.cms.gov/sites/default/files/2026-07/9213e585-a53b-4728-bd47-5713c80ab2ba/mup_dme_ry26_p05_v10_dy24_suphpr.csv, 188,599,281 bytes.
- Opened September 2026 supplements, not a training join: https://oig.hhs.gov/exclusions/downloadables/2026/2609excl.csv and https://oig.hhs.gov/exclusions/downloadables/2026/2609rein.csv. The opened reinstatement sample is EXCLTYPE 1128a2 with REINDATE 20260910.
- Two named 2024 labs are not on the LEIE and are not training labels. Prince Laboratories Limited Liability Company, NPI 1124725817, percentile 99.988902. Reliable Results Labs Inc, NPI 1639879034, percentile 99.945258. Score them after the new fit. Do not train on them. Do not hide a miss.
- The page score is a resemblance to providers later excluded for a fraud-type reason. It is not a fraud finding.

Decision the report must make. Write the action plan for one new fit on physician years 2013-2023, hold out 2024, same eight features, same four codes, same exclusion-year-after-billing-year rule. Include a pile in the training file only when the question that owns it opened a source for the join. A year with no opened URL stays under Unverified.

- New model path: models/xgb_expanded.json. Do not write models/xgb_shallow.json.
- Add 2018's 541 current-LEIE fraud rows. They are already joined.
- Add the 282 recovered NPIs for billing years before their exclusion only if question 8's opened sources support that rule. If the sources do not support it, leave those 36 rows out and say so in the label rule.
- Add 2013-2017 only for years whose full CSV URL was opened.
- Add training-year DMEPOS rows only for years whose full CSV URL was opened. Count referring NPIs and supplier NPIs separately. Do not put a 2024 DMEPOS row in the training file.
- Add supplement rows only when an opened exclusion file has one of the four codes and the exclusion year is after the billing year, and the NPI is not already positive from UPDATED.csv.
- Skip the no-NPI pile unless question 10 opened a bulk exact-match file.
- Leave DOJ names, False Claims Act settlements, and corporate integrity agreements out of the default fit.

Output. Use these headers.

- Decision. One paragraph. Name the training years, the label piles included, and the new model path. Say that models/xgb_shallow.json stays the baseline until the keep rule passes.
- Counts to replace. A table with one row per pile. Columns: pile, rows already counted, rows still unknown until a download, whether the opened sources put it in the training file.
- Steps. Numbered. Each step names the owner script or the new script, the input files, the output file, and the count to write before the next step starts. Include the exact CSV URL and the header columns you opened. One year per download step. Delete that year's raw CSV after the roll. If a year URL was not opened, put that year under Unverified and do not invent the URL.
- Label rule. The rule that stays the same, and the reinstatement rule the opened OIG page or statute supports. Name the years that are not positive.
- Keep rule. The numeric comparison that decides whether models/xgb_expanded.json replaces the baseline. Include 2024 top 1% and top 5% capture against 11/48 and 18/48. Say how large a move has to be before it counts, from a methods paper you opened. If no opened paper sets that bar, write the two numerators and do not replace the baseline on a move of one or a few events. Do not invent a confidence interval.
- Unverified. Claims you could not confirm. A blocked dataset page, a missing year URL, or a methods page you could not open goes here.
- Sources. The URL you opened, next to the question number it supports.

Leave open. Do not invent a preference on these unless a source you opened makes them part of a step: a second algorithm, a grid search on depth, Part D, and license-revocation LEIE codes.

Do not invent a district, a school, a home address, a parent email, or a 9-digit ZIP. Do not say the page has found fraud. A high score is a resemblance to providers later excluded for a fraud-type reason.
```

## Citations

- Student request on 2026-10-18 for a research prompt that plans the expanded model and uses at least 12 agents.
- Local runner, `deep-research.rhai`. Breadth is applied only when `args.breadth` is from 2 to 6. Verification is hardcoded to two shards. An out-of-range breadth leaves the split at 4.
- [[full retrain action-plan prompt]]
- `models/holdout_note.txt`
- `handoff-firm-flagging.md`
- `handoff-label-shortage.md`

## What this changes in the wiki

Filed the prompt. It does not start the research run and it does not edit `scripts/` or `models/`.

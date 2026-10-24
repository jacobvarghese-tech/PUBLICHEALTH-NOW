---
type: query
title: Full retrain action-plan prompt
updated: 2026-10-18
tags: [query, app, model]
sources:
  - models/holdout_note.txt
  - handoff-firm-flagging.md
  - handoff-label-shortage.md
  - https://developers.openai.com/api/docs/guides/deep-research
  - https://www.anthropic.com/engineering/multi-agent-research-system
---

# Full retrain action-plan prompt

## Question

What prompt should the deep-research run use so the report is an action plan a later session can execute for a full retrain, including older physician years and a DMEPOS trial?

## Answer

The student wants a full retrain. Disk size and the contest clock are not constraints. A new model file is allowed. The earlier retrain prompt was limited to files already in the workspace and to one change. This prompt opens downloads, a longer train window, archived LEIE snapshots, and a separate DMEPOS trial.

The local workflow splits the query into at most four questions, returns at most six claims per question, and keeps a claim only when a second pass can open the cited source and support the exact statement. A prompt that prescribes the search order, or that asks for one blended recommendation, collapses those questions onto the same pages. This prompt names the decision, the measured facts, four evidence targets, the output, and the source rules. It does not name the search sequence.

The prompt to pass as `args.query`:

```
I need an action plan for a full retrain of a Medicare fraud-flagging model. The decision is which downloads, label joins, and fits to run, in what order, so a later session can execute the plan without inventing URLs or label rules. A new model is allowed. Disk size and calendar time are not constraints. Write a plan a coder can apply. Cite a primary source for every published claim, including every download URL and every column name. A claim with no opened source goes under Unverified, not into a step.

The audience is one person who can download CMS files, edit scripts, and fit a new XGBoost model. They will not read a literature survey. They need ordered steps, exact file URLs, a stop-and-count rule, and a keep-or-discard rule for the new fit.

How to split the work. This run plans at most four questions and verifies claims independently. Give each question a different evidence target so the researchers do not open the same pages:

1. Physician-year files. The current public download URL, byte size, and header columns for Medicare Physician & Other Practitioners by Provider and Service for each year 2013 through 2017. 2018-2024 are already rolled. Confirm whether 2013 is the first year of this file family and whether the 2012 Physician and Other Supplier PUF can be rolled to the same columns. Name the columns needed to rebuild Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, and Growth.
2. DMEPOS files. The current public download URL, year range, and header columns for Medicare DMEPOS by Referring Provider and Service and by Supplier and Service. State which NPI column is the join key (referring NPI versus supplier NPI), which columns can rebuild the same eight features, and which years exist. This is a second table, not a filter to catheter codes.
3. Exclusion list archive. Where OIG publishes the current LEIE UPDATED.csv, the monthly supplements, and whether older full files are officially archived. Confirm the column names NPI, EXCLTYPE, EXCLDATE, and any reinstatement date column. Confirm how 1128(a)(1), 1128(a)(3), 1128(b)(6), and 1128(b)(7) are written in the file. State whether billing years before an exclusion stay a valid positive after the person is reinstated and dropped from the current file.
4. Fit and readout. What a published Medicare fraud paper and a published rare-event validation paper say about holding out the latest year, reporting capture in the top 1% and top 5% rather than accuracy, and how many holdout events make that share readable. Use that only to set the keep rule. Do not pick a new algorithm unless a source you opened says the physician-year rollup cannot be scored by the same shallow XGBoost already used.

Source rules. Prefer the CMS dataset page, the file URL that returns the CSV, the OIG LEIE download page, the statute, the paper's own PDF, and the XGBoost documentation. Deprioritize SEO explainers, vendor blogs, and Wikipedia. Open the dataset page or the CSV header before you cite a URL, a byte size, or a column name. If a page is blocked, say so and do not reconstruct the URL from a citation. Do not cite a page you did not open.

Measured facts. These were counted in this workspace on 2026-10-18. Use them. Do not re-estimate them. Do not treat a cited AUC from another paper as a score this model has earned.

- Saved fit, leave it as the baseline: models/xgb_shallow.json. SHA-256 5A215FB6D4995C59AF0528C9427D3B29A430E6AE5B3D1893262572357D8D5531. One XGBClassifier, max_depth 4, random_state 1, other booster settings at the XGBoost 3.4.1 default, 100 trees, one fit. No search. No scale_pos_weight. No early stopping.
- Features, in order: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth. Specialty is an integer code from a sorted list of training-year specialty strings. Missing numbers stay missing. Name, NPI, city, state, ZIP, and Year are not features.
- Current training years 2019-2023. Every fraud row kept. Clean rows undersampled to 9 per fraud row, seed 1. Training sample: 1,270 fraud rows and 11,430 clean rows.
- A row is fraud only when its NPI matches a 10-digit LEIE NPI, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the exclusion year is after the billing year. Same-year and earlier exclusions are not positive. Years after a reinstatement are not positive.
- Same model scored on every 2019-2023 row: 475 of 1,270 fraud rows in the top 1%, 918 of 1,270 in the top 5%. Those rows were in the fit, so this figure is optimistic.
- 2024 was not used to fit. 2024 has 1,207,473 provider-years and 48 fraud rows. Capture: 11 of 48 in the top 1%, 18 of 48 in the top 5%.
- Fraud provider-years already joined, current LEIE, exclusion year after billing year: 2018=541, 2019=433, 2020=335, 2021=251, 2022=158, 2023=93, 2024=48. Unique NPIs in 2019-2023: 464. Unique NPIs in 2018-2023: 589. 2018 is rolled and unused for training. Growth in 2018 is missing because 2017 is not rolled.
- Wayback snapshots of UPDATED.csv from 2022 through January 2026 recovered 282 fraud-type NPIs missing from the current file. Joined extras: 2018=16, 2019=10, 2020=4, 2021=4, 2022=1, 2023=1, 2024=0. Combined 2018-2023 extra rows: 36. Combined extra unique NPIs: 16.
- Physician files already rolled: data/rolled/2018.csv through 2024.csv. Raw yearly service files for 2018-2024 are on disk. 2013-2017 are not downloaded.
- LEIE on disk: data/training/UPDATED.csv. 32,790 fraud-type rows. 4,296 have a 10-digit NPI. 28,494 do not. Of the no-NPI rows, 27,359 are people with first and last name, 1,135 are businesses, 26,623 have a date of birth. Public NPPES does not publish date of birth. A live sample of the NPPES API on 2026-10-18 returned 0 unique matches in 40 company searches (name + city + state) and 1 unique match in 40 person searches (name + city + state + ZIP).
- Watched-code DMEPOS, not a full join: catheter codes A4351-A4353, 2021-2024, 22,550 referring NPIs, 3 fraud-type matches. Supplier file, 2,225 NPIs, 0 matches. Fifty-five skin-substitute Q codes, 1,564 NPIs, 2 matches. Those searches added 5 unique fraud-type NPIs, all billed before the exclusion year. Those 5 NPIs are absent from the rolled physician files.
- Two named 2024 labs are not on the LEIE and are not training labels. Prince Laboratories Limited Liability Company, NPI 1124725817, percentile 99.988902. Reliable Results Labs Inc, NPI 1639879034, percentile 99.945258. Score them after the new fit. Do not train on them. Do not hide a miss.
- The page score is a resemblance to providers later excluded for a fraud-type reason. It is not a fraud finding.

Decision the report must make. Compare these trials using the sources you opened and write the action plan for the ones the sources support. A trial with no opened download URL stays out of the steps.

- Trial A. Physician years 2013-2023, plus the 282 Wayback NPIs, current LEIE rule unchanged. Hold out 2024. New model file. Compare 2024 top 1% and top 5% capture to 11/48 and 18/48. Also report a 2023 readout if the sources say 48 events are too few to keep or discard a fit.
- Trial B. A full DMEPOS join, all codes, referring file and supplier file, same label rule, rolled to the same eight features where the columns exist. Count new unique positive NPIs after removing NPIs already positive in the physician join. Then either one combined model or a second model. Say which, and why, from the columns you opened.
- Trial C. Unique-only NPPES name match for the 1,135 no-NPI businesses, then the no-NPI people, human check, count only. Include it only if a source shows a bulk file that can do an exact unique match. Do not include an LLM step that assigns NPIs.
- Skip. Leave models/xgb_shallow.json as the baseline even if a new file is fit. Do not replace it until the keep rule passes.

Output. Use these headers.

- Decision. One paragraph. Name which trials to run, in order. Name the new model path. Say that models/xgb_shallow.json stays the baseline until the keep rule passes.
- Why this order. A table with one row per trial. Columns: trial, what the opened sources say it can change in the positive count, what it cannot change, whether it needs a new fit.
- Steps. Numbered. Each step names the owner script or the new script, the input files, the output file, and the count to write before the next step starts. Include the exact CSV URL and the header columns you opened. If a year URL was not opened, put that year under Unverified and do not invent the URL.
- Label rule. The rule that stays the same, and any reinstatement rule the opened OIG page supports. Do not add DOJ press-release names, False Claims Act settlements, or OIG corporate integrity agreements as training labels.
- Keep rule. The numeric comparison that decides whether the new file replaces the baseline. Include 2024 top 1% and top 5% capture against 11/48 and 18/48, and a 2023 check if you include one. Say how large a move has to be before it counts, given the event counts you opened. Do not invent a confidence interval unless you opened a methods paper that covers a capture share at this sample size, and name that paper.
- Unverified. Claims you could not confirm. A blocked dataset page, a missing year URL, or a methods page you could not open goes here.
- Sources. The URL you opened, next to the step it supports.

Leave open. Do not invent a preference on these unless a source you opened makes them part of a step: a second algorithm, a grid search on depth, Part D, and license-revocation LEIE codes. Part D is a different fraud type. License revocations are a larger LEIE category and are not the current positive class.

Do not invent a district, a school, a home address, a parent email, or a 9-digit ZIP. Do not say the page has found fraud. A high score is a resemblance to providers later excluded for a fraud-type reason.
```

Pass it with `args.breadth` set to 4. Breadth 6 would split the four evidence targets into paraphrases, and the workflow drops claims past the cap.

## Citations

- Student request on 2026-10-18 for a deep-research prompt that sets up an action plan for a full retrain, including a DMEPOS trial and maxed labels.
- OpenAI, Deep research, prompting section. The rewrite rules used here are: include every stated preference, leave unstated dimensions open, request tables for comparisons, specify the output headers, and prefer primary sources. https://developers.openai.com/api/docs/guides/deep-research
- Anthropic, How we built our multi-agent research system, 2025-06-13. A delegated research task needs its own objective, output, sources, and boundary, or the workers repeat the same search. https://www.anthropic.com/engineering/multi-agent-research-system
- [[retrain research prompt]]
- [[action-plan prompt]]
- `models/holdout_note.txt`
- `handoff-firm-flagging.md`
- `handoff-label-shortage.md`

## What this changes in the wiki

Filed the prompt. It does not start the research run and it does not edit `scripts/` or `models/`. The standing action plan does not exist until a report returns.

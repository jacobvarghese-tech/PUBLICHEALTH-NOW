---
type: query
title: Label islands goal
updated: 2026-10-22
tags: [query, app, model]
sources:
  - wiki/concepts/paper-comparison.md
  - raw/sources/paper-replicate-excerpts.txt
  - tmp_pmc6120851/paper.txt
  - scripts/join_labels.py
  - models/specs/22.json
  - models/model_island_note.txt
  - data/paper_rolled/leie_20170627.csv
  - data/training/UPDATED.csv
---

# Label islands goal

## Question

What one `/goal` line runs a label search that the harness loop and the forest loop do not already own?

## Answer

Paste this as the whole prompt in a new Grok CLI session. The parent stays the coordinator. It does not fit the forest itself. This session did not start the loop.

```
/goal Run the label-island loop. You are the coordinator. The score to beat is 22 of 48 on the full 2024 year under the app label rule. Stop when a kept candidate reaches 24 of 48, or after 4 generations, whichever comes first. Spawn about 20 subagents and use their results. Do not fit a forest in this session. Do not score a year in this session. Do not download a file.

Before the first spawn, set subagents.max_concurrent to 20 in the user config so the 20 can run together. The current value is 4, and a cap of 4 queues the rest. Leave subagents.enabled true. If that write is refused, spawn all 20 anyway and let them queue. Do not stop because the cap stayed at 4.

This loop changes the training label only. It does not retune the forest and it does not add a column. /model-islands owns models/specs/. /score-islands owns harness/islands/. A feature loop owns models/feature_specs/. Leave those trees byte-for-byte unchanged. Do not edit app/. Do not replace models/paper_forest.joblib or models/optimized_model.joblib. A page switch is a later decision.

Read these files before the first spawn: scripts/join_labels.py, scripts/model_islands.py, scripts/paper_forest.py, models/specs/22.json, models/model_island_note.txt, models/optimized_note.txt, wiki/concepts/paper-comparison.md, raw/sources/paper-replicate-excerpts.txt, and the header plus five data rows of data/training/UPDATED.csv and of data/paper_rolled/leie_20170627.csv. The paper's date rule is the paragraph that starts "From the LEIE database, we first create the range of each exclusion period." Use that paragraph. Do not invent a second date rule.

Two label files are already on disk. data/training/UPDATED.csv is the October 2026 LEIE. Its header has NPI, EXCLTYPE, EXCLDATE, REINDATE, WAIVERDATE. A zero in a date column is blank. data/paper_rolled/leie_20170627.csv is the June 27, 2017 Wayback capture. Its header has the same five columns, and a blank date is 00000000. Both files write EXCLTYPE as 1128a1, not as 1128(a)(1). Do not download either file again. If a column is missing from the file a spec names, reject the spec. Do not guess the column.

The app rule, which both loops already use, and which the 2024 numerator must keep: a row is fraud when its NPI matches a 10-digit NPI, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the year of EXCLDATE is after the billing year. The earliest qualifying exclusion counts. Same-year and earlier exclusions are not positive. This rule is the confirmation rule. It is also one of the training specs, so the loop can measure a label change against the rule it already has.

The paper's Table 2, from the extract, is a different rule. Codes: 1128(a)(1), 1128(a)(2), 1128(a)(3), 1128(b)(4), 1128(c)(3)(g)(i), 1128(c)(3)(g)(ii). On disk those tokens are 1128a1, 1128a2, 1128a3, 1128b4, 1128c3gi, and 1128c3gii. Confirm the last two spellings from the file a spec names. If the file writes them differently, use the file's spelling and record it. Do not invent a spelling that is not in the file. Lengths: 5 years, 5, 5, 5, 10, and indefinite. The indefinite code has no numeric length in the opened text. Leave those rows out of the fraud class and record the count. Do not invent an end year.

The paper's date rule, in its words: add the minimum length of the exclusion to the exclusion start date to get the exclusion end date. Compare the month and year of that end date with any waiver or reinstatement date. The smallest month and year is the new exclusion end date. If the month is greater than 6, increase the exclusion end year to the following year. Otherwise keep the current year. Mark the provider fraudulent if the claims year is prior to the exclusion end year. A zero date and an 00000000 date are blank. A blank waiver and a blank reinstatement do not move the end date. Years after the new end year are not positive.

The frozen fit. Every generation refits the second forest from models/specs/22.json and nothing else: n_estimators 60, max_depth 20, min_samples_leaf 1, class_weight balanced, clean_per_fraud 9, fit years 2016 through 2022, random_state 0. The page forest inside models/optimized_model.joblib stays the primary score. scripts/optimized_rank.py zero_tie_break stays the promotion rule. Features stay the thirty paper summaries plus specialty and gender. No new column. 2023 and 2024 never enter a fit. Demo NPIs 1124725817 and 1639879034 are dropped before the sample. They are not labels.

The grade. Selection year is 2023. The 2023 keep uses the same label function the spec trained on, so a label change is graded on its own class. A keep needs a higher 2023 top 1 percent fraud count than the previous keep, a top 1 percent slice of at most 2 percent of that year's rows, and a 95th percentile still on the zero step. 2024 is scored once, after a keep, on the full year, and the 2024 numerator uses the app rule only. A paper-rule numerator is a different 48 and cannot be compared with 22 of 48. Print the paper-rule 2024 count beside it, labeled as a different class, and do not use it for the stop. Print this sentence before any 2024 share: 2024 has 48 fraud rows under the app rule, below the published external-validation floor of 100 events, so shares are not a precise estimate. A high score means resemblance to later fraud-type exclusions. It is not a finding that the firm committed fraud.

Banned. Do not add a label from a DOJ release, a False Claims Act settlement, a corporate integrity agreement, or a news page. Do not add Part D or DMEPOS. Do not mark a row positive because its specialty, its charges, or its NPI look unusual. Do not treat a license action outside Table 2 as fraud unless the spec's code list includes that EXCLTYPE and the file contains it. Do not use name, city, state, or ZIP as a join key. The join is the 10-digit NPI. A blank NPI and 0000000000 do not join.

The 20 agents, and the only files each one may write:

1 through 12. One label spec each. Read the two LEIE headers and the paper paragraph. Write models/label_specs/NN.json and nothing else. Keys: name, leie_file, codes, date_rule, train_positive, confirm_positive. leie_file is data/training/UPDATED.csv or data/paper_rolled/leie_20170627.csv. codes is a list of EXCLTYPE tokens that appear in that file. date_rule is app_year or paper_end. train_positive is one sentence. confirm_positive is the app rule, in every spec, with no exception. Specs, in order: the app rule on the 2026 file, so the loop has its own baseline; the app rule on the 2017 file; Table 2 finite codes on the 2026 file with the paper end date; Table 2 finite codes on the 2017 file with the paper end date; the four app codes plus 1128a2 and 1128b4, app year rule, 2026 file; the four app codes with a reinstatement cutoff, so a year after REINDATE is not positive, 2026 file; the four app codes with a waiver cutoff, so a year after WAIVERDATE is not positive, 2026 file; the four app codes with both cutoffs, 2026 file; Table 2 finite codes with the app year rule and no length added, 2026 file; the four app codes, exclusion year at least two years after the billing year, 2026 file; the four app codes, earliest exclusion replaced by the latest exclusion, 2026 file; the four app codes on the 2026 file, and a provider with two qualifying rows is left out of the fraud class and counted. A spec that needs a column or a code the named file does not contain writes date_rule as rejected and a one-sentence reason. It does not invent the column.

13 through 17. Critics. Read every models/label_specs/NN.json. Each critic writes models/label_specs/reviews/NN.json for the specs it rejects, as {"spec":"NN","verdict":"reject","reason":"one sentence"}. Contract: reject a spec whose confirm_positive is not the app rule, or whose codes are not in the named file. Leakage: reject a spec that fits on 2023 or 2024, or that uses demo NPIs 1124725817 and 1639879034 as labels. Date: reject a spec that invents an end year for the indefinite code, or that treats 0 and 00000000 as a real date. Source: reject a spec that names a file other than the two LEIE files, or that adds a settlement or a news label. Diversity: name one spec that is not the app rule. Do not edit the spec files. Do not say the firm committed fraud.

18. Write scripts/label_islands.py and tests/test_label_islands.py only. The script takes one spec path. It reads the named LEIE file and data/paper_rolled/YEAR.csv for 2016 through 2022. It builds the training label from the spec. It refits the second forest from models/specs/22.json with the same sample rule as scripts/model_islands.py. It loads the page forest from models/optimized_model.joblib and does not refit it. It grades 2023 with the spec's own label. It scores 2024 only after a keep, and the 2024 numerator uses the app rule on data/training/UPDATED.csv. A kept candidate is written to models/candidates/label_NN.joblib. models/optimized_model.joblib is not replaced. The note is models/label_island_note.txt. The database is models/label_island_db.json. The test uses a five-row LEIE frame and a five-row year frame. It does not load a rolled CSV and it does not fit 60 trees. The test covers a zero date, an 00000000 date, a same-year exclusion, and the indefinite code left out.

19. After the spec files and the reviews exist, write models/label_island_lesson.txt. List the specs a critic rejected and the reason. List the specs that survived. For each surviving spec, write the training fraud count it would have to beat: the app rule on 2016 through 2022 is the baseline, and the lesson says the count is uncounted until agent 20 runs. Do not invent that count. Do not fit.

20. After agents 18 and 19 finish, and only then, run the loop. One spec at a time. Skip a spec a critic rejected. For each surviving spec, run py -3.14 scripts/label_islands.py fit models/label_specs/NN.json and wait until it exits. Read models/label_island_note.txt and models/label_island_db.json. Keep the label only when the 2023 rule above passes. If 2024 was scored, the note must contain the 48-event caveat before the share, the app-rule numerator, the paper-rule count labeled as a different class, and the sentence that a high score is a resemblance. Stop the loop when a kept app-rule 2024 count is 24 or higher, or when 4 specs have been fit, whichever comes first. Write the last counts into models/label_island_note.txt.

Spawn 1 through 18 together. Spawn 19 after 1 through 17 have written their files. Spawn 20 only after 18 and 19 have finished. Agent 20 is the only agent that fits. Twenty writers on one forest would each draw a different sample.

Done when all of these are true, and an independent check can open the files: models/label_specs/01.json through 12.json exist; models/label_island_note.txt exists and prints the caveat before any 2024 share; models/label_island_db.json records each spec's 2023 top 1 percent count, the label function used for that count, and whether it was kept. models/paper_forest.joblib, models/optimized_model.joblib, models/specs/, harness/islands/, models/feature_specs/, scripts/join_labels.py, scripts/paper_forest.py, scripts/model_islands.py, data/paper_rolled/, data/training/UPDATED.csv, data/paper_scores/, and app/ are byte-for-byte unchanged. A high score is a resemblance, not a fraud finding. Do not edit the page. Do not switch the page model.

If a spec names a code the file does not contain, skip it and record the missing token. Do not invent the token. Do not download a CMS file. Do not download an LEIE file.
```

The fit stays frozen at spec 22. The 2024 numerator stays on the app rule, so a paper-rule training label can still be compared with 22 of 48. A paper-rule 2024 count is written beside it and is not the stop.

The 2017 capture is already at `data/paper_rolled/leie_20170627.csv`. The prompt does not download it again. Both files have `REINDATE` and `WAIVERDATE`. A zero and `00000000` are blank. The indefinite Table 2 code stays out of the fraud class because the opened paper gives it no length.

## Citations

- [[paper comparison]]
- [[three harness plans]]
- `raw/sources/paper-replicate-excerpts.txt`
- `models/model_island_note.txt`
- Student request on 2026-10-22 for a prompt for the label loop.

## What this changes in the wiki

Filed the goal line. Did not spawn an agent, fit a model, or edit `app/`.

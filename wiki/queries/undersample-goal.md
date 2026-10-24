---
type: query
title: Undersample goal
updated: 2026-10-20
tags: [query, app, model]
sources:
  - wiki/concepts/undersample-plan.md
  - models/paper_forest_shares.json
  - models/paper_forest_note.txt
  - tmp_pmc6120851/paper.txt
---

# Undersample goal

## Question

What one `/goal` line finishes the second paper forest from [[undersample plan]], and uses about 20 agents to do the year work in parallel?

## Answer

Paste this as the whole prompt in a new Grok CLI session. The parent stays the coordinator. It does not fit the forest itself.

```
/goal Finish the second Medicare forest on wiki/concepts/undersample-plan.md. You are the coordinator. Spawn 20 subagents and use their results. Do not fit the forest in this session. Do not score a year in this session.

Before the first spawn, set subagents.max_concurrent to 20 in the user config so the 20 can run together. The current value is 4, and a cap of 4 queues the rest. Leave subagents.enabled true. If that write is refused, spawn all 20 anyway and let them queue. Do not stop because the cap stayed at 4.

The 20 agents, and the only files each one may write:

1. Label 2013. Read data/paper_rolled/2013.csv and data/training/UPDATED.csv. A row is fraud when its NPI matches a 10-digit NPI, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the exclusion year is after the billing year. The earliest qualifying exclusion counts. Write data/paper_rus_parts/2013_labels.csv with npi and fraud, and data/paper_rus_parts/2013_labels.count.txt with the row count and the fraud count. Do not edit any other file.
2. Label 2014. Same rule. Write data/paper_rus_parts/2014_labels.csv and data/paper_rus_parts/2014_labels.count.txt only.
3. Label 2015. Same rule. Write data/paper_rus_parts/2015_labels.csv and data/paper_rus_parts/2015_labels.count.txt only.
4. Label 2016. Same rule. Write data/paper_rus_parts/2016_labels.csv and data/paper_rus_parts/2016_labels.count.txt only.
5. Label 2017. Same rule. Write data/paper_rus_parts/2017_labels.csv and data/paper_rus_parts/2017_labels.count.txt only.
6. Label 2018. Same rule. Write data/paper_rus_parts/2018_labels.csv and data/paper_rus_parts/2018_labels.count.txt only.
7. Label 2019. Same rule. Write data/paper_rus_parts/2019_labels.csv and data/paper_rus_parts/2019_labels.count.txt only.
8. Label 2020. Same rule. Write data/paper_rus_parts/2020_labels.csv and data/paper_rus_parts/2020_labels.count.txt only.
9. Label 2021. Same rule. Write data/paper_rus_parts/2021_labels.csv and data/paper_rus_parts/2021_labels.count.txt only.
10. Label 2022. Same rule. Write data/paper_rus_parts/2022_labels.csv and data/paper_rus_parts/2022_labels.count.txt only.
11. Label 2023. Same rule. Write data/paper_rus_parts/2023_labels.csv and data/paper_rus_parts/2023_labels.count.txt only.
12 through 18. Read-only checks, one year each, for 2018, 2019, 2020, 2021, 2022, 2023, and 2024. Open data/paper_rolled/YEAR.csv. Confirm the header has provider_type, nppes_provider_gender, and the thirty paper summaries. Write data/paper_rus_parts/YEAR_features.txt with the row count and the missing-column list. Write nothing else. Do not invent a gender. A blank gender stays blank.
19. Write scripts/paper_forest_rus.py and tests/test_paper_forest_rus.py only. The script labels with the app rule above, keeps every fraud row, undersamples clean rows with clean.sample(n=keep_clean, replace=False, random_state=0) at nine clean rows per fraud row, fits sklearn.ensemble.RandomForestClassifier with n_estimators=100, random_state=0, and n_jobs=-1, and does not set max_features or class_weight. It reads the eleven label parts, writes models/paper_forest_rus_counts.txt before the fit, writes models/paper_forest_rus.joblib, scores every real row in data/paper_rolled/2018.csv through data/paper_rolled/2024.csv into data/paper_scores_rus/, and writes models/paper_forest_rus_shares.json. It does not fit on 2024 and does not undersample 2024. The test uses a tiny frame. It does not load a year CSV and it does not fit 100 trees.
20. After agents 1 through 11 finish, and only then, run the script. Sum the eleven fraud counts. If that sum is 5900, the counts file must record 5900 fraud, 53100 clean, and 59000 total. If the sum differs, recompute clean as nine times the measured fraud count and write both numbers. Do not invent labels to reach 5900. Fit on that sample only. Score 2018 through 2024 from the real rolled files. Write the 2024 row count, the 2024 fraud count, how many of those fraud rows score above 0.00, and how many ordinary rows score above 0.00.

Spawn 1 through 19 together. Spawn 20 only after 1 through 11 have written their count files and agent 19 has written the script. Agents 12 through 18 may overlap the fit. They must not touch the year files the fit reads.

Done when all of these are true, and an independent check can open the files: models/paper_forest_rus.joblib exists; models/paper_forest_rus_counts.txt records the fraud count, the clean count, and the total; data/paper_scores_rus/2018.csv through data/paper_scores_rus/2024.csv exist; models/paper_forest_rus_shares.json records the 2024 row count, the 2024 fraud count, the fraud rows scoring above 0.00, and the ordinary rows scoring above 0.00. models/paper_forest.joblib, models/paper_forest_shares.json, models/paper_forest_note.txt, models/xgb_shallow.json, models/xgb_expanded.json, models/paper_replicate.json, scripts/train.py, scripts/paper_fit.py, scripts/paper_forest.py, data/rolled/, data/paper_scores/, and app/ are byte-for-byte unchanged. A high score is a resemblance, not a fraud finding. Do not edit the page. Do not switch the page model. That switch is a later decision.

If a label part is missing, stop and name the year. Do not download a CMS file. Do not download an LEIE file. Do not use the paper's Table 2 codes. The app's four codes stay, and the counts file records that difference.
```

Twenty agents is the fan-out. Eleven label one training year each. Seven check that 2018–2024 still have the paper features. One writes the script and its test. One runs the fit after the eleven counts exist. The fit stays one agent because twenty writers on one forest would each draw a different sample.

`~/.grok/config.toml` currently sets `subagents.max_concurrent` to 4. A spawn of 20 with that cap queues 16. The prompt tells the session to raise the cap to 20 before the first spawn. Nesting stays at one level. A subagent cannot spawn its own subagents.

The parent session coordinates. It does not fit the forest and it does not score a year. That is the work agents 1–11 and agent 20 own.

The page model stays `models/paper_forest.joblib`. This goal writes the comparison forest only. The keep rule on [[undersample plan]] decides a later switch, and that switch is not part of this goal.

## Citations

- [[undersample plan]]
- [[undersampling action-plan prompt]]
- Student request on 2026-10-20 for one `/goal` line that spins up about 20 agents and finishes the model.

## What this changes in the wiki

Filed the goal line. Did not spawn an agent, fit a model, or edit `app/`.

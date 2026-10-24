---
type: concept
title: Undersample plan
updated: 2026-10-20
tags: [app, model, planning]
sources:
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/
  - tmp_pmc6120851/paper.txt
  - models/paper_forest_shares.json
  - models/paper_forest_note.txt
---

# Undersample plan

Compiled 2026-10-20 from the `deep-research` run `wf_01a15ae53a5476d0af708d23029c8121`. That run finished Partial. The paper sampling, the score table, and the keep rule survived. The numbered fit checklist did not, because no surviving claim named a script, an input path, an output path, and a count together. This page rebuilds those steps from the surviving findings plus files already on disk. A line under Unverified is not a step.

This is one comparison forest. It does not replace `models/paper_forest.joblib`. The switch, if any, is a later decision on the real 2024 list.

## Decision

Fit one second forest on the paper's 90:10 mix. Write it to `models/paper_forest_rus.joblib`. Leave `models/paper_forest.joblib` unchanged. Keep the page model unless the keep rule below is met on the real 2024 provider list.

## Paper sampling

Opened text: `tmp_pmc6120851/paper.txt`, Bauder and Khoshgoftaar, Health Information Science and Systems, 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/. The research run could not retrieve the live PMC HTML. These sentences are from the local PDF text.

The study sampled because the Medicare dataset was severely imbalanced: "Since our Medicare dataset is severely imbalanced, we employ data sampling to mitigate the adverse effects of class imbalance."

The sampler is random undersampling: "In our study, we use random undersampling (RUS) because it retains all of the fraud labels, it affords good performance (especially with big data), and has relatively few weaknesses."

Oversampling and SMOTE were named and not used. Oversampling "balances classes by adding instances to the minority class via sampling with replacement." SMOTE "generates artificial data." Undersampling "reduces the size of the majority class by sampling without replacement."

Seven majority:minority mixes: 99.9:0.1, 99:1, 95:5, 90:10, 75:25, 65:35, and 50:50. Every fraud row is kept. Only non-fraud rows are reduced. Each repeat removes a different set of majority-class instances.

The recommendation, from the page 11 prose: "Therefore, with the good performance of RF100, and to some extent LR, with more imbalanced datasets, we recommend using the 90:10 class distribution for Medicare Part B fraud detection." That mix also retains more majority-class instances than 50:50.

The same page says the best RF100 distributions are "99:10 and 99:5." Those mixes are not in the study. Table 5 wins. The best published RF100 score is 90:10 at 0.87302. The "99:10 and 99:5" sentence stays under Unverified.

## Paper table

The metric is AUC. Each score is the average of stratified 5-fold cross-validation repeated 10 times. These figures are not a ranked real-year provider list, a top 1% share, or a top 5% share.

| Mix | Fraud rows | Non-fraud rows | RF100 AUC |
| --- | --- | --- | --- |
| 99.9:0.1 | 1,409 | 301,591 | 0.74375 |
| 99:1 | 1,409 | 139,491 | 0.85069 |
| 95:5 | 1,409 | 26,771 | 0.87246 |
| 90:10 | 1,409 | 12,681 | 0.87302 |
| 75:25 | 1,409 | 4,227 | 0.86688 |
| 65:35 | 1,409 | 2,617 | 0.86136 |
| 50:50 | 1,409 | 1,409 | 0.85299 |

The fraud and non-fraud counts are the paper's 2012–2015 study, mapped from Table 4's 1,409 fraud rows. The series is lowest at 99.9:0.1, peaks at 90:10, and is lower again toward 50:50.

The only random-forest setting the paper states is 100 trees. The seed, the feature-subspace size, and every other random-forest parameter are unnamed Weka defaults. Record `random_state=0` as a stand-in. Do not set a feature-subspace size. Do not set `class_weight`.

## Count this fit uses

The page forest's note records 5,900 fraud rows in the 2013–2023 join, from `models/paper_forest_note.txt` and `models/paper_forest_shares.json`. That total was not recomputed in the research pass. Recompute it in step 1 before sampling.

A 90:10 mix that keeps all 5,900 fraud rows has 53,100 clean rows. That is 9 clean rows per fraud row, the same ratio as the paper's 1,409 fraud and 12,681 non-fraud. If step 1 writes a different fraud count, recompute clean rows as nine times that count. Do not invent a second fraud definition to reach 5,900.

## Steps

Critical path: step 1, then step 2, then step 3. No new CMS download. No new LEIE download. Do not fit on 2024. Do not undersample the 2024 list.

Must not edit: `scripts/train.py`, `scripts/paper_fit.py`, `scripts/paper_forest.py`, `models/xgb_shallow.json`, `models/xgb_expanded.json`, `models/paper_replicate.json`, `models/paper_forest.joblib`, `models/paper_forest_shares.json`, `models/paper_forest_note.txt`, `data/rolled/`, `data/paper_scores/`, `app/`.

### 1. Label and undersample

- May create: `scripts/paper_forest_rus.py`
- Inputs already on disk: `data/paper_rolled/2013.csv` through `data/paper_rolled/2023.csv`, and `data/training/UPDATED.csv`
- May write: `models/paper_forest_rus_counts.txt`
- Label rule, same as the page forest: a row is fraud when its NPI matches a 10-digit NPI in `data/training/UPDATED.csv`, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the exclusion year is after the billing year. The earliest qualifying exclusion is the one that counts. This is not the paper's Table 2 rule. Keep it so the 2024 comparison uses the same labels as the page. Record that difference in the counts file.
- Keep every fraud row. Undersample only clean rows, without replacement, to nine clean rows per fraud row.
- Python call, opened in pandas 3.0.6 `DataFrame.sample`: `clean.sample(n=keep_clean, replace=False, random_state=0)`. `replace` defaults to False. `random_state=0` is a stand-in. The paper names no seed.
- Done when: `models/paper_forest_rus_counts.txt` records the fraud count before sampling, the clean count after sampling, and the total. If the fraud count is 5,900, the clean count must be 53,100 and the total must be 59,000.

### 2. Fit

- Uses: `scripts/paper_forest_rus.py`
- Input: the sample from step 1. Do not refit on the full 2013–2023 table.
- May write: `models/paper_forest_rus.joblib`
- Fit `sklearn.ensemble.RandomForestClassifier` with `n_estimators=100` and `random_state=0`. `n_jobs=-1` is a laptop stand-in, not a paper setting. Do not set a feature-subspace size. Do not set `class_weight`.
- Features already on each rolled row: specialty, gender, and thirty numeric summaries. The summaries are mean, sum, median, standard deviation, minimum, and maximum of line_srvc_cnt, bene_unique_cnt, bene_day_srvc_cnt, average_submitted_chrg_amt, and average_medicare_payment_amt. Gender comes from `data/nppes/npi_sex.csv`. An organization can have a blank gender. Do not invent a gender. Do not add a feature the paper did not use.
- Done when: `models/paper_forest_rus.joblib` exists and `models/paper_forest.joblib` is unchanged.

### 3. Score the real years

- Uses: `scripts/paper_forest_rus.py`
- Inputs: `data/paper_rolled/2018.csv` through `data/paper_rolled/2024.csv`, and the forest from step 2
- May write: `data/paper_scores_rus/2018.csv` through `data/paper_scores_rus/2024.csv`, and `models/paper_forest_rus_shares.json`
- Score every real rolled row in those years. Do not undersample them. Do not fit on 2024.
- For 2024, write the row count, the fraud-row count, how many of those fraud rows score above the ordinary crowd, and how many ordinary providers score above that same crowd. Ordinary crowd for this comparison is every 2024 score at or below the page forest's top 5% cutoff. That cutoff, stored in the prompt and not in the score file, is 0.00, and the page forest places every 2024 row in its top 5%. Also write the count of 2024 scores strictly above 0.00, so a later session can see whether this forest spreads the pile.
- Done when: `models/paper_forest_rus_shares.json` exists, the 2024 fraud count is written, and `app/` was not edited.

Start line for one session that fans the year work across 20 agents: [[undersample goal]]. Paste that page's fenced prompt as the whole message. The single-session line below does the same fit without the fan-out.

`/goal Do the steps on wiki/concepts/undersample-plan.md. Create scripts/paper_forest_rus.py. Label 2013-2023 from data/paper_rolled/ and data/training/UPDATED.csv with the app label rule. Keep every fraud row. Undersample clean rows without replacement to nine clean rows per fraud row. Write the fraud count, the clean count, and the total to models/paper_forest_rus_counts.txt before fitting. Fit one 100-tree forest on that sample only and write models/paper_forest_rus.joblib. Score every real 2018-2024 rolled row into data/paper_scores_rus/ and write models/paper_forest_rus_shares.json. Do not fit on 2024. Do not undersample the 2024 list. Do not edit scripts/train.py, scripts/paper_fit.py, scripts/paper_forest.py, models/paper_forest.joblib, models/xgb_shallow.json, models/xgb_expanded.json, models/paper_replicate.json, data/rolled/, data/paper_scores/, or app/.`

## Keep rule

The switch is a later decision. It is not a step in this fit.

Decide on the real 2024 provider list, not on the undersampled training mix. The two counts that matter are how many of the 48 fraud rows score above the ordinary crowd, and how many ordinary providers score above that same crowd. A higher AUC on the balanced training mix is not enough to replace the page model.

The page forest's printed 2024 shares, from `models/paper_forest_shares.json`, are top 1% 19/48 and top 5% 48/48, on 1,206,284 rows and 48 fraud rows. The top 5% cutoff of 0.00 includes every 2024 row, so that share does not separate a shorter crowd. A later switch needs the second forest to put a shorter crowd above that cutoff and to place more of the 48 fraud rows in that shorter crowd than the page forest places in its top 1% (19 of 48). Forty-eight events are below the usual 100-event floor. Keep that caveat. A high score is a resemblance, not a fraud finding.

## Gaps

The paper names no random-forest seed and no numeric feature-subspace size. `random_state=0` is a stand-in.

The app label rule is the four codes in `data/training/UPDATED.csv`. The paper's Table 2, as extracted on [[paper comparison]], uses different exclusion codes and a date rule built from exclusion length, waiver, and reinstatement. No verified finding says undersampling cannot be separated from those codes, so this fit keeps the app rule. The difference is recorded in the counts file.

The 2024 list has 48 fraud rows. That count is stored in `models/paper_forest_shares.json`. It was not re-joined from the LEIE in the research pass.

## Unverified

The live PMC HTML page was not retrieved. Claims rest on `tmp_pmc6120851/paper.txt`.

Page 11 prose says the best RF100 distributions are "99:10 and 99:5." Those are not mixes in this study. Table 5 wins.

Random forest itself "generates random datasets via sampling with replacement" to build trees. That is internal tree sampling. The class-mix sampler is without replacement.

The numeric Weka defaults for seed and feature-subspace size are not in the paper. They stay unspecified.

The 5,900 fraud-row total is recorded in `models/paper_forest_note.txt`. It was not recomputed from the rolled CSVs in the research pass.

The second forest has not been scored. The two ordinary-crowd counts are the written decision rule, not measured results.

The 2024 score file was not re-counted in the research pass. The prompt records 1,162,743 scores at 0.00 and 43,541 above zero. Those two counts are in the prompt, not in `models/paper_forest_shares.json`.

## Left open

A second learner, a grid the paper did not run, `class_weight` as a substitute for undersampling, Part D, DMEPOS, and a change to the page text. The paper does not make any of those part of the undersampling step.

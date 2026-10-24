---
type: concept
title: Leaf-size plan
updated: 2026-10-20
tags: [app, model, planning]
sources:
  - https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.RandomForestClassifier.html
  - https://scikit-learn.org/1.8/modules/generated/sklearn.tree.DecisionTreeClassifier.html
  - https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.RandomForestClassifier.html#sklearn.ensemble.RandomForestClassifier.predict_proba
  - https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
  - https://scikit-learn.org/1.8/modules/tree.html
  - models/paper_forest.joblib
  - models/paper_forest_note.txt
  - models/paper_forest_shares.json
  - scripts/paper_forest.py
---

# Leaf-size plan

Compiled 2026-10-20 from the `deep-research` run on [[leaf-size action-plan prompt]]. That run finished Partial. The leaf-stop name, the default, the `predict_proba` vote, and the keep rule survived. Several fit-step claims named a path and a count, and this page rebuilds those steps from the surviving findings plus files already on disk. A line under Unverified is not a step.

The installed sklearn is 1.8.0. The 1.8.0 pages win over the current stable 1.9.1 docs. The 1.9.1 page was opened only to check names.

This is two comparison forests. They do not replace `models/paper_forest.joblib`. The switch, if any, is a later decision on the real 2024 list.

## Decision

Fit two 100-tree forests on the same real 2013–2023 mix the page forest used. One stops a leaf at 50 rows (`min_samples_leaf=50`). The other stops a leaf at 100 rows (`min_samples_leaf=100`). Write them to `models/paper_forest_leaf50.joblib` and `models/paper_forest_leaf100.joblib`. Leave `models/paper_forest.joblib` unchanged. Keep the page model unless the keep rule below is met on the real 2024 provider list.

## Leaf stop

Opened: sklearn 1.8.0 `RandomForestClassifier`, https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.RandomForestClassifier.html, and the decision-tree page it points to, https://scikit-learn.org/1.8/modules/generated/sklearn.tree.DecisionTreeClassifier.html. The installed class is sklearn 1.8.0. The constructor argument is `min_samples_leaf`.

Quote, both pages, default 1: "The minimum number of samples required to be at a leaf node. A split point at any depth will only be considered if it leaves at least `min_samples_leaf` training samples in each of the left and right branches. This may have the effect of smoothing the model, especially in regression."

Quote, `predict_proba` on the 1.8.0 forest page: "The predicted class probabilities of an input sample are computed as the mean predicted class probabilities of the trees in the forest. The class probability of a single tree is the fraction of samples of the same class in a leaf." The decision-tree page says the same leaf vote: "The predicted class probability is the fraction of samples of the same class in a leaf." A mixed leaf therefore votes the class fraction, for example 3 fraud rows in a 50-row leaf vote 0.06. The page forest scores with `predict_proba`[:, 1] in `scripts/paper_forest.py`. The comparison forests use that same call.

The 1.8 tree user guide, https://scikit-learn.org/1.8/modules/tree.html, describes `.predict()` separately: the predicted class is the class with the highest proportion in the node, and a tie takes the lowest class index. That majority-class call is not the page score.

`min_samples_split` is a different stop. Quote, both pages, default 2: "The minimum number of samples required to split an internal node." Quote, `max_depth=None`: "If None, then nodes are expanded until all leaves are pure or until all leaves contain less than min_samples_split samples." Setting only `min_samples_leaf` is enough for this comparison. Leave `min_samples_split` at 2.

The page forest leaves `min_samples_leaf` at 1. Quote, Notes on both pages: "The default values for the parameters controlling the size of the trees (e.g. `max_depth`, `min_samples_leaf`, etc.) lead to fully grown and unpruned trees." With that default a pure leaf votes 0 or 1, and a 100-tree mean moves in steps of 0.01.

This parameter does not add labels, change the exclusion codes, undersample clean rows, set `class_weight`, or change `n_estimators`. A larger count of distinct scores is not, by itself, a better review list.

## What stays the same

The class mix stays the real 2013–2023 join. Every fraud row is kept. Clean rows are not reduced.

The four exclusion codes stay 1128a1, 1128a3, 1128b6, and 1128b7, with the exclusion year after the billing year, earliest qualifying exclusion. That is the page forest rule in `scripts/paper_forest.py`.

The forest stays 100 trees. The seed stays `random_state=0`. `n_jobs=-1` stays a laptop stand-in.

The features stay specialty, gender, and the thirty numeric summaries already on each rolled row: mean, sum, median, standard deviation, minimum, and maximum of line_srvc_cnt, bene_unique_cnt, bene_day_srvc_cnt, average_submitted_chrg_amt, and average_medicare_payment_amt. Gender comes from `data/nppes/npi_sex.csv`. An organization can have a blank gender. Do not invent a gender. Do not add a feature.

Leave `class_weight` unset. Leave `max_features` unset. Leave `min_samples_split` at 2.

## Steps

Critical path: step 1, then step 2, then step 3, then step 4, then step 5. No new CMS download. No new LEIE download. Do not fit on 2024. Do not undersample. Do not drop a fraud row.

Must not edit: `scripts/train.py`, `scripts/paper_fit.py`, `scripts/paper_forest.py`, `models/xgb_shallow.json`, `models/xgb_expanded.json`, `models/paper_replicate.json`, `models/paper_forest.joblib`, `models/paper_forest_shares.json`, `models/paper_forest_note.txt`, `models/paper_forest_rus.joblib`, `models/paper_forest_rus_shares.json`, `models/paper_forest_rus_counts.txt`, `data/rolled/`, `data/paper_scores/`, `data/paper_scores_rus/`, `app/`.

The new script may import `label_for_row`, `earliest_exclusion_years`, `design_matrix`, `load_year`, `score_year`, and `training_columns` from `scripts/paper_forest.py`. It must not edit that file.

### 1. Reuse the page-forest labels

- May create: `scripts/paper_forest_leaf.py`
- Inputs already on disk: `data/paper_rolled/2013.csv` through `data/paper_rolled/2023.csv`, and `data/training/UPDATED.csv`
- May write: `models/paper_forest_leaf_counts.txt`
- Count to write: the fraud-row total and the row total after the 2013–2023 join, before any fit
- Leaf rule this step applies: none. This step only labels.
- Label rule, same as the page forest: a row is fraud when its NPI matches a 10-digit NPI in `data/training/UPDATED.csv`, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the exclusion year is after the billing year. The earliest qualifying exclusion is the one that counts.
- Done when: `models/paper_forest_leaf_counts.txt` records `fraud=` and `rows=`. Write the measured fraud count. The page forest recorded 5,900. A later recount of the same four codes wrote 5,901. Do not invent a fraud row to close that gap.

### 2. Fit the 50-row leaf forest

- Uses: `scripts/paper_forest_leaf.py`
- Input: the labeled 2013–2023 mix from step 1. Do not undersample it. Do not drop a fraud row.
- May write: `models/paper_forest_leaf50.joblib`
- Count to write: `n_estimators=100` and `min_samples_leaf=50` beside the model, and the fraud-row total from step 1
- Leaf rule this step applies: `min_samples_leaf=50`. Leave `min_samples_split` at 2. Fit `sklearn.ensemble.RandomForestClassifier` with `n_estimators=100`, `random_state=0`, `n_jobs=-1`, and `min_samples_leaf=50`.
- Done when: `models/paper_forest_leaf50.joblib` exists and `models/paper_forest.joblib` is unchanged.

### 3. Fit the 100-row leaf forest

- Uses: `scripts/paper_forest_leaf.py`
- Input: the same labeled 2013–2023 mix from step 1. Do not undersample it. Do not drop a fraud row.
- May write: `models/paper_forest_leaf100.joblib`
- Count to write: `n_estimators=100` and `min_samples_leaf=100` beside the model, and the fraud-row total from step 1
- Leaf rule this step applies: `min_samples_leaf=100`. Leave `min_samples_split` at 2. Fit `sklearn.ensemble.RandomForestClassifier` with `n_estimators=100`, `random_state=0`, `n_jobs=-1`, and `min_samples_leaf=100`.
- Done when: `models/paper_forest_leaf100.joblib` exists and `models/paper_forest.joblib` is unchanged.

### 4. Score the real years

- Uses: `scripts/paper_forest_leaf.py`
- Inputs: `data/paper_rolled/2018.csv` through `data/paper_rolled/2024.csv`, and the two forests from steps 2 and 3
- May write: `data/paper_scores_leaf50/2018.csv` through `data/paper_scores_leaf50/2024.csv`, and `data/paper_scores_leaf100/2018.csv` through `data/paper_scores_leaf100/2024.csv`
- Count to write: each year's row count
- Leaf rule this step applies: the 50-row forest scores into `data/paper_scores_leaf50/`; the 100-row forest scores into `data/paper_scores_leaf100/`. Score every real rolled row. Do not fit on 2024. Do not undersample 2024.
- Done when: both 2024 score files exist and `data/paper_scores/` was not edited.

### 5. Write the 2024 comparison

- Uses: `scripts/paper_forest_leaf.py`
- Inputs: `data/paper_scores_leaf50/2024.csv`, `data/paper_scores_leaf100/2024.csv`, and the 2024 labels from the same four-code rule
- May write: `models/paper_forest_leaf50_shares.json` and `models/paper_forest_leaf100_shares.json`
- Count to write, for each forest: 2024 row count, number of distinct scores, number of rows still at 0.00, 2024 fraud-row count, how many of those fraud rows score above 0.00, and how many ordinary rows score above 0.00
- Leaf rule this step applies: none new. This step only reads the two scored lists.
- Done when: both shares files exist, the six counts are written in each, and `app/` was not edited.

`/goal Do the steps on wiki/concepts/leaf-size-plan.md. Create scripts/paper_forest_leaf.py. Label 2013-2023 from data/paper_rolled/ and data/training/UPDATED.csv with the app label rule already used by the page forest. Write the fraud count and the row total to models/paper_forest_leaf_counts.txt before fitting. Fit one 100-tree forest with min_samples_leaf=50 and write models/paper_forest_leaf50.joblib. Fit one 100-tree forest with min_samples_leaf=100 and write models/paper_forest_leaf100.joblib. Both fits use n_estimators=100, random_state=0, and n_jobs=-1, and leave min_samples_split at 2. Score every real 2018-2024 rolled row into data/paper_scores_leaf50/ and data/paper_scores_leaf100/. Write models/paper_forest_leaf50_shares.json and models/paper_forest_leaf100_shares.json with the 2024 row count, the distinct-score count, the 0.00 count, the fraud-row count, the fraud rows above 0.00, and the ordinary rows above 0.00. Do not fit on 2024. Do not undersample. Do not drop a fraud row. Do not edit scripts/train.py, scripts/paper_fit.py, scripts/paper_forest.py, models/paper_forest.joblib, models/paper_forest_rus.joblib, models/xgb_shallow.json, models/xgb_expanded.json, models/paper_replicate.json, data/rolled/, data/paper_scores/, data/paper_scores_rus/, or app/.`

## Keep rule

The switch is a later decision. It is not a step in this fit.

Decide on the real 2024 provider list. The counts that matter, for each comparison forest, are how many distinct scores the year has, how many rows still score 0.00, how many of the 48 fraud rows score above the ordinary crowd, and how many ordinary providers score above that same crowd. Ordinary crowd for this comparison is every 2024 score at 0.00.

A shorter crowd above 0.00 is not enough unless more of the 48 fraud rows sit in that shorter crowd than the page forest places in its top 1% (19 of 48). A higher number of unique scores is not enough to replace the page model.

The page forest's printed 2024 shares, from `models/paper_forest_shares.json`, are top 1% 19/48 and top 5% 48/48, on 1,206,284 rows and 48 fraud rows. The top 5% cutoff of 0.00 includes every 2024 row. Forty-eight events are below the usual 100-event floor. Keep that caveat. A high score is a resemblance, not a fraud finding.

## Gaps

The 2024 list has 48 fraud rows. That count is stored in `models/paper_forest_shares.json`. It was not re-joined from the LEIE in this pass.

The page forest's note records 5,900 fraud rows in the 2013–2023 join. A later recount of the same four codes, stored in `models/paper_forest_rus_counts.txt`, wrote 5,901. Step 1 writes the measured count from the page forest's label functions. Do not invent a fraud row to close the gap.

The prompt's 2013–2015 grouped counts (941,090, 963,179, 1,001,385) disagree with the count files on disk: `data/paper_rolled/2013.count.txt` is 908,542, `2014.count.txt` is 937,119, and `2015.count.txt` is 967,313. The fit note's 11,524,741 rows matches those on-disk counts. Use the rolled CSVs. The prompt's three grouped counts are stale.

The leaf-stop argument is named `min_samples_leaf` on installed sklearn 1.8.0, on the 1.8.0 docs, and on the current stable 1.9.1 page. The default is 1 on all three. `min_samples_split` is also named the same, default 2. The 1.9.1 page describes `max_samples` differently (a float is relative to `sample_weight.sum()`). That argument is not part of this leaf stop. Leave it unset.

## Unverified

The 5,900 fraud-row total is recorded in `models/paper_forest_note.txt`. It was not recomputed from the rolled CSVs in this pass.

The 2024 score file was not re-counted in this pass. The prompt records 1,206,284 rows, 25 distinct scores, 1,162,743 scores at 0.00, and 43,541 above zero. Those grain counts sit in the prompt and were not reopened from `data/paper_scores/2024.csv` here.

The two comparison forests have not been scored. The keep-rule counts are the written decision rule, not measured results.

`models/paper_forest_rus.joblib` already exists. It undersampled clean rows and left `min_samples_leaf` at 1. It is a separate experiment. This plan does not open its 2024 list as a keep-rule input.

The research run retrieved the 1.8 constructor pages as search-indexed excerpts. The leaf-stop name and the `predict_proba` quote were checked against a full scrape of those same 1.8.0 URLs and against the installed 1.8.0 class. The user-guide sentence about `.predict()` majority class was not re-fetched as a full HTML page in the compile pass.

`scripts/paper_forest_leaf.py` does not exist yet. The name follows `scripts/paper_forest_rus.py`. The brief allows a new script.

No sklearn page for the leaf stop was blocked. The vote rule used for scoring was opened on the 1.8.0 `predict_proba` documentation.

## Sources

1. Leaf stop. https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.RandomForestClassifier.html ; https://scikit-learn.org/1.8/modules/generated/sklearn.tree.DecisionTreeClassifier.html ; https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.RandomForestClassifier.html#sklearn.ensemble.RandomForestClassifier.predict_proba ; https://scikit-learn.org/1.8/modules/tree.html (`.predict()` majority class, separate from the page score)
2. What this change does not do. The same three 1.8.0 URLs. Current stable name check: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
3. Fit steps. `scripts/paper_forest.py`, `models/paper_forest_note.txt`, `data/paper_rolled/2013.csv` through `data/paper_rolled/2024.csv`, `data/training/UPDATED.csv`
4. Keep rule. `models/paper_forest_shares.json`

## Left open

A second learner, a grid of leaf sizes other than 50 and 100, `class_weight`, undersampling, more labels, Part D, DMEPOS, and a change to the page text. The opened documentation does not make any of those part of the leaf stop.

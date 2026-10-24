---
type: query
title: Leaf-size action-plan prompt
updated: 2026-10-20
tags: [query, app, model]
sources:
  - https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
  - models/paper_forest.joblib
  - data/paper_scores/2024.csv
---

# Leaf-size action-plan prompt

## Question

What prompt should deep research use so the report is an action plan for one comparison forest that stops a leaf at 50 rows and at 100 rows, and a keep-or-leave rule for the page?

## Answer

The page forest grows every tree until each leaf is pure. A tree can only vote 0 or 1. With 100 trees the score moves in steps of 0.01, and on the 2024 list 1,162,743 of 1,206,284 scores are exactly 0.00. The student asked for an action plan for one change only: stop growing a leaf once it holds 50 rows, and once it holds 100 rows, so a mixed leaf can vote a fraction and the average can take many more values. More labels are not this plan. Undersampling is not this plan. The page model stays until the 2024 list is compared.

The stock `/deep-research` runner splits a query into at most four questions when breadth is left unset. Each question returns at most six claims. A second pass keeps a claim only when it can open the cited source and support the exact statement. A numbered checklist that is not itself a verified claim gets dropped. The prompt below puts the executable fact inside each question. Do not pass a breadth outside 2–6.

The prompt to pass as the query:

```
I need an action plan a later session can execute for one comparison of Medicare fraud forests. The only change under test is the leaf stop. The page forest grows each tree until every leaf is pure, so a tree votes 0 or 1 and a 100-tree score moves in steps of 0.01. The comparison forests stop growing a leaf once it holds 50 rows, and once it holds 100 rows. A mixed leaf then votes a fraction, such as 0.03, instead of 0 or 1. Open the scikit-learn documentation for RandomForestClassifier and for the decision-tree parameter that stops a leaf. The opened documentation wins over every local note. If a page is blocked, put that item under Unverified and do not reconstruct the parameter name.

The page already scores a 100-tree random forest fit on the real class mix. Most of its 2024 scores are zero, so a top 5% list is not a short list. The question is whether stopping a leaf at 50 rows, and at 100 rows, spreads those scores enough to make a short review list more useful. Each comparison forest is a comparison. Neither replaces the page model unless the keep rule in this plan says it is better on the real 2024 list.

The audience is one person who can edit Python and fit a model on a laptop with about 16 GB of RAM. They will not read a literature survey. They need the sklearn parameter, its default, what a mixed leaf votes, ordered steps that use files already on disk, and a keep rule. Do not plan a new CMS download. Do not plan a new LEIE download. Do not plan more labels. Do not plan a change to the exclusion codes.

This run uses the stock deep-research split. Keep these four questions separate. Do not merge them. Each question may return at most six claims, and a claim survives only if a second pass can open its source. Put the executable fact in the claim itself: the parameter name, the default, the output path, and the count the step must write. A step that is not inside a surviving claim will be dropped.

1. Leaf stop. Open the scikit-learn RandomForestClassifier page and the decision-tree page it points to for the leaf-size parameter. Name the parameter that stops a leaf once it holds a minimum number of rows. Quote the default. State what a leaf votes when it still contains both classes. State whether that vote is the fraction of the class in the leaf. State whether min_samples_split is a different stop, and whether setting only the leaf-size parameter is enough. If the documentation and a local note disagree, the documentation wins and the note goes under Unverified.
2. What this change does not do. Open the same pages. State whether the leaf stop adds labels, changes the exclusion rule, undersamples clean rows, sets class_weight, or changes n_estimators. State the vote grain of a 100-tree forest when every leaf is pure, and the smaller grain a mixed leaf can add. State that a higher number of unique scores is not, by itself, a better review list. Do not treat a published AUC as a top 1% share.
3. Fit steps. Write one claim per step. Each claim names the script to create, the input path already on disk, the output path, the count to write before the next step, and the leaf rule that step applies. The steps are: reuse the label rule already used by the page forest, fit one 100-tree forest on the real 2013-2023 mix with the leaf stop at 50, fit one 100-tree forest on that same mix with the leaf stop at 100, score every real 2018-2024 rolled row for each forest, and write the 2024 comparison. Do not fit on 2024. Do not undersample. Do not drop a fraud row. Name the seed as random_state=0, the same stand-in the page forest uses. Do not assign a script you did not open. A new script is allowed. Do not edit scripts/train.py, scripts/paper_fit.py, scripts/paper_forest.py, models/xgb_shallow.json, models/xgb_expanded.json, models/paper_replicate.json, models/paper_forest.joblib, models/paper_forest_rus.joblib, or data/rolled/.
4. Keep rule. State the comparison that can decide whether the page should switch models. The comparison is on the real 2024 provider list, not on the number of unique training scores. State the counts that matter: how many distinct scores the year has, how many rows still score 0.00, how many of the 48 fraud rows score above the ordinary crowd, and how many ordinary providers score above that same crowd. State that a shorter crowd above 0.00 is not enough unless more of the 48 fraud rows sit in that shorter crowd than the page forest places in its top 1% (19 of 48). State that a high score remains a resemblance, not a fraud finding.

Known local facts. Use them as the workspace. Re-open the sklearn pages before you put a parameter name into a step. If your open disagrees with a fact below, your open wins and the fact moves to Unverified.

- Page model: models/paper_forest.joblib. One sklearn RandomForestClassifier, n_estimators=100, random_state=0, n_jobs=-1, class_weight=None, max_features=sqrt. max_depth is None. min_samples_leaf is 1. min_samples_split is 2. No undersampling. Fit once on 2013-2023. 2024 was scored and was not fit. Do not overwrite this file.
- Score grain already measured on data/paper_scores/2024.csv: 1,206,284 rows, 25 distinct scores, minimum 0.00, maximum 0.49, none below 0.00, none above 1.00. The counts are 0.00 on 1,162,743 rows, 0.01 on 36,439, 0.02 on 4,834, 0.03 on 1,209. The top 1% cutoff is 0.01 and contains 43,541 rows, including 19 of the 48 fraud rows. The top 5% cutoff is 0.00 and contains all 1,206,284 rows. The other 29 fraud rows scored 0.00.
- Same measurement on the other scored years, page forest: every year has minimum 0.00 and maximum at most 1.00, and no score below 0.00. Maxima: 2018 0.96, 2019 0.84, 2020 0.87, 2021 0.88, 2022 0.91, 2023 0.73, 2024 0.49.
- Training rows already rolled: data/paper_rolled/2013.csv through data/paper_rolled/2023.csv. Grouped counts are 2013 941,090; 2014 963,179; 2015 1,001,385; 2016 999,815; 2017 1,031,714; 2018 1,059,872; 2019 1,092,019; 2020 1,083,767; 2021 1,122,562; 2022 1,147,815; 2023 1,174,203. Sum of those counts: 11,617,421. The fit note records 11,524,741 rows after the label join. Fraud rows in that fit, by year: 2013 958, 2014 894, 2015 835, 2016 751, 2017 651, 2018 541, 2019 433, 2020 335, 2021 251, 2022 158, 2023 93. Sum: 5,900. A later recount of the same four codes wrote 5,901. Use the labels the page forest already used. Do not invent a fraud row to close that one-row gap.
- App label rule: a row is fraud when its NPI matches a 10-digit NPI in data/training/UPDATED.csv, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the exclusion year is after the billing year. The earliest qualifying exclusion is the one that counts. Keep this rule. Do not add labels from another source.
- 2024 rolled file: data/paper_rolled/2024.csv, 1,206,284 grouped rows. 2024 fraud rows under the app rule: 48. Forty-eight events are below the usual 100-event floor. The new plan must keep that caveat.
- Features already on each rolled row: specialty, gender, and thirty numeric summaries. The summaries are mean, sum, median, standard deviation, minimum, and maximum of line_srvc_cnt, bene_unique_cnt, bene_day_srvc_cnt, average_submitted_chrg_amt, and average_medicare_payment_amt. Gender comes from data/nppes/npi_sex.csv. An organization can have a blank gender. Do not invent a gender. Do not add a feature.
- Output files for the two comparison forests: models/paper_forest_leaf50.joblib and models/paper_forest_leaf100.joblib. Score files: data/paper_scores_leaf50/ and data/paper_scores_leaf100/. Do not write over data/paper_scores/ or data/paper_scores_rus/.
- A second forest already exists at models/paper_forest_rus.joblib. It undersampled clean rows to 9 per fraud row and left the leaf stop at 1. On 2024 it scored 48 of 48 fraud rows above 0.00 and also scored 1,062,235 ordinary rows above 0.00. Its top 1% held 10 of 48. It is not this experiment. Do not overwrite it. Do not combine its undersampling with this leaf stop.
- Interpreter: Python 3.14. scikit-learn 1.8.0 is installed. The requirements pin says 1.9.1. Do not upgrade it. Name the constructor argument only after you open the installed version's documentation or the source of the installed class. If 1.8.0 and the current stable page disagree, the installed version wins and the disagreement goes under Unverified.
- Protected files: models/xgb_shallow.json, models/xgb_expanded.json, models/paper_replicate.json, models/paper_forest.joblib, models/paper_forest_rus.joblib, scripts/train.py, scripts/paper_fit.py, scripts/paper_forest.py, data/rolled/, data/paper_scores/, and app/. This fit must not edit them.

Output of this research run. Write the report as an action plan. Use these sections, in this order:

- Decision. Two comparison forests, the leaf stops, the output files, and the rule for keeping or leaving the page model.
- Leaf stop. The parameter, the default, what a mixed leaf votes, and why min_samples_split is or is not part of this step. Quote the documentation.
- What stays the same. The class mix, the four exclusion codes, the 100 trees, the seed, and the features.
- Steps. Numbered. Each step names the script, the input file, the output file, the count to write, and the leaf rule it applies. The last step writes the 2024 comparison and does not change the page.
- Keep rule. The 2024 counts that decide a later switch. State that the switch is a later decision, not a step in this fit.
- Gaps. The 48-event holdout, the one-row fraud-count gap between 5,900 and 5,901, and any parameter the installed sklearn and the current docs name differently.
- Unverified. A blocked page, a parameter you could not read, or a vote rule you could not open.
- Sources. The URL you opened, next to the question number it supports.

Leave open. Do not invent a preference on these unless the opened documentation makes them part of the leaf stop: a second learner, a grid of leaf sizes other than 50 and 100, class_weight, undersampling, more labels, Part D, DMEPOS, and a change to the page text.

Do not invent a district, a school, a home address, a parent email, or a 9-digit ZIP. Do not say any forest has found fraud.
```

## Citations

- Student request on 2026-10-20 for a research prompt whose report is an action plan for stopping a leaf at 50 rows and at 100 rows.
- Page forest constructor read from models/paper_forest.joblib on 2026-10-20: min_samples_leaf=1, min_samples_split=2, max_depth=None.
- Score grain counted from data/paper_scores/2024.csv on 2026-10-20: 25 distinct scores, 1,162,743 zeros.
- [[undersampling action-plan prompt]]

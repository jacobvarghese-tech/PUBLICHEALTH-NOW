---
type: query
title: Tie-break action-plan prompt
updated: 2026-10-20
tags: [query, app, model]
sources:
  - data/paper_scores/2024.csv
  - models/paper_forest.joblib
  - app/server.py
---

# Tie-break action-plan prompt

## Question

What prompt should deep research use so the report is an action plan for one list order that breaks a tied forest score with a second fact the forest already saw, without fitting a new model?

## Answer

The page forest scores 2024 in steps of 0.01, and 1,162,743 of 1,206,284 scores are exactly 0.00. The page does not show a national ranked list. Search returns name, city, and NPI matches, ordered by name or city. A typed row gets one score and one percentile. The student asked for an action plan for option three only: when two forest scores match, sort the list a person reads by a second fact. The forest score stays tied. No new model is fit. More labels, a leaf stop, and undersampling are not this plan.

The stock `/deep-research` runner splits a query into at most four questions when breadth is left unset. Each question returns at most six claims. A second pass keeps a claim only when it can open the cited source and support the exact statement. A numbered checklist that is not itself a verified claim gets dropped. The prompt below puts the executable fact inside each question. Do not pass a breadth outside 2–6.

The prompt to pass as the query:

```
I need an action plan a later session can execute for one review list. The model does not change. The page forest already scored every 2018-2024 provider. Those scores stay. When two providers have the same forest score, the list a person reads sorts them by a second fact the forest did not use as a separate ranking key. The example fact is how unusual that provider's charge is for their specialty. The forest score stays tied. The displayed order does not.

Open a source for the tie-break rule before you name it. Prefer a statistics or ranking methods page that defines a secondary sort key, and a robust within-group scale such as a median and a median absolute deviation. The opened page wins over every local note. If a page is blocked, put that item under Unverified and do not invent the formula.

The page already scores a 100-tree random forest fit on the real class mix. Most of its 2024 scores are zero, so a top 5% list is not a short list. The page itself does not show a national ranked list. Search is by name, city, or NPI, and a typed row gets one percentile. This plan builds the list. It does not replace the forest, and it does not change the percentile, unless the keep rule says a later session should.

The audience is one person who can edit Python on a laptop with about 16 GB of RAM. They will not read a literature survey. They need the second fact, the sort rule, ordered steps that use files already on disk, and a keep rule. Do not plan a new CMS download. Do not plan a new LEIE download. Do not plan a new model. Do not plan more labels. Do not plan a leaf stop. Do not plan undersampling.

This run uses the stock deep-research split. Keep these four questions separate. Do not merge them. Each question may return at most six claims, and a claim survives only if a second pass can open its source. Put the executable fact in the claim itself: the fact name, the formula, the output path, and the count the step must write. A step that is not inside a surviving claim will be dropped.

1. Second fact. Open the ranking or robust-scale source. Name one second fact that can be computed from columns already on data/paper_rolled/2024.csv. The candidate is how unusual the charge is for that specialty. State the charge column, the group column, the center, and the scale. State whether a specialty with one provider, or a scale of zero, gets a defined value. State whether a blank gender changes this fact. The fact must not use the fraud label and must not use the forest score. If the source and a local note disagree, the source wins and the note goes under Unverified.
2. What this change does not do. State that the forest score is unchanged, the number of distinct scores is unchanged, and a tie in the score file remains a tie. State that this plan does not fit a model, does not add a label, does not stop a leaf, and does not undersample. State that a second fact the forest already used as a feature can still be a sort key, and that this is not a new feature in the model. State that a higher rank on the tie-broken list is still a resemblance, not a fraud finding.
3. List steps. Write one claim per step. Each claim names the script to create, the input path already on disk, the output path, the count to write before the next step, and the sort rule that step applies. The steps are: compute the second fact for every 2018-2024 rolled row, join it to the existing score file by NPI and year, write one ordered list per year, and write the 2024 comparison. The order is forest score descending, then the second fact descending, then NPI ascending so the order is stable. Do not fit. Do not rescore. Do not edit data/paper_scores/. Do not assign a script you did not open. A new script is allowed. Do not edit scripts/train.py, scripts/paper_fit.py, scripts/paper_forest.py, models/paper_forest.joblib, models/paper_forest_rus.joblib, models/xgb_shallow.json, models/xgb_expanded.json, models/paper_replicate.json, or data/rolled/.
4. Keep rule. State the comparison that can decide whether a later session should show this order on the page. The comparison is on the real 2024 provider list. State the counts that matter: how many of the 1,162,743 zero-score rows the second fact separates, how many of the 29 fraud rows that scored 0.00 rise above the ordinary zero-score crowd, and how many ordinary zero-score providers sit above that same crowd. State that a shorter crowd is not enough unless more of the 48 fraud rows sit in a list as short as the page forest's top 1% (43,541 names, 19 of 48) than that page list already holds. State that the forest score file stays the score. State that a high place on the list remains a resemblance, not a fraud finding.

Known local facts. Use them as the workspace. Re-open the method page before you put a formula into a step. If your open disagrees with a fact below, your open wins and the fact moves to Unverified.

- Page model: models/paper_forest.joblib. One sklearn RandomForestClassifier, n_estimators=100, random_state=0, n_jobs=-1. Fit once on 2013-2023. 2024 was scored and was not fit. Do not overwrite this file. Do not fit another forest.
- Scores already written: data/paper_scores/2018.csv through data/paper_scores/2024.csv. Columns are npi, year, score. 2024 has 1,206,284 rows, in the same NPI order as data/paper_rolled/2024.csv. The 2024 scores have 25 distinct values, minimum 0.00, maximum 0.49, none below 0.00, none above 1.00. Counts: 0.00 on 1,162,743 rows, 0.01 on 36,439, 0.02 on 4,834, 0.03 on 1,209. The top 1% cutoff is 0.01 and contains 43,541 rows, including 19 of the 48 fraud rows. The top 5% cutoff is 0.00 and contains every row. The other 29 fraud rows scored 0.00.
- Rolled rows already on disk: data/paper_rolled/2018.csv through data/paper_rolled/2024.csv. Columns include provider_type, npi, nppes_provider_gender, year, name, city, state, zip, and the thirty summaries. Charge columns already present: average_submitted_chrg_amt_mean, average_submitted_chrg_amt_sum, average_submitted_chrg_amt_median, average_submitted_chrg_amt_std, average_submitted_chrg_amt_min, average_submitted_chrg_amt_max. Specialty is provider_type. Do not add a column that is not already there.
- App label rule, for the comparison only: a row is fraud when its NPI matches a 10-digit NPI in data/training/UPDATED.csv, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the exclusion year is after the billing year. The earliest qualifying exclusion is the one that counts. The second fact must not be computed from this label. 2024 has 48 fraud rows. Forty-eight events are below the usual 100-event floor. The plan must keep that caveat.
- Page behavior today: app/server.py search_year orders city matches by city and name, and name matches by name. It does not order by score. app/page_logic.py percentile_result ranks one score among all scores and counts ties at the cutoff as inside the slice. A zero score is tied with 96% of 2024, so its percentile is about 96. This plan writes a separate list. It does not change that percentile in this fit.
- Output files: data/paper_tiebreak/2018.csv through data/paper_tiebreak/2024.csv, with npi, year, score, specialty, charge_fact, and list_rank. A note at data/paper_tiebreak/rule.txt names the formula and the sort order. Do not write over data/paper_scores/ or data/paper_scores_rus/.
- Other forests already on disk: models/paper_forest_rus.joblib undersampled clean rows and is not this experiment. models/xgb_shallow.json and models/xgb_expanded.json are not this experiment. Do not combine this sort with a new fit.
- Protected files: models/paper_forest.joblib, models/paper_forest_rus.joblib, models/xgb_shallow.json, models/xgb_expanded.json, models/paper_replicate.json, scripts/train.py, scripts/paper_fit.py, scripts/paper_forest.py, data/rolled/, data/paper_scores/, and app/. This plan must not edit them. A later page change is a later decision.

Output of this research run. Write the report as an action plan. Use these sections, in this order:

- Decision. One list order, the second fact, the output files, and the rule for showing that order on the page later.
- Second fact. The column, the group, the center, the scale, and the value used when the scale is zero. Quote the source.
- Sort rule. Score descending, second fact descending, NPI ascending. State that equal scores stay equal in the score file.
- Steps. Numbered. Each step names the script, the input file, the output file, the count to write, and the rule it applies. The last step writes the 2024 comparison and does not change the page.
- Keep rule. The 2024 counts that decide a later page change. State that the page change is a later decision, not a step in this plan.
- Gaps. The 48-event holdout, the fact that the forest already used charge as a feature, and any specialty whose scale is zero.
- Unverified. A blocked page, a formula you could not read, or a column you could not find on the rolled header.
- Sources. The URL you opened, next to the question number it supports.

Leave open. Do not invent a preference on these unless the opened source makes them part of the sort: a new model, a leaf stop, undersampling, more labels, a second fact other than specialty charge, Part D, DMEPOS, and a change to the page text.

Do not invent a district, a school, a home address, a parent email, or a 9-digit ZIP. Do not say the list has found fraud.
```

## Citations

- Student request on 2026-10-20 for a deep-research prompt whose report is an action plan for breaking a tied forest score with a second fact.
- Score grain counted from data/paper_scores/2024.csv on 2026-10-20: 25 distinct scores, 1,162,743 zeros.
- Page search order read from app/server.py search_year on 2026-10-20. It orders by name or city, not by score.
- [[leaf-size action-plan prompt]]

---
type: query
title: Undersampling action-plan prompt
updated: 2026-10-20
tags: [query, app, model]
sources:
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/
  - models/paper_forest_shares.json
  - wiki/queries/closest-paper-model-prompt.md
---

# Undersampling action-plan prompt

## Question

What prompt should deep research use so the report is an action plan for one second paper forest, trained with the paper's random undersampling, and a keep-or-leave rule for the page?

## Answer

The page forest was fit on the real class mix. On the 2024 holdout, 96% of its scores are zero, so the top 5% cutoff falls inside that pile and counts every provider. The paper's forest was not trained on that mix. It kept every fraud row and randomly undersampled clean rows. The student asked for an action plan for that step, not for a replacement of the page model before the 2024 list is compared.

The stock `/deep-research` runner splits a query into at most four questions when breadth is left unset. Each question returns at most six claims. A second pass keeps a claim only when it can open the cited source and support the exact statement. A numbered checklist that is not itself a verified claim gets dropped. The prompt below puts the executable fact inside each question. Do not pass a breadth outside 2–6.

The prompt to pass as the query:

```
I need an action plan a later session can execute for one second Medicare fraud model. The model copies the random-undersampling step from Bauder and Khoshgoftaar, "The effects of varying class distribution on learner behavior for medicare fraud detection with imbalanced big data," Health Information Science and Systems, 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/ . Open the paper. The PDF wins over every local note. If a methods page or a table is blocked, put that item under Unverified and do not reconstruct it.

The page already scores a 100-tree random forest fit on the real class mix. Most of its 2024 scores are zero, so a top 5% list is not a short list. The question is whether a second forest, trained the way the paper trained, spreads those scores enough to make a short review list more useful. The second forest is a comparison. It does not replace the page model unless the keep rule in this plan says it is better on the real 2024 list.

The audience is one person who can edit Python and fit a model on a laptop with about 16 GB of RAM. They will not read a literature survey. They need the paper's undersampling rule, the class mix, the learner settings the paper names, the settings it leaves unnamed, the metric, the published score table, and ordered steps that use files already on disk. Do not plan a new CMS download. Do not plan a new LEIE download.

This run uses the stock deep-research split. Keep these four questions separate. Do not merge them. Each question may return at most six claims, and a claim survives only if a second pass can open its source. Put the executable fact in the claim itself: the paper sentence, the class ratio, the output path, and the count the step must write. A step that is not inside a surviving claim will be dropped.

1. Paper undersampling. Open the paper. Quote the reason they sampled, the sampler they chose, and the samplers they named and did not use. Name every class mix in the selected study, which rows are kept, which rows are reduced, and whether the sampling is with or without replacement. Name the mix with the best published score for their 100-tree random forest, and quote the sentence that recommends a mix. If the prose and the score table disagree, the table wins and the prose goes under Unverified. A local note of 90:10 and AUC 0.87302 is a prior note. The paper replaces it.
2. Paper score and unnamed settings. Open the score table. Copy the 100-tree random forest score for every class mix. Name the split and the metric. Name every random-forest setting the paper states, and every setting it leaves as a software default, including the seed, the feature-subspace size, and the number of trees. State whether the paper ranks a real-year provider list, publishes a top 1% share, or publishes a top 5% share. If it does not, say so. Do not treat AUC on a balanced test fold as a top 1% share.
3. Second-fit steps. Write one claim per step. Each claim names the script to create, the input path already on disk, the output path, the count to write before the next step, and the paper rule that step applies. The steps are: label 2013-2023 from the file already on disk, keep every fraud row, undersample clean rows to the paper's best class mix, fit one 100-tree random forest on that sample only, score every real 2018-2024 rolled row, and write the 2024 comparison. Do not fit on 2024. Do not undersample the 2024 list. Map the paper's mix to a count from the measured fraud-row total below. Name the seed as a recorded stand-in if the paper names none. Do not assign a script you did not open. A new script is allowed. Do not edit scripts/train.py, scripts/paper_fit.py, models/xgb_shallow.json, models/xgb_expanded.json, models/paper_replicate.json, models/paper_forest.joblib, or data/rolled/.
4. Keep rule. State the comparison that can decide whether the page should switch models. The comparison is on the real 2024 provider list, not on the undersampled training mix. State the two counts that matter: how many of the 48 fraud rows score above the ordinary crowd, and how many ordinary providers score above that same crowd. State that a higher AUC on the balanced training mix is not enough to replace the page model. State that a high score remains a resemblance, not a fraud finding.

Known local facts. Use them as the workspace. Re-open the paper before you put a paper number into a step. If your open disagrees with a fact below, your open wins and the fact moves to Unverified.

- Page model: models/paper_forest.joblib. One sklearn RandomForestClassifier, n_estimators=100, random_state=0, n_jobs=-1. No class_weight. No undersampling. No feature-subspace size. Fit once on 2013-2023. 2024 was scored and was not fit. Do not overwrite this file. Write the second forest to models/paper_forest_rus.joblib.
- Training rows already rolled: data/paper_rolled/2013.csv through data/paper_rolled/2023.csv. Grouped counts are 2013 941,090; 2014 963,179; 2015 1,001,385; 2016 999,815; 2017 1,031,714; 2018 1,059,872; 2019 1,092,019; 2020 1,083,767; 2021 1,122,562; 2022 1,147,815; 2023 1,174,203. Sum of those counts: 11,617,421. The fit note records 11,524,741 rows after the label join.
- Fraud rows in that fit, by year: 2013 958, 2014 894, 2015 835, 2016 751, 2017 651, 2018 541, 2019 433, 2020 335, 2021 251, 2022 158, 2023 93. Sum: 5,900. A 90:10 sample that keeps all 5,900 fraud rows has 53,100 clean rows and 59,000 rows in total. Recompute the clean-row count from the mix the paper's table names. Do not invent a second fraud definition to reach that count.
- App label rule, already used by the page forest: a row is fraud when its NPI matches a 10-digit NPI in data/training/UPDATED.csv, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the exclusion year is after the billing year. The earliest qualifying exclusion is the one that counts. This is not the paper's Table 2 rule. Keep this rule for the second fit so the 2024 comparison uses the same labels as the page. Record the difference. Do not switch the second fit to the paper's exclusion codes unless the opened paper says the undersampling step cannot be separated from those codes.
- 2024 rolled file: data/paper_rolled/2024.csv, 1,206,284 grouped rows. 2024 fraud rows under the app rule: 48. Scores already written: data/paper_scores/2024.csv. Of those scores, 1,162,743 are 0.00 and 43,541 are above zero. The top 1% cutoff is 0.01 and contains 43,541 rows, including 19 of the 48 fraud rows. The top 5% cutoff is 0.00 and contains all 1,206,284 rows, including all 48 fraud rows. The other 29 fraud rows scored 0.00.
- Page shares already printed: the paper forest's 2024 top 1% share is 19/48 and its top 5% share is 48/48. The earlier shallow XGBoost shares printed beside them are 11/48 and 18/48. Forty-eight events are below the usual 100-event floor. The new plan must keep that caveat.
- Features already on each rolled row: specialty, gender, and thirty numeric summaries. The summaries are mean, sum, median, standard deviation, minimum, and maximum of line_srvc_cnt, bene_unique_cnt, bene_day_srvc_cnt, average_submitted_chrg_amt, and average_medicare_payment_amt. Gender comes from data/nppes/npi_sex.csv. An organization can have a blank gender. Do not invent a gender. Do not add a feature the paper did not use.
- Interpreter: Python 3.14. scikit-learn 1.8.0 is installed. The requirements pin says 1.9.1. Do not upgrade it. Weka is not installed. Name the Python call for random undersampling without replacement only after you open that library's documentation. If the paper names no seed, record the seed as a stand-in.
- Protected files: models/xgb_shallow.json, models/xgb_expanded.json, models/paper_replicate.json, scripts/train.py, and data/rolled/. The second fit must not edit them.

Output of this research run. Write the report as an action plan. Use these sections, in this order:

- Decision. One second forest, the class mix, the output file, and the rule for keeping or leaving the page model.
- Paper sampling. The sampler, the mixes, the keep rule, and the recommended mix. Quote the paper.
- Paper table. The 100-tree forest score for every class mix, with the split and the metric.
- Steps. Numbered. Each step names the script, the input file, the output file, the count to write, and the paper rule it applies. The last step writes the 2024 comparison and does not change the page.
- Keep rule. The 2024 counts that decide a later switch. State that the switch is a later decision, not a step in this fit.
- Gaps. The app label rule versus the paper's Table 2, the missing paper seed, and the 48-event holdout.
- Unverified. A blocked page, a table cell you could not read, or a software default you could not open.
- Sources. The URL you opened, next to the question number it supports.

Leave open. Do not invent a preference on these unless the paper makes them part of the undersampling step: a second learner, a grid the paper did not run, class_weight as a substitute for undersampling, Part D, DMEPOS, and a change to the page text.

Do not invent a district, a school, a home address, a parent email, or a 9-digit ZIP. Do not say either forest has found fraud.
```

## Citations

- Student request on 2026-10-20 for a deep-research prompt whose report is an action plan for the paper's random undersampling.
- Bauder and Khoshgoftaar, Health Information Science and Systems, 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/
- Page forest holdout counts in models/paper_forest_shares.json and data/paper_scores/2024.csv, counted 2026-10-20.
- [[closest paper-model prompt]]

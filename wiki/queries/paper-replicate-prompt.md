---
type: query
title: Paper replication action-plan prompt
updated: 2026-10-19
tags: [query, app, model]
sources:
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/
  - models/holdout_note.txt
  - models/xgb_expanded_note.txt
  - wiki/concepts/action-plan.md
---

# Paper replication action-plan prompt

## Question

What prompt should deep research use so the report is an action plan for replicating the Bauder and Khoshgoftaar 2018 Medicare fraud model?

## Answer

The student wants that plan. The replica is a comparison model. It does not replace `models/xgb_shallow.json` or `models/xgb_expanded.json`. The stock `/deep-research` runner splits a query into at most four questions when breadth is left unset. The prompt below is written for that runner. Do not pass a breadth outside 2–6.

The prompt to pass as the query:

```
I need an action plan a later session can execute to replicate one published Medicare fraud model. The paper is Bauder and Khoshgoftaar, "The effects of varying class distribution on learner behavior for medicare fraud detection with imbalanced big data," Health Information Science and Systems, 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/ . Open the paper PDF. Extract the method from the PDF. A number in this prompt that came from a local wiki note is a prior note, not a verified paper result. If the PDF disagrees with a prior note, the PDF wins. If a methods page, a table, or a supplement is blocked, put that item under Unverified and do not reconstruct it.

The audience is one person who can download CMS files, edit Python, and fit a model on a laptop with about 16 GB of RAM. They will not read a literature survey. They need the paper's learner, its settings, its features, its label rule, its years, its class mix, its split, its metric, the published score table, the files required to rebuild that table, and ordered steps. Disk size and calendar time are not constraints. A multi-gigabyte CSV is downloaded, rolled in chunks, counted, and deleted before the next file starts.

This run uses the stock deep-research split. Keep these four questions separate. Do not merge them.

1. Paper method. Open the PDF. Return the learner that produced the best published score, every setting named for that learner, the feature list in the paper's order, the class mix, the years, the train and test split, the metric, and the full score table for that learner. Name the exclusion types in the selected-rule table, including whether 1128(b)(6) and 1128(b)(7) are in it. Name the exclusion-period rule in the paper's words. Copy the best score from the table, with the class mix it belongs to. Do not treat a local note of "about 0.873" as the score.

2. Source files. Open the CMS dataset page for the physician file family the paper used, for each year the paper used. Return the CSV URL, the byte size, and the header columns that can rebuild each paper feature. Open the OIG LEIE download page and state which current file, archive, or monthly supplement can supply the exclusion types and dates the paper's rule needs. If a year has no opened URL, leave that year under Unverified. Do not invent a URL from a neighboring year.

3. Rebuild steps. Using only columns you opened, write the rollup that produces the paper's feature table. State which of this workspace's already rolled columns match a paper feature and which paper features are absent. State the sampling step that reproduces the class mix in the score table. State the split. State the one fit, with the learner and settings from question 1. Name the output file models/paper_replicate.json. Do not write models/xgb_shallow.json or models/xgb_expanded.json. Do not add a second learner. Do not grid-search a setting the paper did not search.

4. Score comparison. State the metric and the class mix that can sit beside the paper's published score. State which local numbers cannot sit beside it, including a top 1% share of a real provider-year file. Give the keep rule for calling the run a replication: the same learner, the same named settings, the same label rule, the same class mix, and a score written next to the table value. If a required file URL or a required table cell was not opened, the plan stops at that missing piece.

Source rules. Prefer the paper PDF, a CMS dataset-resources JSON, the CSV URL that returns the file, the OIG LEIE page, and the documentation page for the learner the PDF names. Deprioritize SEO explainers, vendor blogs, and Wikipedia. Open the PDF page or the resources JSON before you cite a score, a URL, a byte size, or a column name. If a page is blocked, say so. Do not cite a page you did not open.

Measured facts. Counted in this workspace. Use them as local facts. Do not treat them as paper results. Do not re-estimate them.

- The paper URL to open is https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/ . An earlier local note says the best learner was a random forest, the class mix was 90 clean to 10 fraud, the years were 2012-2015, the fraud provider-years were 1,409, and the AUC was about 0.873. Those notes were not re-opened from the PDF for this prompt. Question 1 replaces them.
- An earlier local note says the paper marked a provider fraudulent only when the claims year was before the exclusion end year and the exclusion period fell within 2012-2015. The same note says a search of the PDF for 1128(b)(6) and 1128(b)(7) was not completed. Question 1 replaces both notes.
- Saved baseline, do not overwrite: models/xgb_shallow.json. SHA-256 5A215FB6D4995C59AF0528C9427D3B29A430E6AE5B3D1893262572357D8D5531. One XGBClassifier, max_depth 4, random_state 1, 100 trees, one fit. Training years 2019-2023. Training sample 1,270 fraud rows and 11,430 clean rows. 2024 holdout 11/48 in the top 1% and 18/48 in the top 5%.
- Saved comparison file, do not overwrite: models/xgb_expanded.json. Training years 2013-2023. Fit used 5,900 fraud rows and 53,100 clean rows. 2024 holdout 8/48 in the top 1% and 19/48 in the top 5%. Both files stay in place. The replica is a third file.
- Local features, in order: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth. These are this build's features. They are not the paper's features unless question 1 finds them in the PDF.
- Local label rule: a row is fraud only when its NPI matches a 10-digit LEIE NPI, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the exclusion year is after the billing year. This is this build's rule. The replica uses the paper's rule from question 1.
- Physician rolls already on disk: data/rolled/2013.csv through data/rolled/2024.csv. Provider rows: 2013=909560, 2014=938141, 2015=968333, 2016=1000924, 2017=1032911, 2018=1061278. 2019-2024 notes are beside those files. 2012 is not rolled. LEIE on disk: data/training/UPDATED.csv. 32,790 fraud-type rows, 4,296 with a 10-digit NPI.
- Two named 2024 labs are not training labels for any model. NPI 1124725817 and NPI 1639879034. Do not put them in the replica's training file.
- The page score remains a resemblance to providers later excluded for a fraud-type reason. The replica does not change that sentence. It does not say the page has found fraud.

Decision the report must make. Write the action plan for one replica of the paper's best published model, scored with the paper's metric on the paper's class mix. The output path is models/paper_replicate.json. If the opened PDF's best model is not a random forest, follow the PDF. If the opened files cannot rebuild a required feature, stop at that feature and name the column that is missing.

Output. Use these headers.

- Decision. One paragraph. Name the learner, the years, the class mix, the metric, and the output path. Say that both saved model files stay in place.
- Paper table. The score table you opened, including the best row and the class mix on that row.
- Steps. Numbered. Each step names the script, the input files, the output file, and the count to write before the next step starts. Include the exact CSV URL and the header columns you opened. One year per download step. Delete that year's raw CSV after the roll.
- Label rule. The paper's rule, in the paper's terms. Name the exclusion types you found in the table. Name the years that are not positive.
- Score rule. The metric and the class mix that sit beside the published score. State the local top 1% and top 5% shares as a separate readout, not as the replication result.
- Unverified. A blocked PDF page, a missing year URL, a feature with no opened column, or a table cell you could not read.
- Sources. The URL you opened, next to the question number it supports.

Leave open. Do not invent a preference on these unless the PDF makes them part of a step: a second learner, a grid the paper did not run, Part D, DMEPOS, and a 2024 real-mix score for the replica.

Do not invent a district, a school, a home address, a parent email, or a 9-digit ZIP. Do not say the replica has found fraud.
```

## Citations

- Student request on 2026-10-19 for a deep-research prompt whose report is an action plan to replicate the paper's model.
- Bauder and Khoshgoftaar, Health Information Science and Systems, 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/
- [[action plan]]
- [[good flag]]
- `models/holdout_note.txt`
- `models/xgb_expanded_note.txt`

## What this changes in the wiki

Filed the prompt. It does not start the research run and it does not edit `scripts/` or `models/`.

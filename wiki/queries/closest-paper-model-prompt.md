---
type: query
title: Closest paper-model action-plan prompt
updated: 2026-10-19
tags: [query, app, model]
sources:
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/
  - http://data.nber.org/cms/providercharge/
  - http://data.nber.org/providerchargepuf/2012/
  - https://web.archive.org/web/20170627194828id_/https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv
  - wiki/queries/paper-replicate-prompt.md
---

# Closest paper-model action-plan prompt

## Question

What prompt should deep research use so the report is an action plan for the closest public rebuild of the Bauder and Khoshgoftaar 2018 Medicare fraud model?

## Answer

The student wants the closest model the public files can support. An exact copy of the published score is not the goal. A missing 2015 original file, a later gender snapshot, or an unnamed Weka seed is a recorded gap, and the plan continues.

The stock `/deep-research` runner splits a query into at most four questions when breadth is left unset. Each question returns at most six claims. A second pass keeps a claim only when it can open the cited source and support the exact statement. A numbered checklist that is not itself a verified claim gets dropped. The prompt below puts the executable fact inside each question. Do not pass a breadth outside 2–6.

The prompt to pass as the query:

```
I need an action plan a later session can execute to build the closest public model to one published Medicare fraud paper. The paper is Bauder and Khoshgoftaar, "The effects of varying class distribution on learner behavior for medicare fraud detection with imbalanced big data," Health Information Science and Systems, 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/ . Open the paper. The PDF wins over every local note. If a methods page, a table, or a supplement is blocked, put that item under Unverified and do not reconstruct it.

The goal is the closest runnable model, not an exact copy of the published score. A missing original file does not stop the plan. For each gap, name the closest public substitute you opened, say how it differs from the paper, and keep it in a step. If you opened no substitute, that one item goes under Unverified and the other steps still run. Do not tell the later session to stop before the fit.

The audience is one person who can download public files, edit Python, and fit a model on a laptop with about 16 GB of RAM. They will not read a literature survey. They need the paper's learner, the settings the paper names, the feature construction, the label rule, the years, the class mix, the split, the metric, the published score table, the closest public file for each year, and ordered steps. Disk size and calendar time are not constraints. A multi-gigabyte file is downloaded, rolled in chunks, counted, and deleted before the next file starts.

This run uses the stock deep-research split. Keep these four questions separate. Do not merge them. Each question may return at most six claims, and a claim survives only if a second pass can open its source. Put the executable fact in the claim itself: the URL, the byte size, the header names, the paper sentence, and the output path. A step that is not inside a surviving claim will be dropped.

1. Paper method. Open the paper. Name the learner that produced the best published score, every setting the paper names for that learner, and every setting it leaves unnamed. Name the grouping keys and the derived numeric features in the paper's words. Name the exclusion types in the selected-rule table, including whether 1128(b)(6) and 1128(b)(7) are in it. Quote the exclusion-period rule, the month rule, and the claims-year rule. Name the years, the class mixes, the split, the metric, and the full score table for that learner, including the best cell. A local note of random forest, 90:10, 2012-2015, 1,409 fraud provider-years, or AUC about 0.873 is a prior note. The paper replaces it.
2. Closest public files. For each paper year, open the closest public procedure-level physician file that still has gender, provider type, HCPCS, place of service, service count, beneficiary count, beneficiary-day service count, average submitted charge, and average Medicare payment. Record the URL, byte size, and header you opened. Check these pages before you look elsewhere: http://data.nber.org/providerchargepuf/2012/ , http://data.nber.org/cms/providercharge/2013/ , and http://data.nber.org/cms/providercharge/2014/ . For 2015, open an original physician PUF if one is public. If it is not, open the current CMS 2015 provider-and-service file and the public NPPES dissemination file, and state which NPPES column can supply gender and that it is a later snapshot. For labels, open a public LEIE full file from June 2017 or the nearest later 2017 snapshot that still returns bytes, including https://web.archive.org/web/20170627194828id_/https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv . Record its byte size and whether the header contains NPI, EXCLTYPE, EXCLDATE, REINDATE, and WAIVERDATE. State that today's UPDATED.csv drops reinstated people, so it is not the label file.
3. Rebuild steps. Write one claim per step. Each claim names the script to create or edit, the input URL, the output path, the count to write before the next step, and the paper rule that step applies. The steps are: download one year, roll that year by the paper's grouping keys, derive the paper's numeric features, delete the raw file, repeat until every opened year is rolled, join the opened LEIE file with the paper's exclusion types and date rule, keep every fraud row, undersample clean rows to the paper's best class mix, fit the paper's learner with only the settings the paper names, and score it with the paper's split and metric. Map each opened header name to the paper's feature name in the claim. Do not assign a script that you did not open. scripts/download_year.py rolls one row per NPI and has no gender column, so it is not the paper roll. A new script is allowed. Do not edit scripts/train.py, models/xgb_shallow.json, models/xgb_expanded.json, app/, or data/rolled/.
4. Score comparison. Open the paper's score table again. State the one cell the new score may sit beside, the class mix of that cell, and the metric. State the gaps that keep the new score from being a replication: a missing original year, a later gender snapshot, a LEIE snapshot that is not the authors' extract, and any learner setting the paper does not name. State the local top 1% and top 5% shares as a separate readout, not as the paper comparison.

Known local facts. Use them as the workspace. Re-open a public file before you put its URL, size, or header into a step. If your open disagrees with a fact below, your open wins and the fact moves to Unverified.

- Output file: models/paper_replicate.json. Both models/xgb_shallow.json and models/xgb_expanded.json stay in place. The replica is a comparison. It does not replace either saved model and it does not change the app.
- Interpreter: Python 3.14. The fit must run on a laptop with about 16 GB of RAM. Weka is not installed. If the paper's learner is a random forest, name a Python library you opened and the setting map from the paper's named settings to that library. Do not invent a seed. If the paper names no seed, say so and pick one only as a recorded stand-in.
- A prior open of the current CMS provider-and-service files for 2013, 2014, and 2015 found no nppes_provider_gender and no Rndrng_Prvdr_Gndr. Those current files are not the paper's extract. Do not use them as the gender source.
- A prior open of http://data.nber.org/providerchargepuf/2012/desc_phys2012.txt listed pgender, provider_type, plcsrvc, srvc_cnt, bene_unique_cnt, bene_day_srvc_cnt, average_submitted_chrg_amt, and average_medicare_payment_amt. The same note says that processed 2012 file has no HCPCS. Confirm that on the page. If the processed file has no HCPCS, find the original 2012 procedure-level file or record the gap and still roll the columns that exist.
- A prior open of http://data.nber.org/cms/providercharge/2013/phys2013.csv returned a header containing cyear, npi, pgender, provider_type, and medicare_parti. The zip at http://data.nber.org/cms/providercharge/2013/Medicare_Provider_Util_Payment_PUF_CY2013.zip returned Content-Length 497014400. Re-open both before using them.
- A prior directory listing showed http://data.nber.org/cms/providercharge/2014/Medicare_Provider_Util_Payment_PUF_CY2014.zip . The 2014 SAS infile and HTML page returned 403 on that pass. Re-open the zip or the directory and read the header.
- A prior directory listing of http://data.nber.org/cms/providercharge/ stopped at 2014. No 2015 directory was opened there.
- A prior HEAD of https://web.archive.org/web/20170627194828id_/https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv returned 200 and Content-Length 12069440. A ranged read began "LASTNAME","FIRSTNAME" and included NPI, EXCLTYPE, EXCLDATE, REINDATE, and WAIVERDATE. The capture date is 2017-06-27. The paper says the 2015 Medicare file was released in June 2017. Treat this snapshot as a candidate, not as the authors' file, until you open it.
- Physician rolls already on disk, data/rolled/2013.csv through data/rolled/2024.csv, are one row per NPI. They have no gender and no paper derived features. They do not rebuild the paper table. Do not edit them.
- LEIE already on disk, data/training/UPDATED.csv, is the current file. It is not the 2017 snapshot. Do not use it as the paper label source.
- The app's label rule marks fraud when the exclusion year is after the billing year and the code is 1128(a)(1), 1128(a)(3), 1128(b)(6), or 1128(b)(7). That is not the paper's rule. The paper's table and date rule win for this replica.

Output of this research run. Write the report as an action plan. Use these sections, in this order:

- Decision. The learner, the class mix, the metric, the output file, and the one published cell the new score may sit beside. Say that the result is a comparison, not a replication.
- Paper method. Grouping keys, features, label rule, years, split, and the settings the paper names. Settings the paper does not name go in the same section as gaps.
- Paper table. The learner's score column, one row per class mix.
- Closest files. One row per paper year plus one row for the LEIE file: URL, bytes, header status, and the difference from the paper.
- Steps. Numbered. Each step names the script, the input URL, the output file, the count to write, and the paper rule it applies. One year per download step. Delete that year's raw file after the roll. The last steps fit the model and write the score beside the published cell.
- Gaps. Each difference that remains after the closest public file is used. A gap is not a reason to skip the fit.
- Score rule. The metric and class mix that sit beside the published cell. State the local top 1% and top 5% shares as a separate readout.
- Unverified. A blocked page, a year with no opened file and no opened substitute, or a table cell you could not read.
- Sources. The URL you opened, next to the question number it supports.

Leave open. Do not invent a preference on these unless the paper makes them part of a step: a second learner, a grid the paper did not run, Part D, DMEPOS, and a 2024 real-mix score for the replica.

Do not invent a district, a school, a home address, a parent email, or a 9-digit ZIP. Do not say the replica has found fraud.
```

## Citations

- Student request on 2026-10-19 for a high-quality deep-research prompt whose report is an action plan to develop a model as close as possible to the paper.
- Bauder and Khoshgoftaar, Health Information Science and Systems, 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/
- NBER physician-file directories opened 2026-10-19: http://data.nber.org/cms/providercharge/ , http://data.nber.org/providerchargepuf/2012/ , http://data.nber.org/cms/providercharge/2013/ , http://data.nber.org/cms/providercharge/2014/
- June 27, 2017 LEIE snapshot opened 2026-10-19: https://web.archive.org/web/20170627194828id_/https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv
- [[paper replicate prompt]]
- [[action plan]]

## Compiled plan

The research run finished Partial on 2026-10-19. The executable plan is [[paper comparison]].

## What this changes in the wiki

Filed the prompt. It does not start the research run and it does not edit `scripts/` or `models/`.

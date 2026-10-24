---
type: query
title: Paper forest app goal
updated: 2026-10-20
tags: [query, app, model]
sources:
  - wiki/concepts/paper-comparison.md
  - wiki/concepts/action-plan.md
  - scripts/paper_roll_year.py
  - scripts/paper_fit.py
  - app/server.py
  - data/nppes/npi_sex.csv
  - data/training/UPDATED.csv
---

# Paper forest app goal

## Question

What one `/goal` line makes the paper forest usable as the lookup in place of the shallow XGBoost model?

## Answer

Paste this as the whole prompt:

```
/goal Make the paper forest the model the Medicare Fraud Flagger page scores, in place of models/xgb_shallow.json. Extend scripts/paper_roll_year.py so it can roll 2016, then 2017, then 2018, then 2019, then 2020, then 2021, then 2022, then 2023, then 2024, one year at a time, into data/paper_rolled/. Skip 2013, 2014, and 2015. Those three files and counts already exist. A year whose rolled file and count already exist is skipped. A partial download is resumed. Before a year is downloaded, open that year's CMS resources page and record the CSV URL and byte count. If the download size disagrees with the opened byte count, stop and record both sizes. Do not invent a URL. Keep name, city, state, and ZIP on the rolled row so search and the map still work. Gender still comes from data/nppes/npi_sex.csv. Delete each raw CSV after that year is rolled. Fit one RandomForestClassifier with n_estimators=100 and random_state=0 on 2013-2023 only, using the paper features and the app label rule from data/training/UPDATED.csv: EXCLTYPE in 1128a1, 1128a3, 1128b6, or 1128b7, and the exclusion year after the billing year. Do not fit on 2024. Save the forest as models/paper_forest.joblib. Score every 2018-2024 rolled row. Point app/server.py at that forest. Search by name, city, or NPI for 2018-2024 must return a percentile. A typed row is scored only when specialty, gender, and the paper numeric summaries are present. A blank stays blank and the row is marked incomplete. Show Prince Laboratories NPI 1124725817 and Reliable Results Labs NPI 1639879034 on 2024 with their percentiles. Print the 2024 top 1% and top 5% shares on the about page beside 11/48 and 18/48. The page must still say a high score is a resemblance, not a fraud finding. Leave models/xgb_shallow.json, models/xgb_expanded.json, models/paper_replicate.json, scripts/train.py, and data/rolled/ unchanged.
```

The page cannot score this forest today. Search and the form use an eight-field row from `data/rolled/` for 2018–2024. The forest needs specialty, gender, and the thirty paper summaries. Those summaries exist only for 2013–2015, and those rolled files have no name, city, state, or ZIP.

The goal is usable when a person can search a 2018–2024 provider and get a percentile from the forest, and can type a complete paper-feature row and get a score. Replacing the file path in `app/server.py` without those rows leaves the lookup with nothing to score.

Already on disk:

- 2013, 2014, and 2015 are rolled at `data/paper_rolled/`. Skip them. Do not download them again.
- Gender lookup is `data/nppes/npi_sex.csv`. Column is `Provider Sex Code`. Codes are M, F, and blank. The snapshot date is 2026-10-12.
- Column map is `data/nppes/column_map.txt`. CMS headers for 2014 and 2015 use `Rndrng_NPI`, `Rndrng_Prvdr_Type`, `HCPCS_Cd`, `Place_Of_Srvc`, `Tot_Srvcs`, `Tot_Benes`, `Tot_Bene_Day_Srvcs`, `Avg_Sbmtd_Chrg`, and `Avg_Mdcr_Pymt_Amt`. Confirm each later year's header before using that map. A header that does not match is recorded, not guessed.
- App labels are `data/training/UPDATED.csv`. That is a different file from `data/paper_rolled/leie_20170627.csv`. The June 27, 2017 capture stays the comparison file. Do not use it as the app label source.
- Opened CSV URLs and byte counts for 2018–2024 are on [[action plan]]. Re-open each year's resources page before download. The opened counts are a check, not a substitute for that open.
- 2016 and 2017 filenames and byte counts were opened. Their full URLs were not transcribed. Open those URLs. Do not invent them. The opened filenames are `MUP_PHY_R25_P04_V20_D16_Prov_Svc.csv` (3,051,491,999 bytes) and `MUP_PHY_R25_P04_V20_D17_Prov_Svc.csv` (3,086,599,908 bytes).
- The two demo NPIs are `1124725817` and `1639879034`. Both are in the 2024 app table. Show the percentile either way.

The saved XGBoost files stay. The page loads the forest. `models/paper_replicate.json` stays the 2013–2015 comparison and is not the app model.

## Citations

- [[paper comparison]]
- [[paper one-shot goal]]
- [[action plan]]
- [[scope]]
- Student request on 2026-10-20 to make the paper forest usable in place of the XGBoost model.

## What this changes in the wiki

Filed the goal line. Did not download a year, fit a model, or edit `app/`.

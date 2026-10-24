---
type: concept
title: Paper comparison
updated: 2026-10-19
tags: [app, model, planning]
sources:
  - raw/sources/pmc_extract.txt
  - raw/sources/pmc_body.txt
  - raw/sources/paper-replicate-excerpts.txt
  - raw/sources/cms_2015_resources.json
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/
  - https://web.archive.org/web/20170627194828id_/https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv
---

# Paper comparison

Compiled 2026-10-19 from the `deep-research` run on [[closest paper-model prompt]]. That run finished Partial. The live PMC HTML and PDF were not opened in the run. NCBI blocked automated retrieval, so the method and the score table rest on `raw/sources/pmc_extract.txt` and `raw/sources/pmc_body.txt`, checked against the paper URL. A numbered checklist that was not itself a surviving claim was dropped by the runner. This page rebuilds the steps from the surviving findings. A line under Unverified is not a step.

This is a comparison, not a replication. The output is `models/paper_replicate.json`. Leave `models/xgb_shallow.json` and `models/xgb_expanded.json` in place. Do not edit `scripts/train.py`, `app/`, or `data/rolled/`. This page does not change [[scope]]. The contest app stays the saved XGBoost fit.

The cell a new score may sit beside is RF100 at 90:10. The metric is AUC. The paper's cell is 0.87302. Sit the new average beside that cell only.

## Paper method

Group by specialty (provider type), provider (NPI), gender, and Medicare year. Aggregate over procedure (HCPCS) and place of service. From the original five numeric features, derive the mean, sum, median, standard deviation, minimum, and maximum.

Selected exclusion rules, from the paper's Table 2 as extracted: 1128(a)(1) (5 years), 1128(a)(2) (5 years), 1128(a)(3) (5 years), 1128(b)(4) (5 years), 1128(c)(3)(g)(i) (10 years), and 1128(c)(3)(g)(ii) (indefinite). 1128(b)(6) and 1128(b)(7) are not in that table. The current app's four codes are a different label rule. Do not copy them into this fit.

Date rule, in the paper's words: create the range of each exclusion period by adding the minimum length of the exclusion to the exclusion start date to get the exclusion end date. Compare the month and year of the exclusion end date with any waiver or reinstatement dates. The smallest month and year is the new exclusion end date. If the month is greater than 6, increase the exclusion end year to the following year. Otherwise keep the current year. Mark a provider fraudulent if the claims year is prior to the exclusion end year.

1128(c)(3)(g)(ii) is indefinite. The opened text gives no numeric length to add. Do not invent an end year for that rule. Record those rows and leave them out of the fraud class.

The learner is a random forest with 100 trees. The paper names no seed and no numeric feature-subspace size. It says subspace selection randomly assigns i features, without a value for i, and otherwise leaves random-forest settings as Weka defaults. Record `random_state=0` as a labeled stand-in, not a paper seed. Do not set a feature-subspace size.

Medicare years in the paper are 2012–2015, with 3,691,146 non-fraud and 1,409 fraud labels. The seven mixes were scored with stratified 5-fold cross-validation repeated 10 times. The metric is AUC.

| Majority:minority | RF100 AUC |
| --- | --- |
| 99.9:0.1 | 0.74375 |
| 99:1 | 0.85069 |
| 95:5 | 0.87246 |
| 90:10 | 0.87302 |
| 75:25 | 0.86688 |
| 65:35 | 0.86136 |
| 50:50 | 0.85299 |

The series is lowest at the most imbalanced mix, peaks at 90:10, and eases toward 50:50. The extract's prose says the best RF100 distributions are "99:10 and 99:5." That sentence does not match this table. Use the table.

## Files a later session may open

| Year | What was opened | What to do |
| --- | --- | --- |
| 2012 | Description only, at http://data.nber.org/providerchargepuf/2012/desc_phys2012.txt. HCPCS was removed from that public file. No data-file URL was opened. | Do not invent a URL. Skip the year. Record the skip in the output JSON. |
| 2013 | Description at http://data.nber.org/cms/providercharge/2013/desc_phys2013.txt labels `pgender` and `hcpcs_cd`. Directory lists `phys2013.csv` (2.4G) and a zip (474M). The roll-step download URL was not in the opened claim. A separate opened CMS header has no gender column. | Re-open the NBER directory. If that file's header has `pgender` and `hcpcs_cd`, roll that file. If it does not, roll the CMS file only after filling gender from NPPES, and record the substitute. |
| 2014 | CMS CSV URL below. Expected bytes 2,905,565,005. NBER also lists a 1.9G text and a 400M zip. The NBER text header was not read field by field. | Download the CMS URL. Write received bytes against 2,905,565,005. Fill gender from NPPES. |
| 2015 | CMS CSV URL below. Opened byte count 2,975,342,985. Current dictionary has no gender column. No original 2015 physician PUF on the NBER index. | Download the CMS URL. Write received bytes against 2,975,342,985. Fill gender from NPPES. |
| Labels | June 27, 2017 Wayback capture, 2,814,802 bytes. Header includes NPI, EXCLTYPE, EXCLDATE, REINDATE, WAIVERDATE. | Use this file. Do not use `data/training/UPDATED.csv`. Today's file drops reinstated people. |
| Gender | NPPES ZIP `https://download.cms.gov/nppes/NPPES_Data_Dissemination_October_2026_V2.zip`, 1,159,720,219 bytes, file date October 12, 2026. Inner CSV `npidata_pfile_20050523-20261011.csv`. Header column is `Provider Sex Code`. Lookup is `data/nppes/npi_sex.csv`: 9,852,180 NPIs, 2,298,983 M, 5,159,668 F, 2,340,086 blank. | Join `Provider Sex Code` to `Rndrng_NPI` and write it as `nppes_provider_gender`. Keep M, F, and blank. Record that the snapshot is later than the physician files. |

2014 URL: `https://data.cms.gov/sites/default/files/2025-11/6700f86d-d2e5-4f2d-9dcb-8c30412768ff/MUP_PHY_R25_P04_V20_D14_Prov_Svc.csv`

2015 URL: `https://data.cms.gov/sites/default/files/2025-11/14954ce3-4c43-43df-97e9-2c0437d7b43c/MUP_PHY_R25_P04_V20_D15_Prov_Svc.csv`

LEIE URL: `https://web.archive.org/web/20170627194828id_/https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv`

Opened CMS headers for 2013–2015 match each other and contain `Rndrng_NPI`, `Rndrng_Prvdr_Type`, `HCPCS_Cd`, and `Place_Of_Srvc`. They contain neither `nppes_provider_gender` nor `Rndrng_Prvdr_Gndr`. Map `Rndrng_NPI` to `npi`, `Rndrng_Prvdr_Type` to `provider_type`, `HCPCS_Cd` to the aggregated procedure, and `Place_Of_Srvc` to the aggregated place of service.

The five numeric names map onto those same headers. The map is also in `data/nppes/column_map.txt`.

| Paper name | Header on disk |
| --- | --- |
| `line_srvc_cnt` | `Tot_Srvcs` |
| `bene_unique_cnt` | `Tot_Benes` |
| `bene_day_srvc_cnt` | `Tot_Bene_Day_Srvcs` |
| `average_submitted_chrg_amt` | `Avg_Sbmtd_Chrg` |
| `average_medicare_payment_amt` | `Avg_Mdcr_Pymt_Amt` |

## Steps

Critical path: step 1, then step 2, then step 3, then step 4. One year at a time. Delete that year's raw CSV before the next download. A missing 2012 file is not a reason to stop before the fit.

### 1. Roll 2013

- May create: `scripts/paper_roll_year.py`
- May write: `data/paper_rolled/2013.csv`
- Must not edit: `scripts/download_year.py`, `scripts/train.py`, `data/rolled/`, `app/`, `models/xgb_shallow.json`, `models/xgb_expanded.json`
- Group by provider type, NPI, gender, and Medicare year. Aggregate over HCPCS and place of service. Write the grouped row count before deriving the six summaries. Then delete the raw file.
- If the re-opened 2013 file has `pgender` and `hcpcs_cd`, use that gender. If it does not, fill gender from NPPES Provider Sex Code and record the later snapshot.
- Done when: `data/paper_rolled/2013.csv` exists, a grouped row count is written beside it, and the raw 2013 CSV is gone.

### 2. Roll 2014

- Uses: `scripts/paper_roll_year.py`
- URL: the 2014 URL above
- May write: `data/paper_rolled/2014.csv`
- Write received bytes against 2,905,565,005 and the grouped row count. Same grouping and six summaries. Fill gender from Provider Sex Code. Delete the raw file before 2015.
- If the download size disagrees with 2,905,565,005, stop and record both sizes.

### 3. Roll 2015

- Uses: `scripts/paper_roll_year.py`
- URL: the 2015 URL above
- May write: `data/paper_rolled/2015.csv`
- Write received bytes against 2,975,342,985 and the grouped row count. Same grouping, six summaries, and Provider Sex Code fill. Delete the raw file before the join.
- If the download size disagrees with 2,975,342,985, stop and record both sizes.

### 4. Join, undersample, and fit

- May create: a new fit script. Do not edit `scripts/train.py`.
- Inputs: the June 27, 2017 LEIE capture and the three `data/paper_rolled/` year files.
- Join on NPI. Keep EXCLTYPE only for the Table 2 rules. Use EXCLDATE as the start, REINDATE as reinstatement, and WAIVERDATE as waiver. Apply the date rule above. Leave indefinite 1128(c)(3)(g)(ii) rows out of the fraud class and record the count.
- Keep every fraud row. Undersample only clean rows to nine clean rows per fraud row. The paper's 90:10 cell is 1,409 fraud and 12,681 non-fraud. The new counts need not match. Write the kept fraud count and the kept clean count before fitting.
- Fit `sklearn.ensemble.RandomForestClassifier` with only `n_estimators=100`. Record `random_state=0` as a stand-in. Do not set a feature-subspace size.
- Score with stratified 5-fold cross-validation repeated 10 times. Average the AUC. Write that score to `models/paper_replicate.json` beside the 90:10 cell, with the gaps listed below.
- Done when: `models/paper_replicate.json` exists, the two saved XGBoost files are unchanged, and `data/rolled/` and `app/` were not edited.

Start line, typed as the whole prompt tonight: `/goal Do the steps on wiki/concepts/paper-comparison.md by running python scripts/paper_oneshot.py. That script rolls 2013, then 2014, then 2015, then fits. A year whose data/paper_rolled file and count already exist is skipped. A partial download is resumed. If a download size disagrees with the expected byte count, stop and record both sizes. Write models/paper_replicate.json beside the paper cell 0.87302. Do not edit scripts/train.py, data/rolled/, app/, models/xgb_shallow.json, or models/xgb_expanded.json. A missing 2012 file is a recorded gap. Do not stop before the fit unless a byte count disagrees.`

The same line is filed at [[paper one-shot goal]].

## Gaps that stay in the output JSON

These differences remain after the closest opened files are used. None of them is a reason to skip the fit.

- No original 2012 procedure-level file was opened. The paper window is 2012–2015. This fit uses the years that were opened.
- Gender on the opened 2014 and 2015 CMS files comes from a later NPPES snapshot, not the physician extract.
- The June 27, 2017 LEIE capture is a candidate snapshot, not the authors' extract. The paper does not name its exact LEIE download date.
- The forest seed and the feature count i are unnamed. `random_state=0` is not a paper setting.
- The new fraud count need not match 1,409.
- The local top 1% and top 5% shares are a separate readout: 475/1270 of 2019–2023 fraud rows are in the top 1% of all 2019–2023 scores (0.374016), and 918/1270 are in the top 5% (0.722835). Do not treat those shares, or any other mix, as the paper comparison.

The follow-up that tries to close the holes below is [[paper-holes research prompt]]. It does not replace this plan.

## Unverified

- The live PMC HTML and PDF were not opened in the research run. The method and table rest on the local extract.
- No 2012 data-file URL or byte size was opened.
- The 2013 roll-step download URL was not in the opened claim. The 2013 description and a later CMS header disagree on gender and HCPCS. Re-open the file before choosing it.
- The 2014 NBER text header was not read field by field.
- Codes other than M and F in the October 12, 2026 `Provider Sex Code` column were blanked: 52,017 X and 1,426 U. The lookup keeps M, F, and blank.
- No LEIE data row was opened, so EXCLTYPE spelling and the date format of EXCLDATE, REINDATE, and WAIVERDATE were not verified from values.
- Weka's other RandomForest defaults were not opened.
- Figure 1 monthly frequencies and Figure 2 were not numerically extracted. No supplement was present in the extract.

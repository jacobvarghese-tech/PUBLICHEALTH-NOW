# Handoff: not enough fraud labels to train XGBoost

Date: 2026-10-15. Workspace: `C:\Users\Jacob\Downloads\congressional app`.

The student wants a Congressional App Challenge app that ranks unusual Medicare billing for medically unnecessary services, in the spirit of the Coffeezilla video transcript in this folder. A supervised XGBoost model was the first plan. That plan is blocked by labels, not by billing rows. Do not rebuild the app around a classifier until a label source below clears the gate in this file.

## Goal

Train a model whose positive class is "this biller was later sanctioned for a scheme built on medically unnecessary services." The score shown to a user must stay a resemblance or unusual-pattern score. It must not say the biller committed fraud.

If the label gate fails, ship the unsupervised ranking instead. That version is viable now and matches the video better than a weak classifier.

## What was measured

Counts below were queried from the CMS data API and the OIG LEIE file downloaded on 2026-10-15 to `C:\Users\Jacob\AppData\Local\Temp\UPDATED.csv`. That temp file is not part of the repo. Re-download it. The counting scripts are also in that temp folder and can be rerun: `count_labels.py`, `count_older.py`, `count_81.py`, `count_top_services.py`.

Billing source: Medicare Physician & Other Practitioners by Provider and Service. One row is one rendering NPI, one HCPCS code, one place of service, one year. Public years are 2013 through 2024. There is no 50-year file. The current LEIE has 84,093 records. Fraud-type records (`1128a1`, `1128a3`, `1128b7`, `1128b6`) number 32,790. Only 4,296 of those have a real NPI. In 2024 alone, 1,547 fraud-type exclusions were added and 433 had an NPI.

### Genetic-test slice

Codes used: 81408, 81415, 81416, 81417, 81418, 81419, 81420, 81425, 81432, 81433, 81435, 81440, 81443, 81445, 81448, 81450, 81455, 81479, 81518, 81519, 81528, 81541, 81542, 81546.

| Years | Rows | Unique NPIs | Fraud-type LEIE matches |
|---|---:|---:|---:|
| 2013–2020 | 1,104 | 349 | 4 |
| 2021–2024 | 1,452 | 378 | 2 |
| Unique across both | about 2,550 | under 700 | 5 |

All 5 matches are `1128b7` kickback exclusions, not the medically unnecessary code `1128b6`. Code 81419 did not exist in the early files. Prince Laboratories (`1124725817`) and Reliable Results (`1639879034`), the Deerfield Beach labs in the video, billed 81419 in 2024 and are not on the current LEIE.

A wider 2021–2024 scan of every appearing code from 81100 through 81599 found 222 codes, 15,318 rows, 891 NPIs, and 3 fraud-type matches. Widening the code list did not fix the label count.

### Broader high-risk services, 2022–2024

These are not lab tests only. The student asked whether a top-20 list of medically unnecessary services would fix the label count. It did not.

| Group | Codes queried | Rows | NPIs | Fraud-type LEIE matches |
|---|---|---:|---:|---:|
| COVID testing | U0003, U0004, U0005, 87635 | 42,786 | 22,867 | 9 |
| Remote patient monitoring | 99453, 99454, 99457, 99458, 99091 | 55,258 | 10,433 | 8 |
| Nerve conduction | 95907–95913 | 40,448 | 7,167 | 2 |
| Urine drug testing | G0480–G0483 | 17,800 | 4,915 | 6 |
| Allergy testing | 95004, 95024 | 16,381 | 5,056 | 6 |
| Skin-graft application | 15271–15278 | 6,990 | 3,235 | 2 |
| Respiratory PCR | 87631–87633 | 2,008 | 1,277 | 1 |
| Genetic codes above | 81408, 81419, 81479 | 307 | 163 | 0 |
| Power wheelchairs | K0823, K0813, K0822 | 0 | 0 | 0 |

Unique fraud-type NPIs across every group: **28**. That number is a join result. It is not the number of people convicted of unnecessary lab tests. Medicaid Fraud Control Units reported 817 fraud convictions in FY 2024. The 2025 national Medicare takedown charged 324 defendants. Those convictions mostly cannot be joined to these rows.

A match also does not mean the person was excluded for that service. The LEIE reason code does not name the HCPCS code.

## Why the obvious fixes fail

- More billing years do not exist. This table starts with 2012, and the catalog used here starts with 2013.
- The current LEIE drops reinstated people. OIG keeps monthly supplements for 12 months and does not publish an archive of old full files. Wayback snapshots of `UPDATED.csv` can recover some dropped NPIs. That is worth doing, and it will not multiply the label count by ten.
- About 90% of LEIE records have no usable NPI. Name-and-date-of-birth matching can recover some billers. A loose business-name match was tried on the genetic slice and produced false hits such as "DIGNITY HEALTH" and "AMERICAN MEDICAL." Exact normalized names only, then a human check.
- DOJ press releases and indictments mostly name owners, marketers, and ordering doctors. The billing row is the rendering NPI. An independent compilation of NPIs from DOJ healthcare-fraud press releases found only a small number that were not already on the LEIE. Scraping 2019–2025 takedown pages is worth doing for the demo examples. Expect a few dozen matched labs, not hundreds.
- An indictment is a charge. Use convicted or settled cases as labels. Keep charged-only cases in a separate "named in a case" list.
- Catheters and most skin-substitute products are not in the physician file. They are in the DMEPOS files. The physician-file count missed the largest recent schemes for that reason.

## Label gate

Do not train a classifier unless all of these are true after the searches below:

- At least 50 unique positive NPIs remain after deduplicating LEIE, DOJ, and CIA sources.
- Each positive billed one of the watched codes in a year before the sanction date.
- Positives are spread across more than one scheme. Fifty NPIs from one ownership network count as one pattern.
- A time split is possible: train on earlier billing years, test on a later year, with positives in both sides.
- The test metric is the share of held-out sanctioned NPIs landing in the top 1% and top 5% of scores. Accuracy is not a result.

If the gate fails, stop. Report the count and ship the ranking.

## Searches that have not been run

These are the remaining chances to raise the label count. Run them in this order and write the new unique-NPI count after each one.

1. **DMEPOS by Referring Provider and Service, plus the supplier file if available.** Dataset search: data.cms.gov, "Medicare Durable Medical Equipment, Devices & Supplies by Referring Provider and Service." Filter catheter codes A4351, A4352, A4353 and the high-volume skin-substitute Q codes. Join `Rfrg_NPI` to LEIE. This is the file that can see the Coffeezilla catheter scheme and the 2025 skin-graft cases. Expect the referring-doctor count to be larger than the lab count. Still apply the gate.

2. **Medicare Part D opioid and drug files are out of scope.** They are a different fraud type. Do not add them to inflate the label count.

3. **Archived LEIE snapshots.** Download the current file from https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv and the monthly supplements from https://oig.hhs.gov/exclusions/supplements.asp. Search Wayback Machine for older `UPDATED.csv` copies. Keep exclusions whose date is after the billing year. Positive types: `1128a1`, `1128a3`, `1128b6`, `1128b7`. Record `1128b6` separately. It is the closest official unnecessary-services code, and the current file has only 9 of those records with an NPI.

4. **DOJ case summaries, as a name list, not as a scrape-and-train pipeline.** Read the national takedown summary pages for 2019 through 2026 on justice.gov, including Operation Double Helix. Extract lab and supplier legal names. Resolve each name to an NPI in the CMS NPPES registry. Drop names that do not resolve. Keep convictions and settlements separate from charges. Compare the resolved NPIs with the LEIE matches and report only the new ones.

5. **OIG corporate integrity agreements.** Browse https://oig.hhs.gov/compliance/corporate-integrity-agreements/ for laboratories and wound-care companies. A CIA is a settlement outcome, so it can be a positive label. The list is small and many labs will already be in the DOJ pages.

6. **False Claims Act settlement press releases.** These name labs that paid to settle unnecessary-testing allegations and were never criminally charged. Same resolution rule: legal name to NPI, human check, count only new NPIs.

Stop after step 6 if the unique positive count is under 50. Further scraping will not change the decision.

## If the gate passes

Train one row per rendering NPI plus HCPCS code plus year. Features must be within-code, not raw dollars:

- Provider share of national services for that code and year.
- ZIP-code share of national services for that code and year.
- Services per beneficiary.
- Average submitted charge divided by the median charge for that code and year.
- Average Medicare payment divided by the median payment for that code and year.
- Year-over-year growth for the same NPI and code. Leave it missing for a new biller. XGBoost can keep missing values.
- Count of watched codes where this NPI is a new top biller in the same year.

Split by year. Train on older years and test on a later year. Weight the positive class. Keep trees shallow, around depth 4. Publish the top 1% and top 5% capture rates, the positive count, and the label sources. The page text is "this billing resembles sanctioned billers," with the feature values beside the score.

## If the gate fails

Build the ranking with no model. For a chosen code and year, sort by national share, ZIP share, growth, and charge ratio. Show the known Prince Laboratories and Reliable Results rows for 81419 so the demo can recover the video example. Show the 5 genetic LEIE matches and the 28 broader matches as known sanctioned billers the ranking can be checked against. Say plainly that there were not enough joined labels to train a fraud classifier.

The contest deadline in `AGENTS.md` is noon Eastern on 2026-10-26. The ranking version can ship inside that window. A label hunt that misses the gate cannot.

## Do not

- Do not treat the 28 as a conviction count.
- Do not mix a provider's rows across the train and test split.
- Do not use accuracy as the result.
- Do not label every LEIE record as medically unnecessary. License revocations are the largest LEIE category.
- Do not call a high score fraud on the page.
- Do not download or store beneficiary-level claims. The public use files are the allowed source.

---
type: concept
title: Action plan
updated: 2026-10-17
tags: [app, planning]
sources:
  - wiki/queries/action-plan-prompt.md
---

# Action plan

Compiled 2026-10-17 from the `deep-research-2` report. That run finished Partial. The numbered checklist it was asked for did not survive citation validation, so this page rebuilds the steps from the verified findings only. A URL below is one the report cited. A line under Unverified checks is not a step.

Critical path: step 1, then step 2, then steps 3 and 4 one year at a time, then step 5, then step 6, then step 7. Step 8 is not on the path. A public URL does not block the page.

Owners may edit only the files named on their step. Two owners must not edit the same file.

## Steps

### 1. Environment

- Owner: env
- Depends on: nothing
- May edit: `requirements.txt`, `README.md`
- Must not edit: `data/`, `models/`, `app/`
- Command: `py -3.14 -m venv .venv` then `.venv\Scripts\python -m pip install xgboost pandas`
- Done when: `requirements.txt` lists `xgboost` and `pandas`, and both import in that venv.
- Start line, typed in the Grok prompt: `/goal Do step 1 of wiki/concepts/action-plan.md. Create the venv and install xgboost and pandas. Finish only when both import in that venv and requirements.txt lists them. Do not download a year.`

Python 3.14.4 is already installed. XGBoost 3.4.1, pandas 3.0.6, and pyarrow 26.0.0 publish Windows x86-64 wheels for it. The smallest install is `xgboost` and `pandas`. Add `pyarrow` only if the rolled table is stored as Parquet. The wheels were not imported on this machine during the research. If the import fails, stop and record the error. Do not invent a second Python version until that happens.

### 2. Download the exclusion list

- Owner: labels
- Depends on: step 1
- May edit: `scripts/join_labels.py`, `data/training/`
- Must not edit: `app/`, `models/`
- URL: `https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv`
- Done when: the file is in `data/training/` and a count of rows with `EXCLTYPE` in `1128a1`, `1128a3`, `1128b6`, `1128b7` is written next to it.
- Start line, typed in the Grok prompt after step 1 is done: `/goal Do step 2 of wiki/concepts/action-plan.md. Download the LEIE file into data/training/. Finish only when that file is there and a written count of rows with EXCLTYPE in 1128a1, 1128a3, 1128b6, and 1128b7 sits next to it. Do not download a billing year.`

Columns verified in that file: `NPI`, `EXCLTYPE`, `EXCLDATE`. The four reason codes are written `1128a1`, `1128a3`, `1128b6`, `1128b7`. `EXCLDATE` values are eight-digit `YYYYMMDD`. The downloads page, fetched 2026-10-17, labeled this file as the 09-2026 file, last modified 9 October 2026. A copy from 2026-10-15 is stale.

### 3. Download one billing year

- Owner: data
- Depends on: step 1
- May edit: `scripts/download_year.py`, `data/rolled/`
- Must not edit: `app/`, `models/`
- URL: the CSV for that year in the table below. Download one year. Delete the raw CSV in the same step, after the rollup in step 4.
- Done when: `data/rolled/` has that year and the raw CSV is gone.
- Seven years, 2018 through 2024. One goal can walk them in order. Seven sequential goals isolate a bad rollup to one year. Seven goals at the same time would download seven files at once. A `/loop` is the wrong command: the next tick would start a second 3 GB download while the first year is still running. The check includes the rollup, because a goal that only downloads the CSV can never finish: the raw file has to be gone.
- Prefer 2018 alone first. If that rolled file looks right, one goal can take 2019 through 2024.
- 2018 checked 2026-10-17. `data/rolled/2018.csv` has 1,061,278 data rows and the 14 contract columns. `data/rolled/2018.note.txt` matches that count. The file is 166,982,995 bytes. `data/raw/` is empty. No raw year CSV remains. The source-row count and the download byte count were not re-read from a CMS page in this check.
- 2019 checked 2026-10-17. `data/rolled/2019.csv` has 1,093,367 data rows, no duplicate NPIs, and the 14 contract columns. The note matches. The file is 190,354,368 bytes. Every Year value is 2019. `data/raw/` is empty. Growth is filled for 981,474 rows, which is every NPI that also appears in 2018 with a non-zero service count. The formula matches this year's service count divided by the 2018 service count, minus 1, with zero mismatches. The other 111,893 rows have no 2018 match and Growth is blank. No Growth value was filled without a 2018 match or against a zero 2018 service count. `data/rolled/2018.csv` is unchanged at 166,982,995 bytes and 1,061,278 rows, all with Growth blank. The download byte count was not re-read from CMS in this check.
- Remaining years start line, 2022 then 2023 then 2024: `/goal Do steps 3 and 4 of wiki/concepts/action-plan.md for 2022, then 2023, then 2024, one year at a time. 2018, 2019, 2020, and 2021 are already rolled. Do not download them again and do not change those four files. Run scripts/download_year.py once per remaining year. 2022 uses --year 2022, --bytes 3066783950, and --url https://data.cms.gov/sites/default/files/2025-11/53fb2bae-4913-48dc-a6d4-d8c025906567/MUP_PHY_R25_P05_V20_D22_Prov_Svc.csv, and fills Growth from data/rolled/2021.csv. 2023 uses --year 2023, --bytes 3062332720, and --url https://data.cms.gov/sites/default/files/2025-04/e3f823f8-db5b-4cc7-ba04-e7ae92b99757/MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv, and fills Growth from data/rolled/2022.csv. 2024 uses --year 2024, --bytes 3250282192, and --url https://data.cms.gov/sites/default/files/2026-05/b5ebab5a-f490-418a-9bce-4b9f31419356/PHY_R26_P05_V10_D24_Prov_Svc.csv, and fills Growth from data/rolled/2023.csv. Add each year to the script's year table if it is missing. Read each file in chunks. Delete that year's raw CSV before starting the next year. Leave Growth missing when the prior year's service count is missing or 0. If a download size disagrees with that year's byte count, stop and record both sizes. Do not download two years at once. Finish only when data/rolled/2022.csv, data/rolled/2023.csv, and data/rolled/2024.csv each exist with a row count and column names written beside them, and no raw year CSV remains. Do not edit app/ or models/.`
- 2021 checked 2026-10-17. `data/rolled/2021.csv` has 1,123,589 data rows, no duplicate NPIs, and the 14 contract columns. The note matches. The file is 195,031,614 bytes. Every Year value is 2021. `data/raw/` is empty. Growth is filled for 996,091 rows, which is every NPI that also appears in 2020 with a non-zero service count. The formula matches the 2021 service count divided by the 2020 service count, minus 1, with zero mismatches. The other 127,498 rows have no 2020 match and Growth is blank. No Growth value was filled without a 2020 match or against a zero 2020 service count. The 2018, 2019, and 2020 files are unchanged at 166,982,995, 190,354,368, and 188,876,130 bytes. The download byte count was not re-read from CMS in this check.
- 2021 start line: `/goal Do steps 3 and 4 of wiki/concepts/action-plan.md for 2021 only. Run scripts/download_year.py with --year 2021, --bytes 3100222715, and --url https://data.cms.gov/sites/default/files/2025-11/bffaf97a-c2ab-4fd7-8718-be90742e3485/MUP_PHY_R25_P05_V20_D21_Prov_Svc.csv. Add 2021 to the script's year table if it is missing. Read the file in chunks and write one row per Rndrng_NPI to data/rolled/2021.csv. Fill Growth from data/rolled/2020.csv, not from 2019 or 2018. Leave Growth missing when the 2020 service count is missing or 0. Do not change data/rolled/2018.csv, data/rolled/2019.csv, or data/rolled/2020.csv. Finish only when the rolled 2021 file exists, its row count and column names are written beside it, and the raw 2021 CSV is deleted. If the download size disagrees with 3100222715, stop and record both sizes. Do not download 2022, 2023, or 2024. Do not edit app/ or models/.`
- 2020 checked 2026-10-17. `data/rolled/2020.csv` has 1,085,313 data rows, no duplicate NPIs, and the 14 contract columns. The note matches. The file is 188,876,130 bytes. Every Year value is 2020. `data/raw/` is empty. Growth is filled for 986,846 rows, which is every NPI that also appears in 2019 with a non-zero service count. The formula matches the 2020 service count divided by the 2019 service count, minus 1, with zero mismatches. The other 98,467 rows have no 2019 match and Growth is blank. No Growth value was filled without a 2019 match or against a zero 2019 service count. `data/rolled/2018.csv` and `data/rolled/2019.csv` are unchanged at 166,982,995 and 190,354,368 bytes. The download byte count was not re-read from CMS in this check.
- 2020 start line: `/goal Do steps 3 and 4 of wiki/concepts/action-plan.md for 2020 only. Run scripts/download_year.py with --year 2020, --bytes 2994090236, and --url https://data.cms.gov/sites/default/files/2025-11/d22b18cd-7726-4bf5-8e9c-3e4587c589a1/MUP_PHY_R25_P05_V20_D20_Prov_Svc.csv. Add 2020 to the script's year table if it is missing. Read the file in chunks and write one row per Rndrng_NPI to data/rolled/2020.csv. Fill Growth from data/rolled/2019.csv, not from 2018. Leave Growth missing when the 2019 service count is missing or 0. Do not change data/rolled/2018.csv or data/rolled/2019.csv. Finish only when the rolled 2020 file exists, its row count and column names are written beside it, and the raw 2020 CSV is deleted. If the download size disagrees with 2994090236, stop and record both sizes. Do not download 2021, 2022, 2023, or 2024. Do not edit app/ or models/.`
- 2019 start line: `/goal Do steps 3 and 4 of wiki/concepts/action-plan.md for 2019 only. Use the 2019 CSV URL and the byte count 3176102801. The current script is hard-coded to 2018. Change it so the year, the URL, and the byte count are arguments, and keep 2018 working. Read the file in chunks, keep only the columns in the column contract, and write one row per Rndrng_NPI to data/rolled/2019.csv. Fill Growth from data/rolled/2018.csv by joining on NPI: this year's service count divided by the 2018 service count, minus 1. Leave Growth missing when the 2018 service count is missing or 0. Do not change data/rolled/2018.csv. Finish only when the rolled 2019 file exists, its row count and column names are written beside it, and the raw 2019 CSV is deleted. If the download size disagrees with 3176102801, stop and record both sizes. Do not download 2020, 2021, 2022, 2023, or 2024. Do not edit app/ or models/.`
- 2018 start line: `/goal Do steps 3 and 4 of wiki/concepts/action-plan.md for 2018 only. Use the 2018 CSV URL and the byte count 3125246884. Read the file in chunks, keep only the columns in the column contract, and write one row per Rndrng_NPI to data/rolled/. Finish only when the rolled 2018 file exists, its row count and column names are written beside it, and the raw 2018 CSV is deleted. If the download size disagrees with 3125246884, stop and record both sizes. Do not download 2019, 2020, 2021, 2022, 2023, or 2024. Do not edit app/ or models/.`
- Start line, typed in the Grok prompt after step 1 is done: `/goal Do steps 3 and 4 of wiki/concepts/action-plan.md for 2018, then 2019, then 2020, then 2021, then 2022, then 2023, then 2024, one year at a time. Use that year's CSV URL and byte count. Read the file in chunks, keep only the columns in the column contract, and write one row per Rndrng_NPI to data/rolled/. Delete that year's raw CSV before starting the next year. Finish only when all seven rolled files exist, each has its row count and column names written beside it, and no raw year CSV remains. If a download size disagrees with the byte count on that page, stop and record the sizes. Do not download two years at once. Do not edit app/ or models/.`

| Year | CSV | Bytes |
|---|---|---|
| 2018 | https://data.cms.gov/sites/default/files/2025-11/5669eafb-f0b3-4dc5-be6d-abc09b480c2e/MUP_PHY_R25_P04_V20_D18_Prov_Svc.csv | 3,125,246,884 |
| 2019 | https://data.cms.gov/sites/default/files/2025-11/7befba27-752e-47a8-a76c-6c6d4f74f2e3/MUP_PHY_R25_P04_V20_D19_Prov_Svc.csv | 3,176,102,801 |
| 2020 | https://data.cms.gov/sites/default/files/2025-11/d22b18cd-7726-4bf5-8e9c-3e4587c589a1/MUP_PHY_R25_P05_V20_D20_Prov_Svc.csv | 2,994,090,236 |
| 2021 | https://data.cms.gov/sites/default/files/2025-11/bffaf97a-c2ab-4fd7-8718-be90742e3485/MUP_PHY_R25_P05_V20_D21_Prov_Svc.csv | 3,100,222,715 |
| 2022 | https://data.cms.gov/sites/default/files/2025-11/53fb2bae-4913-48dc-a6d4-d8c025906567/MUP_PHY_R25_P05_V20_D22_Prov_Svc.csv | 3,066,783,950 |
| 2023 | https://data.cms.gov/sites/default/files/2025-04/e3f823f8-db5b-4cc7-ba04-e7ae92b99757/MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv | 3,062,332,720 |
| 2024 | https://data.cms.gov/sites/default/files/2026-05/b5ebab5a-f490-418a-9bce-4b9f31419356/PHY_R26_P05_V10_D24_Prov_Svc.csv | 3,250,282,192 |

Byte counts came from search excerpts of the dataset-resources JSON, not from an HTTP HEAD of the CSV. Confirm the size on the first download. The 2024 id `92396110-2aed-4d63-a6a2-5d6207d46a29` is the latest-release pointer and can move when a later year is published. The year-specific id named beside it is `335e5f35-eca6-482d-87b3-f99883e213e3`.

Each year is its own dataset. One year can also be paged from `https://data.cms.gov/data-api/v1/dataset/{uuid}/data` with `size` at most 5,000 and an `offset`. No API key. Prefer the CSV. Paging a 3 GB file 5,000 rows at a time is the fallback if the CSV download fails.

Dataset ids: 2018 `fb6d9fe8-38c1-4d24-83d4-0b7b291000b2`, 2019 `867b8ac7-ccb7-4cc9-873d-b24340d89e32`, 2020 `c957b49e-1323-49e7-8678-c09da387551d`, 2021 `31dc2c47-f297-4948-bfb4-075e1bec3a02`, 2022 `e650987d-01b7-4f09-b75e-b0b075afbf98`, 2023 `0e9f2f2b-7bf9-451a-912c-e02e654dd725`.

Landing page: https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/medicare-physician-other-practitioners-by-provider-and-service/

Dictionary page: https://data.cms.gov/resources/medicare-physician-other-practitioners-by-provider-and-service-data-dictionary

Dictionary PDF: https://data.cms.gov/sites/default/files/2025-03/bbb1e50e-5ba8-42ed-b072-18368b6f37f9/MUP_PHY_RY25_20250312_DD_PRV_SVC_508.pdf

### 4. Roll that year

- Owner: data
- Depends on: step 3 for that year
- May edit: `scripts/download_year.py`, `data/rolled/`
- Must not edit: `app/`, `models/`
- Command: none verified. The script reads the columns in the contract below and writes one row per `Rndrng_NPI` for that calendar year.
- Done when: the rolled year is in `data/rolled/` and the raw CSV is gone.

A source row is one rendering NPI, one HCPCS code, and one place of service. It is not one provider-year. CMS does not define the rollup. The weighting choices in the contract are locked planning rules, not dictionary rules.

### 5. Join labels

- Owner: labels
- Depends on: steps 2 and 4 for 2019, 2020, 2021, 2022, and 2023
- May edit: `scripts/join_labels.py`, `data/training/`
- Must not edit: `app/`, `models/`
- Command: none verified. Join on `NPI` to `Rndrng_NPI`. Mark a provider-year positive only when `EXCLTYPE` is one of the four codes and the exclusion year is after the billing year.
- Done when: the fraud provider-year count for 2019–2023 is written in `data/training/`. If that count is under 200, stop. Do not train.
- Start line, after all seven rolled years exist: `/goal Do step 5 of wiki/concepts/action-plan.md. Join data/training/UPDATED.csv to the rolled files for 2019, 2020, 2021, 2022, and 2023. Match NPI to the rolled NPI column. Mark a provider-year positive only when EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7 and the exclusion year is after the billing year. Write the fraud provider-year count in data/training/. Finish when that count is written. If the count is under 200, stop and do not train. Do not change data/rolled/. Do not edit app/ or models/.`

2018 is for the growth feature only. 2024 is held out. An exclusion in or before the billing year does not mark that row positive. The published paper used 2012–2015 and a different timing rule. Keep this rule. The conflict is in Unverified checks.

One extension, billing years 2016–2018, is allowed only before 2026-10-22, then recount. Do not open 2013–2015 after that date. Those older CSV URLs were not verified.

### 6. Train

- Owner: model
- Depends on: step 5, and a fraud-row count of at least 200
- May edit: `scripts/train.py`, `models/`
- Must not edit: `data/rolled/`, `app/`
- Command: none verified. One shallow XGBoost model. Keep every fraud row. Undersample clean rows toward 90:10 for training. Also score the real mix. Do not tune. Do not train a second model.
- Done when: `models/` has one model file and a note with the share of 2024 fraud rows in the top 1% and the top 5%. Accuracy is not a result.
- Join result, 2026-10-17: `data/training/fraud_provider_year_count.txt` says 1270. That clears the 200 stop.
- Checked 2026-10-17. `models/xgb_shallow.json` loads. It has 8 features, the locked names, max depth 4, and 100 trees. One `fit` call. No search and no second model. The training sample is 1270 fraud rows and 11430 clean rows, which is 9:1. The note records the real-mix ranking score: 475/1270 in the top 1% and 918/1270 in the top 5%. The 2024 holdout is 11/48 in the top 1% and 18/48 in the top 5%. The LEIE file contains exclusion years through 2026, so a 2024 row can be labeled when the exclusion year is 2025 or 2026. Rolled file sizes are unchanged. Accuracy is not in the note. The two demo NPI percentiles were not scored in this check.
- Start line: `/goal Do step 6 of wiki/concepts/action-plan.md. The join count is 1270, so training is allowed. Train one shallow XGBoost model on 2019-2023. Keep every fraud row. Undersample clean rows toward 90:10 for training. Also score the real mix. Do not tune. Do not train a second model. Write one model file in models/ and a note with the share of 2024 fraud rows in the top 1% and the top 5%. Accuracy is not a result. Finish only when that model file and that note exist. Do not change data/rolled/. Do not edit app/.`

### 7. Page

- Owner: page
- Depends on: step 6
- May edit: `app/`
- Must not edit: `scripts/`, `models/`
- Command: none verified. A static `python -m http.server` can serve files. It cannot score a typed row. The local server has to be a small Python program that loads the model.
- Done when: the local server shows the form and the year browser on one screen, a search by name, city, or NPI fills the form, a pin opens that same row, and NPIs `1124725817` and `1639879034` each show a 2024 percentile. If either is outside the top 5%, the page says so. Every result shows the sentence that a high score is a resemblance, not a fraud finding.
- Start line: `/goal Do step 7 of wiki/concepts/action-plan.md. The model is models/xgb_shallow.json. The held-out note is models/holdout_note.txt: 11/48 of 2024 fraud rows are in the top 1%, and 18/48 are in the top 5%. Replace the Pattern Check page in app/ with Medicare Fraud Flagger. One screen, two equal parts: a form for the eight features, and a browser of the rolled 2018-2024 rows. Search by name, city, or NPI fills the form from the stored row. Typing scores a new row through a local Python server that loads the model. A static file server is not enough. Missing fields stay missing and the row is marked incomplete. A map pin uses city, state, and ZIP, and clicking it opens that same row. Score NPI 1124725817 and NPI 1639879034 on 2024. Show each percentile. If either is outside the top 5%, the page says so. Every result says a high score is a resemblance, not a fraud finding. The about page names Grok, the CMS files, the LEIE, XGBoost, and the map library, and states training years 2019-2023, 1270 fraud rows, and the 11/48 and 18/48 holdout shares. Finish only when the local server shows that screen and both percentiles. Do not change data/rolled/, scripts/, or models/.`
- Checked 2026-10-17. `python app/server.py` listened on `http://127.0.0.1:8765/` and again on `http://127.0.0.1:8766/`. Both boots printed `ready model=xgb_shallow.json scores=1207473` and a listening URL. `GET /` is one screen with the eight feature fields and year options 2018 through 2024. Search by name (`Prince Laboratories`), city (`Deerfield Beach`), and NPI `1124725817` each returned that NPI. Opening the row returned the same eight values. The pin is Deerfield Beach, FL, ZIP 33441, at 26.3111, -80.0979, and clicking it reopened NPI `1124725817`. A typed row with Growth blank stayed blank and was marked incomplete. NPI `1124725817` is 2024 percentile 99.988902 (1207339/1207473), inside the top 5%. NPI `1639879034` is 2024 percentile 99.945258 (1206812/1207473), inside the top 5%. Neither result says outside the top 5%. Every score, search, and demo result includes "A high score is a resemblance, not a fraud finding." `GET /about.html` names Grok, the CMS files, the LEIE, XGBoost, and Leaflet, and states training years 2019-2023, 1270 fraud rows, and holdout shares 11/48 and 18/48. No done-when line failed, so `app/` was not changed for this check. `data/rolled/`, `scripts/`, and `models/` were unchanged.

Missing fields stay missing. The row is marked incomplete.

### 8. Hosting, later

- Owner: notes
- Depends on: step 7, plus an AWS account and credits the student does not have
- May edit: `app/about.html`, `wiki/concepts/app-idea.md`
- Must not edit: `scripts/`, `models/`
- Done when: this step stays written here with a price source. It is not done when a URL is live.

The smallest documented Lightsail Linux bundle with a public IPv4 address is Nano-0.5GB at $5.00 USD per month, or $0.0067 USD per hour, with 2 vCPUs, 0.5 GB memory, 20 GB storage, and 1 TB of transfer. App Runner is not a shape a new account can start: AWS stopped accepting new customers on April 30, 2026. A Lambda lookup can sit inside the always-free 1 million requests and 400,000 GB-seconds. That allowance does not include storing the rolled table. Do not pick a host until the local page runs.

### 9. About page

- Owner: notes
- Depends on: step 6 for the held-out numbers, step 7 for the page
- May edit: `app/about.html`, `wiki/concepts/app-idea.md`
- Must not edit: `scripts/`, `models/`
- Done when: the about page names Grok, the CMS files, the LEIE, XGBoost, and the map library, and states the training years, the fraud-row count, and the held-out top 1% and top 5%.

## Column contract

| Our name | Source column | File | Transform |
|---|---|---|---|
| NPI | `Rndrng_NPI` | year CSV | Group key. Not a feature. |
| Name | `Rndrng_Prvdr_Last_Org_Name`, `Rndrng_Prvdr_First_Name` | year CSV | Keep for search. Not a feature. |
| City | `Rndrng_Prvdr_City` | year CSV | Pin. Not a feature. |
| State | `Rndrng_Prvdr_State_Abrvtn` | year CSV | Pin. Not a feature. |
| ZIP | `Rndrng_Prvdr_Zip5` | year CSV | Pin. Not a feature. |
| Specialty | `Rndrng_Prvdr_Type` | year CSV | Dictionary says this is the specialty with the largest number of services when more than one was reported. |
| Service count | `Tot_Srvcs` | year CSV | Sum across HCPCS and place of service for that NPI and year. The counting metric can vary by service. |
| Beneficiary count | `Tot_Benes` | year CSV | Distinct beneficiaries are per HCPCS and place of service. Summing them double-counts. The locked rule is to sum them and say so on the about page. |
| Average charge | `Avg_Sbmtd_Chrg` | year CSV | Row average. Weight by `Tot_Srvcs` when rolling to the provider-year. |
| Average payment | `Avg_Mdcr_Pymt_Amt` | year CSV | Row average, after deductible and coinsurance. Weight by `Tot_Srvcs`. |
| Charge-to-payment ratio | none | derived | Weighted average charge divided by weighted average payment. Leave missing if payment is 0. |
| Top-code share | `HCPCS_Cd`, `Tot_Srvcs` | year CSV | Largest HCPCS service count for that NPI-year, divided by the summed service count. Compute before the row collapses. |
| Growth | `Tot_Srvcs` prior year | prior year CSV | This year's service count divided by the prior year's, minus 1. Join on `Rndrng_NPI`. 2018 has no prior year in this window, so 2018 growth stays missing. |
| Year | none | file name | The calendar year of the CSV. |
| Exclusion type | `EXCLTYPE` | `UPDATED.csv` | Keep only `1128a1`, `1128a3`, `1128b6`, `1128b7`. Not a feature. |
| Exclusion date | `EXCLDATE` | `UPDATED.csv` | `YYYYMMDD`. Positive only when the year is after the billing year. Not a feature. |
| Place of service | `Place_Of_Srvc` | year CSV | Used to know a source row is not a provider-year. Dropped after the rollup. |

## Unverified checks

These are not steps.

- Byte counts were not confirmed with an HTTP HEAD of the CSV files.
- CMS does not define a provider-year rollup. The weighting rules above are planning locks.
- The record-layout PDF lists `EXCLDATE` as 8 characters and does not print the words `YYYYMMDD`. The format is from the CSV values.
- The paper's selected-rule table uses citations such as `1128(a)(1)`. A search of the PDF for `1128(b)(6)` and `1128(b)(7)` was not possible. Keep the four locked codes.
- The paper labeled a provider fraudulent only when the claims year was before the exclusion end year and the exclusion period fell within 2012–2015. This build uses a later exclusion year than the billing year, on 2019–2023. Keep this build's rule.
- The wheels were not imported on this machine. Windows ARM64 was not checked. XGBoost 3.4.1 classifiers stop at Python 3.14.
- No server file exists yet, so the local command cannot be named beyond "a Python program that loads the model." `python -m http.server` listens on port 8000 by default and cannot score a typed row.
- Lightsail's FAQ hourly arithmetic is inconsistent on the page itself. The $5 monthly cap is the figure to cite.
- The EC2 t4g.nano price was not copied from an official page.
- Older-year CSV URLs for a 2016–2018 extension were not verified.
- Leaflet was not compared with a smaller map library. Use Leaflet until a comparison is done.

## Sources

The report's source list is the authority for the URLs in the steps. Status of that run: Partial. The report body failed citation validation, so this page uses the deterministic finding list.

Related: [[scope]], [[action-plan prompt]], [[build decisions]], [[core idea]].

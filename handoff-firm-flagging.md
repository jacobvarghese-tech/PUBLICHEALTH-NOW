# Handoff: Medicare Fraud Flagger

Date: 2026-10-16. Workspace: `C:\Users\Jacob\Downloads\congressional app`.

Read this file first when the student says to start the model. Read `handoff-label-shortage.md` only for the rejected path. Do not restart the medically-unnecessary-test classifier. That gate failed.

## Decision

Build one app, Medicare Fraud Flagger. It stores the public Medicare billing history for 2013–2024, trains XGBoost on which of those providers were later excluded for a fraud-type reason, and lets a person search a provider or enter a new billing row. The score is a review flag. The page must not say the firm committed fraud.

The audience is a government official or a Medicaid Fraud Control Unit looking for a provider to check. The app does not replace their claims systems. It scores public billing numbers, or the same numbers when a person types them in.

This is the published method, not a new idea:

1. Take the Medicare Physician & Other Practitioners file.
2. Roll it to one row per provider per year.
3. Mark the row fraud if that NPI is on the OIG exclusion list for a fraud-type reason.
4. Mark every other provider not fraud.
5. Train XGBoost on the billing profile.
6. Show the percentile and the numbers behind it. A person still has to check the provider.

The published paper is Bauder and Khoshgoftaar, "The effects of varying class distribution on learner behavior for medicare fraud detection with imbalanced big data," Health Information Science and Systems, 2018. https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/

The method and the paper are public. The trained model is not. Train a new one. Do not look for a downloadable XGBoost file.

## How a person uses it

1. Search a name, city, or NPI in the 2013–2024 database, or enter a new billing row for a year the public file does not have.
2. Read the percentile and the billing numbers that produced it.
3. See the provider on the map and open that row from its pin.
4. Check the provider against the exclusion list and the source of the tip. A high percentile is a reason to keep reading.

A tip names who to look up. The model scores that provider's billing row. The allegation text is not an input.

## What the model scores

One row is one provider for one year. The name and NPI identify the row. They are not features. XGBoost scores these fields:

- Service count: how many services the provider billed that year.
- Beneficiary count: how many patients those services covered.
- Average charge: the average amount billed per service.
- Average payment: the average amount Medicare paid per service.
- Charge-to-payment ratio: average charge divided by average payment. Compute this from the two averages.
- Top-code share: the share of that year's services from the most-billed service code.
- Specialty: the provider's specialty, such as clinical laboratory.
- Growth: the change in service count from the prior year. If the provider is already in the stored data, compute this from the prior row.

Do not add a feature the student cannot explain in the demo. City, state, and ZIP place the map pin. They are not model features.

A 2025 or 2026 tip can be scored without the public file when these fields are filled in. The 2025 CMS file is not published, so the app cannot look that year up. The person supplies the row. If some fields are missing, XGBoost can still return a score. Mark that row incomplete. The result is still a resemblance flag.

## What not to rebuild

The unnecessary-test classifier is closed. Watched codes joined to 32 fraud-type NPIs. The gate was 50. Details and the code lists are in `handoff-label-shortage.md`.

These sources were checked and are not a public training set:

- CMS Fraud Prevention System. Scores claims inside Medicare. The model and the scores are not published.
- State Medicaid SURS systems. They read the state's own claims.
- Codoxo, Cotiviti, and Optum. They sell claim review to insurers. A person then reads the chart.
- CERT improper-payment rates. Public as national rates, not as provider labels.
- Claim adjustment reason code 50, "not medically necessary." On the remittance, not in the public use file.
- MFCU complaints and case files. Public output is a statewide total, or a press release that names a person. Those names do not join to the rendering NPI.

Dropping the unnecessary-test filter is what makes the project trainable. The positive class is any fraud-type exclusion, not a confirmed unnecessary test.

## Size

Measured, from the paper, Medicare Part B 2012–2015:

- 37 million procedure rows, rolled up to 3,692,555 provider-year rows.
- 1,409 fraud labels after joining LEIE and accounting for exclusion periods.
- Fraud share 0.04 percent.
- Best result: random forest, after deleting clean rows until the mix was 90:10, AUC 0.873.
- Their positive class was exclusion for patient abuse, neglect, or billing for services not rendered. It was not "this HCPCS code was medically unnecessary."

Measured, from `C:\Users\Jacob\AppData\Local\Temp\UPDATED.csv`, downloaded 2026-10-15:

- 84,093 LEIE records.
- 32,790 fraud-type records (`1128a1`, `1128a3`, `1128b7`, `1128b6`).
- 4,296 of those have a 10-digit NPI.
- 3,287 of the NPI records were excluded in 2012–2024.
- 645 more were excluded in 2025 or 2026 and can label an earlier billing year.
- License revocations are a larger category. Leave them out.

Estimate for 2012–2024, not a join we have run: about 4,600 fraud provider-year rows inside about 15 million provider-year rows. That is the paper's 1,409 over 4 years, times 13/4. Do not quote 12,000–15,000. That would require every excluded NPI to match for several years, which the paper's join did not find. Do not quote 1,500. That subtracted repeat years the 350-a-year rate already includes.

2024 physician-by-provider file: 1,296,739 providers. 2024 by-provider-and-service file: 9,449,361 rows. The model uses the service file, rolled up, so the features can include which codes dominate.

Store the rolled-up provider-year table in the app. The raw yearly files are multi-gigabyte downloads. Do not ship those files in the page.

## Demo target

The app has to recover the Coffeezilla example as a flag, not as a training label.

- Prince Laboratories Limited Liability Company, NPI `1124725817`, Deerfield Beach, Florida, ZIP 33441.
- Reliable Results Labs Inc, NPI `1639879034`, Deerfield Beach, Florida, ZIP 33441.
- Both billed HCPCS 81419 in 2023 and 2024.
- Neither is on the October 15, 2026 exclusion list, so neither is a positive training row.
- The test is whether the trained score flags them anyway.

Current ranking, already shipped, for 81419 in 2024: Prince Laboratories is rank 1 of 48. Reliable Results is rank 3 of 48. ZIP 33441 holds 23.8% of national 81419 services. That page is not the model. A firm-level score may not put these labs near the top. If it does not, say so on the page.

## What already exists

- `app/` — Pattern Check, a static ranking page. HTML, CSS, JavaScript. No framework. Open it through a local server so `app/data/rankings.json` can load.
- `app/data/rankings.json` — top 40 plus known sanctioned billers for watched codes, 2022–2024. Gate block says the classifier was not trained.
- `app/about.html` — label-count disclosure and the AI disclosure. Update it when the model exists. Do not leave the old "gate failed, so this is only a ranking" text as the description of the shipped app.
- `wiki/concepts/app-idea.md` — describes the ranking. Rewrite it when the model is the app.
- Temp files, not in the repo, safe to regenerate: `C:\Users\Jacob\AppData\Local\Temp\UPDATED.csv`, `C:\Users\Jacob\AppData\Local\Temp\genetic_panel_2021_2024.csv`, `C:\Users\Jacob\AppData\Local\Temp\label_hunt\`.

There is no trained model and no model file.

## Build order

1. Re-download the LEIE file. The October 15 copy is in temp and can go stale.
2. Download Medicare Physician & Other Practitioners by Provider and Service for 2013–2024. The dataset family starts in 2013. The paper's 2012 file was the older Physician and Other Supplier PUF. Use 2013–2024 unless that older file is easy to get in the same shape.
3. Join on NPI. A positive is a fraud-type exclusion whose exclusion year is after the billing year. Do not mark a 2024 row positive because of a 2019 exclusion. Count the overlap before training. If the fraud rows are far below the 4,600 estimate, stop and report the count.
4. Roll each provider-year to one row. Keep the eight features above, plus name, NPI, city, state, and ZIP for search and the map. Store that table as the searchable database.
5. Train XGBoost. Keep every fraud row. Undersample the clean rows toward 90:10 for training, and also report a score on the real mix. Hold out the latest billing year. Do not tune until the held-out year looks possible.
6. Score Prince Laboratories and Reliable Results on 2024. Record the percentile. If they are not near the top, say so on the page. Do not hide a miss.
7. Replace the ranking table with the model flag, or put the model flag above the existing ranking. Add a search box and a form for a new billing row. Mark an incomplete row. Add an interactive map. A pin uses city, state, and ZIP. Clicking a pin opens that provider's score. Disclose the map library.
8. Update `app/about.html`, `wiki/concepts/app-idea.md`, `wiki/overview.md`, `wiki/index.md`, and `wiki/log.md`.

## Rules for the page and the submission

- The app name on the page is Medicare Fraud Flagger.
- A high score means the billing profile resembles excluded providers. It does not mean this firm committed fraud.
- Name the exclusion types used: `1128(a)(1)`, `1128(a)(3)`, `1128(b)(6)`, and `1128(b)(7)`. A match does not say which service caused the exclusion.
- Disclose XGBoost, the CMS files, the LEIE file, the map library, and Grok's role. The student describes their own part in the portal, in their own words.
- Do not store a home address, a school name, a parent email, or a 9-digit ZIP in this repo.
- District and school are still unknown. Do not invent them. Do not submit until the district is on the participating list.
- Deadline to plan for: noon Eastern on October 26, 2026. The registration page has also said 9:00 p.m. ET. Submit earlier.

## Done when

The app runs locally, searches the 2013–2024 provider-year table, scores a provider from that table or from a typed billing row, and shows the percentile with the features behind it. Prince Laboratories and Reliable Results appear with their percentile, including a miss if they are not near the top. The map opens the same row. An incomplete tip is marked incomplete. The about page states the training years, the fraud-row count, the held-out metric, and that the flag is not a fraud finding.

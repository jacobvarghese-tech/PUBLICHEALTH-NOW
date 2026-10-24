---
type: query
title: Action-plan research prompt
updated: 2026-10-17
tags: [query, app, planning]
sources: []
---

# Action-plan research prompt

## Question

What prompt should the deep-research run use so the report can be reopened as the coding checklist?

## Answer

The workflow keeps only claims a second pass can verify. The prompt below asks for those claims in the shape of steps: a URL, a column, a command, a size, or a done-when check. When the report returns, file the standing checklist at `wiki/concepts/action-plan.md`. Do not reopen the product idea.

The prompt to pass as `args.query`:

```
Build a coding checklist for Medicare Fraud Flagger. The report will be reopened while the app is being written. Every sentence should be something a coder can do, check, or cite. Do not write a strategy essay. Do not reopen the product idea.

Write the report in this order, and skip a section only when no verified fact supports it:

1. How to use this plan. Three to five sentences. Name the critical path and the step that is not on it.
2. Numbered steps. Each step has: owner, depends on, files that owner may create or edit, files that owner must not edit, the command or URL, and Done when. Number them so a later session can say "do step 4."
3. Column contract. One table. Our feature name, the source column, the file it comes from, and the transform.
4. Unverified checks. Facts you could not confirm. A check is not a step.
5. Sources. The URL you opened, next to the step it supports.

Locked decisions. Treat these as given. Do not research them as open questions. If a source conflicts with one, put the conflict under Unverified checks and keep the lock.

- App name: Medicare Fraud Flagger. A high score means the billing profile resembles providers later excluded for a fraud-type reason. Every result shows that sentence. The page must not say the firm committed fraud.
- Data: CMS Medicare Physician & Other Practitioners by Provider and Service, calendar years 2018 through 2024. Year 2018 exists so 2019 has a prior-year service count. Train on provider-years 2019-2023. Hold out 2024. Do not mark a row positive because of an exclusion in or before that billing year.
- Labels: HHS OIG LEIE. Fraud-type reasons 1128(a)(1), 1128(a)(3), 1128(b)(6), and 1128(b)(7). A match does not name the HCPCS code. Re-download the file. A copy from 2026-10-15 may be stale.
- One XGBoost model. The only features are service count, beneficiary count, average submitted charge, average Medicare payment, charge-to-payment ratio, top-code share of that year's services, specialty, and year-over-year growth in service count. Name, NPI, city, state, and ZIP identify the row and place a map pin. They are not features. Keep every fraud row. Undersample clean rows toward 90:10 for training. Also score the real mix. Keep trees shallow. Do not tune. Do not train a second model. The held-out result is the share of 2024 fraud rows in the top 1% and the top 5%. Accuracy is not a result.
- Page: one screen, two equal parts. A form for the eight features, and a browser of the stored 2018-2024 rows. Search by name, city, or NPI fills the form. Typing scores a new row. Missing fields stay missing, and the row is marked incomplete. A map pin uses city, state, and ZIP. Clicking the pin opens that same row. Leaflet is the default map library unless you verify a smaller built-in option.
- Demo rows, not training labels: Prince Laboratories Limited Liability Company, NPI 1124725817, and Reliable Results Labs Inc, NPI 1639879034, Deerfield Beach, Florida, ZIP 33441, scored on 2024. Show the percentile either way. If either is outside the top 5%, the page says so.
- Machine, measured 2026-10-17: Windows, Python 3.14.4 at C:\Users\Jacob\AppData\Local\Programs\Python\Python314\python.exe, pip on PATH, 345 GB free on C:, 15.8 GB RAM, no AWS CLI. Workspace: C:\Users\Jacob\Downloads\congressional app. Do not store a home address, a school name, a parent email, or a 9-digit ZIP in that folder.
- Agents write the code. October 26, 2026, noon Eastern, is a motivation deadline. The plan does not wait on a student-written file. The about page still names Grok, the CMS files, the LEIE, XGBoost, and the map library.
- A local run is the critical path. AWS is a later step. The student has no AWS account and no credits. Do not put a public URL on the critical path.
- Stop the join if 2019-2023 has fewer than 200 fraud provider-year rows. One extension, billing years 2016-2018, is allowed only before 2026-10-22, then recount. Do not open 2013-2015 after that date. Do not hunt for medically-unnecessary-test labels.
- Method check only: Bauder and Khoshgoftaar, Health Information Science and Systems, 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/ . Use it to confirm the join rule. Do not look for a downloadable model. Do not adopt their feature list over the eight features above.

File owners. Steps must use these owners. Two owners must not be told to edit the same file.

- env: may edit requirements.txt and README.md. Must not edit data/, models/, or app/.
- data: may edit scripts/download_year.py and data/rolled/. May write a raw year file and must delete it in the same step. Must not edit app/ or models/.
- labels: may edit scripts/join_labels.py and data/training/. Must not edit app/ or models/.
- model: may edit scripts/train.py and models/. Must not edit data/raw, data/rolled, or app/.
- page: may edit app/. May read models/ and data/training/. Must not edit scripts/ or models/.
- notes: may edit app/about.html and wiki/concepts/app-idea.md. Must not edit scripts/ or models/.

Research these four questions. Prefer the primary page. Cite only a URL you opened. If a column name or URL cannot be verified, leave it as a check.

1. For each year 2018-2024, what is the current data.cms.gov dataset page, the CSV download URL, and the approximate file size? Which columns are required to roll one row per rendering NPI per year into the eight features plus name, NPI, city, state, and ZIP? What is the data-dictionary URL? How can one year be downloaded and rolled without keeping the other raw files?

2. What is the current OIG LEIE UPDATED.csv URL? What are the exact column names for NPI, exclusion date, and exclusion type? How are 1128(a)(1), 1128(a)(3), 1128(b)(6), and 1128(b)(7) written in that file? What date format is the exclusion date in?

3. On Python 3.14 for Windows, do xgboost, pandas, and pyarrow publish wheels as of this search? If not, what is the newest Python version that has them, and what is the install command? What is the smallest set of packages that can train this model, store a rolled table, and serve one local page? Give the pip command.

4. What is a small AWS shape that can serve this lookup later, without an account today, and what does it cost at one low-traffic demo? Which official page states that price? The local server remains the required path. Name the local command once the app exists.

Also pull from the Bauder and Khoshgoftaar paper only the join rule they used and the years they used, so the checklist can say where this build matches that paper.

Done when, for the steps you can specify:

- A year step is done when data/rolled/ has that year and the raw CSV is gone.
- The join step is done when the fraud provider-year count for 2019-2023 is written down, and the build has stopped if that count is under 200.
- The model step is done when models/ has one model and a note with the held-out top 1% and top 5% shares.
- The page step is done when a local server shows the form and the year browser, a search fills the form, a pin opens the same row, and the two demo NPIs show a percentile.
- The AWS step is done when it is written as a later step with a price source. It is not done when a URL is live.

Return verified facts only. A guessed URL is a failed step.
```

## Citations

- Student request on 2026-10-17 for a prompt whose output is a coding checklist.
- [[scope]], [[build decisions]], [[core idea]]

## What this changes in the wiki

Filed the prompt. The standing checklist does not exist until the research report is compiled into `wiki/concepts/action-plan.md`.

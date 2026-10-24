---
type: query
title: Will the action plan hit the goal
updated: 2026-10-17
tags: [query, app, planning]
sources:
  - https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv
  - https://data.cms.gov/sites/default/files/2026-05/b5ebab5a-f490-418a-9bce-4b9f31419356/PHY_R26_P05_V10_D24_Prov_Svc.csv
  - https://data.cms.gov/data-api/v1/dataset/92396110-2aed-4d63-a6a2-5d6207d46a29/data
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/
---

# Will the action plan hit the goal

## Question

Checked against the live files, will [[action plan]] hit the goal?

## Answer

The working-app goal is reachable. The "good flag" goal is reachable as a lookup for a name you already have, and the label count clears the stop line. A reliable national hunt list is not the goal, and this audit does not make it one.

Checked on 2026-10-17, after the research report:

- The 2018, 2023, and 2024 CSV URLs returned HTTP 200. A range request on the 2024 file returned `bytes 0-400/3250282192`, so the plan's 3,250,282,192 byte figure is exact. The header starts with `Rndrng_NPI`. The 2019–2022 URLs were not re-checked in this audit.
- `UPDATED.csv` downloaded at 10,802,977 bytes. Columns include `NPI`, `EXCLTYPE`, and `EXCLDATE`. The file has 84,093 rows. Fraud-type rows (`1128a1`, `1128a3`, `1128b6`, `1128b7`) number 32,790. Of those, 4,296 have a usable 10-digit NPI. The other 28,494 cannot join to the billing file on NPI.
- Exclusion years on those 4,296 NPIs include 250 in 2019, 257 in 2020, 221 in 2021, 317 in 2022, 345 in 2023, 433 in 2024, 351 in 2025, and 294 in 2026. A positive label needs the exclusion year after the billing year. Those later-year counts are large enough that the 200-row stop on [[scope]] is unlikely to trip. The overlap with providers who billed in 2019–2023 is still uncounted. That count happens at step 5.
- Prince Laboratories (`1124725817`) and Reliable Results Labs (`1639879034`) are in the current CMS release, as Clinical Laboratory, Deerfield Beach, FL, ZIP 33441. Neither NPI is in this LEIE file. They can be scored. They are not training labels. Whether they land in the top 5% is unknown until step 6.
- The current CMS release has about 9.66 million service rows. Chunked reading is still required on 16 GB of RAM.
- The 2018 paper's best AUC was about 0.873. That supports the method. It does not promise this model's top 1% capture.

The plan hits the goal if step 5 writes a fraud-row count of at least 200 and step 7 serves a percentile for a searched NPI, including the two labs. It misses the goal if the join count is under 200, or if a year cannot be rolled without exhausting memory. It does not miss the goal if the two labs score outside the top 5%. That result gets printed.

## Citations

- Live HEAD and range checks, 2026-10-17, on the 2018, 2023, and 2024 CSV URLs in [[action plan]].
- Live download of https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv the same day. Temp file deleted after the count.
- CMS data API filter on dataset `92396110-2aed-4d63-a6a2-5d6207d46a29` for the two demo NPIs.
- [[action plan]], [[scope]], [[good flag]]
- Bauder and Khoshgoftaar, 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/

## What this changes in the wiki

Filed this page. Did not change a step on [[action plan]]. The 200-row stop stays. The NPI-join gap is now a measured fact, not a worry.

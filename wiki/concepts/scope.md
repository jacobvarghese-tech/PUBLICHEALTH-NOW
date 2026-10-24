---
type: concept
title: Scope
updated: 2026-10-17
tags: [app, scope]
sources:
  - handoff-firm-flagging.md
  - raw/sources/2026-CAC-Rules.pdf
  - raw/sources/contest-brief-2026-10-15.md
---

# Scope

Locked 2026-10-17. This page narrows `handoff-firm-flagging.md` for the contest. If this page and the handoff disagree, follow this page. The idea stays Medicare Fraud Flagger. See [[core idea]].

## What the contest can reward

[[judging]] scores the idea, the implementation and design, and the coding the student can explain. [[submission]] is a working app, a public 1–3 minute video, and six written answers. Judges may ask to run the app and read the source. A small app that runs beats a deeper app that does not.

Today is 2026-10-17. The planning cutoff on [[deadline]] is noon Eastern on 2026-10-26. Nine days remain. October 24 and 25 stay free for the demo script and the written answers.

The student later said the deadline is motivation and they may not submit. Finish the app. Do not block the build on a student-written file. See [[build decisions]].

## The build

One app. The page is one screen with two equal parts: a form for the eight features, and a browser of 2018–2024. Search fills the form from a stored row. Typing scores a new row. The page shows a percentile and the eight features that produced it. A high score means the billing profile resembles providers later excluded for a fraud-type reason. The page says that on every result. It does not say the firm committed fraud.

The running app is a Python server plus one HTML page. The rolled-up table does not fit in a static JSON file. A local run stays in the build so the source works without a host. On 2026-10-17 the student said they can host it for the contest duration and buy a public URL, and they assume AWS. That replaces the earlier "local only" line. The service, the cost, and whether scores may be public are still open. See [[build decisions]].

### Data

Download Medicare Physician & Other Practitioners by Provider and Service for **2018–2024**. Re-download the OIG LEIE file. The October 15 copy can go stale.

- 2018 supplies the prior-year service count for the 2019 growth feature.
- Train on provider-years **2019–2023**.
- Hold out **2024**. Do not mark a row positive because of an exclusion in or before that billing year.
- Positive types stay `1128(a)(1)`, `1128(a)(3)`, `1128(b)(6)`, and `1128(b)(7)`. A match does not name the service.

The handoff asked for 2013–2024 and a stop if the fraud rows landed far below about 4,600. That estimate was for the long window. This page cuts the window. Twelve yearly service files are multi-gigabyte, and the video cannot show the earliest years. The published paper used four years.

The paper's 1,409 fraud provider-years over four years is about 350 a year. A 2019–2023 train window is on the order of 1,800 fraud rows if that rate holds. That number is not a join. Count the overlap before training.

### Model

One XGBoost model. Keep every fraud row. Undersample the clean rows toward 90:10 for training. Also report a score on the real mix. Trees stay shallow. Do not tune. Do not train a second algorithm.

Publish the held-out result as the share of 2024 fraud rows in the top 1% and the top 5% of scores. Accuracy is not a result. If that capture is weak, print the number on the about page and ship the flag anyway.

Features stay the eight in the handoff: service count, beneficiary count, average charge, average payment, charge-to-payment ratio, top-code share, specialty, and growth. Name, NPI, city, state, and ZIP identify the row and place the pin. They are not features.

Precompute the score for every stored row and keep it in the search table. Score a typed row live. If a typed row is missing fields, mark it incomplete. Do not fill the blanks in silence.

### Page

- Search by name, city, or NPI.
- Percentile, the eight features, and exclusion status when the NPI is on the list.
- One map. A pin uses city, state, and ZIP. Clicking the pin opens that same row. Disclose the map library. Use Leaflet unless a smaller built-in option appears while building.
- A form for a new billing row, with an incomplete mark.
- The same disclaimer on the result and on the about page.
- About page: training years, fraud-row count, held-out top 1% and top 5%, libraries, and Grok's role. The student describes their own part in the portal, in their own words.

Score Prince Laboratories (NPI `1124725817`) and Reliable Results Labs (NPI `1639879034`) on 2024. Show the percentile either way. Treat the top 5% as the line for "near the top" in the demo script. A miss stays on the page.

The app name on the page is Medicare Fraud Flagger.

## Schedule

- Through October 22: download, join, count, train, and score the two labs.
- October 23: the page runs end to end. Search, stored score, map, typed row, about page.
- October 24–25: demo beats and the six written answers. Recording waits on the student.
- October 26, before noon Eastern: submit only if the district is on the participating list. An unknown district still blocks the portal. Do not invent it.

## Stop conditions

Stop and report the count if the 2019–2023 join has fewer than 200 fraud provider-year rows. That threshold is a planning rule, not a measured result.

Before October 22, a thin count allows one extension, to billing years 2016–2018, and one recount. After that extension, train on what you have or stop. Do not open 2013–2015 after October 22. Do not reopen the medically unnecessary-test hunt in `handoff-label-shortage.md`.

If a download or the rollup is still unfinished on October 22, cut the table to the years already rolled, train if the stop condition is clear, and spend October 23 on the page. A scored 2022–2024 slice that runs is the contest entry. An unfinished 2018–2024 pipeline is not.

## Left for a 2.0

The written answers ask what a 2.0 would change. These stay there:

- Billing years 2013–2017, once the shipped window is already training.
- A second host, if the first public URL is already up. Hosting is now in this build. See [[build decisions]].
- Hyperparameter search, a second model, or a comparison to the paper's AUC.
- DMEPOS, Part D, and any new label scrape.
- A national dashboard. The page looks up one provider.
- Shipping the raw yearly files. The stored table is the rolled provider-year rows, the model, and the search index.

## Disclosure list

CMS Physician & Other Practitioners by Provider and Service, 2018–2024. OIG LEIE. XGBoost. The Python packages the rollup actually uses, named when they are chosen. Leaflet, or whichever map library ships. Grok, in the Grok Build CLI, for the pipeline, the page, and the vault notes. Bauder and Khoshgoftaar, 2018, as the published method. The student owns the explanation of the features, the holdout, and why the score is not a finding.

Related: [[app idea]], [[core idea]], [[submission]], [[judging]], [[deadline]].

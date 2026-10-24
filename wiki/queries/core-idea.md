---
type: query
title: Core idea at the start of the build
updated: 2026-10-17
tags: [query, app]
sources:
  - handoff-firm-flagging.md
  - handoff-label-shortage.md
---

# Core idea at the start of the build

## Question

What is the core idea, now that the idea stage is done and the build is about to start?

## Answer

The idea to build is Medicare Fraud Flagger, written in `handoff-firm-flagging.md` on 2026-10-16. [[index]] points there as the next build. The model does not exist yet.

It stores public Medicare physician billing for 2013–2024, rolls that file to one row per provider per year, and trains XGBoost on which of those providers were later excluded for a fraud-type reason. A person searches a provider or types a new billing row. The score is a review flag. The page must not say the firm committed fraud.

The audience is a government official or a Medicaid Fraud Control Unit looking for a provider to check. The app scores public billing numbers. It does not replace their claims systems. A tip names who to look up. The allegation text is not an input.

The method is the published one in Bauder and Khoshgoftaar, 2018: mark a provider-year fraud if that NPI is on the OIG exclusion list for a fraud-type reason and the exclusion year is after the billing year. Mark every other provider not fraud. Train on the billing profile. Show the percentile and the numbers behind it. A person still has to check the provider.

Fraud-type reasons named for the page: `1128(a)(1)`, `1128(a)(3)`, `1128(b)(6)`, and `1128(b)(7)`. A match does not say which service caused the exclusion.

Features the model scores: service count, beneficiary count, average charge, average payment, charge-to-payment ratio, top-code share, specialty, and year-over-year growth. Name, NPI, city, state, and ZIP identify the row and place the map pin. They are not features.

The demo has to recover the Coffeezilla labs as flags, not as training labels. Prince Laboratories (NPI `1124725817`) and Reliable Results Labs (NPI `1639879034`), both in Deerfield Beach, ZIP 33441, billed HCPCS 81419 and are not on the October 15, 2026 exclusion list. If a firm-level score does not put them near the top, the page says so.

The rejected path is the medically unnecessary-test classifier in `handoff-label-shortage.md`. That gate needed 50 unique positive NPIs and failed. Dropping the unnecessary-test filter is what makes this version trainable. The positive class is any fraud-type exclusion. Part D stays out.

[[app idea]] and [[overview]] still describe Pattern Check, the unsupervised ranking that was the fallback when that gate failed. The handoff says to rewrite those pages when the model is the app. On 2026-10-17 the `app/` folder was not in this workspace.

## Citations

- `handoff-firm-flagging.md`
- `handoff-label-shortage.md`
- [[app idea]]
- [[overview]]
- [[index]]
- `wiki/log.md`, 2026-10-16 firm-flagging entry

## What this changes in the wiki

Filed this page. Linked it from [[app idea]] and [[index]]. Did not rewrite the concept page. The handoff says to do that when the model is the app.

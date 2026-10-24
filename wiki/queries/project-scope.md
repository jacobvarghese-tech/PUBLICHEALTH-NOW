---
type: query
title: How deep the build goes
updated: 2026-10-17
tags: [query, app, scope]
sources:
  - handoff-firm-flagging.md
  - raw/sources/2026-CAC-Rules.pdf
  - raw/sources/contest-brief-2026-10-15.md
---

# How deep the build goes

## Question

What is the scope of Medicare Fraud Flagger, and how deep can it go given what the Congressional App Challenge requires?

## Answer

The contest rewards a working lookup a judge can watch in under three minutes and a student can explain in the written answers. It does not reward a full reproduction of the 2013–2024 research pipeline.

The locked depth is on [[scope]]. Short version: one local Python app, billing years 2018–2024, train on 2019–2023, hold out 2024, one untuned XGBoost model, search, percentile, eight features, a Leaflet map, a typed row marked incomplete when fields are missing, and an honest 2024 percentile for Prince Laboratories and Reliable Results Labs. Fewer than 200 fraud provider-years in the train window stops the build for a recount or a report. October 23 is the last day for the page. October 24–25 are for the demo and the six answers.

## Citations

- [[scope]]
- [[judging]]
- [[submission]]
- [[deadline]]
- [[core idea]]
- `handoff-firm-flagging.md`

## What this changes in the wiki

Added [[scope]] and this page. Pointed [[app idea]], [[overview]], and [[index]] at the locked depth. Left the handoff in place. This page wins where they disagree.

---
type: query
title: Harness pick query
updated: 2026-10-22
tags: [query, app, model, llm]
sources:
  - https://github.com/gepa-ai/gepa
  - https://arxiv.org/abs/2507.19457
  - https://docs.x.ai/developers/models
  - https://docs.x.ai/developers/pricing
  - https://docs.x.ai/developers/rate-limits
  - models/holdout_note.txt
  - models/paper_forest_note.txt
---

# Harness pick query

## Question

Which self-optimizing harness fits Medicare Fraud Flagger, the xAI key, and the highest score on the control trials, and how is that workflow structured?

## Answer

The pick is `optimize_anything` in the installed `gepa` package, GEPA engine, xAI only. The student model is `grok-4.20-0309-non-reasoning`. The reflection model is `grok-4.3`. Base URL `https://api.x.ai/v1`. Key from `XAI_API_KEY`.

The control trials are three frozen files. Search is 2019–2022. Selection is 2023, 93 fraud rows. Confirmation is 2024, 48 fraud rows, scored once after the search stops. The number the search may raise is the selection-trial top 1 percent fraud count, with the top 5 percent written beside it, and the top 1 percent list must stay short. The one-row metric in `scripts/harness_score.py` is the wrong objective.

The workflow, the wiring, the systems left out, and the unverified lines are on [[harness pick]].

No compile was started. `app/` was not edited. The page model stays.

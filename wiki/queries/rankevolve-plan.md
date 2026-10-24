---
type: query
title: RankEvolve plan query
updated: 2026-10-22
tags: [query, app, model]
sources:
  - https://arxiv.org/abs/2602.16932
  - models/harness_rank_note.txt
---

# RankEvolve plan query

## Question

What is the after-school plan for building and testing a RankEvolve-style scorer for this app?

## Answer

Build `scripts/rank_evolve.py`. The candidate is a Python function that reads the eight billing fields and the frozen shallow-tree score, and may add a capped adjustment. Grade it on the whole 2023 list. Keep it only when the top 1 percent fraud count rises and the slice stays short. Score 2024 once after the search stops, on the same subsample the prompt harness lost.

The steps, the fitness, the stop rule, and the files are on [[rankevolve plan]]. No script was started. `app/` was not edited.

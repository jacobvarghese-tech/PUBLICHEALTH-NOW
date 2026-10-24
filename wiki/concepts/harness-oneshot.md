---
type: concept
title: Harness one-shot
updated: 2026-10-22
tags: [app, model, llm, planning]
sources:
  - wiki/concepts/harness-pick.md
  - scripts/harness_rank.py
  - models/holdout_note.txt
---

# Harness one-shot

Started 2026-10-22. The script is `scripts/harness_rank.py`. The morning files are `models/harness_rank_note.txt` and `models/harness_rank.json`. The page model stays.

## Steps

1. Load 2019–2022 as the search years and 2023 as the selection year. Drop the two demo NPIs. 2024 stays out.
2. Give GEPA 12 search fraud rows and 8 selection fraud rows, plus one clean row per fraud row. Cap the search at 80 metric calls. Student model `grok-4.5`. Reflection model `grok-4.6` with `reasoning_effort` high. Key from `XAI_API_KEY`. Base URL `https://api.x.ai/v1`. The first run used `grok-4.20-0309-non-reasoning` and `grok-4.3`. That process was stopped before a confirmation score was written. A second run with `grok-4.5` and `grok-4.6` failed every reflection call because `drop_params` was passed twice. That process was stopped. The restart omits that extra argument and compares the harness with both saved trees on the same 2024 subsample.
3. After the search stops, rank the winning instruction on 30 selection-year fraud rows and 9 clean rows per fraud row.
4. Score 2024 once: every fraud row in that file, and 5 clean rows per fraud row. Print the 48-event caveat before the share.
5. Sit those shares beside 11/48 and 18/48, and beside 19/48 and 48/48. Those saved figures are the full year. This confirmation is the subsample.

## Morning check

The run succeeded when `models/harness_rank_note.txt` contains `confirm_top1=` and `confirm_top5=`, and `models/harness_rank.json` contains no API key. A missing `confirm_top1=` line means the search did not finish.

The GEPA loop scores one row at a time. The installed batch hook cannot return one rank for the whole year. The morning top 1 percent and top 5 percent lines are the success check. They are not the number GEPA maximized during search.

A high score means resemblance to later fraud-type exclusions. It is not a finding that the firm committed fraud.

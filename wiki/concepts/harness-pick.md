---
type: concept
title: Harness pick
updated: 2026-10-22
tags: [app, model, llm, planning]
sources:
  - https://github.com/gepa-ai/gepa
  - https://arxiv.org/abs/2507.19457
  - https://arxiv.org/html/2507.19457v2
  - https://docs.x.ai/developers/quickstart
  - https://docs.x.ai/developers/models
  - https://docs.x.ai/developers/models/grok-4.20-non-reasoning.md
  - https://docs.x.ai/developers/pricing
  - https://docs.x.ai/developers/rate-limits
  - https://arxiv.org/abs/2609.05736
  - https://arxiv.org/abs/2610.26770
  - https://arxiv.org/abs/2610.14224
  - https://github.com/ShengranHu/ADAS
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC4738418/
  - models/holdout_note.txt
  - models/paper_forest_note.txt
  - scripts/harness_score.py
---

# Harness pick

Picked 2026-10-22 for Medicare Fraud Flagger. The earlier GEPA sentence was a wiring choice made before the ranking ran. This page is the ranking. It does not start a compile and it does not edit `app/`.

## Pick

Use `optimize_anything` from the installed `gepa` package, with the GEPA engine. The student call and the reflection call both go to xAI. The key is `XAI_API_KEY`. The base URL is `https://api.x.ai/v1`.

What gets rewritten is the scoring harness as text: the instruction, the field-reading rules, and the Python that turns eight billing fields into a score from 0 to 1. The model weights stay frozen.

Why this one:

- The control trials are a ranking job. A row is useful only if its score lands in the top 1 percent or the top 5 percent of that year's scores. `optimize_anything` accepts a `batch_evaluator`. That function sees the whole trial batch in one call, ranks it, and returns the fraud share plus a note on which fraud rows missed. A one-row metric cannot compute that share.
- The package is already imported on this Python 3.14.4 interpreter. License is MIT. Repo: https://github.com/gepa-ai/gepa.
- The GEPA paper's metric returns a score and feedback text. The reflection model reads the miss note and proposes the next harness. Paper: https://arxiv.org/abs/2507.19457.
- DSPy GEPA, already stubbed in `scripts/harness_score.py`, rewrites the instruction of one typed program. It does not rewrite the scoring code, and its current metric scores one row at a time. That is the fallback if `optimize_anything` cannot take the xAI base URL. It is not the pick.

A high score means the billing profile resembles providers later excluded for a fraud-type reason. The harness must not say the firm committed fraud.

## xAI wiring

Opened 2026-10-22 from the docs pages named above.

| Role | Model id | Why |
| --- | --- | --- |
| Student, the model inside the harness | `grok-4.20-0309-non-reasoning` | Text in, text out, reasoning off, 1,000,000 context. Short-context price is $1.25 input and $2.50 output per 1 million tokens. Tier 0 is 37 requests per second and 10 million tokens per minute. |
| Reflection, the model that rewrites the harness | `grok-4.3` | The proposer. Same short-context price as the student id above on the pricing page. Tier 0 is 37 requests per second and 10 million tokens per minute. |
| Left unused | `grok-4.7` | $2.00 input and $6.00 output per 1 million tokens under 200,000 prompt tokens. Tier 0 is 150 requests per second and 50 million tokens per minute. Use it only if a `grok-4.3` reflection call fails. |

Auth is `Authorization: Bearer` plus the value of `XAI_API_KEY`. Read the key from the environment at call time. Do not write it into a file, a log, or a wiki page. A presence check may print `true` or `false`.

A prompt of 200,000 tokens or more is billed at the long-context rate for every token in that request. Keep each scoring call on one provider-year. Eight fields do not need a long prompt.

The US host `https://us.api.x.ai/v1` is a 10 percent premium and, on the page opened, serves `grok-4.7` and `grok-4.6`. This workflow uses the global host.

LiteLLM-style ids for the GEPA engine are `openai/grok-4.20-0309-non-reasoning` and `openai/grok-4.3`, with `api_base` set to `https://api.x.ai/v1` and `api_key` set from the environment. The GEPA config page puts those knobs in `engine_config.reflection.reflection_lm_kwargs`. Confirm that path in the installed package before the first paid call. If the installed 0.1.4 build has no `optimize_anything`, stop and record the import error. Do not invent a second client.

Retry on HTTP 429. The script already sleeps and retries rate-limit text. Do not print the key on a retry.

## Control trials

Three trials. The first two decide the search. The third is scored once.

| Trial | Years | What it decides | Fraud rows on disk |
| --- | --- | --- | --- |
| Search | 2019, 2020, 2021, 2022 | The reflection model may read these rows, the scores, and the miss notes | Part of the 1,270 fraud rows in 2019–2023 |
| Selection | 2023 | Keep a candidate only when this trial's top 1 percent numerator rises and the top 1 percent list stays short | 93 |
| Confirmation | 2024 | Scored once after the search stops. Never enters search or selection | 48 |

The rolling-origin rule is the one already used for the year split: training observations come from before the test observation. 2023 is the selection trial because it is the latest year that is still before the confirmation year. 2024 is the confirmation trial because every saved note holds it out.

Saved confirmation figures, already in the notes:

| Scorer | Top 1% | Top 5% | File |
| --- | --- | --- | --- |
| Shallow XGBoost | 11/48 | 18/48 | `models/holdout_note.txt` |
| Paper forest | 19/48 | 48/48 | `models/paper_forest_note.txt` |

The paper forest's 48/48 top 5 percent share includes every 2024 fraud row. It is not a short list. A harness that ties every score and then calls the whole year the top slice fails the short-list rule.

48 events are below the external-validation floor of at least 100 events, ideally 200 or more. Print that caveat before any 2024 share. The floor is Collins, Ogundimu, and Altman, Statistics in Medicine, 2016, https://pmc.ncbi.nlm.nih.gov/articles/PMC4738418/. A move of one or two 2024 events does not switch the page.

2023 has 93 fraud rows. That is also below 100. Use it to pick the harness. Do not call a 2023 share a precise estimate.

## Score the search is allowed to raise

Primary: the number of selection-trial fraud rows whose score is in the top 1 percent of that trial's scores.

Secondary, written beside it: the same count for the top 5 percent.

Short list: the top 1 percent slice must be about 1 percent of the trial rows. A slice that quietly grows to hold every fraud row fails.

Do not optimize accuracy, precision, or a dollar estimate. Do not let the reflection model see the confirmation trial.

The current script metric, `1 - abs(predicted - label)` on one row, is the wrong objective. A model can raise that number by scoring every row 0.5 and still miss the top 1 percent. The batch evaluator replaces it.

## Workflow

One script owns this: `scripts/harness_rank.py`. It does not exist yet. Output is `models/harness_rank.json` and `models/harness_rank_note.txt`. Those files do not exist yet.

1. Build three frozen files before the first model call. Search rows are 2019–2022. Selection rows are 2023. Confirmation rows are 2024. Drop demo NPIs `1124725817` and `1639879034` from all three. A row is positive only when the exclusion year is after the billing year and `EXCLTYPE` is `1128a1`, `1128a3`, `1128b6`, or `1128b7`.
2. Keep every fraud row in the search file and the selection file. Sample clean rows at 9 per fraud, seed 1, inside each file. Do not sample the confirmation file. That file is the real mix, scored once.
3. Seed harness: the instruction already in `scripts/harness_score.py`. It reads the eight billing fields and returns a resemblance score plus a reason.
4. Student call: one provider-year, `grok-4.20-0309-non-reasoning`, no streaming. Parse a number in 0 to 1. A missing parse is a miss, not a middle score.
5. Batch evaluator: score the search batch or the selection batch, rank it, and return the top 1 percent fraud count as the number to maximize. The note names the fraud rows that fell out of the top 5 percent and quotes the billing fields that were blank. That note is the feedback text.
6. Reflection call: `grok-4.3`, through the same base URL. It may rewrite the instruction and the parse code. It may not add NPI, name, city, state, ZIP, or year as an input. It may not read a file, open a socket, or import a new module.
7. Keep a candidate only when the selection-trial top 1 percent numerator rises and the short-list rule holds. Two selection rounds with no gain stop the search.
8. Budget: start at `max_evals=150`. That is the README example named in the earlier harness plan. Raise it only after a saved file exists and the selection trial has moved. Do not set the budget to the full 12,700-row pool.
9. After the stop, score 2024 once. Write the top 1 percent and top 5 percent shares beside 11/48 and 18/48, and beside 19/48 and 48/48. Print the 48-event caveat first.
10. Save the winning harness text. Strip the key from the JSON. The page stays on the current model until a later session compares that note with the page score.

The parent coordinates. It does not score the confirmation year inside the search, and it does not call the model once per 2024 row during search.

## Systems opened and not picked

| System | Why it is not the pick | URL opened |
| --- | --- | --- |
| DSPy GEPA | Rewrites one instruction. Current metric is one-row. Fallback if the installed package has no `optimize_anything`. | https://dspy.ai/current/api/optimizers/GEPA/overview/ |
| ADAS | Invents an agent as generated Python. README installs on Python 3.11 and reads `OPENAI_API_KEY`. It executes generated code. | https://github.com/ShengranHu/ADAS |
| PRISM | Rewrites prompt and tool-boundary middleware. Shown on BFCL and tau-bench tool agents, not on a ranking trial. | https://arxiv.org/abs/2609.05736 |
| HarnessPro | Label-free. Grades with tests the model writes. README requires Linux, Docker, and Codex. | https://arxiv.org/abs/2610.26770 |
| Harness² | No ground-truth labels. Built for new tasks with no answer key. | https://arxiv.org/abs/2610.14224 |
| MIPROv2 | Rewrites instructions and few-shots from a scalar score. No miss note. No harness code. | https://dspy.ai/api/optimizers/MIPROv2/ |
| TextGrad | Rewrites text variables. No saved harness program. | https://github.com/zou-group/textgrad |
| OPRO | Official repo has no `api_base` flag for this endpoint. | https://github.com/google-deepmind/opro |

Self-HPO also trains model weights. That is a different job. RiseHarness and Harmony Harness had no install page that opened.

## Unverified

- The installed `gepa` 0.1.4 tree was not opened file by file. `import gepa` succeeds. Whether that build exports `optimize_anything` and `batch_evaluator` was read from the current GitHub tree, not from the installed wheel.
- xAI prices and rate limits were read through search snippets of the docs pages on 2026-10-22. Re-open https://docs.x.ai/developers/models and https://docs.x.ai/developers/pricing before the first paid night if a model id has moved.
- No opened paper reports top 1 percent capture for a Medicare billing ranker. The metric is the project's control-trial rule, not a number copied from a harness paper.
- A 2023 top 1 percent numerator for the current page model is not in the notes. The search needs that count from the files before it can say a candidate beat the page.

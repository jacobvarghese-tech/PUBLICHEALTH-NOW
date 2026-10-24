---
type: query
title: Meta harness action-plan prompt
updated: 2026-10-22
tags: [query, app, model, llm]
sources:
  - https://docs.x.ai/developers/models/grok-4.5
  - https://docs.x.ai/developers/models/grok-4.7.md
  - https://docs.x.ai/developers/models
  - models/optimized_note.txt
  - models/paper_forest_note.txt
  - models/holdout_note.txt
  - models/harness_rank_note.txt
  - models/rank_evolve_note.txt
  - scripts/meta_harness.py
  - harness/score_rows.py
---

# Meta harness action-plan prompt

## Question

What `/goal` line should the next session paste so about 20 agents write and review an action plan for a meta-harness run, with grok-4.5 as the writer and grok-4.7 as the reviewer, aimed at the highest fraud-row count out of 48?

## Answer

Deep research is the wrong runner. It splits a query into a handful of questions and drops a step that is not a surviving claim. This job is a `/goal`. The parent starts about 20 subagents in the first round. grok-4.5 writes. grok-4.7 reviews. The deliverable is the action plan, not a live compile and not a conclusion that the run cannot beat the saved models.

The line to paste:

```
/goal Write the meta-harness action plan at wiki/concepts/meta-harness-plan.md before you stop. Use about 20 subagents in the first round. The writer model is grok-4.5. The reviewer model is grok-4.7. Spawn writer subagents with model grok-4.5 and reviewer subagents with model grok-4.7. Do not leave the model field off. A writer drafts one slice of the plan. A reviewer checks that slice against the files and the pages it opened, and sends the miss back. The parent merges only slices a grok-4.7 reviewer has passed. Do not use /deep-research. Do not start the live meta-harness loop. Do not fit a model. Do not edit app/. Do not replace models/xgb_shallow.json, models/paper_forest.joblib, or models/optimized_model.joblib. Do not conclude that this would not work. The student's instruction is to plan the run that chases the highest score out of 48. A low prior score is a fact in the plan, not a reason to stop.

Student instructions, in front of every subagent prompt. Copy this block into each spawn. Do not shorten it.

- The score is fraud rows caught in the top 1 percent of the 2024 year, out of 48. Higher is better. The plan also records the top 5 percent count out of 48. Accuracy is not a score.
- grok-4.5 is the model that writes the harness code in the later run. grok-4.7 is the model that reviews that code in the later run. The same split applies to this planning session: 4.5 writes, 4.7 reviews.
- The later agent has free rein inside the harness codebase. It may rewrite harness/score_rows.py and any helper it creates under harness/. It may combine frozen scores, billing fields, and free tools it installs. It may call grok-4.5 to propose the next file. It may call grok-4.7 to review that file before the parent scores it.
- Free rein does not include the scorekeeper. scripts/meta_harness.py, or the script the plan names as the parent, computes the 2023 keep decision and the one 2024 score. The agent does not edit that file, the labels, app/, or the saved model binaries.
- Install every relevant tool that is free and usable immediately. Open the tool's own page, then put the install line in the plan. Prefer pip, a local wheel, or a no-account library. Skip a tool that needs a paid key, a cloud account, or a wait. The xAI key is already in the environment as XAI_API_KEY. Do not print it. Do not write it into a file.
- 2024 is scored once, after the search stops. The plan does not put 2024 labels in the prompt that writes the harness.
- A high score means resemblance to later fraud-type exclusions. The plan must say that. It must not say the firm committed fraud.
- Do not conclude yourself this would not work. Prior harnesses lost. That loss is why this plan exists. Write the steps that chase a higher count out of 48.

What the plan must contain. Number the steps so a later session can say "do step 4."

1. How to use the plan. Name the writer model, the reviewer model, the parent script, the harness folder, and the file that records the 2024 count out of 48.
2. Tool install steps. For each tool: the page you opened, the install command, the import check, and why it can raise the count out of 48. Include the xAI OpenAI-compatible client, and any free ranker, explainer, or code-search library the writers open and the reviewers accept. Re-open https://docs.x.ai/developers/models/grok-4.5 and https://docs.x.ai/developers/models/grok-4.7.md before you lock a model id. If a page has moved, the open wins. Do not invent an id.
3. The harness contract. score_rows(rows) returns one float per row. Each row has the eight billing fields plus tree_score and paper_score. The parent computes those two scores. The harness must not import a module that reads NPI, name, city, state, ZIP, or year. The plan may widen the harness folder. It may not hand the agent the evaluator.
4. The loop. Score the seed on the 2023 selection file before proposal 1. Then run the proposal count the reviewers accept. A rejected proposal counts. Do not stop after two quiet rounds. Send an error back as the next note. Keep a candidate only when the 2023 top 1 percent fraud count rises and the top 1 percent slice stays at most 2 percent of the selection rows. grok-4.5 proposes. grok-4.7 reviews the file before the parent scores it.
5. The one 2024 score. After the loop, score the best kept harness once on the full 2024 year if the reviewers say the machine can hold it, otherwise on the 288-row subsample already used by models/harness_rank_note.txt, and say which one. Write confirm_top1= as a count out of 48. Also write the same-row count for the page forest and for the shallow tree. beats_current_best is true only when the new count is higher than 20/48 on the full year, or higher than the same-row paper count when the plan uses the subsample.
6. Files the later session may create, and files it must not replace.

Measured facts. Use them. Do not re-estimate them.

- Workspace: C:\Users\Jacob\Downloads\congressional app. Windows. Python 3.14.4. The key is XAI_API_KEY. Base URL https://api.x.ai/v1.
- Eight billing fields: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth. NPI, name, city, state, ZIP, and year identify the row. They are not features.
- A row is positive only when the exclusion year is after the billing year and EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7. Demo NPIs 1124725817 and 1639879034 are dropped.
- Full 2024 year, already scored, do not refit: shallow XGBoost 11/48 and 18/48. Page forest 19/48 and 48/48, recounted from data/paper_scores/2024.csv. Optimized rank 20/48 and 48/48 in models/optimized_note.txt. That 20/48 is the current best. The page still loads models/paper_forest.joblib.
- Subsample, 288 rows, 48 fraud rows, 5 clean per fraud, seed 1: prompt harness 1/48, shallow tree 3/48, RankEvolve seed 3/48. RankEvolve kept none of 20 proposals.
- 2024 has 48 fraud rows, below the 100-event floor. The plan prints that caveat before the share. The share is still the score the student asked for.
- Setup already on disk, not a finished run: harness/score_rows.py returns the page-forest score. scripts/meta_harness.py is the parent. tests/test_meta_harness.py passes. The live loop has not started.

Done when wiki/concepts/meta-harness-plan.md exists, names grok-4.5 as the writer and grok-4.7 as the reviewer, lists the free install lines the reviewers accepted, and ends with the 2024 count out of 48 as the success line. A missing success line means you are not done.
```

The planning session does not start `scripts/meta_harness.py`. It writes the plan. A later session executes that plan.

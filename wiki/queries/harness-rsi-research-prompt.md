---
type: query
title: Harness RSI research prompt
updated: 2026-10-20
tags: [query, app, model, llm]
sources:
  - models/holdout_note.txt
  - models/paper_forest_note.txt
  - models/paper_forest_shares.json
  - models/xgb_expanded_note.txt
  - models/paper_replicate_note.txt
  - handoff-firm-flagging.md
---

# Harness RSI research prompt

Superseded for the next run by [[harness action-plan prompt]]. This page stays as the ranking query. Do not pass it to `/deep-research` again.

## Question

What prompt should the deep-research run use so the report names the four best public LLM harnesses that can optimize the harness itself, using about 1,200 labeled fraud rows, for recursive self-improvement on Medicare Fraud Flagger?

## Answer

Tree models on this table are the current scoring path and they are not a usable next-year ranker. Shallow XGBoost holds 11 of 48 2024 fraud rows in the top 1%. The paper-style forest holds every training-year fraud row in the top 1% of the years it fit, then 19 of 48 on 2024. The student wants an LLM scoring harness instead, and wants that harness optimized against the labeled fraud rows already on disk.

RSI here means recursive self-improvement of the harness: the system prompt, few-shots, tools, scoring loop, and any other scaffolding around a frozen or lightly adapted LLM. The optimizer may use the labeled rows. A later session will open the report and pick one of the four named systems. The page and the saved tree files stay until that later session says otherwise.

The stock `/deep-research` runner splits a query into at most four questions when breadth is left unset. Each question returns at most six claims. A second pass keeps a claim only when it can open the cited source and support the exact statement. A ranked list that is not inside surviving claims gets dropped. Put the executable fact in the claim: repo URL, paper URL, license, how labels enter, and the metric hook.

The prompt to pass as `args.query`:

```
I need exactly four public LLM harnesses that can optimize the harness itself, given about 1,200 labeled Medicare-fraud provider-year rows, for recursive self-improvement (RSI) of a scoring loop. The report will be reopened by one person who can install a Python package, call an LLM, and score one provider-year row. They will not read a literature survey. They need four named systems, ranked, each with a URL you opened, how the labels enter the optimizer, and the metric to plug in.

The product is Medicare Fraud Flagger. A person looks up a Medicare provider or types eight billing numbers. The score is a review flag: this billing profile resembles providers later excluded for a fraud-type reason. The page must not say the firm committed fraud. The audience is a government official or a Medicaid Fraud Control Unit looking up a name they already have.

Tree models already trained on this table failed the use case. Do not recommend another XGBoost, random forest, or other tabular ML model. Do not treat a published AUC as a score this project has earned. The LLM harness is the candidate replacement. The saved tree files and the running page stay in place until a later session chooses one of the four systems.

How to split the work. This run plans at most four questions and verifies claims independently. Keep these four questions separate. Do not merge them. Each question may return at most six claims.

1. Labeled harness optimizers. Open the primary paper or official docs, then the public repository, for systems that compile or evolve an LLM program from a trainset of labeled examples. Cover at least DSPy with GEPA, DSPy MIPROv2, TextGrad, and OPRO if those pages still exist. For each system you opened: full name, GitHub or docs URL, license, whether the optimizer takes labeled examples, the authors' stated example-count range, and the exact object it updates (instructions, few-shots, traces, graph, weights). State whether about 1,200 positive labels sits inside the range they claim.

2. RSI and full-harness search. Open the primary paper or official repository for recursive self-improvement of the agent harness, where the optimization surface is the runtime scaffolding (system prompt, tools, middleware, memory, recovery), not only a single instruction string. Cover HarnessPro, Harness2 / Harness² (including google-research/harness2 if that repo exists), the Beyond Prompts / PRISM protocol, and the RSI baseline those papers compare against. For each: URL you opened, whether it requires ground-truth labels, is label-free, or can take either, and whether 1,270 LEIE-joined provider-year labels can be the trainset. A label-free-only system can still be one of the four if you opened a way to attach a labeled metric.

3. Rare-event ranking fit. This job is a ranker with about 0.04 percent positives, not a coding agent. Open sources that show one of the systems above on classification, screening, compliance, fraud, extraction, or ranking, with a metric a coder can point at top-1-percent and top-5-percent capture. If a system was only shown on SWE-bench, Terminal-Bench, or pass@k, say that. Name the metric interface (function signature, return type, whether it can return textual feedback) so a later session can pass: share of held-out fraud rows whose score lands in the top 1 percent and top 5 percent of that year's scores.

4. Runnable four. From the systems you opened in questions 1-3, pick exactly four that this laptop can run as a scoring harness over one provider-year row. Rank them 1 through 4 for this job. Each pick must exist as a public internet project you opened (repository, paper with code, or official docs with an install path). Each pick must allow harness optimization. Each pick must have a path that uses the labeled fraud rows, or a documented adapter that does. For each of the four: name, rank, URL, license, install or import line you opened, what gets optimized, how the 1,270 fraud rows and the undersampled clean rows enter, the metric to pass in, a 2024 holdout rule, and Done when for a later coding session.

Measured facts. Counted in this workspace. Use them. Do not re-estimate them.

- One row is one rendering NPI for one calendar year, rolled from Medicare Physician and Other Practitioners by Provider and Service.
- Features a scorer may read, in this order: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth. Specialty is a string such as Clinical Laboratory. Growth is this year's service count divided by the prior year's service count, minus 1, and is missing when there is no prior row or the prior service count is 0. Name, NPI, city, state, ZIP, and Year identify the row and place a map pin. They are not required scorer inputs. Do not add city, state, ZIP, NPI, or name as learned features. Do not download beneficiary-level claims.
- A row is fraud only when its NPI matches a 10-digit NPI on the HHS OIG LEIE, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the year of EXCLDATE is after the billing year. Same-year and earlier exclusions are not positive. License actions and other exclusion types are not labels.
- Student named about 1,200 labeled fraud rows as the optimization set. The counted 2019-2023 train-window fraud count is 1,270 provider-years, with 11,430 undersampled clean rows at 9 clean per fraud, seed 1. Use 1,270 as the positive count for the optimizer. The paper-style forest on 2013-2023 counted 5,900 fraud rows on a different rollup. That larger count is not the RSI trainset unless a later session says so.
- Saved XGBoost, models/xgb_shallow.json, max_depth 4, 100 trees, eight features, trained 2019-2023, 2024 held out. Real-mix 2019-2023: 475/1270 in the top 1 percent, 918/1270 in the top 5 percent. 2024 holdout: 11/48 in the top 1 percent, 18/48 in the top 5 percent. 48 events sit below the Collins, Ogundimu, and Altman external-validation floor of 100 events.
- Expanded XGBoost, 2013-2023 train, 2024 held out: 8/48 in the top 1 percent, 19/48 in the top 5 percent.
- Paper-style random forest, models/paper_forest.joblib, 100 trees, 2013-2023 train, 5,900 fraud rows among 11,524,741 rows. On every training year 2018-2023 it put every fraud row in that year's top 1 percent. 2024 holdout: 19/48 in the top 1 percent, 48/48 in the top 5 percent. Perfect training-year capture with a 19/48 next-year top-1-percent share is the tree failure mode.
- Paper comparison forest on 2013-2015 only, 90:10 mix, 885 fraud and 7,965 clean, stratified 5-fold CV repeated 10 times, mean AUC 0.814268 beside the published RF100 90:10 cell 0.87302. Real-mix 2013-2015 top 1 percent was 885/885. That AUC is a comparison point, not a target for the LLM harness.
- 2024 has about 1.21 million provider-years and 48 fraud rows, about 1 in 25,000. A top 1 percent list is about 12,000 names. At 11 of 48, that list holds about 1 known fraud row per 1,100 names.
- Demo rows are not labels. Prince Laboratories Limited Liability Company, NPI 1124725817, 2024 XGBoost percentile 99.988902. Reliable Results Labs Inc, NPI 1639879034, 2024 XGBoost percentile 99.945258. Neither is on the LEIE. Do not train or optimize on them. A later miss stays visible.
- Machine: Windows, Python 3.14.4, about 16 GB RAM, workspace C:\Users\Jacob\Downloads\congressional app. Rolled years are CSV, about 1.06 million to 1.21 million rows each. An optimizer that needs a small labeled set may subsample clean rows. An optimizer that needs to score all 1.21 million 2024 rows in-loop during search will not finish. Prefer a system that can optimize on a few thousand labeled rows and then score the holdout once.
- Interpreter and libraries already here include xgboost 3.4.1, pandas, numpy, scikit-learn 1.8.0. A new LLM harness package may be added. Weka is not installed.

Locks. Treat these as given. If a source conflicts with one, put the conflict under Unverified and keep the lock.

- The result stays the share of 2024 fraud rows in the top 1 percent and the top 5 percent of 2024 scores. Accuracy, precision, and dollars saved are not the result.
- 2024 stays held out of optimization. A validation split may be taken from 2019-2023. 2023, with 93 current-rule fraud rows, may be a check year.
- A high score means resemblance to later-excluded billing. The harness output is a score or rank, not a fraud finding.
- Do not mark a row positive because of an exclusion in or before that billing year.
- Do not reopen the medically-unnecessary-test label hunt. Do not add Part D. DMEPOS stays a 2.0 item.
- Do not invent a district, a school, a home address, a parent email, or a 9-digit ZIP.
- The four picks must be systems you opened. A guessed GitHub path is Unverified, not a pick.
- Name four. Not three. Not five. If you opened fewer than four systems that meet the runnable bar, say so under Unverified and still rank every system you did open.

Output. Use these headers.

- Decision. One paragraph. Name the four harnesses in rank order. Say that the page and the saved tree files stay until a later session picks one.
- Why these four. A table with one row per pick. Columns: rank, name, URL you opened, license, what it optimizes, whether it takes the 1,270 labels directly, and why it beats the systems you left out.
- Label path. For each of the four, the trainset shape (example fields, positive and negative counts), how clean rows are sampled, and the metric function to pass in, written so a coder can implement it against 2023 then 2024.
- Holdout rule. 2024 never enters the optimizer. Report the 2023 top 1 percent and top 5 percent shares during search, then score 2024 once.
- Leave out. Systems you opened and rejected, one sentence each, with the reason (label-free only with no metric hook, coding-agent only, no public code, needs a cluster, needs beneficiary claims).
- Unverified. Pages you could not open, example-count claims you could not read, and any RSI paper whose code was missing.
- Sources. The URL you opened, next to the question number it supports.

Leave open. Do not invent a preference on these unless a source makes them part of a pick: which LLM vendor or model, whether to fine-tune weights versus prompts, whether to host the page, and whether the running app switches off the forest. A page switch is a later decision.

Return verified facts only. A guessed repository is a failed pick.
```

Pass it with `args.breadth` set to 4. Breadth 6 would split the four evidence targets into paraphrases, and the workflow drops claims past the cap.

## Citations

- Student request on 2026-10-20 for a deep-research prompt that finds the four best public harnesses that allow harness optimization, given about 1,200 labeled fraud rows, for RSI optimization of Medicare Fraud Flagger, after tree models failed the use case.
- [[core idea]]
- [[scope]]
- [[model reliability]]
- [[retrain research prompt]]
- [[closest paper-model prompt]]
- `models/holdout_note.txt`
- `models/paper_forest_shares.json`
- `models/xgb_expanded_note.txt`
- `models/paper_replicate_note.txt`
- `handoff-firm-flagging.md`

## What this changes in the wiki

Filed the prompt. It does not start the research run and it does not edit `scripts/`, `models/`, or `app/`. The one-model lock on [[scope]] stays until a later session picks one of the four harnesses. The standing harness note does not exist until a report returns.

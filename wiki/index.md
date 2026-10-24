---
type: index
title: Index
updated: 2026-10-22
tags: [index]
sources: []
---

# Index

Read this first when answering a question. Summaries are one line. Open the page before you rely on it.

## Overview

- [[overview]] — Where the entry stands, what is known, and what is blocking submission.

## Concepts

- [[deadline]] — October 26, 2026. Plan for noon Eastern. A second official clock says 9 p.m.
- [[eligibility]] — Middle or high school, U.S. resident, one hosting district, team of at most 4, one app.
- [[submission]] — Portal, demo video, written answers, and the exit questionnaire.
- [[judging]] — Idea, implementation, coding. One winner per hosting district.
- [[prizes]] — Capitol display eligibility, House.gov, #HouseOfCode, ARTS Act fee waiver. Travel is unpaid.
- [[app idea]] — Pattern Check, the earlier ranking. The build is Medicare Fraud Flagger. Read [[scope]] before the handoff's year list.
- [[scope]] — Locked depth. Years 2018–2024, one XGBoost model, a local search page. This page wins over `handoff-firm-flagging.md`.
- [[action plan]] — Coding checklist from the research run. Nine steps. AWS is off the critical path. Unverified items are marked.
- [[LLM Wiki pattern]] — How this vault is supposed to work.

## Entities

- [[Congressional App Challenge]] — The contest itself.
- [[Internet Education Foundation]] — Outside administrator.
- [[House of Representatives]] — Host. Each member runs a district contest.

## Sources

- [[2026 contest brief]] — Compiled official facts as of 2026-10-15. Start here for contest claims.
- [[2026 CAC Rules PDF]] — Binding rule text. Downloaded 2026-10-15.
- [[Karpathy LLM Wiki gist]] — Unmodified import of the idea file. The compiled reading is [[LLM Wiki pattern]].

## Queries

- [[core idea]] — Medicare Fraud Flagger is the idea to build. Pattern Check is the earlier ranking. The model does not exist yet.
- [[project scope]] — Why the contest caps the build at one lookup. The decision lives on [[scope]].
- [[build decisions]] — Student answers before the action-plan research. Agents write the code. Hosting is wanted. Machine can hold the files.
- [[action-plan prompt]] — The research query. The compiled checklist is [[action plan]].
- [[app viable]] — The lookup can be built on this laptop. The score is a review flag. Capture quality waits on training.
- [[good flag]] — The database can be good. The score is for a name you already have. A national top-flags list is mostly clean providers.
- [[xgboost viable]] — One shallow XGBoost model still fits. It installs on Python 3.14. The 2018 paper's 0.873 is a comparison point.
- [[model reliability]] — Saved fit stands. 48 holdout events are below the 100-event floor. The about page prints that caveat beside 11/48 and 18/48. No refit.
- [[model reliability prompt]] — Research query for making the trained model more reliable. The compiled note is [[model reliability]].
- [[reliability apply prompt]] — Coding prompt from the Partial reliability report. The diagnosis and the one page change are on [[model reliability]].
- [[retrain research prompt]] — Research query for one retrain decision. Four evidence targets. Measured 48-row ranks are facts in the prompt.
- [[full retrain action-plan prompt]] — Research query for a full retrain plan: 2013–2017 physician years, Wayback labels, and a full DMEPOS trial. A new model file is allowed.
- [[expanded retrain action-plan prompt]] — Research query for the expanded 2013–2023 fit. Twelve separate questions. The stock runner cannot field twelve research agents.
- [[paper replicate prompt]] — Research query for an action plan that replicates the Bauder and Khoshgoftaar 2018 model as a third file. Four questions, written for the stock runner.
- [[closest paper-model prompt]] — Research query for the closest public rebuild of that 2018 model. A missing original file is a gap, not a stop. Four questions, written for the stock runner.
- [[paper comparison]] — Executable comparison plan from that run. RF100 at 90:10, written to models/paper_replicate.json. The saved XGBoost files stay.
- [[paper one-shot goal]] — The `/goal` line for tonight. It runs `scripts/paper_oneshot.py` and leaves the app model in place.
- [[paper forest app goal]] — The `/goal` line that rolls 2016–2024 the paper way and points the page at that forest. The saved XGBoost files stay.
- [[undersampling action-plan prompt]] — Research query for a second forest trained with the paper's random undersampling. The page model stays until the 2024 list says otherwise.
- [[undersample plan]] — Executable comparison plan from that run. One 90:10 forest at models/paper_forest_rus.joblib. The page forest stays until the 2024 list is compared.
- [[undersample goal]] — The `/goal` line that fans that plan across 20 agents. Eleven label a year, seven check features, one writes the script, one fits.
- [[leaf-size action-plan prompt]] — Research query for two comparison forests that stop a leaf at 50 rows and at 100 rows. The page forest stays until the 2024 list says otherwise.
- [[leaf-size plan]] — Executable comparison plan from that query. Two forests at min_samples_leaf 50 and 100. The page forest stays until the 2024 list is compared.
- [[tie-break action-plan prompt]] — Research query for a list order that breaks a tied forest score with a specialty charge fact. No new model. The page stays until that list says otherwise.
- [[paper-holes research prompt]] — Twelve-agent prompt that fills only the holes in that plan. The stock runner cannot field 12. The runner is the paper-holes workflow.
- [[plan audit]] — Live check of the files. The working app is reachable. 4,296 fraud rows have an NPI. The two labs are in the 2024 file and not on the exclusion list.
- [[harness RSI research prompt]] — Ranking query for four public harnesses. Superseded for the next run by [[harness action-plan prompt]].
- [[harness action-plan prompt]] — Research query for an action plan that finishes one labeled scoring harness on xAI. Tree files stay until that plan is executed.
- [[harness goal]] — The `/goal` line that executes that plan overnight: one DSPy/GEPA scorer, xAI key only, trees stay.
- [[three harness plans prompt]] — Research prompt for three overnight train-grade-improve plans. The stock runner was the wrong runner. The checklist it did not write is [[three harness plans]].
- [[three harness plans]] — The three overnight plans: year-holdout, feature-code, and label-lag. One night runs one plan. The page model stays.
- [[harness pick]] — The harness for the control trials. `optimize_anything` on xAI. Search 2019–2022, select on 2023, score 2024 once.
- [[harness pick query]] — The question that produced that pick. No compile was started.
- [[harness one-shot]] — Overnight run of `scripts/harness_rank.py`. It lost the same-row comparison. The note is `models/harness_rank_note.txt`.
- [[rankevolve plan]] — After-school plan for a listwise code search. The seed is the shallow tree. 2024 is scored once.
- [[rankevolve plan query]] — The question that produced that plan. No script was started.
- [[meta harness action-plan prompt]] — The `/goal` line for a 20-agent plan. grok-4.5 writes. grok-4.7 reviews. The score is fraud rows out of 48.
- [[label islands goal]] — The `/goal` line for a training-label search. Spec 22 stays frozen. The 2024 numerator stays on the app rule.

Phase 1 starts with the `/goal` line on [[action plan]], step 1. A phase name alone is not a goal.

---
type: query
title: Is XGBoost still viable
updated: 2026-10-17
tags: [query, app]
sources:
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/
  - wiki/concepts/action-plan.md
---

# Is XGBoost still viable

## Question

Is one XGBoost model still a sound choice for Medicare Fraud Flagger?

## Answer

Yes. XGBoost 3.4.1 has a Windows wheel for Python 3.14, which is the interpreter on this laptop. The model is one shallow run on eight numbers after the years are rolled. That job is small.

The 2018 paper's best learner was a random forest, AUC about 0.873, at a 90:10 mix of clean rows to fraud rows. XGBoost is a tree model built for the same kind of table. This build already uses that 90:10 mix. The paper did not test XGBoost, so 0.873 is a comparison point, not a score this model has earned. [[scope]] keeps one model and does not add a second.

## Citations

- [[action plan]], step 1 and step 6
- [[scope]]
- [[good flag]]
- Bauder and Khoshgoftaar, 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/

## What this changes in the wiki

Filed this page. Did not change the model lock on [[scope]].

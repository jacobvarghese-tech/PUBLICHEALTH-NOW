---
type: query
title: Retrain research prompt
updated: 2026-10-18
tags: [query, app, model]
sources:
  - models/holdout_note.txt
  - https://developers.openai.com/api/docs/guides/deep-research
  - https://www.anthropic.com/engineering/multi-agent-research-system
---

# Retrain research prompt

## Question

What prompt should the deep-research run use so the report can say whether a retrain makes this model more reliable and more usable, and which retrain to run?

## Answer

The student is willing to retrain. The previous reliability run was told not to recommend a second fit, so it could not answer this. This prompt opens the fit and keeps the product.

The local workflow splits the query into at most four questions, returns at most six claims per question, and keeps a claim only when a second pass can open the cited source and support the exact statement. A prompt that prescribes the search order, or that asks for one blended recommendation, collapses those questions onto the same papers. This prompt names the decision, the measured facts, four evidence targets, the output, and the source rules. It does not name the search sequence.

The prompt to pass as `args.query`:

```
I need a retrain decision for one saved XGBoost model. The decision is whether a new fit, trained only on files already in this workspace, would make the flag more reliable and more usable than the saved fit, and if so which single change to make. A later session will open this report and either retrain once or leave the saved file alone. Write a decision memo a coder can apply. Cite a primary source for every published claim. A claim with no opened source goes under Unverified, not into the recommendation.

The audience is one person who can edit scripts/train.py and refit models/xgb_shallow.json. They will not read a literature survey. They need a keep-or-replace call, one change if the call is replace, and a check that says whether the new fit is kept.

How to split the work. This run plans at most four questions and verifies claims independently. Give each question a different evidence target so the researchers do not open the same papers:

1. Label timing. Whether a fraud label whose exclusion falls years after the billing year is a different target from a label whose exclusion falls within two years, and what published Medicare-exclusion studies did about that gap.
2. Rare-event validation. What sample size, interval, or comparison a published methods paper says is readable for a capture share of 11 events out of 48, and for a second check year with 93 events.
3. Feature grain. Whether peer-reviewed Medicare fraud models built features from the claim or HCPCS line, or from a provider-year rollup, and which of those features can be built from the columns already rolled here.
4. Decision threshold. How a published screening or fraud-detection paper turns a rank into a usable review list when the base rate is about 1 in 25,000, including precision at a fixed review budget.

Source rules. Prefer the paper's own PDF, the journal page, CMS or OIG documentation, the statute, and the XGBoost documentation. Deprioritize SEO explainers, vendor blogs, and Wikipedia. Open the methods page before you cite a number from a Medicare fraud paper. If a methods page is blocked, say so and do not reconstruct the number from a citation of that paper. Do not cite a page you did not open.

Measured facts. These were counted in this workspace on 2026-10-18. Use them. Do not re-estimate them, and do not treat a cited AUC from another paper as a score this model has earned.

- Saved fit: models/xgb_shallow.json. One XGBClassifier, max_depth 4, random_state 1, other booster settings at the XGBoost 3.4.1 default, 100 trees, one fit. No search. No second model. No scale_pos_weight. No early stopping.
- Features, in order: Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Specialty, Growth. Specialty is an integer code from a sorted list of training-year specialty strings. Missing numbers stay missing. Name, NPI, city, state, ZIP, and Year are not features.
- Training years 2019-2023. Every fraud row kept. Clean rows undersampled to 9 per fraud row, seed 1. Training sample: 1,270 fraud rows and 11,430 clean rows.
- A row is fraud only when its NPI matches a 10-digit LEIE NPI, EXCLTYPE is 1128a1, 1128a3, 1128b6, or 1128b7, and the exclusion year is after the billing year. The LEIE on disk is the September 2026 UPDATED.csv and contains dates through 2026.
- Same model scored on every 2019-2023 row: 475 of 1,270 fraud rows in the top 1% of those scores, 918 of 1,270 in the top 5%. Those rows were in the fit, so this figure is optimistic.
- 2024 was not used to fit. 2024 has 1,207,473 provider-years and 48 fraud rows. The same model put 11 of those 48 in the top 1% of 2024 scores and 18 of 48 in the top 5%. Cutoffs were 0.583318 for the top 1% and 0.263635 for the top 5%.
- Rank of those 48 against the stored 2024 scores: median percentile 89.3. Eleven in the top 1%, 7 more in the top 5%, 5 more in the top 10%, 13 more in the top 25%, and 12 below the 75th percentile. The highest of the 48 is percentile 99.958. None of the 48 is inside the top 0.01%, which is about 121 names.
- The 12 rows below the 75th percentile have ordinary rolled billing. Their median service count is 318, against 410 for all 2024 rows. Their median average charge is $179, against $199. Their specialties are family practice, nurse practitioner, psychiatry, internal medicine, otolaryngology, and nurse anesthesia.
- The 11 top-1% hits are extreme rows: a collapsing year, a charge-to-payment ratio of 7 or 8, or 11,413 services.
- Label window. A 2019 fraud row can be an NPI excluded as late as 2026. A 2024 fraud row can be positive only for an exclusion in 2025 or 2026. The LEIE has 4,254 qualifying NPIs. Of those, 346 were excluded in 2025 and 292 in 2026, and 48 of that set appear in the 2024 physician file. Under the current rule, 2023 has 93 fraud rows.
- Base rate. 48 fraud rows in 1,207,473 is about 1 in 25,000. A top 1% list is about 12,075 names. At the measured 11 of 48, that list holds about 1 known fraud row per 1,100 names. Capturing all 48 would still be about 1 in 250.
- Two named 2024 labs are not on the LEIE and are not training labels. Prince Laboratories Limited Liability Company, NPI 1124725817, percentile 99.988902 (1,207,339 of 1,207,473). Reliable Results Labs Inc, NPI 1639879034, percentile 99.945258 (1,206,812 of 1,207,473). Prince Laboratories outranks every one of the 48 fraud rows.
- Rolled columns already on disk, one row per rendering NPI per year: NPI, Name, City, State, ZIP, Specialty, Service count, Beneficiary count, Average charge, Average payment, Charge-to-payment ratio, Top-code share, Growth, Year. There is no entity-code column and no HCPCS column in the rolled file. Beneficiary count is a sum of Tot_Benes across HCPCS and place of service, so it can double-count. The raw yearly service files are still on disk if a feature needs a column the rollup dropped. Do not assume a column exists in the rollup because it exists in the raw file.

Decision the report must make. Compare these uses of a new fit, using the sources you opened, and pick one. If the sources do not support a new fit, the pick is to leave the saved file alone.

- A matched label window. A training row is positive only when the exclusion falls in the next two calendar years, the same window 2024 has. Same depth, same eight features, same undersample, same four codes. 2024 stays held out. 2023, with 93 current-rule fraud rows, is the check year.
- A feature that can be rebuilt from columns already in the rolled files or the raw yearly files on disk, if a published method says the provider-year average is the reason ordinary-looking fraud rows land below the 75th percentile.
- A change to how the page uses the existing scores, with no new fit, if the sources say the rank is already as concentrated as this feature grain can make it and the usability problem is the review budget.
- Leave the saved fit alone.

Output. Use these headers.

- Decision. One paragraph. Name the pick. Name the file that owns it. Say what the 2023 check must show before the new file replaces models/xgb_shallow.json.
- Why this pick. A table with one row per option above. Columns: option, what the opened sources say it can change, what it cannot change in the 48-row rank or the 1-in-1,100 list, and whether it needs a new fit.
- The change. If the pick is a new fit, give the label rule or the feature definition, the owner file, and the values that stay the same. If the pick is a page change, give the sentence or the cutoff. If the pick is to leave the fit alone, say which file stays byte-for-byte the same.
- Keep rule. A numeric comparison the coder can run on files already here. Include the 2023 top 1% and top 5% shares and the 2024 top 1% and top 5% shares. Say how large a move has to be before it counts, given 93 and 48 events. Do not invent a confidence interval unless you opened a methods paper that covers a capture share at this sample size, and name that paper.
- Unverified. Claims you could not confirm. A blocked methods page goes here.
- Sources. The URL you opened, next to the section it supports.

Leave open. Do not invent a preference on these. Put them in the report only if a source makes them part of the pick: whether to add a second algorithm, whether to grid-search depth, whether to download a new dataset, and which review budget a person can actually work. A second dataset is a separate decision from a retrain of this file.

Do not invent a district, a school, a home address, a parent email, or a 9-digit ZIP. Do not say the page has found fraud. A high score is a resemblance to providers later excluded for a fraud-type reason.
```

Pass it with `args.breadth` set to 4. Breadth 6 would split the four evidence targets into paraphrases, and the workflow drops claims past the cap.

## Citations

- Student request on 2026-10-18 for a deep-research prompt on retraining this model.
- OpenAI, Deep research, prompting section. The rewrite rules used here are: include every stated preference, leave unstated dimensions open, request tables for comparisons, specify the output headers, and prefer primary sources. https://developers.openai.com/api/docs/guides/deep-research
- Anthropic, How we built our multi-agent research system, 2025-06-13. A delegated research task needs its own objective, output, sources, and boundary, or the workers repeat the same search. https://www.anthropic.com/engineering/multi-agent-research-system
- [[model reliability prompt]]
- [[reliability apply prompt]]
- `models/holdout_note.txt`
- `data/rolled/2024.note.txt`

## What this changes in the wiki

Filed the prompt. It does not start the research run and it does not edit `scripts/` or `models/`. The standing retrain note does not exist until a report returns.

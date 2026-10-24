---
type: query
title: DOJ and conviction labels research prompt
updated: 2026-10-18
tags: [query, labels, model]
sources:
  - handoff-label-shortage.md
  - models/holdout_note.txt
  - data/training/fraud_provider_year_count.txt
  - wiki/queries/retrain-research-prompt.md
---

# DOJ and conviction labels research prompt

## Question

What prompt should the deep-research run use so the report can decide whether resolving names from public DOJ press releases, indictments, settlements, and OIG corporate integrity agreements can produce enough new positive NPIs (rendering NPIs that billed a watched code before the sanction date) to pass the label gate and materially improve the 2024 holdout rank, and whether that change justifies editing join_labels.py and refitting the model.

## Answer

The student is willing to add non-LEIE positives if the sources show a realistic path to passing the gate. The previous research runs were restricted to files already on disk and therefore returned "leave the saved fit alone." This prompt opens the question of new label sources while still requiring every claim to be verified by opening a primary source. The workflow must split into at most four questions, return at most six claims per question, and keep a claim only when a second pass can open the cited source and support the exact statement.

The prompt to pass as `args.query`:

```
I need a decision on whether to add DOJ, False Claims Act settlements, and OIG corporate integrity agreement names as extra positive labels for a Medicare fraud flagging model. The decision is whether resolving legal names from public DOJ press releases and OIG CIA pages to 10-digit NPIs, then joining those NPIs to the rolled billing files on a year before the sanction date, produces enough new fraud-type provider-years to pass a pre-defined label gate and to raise the share of 2024 holdout fraud rows captured in the top 1% and top 5% of scores. A later session will open this report and either add a name-resolution step to join_labels.py or leave the current LEIE-only labeling rule unchanged. Write a decision memo a coder can apply. Cite a primary source for every published claim. A claim with no opened source goes under Unverified, not into the recommendation.

The audience is one person who can edit scripts/join_labels.py and scripts/train.py. They will not read a literature survey. They need a keep-or-add call, the exact name-resolution rule if the call is add, and a numeric keep rule that can be checked on files already here.

How to split the work. This run plans at most four questions and verifies claims independently. Give each question a different evidence target so the researchers do not open the same pages:

1. Labeling practice. Whether published Medicare fraud detection studies or OIG/DOJ guidance treat convictions, False Claims Act settlements, and corporate integrity agreements as positive labels that are equivalent to or additive with LEIE fraud-type exclusions (1128a1, 1128a3, 1128b6, 1128b7), and whether any study reports the incremental yield after deduplicating against the current LEIE.
2. Name-to-NPI recovery yield. What fraction of legal names extracted from 2019–2026 DOJ national healthcare-fraud takedown press releases and from the OIG corporate integrity agreements list resolve to a usable 10-digit NPI in the CMS NPPES registry, survive a human-name check, and appear in the rolled physician or DMEPOS files for a year before the sanction date.
3. Gate passage. After adding the newly resolved NPIs to the current 29 unique fraud-type LEIE NPIs, does the deduplicated positive NPI count reach at least 50, are the positives spread across more than one ownership or billing scheme, and is a time split possible with positives present in both the 2019–2023 training window and the 2024 holdout window.
4. Rank impact on holdout. For any newly resolved NPIs that appear in the 2024 rolled physician file, what share of those rows land in the top 1% and top 5% of the current stored 2024 scores, and whether any opened source states that adding conviction or settlement labels changes the expected concentration of the rank when the base rate remains ~1 in 25,000.

Source rules. Prefer primary sources: the DOJ press release itself, the OIG CIA list page, the CMS NPPES registry result for a resolved name, the court docket or settlement agreement when linked, and peer-reviewed Medicare fraud papers that describe their labeling rule. Deprioritize secondary summaries, vendor explainers, and Wikipedia. Open the actual DOJ or OIG page before citing a count of cases or names. If a page is blocked or a name does not resolve in NPPES, say so and do not reconstruct the number. Do not cite a page you did not open.

Measured facts. These were counted in this workspace on 2026-10-18. Use them exactly. Do not re-estimate them.

- Current positive count: 29 unique fraud-type NPIs after joining the September 2026 LEIE (EXCLTYPE in 1128a1, 1128a3, 1128b6, 1128b7) to the rolled 2018–2024 physician files and after all DMEPOS, genetic-panel, and Wayback searches described in handoff-label-shortage.md. These 29 NPIs billed one of the watched codes in a year before their exclusion year.
- 2024 holdout: 1,207,473 provider-years, 48 fraud rows under the current LEIE rule. The saved model places 11 of those 48 in the top 1% of 2024 scores and 18 of 48 in the top 5%. Twelve of the 48 sit below the 75th percentile.
- Gate requirement (from handoff-label-shortage.md): at least 50 unique positive NPIs after deduplicating LEIE + DOJ + CIA sources; positives must be spread across more than one scheme; a time split must be possible with positives in both train and test windows; the test metric is the share of held-out sanctioned NPIs landing in the top 1% and top 5% of scores. Accuracy is not a result.
- Two named 2024 labs that outrank every known fraud row are not on the LEIE and are not training labels: Prince Laboratories Limited Liability Company (NPI 1124725817, percentile 99.988902) and Reliable Results Labs Inc (NPI 1639879034, percentile 99.945258).
- Rolled columns already on disk: one row per rendering NPI per year. No entity-code or HCPCS column. Beneficiary count can double-count. Name resolution must target the rendering NPI that appears in the billing row, not owners or ordering providers.
- Label rule in use: a provider-year is positive only when its NPI matches a 10-digit LEIE NPI with one of the four fraud-type codes and the exclusion year is strictly after the billing year. No reinstatement rule and no pre-exclusion labeling.

Decision the report must make. Compare these options using the sources you opened and pick one. If the sources do not support adding the new label source, the pick is to leave the current LEIE-only rule unchanged.

- Add a name-resolution step. Extract legal names from 2019–2026 DOJ national takedown pages and from the current OIG CIA list, resolve each name to a 10-digit NPI via NPPES, apply a human-name check, keep only those that billed a watched code before the sanction date, deduplicate against the existing 29 LEIE positives, and add the new rows as positives. Refit the model on the expanded label set. 2024 stays held out. 2023 (currently 93 fraud rows) is the check year.
- Add the new positives only as a separate "named in a case" list for display, without using them as training labels or changing the model.
- Leave the current LEIE-only labeling rule unchanged. Do not edit join_labels.py or train.py for new label sources.

Output. Use these headers.

- Decision. One paragraph. Name the pick. Name the file that owns it. Say what the 2023 check must show before the new label rule replaces the current one in join_labels.py.
- Why this pick. A table with one row per option above. Columns: option, what the opened sources say it can change in the positive count or the 48-row rank, what it cannot change, and whether it needs a new fit.
- The change. If the pick is to add the name-resolution step, give the exact source pages, the resolution rule (exact normalized name match, human check required), the owner file, and the values that stay the same (four EXCLTYPE codes, exclusion-year-after-billing-year rule for LEIE rows, 9:1 undersample, seed 1). If the pick is to leave the rule alone, say which file stays byte-for-byte the same.
- Keep rule. A numeric comparison the coder can run on files already here after the name-resolution step. Include the current 29 unique positives, the 2023 top 1% and top 5% shares, and the 2024 top 1% and top 5% shares. Say how large a move in unique positives or in capture share has to be before it counts as material, given 93 and 48 events. Do not invent a confidence interval unless you opened a methods paper that covers a capture share at this sample size, and name that paper.
- Unverified. Claims you could not confirm. A blocked DOJ or OIG page, a name that does not resolve in NPPES, or a methods page that is paywalled goes here.
- Sources. The exact URL you opened, next to the section it supports.

Leave open. Do not invent a preference on these. Put them in the report only if a source makes them part of the pick: whether to add a second algorithm, whether to grid-search depth, whether to download DMEPOS files, and which review budget a person can actually work. Downloading a new dataset is a separate decision from adding DOJ/CIA names as labels.

Do not invent a district, a school, a home address, a parent email, or a 9-digit ZIP. Do not say the page has found fraud. A high score is a resemblance to providers later excluded or sanctioned for a fraud-type reason. An indictment is a charge; use only convictions and settlements as labels. Keep charged-only cases in a separate list.
```

Pass it with `args.breadth` set to 4. Breadth 6 would split the four evidence targets into paraphrases, and the workflow drops claims past the cap.

## Citations

The prompt above follows the same structure and verification discipline as retrain-research-prompt.md while targeting the exact gap named in handoff-label-shortage.md (DOJ name resolution yield and gate passage). Every measured fact is taken from files already in the workspace. The decision options are written so a later coder can implement or reject without further interpretation.
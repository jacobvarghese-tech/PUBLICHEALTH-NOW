---
type: query
title: Paper-holes research prompt
updated: 2026-10-19
tags: [query, app, model]
sources:
  - wiki/concepts/paper-comparison.md
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/
  - https://web.archive.org/web/20170627194828id_/https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv
---

# Paper-holes research prompt

## Question

What prompt should a 12-agent research run use so the report fills only the holes left in the Bauder paper-comparison plan?

## Answer

The comparison plan is [[paper comparison]]. The fit can already run. This prompt does not ask for another model, another class mix, or another learner. It asks for the twelve facts the last run could not open.

The stock `/deep-research` runner cannot field 12 research agents. `args.breadth` is ignored unless it is from 2 to 6, and an out-of-range value leaves the split at 4. The runner that keeps all 12 is the project workflow `paper-holes` at `.grok/workflows/paper-holes.rhai`. Each hole is one research agent. A second agent must open the cited source before a finding counts as filled. Do not pass this prompt to `/deep-research`.

The prompt to pass as the query:

```
I need the missing facts from one comparison plan, so a later session can patch that plan and then fit. The plan is wiki/concepts/paper-comparison.md. The paper is Bauder and Khoshgoftaar, Health Information Science and Systems, 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/ . Do not rebuild the plan. Do not add a learner, a class mix, a year, or a feature the plan does not already name. A hole that stays blocked stays under Unverified. Do not invent a URL, a byte size, a column name, a date format, or a year length.

This run uses 12 agents at once, one hole each. Copy the 12 questions. Do not merge two holes onto one agent. Verification agents are extra. They do not replace any of the 12. A finding counts only when the agent opened the page and a second agent opened it again.

The audience is one person who will patch the plan and then download files. They need a URL, a byte size, a header name, or a quote. They do not need a literature survey.

The 12 holes:

1. 2012 physician file only. Open http://data.nber.org/providerchargepuf/2012/ and the CMS dataset-resources JSON for data year 2012 if a public page lists that year. Return a direct CSV or TXT URL that still contains HCPCS, the byte size, and the header names for gender, provider type, HCPCS, place of service, and the five numeric fields. If the only public 2012 file has HCPCS removed, say so and quote the page. Do not invent a URL from a later year's folder id.

2. 2013 download only. Open http://data.nber.org/cms/providercharge/2013/ and read the data file's header, not only desc_phys2013.txt. Return the direct URL, the byte size, and whether that header contains pgender and hcpcs_cd. A description is not a header.

3. 2014 NBER header only. Open http://data.nber.org/cms/providercharge/2014/ and read the text or CSV header field by field. State whether a gender column is present. Confirm or correct the already-opened CMS URL https://data.cms.gov/sites/default/files/2025-11/6700f86d-d2e5-4f2d-9dcb-8c30412768ff/MUP_PHY_R25_P04_V20_D14_Prov_Svc.csv and the byte count 2905565005 by opening that file's header or its resources JSON. Do not download the whole file if a header read gives the size.

4. NPPES gender file only. Open the current CMS NPI Files page and the latest monthly dissemination page. Return the direct zip URL, the byte size, the file date, and the column name for provider sex. Quote the code values for male, female, and unknown. A March 4, 2026 readme is not enough if the current monthly page is reachable.

5. Paper PDF only. Open https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/ and the PDF. If NCBI blocks the fetch, open the Europe PMC page for PMC6120851 and its PDF. Quote the grouping keys, the five numeric features, the six summaries, the selected exclusion-rule table, the date rule, the month rule, the claims-year rule, and the RF100 score for every class mix. If the PDF disagrees with a local note of AUC 0.87302 at 90:10, the PDF wins. If both sites are blocked, say so.

6. LEIE date format only. Fetch enough of https://web.archive.org/web/20170627194828id_/https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv to read the header and at least five data rows. Quote one EXCLTYPE, one EXCLDATE, one REINDATE, and one WAIVERDATE, including blanks. State whether the dates are YYYYMMDD and whether EXCLTYPE is written 1128a1 or 1128(a)(1). Do not use the October 2026 file in this workspace.

7. Indefinite exclusion only. Open Social Security Act section 1128(c)(3)(G)(ii) and the LEIE exclusion-type page. Quote the minimum period for three or more mandatory offenses. If no opened page gives a numeric year a coder can add, say the plan must keep leaving those rows out of the fraud class. Do not invent a length.

8. Weka RandomForest defaults only. Open the Weka 3.8 RandomForest documentation or source. Name the default number of features per tree and the default seed. If the paper names a seed or a value of i, quote that sentence and prefer the paper. If you cannot open a Weka page, say so. Do not copy an unopened search snippet.

9. Paper LEIE date only. Read the paper's data section and reference 21. Quote any sentence that names the LEIE download month or year. Then open 2017 Wayback captures of the OIG UPDATED.csv. Return the capture date, URL, and byte size of the June 27, 2017 capture and of any nearer 2017 capture that still returns bytes and still has NPI, EXCLTYPE, EXCLDATE, REINDATE, and WAIVERDATE. If the paper names no day, say so.

10. 2013 CMS header only. Open the CMS dataset-resources JSON for data year 2013 and read the data dictionary or the CSV header. Return the CSV URL, the byte size, and whether Rndrng_Prvdr_Gndr, nppes_provider_gender, or HCPCS_Cd is present. This question does not own the NBER 2013 file. If this header has no gender, say the later session must fill gender from NPPES.

11. Five numeric source columns only. Quote the paper sentence that names the five original numeric features. Map each one to a column name you opened in a 2013, 2014, or 2015 physician header or data dictionary. If a feature has no opened column, name the feature and leave it open. Do not guess a column from a later rolled file in this workspace.

12. Figures and supplement only. From the paper PDF, extract the numeric values in Figure 1 and any numeric claim in Figure 2. List every supplement link on the article page, or state that the page you opened has none. These figures do not change the fit. If the PDF is blocked, say so.

Source rules. Prefer the file, the data dictionary, the statute, the Wayback capture, and the paper PDF. Deprioritize SEO explainers, vendor blogs, and Wikipedia. If a page is blocked, say so. Do not reconstruct a URL from a citation or from a neighboring year's folder id. Do not cite a page you did not open.

Already known. Use these as the holes, not as facts to re-derive. The last run did not open the live PDF. It did not open a 2012 data URL. It did not put a 2013 download URL in the roll step. It did not read the 2014 NBER header field by field. It did not open an NPPES zip URL. It did not open an LEIE data row. It found no numeric length for 1128(c)(3)(g)(ii). It did not open Weka's defaults. It did not extract Figure 1 or Figure 2.

Decision the report must make. For each hole, write either the opened fact and its URL, or "still open" and the page that blocked it. Patch wiki/concepts/paper-comparison.md only where a second agent confirmed the fact. Leave every other hole under Unverified. Do not start a download. Do not edit scripts/ or models/.
```

## Citations

- Student request on 2026-10-19 for a deep-research prompt that plugs the holes in the comparison plan, using at least 12 agents at once.
- [[paper comparison]]
- [[closest paper-model prompt]]
- Bauder and Khoshgoftaar, Health Information Science and Systems, 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6120851/

## What this changes in the wiki

Filed the prompt and the `paper-holes` workflow. The workflow smoke check passed. No research run was started. No script or model file was edited.

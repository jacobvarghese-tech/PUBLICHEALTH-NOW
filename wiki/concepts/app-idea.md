---
type: concept
title: App idea
updated: 2026-10-15
tags: [app, ranking, medicare]
sources:
  - coffeezilla-100-billion-healthcare-fraud-transcript-clean.txt
  - handoff-label-shortage.md
---

# App idea

One app: Pattern Check. It ranks unusual Medicare billing for a watched service. A high score is a resemblance to an unusual pattern. The page does not say the biller committed fraud.

## One-sentence purpose

Pattern Check ranks public Medicare billers whose billing for a watched service is unusually concentrated, fast-growing, or high-charged compared with other billers of the same code.

## Audience

Students, reporters, and anyone reading a public Medicare file who wants a starting list, not a verdict.

## Platform and language

A static web app in `app/`. HTML, CSS, and JavaScript. No framework. Open `app/index.html` through a local server so `data/rankings.json` can load. Python prepared that JSON. It is not part of the running page.

## What the demo shows

Service 81419, epilepsy gene panel, year 2024. Prince Laboratories (NPI 1124725817) ranks 1 of 48. Reliable Results Labs (NPI 1639879034) ranks 3 of 48. Both are in Deerfield Beach, ZIP 33441, which holds 23.8% of national services for that code. Neither lab is on the October 15, 2026 exclusion list. The ranking recovers the Coffeezilla example without calling it fraud.

Other watched codes in the file include urine drug tests, remote monitoring, COVID testing, allergy tests, respiratory panels, nerve conduction, and skin-graft application. The table shows the top 40 plus any known sanctioned biller. Rank is against every biller of that code.

## Why there is no classifier

The label gate in `handoff-label-shortage.md` required 50 unique positive NPIs, spread across more than one scheme, each billed before the sanction date, with a year split. The gate failed.

- Physician-file watched codes, 2022–2024, joined to 29 fraud-type LEIE NPIs after the full download. The earlier handoff count was 28. The extra match does not clear the gate. It is a join result, not a conviction count.
- DMEPOS referring-provider catheter codes A4351–A4353, 2021–2024: 22,550 referring NPIs, 3 fraud-type matches. Supplier file: 2,225 NPIs, 0 matches.
- Fifty-five skin-substitute Q codes in the physician file, 2022–2024: 1,564 NPIs, 2 fraud-type matches.
- Those DMEPOS and skin joins together added 5 unique fraud-type NPIs. All 5 billed before the exclusion year. Four are 1128(a)(1). One is 1128(b)(7).
- Wayback snapshots of the exclusion file from 2022 through January 2026 recovered 282 fraud-type NPIs missing from the current file. Ten are 1128(b)(7). None are 1128(b)(6). They were not joined back to billing rows.
- Named labs resolved in NPPES and kept off the positive list: ASAP Lab LLC (1588066278), Andor Labs LLC (1184861353), Minerva Genetics LLC (1023460334), Apex Mobile Medical LLC (1821726589). Charges and a related guilty plea are not labels for the rendering NPI.

Part D was left out on purpose. It is a different fraud type.

## Libraries and tools

- Public CMS Medicare Physician & Other Practitioners by Provider and Service, data.cms.gov, years 2022–2024.
- CMS DMEPOS by Referring Provider and Service, and by Supplier and Service, for the catheter count.
- HHS OIG LEIE `UPDATED.csv`, downloaded 2026-10-15, plus Wayback Machine snapshots.
- CMS NPPES NPI Registry API, for legal-name resolution.
- Python, standard library only, for the counts and the JSON build.

## AI tools used, and for what

Grok, in the Grok Build CLI, queried the public files, counted the label joins, wrote the ranking page, and drafted this note. The decision not to train a classifier follows the gate in the handoff. The student should describe their own part of the build in the portal, in their own words.

## Technical difficulty worth describing

Joining a public billing row to a later sanction. Most exclusion records have no NPI. A match does not name the HCPCS code. The rendering NPI on a lab row is often not the person named in a press release. The working answer was to stop at the ranking and show the feature values beside the score.

## Demo script beats

Under 3 minutes. Names, app name, purpose, audience, tools, then the working demo.

1. Names and "Pattern Check."
2. Purpose, in the sentence above. Say the score is not a fraud finding.
3. Audience: students and anyone reading a public Medicare file.
4. Tools: HTML, CSS, JavaScript, public CMS files, the OIG exclusion list. Mention Grok as a disclosed assistant, and name what the student wrote.
5. Open 81419 for 2024. Show Prince Laboratories at rank 1 and Reliable Results at rank 3. Open a row and read national share, ZIP share, growth, and charge ratio.
6. Switch on "Known sanctioned only" for another code and say these are exclusion matches, not convictions for that service.

## Still blocking a real submission

Home district, school district, and whether either member is hosting. Do not invent them. Parent email, personal email, and 9-digit ZIPs stay out of this vault unless asked.

Related: [[submission]], [[overview]], [[judging]].

# Log

Append-only. Newest entries at the bottom. Prefix format: `## [YYYY-MM-DD] ingest|query|lint | Title`

## [2026-10-15] ingest | Karpathy LLM Wiki gist

Imported the idea file unchanged to `raw/sources/karpathy-llm-wiki.md` from https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f. Instantiated the pattern for this contest in `WIKI.md` and the Obsidian vault config. Did not edit the gist.

Pages: [[LLM Wiki pattern]], [[Karpathy LLM Wiki gist]].

## [2026-10-15] ingest | 2026 contest brief and rules PDF

Saved the official rules PDF to `raw/sources/2026-CAC-Rules.pdf`. Copied the 2026-10-15 agent brief to `raw/sources/contest-brief-2026-10-15.md` and left `AGENTS.md` as the operating schema, not a wiki page.

Seeded the wiki from those two sources. Open conflict: rules PDF says submit by 12:00 p.m. EDT on October 26, 2026. Registration page, as recorded in the brief, says 9:00 p.m. ET the same day. Planning deadline is noon.

Pages touched: [[overview]], [[index]], [[Congressional App Challenge]], [[Internet Education Foundation]], [[House of Representatives]], [[deadline]], [[eligibility]], [[submission]], [[judging]], [[prizes]], [[app idea]], [[2026 contest brief]], [[2026 CAC Rules PDF]], [[LLM Wiki pattern]].

District, member, team, and app concept are still unknown.

## [2026-10-15] query | Label gate and the ranking app

Finished the label hunt in `handoff-label-shortage.md` and shipped the unsupervised ranking because the gate failed.

DMEPOS referring-provider catheter codes A4351–A4353, 2021–2024, joined 22,550 NPIs to 3 fraud-type exclusions. The supplier file joined 2,225 NPIs to 0. Fifty-five skin-substitute Q codes joined 1,564 NPIs to 2. Those searches added 5 unique fraud-type NPIs, all billed before the exclusion year. Wayback snapshots recovered 282 fraud-type NPIs missing from the current file. They were not joined to billing rows. Named labs resolved in NPPES stayed off the positive list. Physician-file watched codes joined to 29 after the full 2022–2024 download. The gate needed 50.

## [2026-10-16] query | Firm-flagging handoff

The next build is the published LEIE join, not another unnecessary-test label hunt. Wrote `handoff-firm-flagging.md`. Paper baseline is 1,409 fraud provider-years for 2012–2015. The 2012–2024 estimate is about 4,600 fraud rows. The trained model does not exist yet. Pattern Check in `app/` remains the ranking page.

The app is Pattern Check in `app/`. For 81419 in 2024, Prince Laboratories ranks 1 of 48 and Reliable Results ranks 3 of 48. The page says a high score is an unusual pattern, not a fraud finding.

Pages touched: [[app idea]], [[overview]], [[index]].

# LLM Wiki schema — Congressional App Challenge

This file is the schema for the Obsidian vault in this folder. It instantiates Andrej Karpathy's LLM Wiki pattern for one job: get one eligible app submitted to the 2026 Congressional App Challenge before noon Eastern on October 26, 2026.

The idea file is imported unchanged at `raw/sources/karpathy-llm-wiki.md`. Source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

Read this file at the start of every session that touches the vault. Then read `wiki/index.md`. Then read `wiki/log.md` from the bottom if you need recent context. The contest operating rules stay in `AGENTS.md`. This file tells you how to maintain the wiki. `AGENTS.md` tells you how to help ship the entry.

## Roles

Obsidian is the IDE. The agent is the programmer. The wiki is the codebase.

The human curates sources, picks the app idea, and asks questions. The agent writes and maintains every page under `wiki/`. The human rarely edits wiki pages. If the human does edit one, treat that edit as intentional and do not revert it.

## Three layers

```
congressional app/
  AGENTS.md          contest operating rules (do not turn this into a wiki page)
  WIKI.md            this schema
  raw/sources/       immutable sources. Read only. Never edit, rename, or delete.
  raw/assets/        images and attachments. Obsidian saves new attachments here.
  wiki/index.md      catalog. Update on every ingest, filed query, and lint.
  wiki/log.md        append-only timeline.
  wiki/overview.md   current synthesis. Rewrite when the picture changes.
  wiki/sources/      one summary page per ingested source
  wiki/entities/     people, orgs, offices, products
  wiki/concepts/     rules, deadlines, judging, prizes, app idea, submission
  wiki/queries/      answers worth keeping
  templates/         Obsidian templates for new source and query notes
  .obsidian/         vault config
```

`raw/` is the source of truth. If a wiki page and a raw source disagree, the raw source wins. Flag the disagreement on both pages instead of silently picking one.

Do not store home addresses, parent emails, phone numbers, or school names in this vault unless the human explicitly asks for a private notes file. Tell them what to type into the portal.

## Page format

Every wiki page starts with YAML frontmatter:

```yaml
---
type: source | entity | concept | query | overview | index
title: Human title
updated: YYYY-MM-DD
tags: []
sources: []
---
```

- `sources` lists raw filenames or URLs the page depends on, not wiki pages.
- Body links to other wiki pages use Obsidian wikilinks: `[[eligibility]]`, `[[Internet Education Foundation]]`.
- Cite a raw source inline like this: `(raw/sources/2026-CAC-Rules.pdf)`.
- One idea per page. If a section wants to become its own page, make the page and leave a link.
- Write in plain sentences. No pep talk. No invented facts. If a date or rule is uncertain, say which source said what.
- When two official sources disagree, keep both claims and name both sources. Do not average them.

## index.md

`wiki/index.md` is the catalog. The agent reads it first on a query.

Each entry is a wikilink plus one sentence. Group by category: Overview, Concepts, Entities, Sources, Queries. Update it in the same pass as any page you add, rename, or retire.

At this size, the index replaces a search engine. Do not add embeddings or qmd unless the wiki passes a few hundred pages.

## log.md

Append only. Never rewrite old entries. Each entry starts with this prefix so it can be grepped:

```
## [YYYY-MM-DD] ingest | Title
## [YYYY-MM-DD] query | Question
## [YYYY-MM-DD] lint | Short result
```

Under the heading, write 3–8 lines: what changed, which pages were touched, and any contradiction left open.

## Operations

### Ingest

Trigger: the human drops a file in `raw/sources/` or pastes a URL and says to ingest it. Also ingest when you fetch a new official page that changes a contest fact.

1. Read the source. Do not modify it. If it is a URL, save a markdown or PDF copy into `raw/sources/` first, with a dated filename, then ingest the file.
2. Discuss the takeaways with the human if they are in the conversation. If they are not, proceed and note assumptions in the log.
3. Write `wiki/sources/<slug>.md`. Lead with what the source establishes, then claims, then what it does not say.
4. Update every entity and concept page the source touches. One source often updates 5–15 pages. That is expected.
5. If a claim contradicts an existing page, write the contradiction on both pages. Do not delete the old claim.
6. Update `wiki/overview.md` if the current picture changed.
7. Update `wiki/index.md`.
8. Append a log entry.

Stay involved on the first sources. Batch later sources only if the human asks.

Official contest pages already scraped on 2026-10-15 and compiled into `AGENTS.md` are ingested via `raw/sources/contest-brief-2026-10-15.md`. Re-fetch a page when a decision depends on a fact that may have changed, especially the deadline clock time and the participating-district list.

### Query

Trigger: the human asks a question about the contest, the app, the district, the video, or the written answers.

1. Read `wiki/index.md`.
2. Open the pages that match. Open raw sources only when the wiki is thin or the pages disagree.
3. Answer with citations to wiki pages and, when the claim is load-bearing, to the raw file.
4. If the answer is reusable, file it at `wiki/queries/<slug>.md` and link it from the pages it depends on. Chat history is not the knowledge base.
5. Append a log entry for filed answers. Skip the log for a one-line lookup that changed nothing.

### Lint

Trigger: the human says "lint", or a session is about to make a submission decision.

Check:

- Contradictions between pages, especially deadline, eligibility, and prizes.
- Claims superseded by a newer source.
- Orphan pages with no inbound links.
- Concepts mentioned on two or more pages that still have no page of their own.
- Missing cross-links.
- Gaps a web search could fill. Suggest the search. Do not invent the result.
- Personal data that should not be in the vault.
- Whether `wiki/overview.md` still matches the concept pages.

Write the result to `wiki/queries/lint-YYYY-MM-DD.md` if you found real issues. Always append a log entry.

## Domain rules for this vault

The deadline in force for planning is noon Eastern on October 26, 2026. The registration page said 9:00 p.m. ET as of 2026-10-12. Keep both on [[deadline]] until a newer official source resolves it.

Do not invent a district, member, school, or ZIP. Those pages stay stubs until the human supplies an address and you look it up.

One student, one app, one district. Do not open a second app concept page unless the human retires the first idea.

AI use on the contest app must be disclosed. Track tools and libraries on [[app idea]] as soon as they are chosen.

Judging weight, in the order the rules list it: idea, implementation and design, coding skill. A pretty unfinished app loses to a small app that runs.

## Obsidian

Open this folder as a vault: **Open folder as vault** and choose `congressional app`.

- Graph view is the map. Color groups are already set: sources blue, entities orange, concepts green, queries purple.
- New attachments go to `raw/assets`.
- Wikilinks are shortest path, so `[[deadline]]` resolves.
- Core plugins on: graph, backlinks, outgoing links, outline, properties, canvas, page preview.
- Templates live in `templates/`. Core Templates plugin is off so this vault does not depend on a plugin install. Copy a template by hand, or enable Templates and point it at `templates/` if you want hotkeys.
- Optional later: Obsidian Web Clipper, Dataview, Marp. None are required.

## Co-evolution

If a workflow in this file is wrong for how the human actually works, edit this file and log the change. Do not fork a second schema.

---
type: concept
title: LLM Wiki pattern
updated: 2026-10-15
tags: [wiki, method]
sources:
  - raw/sources/karpathy-llm-wiki.md
---

# LLM Wiki pattern

Andrej Karpathy's idea file for a persistent, compounding knowledge base. Imported unchanged to `raw/sources/karpathy-llm-wiki.md`. Gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

This page is both the concept note and the source note. The gist says the wiki should be written by the agent. The gist itself stays immutable in `raw/sources/`.

## What he is arguing

RAG re-derives an answer from chunks on every question. Nothing accumulates. An LLM wiki sits between the human and the raw sources. On ingest, the model updates entity pages, summaries, and contradictions. The next question starts from that compiled graph.

The human curates sources and asks questions. The model does the bookkeeping. Obsidian is the IDE, the LLM is the programmer, and the wiki is the codebase.

## Three layers, as used here

- Raw sources: `raw/sources/`. Immutable.
- Wiki: `wiki/`. The agent owns it.
- Schema: `WIKI.md`. Contest behavior stays in `AGENTS.md`.

## Three operations

- Ingest a source and update the pages it touches.
- Query the index first, then file a useful answer back into `wiki/queries/`.
- Lint for contradictions, stale claims, orphans, and missing pages.

`wiki/index.md` is the catalog. `wiki/log.md` is the append-only timeline. At this size, the index is enough. Karpathy points at [qmd](https://github.com/tobi/qmd) only after the wiki outgrows an index.

The schema for this vault is `WIKI.md`. If that file drifts from the gist, the gist remains the idea and `WIKI.md` remains the local rules.

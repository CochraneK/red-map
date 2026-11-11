# Decisions

## Canonical data

`data_edit/*.csv` is the editable canonical layer. `data/long_march_events.json` is generated and must reproduce exactly from the tables.

## Candidate material boundary

Extracted third-party game text is research input only. Raw extraction stays in `research_private/`. Rewritten public entries may use it as a clue source, but game-only support remains low-certainty until independent evidence is attached.

## Asset provenance

A source page is not the same thing as a verified license. External visual assets require per-file provenance, author/credit and redistribution terms. Unresolved entries remain a publication/IP debt rather than being silently treated as cleared.

## Historical/content boundary

Repository-maintenance automation may validate references, schemas, certainty labels and provenance fields. It must not silently adjudicate contested historical interpretations or replace human source review.

## Coordinates and visual narration

Map coordinates, route interpolation and pursuit/blockade layers are visualization devices unless exact precision is separately sourced.

## Agent continuity

Git is canonical. AGENTS/HANDOFF/STATUS/DECISIONS summarize state but do not override the data tables or evidence fields.

## Identity

Repository-facing identity is **CochraneK**.

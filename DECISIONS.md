# Decisions

## Canonical data

`data_edit/*.csv` is the editable canonical layer. `data/long_march_events.json` is generated and must reproduce exactly from the tables.

## Candidate material boundary

Extracted third-party game text is research input only. Raw extraction stays in `research_private/`. Rewritten public entries may use it as a clue source, but game-only support remains low-certainty until independent evidence is attached.

## Asset provenance

A source page is not the same thing as a verified license. External visual assets require per-file provenance, author/credit and redistribution terms. Unresolved entries remain a publication/IP debt rather than being silently treated as cleared.

**Resolution (2026-11-24, v32)**: external asset rows are cleared only when the license string and the attribution string are both fetched from the upstream file page metadata (Wikimedia Commons `extmetadata`), never copied by hand and never left as `see file page`. The check is a hard gate. `imagePageUrl` stays mandatory as the authoritative provenance record.

## Low-certainty adjudication

Game-derived clues are adjudicated in exactly four auditable classes — `UPGRADE_HIGH`, `UPGRADE_MEDIUM`, `DISABLE_DUP`, `DISABLE_BROKEN` — plus an explicit decision to keep a clue at `low` when no independent evidence exists yet. Every disabled row records its reason and its merge target in `notes`; every person link attached to a disabled row is either remapped to the canonical event or disabled. No dangling links are acceptable.

**Date matching requires numeric boundaries.** A substring match on `M月D日` without a `(?<!\d)` guard will match `11月25日` when looking for `1月25日`, and a match on `1935年6月25日` will match `1934年6月25日`. Year constraints and keyword co-occurrence are part of the same rule.

**Certainty promotion requires verbatim verification in a local authoritative corpus.** The authoritative corpora used are `research_private/ebooks/changzhengji_people/` (曲爱国/张从田《长征记》, 29 chapters) and `research_private/ebooks/hongjun_changzhengji/` (1937《红军长征记》, 135 essays plus the《长征大事记》appendix). Matching a summary, a title resemblance, or a plausible date is not sufficient.

## Place-name layer

`data_edit/gazetteer.csv` is the canonical place-name layer and is regenerated on every pipeline run. Homonym disambiguation is explicit: "两河口", "安定", "俄界", "大河滩" and similar names carry a note naming which modern county the historical site belongs to. The gazetteer is a data layer, not a claim of exact historical coordinates.

## Historical/content boundary

Repository-maintenance automation may validate references, schemas, certainty labels and provenance fields. It must not silently adjudicate contested historical interpretations or replace human source review.

## Coordinates and visual narration

Map coordinates, route interpolation and pursuit/blockade layers are visualization devices unless exact precision is separately sourced.

## Agent continuity

Git is canonical. AGENTS/HANDOFF/STATUS/DECISIONS summarize state but do not override the data tables or evidence fields.

## Identity

Repository-facing identity is **CochraneK**.

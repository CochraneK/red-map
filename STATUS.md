# Status

## State

**Active digital-curation prototype with explicit source/provenance debt.**

## Current strengths

- table-first canonical data;
- deterministic JSON generation;
- source ids carried into publication data;
- separate map, museum, immersive museum and local editor;
- ignored private research/extraction area;
- repeatable project checker.

## Current gates

- raw third-party extracted text must stay private;
- game-only candidate material must not silently become high-certainty;
- external image licenses/attribution still need per-file completion where the current registry says only “see file page”;
- route coordinates and some interpretive visual layers are approximate;
- historical/source review is an editorial/research gate separate from code correctness.

## Canonical state

Current data counts should be read from `python tools/check_project.py`, not copied manually into status documents.

## 2026-11-22 structural feedback pass (v9)

Applied structural changes from the 2026-05-28 meeting feedback (see `docs/FEEDBACK_ACTION_PLAN.md`):

- **Route grouping (frontend + data)**: `subjects.csv` now carries `group` / `groupEn`; route panel groups forces into 红军主线 / 星星之火 / 敌军. Added 5 missing subjects as **skeleton only** (红西路军, 琼崖纵队, 东北抗联, 东江纵队, 日军) — no invented events; each marked "events pending sourced review".
- **Colors**: main Red Army routes moved to a red-dominant palette (国旗红 for 红一方面军, darker/lighter reds for others); KMT enemy → black; Japan → dark slate. Interpretive layer, not historical claim.
- **Time range**: `timeRange.end` extended to 1936-12-12 (西安事变) per feedback; `start` already covered 第五次反围剿.
- **Museum navigation**: hall labels reframed as "视角" (viewpoints) instead of "第X展厅"; added a "新长征" placeholder section with the public 论述 quote and an explicit "权威素材待补" note — no fabricated itinerary or speeches.
- **Local consolidation**: reverse-engineering artifacts (pak parse tools, 211MB unpacked game assets, legacy datasets, martyrs reference) moved under ignored `research_private/`; feedback transcript + Steam URL copied into `docs/`.

Gates unchanged: game-only events remain low-certainty (246), raw extraction stays outside Git, visual-asset licenses still unresolved (34/38). All structural additions are candidate/skeleton and must not be presented as verified history without independent sourcing.

Validation: `python tools/check_project.py` passes (subjects=28, events=386, persons=67). Browser smoke test confirmed grouping labels, viewpoint nav, and new-longmarch section render without runtime errors (only favicon 404).

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

## 2026-11-22 sourced-research pass (v10)

Authorized historical research added with authoritative sources; see `research_private/sourced_research/*.md` for full source URLs and ⚠️ doubtful items.

- **Sources** 38→59, **events** 386→411, **persons** 67→79. All 25 new events are `certainty=high` with resolvable source ids; 12 new persons added.
- **西路军** (7 events, force `red_west_route`): 渡河/组建/永昌山丹/高台/倪家营子/石窝/星星峡. **东北抗联** (5, `spark_dongbei`), **琼崖纵队** (8, `spark_qiongya`), **东江纵队** (5, `spark_dongjiang`).
- Correction applied: 董振堂 title is 红五军军长 (not 军团军团长); 杨克明 is 红五军政治部主任 (not 董振堂政委). Rejected as unverifiable: "熊炳林" (查无此人), "陈荣香/陈文香断肠" (无权威来源, likely confused with 陈树湘).
- **新长征**: quote corrected to 2016-10-21 长征胜利80周年讲话原文, with explicit note that "一代人有一代人的长征..." is from 2019-04-30 五四讲话; both official gov.cn links added.
- **Memorial layer**: `data/memorial_sites.geojson` — 16 长征-related memorial sites with GCJ-02 coordinates sourced from 腾讯地图 POI / government sites. Toggle button `#memorial-toggle` on map page shows/hides `L.circleMarker` layer (no external API key). Browser test: marker count 1→17 on toggle.
- **Game-content audit** (`docs/GAME_CONTENT_AUDIT.md`): game text extraction yields 5,905 strings / 1,028 timeline candidates, but only 246 events + 32 persons were imported (all `low` certainty). Game content is NOT fully in the project.
- New tool `tools/import_sourced_research.py` (idempotent, by id) reproduces the table additions.

All new time-extended events (1927-1950) are marked as 延伸视角 in notes; they enlarge the timeline beyond 1934-1936 by design (西路军 is the Long March epilogue; 琼崖/东江/抗联 are the "星星之火" follow-on). Check passes with 0 errors (1 pre-existing visual-asset license warning).

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

## 2026-11-22 evidence-model + multi-source + explore UI (v11)

- **Evidence model**: `sources.csv` gained `sourceType` (authoritative/game_text/book/subtitle/oral_history/public_narrative). `check_project.py` now enforces a non-authoritative certainty ceiling — non-authoritative-backed events cannot be `certainty=high` (246 game events verified). Extend via `tools/extend_evidence_model.py`.
- **Input pipelines** (candidates only, never auto-imported): `tools/extract_book_candidates.py` (PDF text layer / TXT / OCR text → anchored snippets with page + date hints; scanned PDFs require external OCR — no engine bundled), `tools/extract_subtitle_candidates.py` (srt/vtt/ass, timeline-block merge, ASR transcript entry point → public_narrative candidates). Both output to `research_private/`.
- **Explore UI**: new `explore.html` + `js/explore.js` + `css/explore.css` — data-driven thematic entry (person/force/place/event cards), replaces index.html's direct jump to museum. `museum.html?person=<id>` deep-link selects a person automatically. Index now points to explore.html. check_project.py covers the new files.
- Browser verified: 8 person / 12 force / 10 place / 6 event cards render; `?person=dongzhengtang` selects 董振堂 correctly. No runtime errors (favicon 404 only).

Local scanned gazetteers (绥德州志 etc., PDF, 39-154MB) have NO text layer — need OCR before the book pipeline can use them. No OCR engine installed locally at time of writing.

**UI decision (user, same day)**: keep the previous museum-first UI. `index.html` and both start scripts point back to `museum.html`. `explore.html` remains in the repo as an optional, non-default entry. Evidence-model and input-pipeline changes from v11 are unaffected.

## 2026-11-22 data densification (v12/v13)

Addressed the "is the data sufficient?" audit (main route was sufficient; person links + credibility were not):

- **v12 — person-event links**: `tools/link_zero_person_events.py` added 33 evidence-based links (zero orphans 19→0); `tools/add_key_persons.py` added 5 key missing figures (博古/李德/林彪/方志敏/程世才) from authoritative sources + 2 红十军团 events + 10 links.
- **v13 — extended routes**: `tools/import_extended_events.py` (data in `research_private/sourced_research/04_extended_events.json`) added 31 authoritative events + 10 persons + 29 links: 西路军 15, 琼崖 15, 抗联 13, 东江 13 — each route now 13-15 nodes, enough for a continuous story. All with source URLs; doubtful items (镜泊湖 disputed figures, 琼崖 renaming, 孙玉清 exact date) marked medium or excluded.
- **Result**: events 411→444, persons 79→94, links 348→420, high-certainty 32→63, low share 60%→55%, zero person orphans.
- Browser verified: 444 events, timeline 1927-1950, 12 forces, 3 groups, no runtime errors. check_project.py passes.

**Remaining gap**: low-certainty (game-text) events still 246 — the single biggest credibility debt. Next priority is upgrading high-importance game clues with authoritative sources.

## 2026-11-22 low→high upgrade pass

Method: authoritative-source verification, NOT relabeling. `tools/upgrade_game_clues.py` reads a result JSON, replaces the game source with the authoritative source (so the "non-authoritative cannot be high" gate holds), disables duplicates + cleans their person-event links, and annotates keep-low items. All upgrade sources verified as 中国共产党新闻网 / 人民网.

- **batch1 (红一方面军, 20 checked)**: 10 UPGRADE (道县/四道封锁线/施秉黄平/猴场会议/遵义会议/二渡赤水/四渡赤水/金沙江/大渡河/夹金山), 3 DUP disabled, 4 KEEP_LOW (bad dates/game invention).
- **batch2 (data-quality errors)**: 4 游戏文本拼接错点 disabled — "到达莫斯科"×2 ("在贵州遵义一带到达莫斯科"), "占领西宁"×2 ("在四川松潘毛儿盖占领西宁"); also cleaned 8 bogus person-event links these errors had polluted.
- **batch3 (other routes, 12 checked)**: 6 UPGRADE (阆中/红六军团占新田/渡湘江/红25军北上宣言/独树镇/陕甘反围剿), 5 KEEP_LOW (张冠李戴/日期错位: 红四渡金沙江, 会宁占领, 红二渡金沙江, 川南游击纵队, 金沙江日期).
- **Net**: high 63→79 (+16), game-only low 246→223 (-23: 16 upgraded + 7 disabled). No event carries both game source and high certainty. check_project.py passes; browser verified 437 events render.

**Key finding**: game-text extraction has systematic place/event splicing errors (Moscow/Xining) — these were silently polluting the person timelines. Recommend always cross-checking game-derived location against the event description before import.

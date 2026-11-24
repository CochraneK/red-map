# Agent Handoff

## Current mission

Keep the public museum/map reproducible from structured sources while reducing historical-source, copyright, and asset-provenance ambiguity.

## Current architecture

- `data_edit/*.csv` — editable canonical records.
- `tools/build_json_from_tables.py` — deterministic compiler.
- `data/long_march_events.json` — generated publication dataset.
- map/museum/admin pages — static browser consumers.
- `research_private/` — ignored local research material.
- Steam/Unreal extraction tools — candidate-material pipeline, not publication truth.

## Current gates

1. Table → JSON reproduction must be exact.
2. Every referenced source id must resolve.
3. A public item backed only by extracted game text must remain low-certainty until independently sourced.
4. Raw third-party game extraction must stay outside Git.
5. External visual assets require provenance review; a generic “see file page” value is unresolved, not a verified license.
6. Coordinates and interpretive route layers remain visualization approximations unless separately validated.

## Immediate next actions

- Gradually replace game-only low-certainty entries with independently sourced evidence or keep them clearly marked as candidates.
- Replace generic visual-asset license placeholders with exact per-file license/attribution records.
- Add browser smoke tests for map/museum/admin load after the deterministic data checks.
- Keep README/AUDIT_REPORT counts generated or non-stale instead of manually maintained snapshots.

## 2026-11-22 update — feedback structural pass

- Read `docs/FEEDBACK_ACTION_PLAN.md` first: structured checklist extracted from the 2026-05-28 meeting transcript (`docs/feedback_meeting_20260528.txt`). Several items are marked `[已解决]` because the canonical repo had already cleaned severe route cross-contamination; the remaining actionable structural items were applied.
- Added 5 skeleton subjects (红西路军/琼崖纵队/东北抗联/东江纵队/日军) with `group` field — **no events attached**, explicitly pending authoritative sourcing. Do not treat them as verified history.
- Historical-detail items (西路军/琼崖/抗联 event timelines, 英烈牺牲细节, 新长征 图文素材, 烈士陵园地图) are intentionally left as `[需史料]` / `[决策]` — they require authoritative sources, not invention.
- `research_private/` now holds the consolidated reverse-engineering artifacts (pak tools, unpacked assets, legacy datasets, martyrs reference); it stays Git-ignored.

## 2026-11-22 sourced-research pass (v10)

- Authorized factual research is in `research_private/sourced_research/*.md` (Git-ignored; full source URLs + ⚠️ doubtful items). Published tables only carry source-backed, non-doubtful items via `tools/import_sourced_research.py`.
- `docs/GAME_CONTENT_AUDIT.md` answers "is all game content in?": No — 5,905 extracted strings / 1,028 timeline candidates vs 246 imported events (all low-certainty). Decide whether to expand import (as low-certainty clues) or keep the curated 246.
- **Doubtful items deliberately NOT imported**: 熊炳林 (no such person in authoritative sources), 陈荣香/陈文香 断肠 story ( unverifiable, likely 陈树湘 confusion), 冯白驹/王文明/曾生 exact birth-death years (left blank), 八女投江 exact year.
- Memorial layer is data-autonomous: `data/memorial_sites.geojson` (16 sites, GCJ-02) + `#memorial-toggle` on map.html; no API key needed. Some coordinates are POI/估算 — marked in each feature's `precision` field; re-verify before public display.
- 新长征 quote provenance corrected: main quote from 2016-10-21 长征胜利80周年讲话; the "一代人有一代人的长征" line is from 2019-04-30 五四讲话 — do not conflate.

## 2026-11-22 evidence model + explore UI (v11)

- Default UI is museum-first: `index.html` redirects to `museum.html`; start scripts open the museum. `explore.html` is an optional, non-default thematic entry (person/force/place/event) kept in the repo. `museum.html?person=<id>` deep-links to a person.
- To add material from books/subtitles: run the extract_* tools → review candidates in `research_private/` → only then import source-backed items with certainty <= medium. Non-authoritative sources are blocked from `certainty=high` by check_project.py.
- Scanned PDFs (local 绥德州志 etc.) need OCR first; no OCR engine is bundled. Install one (PaddleOCR/Tesseract) or use an external OCR tool, then feed the text/TXT to extract_book_candidates.py.
- Method note: "science-based enrichment" = measure coverage first (主体×时间×证据等级), prefer upgrading low→high over adding more low, deepen person-event links, then broaden. See conversation / STATUS for the four-dimension framework.

## 2026-11-22 data densification (v12/v13)

- Data now: 444 events / 94 persons / 420 person-event links / 63 high-certainty. Zero person orphans. Extended routes (西路军/琼崖/抗联/东江) each 13-15 nodes.
- Reproducible tools: `link_zero_person_events.py`, `add_key_persons.py`, `import_extended_events.py` (reads JSON in `research_private/sourced_research/`). All idempotent.
- **Biggest remaining debt**: 246 `low` (game-text) events. The 58 with importance>=4 are the best upgrade candidates; many duplicate authoritative events already in the data, so dedupe first.
- Note on tooling pitfall: hardcoding Chinese text with embedded ASCII quotes in Python source caused repeated syntax errors; final pipeline puts all Chinese copy in a JSON data file and keeps the Python script quote-free. Follow this pattern for future imports.

## 2026-11-22 low→high upgrade pass

- `tools/upgrade_game_clues.py` upgrades game-derived events with authoritative sources: reads a result JSON (in `research_private/sourced_research/upgrade_results_batch*.json`), REPLACES game source with authoritative (required — gate forbids game-text source at high certainty), disables duplicates + cleans their links, annotates keep-low. Idempotent.
- Result: high 63→79, game low 246→223. 16 events upgraded (全部中国共产党新闻网/人民网核实), 7 disabled (3 dup + 4 extraction errors).
- **Game-text extraction has systematic location splicing errors** (e.g. "在贵州遵义一带到达莫斯科", "在四川松潘毛儿盖占领西宁") — 4 such errors were disabled; they had polluted 8 person-event links. Always cross-check game-derived locationName against description before trusting.
- Still 223 game-text low events — biggest remaining credibility debt. Prioritize by importance=4, but dedupe against existing authoritative events first (many are alternate phrasings of the same event).

## 2026-11-22 multi-source capture + literature extraction

- **ASR/subtitle toolchain** ready but low-yield at current quality: `tools/asr_to_srt.py` (faster-whisper-base from `C:/Users/cunyi/.workbuddy/skills/whisper-openai-shim/models`, run with `envs/default` python), `tools/correct_asr_terms.py` (domain term fix). B站 has no CC subtitles → must ASR; base model too inaccurate for military proper nouns; small model download blocked; film subtitle sites need Turnstile. Full findings: `research_private/sourced_research/06_多源采集实验报告.md`. All media artifacts stay git-ignored under `research_private/media_capture/`.
- **Preferred enrichment method**: WebFetch structured extraction from authoritative党史 pages (事件-时间-地点-人物 五要素, mark 原文未注明, no invention) → `research_private/sourced_research/*.md` → verify with agent → import JSON via `import_extended_events.py`. This yields far higher quality than ASR subtitles.
- Literature gaps filled (07_文献抽取补录.json): +3 events (南方游击战争/扎西张闻天负总责/苟坝三人小组), +3 persons (项英/陈毅/瞿秋白), +9 links. Corrected 程子华政委 in r25_19350918_yongping_meeting.
- `import_extended_events.py` now accepts an optional JSON path argument (defaults to 04_extended_events.json).

## Validation

```bash
python tools/pipeline.py
```

## 2026-11-24 update — P0 + P1 refactor complete (v31)

- **Single build command**: always run `python tools/pipeline.py` (runs `build_cited_details.py` → `build_json_from_tables.py` + `build_variant_groups.py` → `build_references_md.py` → `check_project.py`). Legacy one-off scripts are archived in `tools/archive/`.
- **Strict schema gates** in `tools/check_project.py`:
  - `events.csv` requires valid `layer` (`march`/`spark_march`/`theme_stat`/`historiography`), `datePrecision` (`day`/`month`/`range`/`approx`), `certainty` (`high`/`medium`/`low`), canonical 8 `type` values (`战斗`/`行军`/`决策`/`渡险`/`会师`/`牺牲`/`民生`/`史料`), clean `locationName` (<=24 chars, no quotes/essay titles), and 0 unwhitelisted >300km jumps in `layer=march`.
  - `certainty=high` requires at least one `sourceType=authoritative` source; `subjects.csv` forbids `type=person`; `sources.csv` requires unique titles.
- **Frontend state**: `map.html` defaults to `scopeMode=core` (1934–36) + `evidenceMode=verified` (287 verified core march nodes) and exposes provenance/variants/person-track highlights; `museum.html` paginates catalog (36/page), supports live person search, and turns Viewpoint 7 into a searchable Reference Center with reverse event lookup; `explore.js` 15/15 person IDs and deep links fixed.
- **Next milestone (P2 in `ROADMAP.md`)**: verify/clean the remaining 210 `low` game-text clues, mine remaining ~90 essays of《红军长征记》to zero out 31 orphan authors, resolve 34 external visual-asset licenses, and build `data_edit/gazetteer.csv`.

## 2026-11-24 update — P2 credit cleanup + source depth closed (v32)

- **P2 全部四项子任务完成并达成硬验收标准**：`low` 210 → **40（7.6%）**，`high+medium` **92.4%**；零关联人物 **31 → 0**；未清债外部图片 **34 → 0**；新增 `data_edit/gazetteer.csv`（**365 个规范地名**，53 条同名消歧注释）。
- **裁决方法论（可复用）**：
  - 权威核验只认**逐字命中本地权威全文**——`research_private/ebooks/changzhengji_people/`（曲爱国/张从田《长征记》29 章，人民网党史频道）与 `research_private/ebooks/hongjun_changzhengji/`（1937《红军长征记》135 篇 + 附录《长征大事记》）。
  - **匹配器必须带数字边界**：`(?<!\d){m}月{day}日` + 年份约束 + 关键词共现，否则 `1月25日` 会误命中 `11月25日`、`1935年6月25日` 会误命中 `1934年6月25日`。这一坑已写进 `research_private/p2_analyze_all.py`。
  - Steam 抽取的三类系统性格局错误需成批识别：**主语倒置**（敌军会议/敌军反扑误套红军，如「中央红军召开了敌薛岳部师以上将领参加的军事会议」）、**跨部队克隆**（同一天同一事件被同时记到红一/红二/红四方面军）、**地点串台**（如「若尔盖草地」「贵州遵义」硬贴到实际在云南/陕西的事件）。
  - 处置必须是**可审计四分类**：`UPGRADE_HIGH` / `UPGRADE_MEDIUM` / `DISABLE_DUP` / `DISABLE_BROKEN`，外加诚实保留 `low`；每条禁用都要在 `notes` 写明理由与归并目标，人物关联要么重映射要么禁用，**不允许悬空**。
- **新增工具**：
  - `tools/build_gazetteer.py` → `data_edit/gazetteer.csv`（`pipeline.py` 第 2 步自动重建）。
  - `tools/archive/p2_adjudicate_low_events.py`、`p2_second_pass_low_cleanup.py`、`p2_harvest_hongjun_and_link_authors.py`、`p2_resolve_visual_licenses.py`（均幂等，可重放审计）。
  - `tools/build_cited_details.py` 新增《长征记》章目与《红星照耀中国》篇次识别模式 → `src_changzhengji_people` 的 `citedDetail` 从空变为 23 处章目定位。
- **门禁升级**：`check_project.py` 的视觉资产版权检查由 WARN 改为**硬失败**（未清债即阻断）；新增 `check_gazetteer_integrity`（≥100 条规范地名且坐标合法）。
- **验收方式**：`python tools/pipeline.py`（五步全绿）+ Edge 无头浏览器冒烟测试（`research_private/p2_smoke_test.py`：6 页 + 4 条深链 0 运行时错误，含 `window.marchMap` 双模式切换往返断言）。注意离线冒烟测试需为 Leaflet 提供 stub（`L.control.zoom` / `L.Symbol.arrowHead` / `L.point` 是三个必填桩）。
- **下一步（P3）**：OCR 批处理管线补全陕北地方志；敌军节点与烈士陵园坐标精校；`gazetteer.csv` 接入前端地名检索与同名异地说提示；剩余 40 条 `low`（多为 1933–1935 陕甘根据地建设史与红七军团闽赣转战）定点核实。


Do not rely on chat history as project state; update Git before handing off.

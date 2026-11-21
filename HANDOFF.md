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

## Validation

```bash
python tools/check_project.py
```

Do not rely on chat history as project state; update Git before handing off.

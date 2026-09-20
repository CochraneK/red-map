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

## Validation

```bash
python tools/check_project.py
```

Do not rely on chat history as project state; update Git before handing off.

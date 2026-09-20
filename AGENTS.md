# AGENTS.md

## Mission

`red-map` is a static digital-history / digital-curation prototype built from structured tables, generated JSON, route/museum views, and an offline research-material pipeline.

The repository must keep **published data**, **candidate research material**, and **source/provenance status** clearly separated.

## Read first

1. `README.md`
2. `HANDOFF.md`
3. `STATUS.md`
4. `DECISIONS.md`
5. `PROVENANCE_STATUS.md`
6. `docs/architecture.md`
7. `data_edit/*.csv`
8. `tools/build_json_from_tables.py`
9. `tools/check_project.py`

## Non-negotiable boundaries

- `data_edit/*.csv` is the editable canonical data layer; `data/long_march_events.json` is generated output.
- Third-party game text is a **candidate clue source**, not automatically verified historical evidence.
- Raw extracted game text stays under ignored `research_private/`; do not commit it.
- A rewritten/public event supported only by the game-text source must remain visibly low-certainty until an independent source is attached.
- Do not treat “Wikimedia Commons” or “see file page” as a verified per-file redistribution license. Asset provenance debt stays explicit.
- Do not silently change historical interpretation or source priority in a repository-maintenance task.
- Do not present map coordinates or pursuit lines as exact military reconstruction unless that precision is independently sourced.
- Repository-facing identity is **CochraneK**.

## Validation

```bash
python tools/check_project.py
```

CI also verifies that `research_private/` and other extracted private research artifacts are not tracked.

## Checkpoint rule

Change table sources or code first, regenerate JSON, run the full project check, update STATUS/DECISIONS/HANDOFF/PROVENANCE_STATUS when the gate changes, then commit.

# Provenance Status

This file tracks publication-relevant provenance **without pretending unresolved material is cleared**.

## Source layers

### Structured public sources

`data_edit/sources.csv` registers the source ids referenced by events, persons, exhibits and artifacts. The build pipeline rejects unknown ids.

A registered source is traceability metadata, not automatic proof that every interpretation is correct. Human review still decides whether a source supports the specific claim.

### Extracted game material

Source id `src_steam_longmarch_1934_1936` represents locally extracted third-party game text.

Policy:

- raw extraction: private/ignored only;
- public repository: short rewritten candidate entries only;
- game-only support: `certainty=low`;
- promotion above low certainty: add independent evidence and review the claim;
- do not republish long original game passages.

### Visual assets

`data_edit/visual_assets.csv` tracks image page, credit and license fields.

Current debt: some external rows use generic values such as `see file page`. That is **not** treated as verified license metadata.

Before a fully-cleared redistribution/commercial claim:
1. resolve the exact source file page;
2. record author/source institution;
3. record exact license/public-domain basis;
4. record required attribution;
5. replace or remove assets whose rights cannot be verified.

Project-authored screenshots marked as project assets are a separate category.

## Private research boundary

The following paths are intentionally excluded from public Git:

- `research_private/`
- `steam_text_dump/`
- generated test/browser artifacts

CI checks that private research directories have not accidentally become tracked files.

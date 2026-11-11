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

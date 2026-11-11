# Architecture

```mermaid
flowchart LR
  T[data_edit CSV tables] --> B[build_json_from_tables.py]
  B --> J[data/long_march_events.json]
  J --> M[Route map]
  J --> U[Digital museum]
  J --> I[Immersive museum]
  T --> A[Local admin/editor]
  R[research_private candidate material] --> X[Extraction/import tools]
  X --> T
```

## Evidence boundary

```mermaid
flowchart TB
  RAW[Raw third-party extraction] -->|private only| C[Candidate clues]
  C -->|rewrite + source ids + certainty| TABLE[Canonical tables]
  TABLE --> PUB[Public generated JSON]
  AUTH[Independent source review] --> TABLE

  IMG[External image] --> PROV[image page + credit + license]
  PROV --> PUB
```

The compiler guarantees reproducibility and reference integrity. It does not itself establish historical truth, copyright clearance, or exact geographic precision.

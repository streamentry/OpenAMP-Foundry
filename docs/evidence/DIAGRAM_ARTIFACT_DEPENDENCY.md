# Artifact Dependency Graph

Shows how artifacts depend on each other.

```mermaid
flowchart TD
  A[Candidate CSV] --> B[Ranked JSONL]
  A --> C[Evidence certs]
  B --> D[Batch report]
  B --> E[Run manifest]
  C --> F[Lab batch pack]
  F --> G[Lab results]
  G --> H[Calibration intake]
  H --> I[Gate verdict]
  I -->|pass| J[Weight proposal]
  I -->|fail| K[Blocked]
```

## Rules
- Artifacts higher in the graph are inputs.
- Arrows show the direction of data flow.
- Dotted lines indicate optional dependencies.
- The graph should be updated when new artifact types are added.

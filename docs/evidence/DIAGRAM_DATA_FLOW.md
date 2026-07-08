# Data Flow and Data Boundary Map

```mermaid
flowchart LR
  subgraph Input
    A[Candidate CSV]
    B[Reference CSV]
    C[Config YAML]
  end
  subgraph Pipeline
    D[score_candidates]
    E[rank_candidates]
    F[select_diverse]
  end
  subgraph Output
    G[Ranked JSONL]
    H[Evidence certs]
    I[Run manifest]
    J[Batch report]
  end
  A --> D
  B --> D
  C --> D
  D --> E
  E --> F
  F --> G
  D --> H
  D --> I
  E --> J
```

## Data Boundaries
- **Input boundary**: Candidate CSV, reference CSV, config YAML
- **Pipeline boundary**: `score_candidates` → `rank_candidates` → `select_diverse`
- **Output boundary**: JSONL, evidence certs, manifest, report
- **External boundary**: Lab results (returned by partners)

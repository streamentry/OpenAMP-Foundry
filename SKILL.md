# OpenAMP Foundry Agent Skill

## Overview

Start from the current truth source: `docs/METRICS_CURRENT.md`, then
`docs/ROADMAP.md`, then `AGENTS.md`. Treat computational scores as triage only.
Do not describe candidates as active, safe, therapeutic, or validated without
qualified lab evidence.

## Key Components

- `src/openamp_foundry/pipeline.py`: rank candidates and emit evidence.
- `src/openamp_foundry/scoring/`: activity, safety, hemolysis, novelty,
  synthesis, expert, and rich selectivity scorers.
- `src/openamp_foundry/selection/`: ensemble/expert ranking, diversity, pilot
  panel selection, and structural-class floors.
- `src/openamp_foundry/benchmark/` plus `scripts/benchmark_*.py`: benchmark
  honesty checks.
- `src/openamp_foundry/calibration/`: lab-result intake, gate, and proposal-only
  recalibration.

## Diagrams

### Flowchart

```mermaid
flowchart TD
  A["Candidate sequences"] --> B["Validate + feature extraction"]
  B --> C["Independent scorers"]
  C --> D["Ranking + diversity selection"]
  D --> E["Evidence certificates"]
  E --> F["Human review"]
  F --> G["Qualified external assay"]
  G --> H["Calibration intake + gate"]
```

### Component Diagram

```mermaid
flowchart LR
  Data["data"] --> Pipeline["pipeline"]
  Features["features"] --> Scoring["scoring"]
  Scoring --> Selection["selection"]
  Selection --> Evidence["evidence"]
  Evidence --> Reports["reports"]
  Reports --> Calibration["calibration"]
  Benchmark["benchmark"] --> Scoring
  Benchmark --> Selection
```

### Sequence Diagram

```mermaid
sequenceDiagram
  participant Agent
  participant CLI
  participant Scoring
  participant Selection
  participant Evidence
  Agent->>CLI: rank / pilot-panel
  CLI->>Scoring: compute raw scores
  CLI->>Selection: rank, diversify, optional class floor
  Selection-->>CLI: selected candidates
  CLI->>Evidence: write certificates
  Evidence-->>Agent: reviewable artifacts
```

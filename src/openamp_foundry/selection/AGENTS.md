# Selection Module

## Overview

Selection turns scored candidates into reviewable panels. It must preserve
scientific honesty: diversity or structural-class floors are panel-construction
guards, not biological proof and not scoring improvements.

## Key Components

- `pilot.py`: pilot-panel selection by priority, seed coverage, optional
  similarity filter, optional structural-class floor.
- `structural_class.py`: shared six-class heuristic used by both per-family
  benchmarking and pilot-panel floor logic.
- `diversity.py`: sequence diversity and family warnings.
- `pareto.py`: ranking helpers for ensemble/expert modes.
- `ranking_policy.py`: records why a ranking mode was used.

## Diagrams

### Flowchart

```mermaid
flowchart TD
  A["Scored candidates"] --> B["Add seed + pilot priority"]
  B --> C["Classify structural class"]
  C --> D{"Class floor enabled?"}
  D -->|Yes| E["Reserve top candidates per class"]
  D -->|No| F["Skip class floor"]
  E --> G["Ensure seed representatives"]
  F --> G
  G --> H["Fill remaining slots"]
  H --> I["Assign pilot ranks"]
```

### Component Diagram

```mermaid
flowchart LR
  Pilot["pilot.py"] --> Classifier["structural_class.py"]
  Pilot --> Novelty["scoring.novelty similarity"]
  Pilot --> Report["reports.pilot_panel"]
  Pareto["pareto.py"] --> Policy["ranking_policy.py"]
```

### Sequence Diagram

```mermaid
sequenceDiagram
  participant CLI
  participant Pilot
  participant Classifier
  participant Similarity
  CLI->>Pilot: select_pilot_panel(...)
  Pilot->>Classifier: classify_structural_class
  Pilot->>Similarity: reject near duplicates if configured
  Pilot-->>CLI: ranked panel with seed and structural_class
```

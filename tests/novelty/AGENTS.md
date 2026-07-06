# Novelty Tests

## Overview

This folder verifies novelty scoring behavior and novelty-pressure effects in
selection.

## Key Components

- `test_novelty.py`
- `test_novelty_pressure.py`

## Diagrams (Mermaid)

- Flowchart

```mermaid
flowchart TD
  NoveltyCode["novelty scoring + novelty filters"] --> NoveltyTests["tests/novelty/*"]
  NoveltyTests --> Verdict["scoring and pressure proof"]
```

- Component Diagram

```mermaid
flowchart LR
  NoveltyTests["tests/novelty"] --> Scoring["src/openamp_foundry/scoring/novelty.py"]
  NoveltyTests --> Pipeline["src/openamp_foundry/pipeline.py"]
  NoveltyTests --> ExampleData["examples/benchmark + examples/known_reference"]
```

- Sequence Diagram

```mermaid
sequenceDiagram
  participant Pytest
  participant Test
  participant Novelty
  participant Pipeline
  Pytest->>Test: run novelty tests
  Test->>Novelty: compute novelty score
  Test->>Pipeline: run ranking pipeline when needed
  Novelty-->>Test: similarity and nearest reference
  Pipeline-->>Test: selection under novelty pressure
```

# Wave Tests

## Overview

This folder verifies wave-program specific rules and contracts, especially
gates that decide whether a wave panel is structurally safe to interpret.

## Key Components

- `test_wave0_5_gates.py`

## Diagrams (Mermaid)

- Flowchart

```mermaid
flowchart TD
  WaveScripts["scripts/waves/*"] --> WaveArtifacts["wave outputs"]
  WaveArtifacts --> WaveTests["tests/waves/*"]
  WaveTests --> Verdict["gate pass/fail proof"]
```

- Component Diagram

```mermaid
flowchart LR
  WaveTests["tests/waves"] --> Gates["src/openamp_foundry/gates"]
  WaveTests --> Outputs["wave panel / consensus / novelty CSVs"]
```

- Sequence Diagram

```mermaid
sequenceDiagram
  participant Pytest
  participant Test
  participant Gate
  Pytest->>Test: run wave gate test
  Test->>Gate: evaluate artifact contract
  Gate-->>Test: PASS/FAIL result
```

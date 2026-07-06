# Release Tests

## Overview

This folder verifies release-facing artifact operations and reproducibility
reporting.

## Key Components

- `test_regenerate_all.py`
- `test_full_reproducibility_report.py`

## Diagrams (Mermaid)

- Flowchart

```mermaid
flowchart TD
  ReleaseScripts["scripts/release/*"] --> ReleaseTests["tests/release/*"]
  ReleaseTests --> Verdict["artifact and report proof"]
```

- Component Diagram

```mermaid
flowchart LR
  ReleaseTests["tests/release"] --> ReleaseScripts["scripts/release"]
  ReleaseScripts --> Outputs["outputs/*"]
  ReleaseScripts --> Git["git state"]
```

- Sequence Diagram

```mermaid
sequenceDiagram
  participant Pytest
  participant Test
  participant Script
  Pytest->>Test: run release test
  Test->>Script: invoke function or CLI
  Script-->>Test: artifact or report
```

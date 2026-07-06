# Lab Tests

## Overview

This folder verifies the lab handoff lane: pack creation, returned-result
validation, and batch pass/fail evaluation.

## Key Components

- `test_lab_batch_pack.py`
- `test_validate_lab_data_return.py`
- `test_wave1_pass_fail.py`

## Diagrams (Mermaid)

- Flowchart

```mermaid
flowchart TD
  LabScripts["scripts/lab/*"] --> Tests["tests/lab/*"]
  Tests --> Verdict["CLI + behavior proof"]
```

- Component Diagram

```mermaid
flowchart LR
  LabTests["tests/lab"] --> LabScripts["scripts/lab"]
  LabScripts --> Schema["schemas/lab_result.schema.json"]
  LabScripts --> Docs["lab handoff docs"]
```

- Sequence Diagram

```mermaid
sequenceDiagram
  participant Pytest
  participant Test
  participant Script
  participant Artifact
  Pytest->>Test: run lab lane test
  Test->>Script: invoke function or CLI
  Script->>Artifact: read/write pack or verdict
  Artifact-->>Test: verification state
```

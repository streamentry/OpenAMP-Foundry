# External Tests

## Overview

This folder verifies the external prediction workflow surfaces that generate
submission artifacts and reviewer-facing checklists.

## Key Components

- `test_external_predict.py`

## Diagrams (Mermaid)

- Flowchart

```mermaid
flowchart TD
  Reports["external prediction reports"] --> ExternalTests["tests/external/*"]
  ExternalTests --> Verdict["artifact-format proof"]
```

- Component Diagram

```mermaid
flowchart LR
  ExternalTests["tests/external"] --> Reports["src/openamp_foundry/reports/external_predict.py"]
  ExternalTests --> Outputs["FASTA / checklist / confident panel outputs"]
```

- Sequence Diagram

```mermaid
sequenceDiagram
  participant Pytest
  participant Test
  participant Report
  Pytest->>Test: run external workflow tests
  Test->>Report: generate FASTA / checklist / panel
  Report-->>Test: rendered artifact
```

# Release Scripts

## Overview

This folder is the canonical home for release-facing artifact operations:
demo generation, certificate validation, output regeneration, and full
reproducibility reporting.

## Key Components

- `run_demo.py`
- `generate_evidence.py`
- `validate_certificate.py`
- `regenerate_all.py`
- `full_reproducibility_report.py`

## Diagrams (Mermaid)

- Flowchart

```mermaid
flowchart TD
  Demo["run_demo.py"] --> Evidence["generate_evidence.py"]
  Evidence --> Validate["validate_certificate.py"]
  Validate --> Regen["regenerate_all.py"]
  Regen --> Report["full_reproducibility_report.py"]
```

- Component Diagram

```mermaid
flowchart LR
  ReleaseScripts["scripts/release"] --> Outputs["outputs/*"]
  ReleaseScripts --> Schemas["schemas/*"]
  ReleaseScripts --> Docs["reproducibility docs"]
  Tests["tests/release"] --> ReleaseScripts
```

- Sequence Diagram

```mermaid
sequenceDiagram
  participant Maintainer
  participant Demo
  participant Regen
  participant Report
  Maintainer->>Demo: generate demo artifacts
  Maintainer->>Regen: regenerate tracked outputs
  Regen->>Report: summarize reproducibility state
  Report-->>Maintainer: release-facing evidence
```

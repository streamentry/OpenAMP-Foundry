# Calibration

## Overview

This package joins computational panel predictions to validated result
records, reports descriptive cohort metrics, and evaluates a human-gated
recalibration policy.

## Key Components

- `intake.py`: result join and input-validation status.
- `recalibration_gate.py`: fail-closed policy verdict; never applies weights.

## Diagrams (Mermaid)

```mermaid
flowchart TD
  Panel["Pilot panel"] --> Intake["Calibration intake"]
  Results["Result JSON directory"] --> Intake
  Intake -->|invalid files| Block["Blocked input report"]
  Intake -->|clean input| Gate["Recalibration gate"]
  Gate --> Human["Human decision record"]
```

```mermaid
sequenceDiagram
  participant CLI
  participant Intake
  participant Gate
  CLI->>Intake: build report
  Intake-->>CLI: valid rows + invalid file provenance
  CLI->>Gate: evaluate only after input check
  Gate-->>CLI: may_recalibrate or fail-closed verdict
```

Invalid result files are excluded from metrics but remain in the report and
force the recalibration verdict to false. No result is treated as biological
proof.

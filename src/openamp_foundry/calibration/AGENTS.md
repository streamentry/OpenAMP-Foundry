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
  Results["Validated result JSON directory"] --> Intake
  Missing["Missing/non-directory path"] --> PathBlock["Input path error"]
  Intake -->|invalid files| Block["Blocked input report"]
  Intake -->|duplicate identities| IdentityBlock["Blocked input-integrity report"]
  Intake -->|clean input| Gate["Recalibration gate"]
  Gate --> Human["Human decision record"]
```

```mermaid
sequenceDiagram
  participant CLI
  participant Intake
  participant Gate
  CLI->>Intake: build report
  Intake-->>CLI: valid rows + invalid/duplicate identity provenance
  CLI->>Gate: evaluate only after input check
  Gate-->>CLI: may_recalibrate or fail-closed verdict
```

Invalid result files are excluded from metrics but remain in the report and
force the recalibration verdict to false. No result is treated as biological
proof. Missing or non-directory result paths fail before report generation;
only an existing empty directory represents a known no-results state. Duplicate
result IDs and duplicate panel candidate IDs likewise block clean intake because
they make the evidence identity ambiguous. Control-failed assay observations
remain in the audit report but are excluded from per-assay actual predicates and
cohort metrics, while still blocking recalibration.

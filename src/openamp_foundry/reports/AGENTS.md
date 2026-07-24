# Reports

## Overview

Report builders turn validated computational or experimental records into
review artifacts without strengthening scientific claims.

## Key Components

- `lab_result_report.py`: result counts, candidate rollups, controls, and input
  validation blockers. Markdown and JSON distinguish control-passing outcome
  counts from raw audit observations, including failed-control qualitative
  results. They also show declared raw-data hash coverage without calling it
  independently verified.
- `recalibration_report.py`: proposal/gate summaries; proposals are not applied.

## Diagrams (Mermaid)

```mermaid
flowchart LR
  Records["Validated records"] --> Report["JSON + Markdown report"]
  Invalid["Invalid-file provenance"] --> Report
  Report --> Usable["Control-passing outcome fields"]
  Report --> Raw["Raw observations + failure IDs"]
  Report --> Provenance["Declared raw-data hash coverage"]
  Report --> Verification["Optional raw-file verification"]
  Verification -->|mismatch/missing/path escape| Block["Blocked report status"]
  Report --> Review["Qualified review"]
```

```mermaid
sequenceDiagram
  participant Caller
  participant Builder
  Caller->>Builder: build report(directory, optional raw-data directory)
  Builder-->>Caller: descriptive report + blockers
  Caller->>Caller: stop on input-validation blocker
```

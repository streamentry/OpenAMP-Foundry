# Evidence Documentation

## Overview

Evidence docs define what artifacts can support and where claims must stop.
Gate workflows are structural review controls, never biological proof.

## Key Components

- `METRICS_CURRENT.md`: current measured evidence and limitations.
- `PROOF_LADDER.md`: maximum claim strength by evidence level.
- AARG-: checks presence of reproducibility artifacts before certification.
- Lab-result intake blockers are evidence-completeness signals, not assay
  validation; invalid files must remain visible in reports and gates.
- Control-failed assay observations remain visible for audit but are excluded
  from per-assay calibration predicates, cohort metrics, and interpretable
  candidate outcome flags; raw fields remain available for audit and they cannot
  support recalibration.

## Diagrams (Mermaid)

```mermaid
flowchart LR
  Artifacts["Evidence artifacts"] --> Gate["AARG- / other gates"]
  Gate --> Review["Qualified review"]
  Gate -.->|never proves biology| Claim["Claim boundary"]
```

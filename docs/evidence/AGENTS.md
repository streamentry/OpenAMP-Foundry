# Evidence Documentation

## Overview

Evidence docs define what artifacts can support and where claims must stop.
Gate workflows are structural review controls, never biological proof.

## Key Components

- `METRICS_CURRENT.md`: current measured evidence and limitations.
- `PROOF_LADDER.md`: maximum claim strength by evidence level.
- AARG-: checks presence of reproducibility artifacts before certification.

## Diagrams (Mermaid)

```mermaid
flowchart LR
  Artifacts["Evidence artifacts"] --> Gate["AARG- / other gates"]
  Gate --> Review["Qualified review"]
  Gate -.->|never proves biology| Claim["Claim boundary"]
```

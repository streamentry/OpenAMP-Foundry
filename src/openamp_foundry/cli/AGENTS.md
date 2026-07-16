# CLI Commands

## Overview

The CLI exposes safe, deterministic review and evidence checks. Commands must
preserve dry-lab claim boundaries and fail closed when a gate is incomplete.

## Key Components

- `main.py`: parser and command dispatch.
- `commands/reports.py`: structured evidence and gate handlers.
- `phase-aa-reproducibility-gate-check`: runs the AARG- presence gate; only
  `reproducibility_verified` returns exit code 0.

## Diagrams (Mermaid)

```mermaid
flowchart LR
  JSON["Gate JSON"] --> Parser["CLI parser"] --> Handler["Evidence handler"]
  Handler --> AARG["AARG- gate"] --> Output["Text or JSON + exit status"]
```

```mermaid
sequenceDiagram
  participant User
  participant CLI
  participant Gate as AARG-
  User->>CLI: phase-aa-reproducibility-gate-check
  CLI->>Gate: rebuild typed gate from artifact IDs
  Gate-->>CLI: verified, partial, or not established
  CLI-->>User: report and fail-closed status
```

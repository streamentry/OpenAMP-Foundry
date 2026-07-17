# CLI Commands

## Overview

Handlers expose deterministic report and gate workflows with explicit exit
codes. They do not authorize release or apply recalibration.

## Key Components

- `reports.py`: lab-result and calibration intake command handlers.
- `main.py`: parser and dispatch in the parent directory.

## Diagrams (Mermaid)

```mermaid
flowchart TD
  Args["CLI arguments"] --> Intake["Build intake report"]
  Intake --> PathError["Missing/non-directory path: error, exit 2"]
  Intake --> Clean["Input validated"]
  Intake --> Blocked["Invalid files: status blocked, exit 3"]
  Clean --> Output["Write report"]
  Blocked --> Output
```

```mermaid
sequenceDiagram
  participant User
  participant CLI
  participant Loader
  User->>CLI: calibration-intake
  CLI->>Loader: load with errors
  Loader-->>CLI: records + file errors
  CLI-->>User: report or input-path error with explicit exit status
```

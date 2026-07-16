# Calibration Tests

## Overview

This folder verifies the calibration subsystem: intake, policy versioning,
gate behavior, and the synthetic end-to-end calibration loop.

## Key Components

- `test_bump_recalibration_policy.py`
- `test_calibration_e2e.py`
- `test_calibration_intake.py`
- `test_policy_version.py`
- `test_recalibration_gate.py`
- Invalid result files are retained as intake provenance and must block both
  the intake CLI and recalibration gate.

## Diagrams (Mermaid)

- Flowchart

```mermaid
flowchart TD
  CalScripts["scripts/calibration/*"] --> CalTests["tests/calibration/*"]
  CalPkg["src/openamp_foundry/calibration"] --> CalTests
  CalTests --> Verdict["behavior and policy proof"]
```

- Component Diagram

```mermaid
flowchart LR
  CalTests["tests/calibration"] --> CalScripts["scripts/calibration"]
  CalTests --> CalPkg["src/openamp_foundry/calibration"]
  CalPkg --> Policy["configs/recalibration_policy.yaml"]
```

- Sequence Diagram

```mermaid
sequenceDiagram
  participant Pytest
  participant Test
  participant Script
  participant CalPkg
  Pytest->>Test: run calibration test
  Test->>Script: invoke CLI when needed
  Test->>CalPkg: invoke package APIs
  Script->>CalPkg: execute workflow
  CalPkg-->>Test: artifacts and verdicts
```

- Input-validation state machine

```mermaid
stateDiagram-v2
  [*] --> LoadResults
  LoadResults --> InputValidated: all JSON files valid
  LoadResults --> InputBlocked: one or more invalid files
  InputBlocked --> [*]: report written, exit 3, no recalibration
  InputValidated --> Gate: evaluate policy
  Gate --> [*]: human-reviewed verdict
```

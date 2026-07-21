# CLI Integration Tests

## Overview

Integration tests exercise the public command surface through `cli.main.main`.
They verify exit codes and serialized output, not biological validity.

## Key Components

- `test_cli.py`: command behavior and gate status coverage.
- `test_cli_help_coverage.py`: parser discoverability and `--help` coverage.
- Lab-result report tests must assert invalid-file blockers are visible and
  return exit code `3` rather than appearing successful.
- Lab-result report tests must keep raw qualitative observations auditable while
  asserting failed-control observations are absent from usable outcome counts.
- Scientific-review readiness tests must assert that only
  `ready_for_external_review` returns `0`; incomplete, conditional, safety,
  and malformed inputs return `3`.

## Diagrams (Mermaid)

```mermaid
flowchart LR
  Test["Integration test"] --> Main["cli.main.main"] --> Gate["Evidence gate"]
  Gate --> Assert["Output + exit assertions"]
```

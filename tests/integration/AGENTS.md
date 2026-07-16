# CLI Integration Tests

## Overview

Integration tests exercise the public command surface through `cli.main.main`.
They verify exit codes and serialized output, not biological validity.

## Key Components

- `test_cli.py`: command behavior and gate status coverage.
- `test_cli_help_coverage.py`: parser discoverability and `--help` coverage.

## Diagrams (Mermaid)

```mermaid
flowchart LR
  Test["Integration test"] --> Main["cli.main.main"] --> Gate["Evidence gate"]
  Gate --> Assert["Output + exit assertions"]
```

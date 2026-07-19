# Data Tests

## Overview

Tests protect schema validation, ordering, summaries, and retained invalid-file
provenance for result ingestion.

## Key Components

- `test_lab_results.py`: loader, summary, and missing/non-directory path
  behavior, including the boundary between raw and control-passing outcomes.

## Diagrams (Mermaid)

```mermaid
flowchart LR
  Fixture["Valid + invalid fixtures"] --> Loader["Data loader"]
  Loader --> Assertions["Records, errors, ordering"]
  Loader --> PathAssertions["Path errors fail closed"]
```

```mermaid
sequenceDiagram
  participant Test
  participant Loader
  Test->>Loader: load_lab_results_dir_with_errors
  Loader-->>Test: valid records + named failures
  Test->>Test: assert no silent omission
```

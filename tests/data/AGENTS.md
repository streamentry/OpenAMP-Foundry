# Data Tests

## Overview

Tests protect schema validation, ordering, summaries, and retained invalid-file
provenance for result ingestion.

## Key Components

- `test_lab_results.py`: loader and summary behavior.

## Diagrams (Mermaid)

```mermaid
flowchart LR
  Fixture["Valid + invalid fixtures"] --> Loader["Data loader"]
  Loader --> Assertions["Records, errors, ordering"]
```

```mermaid
sequenceDiagram
  participant Test
  participant Loader
  Test->>Loader: load_lab_results_dir_with_errors
  Loader-->>Test: valid records + named failures
  Test->>Test: assert no silent omission
```

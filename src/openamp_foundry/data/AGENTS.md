# Data Loading

## Overview

This package owns candidate and lab-result loading. Lab-result ingestion is
descriptive evidence plumbing, not biological validation.

## Key Components

- `lab_results.py`: input-path validation, schema validation, structured
  invalid-file provenance, and candidate-level summaries.
- `__init__.py`: stable public loader exports.

## Diagrams (Mermaid)

```mermaid
flowchart LR
  Files["Lab result JSON files"] --> Validate["Schema validation"]
  Validate --> Valid["Validated results"]
  Validate --> Errors["Structured file errors"]
  Validate --> PathError["Missing/non-directory path: fail closed"]
  Valid --> Summary["Descriptive summaries"]
```

```mermaid
sequenceDiagram
  participant Caller
  participant Loader
  participant Schema
  Caller->>Loader: load_lab_results_dir_with_errors
  Loader->>Schema: validate each JSON file
  Schema-->>Loader: valid record or file error
  Loader-->>Caller: sorted records + retained errors
```

Legacy `load_lab_results_dir` keeps warning-compatible behavior. Review and
calibration workflows must use the structured loader. All directory loaders
reject missing or non-directory paths; an existing empty directory remains a
valid, explicit no-results state.

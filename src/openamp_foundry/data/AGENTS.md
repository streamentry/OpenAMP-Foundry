# Data Loading

## Overview

This package owns candidate and lab-result loading. Lab-result ingestion is
descriptive evidence plumbing, not biological validation.

## Key Components

- `lab_results.py`: input-path validation, schema validation, structured
  invalid-file provenance, and candidate-level summaries. Rollups expose raw
  observations separately from control-passing outcome flags and counts;
  batch-level qualitative summaries follow the same raw-versus-usable split.
- `__init__.py`: stable public loader exports.

## Diagrams (Mermaid)

```mermaid
flowchart LR
  Files["Lab result JSON files"] --> Validate["Schema validation"]
  Validate --> Valid["Validated results"]
  Validate --> Errors["Structured file errors"]
  Validate --> PathError["Missing/non-directory path: fail closed"]
  Valid --> Controls{"Both controls passed?"}
  Controls --> Usable["Interpretable outcome flags/counts"]
  Controls --> Raw["Raw audit fields + failure IDs"]
  Usable --> Summary["Usable descriptive summaries"]
  Raw --> Audit["Raw audit summaries"]
```

```mermaid
sequenceDiagram
  participant Caller
  participant Loader
  participant Schema
  Caller->>Loader: load_lab_results_dir_with_errors
  Loader->>Schema: validate each JSON file
  Schema-->>Loader: valid record or file error
  Loader->>Loader: separate control-passing from failed-control observations
  Loader-->>Caller: sorted records + retained errors
```

Legacy `load_lab_results_dir` keeps warning-compatible behavior. Review and
calibration workflows must use the structured loader. All directory loaders
reject missing or non-directory paths; an existing empty directory remains a
valid, explicit no-results state. Failed-control results remain auditable but do
not populate interpretable candidate outcome flags or numeric counts.

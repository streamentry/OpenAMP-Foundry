# Engineering Documentation

## Overview

Engineering docs describe architecture and reproducibility interfaces without
turning artifact presence into scientific validation.

## Key Components

- `ARCHITECTURE.md`: system, trust architecture, data flow, and gates.
- `RUN_MANIFEST_STANDARD.md`: provenance fields for reproducible runs.
- `SCHEMA_REGISTRY.md`: artifact prefixes and compatibility references.
- Result ingestion retains schema-invalid files as structured provenance;
  calibration and reporting paths fail closed on those files.
- Candidate rollups keep failed-control observations auditable without exposing
  them as interpretable outcome flags or counts. Batch-level result summaries
  expose raw and control-passing qualitative counts separately.
- `ARCHITECTURE.md` records the Phase R SRG- CLI/Make surface; only a fully
  ready verdict passes and the checked-in example remains blocked.
- `ARCHITECTURE.md` also records the Phase Z ZAG- CLI/Make surface; all four
  per-family accountability artifacts are required, but presence is not
  benchmark validation.
- `ARCHITECTURE.md` also records the Phase Y YAG- CLI/Make surface; all four
  baseline-accountability artifacts are required, but presence is not evidence
  that the pipeline beats cheap baselines.
- `ARCHITECTURE.md` records that lab-result `assay_date` values undergo
  canonical calendar validation before they can enter sorted reports or
  calibration metrics.

## Diagrams (Mermaid)

```mermaid
flowchart LR
  Run["Pipeline run"] --> Manifest["Run manifest"] --> AARG["AARG- gate"]
  AARG --> Review["Reproducibility review"]
```

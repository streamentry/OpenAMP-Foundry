# Scripts

## Overview

`scripts/` contains human-invoked repository utilities. Canonical benchmark
entrypoints live in `scripts/benchmarks/`. Flat files at `scripts/*.py` may
exist as compatibility shims when historical docs or old commands still point
there.

## Key Components

- `benchmarks/`: benchmark and baseline entrypoints.
- `calibration/`: policy bump and synthetic calibration-loop entrypoints.
- `external/`: predictor submission, normalization, consensus, and sponsor handoff.
- `lab/`: lab handoff, validation, and pass/fail entrypoints.
- `novelty/`: novelty DB refresh, audit, and patent-risk entrypoints.
- `release/`: demo, evidence, validation, regeneration, and reproducibility entrypoints.
- `research/`: exploratory generation, screening, restoration, and dataset-expansion scripts.
- `waves/`: wave-program generation, novelty audit, and panel-selection entrypoints.
- `external_validators/`: browser and Node-driven external validation helpers.
- top-level `*.py`: transitional wrappers or non-benchmark operational scripts.

## Diagrams (Mermaid)

- Flowchart

```mermaid
flowchart TD
  User["Contributor or CI"] --> Script["scripts/*"]
  Script --> Bench["scripts/benchmarks/*"]
  Script --> Ops["Operational utility"]
  Bench --> Package["src/openamp_foundry/benchmark"]
  Ops --> Package
```

- Component Diagram

```mermaid
flowchart LR
  Makefile --> Scripts
  CLI --> Scripts
  Scripts --> BenchmarkPkg["benchmark package"]
  Scripts --> ReportsPkg["reports / qc / calibration packages"]
  External["external_validators"] --> Scripts
```

- Sequence Diagram

```mermaid
sequenceDiagram
  participant User
  participant Wrapper as Flat wrapper
  participant Canon as Canonical script
  participant Lib as src/openamp_foundry/*
  User->>Wrapper: run historical command
  Wrapper->>Canon: delegate main()
  Canon->>Lib: execute benchmark or utility logic
  Lib-->>User: artifact or exit code
```

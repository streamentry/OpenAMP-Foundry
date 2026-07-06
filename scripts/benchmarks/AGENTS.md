# Benchmark Scripts

## Overview

This folder is the canonical home for benchmark, baseline, and benchmark-data
curation entrypoints. If a benchmark path in docs or CI disagrees with this
folder, this folder wins and compatibility wrappers should be updated.

## Key Components

- `benchmark_*.py`: benchmark runners and regression gates.
- `baseline_trivial.py`: cheapest-enemy benchmark.
- `curate_500_amp_benchmark.py`: benchmark dataset curation.
- `expand_benchmark.py`: benchmark expansion utility.

## Diagrams (Mermaid)

- Flowchart

```mermaid
flowchart TD
  Inputs["Toy benchmark inputs"] --> Runner["Benchmark script"]
  Runner --> Metrics["JSON or console metrics"]
  Metrics --> Docs["docs/METRICS_CURRENT.md"]
  Metrics --> Gates["CI / reviewer gate"]
```

- Component Diagram

```mermaid
flowchart LR
  BenchScripts["scripts/benchmarks"] --> BenchPkg["src/openamp_foundry/benchmark"]
  BenchScripts --> Features["src/openamp_foundry/features"]
  BenchScripts --> Outputs["outputs/*.json"]
  Tests["tests/benchmarks"] --> BenchScripts
```

- Sequence Diagram

```mermaid
sequenceDiagram
  participant Dev as Contributor
  participant Script as Benchmark script
  participant Code as Benchmark code
  participant Output as Metrics artifact
  Dev->>Script: run benchmark
  Script->>Code: compute metrics
  Code-->>Script: results
  Script->>Output: write JSON/report
  Output-->>Dev: reviewable evidence
```

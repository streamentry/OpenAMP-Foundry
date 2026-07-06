# Benchmark Tests

## Overview

This folder verifies benchmark scripts, benchmark invariants, and benchmark
reporting. Use it when a change could alter benchmark truth, baseline gates, or
benchmark CLI behavior.

## Key Components

- `test_benchmark_*.py`: benchmark-runner and gate coverage.
- `test_charge_matched_benchmark.py`: charge-matched honesty checks.
- `test_cluster_split_benchmark.py`: leakage-resistant cluster benchmark checks.
- `test_selectivity_benchmark.py`: within-AMP benchmark checks.
- `test_triage_benchmark.py`: triage benchmark checks.

## Diagrams (Mermaid)

- Flowchart

```mermaid
flowchart TD
  Script["scripts/benchmarks/*"] --> Test["tests/benchmarks/*"]
  Test --> Regression["regression verdict"]
  Regression --> CI["CI or local review"]
```

- Component Diagram

```mermaid
flowchart LR
  BenchTests["tests/benchmarks"] --> BenchScripts["scripts/benchmarks"]
  BenchScripts --> BenchPkg["src/openamp_foundry/benchmark"]
  BenchScripts --> Outputs["outputs/metrics_snapshot.json"]
```

- Sequence Diagram

```mermaid
sequenceDiagram
  participant Pytest
  participant Test
  participant Script
  participant BenchCode
  Pytest->>Test: run case
  Test->>Script: invoke CLI or function
  Script->>BenchCode: compute benchmark
  BenchCode-->>Test: metric or exit code
```

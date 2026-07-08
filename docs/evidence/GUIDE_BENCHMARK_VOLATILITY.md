# Benchmark Volatility Report

Measures how much benchmark results vary across runs.

## Sources of Volatility
| Source | Impact | Mitigation |
|--------|:------:|------------|
| Random seed | Low | Deterministic seeds in all scripts |
| Dataset ordering | Low | Stable sorting in all loaders |
| System load | Negligible | No parallel processing dependencies |

## Measurement
Benchmark volatility is measured by running the same benchmark 3 times
and recording the range of AUROC values.

## Current State
All benchmarks use fixed random seeds. Volatility is expected to be < 0.005 AUROC.
If volatility exceeds 0.01, investigate the cause.

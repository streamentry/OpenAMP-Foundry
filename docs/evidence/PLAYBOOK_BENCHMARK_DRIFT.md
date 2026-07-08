# Benchmark Drift Playbook

How to detect and respond to benchmark drift.

## Detection
- Run `make bench-gate` to check regression gates.
- Compare current AUROC to METRICS_CURRENT.md values.
- Check per-family benchmarks for class-specific drift.

## Response
| Drift Magnitude | Action |
|:---------------:|--------|
| < 0.01 | Document, no action needed |
| 0.01 - 0.02 | Investigate, document |
| > 0.02 | Block release, fix required |

## Prevention
- Run benchmarks after every scoring change.
- Gate benchmark regressions in CI.
- Maintain benchmark history in METRICS_CURRENT.md.

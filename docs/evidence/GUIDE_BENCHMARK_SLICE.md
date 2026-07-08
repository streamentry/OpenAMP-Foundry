# Benchmark Slice Explanation

A benchmark slice measures performance on a specific subset of data.

## Why Slice
- Overall AUROC can hide poor performance on important subgroups.
- Slicing reveals which candidate classes the pipeline handles well or poorly.

## Current Slices
| Slice | Description | AUROC | Finding |
|-------|-------------|:-----:|---------|
| Highly cationic | Charge >= 4.0 | 0.958 | Well handled |
| Proline-rich | Pro fraction >= 15% | 0.586 | Poorly handled |
| Cysteine-rich | >= 2 Cys | 0.723 | Moderately handled |
| Short | <= 12 AA | 0.610 | Poorly handled |

## Related
- `docs/evidence/METRICS_CURRENT.md` — per-family benchmark table
- `scripts/benchmark_per_family.py` — how slices are computed

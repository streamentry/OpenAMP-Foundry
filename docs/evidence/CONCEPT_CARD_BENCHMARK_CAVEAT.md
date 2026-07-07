# Benchmark Caveat — Concept Card

Every benchmark has limitations. A benchmark caveat documents what the
benchmark does NOT prove.

## Common Caveats

| Caveat | Example |
|--------|---------|
| Charge-inflated | AMP-vs-decoy AUROC 0.7792 is partially charge-driven |
| Composition bias | Most features are composition-only, not order-aware |
| Small-n | Confidence intervals may be wide |
| Synthetic negatives | Decoys are not biologically validated |
| No wet-lab confirmation | All scores are computational predictions |

## Rules

- Every benchmark result must state its caveats.
- Caveats cannot be hidden in supplementary materials.
- A benchmark without caveats is incomplete.

## Related

- `docs/evidence/BENCHMARK_GOVERNANCE.md` — benchmark policies
- `docs/evidence/METRICS_CURRENT.md` — current results with caveats
- `docs/evidence/LIMITATIONS_OVERVIEW.md` — full limitations list

# Baseline Failure Gallery

Cases where simple baselines outperform or match the pipeline.

| Baseline | Task | Performance | Pipeline Performance | Delta |
|----------|:----:|:-----------:|:-------------------:|:-----:|
| Charge density | AMP-vs-decoy | AUROC 0.8166 | AUROC 0.7792 | −0.0374 |
| Helix propensity | Hemolysis detection | AUROC 0.6489 | Best sim 0.6458 | −0.0031 |
| Selectivity proxy | Hemolysis detection | AUROC 0.3905 | Sim ratio 0.3615 | −0.0290 |

## What This Means
- The pipeline's primary discriminative signal is charge, not sophisticated scoring.
- Simulation modules do not improve over cheap heuristics (0/4 signals).
- Multi-objective optimization (safety, novelty) trades off raw discrimination.

## Related
- `scripts/baseline_trivial.py` — easy baseline benchmark
- `scripts/benchmark_simulation_baselines.py` — simulation cheap-baseline comparison

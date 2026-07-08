# Cheap Baseline Registry for Benchmark Reports

Registry of cheap baselines used for comparison.

| Baseline | Task | Metric | Current Best | Reference |
|----------|:----:|:------:|:------------:|-----------|
| Charge density | AMP-vs-decoy | AUROC | 0.8166 | baseline_trivial.py |
| Selectivity proxy | Hemolysis detection | Det. AUROC | 0.5744 | features/physchem.py |
| Helix propensity | Structure prediction | Raw Pα | 0.6489 | features/physchem.py |
| Length | AMP-vs-decoy | AUROC | 0.5000 | baseline_trivial.py |

## Rules
- Every benchmark should compare against at least one cheap baseline.
- Cheap baselines must be simpler than the method being evaluated.
- Baseline performance must be documented in the benchmark report.
- If a method doesn't beat its cheap baseline, it's marked experimental.

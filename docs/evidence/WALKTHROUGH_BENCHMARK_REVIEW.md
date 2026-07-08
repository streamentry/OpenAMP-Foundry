# Guided Walkthrough: Benchmark Report Review

## Scenario
You need to review a benchmark report to assess pipeline health.

## Steps
1. Run: `make bench-500`
2. Check the AUROC value in `outputs/validate_scoring_500.json`.
3. Compare with the expected value in METRICS_CURRENT.md.
4. If AUROC dropped > 0.02, check for recent regressions.
5. Run: `make bench-gate` — this checks all regression gates.
6. Review the simulation ablation results in `outputs/simulation_ablation.json`.
7. Check that simulation verdict remains NO_IMPROVEMENT.

# Metric Confidence Interval Helper

Helper for computing and interpreting confidence intervals.

## Usage
```python
from openamp_foundry.benchmark.retrospective import bootstrap_ci

# Get bootstrap CI for AUROC
ci_lo, ci_hi = bootstrap_ci(scores_pos, scores_neg, n_bootstrap=2000)
```

## Interpretation
- 95% CI means the true value falls in this range ~95% of the time.
- Narrow CI = more precise estimate.
- If CI includes 0.5, the result is not statistically significant.

## Rules
- All benchmark AUROCs should report a bootstrap CI.
- Use n_bootstrap=2000 for standard benchmarks.
- Cluster-aware bootstrap should be used when near-duplicates exist.
- CIs should be reported as `CI_95: [lower, upper]` in benchmark outputs.

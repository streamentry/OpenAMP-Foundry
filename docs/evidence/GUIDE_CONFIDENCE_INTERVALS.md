# Confidence Interval Interpretation Guide

How to read and interpret confidence intervals in benchmark results.

## What a CI Is
A confidence interval estimates the range where the true value likely falls.
A 95% CI means that if the experiment were repeated 100 times, the true value
would fall within the interval ~95 times.

## How to Read
- Narrow CI = more precise estimate (more data or less variability).
- Wide CI = less precise estimate (less data or more variability).
- If the CI includes 0.5, the result is not statistically significant.

## Examples
| Metric | Value | 95% CI | Interpretation |
|--------|-------|--------|----------------|
| AUROC | 0.7792 | 0.7505–0.8065 | Strong signal (CI above 0.5) |
| Charge density AUROC | 0.8166 | — | Strong trivial baseline |
| Helix_weight detection | 0.6458 | — | Moderate signal |

## Related
- All CIs are bootstrap-based (n=2000 resamples).
- Cluster-aware CIs account for near-duplicate inflation.

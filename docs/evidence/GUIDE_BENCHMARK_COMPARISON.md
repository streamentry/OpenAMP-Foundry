# Benchmark Result Comparison Helper

Helper for comparing benchmark results across runs.

## Usage
```python
# Compare two benchmark runs
delta = current_auroc - baseline_auroc
if delta > 0.02:
    print("IMPROVEMENT")
elif delta < -0.02:
    print("REGRESSION")
else:
    print("NO_SIGNIFICANT_CHANGE")
```

## Thresholds
| Delta | Interpretation | Action |
|:-----:|:--------------|--------|
| > 0.02 | Improvement | Document and proceed |
| -0.02 to 0.02 | No significant change | No action needed |
| < -0.02 | Regression | Investigate and fix |

## Rules
- Compare against the committed baseline, not the previous run.
- Report delta in benchmark outputs.
- If delta is negative, check for recent changes that could explain it.
- If delta is positive, verify the improvement is not due to data leakage.

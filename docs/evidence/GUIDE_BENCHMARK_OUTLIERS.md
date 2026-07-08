# Benchmark Outlier Analysis Report

How to identify and handle outlier results in benchmarks.

## Identifying Outliers
- Per-family AUROC that differs from the overall AUROC by > 0.20.
- Individual candidates that score far outside their family's range.
- Benchmarks where the CI width is > 2x the average.

## Examples
| Class | Overall AUROC | Per-family AUROC | Delta | Verdict |
|-------|:-------------:|:----------------:|:-----:|:--------|
| highly_cationic | 0.779 | 0.958 | +0.179 | Overperforms |
| proline_rich | 0.779 | 0.586 | -0.193 | Underperforms |

## Response
- Outliers should be investigated and documented.
- If an outlier has a known cause, document it in the benchmark card.
- If an outlier cannot be explained, flag it for investigation.
- Outliers may indicate dataset bias or model blind spots.

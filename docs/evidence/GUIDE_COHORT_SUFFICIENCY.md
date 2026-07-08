# Calibration Cohort Sufficiency Explainer

How cohort size affects calibration reliability.

## Minimum Cohort
The recalibration gate requires a minimum cohort size of 5.
This prevents calibration from being influenced by individual outliers.

## Why Size Matters
| Cohort Size | Reliability | Risk |
|:-----------:|:-----------:|:----:|
| 1-4 | Low | Single result can shift weights |
| 5-9 | Moderate | Some protection from outliers |
| 10-19 | Good | Reasonable statistical power |
| 20+ | High | Robust to individual outliers |

## Rules
- Cohorts below minimum size are rejected by the gate.
- Results from small cohorts are informational only.
- Cohort size should be reported alongside calibration results.
- If the cohort is small, the calibration report should note the uncertainty.

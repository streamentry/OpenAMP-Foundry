# Result-Quality Flag Guide

Lab results should be flagged by quality before being used for calibration.

## Quality Levels
| Flag | Meaning | Use in Calibration? |
|------|---------|:-------------------:|
| `high` | Controls passed, triplicate, clear readout | Yes |
| `medium` | Controls passed, single replicate | Yes, with caution |
| `low` | One control failed or unclear readout | No |
| `invalid` | Controls failed or data is missing | No |

## Rules
- Results flagged `low` or `invalid` must not be used for calibration.
- Results flagged `medium` should be noted in the calibration report.
- Quality flags must be set by the lab partner, not the pipeline.

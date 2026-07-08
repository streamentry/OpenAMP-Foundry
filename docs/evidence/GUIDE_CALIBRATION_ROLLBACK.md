# Calibration Rollback Guide

How to roll back a calibration update if it causes issues.

## When to Roll Back
- A calibration update causes benchmark regression > 0.02.
- A calibration update introduces unexpected behavior.
- A calibration update was applied without proper review.

## Process
1. Identify the version before the calibration update.
2. Revert the weight changes in `configs/pipeline.yaml`.
3. Run `make bench-gate` to verify the regression is resolved.
4. Run `make full-reproducibility-report` to confirm all checks pass.
5. Log the rollback in the decision log with the reason.
6. Investigate what went wrong before attempting recalibration again.

# Calibration Philosophy Page

Calibration adjusts model outputs based on real data. It is not a fix for
fundamental model flaws — it adjusts confidence, not correctness.

## Principles
1. Calibration requires real data. Synthetic data cannot calibrate a model.
2. Calibration is gated by policy (see `configs/recalibration_policy.yaml`).
3. Calibration updates are proposed, not applied — human review is required.
4. Calibration cannot change the definition of success after the fact.
5. Calibration cannot override safety constraints.

## What Calibration Is NOT
- A way to make a bad model good
- A substitute for wet-lab validation
- A license to change scoring rules after seeing results
- An automated process — human review is always required

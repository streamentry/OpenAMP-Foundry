# Calibration Gate Explainer

The calibration gate is a safety mechanism that prevents weight updates
unless pre-registered conditions are met.

## How It Works
1. Lab results feed into `calibration-intake`.
2. The intake report is evaluated against `configs/recalibration_policy.yaml`.
3. The gate emits a binary verdict: `may_recalibrate` or not.
4. If blocked, no weight updates are allowed.

## Key Rules
- Exit code 0 = gate allows recalibration.
- Exit code 3 = gate rejects recalibration.
- The gate cannot be bypassed.
- Human review is required before any weight update, even if the gate passes.

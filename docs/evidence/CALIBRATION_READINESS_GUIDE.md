# Calibration Readiness Gate Guide

Schema: `CalibrationReadinessEntry` — binary pass/fail gate before releasing the next candidate batch.

## Purpose

Before releasing a new candidate batch for wet-lab testing, the calibration readiness gate
checks that recent performance is good enough. It consumes a cross-batch aggregator record
(CBA-) and applies threshold checks to produce a pass/fail verdict. Failing batches are held
until recalibration is complete.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `gate_id` | str | Unique ID, must start with "CRG-" |
| `pipeline_version` | str | Pipeline version being evaluated |
| `aggregator_id` | str | CBA- record being used as input (must start with "CBA-") |
| `mean_brier_score` | float | Mean Brier score from aggregator (0.0–1.0) |
| `trend` | str | Trend from aggregator: improving, stable, or degrading |
| `total_batches_evaluated` | int | Number of batches in the aggregation (>= 2) |
| `gate_passed` | bool | True if all threshold checks pass |
| `failure_reasons` | List[str] | Empty if passed; non-empty if failed |
| `gate_notes` | str | Max 400 chars |
| `reviewer` | str | Who signed off on this gate decision |
| `dry_lab_only` | bool | True (computational gate) |

## Validation Rules

1. `gate_id` must start with "CRG-"
2. `aggregator_id` must start with "CBA-"
3. `mean_brier_score` must be in [0.0, 1.0]
4. `trend` must be one of: improving, stable, degrading
5. `total_batches_evaluated` must be >= 2
6. `gate_notes` must not exceed 400 chars
7. `gate_passed` must be consistent: True iff failure_reasons is empty
8. If gate_passed=False, failure_reasons must be non-empty

## Warning Conditions

- trend == "degrading" and gate_passed=True (passed despite degrading trend)
- mean_brier_score >= WARN_BRIER_THRESHOLD (0.2) and gate_passed=True (marginal pass)

## Constants

- `GATE_NOTES_MAX_LENGTH = 400`
- `VALID_TRENDS = {"improving", "stable", "degrading"}`
- `PASS_BRIER_THRESHOLD = 0.25` (Brier > this fails the gate)
- `WARN_BRIER_THRESHOLD = 0.2` (Brier >= this but < 0.25 triggers warning)
- `MIN_BATCHES = 2`

# Recalibration Refusal Record Guide

## Purpose

A Recalibration Refusal Record (RRF) documents when a recalibration evaluation was
conducted and the decision was to **not** recalibrate.

Refusing to recalibrate on weak evidence is a quality outcome.  Without explicit
refusal records, a pipeline might silently skip recalibration with no audit trail.
With RRF records, every evaluated-but-rejected recalibration trigger is documented.

## Relationship to other schemas

| Schema | Records |
|---|---|
| `CalibrationPerformanceSummary` (CPS-) | Accuracy metrics per batch |
| `PredictionDriftMonitor` (DRM-) | Detected drift between batches |
| `CalibrationImprovementRecord` (CIR-) | Approved recalibrations |
| `RecalibrationRefusalRecord` (RRF-) | Rejected recalibration evaluations |

The trigger for an RRF must be a CPS- or DRM- entry.

## Key constraint

`recalibration_refused` must be `True`.  This schema only records valid refusals.
If a recalibration was approved, use `CalibrationImprovementRecord` instead.

## Schema fields

| Field | Type | Description |
|---|---|---|
| `rrf_id` | str | Must start with `RRF-` |
| `pipeline_version` | str | Pipeline version at evaluation time |
| `trigger_id` | str | CPS- or DRM- entry that triggered evaluation |
| `recalibration_refused` | bool | Must be `True` |
| `refusal_reason` | str | One of 5 valid categories |
| `minimum_batches_required` | int | Minimum batches needed to justify recalibration |
| `batches_evaluated` | int | Batches actually available |
| `refusal_notes` | str | Max 400 chars |
| `reviewer` | str | Who made the refusal decision |
| `dry_lab_only` | bool | Default True |

## Refusal reasons

| Reason | When to use |
|---|---|
| `insufficient_data` | Too few batches to justify recalibration |
| `effect_within_noise` | Detected signal is within expected noise range |
| `recent_recalibration` | Recalibration was done too recently |
| `conflicting_signals` | Multiple signals point in different directions |
| `reviewer_override` | Human reviewer overrode automated recommendation |

## Honest boundaries

- An RRF records a human or pipeline decision — it does not prove the decision was
  correct. Future batches may reveal the refusal was wrong.
- The RRF does not validate that `trigger_id` references a real CPS- or DRM- entry;
  referential integrity requires a separate audit step.
- `minimum_batches_required` is a policy value, not a statistical guarantee. The same
  number of batches may be sufficient in some scenarios and insufficient in others.

## Warnings

The validator emits warnings (not errors) for:

- `refusal_reason="insufficient_data"` but `batches_evaluated >= minimum_batches_required`
  — consider a more precise reason.
- `refusal_reason="reviewer_override"` — document the specific reason in `refusal_notes`.

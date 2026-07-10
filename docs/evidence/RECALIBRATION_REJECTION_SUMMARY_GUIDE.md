# RecalibrationRejectionSummary (RRS-) Guide

## Purpose

`RecalibrationRejectionSummary` aggregates recalibration refusal events across
a pipeline period to show that the calibration gate is working correctly —
that the right recalibrations were correctly refused, not rubber-stamped.

## Schema Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rrs_id` | str | yes | Unique identifier, must start with `RRS-` |
| `pipeline_version` | str | yes | Pipeline version during this period |
| `period_start` | str | yes | ISO date (YYYY-MM-DD) for period start |
| `period_end` | str | yes | ISO date (YYYY-MM-DD) for period end |
| `total_checkpoints_reviewed` | int | yes | Total calibration checkpoints reviewed (≥1) |
| `total_refused` | int | yes | Number refused (in [0, total_checkpoints_reviewed]) |
| `total_approved` | int | yes | Number approved (refused+approved=total) |
| `refusal_rate` | float | yes | Fraction refused (must match total_refused/total, tol 0.01) |
| `top_refusal_reason` | str | yes | Most common refusal reason (controlled vocabulary) |
| `gate_status` | str | yes | Current gate status (`active`, `suspended`, `under_review`) |
| `all_refusals_have_rrf` | bool | yes | Must be True — all refusals have RRF- artifacts |
| `summary` | str | yes | Narrative summary (≤400 chars) |
| `notes` | str | no | Additional context (≤300 chars) |

## Controlled Vocabularies

**top_refusal_reason (7 values):**
- `insufficient_data`, `effect_within_noise`, `recent_recalibration`
- `conflicting_signals`, `reviewer_override`, `multiple_reasons`, `none_refused`

**gate_status (3 values):**
- `active` — gate operating normally
- `suspended` — gate temporarily suspended (requires human approval)
- `under_review` — gate configuration under review

## Validation Rules

1. `rrs_id` starts with `RRS-`
2. `pipeline_version` non-empty
3. `period_start` is ISO date (YYYY-MM-DD)
4. `period_end` is ISO date (YYYY-MM-DD)
5. `total_checkpoints_reviewed` ≥ 1
6. `total_refused` in [0, total_checkpoints_reviewed]
7. `total_approved` in [0, total_checkpoints_reviewed]
8. `total_refused + total_approved == total_checkpoints_reviewed`
9. `refusal_rate` in [0.0, 1.0]
10. `refusal_rate` consistent with `total_refused / total_checkpoints_reviewed` (tolerance 0.01)
11. `top_refusal_reason` in controlled vocabulary (7 values)
12. `gate_status` in controlled vocabulary (3 values)
13. `all_refusals_have_rrf` must be True
14. `summary` non-empty and ≤400 chars
15. `notes` ≤300 chars

## Warnings

- `refusal_rate > 0.9`: investigate whether gate thresholds are too strict
- `total_refused == 0`: verify gate is operating (not silently approving all)
- `notes` empty: consider adding context for reviewers

## Integration

- Each refusal references: `RRF-` (recalibration refusal record)
- Triggered by: `RDL-` (recalibration decision log) showing refused outcomes
- Feeds into: governance audit trail, calibration health monitoring

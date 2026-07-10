# Rejection Reason Entry Guide

## Purpose

A `RejectionReasonEntry` (RJR-) records why a specific candidate was rejected
during the selection pipeline. It enforces a controlled vocabulary of rejection
stages and reasons, making failure analysis machine-readable and enabling the
calibration loop to learn from structured failure signals.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rjr_id` | str | Yes | Unique ID, must start with `RJR-` |
| `pipeline_version` | str | Yes | Version of the pipeline at rejection time |
| `candidate_id` | str | Yes | ID of the rejected candidate |
| `rejection_stage` | str | Yes | Which pipeline stage rejected it (controlled vocabulary) |
| `rejection_reason` | str | Yes | Why it was rejected (controlled vocabulary) |
| `rejection_confidence` | str | Yes | Confidence in the decision: `high`, `medium`, `low`, `uncertain` |
| `rejection_date` | str | Yes | ISO YYYY-MM-DD date of rejection decision |
| `borderline` | bool | Yes | `True` if this was a close call |
| `reviewer` | str | Yes | Name of the human who confirmed the rejection |
| `rejection_notes` | str | Yes | Context notes (max 400 chars); required for `manual_exclusion` |
| `dry_lab_only` | bool | No | Default `True` — dry-lab rejections only |

## Rejection stages

| Stage | Meaning |
|-------|---------|
| `initial_screen` | First-pass activity filter |
| `toxicity_screen` | Cytotoxicity / cell viability screen |
| `hemolysis_screen` | Predicted hemolysis above threshold |
| `novelty_filter` | Too similar to known AMPs |
| `selection_gate` | Failed the calibration readiness gate |
| `safety_policy_block` | Triggered a dual-use or biosafety policy |
| `manual_exclusion` | Human override exclusion |

## Rejection reasons

| Reason | Meaning |
|--------|---------|
| `low_activity_score` | Predicted antimicrobial activity below threshold |
| `hemolysis_risk` | Predicted hemolysis above allowed threshold |
| `toxicity_risk` | Predicted cytotoxicity above threshold |
| `insufficient_novelty` | Sequence too similar to known AMPs or training data |
| `data_quality_failure` | Upstream data quality issue |
| `safety_policy_block` | Safety or dual-use policy triggered |
| `duplicate` | Duplicate of another candidate in the batch |
| `out_of_scope` | Outside the current project scope |
| `manual_exclusion` | Human reviewer override |

## Validation rules

1. `rjr_id` must start with `RJR-`
2. `pipeline_version`, `candidate_id`, `reviewer` must not be empty
3. `rejection_stage` must be in the controlled vocabulary
4. `rejection_reason` must be in the controlled vocabulary
5. `rejection_confidence` must be `high`, `medium`, `low`, or `uncertain`
6. `rejection_date` must be ISO format `YYYY-MM-DD`
7. `rejection_notes` must be at most 400 characters
8. `rejection_reason = manual_exclusion` requires non-empty `rejection_notes`
9. `borderline=True` is inconsistent with `rejection_confidence='high'`

## Warnings

- `rejection_confidence='uncertain'` — candidate may need re-evaluation
- `borderline=True` with empty notes — document the borderline rationale
- `rejection_reason='safety_policy_block'` with no notes — name the policy triggered

## CLI usage

```bash
openamp-foundry rejection-reason-check \
  --entry-json '{"rjr_id":"RJR-001","pipeline_version":"v0.10.9","candidate_id":"CAND-001","rejection_stage":"toxicity_screen","rejection_reason":"toxicity_risk","rejection_confidence":"high","rejection_date":"2026-07-10","borderline":false,"reviewer":"Dr. Smith","rejection_notes":"Cytotoxicity above threshold."}' \
  --format text
```

## Honest boundaries

- RJR records are dry-lab-only — they record predicted, not confirmed, rejection reasons.
- A `borderline=True` record is not a weakened rejection — it flags cases where the threshold was met but the decision was close, which is useful calibration signal.
- `manual_exclusion` records must always be documented.

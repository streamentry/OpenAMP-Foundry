# RecalibrationDecisionLog (RDL-) Guide

## Purpose

`RecalibrationDecisionLog` records every governance decision at a calibration
checkpoint — whether the pipeline was recalibrated, refused, deferred, or
partially updated — and preserves the evidence trail for each choice.

## Schema Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rdl_id` | str | yes | Unique identifier, must start with `RDL-` |
| `pipeline_version` | str | yes | Pipeline version at decision time |
| `calibration_checkpoint` | str | yes | Named checkpoint (e.g. `batch_3_review`) |
| `decision_date` | str | yes | ISO date (YYYY-MM-DD) of decision |
| `trigger_type` | str | yes | What triggered the review (controlled vocabulary) |
| `trigger_artifact_id` | str | yes | ID of the artifact that triggered the review |
| `decision_outcome` | str | yes | `approved`, `refused`, `deferred`, `partial_approved` |
| `decision_authority` | str | yes | Who/what made the decision (controlled vocabulary) |
| `evidence_summary` | str | yes | Concise summary of evidence considered |
| `rationale` | str | yes | Reasoning behind decision (≤500 chars) |
| `next_review_date` | str | yes | ISO date for next scheduled review |
| `conditions_if_deferred` | str | no | Required when outcome is `deferred` |
| `notes` | str | no | Additional context (≤300 chars) |

## Controlled Vocabularies

**trigger_type:**
- `batch_outcome` — triggered by batch result data
- `calibration_performance_summary` — triggered by CPS- artifact
- `scheduled_review` — routine scheduled checkpoint
- `anomaly_detected` — triggered by anomaly detection
- `human_request` — human reviewer requested review

**decision_outcome:**
- `approved` — recalibration proceeds
- `refused` — recalibration rejected (see RRF-)
- `deferred` — decision postponed pending more data
- `partial_approved` — selective update to specific components

**decision_authority:**
- `automated_gate` — automated pipeline gate
- `pipeline_owner` — pipeline owner
- `external_reviewer` — external domain expert
- `safety_officer` — safety review officer
- `committee` — multi-member review committee

## Validation Rules

1. `rdl_id` starts with `RDL-`
2. `pipeline_version` non-empty
3. `calibration_checkpoint` non-empty
4. `decision_date` is ISO date (YYYY-MM-DD)
5. `trigger_type` in controlled vocabulary (5 values)
6. `trigger_artifact_id` starts with a known prefix (CPS-, DRM-, PCI-, BSP-, CIR-, RRF-)
7. `decision_outcome` in controlled vocabulary (4 values)
8. `decision_authority` in controlled vocabulary (5 values)
9. `evidence_summary` non-empty
10. `rationale` non-empty and ≤500 chars
11. `next_review_date` is ISO date (YYYY-MM-DD)
12. `conditions_if_deferred` required when outcome is `deferred`
13. `notes` ≤300 chars

## Warnings

- `refused` outcome: verify rationale cites a specific RRF- artifact
- `deferred` with no notes: consider documenting deferral context
- `notes` empty: consider adding context for future reviewers

## Usage

```python
from openamp_foundry.evidence.recalibration_decision_log import (
    RecalibrationDecisionLog, validate
)

log = RecalibrationDecisionLog(
    rdl_id="RDL-20240315-001",
    pipeline_version="v2.1.0",
    calibration_checkpoint="batch_3_review",
    decision_date="2024-03-15",
    trigger_type="batch_outcome",
    trigger_artifact_id="CPS-20240314-001",
    decision_outcome="approved",
    decision_authority="automated_gate",
    evidence_summary="Brier score improved from 0.28 to 0.21 after batch 3.",
    rationale="Metric improvement exceeds minimum threshold and is consistent across 3 cohorts.",
    next_review_date="2024-06-15",
)
errors = validate(log)
assert errors == []
```

## Integration

- Triggered by: `CPS-` (calibration performance summary), `PCI-` (post-experiment intake)
- Refused outcomes generate: `RRF-` (recalibration refusal record)
- Approved outcomes generate: `CIR-` (calibration improvement record)
- Feeds into: governance audit trail, decision pattern analysis

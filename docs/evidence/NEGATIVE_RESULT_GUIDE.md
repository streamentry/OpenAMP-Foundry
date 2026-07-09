# Negative Result Record Guide

## Purpose

A negative result record documents experiments or predictions that failed to
meet expectations. Negative results are not failures of the pipeline — they
are information. Recording them is mandatory for:

1. Honest calibration (you cannot calibrate on cherry-picked successes)
2. Preventing repeated experiments (institutional memory)
3. Publication integrity (selective reporting is a form of bias)
4. Future hypothesis generation (knowing what does NOT work narrows the space)

## Schema Fields

| Field | Type | Description |
|---|---|---|
| record_id | str | Unique identifier (prefix "NRR-") |
| batch_id | str | Batch or experiment set this record covers |
| pipeline_version | str | Pipeline version at time of experiment |
| record_date | str | ISO 8601 date result was recorded |
| failure_category | str | Category of failure (see valid categories) |
| failure_description | str | Plain-language description of what failed (max 500 chars) |
| candidate_ids | list[str] | IDs of candidates that failed (at least 1) |
| assay_type | str | Assay in which failure was observed (see valid types) |
| expected_outcome | str | What was predicted or expected |
| observed_outcome | str | What was actually observed |
| hypothesis_impact | str | How this result affects the working hypothesis (max 300 chars) |
| will_be_reported | bool | Whether this result will be included in any publication or report |
| recorded_by | str | Person or system recording this |
| dry_lab_only | bool | False if real lab data; True if computational only |

## Valid Failure Categories

- `assay_quality_failure` — assay controls failed; results not interpretable
- `below_activity_threshold` — predicted activity not confirmed
- `excessive_toxicity` — candidate was too toxic (hemolysis/cytotoxicity)
- `model_overprediction` — model was significantly more optimistic than results
- `pipeline_error` — computational error or data quality issue
- `stability_failure` — candidate degraded under assay conditions

## Valid Assay Types

- `cytotoxicity_assay`
- `hemolysis_assay`
- `membrane_disruption_assay`
- `mic_assay`
- `stability_assay`

## Validation Rules

1. record_id must start with "NRR-"
2. failure_category must be one of the valid categories
3. failure_description must not be empty and must not exceed 500 characters
4. candidate_ids must contain at least 1 candidate
5. assay_type must be one of the valid assay types
6. expected_outcome must not be empty
7. observed_outcome must not be empty
8. hypothesis_impact must not be empty and must not exceed 300 characters
9. recorded_by must not be empty

## Warning Conditions

- Not reported: will_be_reported=False → warn that suppressing negative results contributes to publication bias
- Large failure set: len(candidate_ids) > 10 → warn about systematic failure; pipeline may need recalibration
- Model overprediction without recalibration note: failure_category="model_overprediction" and "calibrat" not in hypothesis_impact.lower() → warn that recalibration should be considered

## Honest Use Boundary

A negative result record must be filed even when the result is inconvenient.
The commitment to record negative results is not optional. A pipeline that only
documents successes is not a scientific tool — it is a selection bias engine.
Do not set will_be_reported=False without documenting why in hypothesis_impact.

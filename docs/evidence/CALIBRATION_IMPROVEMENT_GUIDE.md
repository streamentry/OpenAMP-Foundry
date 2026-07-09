# Calibration Improvement Record Guide

Schema: `CalibrationImprovementEntry` — documents recalibration actions taken after drift or quality failures.

## Purpose

When calibration performance drops below threshold (high FP rate, low recall, poor Brier score) or
prediction drift is detected, a recalibration action must be taken. This schema provides an auditable
record of what changed, why, and what effect it had — closing the loop between detection and correction.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `improvement_id` | str | Unique ID, must start with "CIR-" |
| `pipeline_version_before` | str | Pipeline version before recalibration |
| `pipeline_version_after` | str | Pipeline version after recalibration |
| `trigger_ids` | List[str] | IDs of CPS- or DRM- records that triggered this action (at least 1) |
| `action_taken` | str | Description of what was changed (max 500 chars) |
| `action_category` | str | One of: threshold_adjustment, retraining, feature_removal, feature_addition, data_augmentation, weighting_change |
| `brier_score_before` | float | Brier score before action (0.0–1.0) |
| `brier_score_after` | float | Brier score after action (0.0–1.0) |
| `improvement_confirmed` | bool | True if brier_score_after < brier_score_before |
| `reviewer` | str | Who reviewed this improvement record |
| `dry_lab_only` | bool | False (may incorporate real lab feedback) |

## Validation Rules

1. `improvement_id` must start with "CIR-"
2. `pipeline_version_before` and `pipeline_version_after` must differ
3. `trigger_ids` must contain at least 1 entry
4. Each trigger_id must start with "CPS-" or "DRM-"
5. `action_taken` must not exceed 500 characters
6. `action_category` must be one of the 6 valid categories
7. `brier_score_before` and `brier_score_after` must be in [0.0, 1.0]
8. `improvement_confirmed` must be consistent: True iff brier_score_after < brier_score_before

## Warning Conditions

- brier_score_after >= brier_score_before but improvement_confirmed=True (inconsistency)
- brier_score_after > POOR_BRIER_THRESHOLD (0.25) even after recalibration
- pipeline_version_before == pipeline_version_after warns about missing version bump

## Constants

- `ACTION_TAKEN_MAX_LENGTH = 500`
- `VALID_ACTION_CATEGORIES = {"threshold_adjustment", "retraining", "feature_removal", "feature_addition", "data_augmentation", "weighting_change"}`
- `VALID_TRIGGER_PREFIXES = {"CPS-", "DRM-"}`
- `POOR_BRIER_THRESHOLD = 0.25`

# Prediction Drift Monitor Guide

Schema: `PredictionDriftEntry` — tracks score distribution shifts across pipeline batches.

## Purpose

Prediction drift monitoring detects when the pipeline's score distributions shift between
batches without a corresponding change in pipeline version. Drift can indicate:
- Changes in input sequence distribution (different organisms, assay conditions)
- Silent model degradation or data leakage
- Recalibration need before lab results confirm it

This is the earliest warning signal available before wet-lab validation data arrives.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `monitor_id` | str | Unique ID, must start with "DRM-" |
| `pipeline_version` | str | Pipeline version being monitored |
| `reference_batch_id` | str | Batch used as baseline for drift comparison |
| `evaluation_batch_id` | str | Batch being evaluated for drift |
| `reference_mean_score` | float | Mean prediction score in reference batch (0.0–1.0) |
| `reference_std_score` | float | Std dev of scores in reference batch (≥ 0.0) |
| `evaluation_mean_score` | float | Mean prediction score in evaluation batch (0.0–1.0) |
| `evaluation_std_score` | float | Std dev of scores in evaluation batch (≥ 0.0) |
| `mean_shift_magnitude` | float | Absolute difference in means (≥ 0.0) |
| `population_size_reference` | int | Number of candidates in reference batch (≥ 1) |
| `population_size_evaluation` | int | Number of candidates in evaluation batch (≥ 1) |
| `drift_flag` | bool | True if drift exceeds threshold |
| `drift_notes` | str | Max 400 chars; required when drift_flag=True |
| `reviewer` | str | Who reviewed this drift assessment |
| `dry_lab_only` | bool | Always True (computational monitoring) |

## Validation Rules

1. `monitor_id` must start with "DRM-"
2. `reference_batch_id` and `evaluation_batch_id` must differ
3. `reference_mean_score` and `evaluation_mean_score` must be in [0.0, 1.0]
4. `reference_std_score` and `evaluation_std_score` must be ≥ 0.0
5. `mean_shift_magnitude` must equal |evaluation_mean_score - reference_mean_score| ± 0.001
6. `population_size_reference` and `population_size_evaluation` must be ≥ 1
7. `drift_notes` must not exceed 400 characters
8. When `drift_flag=True`, `drift_notes` must be non-empty

## Warning Conditions

- Mean shift ≥ 0.1 without drift_flag=True (possible unreported drift)
- Either population < 10 (small sample, drift estimate unreliable)
- Std dev in evaluation batch > 2× reference std dev (variance explosion)

## Constants

- `DRIFT_NOTES_MAX_LENGTH = 400`
- `MEAN_SHIFT_TOLERANCE = 0.001`
- `SIGNIFICANT_DRIFT_THRESHOLD = 0.1`
- `MIN_POPULATION_FOR_RELIABLE_DRIFT = 10`
- `VARIANCE_EXPLOSION_RATIO = 2.0`

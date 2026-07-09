# Calibration Performance Summary Guide

## Purpose

A calibration performance summary aggregates prediction accuracy metrics
across a window of experimental batches where outcomes are known. It answers:
"How well is the pipeline predicting real experimental results?"

Without this record, calibration problems are invisible. A pipeline can be
confidently wrong for many batches before anyone notices.

## Schema Fields

| Field | Type | Description |
|---|---|---|
| summary_id | str | Unique identifier (prefix "CPS-") |
| pipeline_version | str | Pipeline version being evaluated |
| evaluation_date | str | ISO 8601 date of this evaluation |
| batch_ids_evaluated | list[str] | Batches included in this summary (at least 1) |
| total_candidates_evaluated | int | Total candidates with known outcomes |
| true_positive_count | int | Predicted active, confirmed active |
| false_positive_count | int | Predicted active, confirmed inactive |
| true_negative_count | int | Predicted inactive, confirmed inactive |
| false_negative_count | int | Predicted inactive, confirmed active |
| brier_score | float | Probability calibration score (0.0=perfect, 1.0=worst) |
| calibration_notes | str | Observations about calibration quality (max 400 chars) |
| reviewer | str | Person or system that validated this summary |
| dry_lab_only | bool | False (uses real lab outcome data) |

## Derived Metrics (computed, not stored)

From the confusion matrix counts:
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- Specificity = TN / (TN + FP)
- F1 = 2 * Precision * Recall / (Precision + Recall)

## Validation Rules

1. summary_id must start with "CPS-"
2. batch_ids_evaluated must contain at least 1 batch
3. total_candidates_evaluated must be at least 1
4. true_positive_count, false_positive_count, true_negative_count, false_negative_count must all be >= 0
5. total_candidates_evaluated must equal TP + FP + TN + FN
6. brier_score must be between 0.0 and 1.0 (inclusive)
7. calibration_notes must not exceed 400 characters
8. reviewer must not be empty
9. dry_lab_only must be False (requires real lab data)

## Warning Conditions

- High false positive rate: FP / (FP + TN) > 0.5 → warn that pipeline is over-predicting activity
- Low recall: TP / (TP + FN) < 0.3 → warn that pipeline is missing many active candidates
- Poor Brier score: brier_score > 0.25 → warn that probability calibration is poor
- Small evaluation window: total_candidates_evaluated < 10 → warn that sample is too small for reliable calibration assessment

## Honest Use Boundary

Calibration performance is evaluated on *known* outcomes — candidates where
experimental results have been received. Do not extrapolate calibration
statistics to candidates not yet tested. A good Brier score on past batches
does not guarantee accurate predictions for future batches.

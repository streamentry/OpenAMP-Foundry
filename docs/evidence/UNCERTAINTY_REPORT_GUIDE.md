# Uncertainty Quantification Report Guide

An *uncertainty quantification (UQ) report* communicates the prediction-interval width,
calibration status, and confidence bounds for each computational candidate recommendation.
This guide defines the required format, validation rules, and honest-use constraints.

## Purpose

External reviewers need honest uncertainty estimates to:
- judge whether a high-confidence prediction is trustworthy or over-confident,
- compare interval width against historical calibration error,
- decide whether uncertainty is small enough to justify synthesis cost.

## Required fields

| Field | Type | Constraint |
|---|---|---|
| `report_id` | str | Must start with `"UQ-"` |
| `batch_id` | str | Non-empty |
| `candidate_id` | str | Non-empty |
| `pipeline_version` | str | Non-empty |
| `metric_name` | str | One of `VALID_METRIC_NAMES` |
| `point_estimate` | float | Any finite float |
| `lower_bound` | float | Must be ≤ `point_estimate` |
| `upper_bound` | float | Must be ≥ `point_estimate` |
| `confidence_level` | float | 0.0 – 1.0 (e.g. 0.90 for 90%) |
| `calibration_source` | str | Non-empty (e.g. `"historical_holdout_v2"`) |
| `reviewer` | str | Non-empty |
| `dry_lab_only` | bool | Must be `True` |

## Valid metric names

`mic`, `hemolysis_fraction`, `cytotoxicity_score`, `selectivity_index`, `stability_score`

## Warnings

- `upper_bound - lower_bound > WIDE_INTERVAL_THRESHOLD` — warning: interval is wide; low predictive precision.
- `confidence_level < 0.80` — warning: confidence level below 80%; results may be unreliable.
- `confidence_level > 0.99` — warning: confidence level above 99%; verify calibration method.

## How to validate

```bash
make uncertainty-report-check
# or
openamp-foundry uncertainty-report-check \
  --entry-json '{"report_id":"UQ-001","batch_id":"BATCH-001","candidate_id":"AMP-001","pipeline_version":"0.8.3","metric_name":"mic","point_estimate":4.0,"lower_bound":2.0,"upper_bound":8.0,"confidence_level":0.90,"calibration_source":"historical_holdout_v2","reviewer":"alice","dry_lab_only":true}' \
  --format text
```

## Honest-use boundary

UQ reports are dry-lab outputs. Prediction intervals reflect model uncertainty,
not biological variability. A narrow interval does not guarantee experimental success.
Never present these bounds as experimental measurements.

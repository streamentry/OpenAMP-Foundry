# Cross-Batch Performance Aggregator Guide

Schema: `CrossBatchAggregatorEntry` — aggregates calibration performance across multiple batches.

## Purpose

A single batch's calibration metrics (Brier score, FP rate, recall) may be noisy. Tracking
performance across N batches reveals whether calibration is trending up, down, or holding steady
— the key input to the calibration readiness gate (O5).

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `aggregator_id` | str | Unique ID, must start with "CBA-" |
| `pipeline_version` | str | Pipeline version being aggregated |
| `batch_ids_included` | List[str] | Batch IDs included in aggregation (at least 2) |
| `summary_ids_included` | List[str] | CPS- record IDs included (at least 2, must match batch count) |
| `mean_brier_score` | float | Mean Brier score across batches (0.0–1.0) |
| `min_brier_score` | float | Minimum Brier score across batches (0.0–1.0) |
| `max_brier_score` | float | Maximum Brier score across batches (0.0–1.0) |
| `trend` | str | One of: improving, stable, degrading |
| `total_candidates_evaluated` | int | Total candidates across all batches (>= 2) |
| `aggregation_notes` | str | Max 400 chars |
| `reviewer` | str | Who reviewed this aggregation |
| `dry_lab_only` | bool | True (computational aggregation) |

## Validation Rules

1. `aggregator_id` must start with "CBA-"
2. `batch_ids_included` must have at least 2 entries
3. `summary_ids_included` must have at least 2 entries and each must start with "CPS-"
4. `len(batch_ids_included) == len(summary_ids_included)`
5. `mean_brier_score`, `min_brier_score`, `max_brier_score` must be in [0.0, 1.0]
6. `min_brier_score <= mean_brier_score <= max_brier_score`
7. `trend` must be one of: improving, stable, degrading
8. `total_candidates_evaluated` must be >= 2
9. `aggregation_notes` must not exceed 400 chars

## Warning Conditions

- `mean_brier_score >= POOR_BRIER_THRESHOLD (0.25)` — calibration below par
- `max_brier_score - min_brier_score >= HIGH_VARIANCE_THRESHOLD (0.2)` — high variance across batches
- trend == "degrading" — performance getting worse

## Constants

- `AGGREGATION_NOTES_MAX_LENGTH = 400`
- `VALID_TRENDS = {"improving", "stable", "degrading"}`
- `POOR_BRIER_THRESHOLD = 0.25`
- `HIGH_VARIANCE_THRESHOLD = 0.2`
- `MIN_BATCHES = 2`
- `SUMMARY_ID_PREFIX = "CBA-"`
- `CPS_PREFIX = "CPS-"`

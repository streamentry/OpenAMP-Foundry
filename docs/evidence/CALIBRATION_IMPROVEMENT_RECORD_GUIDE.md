# Calibration Improvement Record Guide (CIR-)

## Purpose

A `CalibrationImprovementRecord` (CIR-) documents what changed in the calibration
model and by how much. It is the "before/after" audit record for calibration updates —
recording the metric name, before/after values, the data source used, and the rationale
for the change.

CIR- completes Phase O alongside O1 (calibration performance summary), O2 (prediction
drift monitor), O4 (cross-batch aggregator), and O5 (calibration readiness gate). Without
CIR-, there is no structured record of what actually changed between calibration versions.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `cir_id` | str | Yes | Unique ID, must start with `CIR-` |
| `pipeline_version` | str | Yes | Version of the pipeline performing calibration |
| `calibration_version_before` | str | Yes | Calibration version before the update |
| `calibration_version_after` | str | Yes | Calibration version after the update (must differ) |
| `improvement_date` | str | Yes | ISO date (YYYY-MM-DD) of the improvement |
| `metric_name` | str | Yes | Controlled vocabulary: which metric improved |
| `metric_value_before` | float | Yes | Metric value before calibration update |
| `metric_value_after` | float | Yes | Metric value after calibration update |
| `improvement_confirmed` | bool | Yes | Must be True; not recorded unless confirmed improvement |
| `improvement_rationale` | str | Yes | Why this is a genuine improvement (≤400 chars) |
| `data_source_id` | str | Yes | Batch or dataset used for recalibration |
| `notes` | str | No | Additional context (≤300 chars) |

## Valid Metric Names

### Higher Is Better

| Metric | Description |
|--------|-------------|
| `auroc` | Area under the ROC curve |
| `auprc` | Area under the precision-recall curve |
| `precision_at_k` | Precision at top-K candidates |
| `recall_at_k` | Recall at top-K candidates |
| `f1_at_threshold` | F1 at a fixed decision threshold |

### Lower Is Better

| Metric | Description |
|--------|-------------|
| `brier_score` | Mean squared error of probability predictions |
| `calibration_error` | Mean absolute calibration error |
| `expected_calibration_error` | ECE across probability bins |

## Validation Rules

1. `cir_id` must start with `CIR-`
2. `pipeline_version` must be non-empty
3. `calibration_version_before` must be non-empty
4. `calibration_version_after` must be non-empty
5. `calibration_version_before` and `calibration_version_after` must differ
6. `improvement_date` must match `YYYY-MM-DD`
7. `metric_name` must be in valid set (8 values)
8. `improvement_confirmed` must be True
9. `improvement_rationale` must be non-empty and ≤400 chars
10. `data_source_id` must be non-empty
11. `notes` must be ≤300 chars

## Warnings

| Condition | Warning |
|-----------|---------|
| Higher-is-better metric but `after ≤ before` | Metric went wrong direction; verify it's a genuine improvement |
| Lower-is-better metric but `after ≥ before` | Metric went wrong direction; verify it's a genuine improvement |
| Improvement magnitude < 0.005 | Very small improvement; verify it's scientifically meaningful |
| `notes` is empty | No reviewer context recorded |

## Boundaries

- **CIR- records confirmed improvements only.** `improvement_confirmed` must be True. If calibration regressed, do not create a CIR-; instead investigate the regression.
- **CIR- is per-metric.** One CIR- per metric improved per calibration cycle. If AUROC and ECE both improved, create two CIR- records.
- **Direction validation is advisory (warning, not error).** The schema warns if the metric moved the wrong way but does not error, because calibration objectives sometimes involve trade-offs between metrics.
- **`data_source_id` links to the real outcomes used.** This makes calibration updates reproducible.

## CLI

```bash
openamp-foundry calibration-improvement-record-check '{"cir_id": "CIR-001", ...}'
```

Returns `VALID` or `INVALID` with any errors and warnings.

## Relationship to Other Schemas

```
O1 (CPS-)  ──→  CIR-  (performance summary triggers improvement effort)
O2 (PDM-)  ──→  CIR-  (drift monitor identifies what needs fixing)
CIR-       ──→  O5    (improved calibration feeds readiness gate)
CIR-       ──→  P2    (rejected recalibrations are documented separately via P2/CRG-)
```

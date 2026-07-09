# Post-Experiment Calibration Intake Guide

When an external lab returns results from a pilot batch, each experimental outcome
must be compared against the pipeline's dry-lab predictions. This guide defines the
structured intake format for capturing that comparison and feeding it back into the
calibration system.

## Purpose

Calibration intake records exist so the pipeline can:
- detect when prediction confidence is systematically over- or under-estimated,
- trigger recalibration when error rates cross defined thresholds, and
- maintain an auditable trail of prediction-vs-outcome comparisons.

## Required fields

| Field | Type | Constraint |
|---|---|---|
| `intake_id` | str | Must start with `"CAL-"` |
| `batch_id` | str | Non-empty |
| `candidate_id` | str | Non-empty |
| `pipeline_version` | str | Non-empty |
| `assay_type` | str | One of `VALID_ASSAY_TYPES` |
| `predicted_outcome` | str | One of `VALID_OUTCOME_VALUES` |
| `observed_outcome` | str | One of `VALID_OUTCOME_VALUES` |
| `predicted_confidence` | float | 0.0 – 1.0 |
| `intake_date` | str | ISO 8601 `YYYY-MM-DD` |
| `reviewer` | str | Non-empty |
| `dry_lab_only` | bool | Must be `False` — this record captures real lab results |

## Note on dry_lab_only

Unlike all other records in the pipeline, a calibration intake record **must** set
`dry_lab_only = False` because it contains actual experimental outcome data.
Keeping `dry_lab_only = True` on a record that contains lab results would be a
false claim. The validator enforces this.

## Valid assay types

`mic_assay`, `hemolysis_assay`, `cytotoxicity_assay`, `membrane_disruption_assay`, `stability_assay`

## Valid outcome values

`active`, `inactive`, `inconclusive`, `not_tested`

## Warnings

- `predicted_outcome == observed_outcome` (correct prediction) — no warnings, just noted in PASS output.
- `predicted_confidence >= 0.90` and prediction is wrong — warning: high-confidence misprediction.
- `observed_outcome == "inconclusive"` — warning: result is inconclusive; do not count as calibration signal.

## How to validate

```bash
make calibration-intake-check
# or
openamp-foundry calibration-intake-check \
  --entry-json '{"intake_id":"CAL-001","batch_id":"BATCH-001","candidate_id":"AMP-001","pipeline_version":"0.8.1","assay_type":"mic_assay","predicted_outcome":"active","observed_outcome":"active","predicted_confidence":0.85,"intake_date":"2026-07-09","reviewer":"alice","dry_lab_only":false}' \
  --format text
```

## Honest-use boundary

Calibration intake records describe real experimental outcomes. They must never be
confused with dry-lab predictions. `dry_lab_only` must be `False` on every intake record.

# Post-Experiment Calibration Intake Guide (PCI-)

## Purpose

A `PostExperimentCalibrationIntake` (PCI-) is the structured result-to-prediction
comparison record created after wet-lab experiments complete. It captures:
- How many candidates were tested and how many returned results
- How many showed activity vs. the model's predicted activity count
- The empirical hit rate and whether it is consistent with the stated value
- Whether calibration update is warranted based on the results

Without PCI-, experimental results cannot be systematically compared to predictions,
and the calibration cycle has no structured entry point.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pci_id` | str | Yes | Unique ID, must start with `PCI-` |
| `pipeline_version` | str | Yes | Version of the pipeline that generated predictions |
| `batch_id` | str | Yes | Batch that was experimentally tested |
| `experiment_date` | str | Yes | ISO date (YYYY-MM-DD) when experiments completed |
| `candidates_tested` | int | Yes | Total candidates sent to the lab (≥1) |
| `candidates_with_results` | int | Yes | Candidates that returned a result (≥1, ≤tested) |
| `predicted_active_count` | int | Yes | Number the model predicted would be active |
| `observed_active_count` | int | Yes | Number actually observed as active (≥0, ≤with_results) |
| `prediction_hit_rate` | float | Yes | observed_active/candidates_with_results ∈ [0, 1] |
| `calibration_update_warranted` | bool | Yes | Whether results justify updating calibration |
| `calibration_update_rationale` | str | Yes | Why update is/isn't warranted (≤400 chars) |
| `data_quality_confirmed` | bool | Yes | Must be True; data quality must be verified first |
| `notes` | str | No | Additional context (≤300 chars) |

## Validation Rules

1. `pci_id` must start with `PCI-`
2. `pipeline_version` must be non-empty
3. `batch_id` must be non-empty
4. `experiment_date` must match `YYYY-MM-DD`
5. `candidates_tested` must be ≥1
6. `candidates_with_results` must be ≥1 and ≤`candidates_tested`
7. `observed_active_count` must be ≥0 and ≤`candidates_with_results`
8. `prediction_hit_rate` must be in [0, 1]
9. `prediction_hit_rate` must be consistent with `observed_active_count / candidates_with_results` (tolerance 0.01)
10. `calibration_update_rationale` must be non-empty and ≤400 chars
11. `data_quality_confirmed` must be True
12. `notes` must be ≤300 chars

## Warnings

| Condition | Warning |
|-----------|---------|
| `candidates_with_results < candidates_tested` | Some candidates have no results; verify they are documented |
| `observed_active_count == 0` | No active candidates found; verify experimental conditions |
| `calibration_update_warranted=False` and `prediction_hit_rate < 0.3` | Low hit rate without calibration update; consider whether update is needed |

## Boundaries

- **PCI- records dry-lab-to-wet-lab comparison.** `prediction_hit_rate` is based on wet-lab results, not computational predictions.
- **`data_quality_confirmed` must be True.** Do not record a PCI- unless the experimental data has been quality-checked.
- **One PCI- per batch.** If a batch is run in multiple experiment waves, create separate PCI- records per wave.
- **Hit rate consistency is validated.** `prediction_hit_rate` must equal `observed_active_count / candidates_with_results` within 0.01.

## CLI

```bash
openamp-foundry post-experiment-calibration-intake-check '{"pci_id": "PCI-001", ...}'
```

Returns `VALID` or `INVALID` with any errors and warnings.

## Relationship to Other Schemas

```
BSP-  ──→  PCI-  (batch selection proposal identified the candidates tested)
PCI-  ──→  CIR-  (calibration improvement record documents the resulting update)
PCI-  ──→  P3    (batch outcome summary references PCI- data)
PCI-  ──→  P5    (calibration cycle summary includes PCI- as intake evidence)
```

# Negative Result Dashboard Guide (NRD-)

## Purpose

A `NegativeResultDashboard` (NRD-) aggregates rejection statistics across a batch to
show failure patterns in structured, machine-readable form. It records the top rejection
stage and reason, the overall rejection rate, high-confidence rejection count, and a
summary narrative.

NRD- is the summary layer above NRR- (individual records), NAS- (archive index), and
FCR- (batch report). While those schemas capture individual failures, NRD- makes the
aggregate pattern visible: which stage is failing most, which reason dominates, and
whether the rejection rate is unusually high.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `nrd_id` | str | Yes | Unique ID, must start with `NRD-` |
| `pipeline_version` | str | Yes | Version of the pipeline evaluated |
| `batch_id` | str | Yes | Batch being summarized |
| `report_date` | str | Yes | ISO date (YYYY-MM-DD) of dashboard generation |
| `total_candidates_evaluated` | int | Yes | Total candidates run through the pipeline (≥1) |
| `total_rejections` | int | Yes | Total candidates rejected (≥0, ≤evaluated) |
| `rejection_rate` | float | Yes | total_rejections/evaluated ∈ [0, 1] (tol 0.01) |
| `top_rejection_stage` | str | Yes | Stage responsible for most rejections |
| `top_rejection_reason` | str | Yes | Most common rejection reason |
| `high_confidence_rejections` | int | Yes | Rejections with high confidence (≥0, ≤total) |
| `all_rejections_have_nrr` | bool | Yes | Must be True; all rejections must have NRR- records |
| `summary` | str | Yes | Narrative summary of batch failures (≤400 chars) |
| `notes` | str | No | Additional context (≤300 chars) |

## Valid Vocabularies

### `top_rejection_stage` (7 values)

`sequence_quality`, `candidate_selection`, `toxicity_screen`, `hemolysis_screen`,
`novelty_check`, `simulation`, `manual_review`

### `top_rejection_reason` (9 values)

`low_score`, `failed_toxicity`, `failed_hemolysis`, `insufficient_novelty`,
`simulation_failure`, `duplicate_sequence`, `low_confidence`, `borderline_unsafe`,
`manual_exclusion`

## Validation Rules

1. `nrd_id` must start with `NRD-`
2. `pipeline_version` must be non-empty
3. `batch_id` must be non-empty
4. `report_date` must match `YYYY-MM-DD`
5. `total_candidates_evaluated` must be ≥1
6. `total_rejections` must be ≥0 and ≤`total_candidates_evaluated`
7. `rejection_rate` must be in [0, 1] and consistent with `total_rejections/total_candidates_evaluated` (tolerance 0.01)
8. `top_rejection_stage` must be in valid set (7 values)
9. `top_rejection_reason` must be in valid set (9 values)
10. `high_confidence_rejections` must be ≥0 and ≤`total_rejections`
11. `all_rejections_have_nrr` must be True
12. `summary` must be non-empty and ≤400 chars
13. `notes` must be ≤300 chars

## Warnings

| Condition | Warning |
|-----------|---------|
| `rejection_rate > 0.8` | Unusually high rejection rate; verify selection pipeline is not too strict |
| `total_rejections == total_candidates_evaluated` | All candidates rejected; verify no systematic pipeline failure |
| `notes` is empty | No reviewer context for this batch's failures |

## Boundaries

- **NRD- is a dashboard, not a root record.** It summarizes NRR- records; NRR- is the ground truth.
- **`all_rejections_have_nrr` must be True.** Do not create a NRD- unless every rejection has a corresponding NRR- record.
- **`top_rejection_stage` and `top_rejection_reason` are the modal values.** They name the most common stage and reason, not all stages and reasons.
- **NRD- is dry-lab only.** It records computational and manual filter decisions, not wet-lab results.

## CLI

```bash
openamp-foundry negative-result-dashboard-check '{"nrd_id": "NRD-001", ...}'
```

Returns `VALID` or `INVALID` with any errors and warnings.

## Relationship to Other Schemas

```
NRR-  ──→  NRD-  (dashboard aggregates individual failure records)
NAS-  ──→  NRD-  (archive index confirms all records are captured)
FCR-  ──→  NRD-  (batch report feeds aggregate view)
NRD-  ──→  CIR-  (rejection patterns inform calibration updates)
```

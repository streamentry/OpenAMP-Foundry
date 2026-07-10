# Negative Result Entry Guide (NRR-)

## Purpose

A `NegativeResultEntry` (NRR-) is the atomic failure record in the OpenAMP negative-result
infrastructure. It captures why a specific candidate was rejected at a specific pipeline
stage, using controlled vocabularies that enable structured failure analysis.

NRR- records are indexed by `NegativeResultArchiveSummary` (NAS-) and aggregated by
`FailedCandidateBatchReport` (FCR-). Without NRR-, the negative-result chain has no
foundation.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `nrr_id` | str | Yes | Unique ID, must start with `NRR-` |
| `pipeline_version` | str | Yes | Version string of the pipeline run |
| `candidate_id` | str | Yes | Identifier for the rejected candidate |
| `batch_id` | str | Yes | Batch this candidate belonged to |
| `experiment_date` | str | Yes | ISO date (YYYY-MM-DD) of rejection decision |
| `stage_at_rejection` | str | Yes | Pipeline stage where rejection occurred |
| `rejection_reason` | str | Yes | Controlled vocabulary reason for rejection |
| `rejection_confidence` | str | Yes | Confidence in the rejection decision |
| `outcome_summary` | str | Yes | Human-readable summary (≤400 chars) |
| `rejection_is_final` | bool | No | Whether this rejection is finalized (default: True) |
| `notes` | str | No | Additional context (≤300 chars) |
| `dry_lab_only` | bool | No | Always True; signals computational origin (default: True) |

## Valid Vocabularies

### `stage_at_rejection`

| Value | Description |
|-------|-------------|
| `sequence_quality` | Rejected at raw sequence quality check |
| `candidate_selection` | Rejected during selection/ranking |
| `toxicity_screen` | Rejected by toxicity predictor |
| `hemolysis_screen` | Rejected by hemolysis predictor |
| `novelty_check` | Rejected for insufficient novelty |
| `simulation` | Rejected by simulation module |
| `manual_review` | Excluded by human reviewer |

### `rejection_reason`

| Value | Description |
|-------|-------------|
| `low_score` | Score below selection threshold |
| `failed_toxicity` | Failed toxicity prediction gate |
| `failed_hemolysis` | Failed hemolysis prediction gate |
| `insufficient_novelty` | Too similar to known sequences |
| `simulation_failure` | Simulation returned invalid result |
| `duplicate_sequence` | Exact or near-duplicate already in pipeline |
| `low_confidence` | Model confidence below required minimum |
| `borderline_unsafe` | Near safety threshold, conservatively excluded |
| `manual_exclusion` | Human expert excluded for documented reason |

### `rejection_confidence`

| Value | Description |
|-------|-------------|
| `high` | Clear rejection with strong supporting signal |
| `medium` | Rejection supported but not certain |
| `low` | Marginal rejection; record may be revisited |
| `uncertain` | Reason for rejection unclear; do not treat as final |

## Validation Rules

1. `nrr_id` must start with `NRR-`
2. `pipeline_version` must be non-empty
3. `candidate_id` must be non-empty
4. `batch_id` must be non-empty
5. `experiment_date` must match `YYYY-MM-DD`
6. `stage_at_rejection` must be in valid set (7 values)
7. `rejection_reason` must be in valid set (9 values)
8. `rejection_confidence` must be in valid set (4 values)
9. `outcome_summary` must be non-empty and ≤400 chars
10. `notes` must be ≤300 chars

## Warnings

| Condition | Warning |
|-----------|---------|
| `rejection_is_final=False` and `rejection_confidence='high'` | Unusual: provisional record with high confidence |
| `stage='manual_review'` and `reason!='manual_exclusion'` | Stage/reason mismatch |
| `rejection_confidence='uncertain'` and `rejection_is_final=True` | Low-confidence final record |
| `rejection_reason='manual_exclusion'` and `notes=''` | Missing justification for human exclusion |

## Boundaries

- **NRR- is dry-lab only.** `dry_lab_only` is always True.
- **NRR- does not prove biological failure.** It records a computational or human filter decision.
- **Negative results are valuable.** Every NRR- is a calibration signal; do not discard or omit them.
- **`rejection_is_final=False` records may be revised.** They should not be indexed in NAS- until finalized.

## CLI

```bash
openamp-foundry negative-result-entry-check '{"nrr_id": "NRR-001", ...}'
```

Returns `VALID` or `INVALID` with any errors and warnings.

## Relationship to Other Schemas

```
NRR-  ←── NAS- (NegativeResultArchiveSummary indexes NRR- ids)
NRR-  ←── FCR- (FailedCandidateBatchReport references RJR- + NAS-, NAS- references NRR-)
RJR-  ──→  FCR- (batch-level failure summary)
```

NRR- is the foundation. NAS- is the batch index. FCR- is the aggregated report.

# Failed Candidate Batch Report Guide

## Purpose

A `FailedCandidateBatchReport` (FCR-) summarizes all failed candidates from a
screening batch. It links `RejectionReasonEntry` (RJR-) records and the
`NegativeResultArchiveSummary` (NAS-) into a single auditable report, making
failed batches reviewable and enabling calibration loop learning.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fcr_id` | str | Yes | Unique ID, must start with `FCR-` |
| `pipeline_version` | str | Yes | Pipeline version at report time |
| `batch_id` | str | Yes | Which batch this report covers |
| `report_date` | str | Yes | ISO YYYY-MM-DD report date |
| `total_candidates_screened` | int | Yes | Must be >= 1 |
| `failed_candidate_count` | int | Yes | Must be >= 0 and <= total |
| `failure_rate` | float | Yes | Must be in [0.0, 1.0], consistent with counts |
| `top_rejection_reasons` | List[str] | Yes | From controlled vocabulary |
| `rejection_reason_ids` | List[str] | Yes | Each must start with `RJR-` |
| `negative_result_archive_id` | str | Yes | Must start with `NAS-` if provided |
| `report_notes` | str | Yes | Context notes (max 400 chars) |
| `reviewer` | str | Yes | Human who reviewed the batch report |
| `dry_lab_only` | bool | No | Default `True` |

## Validation rules

1. `fcr_id` must start with `FCR-`
2. `pipeline_version`, `batch_id`, `reviewer` must not be empty
3. `report_date` must be ISO format `YYYY-MM-DD`
4. `total_candidates_screened` >= 1
5. `failed_candidate_count` in [0, `total_candidates_screened`]
6. `failure_rate` in [0.0, 1.0]
7. `failure_rate` consistent with counts (tolerance 0.01)
8. `top_rejection_reasons` all from controlled vocabulary
9. All `rejection_reason_ids` start with `RJR-`
10. `negative_result_archive_id` starts with `NAS-` if non-empty
11. `report_notes` at most 400 characters

## Warnings

- Empty `rejection_reason_ids` — link RJR- records for each failed candidate
- Empty `negative_result_archive_id` — link the NAS- archive for this batch
- `failure_rate = 1.0` — all candidates failed; review screening thresholds
- Empty `report_notes` — document the batch context

## Rejection reason vocabulary

See `RejectionReasonEntry` (RJR-) guide for the full taxonomy of valid stages and reasons.

## Honest boundaries

- This report summarizes dry-lab screening rejections only.
- `failure_rate` is computed from predicted scores, not wet-lab results.
- A high failure rate may indicate threshold miscalibration — use RJR records to investigate.

## CLI usage

```bash
openamp-foundry failed-candidate-batch-report-check \
  --entry-json '{"fcr_id":"FCR-001","pipeline_version":"v0.10.11","batch_id":"BATCH-001","report_date":"2026-07-10","total_candidates_screened":10,"failed_candidate_count":4,"failure_rate":0.4,"top_rejection_reasons":["toxicity_risk"],"rejection_reason_ids":["RJR-001"],"negative_result_archive_id":"NAS-001","report_notes":"Batch summary.","reviewer":"Dr. Smith"}' \
  --format text
```

# Negative Result Archive Summary Guide

## Purpose

A `NegativeResultArchiveSummary` (NAS-) is an index record that validates a batch
of `NegativeResultRecord` (NRR-) entries is complete and ready for long-term archiving.
It enforces that all negative results from a batch are captured and confirmed before
the batch is marked as archived — preventing silent gaps in the failure record.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `nas_id` | str | Yes | Unique ID, must start with `NAS-` |
| `pipeline_version` | str | Yes | Pipeline version at archive time |
| `batch_id` | str | Yes | Which batch this archive covers |
| `archive_date` | str | Yes | ISO YYYY-MM-DD date of archiving |
| `negative_result_count` | int | Yes | Must equal `len(negative_result_ids)` |
| `negative_result_ids` | List[str] | Yes | All NRR- IDs in this archive |
| `completeness_confirmed` | bool | Yes | Must be `True` — all results captured |
| `all_results_have_reason` | bool | Yes | Must be `True` — every NRR has a reason |
| `archive_notes` | str | Yes | Context notes (max 400 chars) |
| `reviewer` | str | Yes | Human who confirmed archive completeness |
| `dry_lab_only` | bool | No | Default `True` |

## Validation rules

1. `nas_id` must start with `NAS-`
2. `pipeline_version`, `batch_id`, `reviewer` must not be empty
3. `archive_date` must be ISO format `YYYY-MM-DD`
4. `negative_result_count` must be >= 0
5. `len(negative_result_ids)` must equal `negative_result_count`
6. All entries in `negative_result_ids` must start with `NRR-`
7. `completeness_confirmed` must be `True`
8. `all_results_have_reason` must be `True`
9. `archive_notes` must be at most 400 characters

## Warnings

- `negative_result_count = 0` — unusual; confirm all results were tracked
- Empty `archive_notes` — document the archive scope
- Count > 50 — large archives warrant extra curation review

## Honest boundaries

- A NAS record confirms that the archive INDEX is complete, not that all NRR entries
  individually pass validation. Always run `openamp-foundry negative-result-check`
  on each NRR before creating the NAS.
- `completeness_confirmed=True` is a human attestation, not an automated cross-check.

## CLI usage

```bash
openamp-foundry negative-result-archive-check \
  --entry-json '{"nas_id":"NAS-001","pipeline_version":"v0.10.10","batch_id":"BATCH-001","archive_date":"2026-07-10","negative_result_count":2,"negative_result_ids":["NRR-001","NRR-002"],"completeness_confirmed":true,"all_results_have_reason":true,"archive_notes":"Batch 1 archive.","reviewer":"Dr. Smith"}' \
  --format text
```

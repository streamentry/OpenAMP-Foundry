# Pipeline Decision Audit Entry Guide

A *pipeline decision audit entry* records each significant decision made during candidate
ranking, filtering, or selection — with the rationale, evidence level, and alternatives
considered. This guide defines the schema, validation rules, and honest-use constraints.

## Purpose

External auditors reviewing a preprint or evidence package need to:
- understand which filters were applied and why,
- verify that threshold choices were pre-specified rather than post-hoc,
- confirm that rejected candidates were documented, not silently dropped,
- trace each decision back to a specific pipeline version and reviewer.

## Required fields

| Field | Type | Constraint |
|---|---|---|
| `audit_id` | str | Must start with `"AUD-"` |
| `batch_id` | str | Non-empty |
| `pipeline_version` | str | Non-empty |
| `decision_date` | str | ISO 8601 `YYYY-MM-DD` |
| `decision_type` | str | One of `VALID_DECISION_TYPES` |
| `decision_description` | str | Non-empty, ≤ 500 characters |
| `rationale` | str | Non-empty, ≤ 1000 characters |
| `alternatives_considered` | list[str] | May be empty |
| `affected_candidate_count` | int | ≥ 0 |
| `evidence_level` | int | 1 – 6 |
| `pre_specified` | bool | Required field |
| `reviewer` | str | Non-empty |
| `dry_lab_only` | bool | Must be `True` |

## Valid decision types

`filter_applied`, `threshold_chosen`, `candidate_ranked`, `candidate_rejected`,
`benchmark_updated`, `safety_flag_applied`, `calibration_adjusted`

## Warnings

- `pre_specified` is `False` — warning: post-hoc decision; document justification carefully.
- `alternatives_considered` is empty — warning: no alternatives documented; consider recording what else was considered.
- `evidence_level <= 2` — warning: low evidence level for this decision.
- `affected_candidate_count == 0` — warning: decision affected no candidates; verify this is intentional.

## How to validate

```bash
make pipeline-decision-audit-check
# or
openamp-foundry pipeline-decision-audit-check \
  --entry-json '{"audit_id":"AUD-001","batch_id":"BATCH-001","pipeline_version":"0.8.9","decision_date":"2026-07-09","decision_type":"filter_applied","decision_description":"Applied hemolysis fraction filter at threshold 0.15.","rationale":"Threshold pre-specified in BENCHMARK_GOVERNANCE.md based on Wave 0 data.","alternatives_considered":["threshold 0.10","threshold 0.20"],"affected_candidate_count":47,"evidence_level":4,"pre_specified":true,"reviewer":"alice","dry_lab_only":true}' \
  --format text
```

## Honest-use boundary

Pipeline decision audit entries are dry-lab records. They document computational choices,
not experimental outcomes. A well-audited decision does not imply the selected candidates
are biologically active.

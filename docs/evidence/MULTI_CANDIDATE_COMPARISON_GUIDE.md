# Multi-Candidate Comparison Guide

A *multi-candidate comparison* is a structured record that compares the key predicted
properties of two or more candidates from the same batch side-by-side. This enables
publication-ready supplementary tables and supports consistent external review.

## Purpose

When nominating multiple candidates from a single batch, reviewers need to:
- see how candidates differ across predicted properties,
- confirm that comparison criteria are consistent across all candidates,
- verify that the top-ranked candidate has a defensible advantage over runners-up.

## Required fields

| Field | Type | Constraint |
|---|---|---|
| `comparison_id` | str | Must start with `"CMP-"` |
| `batch_id` | str | Non-empty |
| `pipeline_version` | str | Non-empty |
| `comparison_date` | str | ISO 8601 `YYYY-MM-DD` |
| `candidate_ids` | list[str] | ≥ `MINIMUM_CANDIDATES` (2) entries |
| `comparison_criteria` | list[str] | ≥ `MINIMUM_CRITERIA` (2) entries |
| `top_candidate_id` | str | Must be in `candidate_ids` |
| `top_candidate_rationale` | str | Non-empty, ≤ 500 characters |
| `evidence_level` | int | 1 – 6 |
| `reviewer` | str | Non-empty |
| `dry_lab_only` | bool | Must be `True` |

## Minimum requirements

- At least 2 candidates must be compared (`MINIMUM_CANDIDATES = 2`).
- At least 2 comparison criteria must be stated (`MINIMUM_CRITERIA = 2`).
- The top candidate must appear in the `candidate_ids` list.

## Valid evidence levels

1 – 6 (from PROOF_LADDER.md)

## Warnings

- `evidence_level <= 2` — warning: low evidence; comparison may not be reliable.
- `len(candidate_ids) > 10` — warning: large candidate set; consider splitting into sub-groups.
- `len(comparison_criteria) < 3` — warning: fewer than 3 criteria; comparison may lack depth.

## How to validate

```bash
make multi-candidate-comparison-check
# or
openamp-foundry multi-candidate-comparison-check \
  --entry-json '{"comparison_id":"CMP-001","batch_id":"BATCH-001","pipeline_version":"0.8.7","comparison_date":"2026-07-09","candidate_ids":["AMP-001","AMP-002","AMP-003"],"comparison_criteria":["predicted_mic","hemolysis_fraction","selectivity_index"],"top_candidate_id":"AMP-001","top_candidate_rationale":"Highest selectivity index with lowest hemolysis fraction.","evidence_level":4,"reviewer":"alice","dry_lab_only":true}' \
  --format text
```

## Honest-use boundary

Multi-candidate comparisons are dry-lab outputs. Predicted property rankings do not
imply experimental superiority. Wet-lab results may differ substantially from predictions.

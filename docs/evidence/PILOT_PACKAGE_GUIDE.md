# Pilot Package Completeness Guide

A *pilot package* is the complete evidence bundle submitted to an external collaborating lab
before any synthesis or assay work begins. This guide defines what must be present, how to
validate completeness, and the honesty constraints that govern every package.

## Purpose

Pilot packages exist so external reviewers can:
- verify the provenance and evidence level of each candidate,
- confirm safety flags were checked, and
- reproduce the prioritisation logic from raw predictions.

A package is only *ready to submit* when its completeness score reaches the threshold
defined in `pilot_package.py` (`READINESS_SCORE_THRESHOLD = 0.80`).

## Required fields

| Field | Type | Constraint |
|---|---|---|
| `package_id` | str | Must start with `"PKG-"` |
| `batch_id` | str | Non-empty |
| `submission_date` | str | ISO 8601 `YYYY-MM-DD` |
| `pipeline_version` | str | Non-empty |
| `included_artifacts` | list[str] | ≥ `MINIMUM_REQUIRED_ARTIFACTS` (3); must cover all `MANDATORY_ARTIFACT_TYPES` |
| `missing_artifacts` | list[str] | May be empty; each entry should name an absent artifact type |
| `reviewer` | str | Non-empty |
| `approver` | str | Non-empty |
| `completeness_score` | float | 0.0 – 1.0 |
| `ready_to_submit` | bool | Must be `False` when `completeness_score < READINESS_SCORE_THRESHOLD` |
| `dry_lab_only` | bool | Must be `True` |

## Mandatory artifact types

The following artifact types must appear in `included_artifacts` for a package to pass:

| Artifact type | Why required |
|---|---|
| `selection_rationale` | Documents why each candidate was chosen. |
| `batch_priority` | Documents synthesis-wave rank with evidence level. |
| `evidence_certificate` | Signed evidence bundle for the batch. |

## Valid artifact types

`batch_priority`, `benchmark_card`, `candidate_manifest`, `evidence_certificate`,
`model_card`, `safety_assessment`, `selection_rationale`, `uncertainty_report`

## Warnings

- `completeness_score < 0.80` and `ready_to_submit=True` — hard error.
- `missing_artifacts` non-empty — warning: package has gaps.
- `completeness_score < 0.90` — warning: consider completing optional artifacts.
- reviewer equals approver — warning: same person reviewed and approved.

## How to validate

```bash
make pilot-package-check
# or
openamp-foundry pilot-package-check \
  --entry-json '{"package_id":"PKG-001","batch_id":"BATCH-001","submission_date":"2026-07-09","pipeline_version":"0.8.1","included_artifacts":["selection_rationale","batch_priority","evidence_certificate"],"missing_artifacts":[],"reviewer":"alice","approver":"bob","completeness_score":1.0,"ready_to_submit":true,"dry_lab_only":true}' \
  --format text
```

## Honest-use boundary

Pilot packages are dry-lab outputs. The completeness score is a documentation metric,
not a biological confidence score. A complete package does not imply experimental success.

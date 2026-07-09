# Preprint Evidence Bundle Guide

A *preprint evidence bundle* ties together all Phase K artifacts for a specific batch
into a single structured record that can be submitted alongside a scientific preprint.
This guide defines what a bundle must contain, how to validate it, and the honesty
constraints that apply.

## Purpose

Before submitting a preprint describing a computationally-nominated antimicrobial peptide
family, the evidence bundle ensures that:
- all K-phase artifacts (selection rationale, batch priority, pilot package, uncertainty reports)
  are referenced,
- the claimed evidence level is consistent with actual artifacts,
- the bundle passes structural review before public release.

## Required fields

| Field | Type | Constraint |
|---|---|---|
| `bundle_id` | str | Must start with `"BND-"` |
| `batch_id` | str | Non-empty |
| `pipeline_version` | str | Non-empty |
| `submission_date` | str | ISO 8601 `YYYY-MM-DD` |
| `title` | str | Non-empty, ≤ 300 characters |
| `artifact_ids` | list[str] | ≥ `MINIMUM_ARTIFACTS` (3) entries |
| `evidence_level` | int | 1 – 6 (from PROOF_LADDER.md) |
| `preprint_doi` | str | May be empty (DOI assigned after submission) |
| `contact_email` | str | Non-empty |
| `release_approved` | bool | Must be `True` for a valid bundle |
| `dry_lab_only` | bool | Must be `True` |

## Minimum artifact types

At least 3 artifact IDs must be provided. The bundle does not enforce specific artifact
types — it enforces count — because artifact IDs are opaque references tracked in the
pilot package system.

## Evidence level

Use the same 1–6 scale as PROOF_LADDER.md:
1. Sequence only
2. Physicochemical
3. Computational model
4. Ensemble
5. Virtual assay
6. Cross-validated virtual assay

A preprint with evidence level 1 or 2 warrants a warning.

## Warnings

- `evidence_level <= 2` — warning: low evidence level; reviewers should apply extra scrutiny.
- `preprint_doi` empty — warning: DOI not yet assigned; update before final release.
- `len(artifact_ids) < 5` — warning: fewer than 5 artifacts; consider adding uncertainty reports and calibration records.

## How to validate

```bash
make preprint-bundle-check
# or
openamp-foundry preprint-bundle-check \
  --entry-json '{"bundle_id":"BND-001","batch_id":"BATCH-001","pipeline_version":"0.8.4","submission_date":"2026-07-09","title":"Computational nomination of AMP candidates from the OpenAMP Foundry","artifact_ids":["SEL-001","PRI-001","PKG-001","UQ-001","CAL-001"],"evidence_level":4,"preprint_doi":"10.1101/2026.07.09.000001","contact_email":"research@openamp.org","release_approved":true,"dry_lab_only":true}' \
  --format text
```

## Honest-use boundary

Preprint evidence bundles describe computational nominations, not experimental validations.
The bundle does not imply experimental success. Wet-lab validation results must be reported
separately and must not be attributed to the pipeline.

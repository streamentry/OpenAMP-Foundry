# Pilot Evidence Package Guide

## Purpose

A Pilot Evidence Package (PEP) is the external export artifact for a pilot candidate
batch.  It bundles references to all required evidence artifacts and validates that
the package is complete and cleared before it can be shared with an external lab
partner.

## Required evidence chain

A complete PEP must reference:

| Artifact | Prefix | Phase | What it documents |
|---|---|---|---|
| CalibrationCycleSummary | CCS- | P5 | Full calibration feedback loop |
| BatchSelectionProposal | BSP- | P1 | Why these candidates were selected |
| PilotBatchSafetyClearance | PSC- | P4 | Safety review and clearance |
| PreRegistrationEntry | PRE- | N1 | Pre-committed experiment plan |
| BaselineComparisonManifest | BCM- | N3 | Evidence pipeline beats baselines |

## Completeness constraint

`is_complete=True` requires `missing_artifacts=[]`.
`is_complete=False` requires `missing_artifacts` to be non-empty.

Incomplete packages can be saved as work-in-progress but cannot be released
for external review.

## Safety constraint

`cleared_for_synthesis=True` is required.  The referenced PSC must have cleared
the batch.  A package without safety clearance cannot be marked as ready for
external sharing.

## Schema fields

| Field | Type | Description |
|---|---|---|
| `pep_id` | str | Must start with `PEP-` |
| `pipeline_version` | str | Pipeline version at package creation |
| `ccs_id` | str | Must start with `CCS-` |
| `bsp_id` | str | Must start with `BSP-` |
| `psc_id` | str | Must start with `PSC-` |
| `pre_registration_id` | str | Must start with `PRE-` |
| `baseline_comparison_id` | str | Must start with `BCM-` |
| `candidate_count` | int | >= 1 |
| `cleared_for_synthesis` | bool | Must be True |
| `is_complete` | bool | True iff missing_artifacts is empty |
| `missing_artifacts` | List[str] | Empty if complete |
| `package_notes` | str | Max 400 chars |
| `reviewer` | str | Who prepared and approved the package |
| `dry_lab_only` | bool | True if no real experimental data in this package |

## Honest boundaries

- A PEP is a reference index, not a data container. The artifacts it references
  must be independently validated.
- `cleared_for_synthesis=True` reflects the PSC gate — it is a computational
  safety check, not wet-lab confirmation.
- `is_complete=True` means all required artifact IDs are present. It does not
  validate the quality of those artifacts.
- `dry_lab_only=True` packages must clearly communicate to lab partners that
  no experimental validation has been performed — candidates are computational
  nominations only.

## Warnings

The validator emits warnings (not errors) for:

- `dry_lab_only=True` with `is_complete=True` — lab partners must be informed
  this is a computational screening package.
- `candidate_count=1` — minimal diversity; consider larger batch.

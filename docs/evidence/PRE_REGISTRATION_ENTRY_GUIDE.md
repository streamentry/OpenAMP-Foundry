# Pre-Registration Entry Guide

## Purpose

A Pre-Registration Entry (PRE) documents the experimental plan that is locked BEFORE
any wet-lab experiment begins. It enforces the pre-commitment discipline that makes the
evidence trail auditable: the hypothesis, primary endpoint, and candidate list must be
committed before results are observed — preventing post-hoc hypothesis adjustment
(HARKing: Hypothesizing After Results are Known).

A PRE entry is referenced by the Pilot Evidence Package (PEP) via `pre_registration_id`.
A PEP cannot claim completeness without a valid PRE reference.

## Required fields

| Field | Type | Constraint |
|---|---|---|
| `pre_id` | str | Must start with `PRE-` |
| `pipeline_version` | str | Non-empty |
| `experiment_title` | str | Non-empty; plain language description |
| `hypothesis` | str | Non-empty; falsifiable claim |
| `primary_endpoint` | str | Non-empty; measurable outcome |
| `candidate_ids` | List[str] | At least 1 candidate |
| `positive_control_id` | Optional[str] | Recommended |
| `negative_control_id` | Optional[str] | Recommended |
| `registered_date` | str | ISO format YYYY-MM-DD |
| `registration_status` | str | `submitted`, `approved`, or `rejected` |
| `registrar` | str | Non-empty; who accepted the registration |
| `notes` | str | Max 400 chars |
| `reviewer` | str | Who prepared this record |
| `dry_lab_only` | bool | Default True |

## Registration statuses

- `submitted` — plan filed, pending review
- `approved` — plan accepted; experiments may begin
- `rejected` — plan rejected; reason in notes; preserved for audit trail

## Honest boundaries

- Pre-registration prevents HARKing but does not guarantee quality.
- `approved` status does not mean results will be positive.
- `dry_lab_only=True` entries document computational screening plans,
  not wet-lab commitments.
- Rejected entries MUST be preserved — they are part of the audit trail.

## Warnings

The validator emits warnings (not errors) for:

- `approved` with `dry_lab_only=True` — confirm experiment type
- No positive control — reduces result interpretability
- No negative control — reduces result interpretability
- Single candidate — limited statistical power

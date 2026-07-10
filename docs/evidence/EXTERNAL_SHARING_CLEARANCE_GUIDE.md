# External Sharing Clearance Guide

## Purpose

An `ExternalSharingClearance` (ESC-) records the formal event of sharing a
`PilotEvidencePackage` with an external lab partner. It is the final release
gate in Phase Q — the moment that transforms an internal dry-lab artifact into
an externally shared package.

No PEP should leave the foundry without an ESC record.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `esc_id` | str | Yes | Unique ID, must start with `ESC-` |
| `pipeline_version` | str | Yes | Version of the pipeline that produced the PEP |
| `pep_id` | str | Yes | Which PEP is being shared (must start with `PEP-`) |
| `pre_id` | str | Yes | Linked pre-registration (must start with `PRE-`) |
| `external_lab_token` | str | Yes | Anonymized partner token — no PII |
| `sharing_date` | str | Yes | ISO YYYY-MM-DD date of sharing |
| `caveat_confirmed` | bool | Yes | Must be `True` — dry-lab caveat was communicated |
| `dry_lab_only_acknowledged` | bool | Yes | Must be `True` — partner acknowledged dry-lab status |
| `sharing_purpose` | str | Yes | `pilot_experiment`, `peer_review`, or `collaboration` |
| `sharing_notes` | str | Yes | Context notes (max 400 chars) |
| `reviewer` | str | Yes | Name of the human who authorized this sharing |
| `dry_lab_only` | bool | No | Default `True` — always True for this schema |

## Validation rules

1. `esc_id` must start with `ESC-`
2. `pep_id` must start with `PEP-`
3. `pre_id` must start with `PRE-`
4. `pipeline_version`, `external_lab_token`, `reviewer` must not be empty
5. `sharing_date` must be ISO format `YYYY-MM-DD`
6. `caveat_confirmed` must be `True`
7. `dry_lab_only_acknowledged` must be `True`
8. `sharing_purpose` must be one of `{pilot_experiment, peer_review, collaboration}`
9. `sharing_notes` must be at most 400 characters

## Warnings

- Empty `sharing_notes` — document the context
- `sharing_purpose = pilot_experiment` — extra reminder to confirm safety clearance with partner
- `sharing_purpose = collaboration` with no notes — document scope

## Sharing purposes

| Purpose | When to use |
|---------|-------------|
| `pilot_experiment` | Package is shared for actual wet-lab testing |
| `peer_review` | Package is shared for scientific peer review only |
| `collaboration` | Package is shared for joint research without immediate wet-lab commitment |

## Honest boundaries

- An ESC record does NOT guarantee the external partner will perform the experiment.
- An ESC record does NOT upgrade the proof level — all contents remain dry-lab-only.
- The `external_lab_token` must never contain PII (names, emails, institutions directly identifying individuals).
- An ESC with `caveat_confirmed=False` will always fail validation.

## CLI usage

```bash
openamp-foundry external-sharing-clearance-check \
  --entry-json '{"esc_id":"ESC-001","pipeline_version":"v0.10.8","pep_id":"PEP-001","pre_id":"PRE-001","external_lab_token":"LAB-A","sharing_date":"2026-07-10","caveat_confirmed":true,"dry_lab_only_acknowledged":true,"sharing_purpose":"pilot_experiment","sharing_notes":"MIC validation run.","reviewer":"Dr. Smith"}' \
  --format text
```

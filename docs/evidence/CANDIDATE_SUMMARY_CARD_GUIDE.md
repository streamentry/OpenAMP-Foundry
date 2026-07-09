# Candidate Summary Card Guide

A *candidate summary card* is a publication-ready, per-candidate structured record
that consolidates the key computational properties, evidence level, safety flags,
and selection rationale for a single candidate into a reviewable snapshot.

## Purpose

Summary cards allow:
- external reviewers to quickly assess individual candidates without reading the full evidence package,
- authors to generate structured supplementary tables for preprints, and
- downstream tooling to render consistent candidate reports.

## Required fields

| Field | Type | Constraint |
|---|---|---|
| `card_id` | str | Must start with `"CRD-"` |
| `candidate_id` | str | Non-empty |
| `batch_id` | str | Non-empty |
| `pipeline_version` | str | Non-empty |
| `sequence` | str | Non-empty, only standard amino acid letters (A-Z, no B/J/O/U/X/Z) |
| `sequence_length` | int | Must equal `len(sequence)` |
| `evidence_level` | int | 1 – 6 |
| `predicted_activity` | str | One of `VALID_ACTIVITY_LABELS` |
| `safety_flags` | list[str] | May be empty; each entry is a named safety concern |
| `selection_rationale_id` | str | Must start with `"SEL-"` |
| `reviewer` | str | Non-empty |
| `dry_lab_only` | bool | Must be `True` |

## Valid activity labels

`high_activity`, `moderate_activity`, `low_activity`, `inactive`, `uncertain`

## Valid amino acid letters

Standard one-letter codes: A C D E F G H I K L M N P Q R S T V W Y
(B, J, O, U, X, Z are excluded)

## Warnings

- `evidence_level <= 2` — warning: low evidence; apply extra scrutiny.
- `len(safety_flags) > 0` — warning: safety concerns are flagged; review before synthesis.
- `predicted_activity == "uncertain"` — warning: activity is uncertain; prioritize candidates with clearer predictions.
- `sequence_length > 50` — warning: long peptide; synthesis cost may be high.

## How to validate

```bash
make candidate-summary-card-check
# or
openamp-foundry candidate-summary-card-check \
  --entry-json '{"card_id":"CRD-001","candidate_id":"AMP-001","batch_id":"BATCH-001","pipeline_version":"0.8.6","sequence":"KWKLFKKIEKVGQNIRDGIVKAGPAVADPQGRPVPVPVDPVDPVD","sequence_length":45,"evidence_level":4,"predicted_activity":"high_activity","safety_flags":[],"selection_rationale_id":"SEL-001","reviewer":"alice","dry_lab_only":true}' \
  --format text
```

## Honest-use boundary

Candidate summary cards are dry-lab outputs. Predicted activity and safety flags are
computational estimates, not experimental results. They must not be presented as
experimental measurements or used to make clinical or safety decisions.

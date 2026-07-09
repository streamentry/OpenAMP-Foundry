# Claim-to-Evidence Mapper Guide

## Purpose

The claim-to-evidence mapper records which artifacts support each scientific
claim made by the pipeline. Every claim must trace to at least one artifact.
External auditors use this map to verify that claims are not free-floating.

## Schema Fields

| Field | Type | Description |
|---|---|---|
| mapping_id | str | Unique identifier (prefix "CEM-") |
| batch_id | str | Batch this mapping belongs to |
| pipeline_version | str | Pipeline version string |
| claim_text | str | The claim being made (max 500 chars) |
| claim_type | str | Category of claim (see valid types) |
| supporting_artifact_ids | list[str] | IDs of artifacts that support this claim |
| evidence_level | int | 1–6 evidence hierarchy level |
| pre_specified | bool | True if claim was pre-specified before analysis |
| reviewer | str | Reviewer who validated this mapping |
| dry_lab_only | bool | Always True for computational claims |

## Valid Claim Types

- `activity_prediction` — predicted antimicrobial activity
- `calibration_statement` — statements about model calibration
- `novelty_claim` — claim about sequence novelty vs. known AMPs
- `performance_comparison` — comparison against a baseline or benchmark
- `reproducibility_claim` — claim that results can be reproduced
- `safety_assessment` — claims about toxicity/hemolysis/dual-use risk
- `selection_rationale` — rationale for selecting a candidate

## Validation Rules

1. mapping_id must start with "CEM-"
2. claim_text must not be empty and must not exceed 500 characters
3. claim_type must be one of the valid types listed above
4. supporting_artifact_ids must contain at least 1 artifact ID
5. evidence_level must be between 1 and 6
6. reviewer must not be empty
7. dry_lab_only must be True (computational claims only)

## Warning Conditions

- Post-hoc claim: pre_specified=False → warn that claim may be exploratory
- Weak evidence: evidence_level <= 2 → warn that evidence is limited
- Single artifact: exactly 1 supporting artifact → warn to seek corroboration
- Long claim text: claim_text > 300 chars → warn for conciseness

## Honest Use Boundary

A claim-to-evidence mapping records the *computational* support for a claim.
It does not imply biological validity. Claims mapped here are dry-lab outputs
only. Do not use this schema to record claims from wet-lab experiments.

## CLI Usage

```bash
openamp-foundry claim-to-evidence-check --entry-json '{"mapping_id": "CEM-001", ...}' --format text
openamp-foundry claim-to-evidence-check --entry-json '{"mapping_id": "CEM-001", ...}' --format json
```

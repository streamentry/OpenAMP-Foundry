# CertificateClaimBoundary (CCB-) Guide

## Purpose

`CertificateClaimBoundary` documents what a certificate does NOT prove. It prevents
score-to-proof drift by requiring explicit enumeration of unsupported claim classes
before a certificate can be shared externally.

This is the negative complement of `ProofLadderLevelCertificate` (PLC-): while PLC-
asserts what level IS supported, CCB- explicitly asserts what is NOT.

## Claim Classes (8 total)

| Class | Description |
|-------|-------------|
| `biological_activity` | Actual in-vitro antimicrobial activity |
| `human_safety` | Safety for human use or administration |
| `clinical_utility` | Usefulness in clinical settings |
| `animal_efficacy` | Efficacy in animal models |
| `therapeutic_indication` | Indication for therapeutic use |
| `regulatory_approval` | Any regulatory or market approval |
| `mechanism_proof` | Proven mechanism of action |
| `resistance_profile` | Actual resistance/susceptibility profile |

## Schema Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ccb_id` | str | yes | Unique identifier, must start with `CCB-` |
| `pipeline_version` | str | yes | Pipeline version |
| `certificate_id` | str | yes | Source certificate ID |
| `candidate_id` | str | yes | Candidate being assessed |
| `boundary_date` | str | yes | ISO date (YYYY-MM-DD) |
| `unsupported_claim_classes` | list | yes | ≥3 claim classes from controlled vocabulary |
| `boundary_statement` | str | yes | Human-readable statement (≤600 chars) |
| `dry_lab_only` | bool | yes | Must be True |
| `all_listed_classes_unsupported` | bool | yes | Must be True |
| `notes` | str | no | Additional context (≤300 chars) |

## Validation Rules

1. `ccb_id` starts with `CCB-`
2. `pipeline_version` non-empty
3. `certificate_id` non-empty
4. `candidate_id` non-empty
5. `boundary_date` is ISO date (YYYY-MM-DD)
6. `unsupported_claim_classes` non-empty
7. All listed classes in controlled vocabulary (8 values)
8. At least 3 valid claim classes listed
9. `boundary_statement` non-empty and ≤600 chars
10. `dry_lab_only` must be True
11. `all_listed_classes_unsupported` must be True
12. No duplicate claim classes
13. `notes` ≤300 chars

## Warnings

- Not all 8 claim classes listed: reports how many are missing
- `notes` empty: consider documenting context

## Integration

- Pairs with: `ProofLadderLevelCertificate` (PLC-) as negative complement
- Required for: external review packets, partner sharing
- Closes: Phase B B2 — score-to-proof drift prevention

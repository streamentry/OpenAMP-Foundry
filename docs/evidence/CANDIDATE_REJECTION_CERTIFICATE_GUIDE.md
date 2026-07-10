# Candidate Rejection Certificate Guide (CRC-)

## Purpose

A `CandidateRejectionCertificate` makes pipeline rejections first-class auditable artifacts.
When any gate rejects a candidate, a CRC- record documents: which gate, which reason, the evidence at time of rejection, and the proof-ladder level reached before rejection.

This closes the feedback loop: failures are as durable as passes.

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `crc_id` | str | Unique ID starting with `CRC-` |
| `pipeline_version` | str | Pipeline version at rejection time |
| `candidate_id` | str | ID of the rejected candidate |
| `sequence` | str | Amino acid sequence |
| `rejection_date` | str | ISO 8601 date |
| `rejection_gate` | str | Gate that triggered rejection (controlled vocab) |
| `rejection_reason` | str | Reason code (controlled vocab) |
| `evidence_summary` | str | Human-readable evidence at rejection |
| `proof_ladder_level_at_rejection` | str | Highest level reached before rejection |
| `dry_lab_only` | bool | Must be True |

## Optional Fields

| Field | Default | Description |
|-------|---------|-------------|
| `scores` | {} | Score dict at rejection time |
| `notes` | "" | Reviewer notes (max 400 chars) |

## Validation Rules

1. `crc_id` must start with `CRC-`
2. `pipeline_version` non-empty
3. `candidate_id` non-empty
4. `sequence` non-empty, standard amino acids only
5. `rejection_date` ISO 8601 format
6. `rejection_gate` in `VALID_REJECTION_GATES`
7. `rejection_reason` in `VALID_REJECTION_REASONS`
8. `evidence_summary` non-empty
9. `proof_ladder_level_at_rejection` in `VALID_PROOF_LADDER_LEVELS`
10. `dry_lab_only` must be True
11. `proof_ladder_level_at_rejection` capped at `multi_signal_candidate_evidence` when `dry_lab_only=True`
12. `scores` must be a dict
13. `notes` ≤400 characters

## Claim Safety

CRC- records are dry-lab artifacts. `dry_lab_only=True` is enforced.
The proof ladder is capped at `multi_signal_candidate_evidence` (level 4).

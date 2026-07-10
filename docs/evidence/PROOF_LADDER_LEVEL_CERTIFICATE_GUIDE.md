# ProofLadderLevelCertificate (PLC-) Guide

## Purpose

`ProofLadderLevelCertificate` makes the proof-ladder level claim machine-checkable.
Instead of a bare string in a certificate, a PLC- record creates a structured assertion
tying a specific candidate to a specific level with explicit evidence references and
unsupported-claims documentation.

## Proof-Ladder Levels (ordered by evidence strength)

| Level | Description | Dry-lab only? |
|-------|-------------|---------------|
| `valid_input` | Passes format validation | Yes |
| `reproducible_dry_lab_features` | Features reproducibly computed | Yes |
| `baseline_triaged` | Beats cheap heuristic baseline | Yes |
| `leakage_aware_benchmark` | Benchmark is split-clean | Yes |
| `multi_signal_candidate_evidence` | Multiple scorers agree (**dry-lab max**) | Yes |
| `expert_reviewed_assay_proposal` | Domain expert reviewed | No — human review required |
| `initial_qualified_assay_result` | First wet-lab result | No — human review required |
| `safety_adjusted_follow_up_signal` | Follow-up with safety adjustment | No |
| `independent_replication` | Independently replicated | No |
| `reusable_discovery_loop` | Reusable pipeline | No |

## Schema Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `plc_id` | str | yes | Unique identifier, must start with `PLC-` |
| `pipeline_version` | str | yes | Pipeline version |
| `candidate_id` | str | yes | Candidate being assessed |
| `certificate_id` | str | yes | Source certificate ID |
| `claimed_level` | str | yes | Claimed proof-ladder level |
| `evidence_type` | str | yes | Evidence type (controlled vocabulary) |
| `verifier_type` | str | yes | Who verified (controlled vocabulary) |
| `verification_date` | str | yes | ISO date (YYYY-MM-DD) |
| `supporting_artifact_ids` | list | yes | Non-empty list of supporting artifact IDs |
| `unsupported_claims` | str | yes | Explicit anti-overclaim statement (≤500 chars) |
| `human_review_required` | bool | yes | Required for levels ≥ expert_reviewed_assay_proposal |
| `human_review_completed` | bool | yes | Tracks completion status |
| `dry_lab_only` | bool | yes | Caps level at multi_signal_candidate_evidence |
| `notes` | str | no | Additional context (≤300 chars) |

## Validation Rules

1. `plc_id` starts with `PLC-`
2. `pipeline_version` non-empty
3. `candidate_id` non-empty
4. `certificate_id` non-empty
5. `claimed_level` in valid proof-ladder vocabulary (10 levels)
6. `evidence_type` in controlled vocabulary (4 values)
7. `verifier_type` in controlled vocabulary (5 values)
8. `verification_date` is ISO date (YYYY-MM-DD)
9. `supporting_artifact_ids` non-empty
10. `unsupported_claims` non-empty and ≤500 chars
11. `dry_lab_only=True` caps `claimed_level` at `multi_signal_candidate_evidence`
12. Levels ≥ `expert_reviewed_assay_proposal` require `human_review_required=True`
13. `human_review_required=True` but `human_review_completed=False` → warning (pending)
14. `notes` ≤300 chars

## Integration

- Source: built from `build_certificate()` output
- Feeds into: external review packets, release gates, audit trails
- Supersedes: bare `proof_ladder_level` string with structured evidence record

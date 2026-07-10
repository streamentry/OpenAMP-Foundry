# SyntheticBoundaryAuditRecord (SBR-) Guide

## Purpose

`SyntheticBoundaryAuditRecord` makes each enforcement of the synthetic results
policy an auditable artifact. It documents that the boundary between
dry-lab simulation and wet-lab proof is actively enforced — synthetic evidence
cannot raise a candidate's proof-ladder level.

## Proof-Ladder Boundary

| Level | Label | Synthetic evidence? |
|-------|-------|---------------------|
| 1 | computational nomination | Yes |
| 2 | virtual-assay support | Yes |
| 3 | in-silico ensemble agreement | Yes |
| **4** | **ex-vivo preliminary** | **No — wet-lab required** |
| 5 | in-vivo preliminary | No — wet-lab required |
| 6 | clinical evidence | No — wet-lab required |

## Schema Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sbr_id` | str | yes | Unique identifier, must start with `SBR-` |
| `pipeline_version` | str | yes | Pipeline version during audit |
| `batch_id` | str | yes | Batch identifier audited |
| `audit_date` | str | yes | ISO date (YYYY-MM-DD) of audit |
| `evidence_source` | str | yes | Source type (controlled vocabulary) |
| `total_candidates_checked` | int | yes | Candidates checked (≥1) |
| `total_violations` | int | yes | Candidates with invalid level proposals |
| `violation_rate` | float | yes | Fraction violated (consistency check, tol 0.01) |
| `blocked_upgrades` | int | yes | Violations that were blocked (in [0, total_violations]) |
| `max_proposed_ladder_level` | int | yes | Highest proposed level in batch (1-6) |
| `policy_enforced` | bool | yes | Must be True |
| `enforcement_outcome` | str | yes | Overall outcome (controlled vocabulary) |
| `summary` | str | yes | Narrative summary (≤400 chars) |
| `notes` | str | no | Additional context (≤300 chars) |

## Controlled Vocabularies

**evidence_source (4 values):**
- `synthetic`, `simulation`, `computational`, `mixed_synthetic_lab`

**enforcement_outcome (3 values):**
- `all_passed` — no violations found
- `violations_blocked` — violations found and blocked
- `violations_flagged` — violations found and flagged for review

## Validation Rules

1. `sbr_id` starts with `SBR-`
2. `pipeline_version` non-empty
3. `batch_id` non-empty
4. `audit_date` is ISO date (YYYY-MM-DD)
5. `evidence_source` in controlled vocabulary (4 values)
6. `total_candidates_checked` ≥ 1
7. `total_violations` in [0, total_candidates_checked]
8. `violation_rate` in [0.0, 1.0]
9. `violation_rate` consistent with total_violations/total_candidates_checked (tol 0.01)
10. `blocked_upgrades` in [0, total_violations]
11. `max_proposed_ladder_level` in [1, 6]
12. Synthetic-only sources cannot propose level ≥4 without recording violations
13. `policy_enforced` must be True
14. `enforcement_outcome` in controlled vocabulary (3 values)
15. `summary` non-empty and ≤400 chars
16. `notes` ≤300 chars

## Warnings

- `violation_rate > 0.3`: high overclaim attempt rate — review batch scoring
- Violations flagged but not all blocked: verify enforcement_outcome
- `notes` empty: consider documenting enforcement context

## Integration

- Triggered after: synthetic score run on candidates
- Violations reference: `SyntheticResultPolicyCheck` (individual policy check)
- Feeds into: evidence audit trail, calibration health, external review packets

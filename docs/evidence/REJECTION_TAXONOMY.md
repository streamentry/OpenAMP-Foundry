# Rejection Reason Taxonomy

## Purpose

Standardized, machine-readable categories for why candidates are rejected by
the OpenAMP pipeline. Enables analysis of failure patterns across batches,
consistent archive entries, and evidence-aware claim boundaries for rejected
candidates.

## Schema

A machine-readable JSON Schema defines the taxonomy structure:

- **Source:** `schemas/rejection_taxonomy.schema.json`
- **Example:** `examples/rejection_taxonomy_example.json`

Every taxonomy entry includes: `code`, `category`, `label`, `description`,
`severity`, `evidence_impact`, `applies_at_stage`, and `related_reason_category`
(mapping to `schemas/negative_result_entry.schema.json`).

## Taxonomy hierarchy

Rejection reasons are grouped by pipeline stage. Each entry has a severity
and an evidence impact on the proof ladder.

### Pre-selection (before scoring)

| Code | Severity | Evidence impact | Description |
|------|:--------:|:---------------:|-------------|
| `PRE_SEQ_INVALID` | hard | claim_unsupported | Non-canonical amino acids or unparseable symbols |
| `PRE_LENGTH_OUT` | hard | claim_unsupported | Length outside configured range |
| `PRE_PATENT_NEAR` | soft | downgrade_by_1 | Similarity to a known reference exceeds novelty cutoff |

### Pipeline scoring

| Code | Severity | Evidence impact | Description |
|------|:--------:|:---------------:|-------------|
| `PIPE_ACTIVITY_LOW` | soft | downgrade_by_1 | Activity score below minimum gate threshold |
| `PIPE_SAFETY_LOW` | soft | downgrade_by_1 | Safety score below minimum threshold |
| `PIPE_NOVELTY_LOW` | soft | downgrade_by_1 | Novelty score below minimum threshold |
| `PIPE_SYNTHESIS_LOW` | soft | downgrade_by_1 | Synthesis feasibility below viability threshold |
| `PIPE_DISAGREEMENT_HI` | informational | no_impact | Scorer disagreement exceeds maximum tolerance |
| `PIPE_ENSEMBLE_LOW` | soft | downgrade_by_1 | Composite ensemble score below synthesis gate threshold |
| `PIPE_SIM_UNCERTAINTY` | informational | no_impact | Simulation proxy uncertainty exceeds 0.5 threshold |

### Diversity and selection

| Code | Severity | Evidence impact | Description |
|------|:--------:|:---------------:|-------------|
| `DIV_TOO_SIMILAR` | soft | no_impact | Near-duplicate of already-selected candidate |
| `DIV_FAMILY_CAP` | soft | no_impact | Per-family panel cap reached |
| `DIV_BUDGET` | informational | no_impact | Budget or scope limitation |

### Reviewer rejection

| Code | Severity | Evidence impact | Description |
|------|:--------:|:---------------:|-------------|
| `REV_EXPERT_REJECT` | hard | downgrade_by_2 | Qualified domain expert recommended against progression |
| `REV_SAFETY_CONCERN` | hard | downgrade_by_2 | Human safety reviewer flagged structural or dual-use concern |
| `REV_INSUFFICIENT` | soft | downgrade_by_1 | Evidence package does not meet minimum reviewer standards |

### Lab result

| Code | Severity | Evidence impact | Description |
|------|:--------:|:---------------:|-------------|
| `LAB_INACTIVE` | hard | downgrade_by_2 | Lab-confirmed inactive (MIC above cutoff) |
| `LAB_TOXIC` | hard | downgrade_by_2 | Lab-confirmed hemolytic or cytotoxic |
| `LAB_CONTROL_FAIL` | hard | claim_unsupported | Assay controls failed — batch invalidated |
| `LAB_SYNTHESIS_FAIL` | hard | downgrade_by_2 | Could not be synthesized at sufficient purity |

### Lifecycle

| Code | Severity | Evidence impact | Description |
|------|:--------:|:---------------:|-------------|
| `LIFECYCLE_SUPERSEDED` | informational | no_impact | Replaced by a higher-scoring or better-characterised candidate |
| `LIFECYCLE_WITHDRAWN` | informational | no_impact | Withdrawn for non-technical reasons (scope, budget, partner feedback) |

## Severity categories

| Severity | Meaning |
|----------|---------|
| `hard` | Final rejection. The candidate cannot proceed regardless of threshold adjustment. Requires new evidence to overturn. |
| `soft` | Conditional on current thresholds. A policy or threshold change could convert this to a pass. The rejection record should document the specific threshold. |
| `informational` | Context-dependent. The candidate was rejected for reasons external to its own merits (budget, diversity, uncertainty). May still be valid in a different context. |

## Evidence impact

| Impact | Meaning |
|--------|---------|
| `claim_unsupported` | No claim about this candidate can be made at any proof-ladder level. The input itself is invalid or the assay failed. |
| `downgrade_by_2` | The highest supportable proof-ladder level drops by 2. For example, from Level 4 (multi-signal candidate evidence) to Level 2 (baseline-triaged). |
| `downgrade_by_1` | The highest supportable proof-ladder level drops by 1. |
| `no_impact` | The rejection does not affect the candidate's claim level. The candidate remains valid at its current evidence level (e.g., diversity pruning). |

## Usage in tools

| Artifact | How the taxonomy is used |
|----------|--------------------------|
| `schemas/negative_result_entry.schema.json` | `reason_category` field maps to the taxonomy's top-level categories |
| Pipeline output JSONL | `known_failure_modes` field records the applying rejection codes |
| Failed-candidate report generator | Reads taxonomy to produce structured rejection summaries |
| Negative-result archive validator | Checks `reason_category` against allowed values |
| External review packet | Rejection codes and rationales are included for reviewed candidates |

## Cross-references

- `docs/evidence/TAXONOMY_EXCLUSION_REASONS.md` — Lightweight exclusion-reason table for selection workflows
- `docs/evidence/NEGATIVE_RESULT_ARCHIVE.md` — Archive format that stores rejection records
- `schemas/negative_result_entry.schema.json` — Rejection entry schema with reason_category enum
- `schemas/rejection_taxonomy.schema.json` — Machine-readable taxonomy schema

## Non-goals

This taxonomy does not cover:

- Wet-lab assay design decisions — see `docs/review/WET_LAB_HANDOFF.md`
- Human review deliberation format — see `docs/review/EXTERNAL_REVIEW_PACKET.md`
- Safety or dual-use review policy — see `docs/trust/SAFETY_DOC_AUDIT.md`
- Recalibration policy decisions — see `docs/evidence/CALIBRATION_POLICY.md`

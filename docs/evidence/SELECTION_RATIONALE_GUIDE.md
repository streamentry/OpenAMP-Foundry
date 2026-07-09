# Selection Rationale Guide

> **Scope:** Dry-lab only. No wet-lab or in-vivo claims.
> **Purpose:** Record WHY each candidate was selected for synthesis or further testing.
> External reviewers and future calibration runs need this to audit and challenge decisions.

---

## What Is a Selection Rationale?

A selection rationale (`SelectionRationaleEntry`) is a machine-validated record that
documents, for each selected candidate:

1. The evidence level (1–6 from `PROOF_LADDER.md`) supporting the selection.
2. What the pipeline's score was compared to (baseline comparison).
3. Which safety and quality flags were checked before selection.
4. Who made the selection decision and when.

## Required Fields

| Field | Description |
|---|---|
| `selection_id` | Unique ID, must start with `SEL-` |
| `batch_id` | The batch this selection belongs to |
| `candidate_id` | The specific candidate being selected |
| `pipeline_version` | Pipeline version used for scoring |
| `selection_date` | Date of selection (YYYY-MM-DD) |
| `evidence_level` | 1–6, must match `PROOF_LADDER.md` levels |
| `baseline_comparison` | Description of what the score was compared to |
| `primary_criterion` | Main reason this candidate was selected |
| `safety_flags_checked` | List of safety/quality flags that were verified |
| `reviewer` | Handle of the person or agent making the selection |
| `dry_lab_only` | Must be True — no wet-lab claims |

## Evidence Levels

| Level | Meaning |
|---|---|
| 1 | Sequence-only computational nomination |
| 2 | Multi-property computational nomination |
| 3 | Computational nomination with novelty filter |
| 4 | Computational nomination with calibration evidence |
| 5 | Computational + simulation evidence (experimental still required) |
| 6 | Experimental validation (requires human review before claim) |

Levels 5 and 6 require `dry_lab_only=True` to avoid overclaiming.

## How to Validate

```bash
make selection-rationale-check
```

or:

```bash
openamp-foundry selection-rationale-check \
  --entry-json '{"selection_id": "SEL-2026-001", ...}'
```

---

*This guide is machine-validated. See `src/openamp_foundry/evidence/selection_rationale.py`.*

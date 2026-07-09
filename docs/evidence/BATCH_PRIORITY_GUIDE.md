# Batch Experiment Priority Guide

> **Scope:** Dry-lab only. No wet-lab or in-vivo claims.
> **Purpose:** Record the prioritization rationale for each candidate in a synthesis batch.
> When lab capacity is limited, external collaborators need a machine-validated priority
> ranking with explicit rationale, evidence level, and synthesis complexity.

---

## What Is a Batch Priority Entry?

A `BatchPriorityEntry` records, for a single candidate within a batch:

1. Its priority rank among all candidates (1 = highest priority).
2. A 0–1 priority score summarizing the evidence and selection signals.
3. The evidence level (1–6 from `PROOF_LADDER.md`) supporting the selection.
4. Synthesis complexity estimate (low/medium/high).
5. Novelty tier relative to known AMPs (high/medium/low).
6. The primary rationale for the ranking.
7. Any disqualifying concerns that were considered and weighed.

## Required Fields

| Field | Description |
|---|---|
| `priority_id` | Unique ID, must start with `PRI-` |
| `batch_id` | The batch this priority entry belongs to |
| `candidate_id` | The specific candidate |
| `pipeline_version` | Pipeline version used for scoring |
| `priority_rank` | Integer ≥ 1 (1 = highest priority) |
| `priority_score` | Float 0.0–1.0 |
| `evidence_level` | 1–6, must match `PROOF_LADDER.md` |
| `synthesis_complexity` | `low`, `medium`, or `high` |
| `novelty_tier` | `high`, `medium`, or `low` |
| `primary_rationale` | Non-empty explanation of ranking |
| `dry_lab_only` | Must be True |

## How to Validate

```bash
make batch-priority-check
```

or:

```bash
openamp-foundry batch-priority-check \
  --entry-json '{\"priority_id\": \"PRI-2026-001\", ...}'
```

---

*This guide is machine-validated. See `src/openamp_foundry/evidence/batch_priority.py`.*

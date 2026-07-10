# Batch Experiment Priority Ranker Guide (BPR-)

## Purpose

A `BatchExperimentPriorityRanker` (BPR-) records the priority ordering of candidates
for the next synthesis wave. While a `CandidateSelectionRationale` (CSR-) documents
why candidates were selected, a BPR- records which should be synthesized first given
resource constraints and scientific priorities.

BPR- makes synthesis wave ordering explicit, auditable, and defensible to external
reviewers and lab partners.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bpr_id` | str | Yes | Unique ID, must start with `BPR-` |
| `pipeline_version` | str | Yes | Version of the pipeline that produced this ranking |
| `batch_id` | str | Yes | Batch being prioritized |
| `csr_id` | str | Yes | Candidate selection rationale (must start with `CSR-`) |
| `ranking_date` | str | Yes | ISO date (YYYY-MM-DD) of ranking decision |
| `priority_method` | str | Yes | Controlled vocabulary: how candidates were ranked |
| `top_priority_candidates` | List[str] | Yes | Ordered list of candidate IDs (at least 1) |
| `priority_rationale` | str | Yes | Why this ordering was chosen (≤400 chars) |
| `synthesis_wave` | int | Yes | Which synthesis wave this is (≥1) |
| `resource_constraint_considered` | bool | Yes | Whether resource constraints were factored in |
| `notes` | str | No | Additional context (≤300 chars) |

## Valid Vocabularies

### `priority_method`

| Value | Description |
|-------|-------------|
| `predicted_activity` | Ranked by predicted antimicrobial activity |
| `structural_diversity` | Ranked to maximize structural diversity in the wave |
| `cost_efficiency` | Ranked by synthesis cost per predicted benefit |
| `risk_stratified` | Ranked to hedge risk across confidence levels |
| `novelty_first` | Most novel candidates synthesized first |
| `expert_ranked` | Final ordering decided by domain expert |

## Validation Rules

1. `bpr_id` must start with `BPR-`
2. `pipeline_version` must be non-empty
3. `batch_id` must be non-empty
4. `csr_id` must start with `CSR-`
5. `ranking_date` must match `YYYY-MM-DD`
6. `priority_method` must be in valid set (6 values)
7. `top_priority_candidates` must contain at least one candidate
8. `priority_rationale` must be non-empty and ≤400 chars
9. `synthesis_wave` must be ≥1
10. `notes` must be ≤300 chars

## Warnings

| Condition | Warning |
|-----------|---------|
| `resource_constraint_considered=False` | Synthesis priority without resource constraints may be suboptimal |
| `priority_method='expert_ranked'` and `notes=''` | Expert ranking decisions should be documented |
| `synthesis_wave > 5` | Unusually high synthesis wave; verify intent |

## Boundaries

- **BPR- records priority ordering, not selection.** Use CSR- for selection rationale; use BPR- for ordering within a selected batch.
- **BPR- is computational input, not a wet-lab instruction.** The lab team decides actual synthesis scheduling; BPR- provides the recommended order.
- **`synthesis_wave` reflects the experiment sequence.** Wave 1 is the first synthesis; wave N is the N-th iteration.

## CLI

```bash
openamp-foundry batch-experiment-priority-ranker-check '{"bpr_id": "BPR-001", ...}'
```

Returns `VALID` or `INVALID` with any errors and warnings.

## Relationship to Other Schemas

```
CSR-  ──→  BPR-  (selection rationale is the basis for priority ranking)
BPR-  ──→  PPC-  (synthesis ordering is a pilot package component)
BPR-  ──→  PRE-  (pre-registration locks priority order before experiments)
```

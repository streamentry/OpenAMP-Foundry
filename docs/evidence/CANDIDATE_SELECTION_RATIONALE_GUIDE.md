# Candidate Selection Rationale Guide (CSR-)

## Purpose

A `CandidateSelectionRationale` (CSR-) records why specific candidates were selected
for a batch. It documents the selection strategy, ranking method, and selection
rationale, and enforces that the calibration gate was passed before selection was
authorized. This makes selection decisions auditable, reproducible, and usable as
calibration signal in future cycles.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `csr_id` | str | Yes | Unique ID, must start with `CSR-` |
| `pipeline_version` | str | Yes | Version of the pipeline that made the selection |
| `batch_id` | str | Yes | Identifier of the batch being selected |
| `bsp_id` | str | Yes | Batch selection proposal (must start with `BSP-`) |
| `selection_date` | str | Yes | ISO date (YYYY-MM-DD) of selection decision |
| `selection_strategy` | str | Yes | Controlled vocabulary: exploit/explore/diversity/mixed |
| `candidate_count` | int | Yes | Number of candidates selected (≥1) |
| `candidate_ids` | List[str] | Yes | Identifiers of selected candidates |
| `ranking_method` | str | Yes | How candidates were ranked/selected |
| `calibration_gate_passed` | bool | Yes | Must be True; gate must be passed before selection |
| `selection_rationale` | str | Yes | Human-readable rationale (≤400 chars) |
| `notes` | str | No | Additional context (≤300 chars) |

## Valid Vocabularies

### `selection_strategy`

| Value | Description |
|-------|-------------|
| `exploit` | Focus on highest-scoring candidates from current model |
| `explore` | Deliberately sample from lower-confidence regions |
| `diversity` | Maximize structural or sequence diversity |
| `mixed` | Combination of exploit and explore or diversity |

### `ranking_method`

| Value | Description |
|-------|-------------|
| `composite_score` | Ranked by composite score from multiple predictors |
| `diversity_filter` | Selected after diversity filtering |
| `novelty_weighted` | Score weighted by novelty vs known sequences |
| `expert_review` | Final selection by domain expert |
| `random_balanced` | Random sampling within strata |
| `calibration_guided` | Selection guided by calibration uncertainty |

## Validation Rules

1. `csr_id` must start with `CSR-`
2. `pipeline_version` must be non-empty
3. `batch_id` must be non-empty
4. `bsp_id` must start with `BSP-`
5. `selection_date` must match `YYYY-MM-DD`
6. `selection_strategy` must be in valid set (4 values)
7. `candidate_count` must be ≥1
8. `len(candidate_ids)` must equal `candidate_count`
9. `ranking_method` must be in valid set (6 values)
10. `calibration_gate_passed` must be True
11. `selection_rationale` must be non-empty and ≤400 chars
12. `notes` must be ≤300 chars

## Warnings

| Condition | Warning |
|-----------|---------|
| `candidate_count > 20` | Unusually large batch; verify intent |
| `ranking_method='random_balanced'` and `notes=''` | Random selection should be justified |
| `ranking_method='expert_review'` and `notes=''` | Expert review decisions should be documented |

## Boundaries

- **CSR- records computational selection, not biological prediction.** Selecting a candidate does not predict its activity.
- **`calibration_gate_passed` must be True.** The pipeline cannot select candidates without passing calibration. This is a hard enforcement of the calibration→selection dependency.
- **CSR- is retrospective.** It documents decisions already made; it does not authorize them.

## CLI

```bash
openamp-foundry candidate-selection-rationale-check '{"csr_id": "CSR-001", ...}'
```

Returns `VALID` or `INVALID` with any errors and warnings.

## Relationship to Other Schemas

```
BSP-  ──→  CSR-  (batch selection proposal authorizes the selection)
CSR-  ──→  PPC-  (selection rationale is a component of pilot completeness)
CSR-  ──→  PRE-  (pre-registration records the candidates selected here)
```

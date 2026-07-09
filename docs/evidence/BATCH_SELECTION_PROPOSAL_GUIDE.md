# Batch Selection Proposal Guide

## Purpose

A Batch Selection Proposal (BSP) documents the next-batch candidate selection
plan immediately after a Calibration Readiness Gate (CRG) passes.

The BSP enforces two things:

1. A batch can only be proposed when `gate_passed=True` — the pipeline
   cannot nominate candidates when calibration quality is insufficient.
2. The selection strategy (exploitation vs exploration fraction) is documented
   before selection, not after, preventing post-hoc rationalization.

## Key constraint

`gate_passed` in a BSP must always be `True`. A failed calibration gate
cannot generate a valid proposal. This links Phase O (Calibration Quality
Assurance) directly to Phase P (Batch Selection).

## Schema fields

| Field | Type | Description |
|---|---|---|
| `bsp_id` | str | Must start with `BSP-` |
| `pipeline_version` | str | Pipeline version at selection time |
| `gate_id` | str | Must start with `CRG-` — the passed gate |
| `gate_passed` | bool | Must be `True` |
| `candidate_ids` | List[str] | At least 1 candidate |
| `selection_strategy` | str | One of 5 valid strategies |
| `exploitation_fraction` | float | [0.0, 1.0] |
| `exploration_fraction` | float | [0.0, 1.0] |
| `max_brier_score_allowed` | float | [0.0, 1.0] |
| `proposal_notes` | str | Max 400 chars |
| `reviewer` | str | Who approved the proposal |
| `dry_lab_only` | bool | Default True |

## Selection strategies

| Strategy | Description |
|---|---|
| `exploitation` | Prefer high-scoring candidates with low uncertainty |
| `exploration` | Prefer candidates in under-sampled regions |
| `diversity` | Prefer structurally distinct candidates |
| `uncertainty_sampling` | Prefer candidates with highest prediction uncertainty |
| `hybrid` | Combination; exploitation + exploration fractions document the mix |

## Fraction constraint

`exploitation_fraction + exploration_fraction` must sum to 1.0 (within 0.001
tolerance). These fractions document the intended mix; the actual selection
algorithm may use any mechanism so long as the mix is documented here.

## Honest boundaries

- A BSP is a plan document. It does not guarantee the selected candidates
  will show activity — it documents the rationale for selection.
- The BSP does not validate that `gate_id` references a real CRG entry in the
  database; referential integrity requires a separate audit step.
- `dry_lab_only=True` by default. A BSP that results in wet-lab synthesis
  should carry `dry_lab_only=False` and must pass safety review before
  candidates are shared with a lab.
- Calibration gate passage at the time of the BSP does not guarantee the
  pipeline remains calibrated after batch execution.

## Warnings

The validator emits warnings (not errors) for:

- Pure exploitation (`exploitation_fraction ≥ 0.99`) — exploration helps
  avoid local optima.
- Single-candidate batch — diversity and calibration coverage may be reduced.
- `max_brier_score_allowed ≥ 0.25` — the gate passed with marginal calibration.

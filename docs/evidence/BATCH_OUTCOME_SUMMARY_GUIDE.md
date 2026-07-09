# Batch Outcome Summary Guide

## Purpose

A Batch Outcome Summary (BOS) documents the aggregate experimental outcomes for a
batch that was originally proposed by a Batch Selection Proposal (BSP).

The BOS closes the loop from computational proposal to experimental results, making
the feedback cycle auditable:

```
BSP (proposed batch)
  → Lab experiments
  → BOS (aggregate outcomes)
  → CPS (calibration performance summary)
  → CBA (cross-batch aggregator)
  → CRG (calibration readiness gate)
  → BSP (next batch proposal)
```

## Key constraint: synthetic/real boundary

`is_synthetic=True` requires `dry_lab_only=True`.  Synthetic results (mock data,
simulated experiments) cannot be treated as real lab data.  This prevents synthetic
validation from being confused with actual experimental validation.

## Schema fields

| Field | Type | Description |
|---|---|---|
| `bos_id` | str | Must start with `BOS-` |
| `pipeline_version` | str | Pipeline version at time of batch execution |
| `bsp_id` | str | Must start with `BSP-` — the proposal this responds to |
| `batch_id` | str | Batch identifier |
| `candidates_proposed` | int | Number of candidates in the original BSP |
| `candidates_tested` | int | Number actually tested (≤ proposed) |
| `candidates_active` | int | Number showing activity |
| `candidates_inactive` | int | Number showing no activity |
| `is_synthetic` | bool | True if results are synthetic/simulated |
| `outcome_notes` | str | Max 400 chars |
| `reviewer` | str | Who validated these outcomes |
| `dry_lab_only` | bool | Must be True when is_synthetic=True |

## Count constraint

`candidates_active + candidates_inactive` must equal `candidates_tested`.
The difference `candidates_proposed - candidates_tested` is computed as
`candidates_untested` and reported in the validation result.

## Honest boundaries

- A BOS records aggregate counts — it does not document which specific candidates
  were active or inactive (use CalibrationIntakeEntry per candidate for that).
- `is_synthetic=True` entries cannot support biological claims even if values
  look favorable — label them clearly in reports.
- The BOS does not validate that `bsp_id` references a real BSP; referential
  integrity requires a separate audit step.
- Untested candidates reduce calibration coverage; a BOS should explain why
  candidates were not tested in `outcome_notes`.

## Warnings

The validator emits warnings (not errors) for:

- Any untested candidates (fraction ≥ 25%: calibration coverage warning; otherwise
  generic warning).
- `is_synthetic=False` with `dry_lab_only=True` — real results should set
  `dry_lab_only=False` after safety review.
- No active candidates — worth investigating if unexpected.

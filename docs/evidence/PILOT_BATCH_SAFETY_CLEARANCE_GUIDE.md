# Pilot Batch Safety Clearance Guide

## Purpose

A Pilot Batch Safety Clearance (PSC) documents that a proposed batch (BSP) has been
safety-reviewed before wet-lab synthesis is authorized.

The PSC is a gate, not a rubber stamp. A batch with `max_safety_risk_tier="high"`
**cannot be cleared** — `cleared_for_synthesis` must be `False` in that case.
This constraint is enforced by the validator and cannot be overridden.

## The four mandatory safety screens

All four must be `True` for a valid PSC:

| Screen | What it checks |
|---|---|
| `dual_use_risk_checked` | Risk that synthesized candidates could be repurposed for harm |
| `novelty_verified` | Candidates are not re-synthesis of known hazardous sequences |
| `toxicity_screened` | Computational toxicity prediction was run |
| `hemolysis_screened` | Computational hemolysis prediction was run |

These screens are required to be marked `True` — marking them `True` attests that
the screen was performed. The PSC does not validate the quality of the screen.
Qualified human review must verify that the screens were performed correctly.

## Risk tier definitions

| Tier | Meaning | Can clear? |
|---|---|---|
| `low` | No concerning signals from any screen | Yes |
| `moderate` | One or more screens raised flags; individual review done | Yes (with warning) |
| `high` | One or more candidates pose unacceptable risk | No |

## Schema fields

| Field | Type | Description |
|---|---|---|
| `psc_id` | str | Must start with `PSC-` |
| `bsp_id` | str | Must start with `BSP-` |
| `pipeline_version` | str | Pipeline version at review time |
| `dual_use_risk_checked` | bool | Must be `True` |
| `novelty_verified` | bool | Must be `True` |
| `toxicity_screened` | bool | Must be `True` |
| `hemolysis_screened` | bool | Must be `True` |
| `max_safety_risk_tier` | str | `low`, `moderate`, or `high` |
| `cleared_for_synthesis` | bool | Must be `False` if tier is `high` |
| `rejection_ids` | List[str] | Candidate IDs rejected for safety |
| `safety_notes` | str | Max 400 chars |
| `reviewer` | str | Who performed or approved the safety review |
| `dry_lab_only` | bool | `True` = computational screen only; `False` = wet-lab safety assay |

## Honest boundaries

- A PSC with `dry_lab_only=True` is a computational safety gate only. It is necessary
  but not sufficient — qualified human review must precede actual synthesis.
- `cleared_for_synthesis=True` means the pipeline's safety gate passed. It does not
  mean synthesis is safe; it means no automated red flags were raised.
- Safety screens check for known risk patterns. Novel sequences may pose risks not
  captured by current screening methods.
- The PSC does not validate that `bsp_id` references a real BSP; referential integrity
  requires a separate audit step.

## Warnings

The validator emits warnings (not errors) for:

- `max_safety_risk_tier="moderate"` with `cleared_for_synthesis=True` — ensure
  moderate-risk candidates were individually reviewed.
- Non-empty `rejection_ids` — lists the rejected candidates.
- `dry_lab_only=True` with `cleared_for_synthesis=True` — computational clearance
  requires additional qualified human review before synthesis.

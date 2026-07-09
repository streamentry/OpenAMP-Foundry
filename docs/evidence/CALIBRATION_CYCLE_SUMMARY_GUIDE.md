# Calibration Cycle Summary Guide

## Purpose

A Calibration Cycle Summary (CCS) is the index record for one complete calibration
feedback loop. It ties together all Phase O and Phase P schemas into a single
searchable audit record.

## The calibration feedback loop

```
CRG-previous (calibration readiness gate passes)
  ↓
BSP (batch selection proposal)
  ↓
PSC (pilot batch safety clearance)
  ↓
[Wet-lab experiments]
  ↓
BOS (batch outcome summary)
  ↓
CPS (calibration performance summary)
  ↓
CBA (cross-batch aggregator)
  ↓
CRG-next (new calibration readiness gate)
  ↓
Next CCS
```

A CCS records the IDs of all artifacts from one pass through this loop. The
`crg_id_previous` and `crg_id_next` must differ — a completed cycle always
opens a new gate.

## Schema fields

| Field | Type | Description |
|---|---|---|
| `ccs_id` | str | Must start with `CCS-` |
| `pipeline_version` | str | Pipeline version for this cycle |
| `bsp_id` | str | Must start with `BSP-` |
| `psc_id` | str | Must start with `PSC-` |
| `bos_id` | str | Must start with `BOS-` |
| `cps_id` | str | Must start with `CPS-` |
| `cba_id` | str | Must start with `CBA-` |
| `crg_id_previous` | str | Must start with `CRG-` — the gate that enabled this cycle |
| `crg_id_next` | str | Must start with `CRG-` — must differ from previous |
| `cycle_outcome` | str | `improved`, `stable`, or `degraded` |
| `cycle_notes` | str | Max 400 chars |
| `reviewer` | str | Who completed and validated this cycle |
| `dry_lab_only` | bool | True if cycle used synthetic/simulated data |

## Artifact ID prefix map

| Prefix | Schema | Phase |
|---|---|---|
| `CCS-` | CalibrationCycleSummary | P5 |
| `BSP-` | BatchSelectionProposal | P1 |
| `PSC-` | PilotBatchSafetyClearance | P4 |
| `BOS-` | BatchOutcomeSummary | P3 |
| `CPS-` | CalibrationPerformanceSummary | O1 |
| `CBA-` | CrossBatchAggregator | O4 |
| `CRG-` | CalibrationReadinessGate | O5 |

## Honest boundaries

- A CCS is an index, not a proof of correctness. The schemas it references may
  themselves contain errors or missing data.
- `crg_id_previous != crg_id_next` is enforced, but not whether the two gates
  belong to the same pipeline version or have a logical succession.
- `dry_lab_only=True` entries document completed cycles in a simulation context;
  they cannot support claims about real experimental outcomes.

## Warnings

The validator emits warnings (not errors) for:

- `cycle_outcome="degraded"` — calibration quality decreased; investigate before
  the next selection cycle.
- `dry_lab_only=True` — no real experimental data was used in this cycle.

# Failed Simulation Stays Useful as Negative Evidence (H7)

This document establishes the cultural and procedural standard for treating failed simulation results as first-class negative evidence rather than noise to be discarded.

## The principle

A simulation that predicts a candidate will fail is not a broken simulation. It is a result. Discarding failed simulation outputs is equivalent to discarding negative lab results — it distorts the evidence base and makes the pipeline look better than it is.

Every failed simulation result MUST be recorded, not silently dropped.

## Why this matters

### Calibration depends on failure signal

The calibration loop (BSP → PSC → BOS → CPS → CBA → CRG) requires honest failure rates to detect when the pipeline's predictions diverge from outcomes. If failures are dropped:

- The observed rejection rate looks lower than it is.
- Calibration updates will overfit to a curated success signal.
- The `FMS-` failure mode similarity report cannot identify repeated failure patterns.

### Evidence trail integrity

The proof-ladder and evidence certificates are only meaningful if the negative evidence is as complete as the positive. A certificate that reflects only the candidates that passed screening — without mentioning how many failed — is incomplete and misleading.

### Anti-selective-reporting

Selective reporting of simulation results (reporting hits, dropping misses) is the computational equivalent of p-hacking. It inflates apparent discovery rates and misleads downstream decisions.

## Required behavior

When a simulation module returns a failed result (low score, below-threshold prediction, error state), the implementer MUST:

1. **Record a NRR- negative result record** with:
   - The candidate ID.
   - The simulation module name.
   - The reason for rejection (from `VALID_REJECTION_REASONS` in the negative result schema).
   - The confidence level.
   - `dry_lab_only=True`.

2. **NOT silently discard** the failed result without recording it.

3. **NOT retry with different parameters** to get a pass result without logging the initial failure.

4. **Include the failure count** in any batch-level summary (BOS-, FMS-, NRD- records).

## What counts as a "useful" failed simulation

A failed simulation is useful when it:

- Was run under the same conditions as passing simulations (no special-casing of hard cases).
- Used an explicit rejection criterion (not "it looked bad").
- Is traceable to a specific candidate ID and pipeline run.
- Has a recorded reason from a controlled vocabulary.

A failed simulation is NOT useful (and should be flagged, not deleted) when:

- The failure is due to a software bug, not a biological prediction.
- The input was malformed (not a valid sequence).
- The simulation module itself was in a degraded state (flag in SUC- calibration report).

## For agents

An agent processing simulation output MUST NOT:

- Drop or filter out below-threshold results without writing a NRR-.
- Report only passing results in a batch summary.
- Rerun a simulation on a failing candidate without logging the initial failure.

An agent MAY:

- Flag a failed result as a software error (not a prediction) if the module returned an error state.
- Note in the NRR- that the failure was due to module unavailability rather than a biological prediction.

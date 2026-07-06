# Virtual Assay Scope

## Purpose

This document defines what the OpenAMP virtual assay layer is allowed to mean.

It exists to prevent simulation theater: an impressive-looking model that does not improve decision quality is noise.

The virtual assay layer is not a replacement for biology.

It is an experimental inspection and prioritization layer that may eventually help qualified humans choose fewer, smarter wet-lab questions if it beats cheap baselines and survives calibration.

## Current status

**Status:** experimental modules implemented; production ranking impact remains gated.

Current state:

- `MembraneProxy` and `StructureProxy` exist.
- Simulation outputs can be surfaced in informational reports where supported by the CLI.
- Current ablation evidence does not justify weighted ranking impact.
- `docs/SIMULATION_BENCHMARK.md` is the source of truth for current simulation benchmark verdicts.
- Weighted simulation remains blocked until the simulation gate passes with stronger evidence.

## Core principle

> An impressive-looking simulator that does not improve real decision quality is noise, not progress.

Every module must demonstrate that it improves triage or selection quality relative to a cheap heuristic baseline before it may affect candidate ranking.

Modules that fail ablation may remain visible only as experimental context.

## What the virtual assay layer is for

The virtual assay layer may help with:

- exposing model uncertainty;
- identifying candidates where simple helical/charge assumptions may fail;
- comparing mechanistic proxy signals;
- informing human review;
- selecting uncertainty probes for future batches;
- generating hypotheses for qualified experts to critique;
- deciding what additional evidence would be useful.

It must not be treated as biological validation.

## What the virtual assay layer models

| Module | Models | Output | Status |
|---|---|---|---|
| Membrane binding proxy | Coarse-grained sequence-derived membrane-interaction proxy. | `SimulationResult` with membrane-related scores and uncertainty. | Experimental. |
| Structure ensemble proxy | Sequence-derived secondary-structure propensity. | Helix/coil/sheet proxy and uncertainty. | Experimental. |
| Selectivity ratio | Proxy contrast between bacterial-facing and mammalian-facing membrane signals. | Selectivity-like score with uncertainty. | Experimental. |
| Stability proxy | Future stability/protease-risk signal. | Not scoped until adequate calibration/benchmark data exists. | Deferred. |
| External simulation adapter | Wrapper around third-party tools or services under explicit user control. | Standard `SimulationResult`. | Interface-level support only. |

## What the virtual assay layer does not model

The virtual assay layer explicitly does not model:

- full-cell biological response;
- immune response;
- pharmacokinetics;
- biodistribution;
- synergy with other compounds;
- biofilm penetration;
- intracellular target engagement unless a specific validated module later earns scope;
- resistance evolution;
- in vivo efficacy;
- human clinical outcomes;
- biological safety.

Any claim that the virtual assay layer predicts these is a category error.

## Uncertainty policy

Every `SimulationResult` must include an uncertainty field.

Uncertainty should reflect:

- parameter uncertainty;
- model-form uncertainty;
- calibration uncertainty;
- domain mismatch;
- input limitations;
- missing external-tool dependencies;
- failure or fallback behavior.

If calibration data is absent or weak, the uncertainty field must surface that directly.

A module with high uncertainty is experimental and must not affect selection.

## Ablation requirement

Each module must pass ablation before it can affect candidate selection.

At minimum, the module must be compared against its cheapest meaningful baseline.

Examples:

| Module output | Cheap baseline challenger |
|---|---|
| Membrane binding score | Hydrophobicity or hydrophobic moment. |
| Selectivity ratio | Existing selectivity proxy. |
| Helix weight | Simple helix propensity. |
| Non-helical flag | Proline/cysteine/length class heuristic. |
| Stability proxy | Simple cleavage-site or length heuristic. |

A module that does not beat its cheapest challenger may remain informational, but it must not alter ranking.

## Integration modes

| Mode | Effect | Allowed use |
|---|---|---|
| `off` | No virtual assay scores computed. | Default production ranking. |
| `info` | Scores may be computed and shown in reports/certificates. | Exploration and human inspection only. |
| `weighted` | Scores affect ranking. | Forbidden unless simulation gate passes. |

`weighted` mode must be fail-closed.

If benchmark artifacts are missing, stale, contradictory, or fail the gate, weighted integration remains blocked.

## Calibration requirement

No virtual-assay module may be used in weighted mode unless it has documented calibration evidence showing that it improves decision quality for the intended task.

Calibration evidence should include:

- dataset or result source;
- task definition;
- cheap-baseline comparison;
- uncertainty behavior;
- failure modes;
- proof-ladder interpretation;
- reviewer decision.

Correlation with outcomes is not enough if the module still fails to improve selection relative to cheap baselines.

## External adapter policy

External simulation or predictor adapters must:

- be explicit about scope;
- be versioned;
- fail closed;
- avoid silent downloads;
- avoid sending sequences to external services without explicit user consent;
- return uncertainty;
- record errors as evidence, not hide them;
- never strengthen biological claims by default.

An adapter is a bridge, not a trust guarantee.

## Evidence certificate policy

When simulation values appear in evidence certificates, they must be labeled as experimental context unless the module has cleared the relevant gate.

Certificates should state:

- module name;
- version;
- scope;
- scores;
- uncertainty;
- calibration set if any;
- validated-against list;
- whether scores affected ranking;
- known limitations.

## Known risks

| Risk | Mitigation |
|---|---|
| Simulation theater | Require ablation and cheap-baseline comparison. |
| False confidence | Propagate uncertainty and block ranking impact. |
| Helical bias | Report family/structure-class blind spots. |
| Hidden external dependencies | Adapter availability checks and fail-closed behavior. |
| Benchmark overfitting | Cross-dataset and family-stratified evaluation. |
| Claim inflation | Proof ladder and certificate caveats. |
| Agent overreach | Agent onboarding and human-review gates. |

## Relationship to calibration pipeline

The virtual assay layer feeds into the calibration roadmap but does not replace it.

```text
candidate source
  -> dry-lab foundry
  -> virtual assay proxies, if enabled
  -> uncertainty and review context
  -> candidate panel design
  -> qualified external testing, if approved
  -> structured result intake
  -> recalibration gate
  -> human-reviewed update or rejection
  -> next candidate-selection round
```

The virtual assay layer proposes context.

The calibration layer decides whether real outcomes justify model updates.

Human review remains mandatory.

## Exit criteria for trusted integration

A virtual assay module may be considered for ranking impact only when:

1. It has a stable interface.
2. It returns uncertainty.
3. It has deterministic behavior or recorded external dependencies.
4. It beats its cheapest baseline on a relevant task.
5. It improves panel-level decision quality, not just isolated AUROC.
6. It has documented failure modes.
7. It has no unresolved safety or release concerns.
8. A human reviewer approves the integration mode.

Until then, it is experimental context.

## Final standard

The best virtual assay module is not the one that sounds most biological.

It is the one that helps qualified humans choose better experiments and makes its own uncertainty impossible to ignore.

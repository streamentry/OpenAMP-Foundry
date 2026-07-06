# Virtual Assay Scope

## Purpose

This document defines what the Phase 3 virtual assay layer IS and IS NOT,
which modules are planned, and the bar each module must clear before
affecting candidate selection. It exists to prevent simulation theater:
an impressive-looking model that does not improve decision quality is noise.

## Status

**Phase 3 — Planning.** No virtual-assay modules are implemented in the
production pipeline. This document describes the intended scope and
constraints. Implementation starts with Loop 31.

## Core Principle

> An impressive-looking simulator that does not improve real decision
> quality is noise, not progress. — AGENTS.md §7.5

Every module must demonstrate that it improves triage or selection quality
relative to a cheap heuristic baseline before it may affect candidate
ranking. Modules that fail the ablation must remain flagged as experimental.

## What the Virtual Assay Layer Models

| Module | Planned loop | Models | Output |
|--------|-------------|--------|--------|
| Membrane binding proxy | 31 | Coarse-grained membrane binding energy using hydrophobicity scale + helical hydrophobic moment. Bacterial membrane proxy (anionic lipid headgroups) and mammalian membrane proxy (zwitterionic/cholesterol). | `SimulationResult` with scores per membrane type, uncertainty |
| Structure ensemble proxy | 32 | Secondary structure propensity (helix/coil/sheet) from sequence. Flags non-helical candidates for which the helic-centric activity scorer is unreliable. | 3-state ensemble weights (helix/coil/sheet), confidence |
| Selectivity ratio | 33 | Ratio of bacterial membrane binding score to RBC/mammalian membrane binding score. Flags candidates where selectivity index is low. | `selectivity_ratio` with uncertainty |
| Stability proxy | Deferred | Protease susceptibility, serum half-life proxy. Deferred because no calibration data exists. | Not scoped until calibration data arrives |

## What the Virtual Assay Layer Does NOT Model

The virtual assay layer explicitly DOES NOT model:

- Full-cell biological response (signaling, metabolism, stress response)
- Immune system interactions (cytokine release, immunogenicity)
- Pharmacokinetics or biodistribution
- Synergistic effects with other compounds
- Biofilm penetration or extracellular matrix interaction
- Intracellular target engagement (DNA, ribosome, protein binding)
- Resistance development or evolutionary dynamics
- In vivo efficacy in any animal model
- Human clinical outcomes

Any claim that the virtual assay layer predicts these is a category error.

## Uncertainty Policy

Every `SimulationResult` MUST include an `uncertainty` field. The
uncertainty reflects:

- **Parameter uncertainty**: how well the module's parameters are
  constrained by available calibration data
- **Model-form uncertainty**: whether the module's functional form
  captures the relevant physics
- **Calibration uncertainty**: whether calibration data exists and how
  well it matches the target domain

If calibration data is absent or weak, the `uncertainty` field must
surface that directly. A module with `uncertainty > 0.5` (on a 0–1 scale
where 0 = fully constrained, 1 = unconstrained) is experimental and must
not affect selection.

## Ablation Requirement

Each module must pass an ablation benchmark before it can affect
selection. The ablation test compares the module's discrimination against
a trivial baseline (single-feature proxy):

| Metric | Required bar |
|--------|-------------|
| Selective-vs-hemolytic AUROC | > 0.65 with CI lower bound > 0.50 |
| Improvement over best single feature | Delta AUROC > 0.05 |
| Uncertainty | < 0.5 on relevant domain |

Modules that do NOT pass the ablation are permanently marked as
experimental and flagged with `SIMULATION_THEATER_RISK` in their
`SimulationResult`.

## Integration Modes

The virtual assay layer supports three modes:

| Mode | Effect | When to use |
|------|--------|-------------|
| `off` (default) | No simulation scores computed. Current pipeline. | Production candidate ranking |
| `info` | Simulation scores computed and included in reports only. No ranking impact. | Benchmarking, exploration |
| `weighted` | Simulation scores affect ranking if each module clears its ablation bar. | Only after ablation validation |

The `rank` CLI accepts `--simulation-mode` to select the mode.

## Calibration Requirement

No virtual-assay module may be used in `weighted` mode unless it has
calibration data from at least one wet-lab batch showing that its
predictions correlate with measured outcomes (MIC, hemolysis, or
selectivity index). The calibration data must be documented in the
module's `calibration_set` field.

## Known Risks

| Risk | Mitigation |
|------|-----------|
| Overinterpretation of coarse-grained proxies | Ablation requirement, uncertainty propagation, explicit scope document |
| False confidence from simulation | Uncertainty > 0.5 gates off selection impact |
| Helical bias propagated to simulation | Structure ensemble proxy flags non-helical candidates |
| Simulation results mistaken for biology | All output labeled with `simulation: true`, no biological claims allowed |
| Ablation benchmarks overfit to reference set | Cross-validate on held-out membrane data, update reference set annually |

## Relationship to Calibration Pipeline

The virtual assay layer feeds INTO the calibration pipeline but does not
replace it. The order is:

```text
candidate source
  → dry-lab foundry (current pipeline)
  → virtual assay proxies (Phase 3)
  → uncertainty estimation
  → informative batch selection
  → lab assay
  → calibration intake → gate → engine (Phase 2)
  → next-round candidate selection
```

The virtual assay layer proposes which candidates are informative. The
calibration layer decides whether and how to update weights based on
actual outcomes. Neither layer operates without human review.

## Exit Criteria for Phase 3

Phase 3 is complete when:

1. At least 2 simulation modules exist and are benchmarked.
2. A module that improves strict-triage selective-vs-hemolytic AUROC
   by > 0.03 is flagged as "improves selection" and available in
   `weighted` mode.
3. Modules that fail the ablation are either removed or permanently
   marked experimental.
4. Uncertainty is propagated through to the evidence certificate.
5. The external adapter protocol (`ExternalSimulationAdapter`) is
   documented in ARCHITECTURE.md.

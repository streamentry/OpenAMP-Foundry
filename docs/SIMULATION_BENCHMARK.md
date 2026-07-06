# Simulation Benchmark Report

## Phase 3 Closeout

Phase 3 (virtual assay scaffolding, Loops 30–39) built two simulation modules,
three benchmarks, a weighted-mode gate, a CLI flag, and an external adapter
protocol. Simulation does not improve ranking. The honest finding across all
benchmarks: **simulation does not improve ranking**.

Current verdict: simulation remains informational only.
Weighted mode is blocked by the gate and will remain blocked until a
future module demonstrably beats its cheapest heuristic baseline.

`weighted` simulation remains blocked.

---

## What Was Built

| Loop | Module | Status |
|:----:|--------|:------:|
| 30 | Virtual assay scope document | ✅ Scope defined |
| 31 | MembraneProxy (Wimley-White scales) | ✅ Ships in info mode |
| 32 | StructureProxy (Chou-Fasman 3-state) | ✅ Ships in info mode |
| 33 | AMP-vs-decoy ablation benchmark | ✅ No improvement |
| 34 | Within-AMP hemolysis ablation | ✅ No improvement |
| 35 | Weighted-mode simulation gate | ✅ Blocks weighted mode |
| 36 | Cheap-baseline comparison benchmark | ✅ 0/4 signals beat baselines |
| 37 | `rank --simulation-mode` CLI flag | ✅ Users can inspect scores |
| 38 | `ExternalSimulationAdapter` protocol | ✅ Third-party integration ready |
| 39 | This report | ✅ Phase 3 closed |

---

## Phase 3 Exit Criteria

| Criterion | Required | Status | Evidence |
|-----------|----------|:------:|----------|
| ≥2 simulation modules exist and are benchmarked | ✅ | ✅ Met | MembraneProxy (Loop 31), StructureProxy (Loop 32). Both benchmarked (Loops 33–36) |
| Simulation improves strict triage by >0.03 AUROC on any pairwise metric | Delta > 0.03 | ❌ Not met | Best simulation helix_weight AUROC 0.6458; best existing rich_selectivity AUROC 0.7453 (delta −0.0995) |
| Modules that fail ablation are removed or permanently experimental | All failed | ✅ Met | All modules flagged permanent experimental (Loop 36 verdict) |
| Uncertainty propagated through to evidence certificate | Via `SimulationResult` | ✅ Met | Each module returns `uncertainty` in range [0, 1]; information added to scores dict in info mode |
| External adapter protocol documented | ARCHITECTURE.md | ✅ Met | `ExternalSimulationAdapter` documented in ARCHITECTURE.md extension points (Loop 38) |

**Verdict: Phase 3 exit criteria partially met. Simulation does NOT earn ranking impact, but the infrastructure and honesty guardrails are complete.**

---

## Reproducible Commands

```bash
PYTHONPATH=src python3 scripts/benchmark_simulation_ablation.py \
  --mode amp-vs-decoy --out outputs/simulation_ablation.json || test $? -eq 3

PYTHONPATH=src python3 scripts/benchmark_simulation_ablation.py \
  --mode within-amp --out outputs/simulation_ablation_within_amp.json || test $? -eq 3

PYTHONPATH=src python3 scripts/benchmark_simulation_baselines.py \
  --out outputs/simulation_baselines.json || test $? -eq 3

PYTHONPATH=src python3 -m openamp_foundry.cli bench simulation-gate \
  --amp-vs-decoy-json outputs/simulation_ablation.json \
  --within-amp-json outputs/simulation_ablation_within_amp.json \
  --out outputs/simulation_gate_verdict.json || test $? -eq 3
```

Exit code `3` is expected for benchmarks or gates that correctly reject
weighted simulation.

---

## Current Results

| Benchmark | Baseline / incumbent | Simulation result | Delta | Verdict |
|---|---:|---:|---:|---|
| AMP-vs-decoy ablation | Ensemble AUROC `0.7792` | Ensemble + simulation AUROC `0.6640` | `-0.1153` | No improvement |
| Within-AMP hemolysis detection | Rich selectivity AUROC `0.7453` | Best simulation AUROC `0.6458` | `-0.0995` | No improvement |
| Cheap baseline: bacterial binding | Mean Eisenberg AUROC `0.5469` | Bacterial binding AUROC `0.4876` | `-0.0593` | No improvement |
| Cheap baseline: selectivity ratio | Selectivity proxy AUROC `0.3905` | Selectivity ratio AUROC `0.3615` | `-0.0290` | No improvement |
| Cheap baseline: helix weight | Helix propensity AUROC `0.6489` | Helix weight AUROC `0.6458` | `-0.0031` | No improvement |
| Cheap baseline: non-helical flag | Proline fraction AUROC `0.4929` | Non-helical flag AUROC `0.4124` | `-0.0805` | No improvement |

---

## Gate Decision

`openamp-foundry bench simulation-gate` blocks `weighted` mode.

Reasons:

- AMP-vs-decoy ablation does not improve over ensemble.
- Within-AMP ablation does not improve over existing scorers.
- Cheap-baseline comparison shows zero of four simulation signals beat their
  simplest meaningful heuristic.

Weighted mode will remain blocked until a future module passes all three checks.

---

## Interpretation

The current simulation layer (1D Chou-Fasman propensities, averaged Wimley-White
scales) is not rich enough to beat existing heuristics. Two reasons dominate:

1. **Composition dominance**: The existing pipeline already extracts charge,
   hydrophobicity, aromatic fraction, and GRAVY — features that correlate
   strongly with membrane interaction. Averaged hydrophobicity scales add
   little beyond what these composition features already capture.

2. **No structural context**: 1D per-residue averages lose all sequence-order
   and spatial information. A proper membrane interaction model requires
   coarse-grained dynamics (Martini), structural ensembles (AlphaFold), or
   at minimum a windowed context that captures local sequence patterns.

Future simulation work must use fundamentally richer inputs than 1D propensities.
Any new module must still beat its cheap baseline before earning ranking impact.

---

## Policy

Until this report changes with stronger evidence:

- `rank --simulation-mode info` is allowed for exploratory reports.
- `weighted` simulation remains blocked.
- Evidence certificates may include simulation values only as experimental
  context, not as activity, safety, or selectivity proof.
- No public claim may imply simulation-validated antimicrobial activity.
- Any future simulation module must pass the gate (Loop 35) before affecting
  ranking. The gate will not be bypassed even if the module appears plausible.

---

## Transition to Phase 4

Phase 4 (wet-lab readiness, Loops 40–49) shifts focus from virtual assay
scaffolding to preparing for real lab partners. The simulation modules ship
in info mode — usable for human inspection but not trusted for ranking.

The honest signal from Phase 3 is: **simulation is not ready to compress
wet-lab experiments.** Phase 4 work should prioritize getting the existing
pipeline into a lab partnership rather than deepening the simulation layer.

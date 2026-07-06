# Simulation Benchmark Report

## Status

Current verdict: simulation remains informational only.

The shipped membrane and structure proxies do not improve candidate ranking
against the repo's current benchmark bar. They may still help humans inspect a
candidate, but they must not affect ranking weights.

Simulation does not improve ranking on the current benchmark set.

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

## Current Results

| Benchmark | Baseline / incumbent | Simulation result | Delta | Verdict |
|---|---:|---:|---:|---|
| AMP-vs-decoy ablation | Ensemble AUROC `0.7792` | Ensemble + simulation AUROC `0.6640` | `-0.1153` | No improvement |
| Within-AMP hemolysis detection | Rich selectivity AUROC `0.7453` | Best simulation AUROC `0.6458` | `-0.0995` | No improvement |
| Cheap baseline: bacterial binding | Mean Eisenberg AUROC `0.5469` | Bacterial binding AUROC `0.4876` | `-0.0593` | No improvement |
| Cheap baseline: selectivity ratio | Selectivity proxy AUROC `0.3905` | Selectivity ratio AUROC `0.3615` | `-0.0290` | No improvement |
| Cheap baseline: helix weight | Helix propensity AUROC `0.6489` | Helix weight AUROC `0.6458` | `-0.0031` | No improvement |
| Cheap baseline: non-helical flag | Proline fraction AUROC `0.4929` | Non-helical flag AUROC `0.4124` | `-0.0805` | No improvement |

## Gate Decision

`openamp-foundry bench simulation-gate` blocks `weighted` mode.

Reasons:

- AMP-vs-decoy ablation does not improve over ensemble.
- Within-AMP ablation does not improve over existing scorers.
- Cheap-baseline comparison shows zero of four simulation signals beat their
  simplest meaningful heuristic.

## Interpretation

Known fact from current benchmark artifacts: the current simulation layer is
not ready to influence ranking.

Logical inference: future simulation work needs richer inputs than the current
1D propensities. A more complex module still has to beat cheap baselines before
it earns ranking impact.

## Policy

Until this report changes with stronger evidence:

- `rank --simulation-mode info` is allowed for exploratory reports.
- `weighted` simulation remains blocked.
- Evidence certificates may include simulation values only as experimental
  context, not as activity, safety, or selectivity proof.
- No public claim may imply simulation-validated antimicrobial activity.

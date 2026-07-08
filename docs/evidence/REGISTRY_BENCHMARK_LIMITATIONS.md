# Benchmark Limitation Registry

Known limitations of the project's benchmarks.

| Benchmark | Limitation |
|-----------|------------|
| 500-AMP benchmark | AUROC is charge-inflated (0.7792; collapses to 0.5103 under exact charge control) |
| Cross-dataset | DRAMP + Swiss-Prot decoys may share database artifacts |
| Simulation ablation | Modules are tested on AMP-vs-decoy, not their designed task |
| Within-AMP hemolysis | Small reference set (n=179), HC50 values from literature with high variability |
| Easy baseline | Charge density beats ensemble — expected, pipeline optimizes for safety |

## Rules
- Every benchmark result must reference its limitations.
- Limitations must be stated alongside the result, not hidden.
- When a limitation is resolved, update this registry.
- If a benchmark has no documented limitations, it's incomplete.

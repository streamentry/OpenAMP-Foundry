# Benchmark Plot Data Export

How to export benchmark data for plotting.

## Available Data
Benchmark results are available in JSON format in `outputs/`:
- `outputs/validate_scoring_500.json` — 500-AMP benchmark
- `outputs/cross_dataset_benchmark.json` — cross-dataset
- `outputs/benchmark_per_family.json` — per-family breakdown

## Format
Each JSON file contains:
```json
{
  "auroc": 0.7792,
  "auprc": 0.7705,
  "ci_95": [0.7505, 0.8065],
  "recall_at_10": 0.02,
  "recall_at_20": 0.04
}
```

## Plotting
Use any JSON-compatible plotting tool (matplotlib, seaborn, etc.).
For per-family data, the JSON includes per-class metrics for grouped bar charts.

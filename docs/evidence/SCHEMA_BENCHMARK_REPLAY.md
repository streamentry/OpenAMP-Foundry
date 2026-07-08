# Benchmark Replay Manifest

Records the inputs and configuration used for a benchmark run.

## Format
```json
{
  "benchmark": "bench-500",
  "timestamp": "ISO 8601",
  "amp_csv": "path/to/amps.csv",
  "decoy_csv": "path/to/decoys.csv",
  "config": "configs/pipeline.yaml",
  "git_sha": "abc123",
  "seed": 20260705,
  "results": {
    "auroc": 0.7792,
    "auprc": 0.7705
  }
}
```

## Rules
- Every benchmark run should produce a replay manifest.
- Manifests are stored in `outputs/replay_manifests/`.
- Manifests enable exact reproduction of benchmark results.
- Include the git SHA and seed for reproducibility.

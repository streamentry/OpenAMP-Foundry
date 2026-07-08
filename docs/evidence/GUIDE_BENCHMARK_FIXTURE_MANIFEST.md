# Benchmark Fixture Manifest Files

Manifest files for benchmark fixtures.

## Format
```json
{
  "benchmark": "bench-500",
  "fixtures": {
    "amps": "examples/validation/known_amps_500.csv",
    "decoys": "examples/validation/random_background_500.csv",
    "config": "configs/pipeline.yaml"
  },
  "hashes": {
    "amps": "sha256:...",
    "decoys": "sha256:..."
  },
  "generated_at": "2026-07-08T12:00:00Z"
}
```

## Rules
- Each benchmark should have a fixture manifest.
- Manifests include hashes of input files for reproducibility.
- If input files change, the manifest should be regenerated.
- Manifests are stored in `outputs/benchmark_fixtures/`.

# Architecture Overview for Contributors

A quick tour of the codebase structure.

```
src/openamp_foundry/     # Pipeline code
  cli/                   # CLI commands (rank, validate, bench, etc.)
  pipeline.py            # Main scoring pipeline
  scoring/               # Individual scorers (activity, safety, etc.)
  features/              # Physicochemical feature extraction
  simulation/            # Virtual assay modules (membrane, structure)
  calibration/           # Recalibration engine and gate
  evidence/              # Evidence certificate generation
  benchmark/             # Benchmark infrastructure
tests/                   # Test suite
  benchmarks/            # Benchmark regression tests
  calibration/           # Calibration tests
  lab/                   # Lab handoff tests
configs/                 # Configuration files (pipeline.yaml, etc.)
schemas/                 # JSON schemas for artifacts
scripts/                 # Utility scripts
docs/                    # Documentation
```

## Entry Points
- `src/openamp_foundry/cli/main.py` — CLI entry points.
- `src/openamp_foundry/pipeline.py` — `run_ranking_pipeline()` is the main function.

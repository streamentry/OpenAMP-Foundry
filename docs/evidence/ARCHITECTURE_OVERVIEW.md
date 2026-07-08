# Architecture Overview for Contributors

## High-Level Structure
```
src/openamp_foundry/     — pipeline code
  cli/                   — command-line interface
  pipeline.py            — main scoring pipeline
  scoring/               — individual scorers
  features/              — feature extraction
  simulation/            — virtual assay modules
  calibration/           — recalibration engine
  evidence/              — certificate generation
tests/                   — test suite
docs/                    — documentation
scripts/                 — utility scripts
configs/                 — configuration files
schemas/                 — artifact schemas
```

## Key Files
- `src/openamp_foundry/pipeline.py` — main scoring pipeline
- `src/openamp_foundry/cli/main.py` — CLI entry points
- `configs/pipeline.yaml` — scoring weights and filters
- `docs/evidence/METRICS_CURRENT.md` — current benchmark metrics

## Data Flow
1. CLI parses arguments and calls `pipeline.run_ranking_pipeline()`.
2. Pipeline loads candidates, scores them, and writes outputs.
3. Outputs include ranked JSONL, evidence certificates, and reports.

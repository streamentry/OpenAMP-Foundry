# CLI Architecture Explainer

How the CLI is structured and how commands are organized.

## Structure
```
openamp-foundry          — main CLI entry point
  rank                   — score and rank candidates
  validate               — validate evidence certificates
  bench                  — run benchmarks
    leakage              — check for near-duplicate leakage
    baseline             — baseline comparison
    cluster-split        — cluster-aware bootstrap
  pilot-panel            — select pilot panel candidates
  calibration-intake     — ingest lab results
  recalibration-gate     — evaluate recalibration permission
```

## Pattern
Each command is a subparser in `src/openamp_foundry/cli/main.py`.
The handler calls a function from the relevant package.
New commands should follow the same pattern.

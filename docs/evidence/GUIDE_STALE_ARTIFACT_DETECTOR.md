# Stale Artifact Detector

Detects artifacts that may be stale (out of sync with current code).

## What It Checks
1. Schema files — compare schema version against code.
2. Benchmark outputs — check if they match current pipeline.
3. Generated docs — check if they reference current features.
4. Config files — check if all keys are still valid.

## Usage
```bash
python scripts/check_doc_links.py  # Check docs for broken references
make bench-gate                     # Check benchmark regression gates
python scripts/check_pyproject.py   # Check pyproject.toml consistency
```

## Manual Checks
- Evidence certificates should be regenerated after scoring changes.
- Benchmarks should be re-run after config changes.
- Docs should be reviewed after major feature changes.

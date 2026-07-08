# Benchmark Dry-Run Mode

A dry-run mode for benchmarks that checks configuration without running.

## Usage
```bash
make bench-500  # Runs the benchmark
# For dry-run, check config validity first:
python -c "
import yaml
from pathlib import Path
config = yaml.safe_load(Path('configs/pipeline.yaml').read_text())
assert 'weights' in config, 'Missing weights in config'
assert 'filters' in config, 'Missing filters in config'
print('Config is valid')
"
```

## What a Dry-Run Checks
- Configuration file is valid YAML.
- Required weights are present.
- Filter thresholds are within expected ranges.
- Input files exist.

## Status
Dry-run mode is not yet implemented as a CLI flag. Use config validation as a substitute.

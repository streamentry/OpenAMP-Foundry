# Artifact Manifest Generator for Command Outputs

Generates manifests for command outputs.

## Usage
```bash
# After running a command, generate its manifest
python -c "
import json, hashlib, datetime
from pathlib import Path

outputs = list(Path('outputs').glob('*.jsonl')) + list(Path('outputs').glob('*.json'))
manifest = {
    'generated_at': datetime.datetime.now().isoformat(),
    'outputs': [str(f) for f in outputs],
    'hashes': {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in outputs}
}
Path('outputs/manifest.json').write_text(json.dumps(manifest, indent=2))
"
```

## Fields
- `generated_at` — ISO 8601 timestamp
- `outputs` — list of output file paths
- `hashes` — SHA-256 hash of each output file

## Rules
- Manifests should be generated when batch processing is complete.
- Hashes enable verification that outputs haven't been modified.
- Manifests are stored alongside the outputs they describe.

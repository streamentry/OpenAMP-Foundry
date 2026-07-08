# Artifact Identity Helper Based on Hashes

Helper for identifying artifacts by their content hash.

## Usage
```python
from scripts.verify_lab_peptides import _sha256

# Get artifact identity
file_hash = _sha256(open("outputs/demo_ranked.jsonl").read())
print(f"Artifact identity: {file_hash}")
```

## Rules
- Artifact identity is the SHA-256 hash of the file contents.
- Two artifacts with the same hash are identical.
- Hash-based identity works across machines and time.
- If the artifact changes, the identity changes.
- Use artifact identity to verify that expected outputs match received outputs.

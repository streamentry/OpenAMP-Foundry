# Output Checksum Lockfile

Records expected checksums for generated outputs.

## Format
```text
sha256:<hash>  outputs/demo_ranked.jsonl
sha256:<hash>  outputs/demo_report.md
```

## Usage
After running a known-good pipeline, record the checksums:
```bash
sha256sum outputs/*.jsonl outputs/*.md > outputs/checksums.lockfile
```

To verify:
```bash
sha256sum -c outputs/checksums.lockfile
```

## Rules
- Lockfiles should be updated when pipeline behavior intentionally changes.
- CI should fail if lockfiles don't match (detects unexpected changes).
- Lockfiles are stored in `outputs/` (git-ignored).
- If outputs are non-deterministic (timestamps), exclude those files.

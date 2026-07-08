# Hidden-State Reproducibility Check

How to verify that pipeline results are reproducible.

## What to Check
1. Same inputs + same config + same version = same outputs.
2. Output hashes match between runs.
3. Random seeds produce deterministic results.

## How to Verify
```bash
# Run twice and compare outputs
make demo
cp outputs/demo_ranked.jsonl /tmp/run1.jsonl
make demo
diff outputs/demo_ranked.jsonl /tmp/run1.jsonl  # Should be identical
```

## What If Outputs Differ
- Check for non-deterministic components (timestamps, UUIDs).
- Check that random seeds are fixed.
- Check that the code version hasn't changed between runs.

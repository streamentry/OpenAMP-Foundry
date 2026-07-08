# Expected Output Gallery for Quickstart

After running `make demo`, you should see these outputs.

## Files Created
```
outputs/demo_ranked.jsonl    — ranked candidate list
outputs/demo_report.md       — human-readable report
outputs/evidence/            — evidence certificates directory
outputs/evidence/AMPF-*.json — one certificate per candidate
outputs/run_manifest.json    — run manifest
```

## Sample Output
The first line of `outputs/demo_ranked.jsonl` should contain a JSON object
with `candidate_id`, `sequence`, `scores`, and `features` fields.

## If Output Differs
- Check that `make demo` completed without errors.
- Check that the input files exist at `examples/sequences/demo_candidates.csv`.
- Check that the reference file exists at `examples/known_reference/demo_known_amps.csv`.

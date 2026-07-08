# Guided Walkthrough: Artifact Validation

## Scenario
You've received lab result JSON files from a partner. Validate them.

## Steps
1. Place the JSON files in a single directory.
2. Run: `python scripts/validate_lab_data_return.py --results-dir <dir>`
3. Check the output:
   - "Passed: N" — all files passed schema validation
   - "Failed: M" — some files have errors (check the error messages)
4. If there are control failures, check the original assay data.
5. If there are schema validation errors, ask the partner to fix and resubmit.

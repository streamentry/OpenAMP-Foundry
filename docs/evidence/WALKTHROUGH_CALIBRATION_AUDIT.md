# Guided Walkthrough: Calibration Audit Reports

## Scenario
You need to audit the calibration pipeline after receiving lab results.

## Steps
1. Place lab result JSONs in a directory.
2. Run: `openamp-foundry calibration-intake --predictions <csv> --results-dir <dir> --panel-name wave1`
3. Check the intake report for matched and orphan results.
4. Run: `openamp-foundry recalibration-gate --intake <intake.json> --policy configs/recalibration_policy.yaml`
5. Check the gate verdict: 0 = recalibration allowed, 3 = blocked.
6. If blocked, review which conditions failed.
7. Document the audit results in the decision log.

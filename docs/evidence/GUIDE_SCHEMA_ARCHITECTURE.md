# Schema Architecture Explainer

How schemas are structured and maintained.

## Schema Locations
| Schema | Location | Purpose |
|--------|----------|---------|
| candidate.schema.json | schemas/ | Evidence certificates |
| lab_result.schema.json | schemas/ | Lab assay results |
| batch_report.schema.json | schemas/ | Batch reports |
| run_manifest.schema.json | schemas/ | Run manifests |
| recalibration_report.schema.json | schemas/ | Calibration reports |
| decision_log.schema.json | schemas/ | Human review decisions |
| panel_csv.schema.json | schemas/ | Panel CSVs |

## Rules
- All schemas use Draft 2020-12.
- Required fields must be documented in the schema.
- Adding fields is backward-compatible; removing fields is not.
- Schema changes require a corresponding version bump.

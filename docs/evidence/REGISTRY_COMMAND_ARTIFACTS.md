# Command Artifact Type Registry

Type of artifact produced by each command.

| Command | Artifact Type | Format | Location |
|---------|:-------------|:------|----------|
| rank | ranked_candidates | JSONL | outputs/*_ranked.jsonl |
| rank | evidence_certificate | JSON | outputs/evidence/ |
| rank | run_manifest | JSON | outputs/run_manifest.json |
| validate | validation_result | stdout | — |
| bench | benchmark_result | JSON | outputs/*.json |
| pilot-panel | panel_csv | CSV | outputs/*_panel.csv |
| calibration-intake | intake_report | JSON | outputs/*_intake.json |
| recalibration-gate | gate_verdict | JSON | outputs/*_verdict.json |

## Rules
- Every command should produce at least one artifact.
- Artifact types should be registered here.
- If a command's output format changes, update this registry.

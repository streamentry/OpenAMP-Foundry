# Command-to-Artifact Map

Maps CLI commands to their output artifacts.

| Command | Output Artifact | Format | Location |
|---------|----------------|:-----:|----------|
| `rank` | Ranked candidates | JSONL | `outputs/*_ranked.jsonl` |
| `rank` | Evidence certificates | JSON | `outputs/evidence/` |
| `rank` | Run manifest | JSON | `outputs/run_manifest.json` |
| `rank --report` | Batch report | MD + JSON | `outputs/*_report.md` |
| `validate` | Validation result | stdout | — |
| `pilot-panel` | Pilot panel CSV | CSV | `outputs/*_panel.csv` |
| `lab-result-report` | Lab result report | JSON | `outputs/*_report.json` |
| `calibration-intake` | Intake report | JSON | `outputs/*_intake.json` |
| `recalibration-gate` | Gate verdict | JSON | `outputs/*_verdict.json` |

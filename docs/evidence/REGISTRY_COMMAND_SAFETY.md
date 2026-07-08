# Command Safety Class Registry

Safety classification for CLI commands.

| Command | Safety Class | Rationale |
|---------|:-----------:|-----------|
| rank | safe | Scores candidates, no external effects |
| validate | safe | Validates files, read-only |
| bench | safe | Runs benchmarks, read-only |
| calibration-intake | requires_review | Affects calibration state |
| recalibration-gate | requires_review | Affects calibration decisions |
| pilot-panel | safe | Selection algorithm, read-only |
| lab-result-report | safe | Report generation, read-only |

## Classes
| Class | Meaning | Required Checks |
|-------|---------|----------------|
| safe | No harmful effects possible | Standard CI |
| requires_review | Could affect decisions | Human review required |
| restricted | High-risk operation | Project lead approval |

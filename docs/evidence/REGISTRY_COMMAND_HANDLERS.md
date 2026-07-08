# Command Handler Registry

Registry of CLI command handlers and their locations.

| Command | Handler Module | Handler Function |
|---------|---------------|-----------------|
| rank | cli/main.py | `run_ranking_pipeline` |
| validate | cli/main.py | `validate_json_schema` |
| bench | cli/commands/benchmark.py | Various `_run_*` functions |
| pilot-panel | cli/commands/selection.py | `_run_pilot_panel` |
| calibration-intake | cli/commands/reports.py | Various `_run_*` functions |
| recalibration-gate | cli/commands/reports.py | Various `_run_*` functions |

## Rules
- New commands should be registered here.
- Each command should map to exactly one handler function.
- Handlers should be in `cli/commands/` or `cli/main.py`.
- If a handler is moved, update this registry.

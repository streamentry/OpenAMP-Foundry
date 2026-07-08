# CLI Parser Construction into Command Modules

Guidelines for organizing CLI parser construction.

## Current Structure
```
cli/main.py              — Main parser and command routing
cli/commands/            — Command handler modules
  benchmark.py            — Bench-related handlers
  selection.py            — Selection-related handlers
  reports.py              — Report-related handlers
```

## Guidelines
- Each command group should have its own module in `cli/commands/`.
- The main parser in `main.py` should only register subparsers and route to handlers.
- Handler modules should not modify the parser after registration.
- New command groups should follow the same pattern.
- Keep handler functions focused — one function per command.

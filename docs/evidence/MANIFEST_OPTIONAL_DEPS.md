# Optional Dependency Manifest

Optional dependencies and their purposes.

| Extra | Package | Purpose |
|-------|---------|---------|
| dev | pytest | Test runner |
| dev | pytest-cov | Test coverage |
| dev | ruff | Linter |
| — | PyYAML | Config file parsing |
| — | jsonschema | Schema validation |

## Installation
```bash
# Core only
pip install openamp-foundry

# With dev tools
pip install "openamp-foundry[dev]"
```

## Rules
- Core dependencies must be kept minimal.
- Optional dependencies should be documented here.
- Adding a new optional dependency should be reviewed.
- No dependency should be optional if it's required for core functionality.

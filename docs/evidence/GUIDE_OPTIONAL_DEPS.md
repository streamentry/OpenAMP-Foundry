# Optional Dependency Explanation

Some dependencies are optional and only needed for specific features.

## Optional Extras
| Extra | Dependencies | Needed For |
|-------|-------------|------------|
| `dev` | pytest, ruff | Development and testing |
| `docs` | — | Building documentation (currently none required) |
| `external` | requests | External predictor submissions |

## How to Install
```bash
# Core only
pip install openamp-foundry

# With dev tools
pip install "openamp-foundry[dev]"

# With everything
pip install "openamp-foundry[dev,external]"
```

## Checking What's Installed
```bash
pip list | grep openamp-foundry
```

# Pyproject Consistency Checker

The pyproject consistency checker validates `pyproject.toml` against the actual package.

## Usage
```bash
python scripts/check_pyproject.py
```

## Checks Performed
- Python version requirement is present
- Console entrypoints reference existing modules
- Optional extras reference valid dependencies
- Package name matches the import name
- Package can be imported

## Exit Codes
| Code | Meaning |
|:----:|---------|
| 0 | All checks pass |
| 2 | File not found or parse error |
| 3 | Inconsistency found |

## Related
- `scripts/check_pyproject.py` — the checker script
- `pyproject.toml` — the project configuration file

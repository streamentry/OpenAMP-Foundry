# Package Metadata Completeness Checker

Validates that package metadata is complete.

## What It Checks
- `name` in pyproject.toml
- `version` is set
- `description` is present
- `requires-python` is specified
- `license` is declared
- `dependencies` list exists

## Usage
```bash
python scripts/check_pyproject.py
```

## Related
- `pyproject.toml` — the project configuration file
- `docs/evidence/GUIDE_PACKAGE_METADATA.md` — metadata guide

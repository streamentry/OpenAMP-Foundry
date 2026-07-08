# Package Metadata Completeness Checker

Verifies that pyproject.toml has all required metadata fields.

## Required Fields
- `name`
- `version`
- `description`
- `requires-python`
- `license`
- `dependencies`

## Optional but Recommended
- `readme`
- `authors`
- `classifiers`
- `keywords`
- `urls`

## Usage
```bash
python scripts/check_pyproject.py
```
The script checks for missing fields and reports them.

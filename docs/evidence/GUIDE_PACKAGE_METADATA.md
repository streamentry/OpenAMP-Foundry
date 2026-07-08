# Package Metadata Guide

How to maintain package metadata in pyproject.toml.

## Required Fields
- `name` — must match the import name (hyphens allowed)
- `version` — semantic versioning
- `description` — one-line summary
- `requires-python` — minimum Python version
- `license` — SPDX identifier

## Optional but Recommended
- `readme` — path to README file
- `authors` — list of maintainers
- `classifiers` — PyPI classifiers
- `keywords` — search keywords
- `urls` — project URLs (repository, docs, issues)

## Common Mistakes
- Version not bumped after changes
- Missing dependencies in `dependencies` or `[project.optional-dependencies]`
- Stale `classifiers` that don't match current Python version

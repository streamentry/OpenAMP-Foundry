# Dev Container Proposal

A development container (devcontainer) provides a consistent development
environment.

## Benefits
- Pre-configured Python environment
- Consistent across macOS, Linux, Windows
- No manual dependency installation
- VS Code integration

## Proposed Configuration
```json
{
  "name": "OpenAMP Foundry",
  "image": "mcr.microsoft.com/devcontainers/python:3.14",
  "postCreateCommand": "pip install -e .[dev]",
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python", "charliermarsh.ruff"]
    }
  }
}
```

## Status
Proposed — not yet implemented. Requires `.devcontainer/devcontainer.json`.

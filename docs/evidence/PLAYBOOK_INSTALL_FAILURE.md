# Scenario Playbook: Install Failure

**Scenario:** A user reports that `pip install -e ".[dev]"` fails.

## Steps

1. Ask for the full error message and Python version.
2. Check if the failure is OS-specific (macOS, Linux, Windows).
3. Common causes:
   - Python version < 3.11
   - Missing build dependencies (gcc, python3-dev)
   - Conflicting packages in the user's environment
4. Recommend a fresh virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```
5. If the problem persists, check `pyproject.toml` for dependency issues.
6. Document the resolution in the issue or discussion.

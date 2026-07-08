# Failed Quickstart Diagnosis Table

Common quickstart failures and how to fix them.

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| `command not found: openamp-foundry` | Package not installed | `pip install -e ".[dev]"` |
| `ModuleNotFoundError: No module named 'openamp_foundry'` | PYTHONPATH not set | `export PYTHONPATH=src` |
| `FileNotFoundError: examples/...` | Wrong working directory | Run from repo root |
| Tests fail | Wrong Python version | `python3 --version` (requires 3.11) |
| `make demo` produces no output | Previous run cleaned up | Re-run `make demo` |
| Git error | Not in a git repo | `git clone` first |

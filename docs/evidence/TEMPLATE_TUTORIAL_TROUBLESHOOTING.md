# Tutorial Troubleshooting Appendix Template

```markdown
## Troubleshooting

### `command not found: openamp-foundry`
Make sure you've installed the package: `pip install -e ".[dev]"`

### `ModuleNotFoundError: No module named 'openamp_foundry'`
Make sure the virtual environment is activated and PYTHONPATH is set:
`source .venv/bin/activate && export PYTHONPATH=src`

### Tests fail
Check your Python version: `python3 --version` (requires 3.11+)
If tests still fail, open an issue.
```

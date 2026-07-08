# Local Setup Troubleshooting Guide

## Quick Check
```bash
python3 --version        # Should be 3.11+
python3 -m venv .venv    # Should create a virtual environment
source .venv/bin/activate
pip install -e ".[dev]"  # Should install without errors
python3 -m pytest -q     # Should pass
```

## Common Issues

### `pip install` fails
- Try: `pip install --upgrade pip setuptools wheel`
- Try: `pip install -e ".[dev]" --no-build-isolation`

### Tests fail with import error
- Make sure you're in the virtual environment: `source .venv/bin/activate`
- Make sure PYTHONPATH includes `src`: `export PYTHONPATH=src`

### `make demo` fails
- Check that input files exist: `ls examples/sequences/demo_candidates.csv`
- Check that reference files exist: `ls examples/known_reference/demo_known_amps.csv`

### Still stuck?
Open an issue with the full error message and your OS/Python version.

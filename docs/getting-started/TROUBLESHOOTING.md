# Troubleshooting Install and Test Failures (A10)

This document covers the most common failures when setting up OpenAMP Foundry for the first time and how to fix them.

## Install failures

### `pip install -e .` fails with dependency conflict

**Symptom:** `ERROR: pip's dependency resolver does not currently take into account all the packages...`

**Fix:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

Using a fresh virtual environment avoids conflicts with system packages.

### `make doctor` reports missing packages

**Symptom:** `MISSING: [package]` in the doctor output.

**Fix:**
```bash
pip install -e ".[dev]"
```

If a specific package still fails:
```bash
pip install [package-name]
```

### Wrong Python version

**Symptom:** `make doctor` reports Python version mismatch or syntax errors on import.

**Fix:** OpenAMP Foundry requires Python 3.9+. Check your version:
```bash
python --version
```

If you have multiple Python versions, use `python3.9` or `python3.11` explicitly:
```bash
python3.11 -m venv .venv
```

## Test failures

### `pytest` fails with `ModuleNotFoundError`

**Symptom:**
```
ModuleNotFoundError: No module named 'openamp_foundry'
```

**Fix:** The package is not installed in editable mode. Run:
```bash
pip install -e .
```

Or set `PYTHONPATH` explicitly:
```bash
PYTHONPATH=src pytest tests/
```

### Test count regression fails

**Symptom:**
```
AssertionError: Test count 8158 deviates from BASELINE 8410 by more than 420.
```

**Cause:** Your local branch is behind `origin/main` and is missing test files that were merged. Or a PR updated the BASELINE but you haven't pulled.

**Fix:**
```bash
git fetch origin
git reset --hard origin/main
```

### `make agent-check` fails with claim violation

**Symptom:**
```
VIOLATION: Found forbidden claim language in [file]
```

**Cause:** A file contains language that overclaims computational results (e.g., "validated," "confirmed efficacy," "biological proof").

**Fix:** Replace the flagged language with approved computational-claim terms ("computationally nominated," "dry-lab candidate," "selected for review"). See `docs/CLAIM_BOUNDARY_RULES.md`.

### `make doc-links-check` reports broken links

**Symptom:**
```
BROKEN: docs/X.md → docs/Y.md (file not found)
```

**Fix:** The linked file was either renamed or deleted. Either update the link or restore the missing file. Check git log to see if it was recently moved:
```bash
git log --all --full-history -- docs/Y.md
```

### Benchmark test fails with threshold mismatch

**Symptom:**
```
AssertionError: precision_at_k 0.48 < PRECISION_AT_K_THRESHOLD 0.50
```

**Cause:** The benchmark result is below the passing threshold. Do NOT lower the threshold to make the test pass. Thresholds are governance decisions.

**Fix:** Investigate why the benchmark dropped. Check if a recent change to the scoring pipeline lowered quality. File an issue if the drop is unexpected.

## Environment issues

### `opencode` not found

**Symptom:** `command not found: opencode`

**Cause:** The `opencode` CLI is an optional dependency used in the agent dispatch loop.

**Fix:** Install via the opencode documentation or skip agent dispatch steps if running manually.

### `gh` not found (GitHub CLI)

**Symptom:** `command not found: gh`

**Fix:**
```bash
brew install gh       # macOS
gh auth login         # authenticate
```

### Pre-push hook is slow

**Symptom:** `git push` runs the full pytest suite and takes several minutes.

**Fix:** The pre-push hook runs tests by design (it prevents bad pushes). For fast iteration, use `git push --no-verify` only for feature branches where CI will catch failures. Never use `--no-verify` on main.

## Getting more help

- Check `CLAUDE.md` for the full operating contract
- Check `AGENTS.md` for agent-specific guidance
- File an issue with the `troubleshooting` label
- For test infrastructure questions, see `tests/README.md` if it exists

"""Verify all scripts/ Python files can be imported without errors."""
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path("scripts")
# Scripts that require external dependencies unavailable in test env
SKIP_SCRIPTS = {
    "scripts/external_validators/run_campR4.py",
    "scripts/external_validators/run_hemofinder.py",
    "scripts/external_validators/run_ampscanner.py",
    "scripts/external_validators/run_anticp.py",
}


def _get_python_scripts():
    for f in sorted(SCRIPTS_DIR.rglob("*.py")):
        rel = str(f.relative_to(SCRIPTS_DIR.parent))
        if rel in SKIP_SCRIPTS:
            continue
        yield f


@pytest.mark.parametrize("script_path", list(_get_python_scripts()), ids=lambda p: str(p))
def test_script_parses(script_path):
    try:
        with open(script_path) as f:
            compile(f.read(), script_path, "exec")
    except SyntaxError as e:
        pytest.fail(f"Syntax error in {script_path}: {e}")

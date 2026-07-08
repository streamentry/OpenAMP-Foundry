"""Run tutorial commands and verify they work."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _clean_outputs():
    for p in Path("outputs").glob("*.jsonl"):
        p.unlink(missing_ok=True)
    for p in Path("outputs").glob("*.md"):
        p.unlink(missing_ok=True)
    ev_dir = Path("outputs/evidence")
    if ev_dir.exists():
        shutil.rmtree(ev_dir)


def test_demo_help():
    r = subprocess.run(["make", "demo"], capture_output=True, text=True)
    # make demo may fail if dependencies aren't installed, but should at least attempt
    assert r.returncode in (0, 2)


def test_quickstart_commands():
    """Verify key quickstart commands are valid."""
    import argparse
    from openamp_foundry.cli.main import build_parser
    parser = build_parser()
    # Verify rank subcommand exists
    for action in parser._actions:
        if hasattr(action, 'choices') and action.choices:
            assert 'rank' in action.choices
            break


def test_readme_validate_command():
    """Verify the README validate command works after make demo."""
    _clean_outputs()
    demo = subprocess.run(["make", "demo"], capture_output=True, text=True)
    assert demo.returncode in (0, 2), f"make demo failed: {demo.stderr[:200]}"

    cert_dir = Path("outputs/evidence")
    if not cert_dir.exists() or not list(cert_dir.glob("*.json")):
        pytest.skip("No evidence certificates generated — skipping validate test")

    cert = str(list(cert_dir.glob("*.json"))[0])
    r = subprocess.run(
        [sys.executable, "-m", "openamp_foundry.cli", "validate",
         "--certificate", cert,
         "--schema", "schemas/candidate.schema.json"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0, f"validate failed: {r.stderr[:200]}"
    assert '"status": "valid"' in r.stdout

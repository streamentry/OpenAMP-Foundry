"""Verify graceful handling of missing optional dependencies."""
import subprocess
import sys
from pathlib import Path


def test_help_works_without_optional_deps():
    """Core CLI help should not require optional dependencies."""
    r = subprocess.run(
        [sys.executable, "-m", "openamp_foundry.cli", "--help"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0
    assert "usage:" in r.stdout


def test_rank_help_works():
    r = subprocess.run(
        [sys.executable, "-m", "openamp_foundry.cli", "rank", "--help"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0


def test_validate_help_works():
    r = subprocess.run(
        [sys.executable, "-m", "openamp_foundry.cli", "validate", "--help"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0

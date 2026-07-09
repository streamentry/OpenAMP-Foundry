"""Test validate-policy-version CLI."""
import subprocess
import sys


def test_validate_policy_version_help():
    r = subprocess.run(
        [sys.executable, "-m", "openamp_foundry.cli", "validate-policy-version", "--help"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0


def test_validate_policy_version_requires_args():
    r = subprocess.run(
        [sys.executable, "-m", "openamp_foundry.cli", "validate-policy-version"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode != 0  # Should fail without required args

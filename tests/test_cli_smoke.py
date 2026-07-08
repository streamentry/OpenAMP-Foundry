"""Smoke tests for CLI commands."""
import subprocess
import sys


def test_rank_help():
    r = subprocess.run([sys.executable, "-m", "openamp_foundry.cli", "rank", "--help"],
                       capture_output=True, text=True, env={"PYTHONPATH": "src"})
    assert r.returncode == 0
    assert "usage" in r.stdout.lower()


def test_validate_help():
    r = subprocess.run([sys.executable, "-m", "openamp_foundry.cli", "validate", "--help"],
                       capture_output=True, text=True, env={"PYTHONPATH": "src"})
    assert r.returncode == 0
    assert "usage" in r.stdout.lower()


def test_bench_help():
    r = subprocess.run([sys.executable, "-m", "openamp_foundry.cli", "bench", "--help"],
                       capture_output=True, text=True, env={"PYTHONPATH": "src"})
    assert r.returncode == 0


def test_version():
    from openamp_foundry import __version__
    assert isinstance(__version__, str)
    assert len(__version__) > 0

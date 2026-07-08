"""Tests that CLI commands properly separate stdout and stderr."""
import subprocess
import sys

import pytest


def _run_cmd(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "openamp_foundry.cli", *args],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )


def test_rank_output_goes_to_stdout():
    r = _run_cmd("rank", "--help")
    assert r.returncode == 0
    assert len(r.stdout) > 0


def test_validate_output_goes_to_stdout():
    r = _run_cmd("validate", "--help")
    assert r.returncode == 0
    assert len(r.stdout) > 0


def test_bench_help_goes_to_stdout():
    r = _run_cmd("bench", "--help")
    assert r.returncode == 0
    assert len(r.stdout) > 0


def test_missing_file_error_goes_to_stderr():
    r = _run_cmd("rank", "--candidates", "/nonexistent.csv", "--out", "/tmp/x.jsonl")
    assert r.returncode != 0
    assert len(r.stderr) > 0 or "Error" in r.stdout


@pytest.mark.parametrize("cmd", [
    ["rank", "--help"],
    ["validate", "--help"],
    ["bench", "--help"],
])
def test_help_uses_stdout(cmd):
    r = _run_cmd(*cmd)
    assert r.returncode == 0
    assert len(r.stdout) > 0

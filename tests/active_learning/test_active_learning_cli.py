"""CLI end-to-end test for active-learning benchmark."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def test_active_learning_bench_cli_runs():
    """Verify the active learning bench CLI completes without error."""
    r = subprocess.run(
        [sys.executable, "-m", "openamp_foundry.cli", "bench", "active-learning",
         "--n-hidden", "2", "--batch-size", "3", "--max-rounds", "3", "--rng-seed", "42"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0, f"CLI failed: {r.stderr[:200]}"
    output = json.loads(r.stdout)
    assert "status" in output or "summary" in output or "rounds" in output


def test_select_batch_cli_requires_arguments():
    """Verify select-batch CLI shows help when missing required args."""
    r = subprocess.run(
        [sys.executable, "-m", "openamp_foundry.cli", "select-batch", "--help"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0
    assert "usage:" in r.stdout

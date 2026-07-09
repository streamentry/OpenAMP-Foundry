"""Smoke test: cross-dataset benchmark runs without error."""
import subprocess
import sys


def test_cross_dataset_benchmark_smoke():
    r = subprocess.run(
        [sys.executable, "scripts/benchmarks/benchmark_cross_dataset.py"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0, f"Cross-dataset benchmark failed: {r.stderr[:200]}"

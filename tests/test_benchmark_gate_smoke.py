"""Smoke test: benchmark regression gate runs without error."""
import subprocess
import sys
from pathlib import Path


def test_bench_gate_script_runs():
    """Verify bench-gate script executes (even if it reports drift)."""
    r = subprocess.run(
        [sys.executable, "scripts/benchmarks/benchmark_gate.py",
         "--baseline", "outputs/metrics_snapshot.json",
         "--tolerance", "0.1"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    # Gate may exit 0 (pass) or 3 (drift detected) — either is acceptable
    assert r.returncode in (0, 3), f"bench-gate crashed: {r.stderr[:200]}"


def test_bench_multi_negatives_script_runs():
    """Verify multi-negative benchmark script runs."""
    r = subprocess.run(
        [sys.executable, "scripts/benchmarks/benchmark_multi_negatives.py"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0, f"multi-negatives failed: {r.stderr[:200]}"


def test_bench_gate_accepts_help():
    r = subprocess.run(
        [sys.executable, "scripts/benchmarks/benchmark_gate.py", "--help"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0

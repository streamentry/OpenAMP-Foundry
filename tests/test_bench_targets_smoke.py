"""Smoke test: verify key bench-* Makefile targets don't crash."""
import subprocess
import sys
from pathlib import Path


def test_bench_charge_distribution_smoke():
    r = subprocess.run(
        [sys.executable, "scripts/benchmarks/benchmark_charge_distribution.py",
         "--amp-csv", "examples/validation/known_amps_500.csv",
         "--decoy-csv", "examples/validation/random_background_500.csv"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0, f"Smoke failed: {r.stderr[:200]}"


def test_bench_calibration_smoke():
    r = subprocess.run(
        [sys.executable, "scripts/benchmarks/benchmark_calibration.py"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0, f"Smoke failed: {r.stderr[:200]}"


def test_bench_simulation_calibration_smoke():
    r = subprocess.run(
        [sys.executable, "scripts/benchmarks/benchmark_simulation_calibration.py"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0, f"Smoke failed: {r.stderr[:200]}"


def test_bench_cheap_enemies_smoke():
    r = subprocess.run(
        [sys.executable, "scripts/benchmarks/benchmark_cheap_enemy_comparison.py"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0, f"Smoke failed: {r.stderr[:200]}"

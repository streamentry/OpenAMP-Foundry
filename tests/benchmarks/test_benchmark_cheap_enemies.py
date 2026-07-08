"""Tests for the cheap enemy comparison benchmark."""
import subprocess
import sys

from scripts.benchmarks.benchmark_cheap_enemy_comparison import run_comparison


def test_run_comparison_returns_list():
    results = run_comparison()
    assert isinstance(results, list)
    assert len(results) > 0


def test_each_result_has_required_fields():
    results = run_comparison()
    for r in results:
        assert "proxy" in r
        assert "baseline_description" in r
        assert "sim_score" in r
        assert "baseline_score" in r
        assert "uncertainty" in r


def test_all_proxies_represented():
    results = run_comparison()
    proxies = {r["proxy"] for r in results}
    assert "MembraneProxy" in proxies
    assert "StructureProxy" in proxies


def test_cli_exit_0():
    r = subprocess.run(
        [sys.executable, "scripts/benchmarks/benchmark_cheap_enemy_comparison.py"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0

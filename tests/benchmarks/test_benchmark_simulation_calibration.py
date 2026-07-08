"""Tests for the simulation uncertainty calibration report."""
import subprocess
import sys

from scripts.benchmarks.benchmark_simulation_calibration import compute_calibration


def test_compute_calibration_returns_dict():
    report = compute_calibration()
    assert isinstance(report, dict)


def test_both_proxies_represented():
    report = compute_calibration()
    assert "membrane_proxy" in report["proxies"]
    assert "structure_proxy" in report["proxies"]


def test_each_proxy_has_required_stats():
    report = compute_calibration()
    for proxy_data in report["proxies"].values():
        assert proxy_data["n_sequences"] > 0
        assert 0 <= proxy_data["mean_uncertainty"] <= 1
        assert "length_correlation" in proxy_data
        assert "tier_counts" in proxy_data


def test_uncertainty_tier_distribution():
    report = compute_calibration()
    for proxy_data in report["proxies"].values():
        total = sum(proxy_data["tier_counts"].values())
        assert total == proxy_data["n_sequences"]


def test_flags_is_list():
    report = compute_calibration()
    assert isinstance(report["flags"], list)


def test_cli_exit_0():
    r = subprocess.run(
        [sys.executable, "scripts/benchmarks/benchmark_simulation_calibration.py"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0

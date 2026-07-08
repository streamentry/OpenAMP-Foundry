"""Tests for charge distribution benchmark."""
import subprocess
import sys

from scripts.benchmarks.benchmark_charge_distribution import charge_distribution


def test_charge_distribution_returns_dict():
    result = charge_distribution("examples/validation/known_amps_500.csv", "AMP")
    assert isinstance(result, dict)
    assert result["count"] > 0


def test_charge_distribution_has_required_fields():
    result = charge_distribution("examples/validation/known_amps_500.csv", "AMP")
    for key in ["mean_charge", "median_charge", "min_charge", "max_charge",
                "fraction_positive", "fraction_negative", "fraction_neutral"]:
        assert key in result


def test_decoy_charge_distribution():
    result = charge_distribution("examples/validation/random_background_500.csv", "Decoy")
    assert result["count"] > 0


def test_cli_exit_0():
    r = subprocess.run(
        [sys.executable, "scripts/benchmarks/benchmark_charge_distribution.py",
         "--amp-csv", "examples/validation/known_amps_500.csv",
         "--decoy-csv", "examples/validation/random_background_500.csv"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0

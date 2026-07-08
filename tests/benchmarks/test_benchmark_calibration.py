"""Tests for the calibration benchmark."""
import subprocess
import sys

from scripts.benchmarks.benchmark_calibration import compute_calibration_metrics


def test_compute_returns_dict():
    metrics = compute_calibration_metrics()
    assert isinstance(metrics, dict)
    assert "error" not in metrics


def test_brier_score_in_range():
    metrics = compute_calibration_metrics()
    assert 0 <= metrics["brier_score"] <= 1


def test_brier_decomposition_has_three_components():
    metrics = compute_calibration_metrics()
    d = metrics["brier_decomposition"]
    assert "reliability" in d
    assert "resolution" in d
    assert "uncertainty" in d


def test_calibration_slope_is_float():
    metrics = compute_calibration_metrics()
    assert isinstance(metrics["calibration_slope"], float)


def test_reliability_diagram_has_bins():
    metrics = compute_calibration_metrics()
    assert len(metrics["reliability_diagram"]) > 0
    for b in metrics["reliability_diagram"]:
        assert "mean_prediction" in b
        assert "actual_fraction" in b
        assert "gap" in b


def test_cli_exit_0():
    r = subprocess.run(
        [sys.executable, "scripts/benchmarks/benchmark_calibration.py"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0

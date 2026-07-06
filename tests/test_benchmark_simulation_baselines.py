"""Tests for the simulation cheap-baseline benchmark."""

import json
import subprocess
import sys

from openamp_foundry.features.physchem import _HYDROPHOBICITY
from scripts.benchmark_simulation_baselines import (
    _auroc,
    _mean_eisenberg,
    run_simulation_baselines,
)


def test_mean_eisenberg_known():
    score = _mean_eisenberg("AAAA")
    expected = _HYDROPHOBICITY["A"]
    assert score == expected


def test_mean_eisenberg_empty():
    assert _mean_eisenberg("") == 0.0


def test_auroc_all_higher():
    assert _auroc([1.0, 1.0], [0.0, 0.0]) == 1.0


def test_auroc_all_lower():
    assert _auroc([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_auroc_empty():
    assert _auroc([], []) == 0.5


def test_benchmark_runs():
    result = run_simulation_baselines()
    assert "error" not in result
    assert result["n_hemolytic"] > 3
    assert result["n_selective"] > 3


def test_benchmark_returns_expected_keys():
    result = run_simulation_baselines()
    for signal in ["bacterial_binding", "selectivity_ratio", "helix_weight", "non_helical"]:
        assert signal in result["results"]
        r = result["results"][signal]
        for key in ["signal_auroc", "baseline_auroc", "delta", "verdict"]:
            assert key in r, f"{signal} missing {key}"


def test_benchmark_all_no_improvement():
    """Current honest finding: NO simulation signal beats its cheap baseline."""
    result = run_simulation_baselines()
    for signal, data in result["results"].items():
        assert data["verdict"] == "NO_IMPROVEMENT", f"{signal} unexpectedly improved"


def test_benchmark_summary_all_blocked():
    result = run_simulation_baselines()
    assert result["summary"]["all_blocked"] is True


def test_benchmark_heli_weight_near_heli_propensity():
    """helix_weight and helix_propensity should have similar AUROC
    (both measure helicity, just normalized differently)."""
    result = run_simulation_baselines()
    hw = result["results"]["helix_weight"]
    hp_auroc = hw["baseline_auroc"]
    hw_auroc = hw["signal_auroc"]
    assert abs(hw_auroc - hp_auroc) < 0.1


def test_cli_exit_code():
    result = subprocess.run(
        [sys.executable, "scripts/benchmark_simulation_baselines.py"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert result.returncode == 3


def test_cli_output_contains_verdict():
    result = subprocess.run(
        [sys.executable, "scripts/benchmark_simulation_baselines.py"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert "NO_IMPROVEMENT" in result.stdout


def test_cli_writes_output_json(tmp_path):
    out = tmp_path / "baselines.json"
    subprocess.run(
        [sys.executable, "scripts/benchmark_simulation_baselines.py", "--out", str(out)],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["summary"]["all_blocked"] is True

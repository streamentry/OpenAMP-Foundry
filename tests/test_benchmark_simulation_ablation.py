"""Tests for the simulation ablation benchmark."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from openamp_foundry.simulation.membrane import MembraneProxy
from openamp_foundry.simulation.structure import StructureProxy
from scripts.benchmark_simulation_ablation import (
    _auroc,
    _simulation_composite,
    run_simulation_ablation_benchmark,
)


def test_auroc_all_higher():
    assert _auroc([1.0, 1.0], [0.0, 0.0]) == 1.0


def test_auroc_all_lower():
    assert _auroc([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_auroc_chance():
    assert _auroc([1.0, 0.0], [1.0, 0.0]) == 0.5


def test_auroc_empty():
    assert _auroc([], []) == 0.5


def test_simulation_composite_ensemble_only():
    score = _simulation_composite(1.0, 0.0, 1.0, 1.0)
    assert 0.5 <= score <= 1.0


def test_simulation_composite_range():
    score = _simulation_composite(0.0, 0.0, 0.0, 1.0)
    assert 0.0 <= score <= 1.0


def test_simulation_composite_helical_bonus():
    helical = _simulation_composite(0.5, 0.5, 1.0, 0.0)
    non_helical = _simulation_composite(0.5, 0.5, 1.0, 1.0)
    assert helical > non_helical


def test_benchmark_runs_on_500_set():
    result = run_simulation_ablation_benchmark()
    assert "error" not in result
    assert result["n_amps"] == 500
    assert result["n_decoys"] == 500


def test_benchmark_returns_expected_keys():
    result = run_simulation_ablation_benchmark()
    r = result["results"]
    for key in ["ensemble_only", "ensemble_plus_simulation", "delta",
                "bacterial_binding_auroc", "verdict"]:
        assert key in r, f"Missing key: {key}"


def test_benchmark_verdict_is_no_improvement():
    """Current honest finding: simulation modules are designed for within-AMP
    tasks and do NOT improve AMP-vs-decoy discrimination."""
    result = run_simulation_ablation_benchmark()
    assert result["results"]["verdict"] == "NO_IMPROVEMENT"


def test_benchmark_delta_negative():
    result = run_simulation_ablation_benchmark()
    assert result["results"]["delta"] < 0


def test_benchmark_bacterial_binding_has_signal():
    """bacterial_binding AUROC > 0.7: genuine non-charge signal from
    Wimley-White interfacial scale + hydrophobic moment."""
    result = run_simulation_ablation_benchmark()
    assert result["results"]["bacterial_binding_auroc"] > 0.7


def test_cli_exit_code():
    """Benchmark exits 3 when verdict is NO_IMPROVEMENT."""
    result = subprocess.run(
        [sys.executable, "scripts/benchmark_simulation_ablation.py"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert result.returncode == 3


def test_cli_output_contains_verdict():
    result = subprocess.run(
        [sys.executable, "scripts/benchmark_simulation_ablation.py"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert "NO_IMPROVEMENT" in result.stdout or "NO_IMPROVEMENT" in result.stderr


def test_cli_writes_output_json(tmp_path):
    out = tmp_path / "ablation.json"
    result = subprocess.run(
        [sys.executable, "scripts/benchmark_simulation_ablation.py", "--out", str(out)],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["results"]["verdict"] == "NO_IMPROVEMENT"


def test_individual_module_scores_accessible():
    membrane = MembraneProxy()
    structure = StructureProxy()
    mem = membrane.simulate("GIGKFLHSAKKFGKAFVGEIMNS")
    struct = structure.simulate("GIGKFLHSAKKFGKAFVGEIMNS")
    assert "bacterial_binding" in mem.scores
    assert "non_helical" in struct.scores
    assert "helix_weight" in struct.scores


def test_error_on_missing_amp_csv():
    result = run_simulation_ablation_benchmark(amp_csv="nonexistent.csv")
    assert "error" in result

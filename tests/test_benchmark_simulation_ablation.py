"""Tests for the simulation ablation benchmark."""

import json
import subprocess
import sys

from openamp_foundry.simulation.membrane import MembraneProxy
from openamp_foundry.simulation.structure import StructureProxy
from scripts.benchmark_simulation_ablation import (
    _auroc,
    _simulation_composite,
    run_amp_vs_decoy,
    run_within_amp,
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


def test_amp_vs_decoy_runs_on_500_set():
    result = run_amp_vs_decoy()
    assert "error" not in result
    assert result["n_amps"] == 500
    assert result["n_decoys"] == 500


def test_amp_vs_decoy_returns_expected_keys():
    result = run_amp_vs_decoy()
    r = result["results"]
    for key in ["ensemble_only", "ensemble_plus_simulation", "delta",
                "bacterial_binding_auroc", "verdict"]:
        assert key in r


def test_amp_vs_decoy_verdict_no_improvement():
    result = run_amp_vs_decoy()
    assert result["results"]["verdict"] == "NO_IMPROVEMENT"


def test_amp_vs_decoy_delta_negative():
    result = run_amp_vs_decoy()
    assert result["results"]["delta"] < 0


def test_amp_vs_decoy_bacterial_binding_has_signal():
    result = run_amp_vs_decoy()
    assert result["results"]["bacterial_binding_auroc"] > 0.7


def test_within_amp_runs():
    result = run_within_amp()
    assert "error" not in result
    assert result["n_hemolytic"] > 3
    assert result["n_selective"] > 3


def test_within_amp_returns_expected_keys():
    result = run_within_amp()
    r = result["results"]
    for key in ["ensemble", "activity", "safety", "rich_selectivity",
                "bacterial_binding", "selectivity_ratio", "non_helical",
                "helix_weight", "best_pipeline", "best_simulation", "delta", "verdict"]:
        assert key in r


def test_within_amp_delta_negative():
    """Simulation modules do NOT improve over rich_selectivity for
    hemolysis detection (current honest finding)."""
    result = run_within_amp()
    assert result["results"]["delta"] < 0


def test_within_amp_rich_selectivity_best_pipeline():
    """rich_selectivity is the best existing hemolysis detector."""
    result = run_within_amp()
    r = result["results"]
    assert r["rich_selectivity"] >= r["ensemble"]
    assert r["rich_selectivity"] >= r["safety"]


def test_within_amp_helix_weight_has_signal():
    """helix_weight has moderate hemolysis detection signal —
    hemolytic AMPs tend to be more helical."""
    result = run_within_amp()
    assert result["results"]["helix_weight"] > 0.5


def test_within_amp_verdict_no_improvement():
    result = run_within_amp()
    assert result["results"]["verdict"] == "NO_IMPROVEMENT"


def test_cli_amp_vs_decoy_exit_code():
    result = subprocess.run(
        [sys.executable, "scripts/benchmark_simulation_ablation.py", "--mode", "amp-vs-decoy"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert result.returncode == 3


def test_cli_within_amp_exit_code():
    result = subprocess.run(
        [sys.executable, "scripts/benchmark_simulation_ablation.py", "--mode", "within-amp"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert result.returncode == 3


def test_cli_writes_output_json(tmp_path):
    out = tmp_path / "ablation.json"
    subprocess.run(
        [sys.executable, "scripts/benchmark_simulation_ablation.py",
         "--mode", "amp-vs-decoy", "--out", str(out)],
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


def test_error_on_missing_hemolysis_csv():
    result = run_within_amp(hemolysis_csv="nonexistent.csv")
    assert "error" in result

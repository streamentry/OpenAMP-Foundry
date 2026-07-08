"""Provide replay fixtures for testing adapters offline."""
from openamp_foundry.simulation.interfaces import SimulationResult


def sample_membrane_result() -> SimulationResult:
    return SimulationResult(
        module="membrane_proxy",
        version="0.1.0",
        scope=["bacterial_membrane_binding", "mammalian_membrane_binding"],
        scores={"bacterial_binding": 0.75, "mammalian_binding": 0.3, "selectivity_ratio": 1.5},
        uncertainty=0.2,
        calibration_set=None,
        validated_against=[],
        notes=["Sample result for offline testing"],
    )


def sample_structure_result() -> SimulationResult:
    return SimulationResult(
        module="structure_proxy",
        version="0.1.0",
        scope=["secondary_structure_prediction"],
        scores={"helix_weight": 0.6, "sheet_weight": 0.2, "coil_weight": 0.2, "non_helical": 0.0},
        uncertainty=0.15,
        calibration_set=None,
        validated_against=[],
        notes=["Sample result for offline testing"],
    )


def test_sample_membrane():
    r = sample_membrane_result()
    assert r.module == "membrane_proxy"
    assert 0 <= r.scores["bacterial_binding"] <= 1


def test_sample_structure():
    r = sample_structure_result()
    assert r.module == "structure_proxy"
    assert abs(sum([r.scores["helix_weight"], r.scores["sheet_weight"], r.scores["coil_weight"]]) - 1.0) < 0.01

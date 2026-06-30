"""Tests for the virtual assay layer interfaces and contracts."""


from openamp_foundry.simulation.dummy import DummyMembraneProxy
from openamp_foundry.simulation.interfaces import SimulationResult


def test_simulation_result_schema():
    """Verify the SimulationResult can be instantiated with the required fields."""
    result = SimulationResult(
        module="test_module",
        version="1.0.0",
        scope=["test_scope"],
        scores={"test_score": 0.95},
        uncertainty=0.1,
        calibration_set="test_dataset",
        validated_against=["test_validation_set"],
        notes=["Test note"]
    )
    
    assert result.module == "test_module"
    assert result.uncertainty == 0.1
    assert "test_note" not in result.notes
    assert "Test note" in result.notes


def test_dummy_proxy_contract():
    """Verify the DummyMembraneProxy obeys the interface contract."""
    proxy = DummyMembraneProxy()
    
    # 1. Simulate must return a SimulationResult
    result = proxy.simulate("KKLFKKILKYL")
    assert isinstance(result, SimulationResult)
    
    # 2. Uncertainty must be surfaced
    assert result.uncertainty == 1.0
    
    # 3. Must have a baseline comparison mechanism
    baseline = proxy.get_baseline()
    baseline_score = baseline.evaluate("KKLFKKILKYL")
    assert isinstance(baseline_score, float)

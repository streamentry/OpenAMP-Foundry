"""Tests for the virtual assay layer interfaces and contracts."""


from openamp_foundry.simulation.dummy import DummyMembraneProxy
from openamp_foundry.simulation.interfaces import (
    ExternalSimulationAdapter,
    SimulationResult,
    VirtualAssayProxy,
)
from openamp_foundry.simulation.membrane import MembraneProxy
from openamp_foundry.simulation.structure import StructureProxy


def _get_all_proxy_classes():
    return [
        MembraneProxy(),
        StructureProxy(),
        DummyMembraneProxy(),
    ]


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


def _mock_simulate(seq: str) -> SimulationResult:
    return SimulationResult(
        module="mock", version="1.0", scope=["mock"],
        scores={"mock_score": 0.75}, uncertainty=0.2,
        calibration_set=None, validated_against=[],
    )


class TestCheapestBaselineDeclaration:
    """Every VirtualAssayProxy must declare what cheap baseline it must beat."""

    def test_all_proxies_have_baseline_description(self):
        for proxy in _get_all_proxy_classes():
            desc = proxy.cheapest_baseline_description
            assert isinstance(desc, str), f"{type(proxy).__name__} missing cheapest_baseline_description"
            assert len(desc) > 10, f"{type(proxy).__name__} baseline description too short"

    def test_baseline_description_is_not_default(self):
        for proxy in _get_all_proxy_classes():
            desc = proxy.cheapest_baseline_description
            assert "TODO" not in desc, f"{type(proxy).__name__} has placeholder baseline"
            assert "baseline" not in desc.lower() or "heuristic" in desc.lower() or "alone" in desc.lower() or "index" in desc.lower() or "signal" in desc.lower()

    def test_external_adapter_has_baseline_description(self):
        adapter = ExternalSimulationAdapter(
            name="test", version="1.0", simulate_fn=_mock_simulate,
        )
        desc = adapter.cheapest_baseline_description
        assert isinstance(desc, str)
        assert len(desc) > 10

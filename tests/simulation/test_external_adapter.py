"""Tests for the external simulation adapter."""

from openamp_foundry.simulation.interfaces import (
    ExternalSimulationAdapter,
    SimulationResult,
    _error_result,
)


def _mock_simulate(seq: str) -> SimulationResult:
    return SimulationResult(
        module="mock",
        version="1.0",
        scope=["mock"],
        scores={"mock_score": 0.75},
        uncertainty=0.2,
        calibration_set=None,
        validated_against=[],
        notes=["Mock simulation"],
    )


def _failing_simulate(seq: str) -> SimulationResult:
    msg = f"Artificial failure for: {seq}"
    return _error_result("fail", "1.0", msg)


def test_adapter_without_module_requirement():
    adapter = ExternalSimulationAdapter(
        name="mock", version="1.0", simulate_fn=_mock_simulate,
    )
    assert adapter.is_available() is True


def test_adapter_simulate_returns_result():
    adapter = ExternalSimulationAdapter(
        name="mock", version="1.0", simulate_fn=_mock_simulate,
    )
    result = adapter.simulate("KKLFKKILKYL")
    assert isinstance(result, SimulationResult)
    assert result.scores["mock_score"] == 0.75
    assert result.uncertainty == 0.2


def test_adapter_with_module_not_installed():
    adapter = ExternalSimulationAdapter(
        name="does_not_exist", version="1.0",
        simulate_fn=_mock_simulate,
        required_module="nonexistent_module_xyz",
    )
    assert adapter.is_available() is False


def test_adapter_fails_gracefully_when_module_missing():
    adapter = ExternalSimulationAdapter(
        name="ghost", version="1.0",
        simulate_fn=_mock_simulate,
        required_module="nonexistent_module_xyz",
    )
    result = adapter.simulate("KKLFKKILKYL")
    assert isinstance(result, SimulationResult)
    assert result.uncertainty == 1.0
    assert result.scores.get("error", 0.0) == -1.0
    assert "not installed" in result.notes[0]


def test_adapter_returns_error_result_on_failure():
    adapter = ExternalSimulationAdapter(
        name="failer", version="1.0", simulate_fn=_failing_simulate,
    )
    result = adapter.simulate("TEST")
    assert result.uncertainty == 1.0
    assert "Artificial failure" in result.notes[0]


def test_adapter_handles_exception_gracefully():
    def _raise_error(seq: str) -> SimulationResult:
        raise ValueError("Simulation crashed")
    
    adapter = ExternalSimulationAdapter(
        name="crash", version="1.0", simulate_fn=_raise_error,
    )
    result = adapter.simulate("K" * 10)
    assert isinstance(result, SimulationResult)
    assert result.uncertainty == 1.0
    assert "ValueError" in result.notes[0]


def test_adapter_has_baseline():
    adapter = ExternalSimulationAdapter(
        name="mock", version="1.0", simulate_fn=_mock_simulate,
    )
    baseline = adapter.get_baseline()
    score = baseline.evaluate("KKLFKKILKYL")
    assert score == 0.5


def test_adapter_module_name():
    adapter = ExternalSimulationAdapter(
        name="martini_md", version="1.0", simulate_fn=_mock_simulate,
    )
    assert adapter.module_name == "martini_md"


def test_adapter_version_in_result():
    adapter = ExternalSimulationAdapter(
        name="tool", version="2.0.1", simulate_fn=_mock_simulate,
    )
    result = adapter.simulate("KKLFKKILKYL")
    assert result.version == "2.0.1"


def test_adapter_scope_default():
    adapter = ExternalSimulationAdapter(
        name="tool", version="1.0", simulate_fn=_mock_simulate,
    )
    result = adapter.simulate("KKLFKKILKYL")
    assert "external_simulation" in result.scope


def test_adapter_scope_custom():
    adapter = ExternalSimulationAdapter(
        name="tool", version="1.0", simulate_fn=_mock_simulate,
        scope=["alpha_fold", "custom"],
    )
    result = adapter.simulate("KKLFKKILKYL")
    assert "alpha_fold" in result.scope
    assert "custom" in result.scope


def test_error_result_schema():
    result = _error_result("mod", "1.0", "test error")
    assert result.module == "mod"
    assert result.version == "1.0"
    assert result.uncertainty == 1.0
    assert result.scores["error"] == -1.0

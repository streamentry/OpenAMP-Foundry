"""Dummy proxy implementation to demonstrate the virtual assay contract."""

from .interfaces import EmulatorBaseline, SimulationResult, VirtualAssayProxy


class DummyBomanBaseline(EmulatorBaseline):
    """A trivial cheap baseline heuristic (e.g. Boman index proxy)."""
    
    def evaluate(self, sequence: str) -> float:
        # Trivial dummy calculation for demonstration
        return len(sequence) * 0.1


class DummyMembraneProxy(VirtualAssayProxy):
    """A stub membrane proxy demonstrating the SimulationResult schema."""
    
    def simulate(self, sequence: str) -> SimulationResult:
        # Trivial dummy calculation
        mock_binding_energy = -5.0 * (len(sequence) / 10.0)
        
        return SimulationResult(
            module="dummy_membrane_proxy",
            version="0.1.0",
            scope=["bacterial_membrane_binding"],
            scores={"binding_energy": mock_binding_energy},
            uncertainty=1.0,  # 1.0 = completely uncertain (no real calibration data)
            calibration_set=None,
            validated_against=[],
            notes=["This is a stub implementation. Do not use for biological decisions."]
        )
    
    def get_baseline(self) -> EmulatorBaseline:
        return DummyBomanBaseline()

    @property
    def cheapest_baseline_description(self) -> str:
        return "sequence length alone (dummy proxy uses length as sole signal)"

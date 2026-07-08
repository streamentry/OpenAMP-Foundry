"""Interfaces and schemas for the OpenAMP virtual assay layer."""

import abc
import importlib
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class SimulationResult:
    """Schema for outputs from any virtual assay or simulation module.
    
    This exact schema is mandated by docs/engineering/ARCHITECTURE.md.
    """
    module: str
    version: str
    scope: List[str]
    scores: Dict[str, float]
    uncertainty: float
    calibration_set: Optional[str]
    validated_against: List[str]
    notes: List[str] = field(default_factory=list)


class EmulatorBaseline(abc.ABC):
    """Contract for cheap heuristic baselines.
    
    Every virtual assay must prove it beats a cheap baseline 
    to avoid 'simulation theater'.
    """
    
    @abc.abstractmethod
    def evaluate(self, sequence: str) -> float:
        """Evaluate the sequence using the cheap heuristic baseline."""
        pass


class VirtualAssayProxy(abc.ABC):
    """Abstract base class for all virtual assay modules.
    
    Modules (e.g., membrane interaction proxies, stability proxies, 
    or learned surrogate models) must implement this interface.
    """
    
    @abc.abstractmethod
    def simulate(self, sequence: str) -> SimulationResult:
        """Run the virtual assay simulation on the sequence.
        
        Returns:
            SimulationResult object containing scores and explicit uncertainty.
        """
        pass
    
    @abc.abstractmethod
    def get_baseline(self) -> EmulatorBaseline:
        """Return the baseline heuristic this simulation must beat."""
        pass

    @property
    @abc.abstractmethod
    def cheapest_baseline_description(self) -> str:
        """Human-readable description of the simplest explanation this module must outperform.

        Examples:
          'charge density alone (net charge at pH 7.4)'
          'sequence length alone'
          'hydrophobicity (GRAVY index)'
          'Boman index (heuristic AMP activity proxy)'
        """
        pass


def _error_result(
    module: str,
    version: str,
    error_msg: str,
) -> SimulationResult:
    """Create a SimulationResult for a failed external simulation."""
    return SimulationResult(
        module=module,
        version=version,
        scope=[],
        scores={"error": -1.0},
        uncertainty=1.0,
        calibration_set=None,
        validated_against=[],
        notes=[f"External simulation failed: {error_msg}"],
    )


class ExternalSimulationAdapter(VirtualAssayProxy):
    """Adapter for third-party external simulation modules.
    
    Wraps an external simulation function (e.g., calling Martini MD,
    AlphaFold, or a REST API) into the VirtualAssayProxy interface.
    
    The wrapped function must accept (sequence: str) -> SimulationResult.
    Fails gracefully with uncertainty=1.0 if the module errors.
    
    Example::
    
        def run_martini(seq: str) -> SimulationResult:
            ...
        
        adapter = ExternalSimulationAdapter(
            name="martini_membrane",
            version="0.1.0",
            simulate_fn=run_martini,
            required_module="martini",
        )
        result = adapter.simulate("GIGKFLHSAKKFGKAFVGEIMNS")
    """
    
    def __init__(
        self,
        name: str,
        version: str,
        simulate_fn: Callable[[str], SimulationResult],
        required_module: str | None = None,
        scope: list[str] | None = None,
    ) -> None:
        self._name = name
        self._version = version
        self._simulate_fn = simulate_fn
        self._required_module = required_module
        self._scope = scope or ["external_simulation"]
    
    def is_available(self) -> bool:
        """Check whether the external module can be imported.
        
        Returns True if no module requirement is specified or the
        module can be imported. This lets callers fail gracefully
        when an external dependency is not installed.
        """
        if self._required_module is None:
            return True
        try:
            importlib.import_module(self._required_module)
            return True
        except ImportError:
            return False
    
    def simulate(self, sequence: str) -> SimulationResult:
        if not self.is_available():
            return _error_result(
                self._name, self._version,
                f"Required module '{self._required_module}' is not installed. "
                f"Install it with: pip install {self._required_module}",
            )
        try:
            result = self._simulate_fn(sequence)
            result.module = self._name
            result.version = self._version
            result.scope = self._scope
            return result
        except Exception as exc:
            return _error_result(
                self._name, self._version,
                f"Simulation raised {type(exc).__name__}: {exc}",
            )
    
    def get_baseline(self) -> EmulatorBaseline:
        return _ExternalFallbackBaseline(self._name)

    @property
    def module_name(self) -> str:
        return self._name

    @property
    def cheapest_baseline_description(self) -> str:
        return f"fallback baseline (0.5 — no signal) for external module '{self._name}'"


class _ExternalFallbackBaseline(EmulatorBaseline):
    """Fallback baseline for external modules: returns 0.5 (no signal)."""
    
    def __init__(self, name: str) -> None:
        self._name = name
    
    def evaluate(self, sequence: str) -> float:
        return 0.5

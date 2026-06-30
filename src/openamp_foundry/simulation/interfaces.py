"""Interfaces and schemas for the OpenAMP virtual assay layer."""

import abc
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SimulationResult:
    """Schema for outputs from any virtual assay or simulation module.
    
    This exact schema is mandated by docs/ARCHITECTURE.md.
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

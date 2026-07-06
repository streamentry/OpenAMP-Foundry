"""Virtual assay simulation layer for OpenAMP Foundry."""

from .gate import SimulationGateVerdict, evaluate_simulation_gate
from .interfaces import (
    EmulatorBaseline,
    ExternalSimulationAdapter,
    SimulationResult,
    VirtualAssayProxy,
)
from .membrane import MembraneProxy
from .structure import StructureProxy

__all__ = [
    "SimulationResult",
    "VirtualAssayProxy",
    "ExternalSimulationAdapter",
    "EmulatorBaseline",
    "MembraneProxy",
    "StructureProxy",
    "SimulationGateVerdict",
    "evaluate_simulation_gate",
]

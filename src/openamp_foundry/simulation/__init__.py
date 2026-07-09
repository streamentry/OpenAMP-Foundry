"""Virtual assay simulation layer for OpenAMP Foundry."""

from .gate import SimulationGateVerdict, evaluate_simulation_gate
from .interfaces import (
    EmulatorBaseline,
    ExternalSimulationAdapter,
    SimulationResult,
    VirtualAssayProxy,
)
from .membrane import MembraneProxy
from .module_registry import (
    SIMULATION_MODULE_REGISTRY,
    SimulationModuleEntry,
    get_active_modules,
    get_module_entry,
    list_module_entries,
    registry_summary,
    validate_registry,
)
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
    "SimulationModuleEntry",
    "SIMULATION_MODULE_REGISTRY",
    "get_module_entry",
    "list_module_entries",
    "get_active_modules",
    "registry_summary",
    "validate_registry",
]

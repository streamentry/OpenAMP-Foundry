"""Virtual assay simulation layer for OpenAMP Foundry."""

from .adapter_gate import (
    AdapterGateResult,
    FAIL_CLOSED_REASONS,
    evaluate_adapter_gate,
    run_adapter_gate_batch,
)
from .provenance import (
    SimulationProvenanceRecord,
    make_provenance_record,
    provenance_summary,
    validate_provenance_record,
)
from .baseline_registry import (
    BASELINE_DECLARATIONS,
    BaselineDeclaration,
    check_baseline_requirement,
    get_baseline_declaration,
    list_baseline_declarations,
    validate_baseline_declarations,
)
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
from .result_validator import (
    validate_simulation_result,
    validate_simulation_result_batch,
)
from .structure import StructureProxy

__all__ = [
    "AdapterGateResult",
    "FAIL_CLOSED_REASONS",
    "evaluate_adapter_gate",
    "run_adapter_gate_batch",
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
    "SimulationProvenanceRecord",
    "make_provenance_record",
    "validate_provenance_record",
    "provenance_summary",
    "validate_simulation_result",
    "validate_simulation_result_batch",
    "BaselineDeclaration",
    "BASELINE_DECLARATIONS",
    "get_baseline_declaration",
    "list_baseline_declarations",
    "check_baseline_requirement",
    "validate_baseline_declarations",
]

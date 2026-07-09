"""Virtual assay simulation layer for OpenAMP Foundry."""

from .scope_checker import (
    ScopeCoverageResult,
    check_scope_coverage,
    check_result_scope,
    scope_coverage_report,
)
from .deprecation_enforcer import (
    BLOCKED_STATUSES,
    DeprecationCheckResult,
    check_module_deprecation,
    enforce_deprecation,
    run_deprecation_check_batch,
)
from .adapter_gate import (
    AdapterGateResult,
    FAIL_CLOSED_REASONS,
    evaluate_adapter_gate,
    run_adapter_gate_batch,
)
from .ensemble_checker import (
    AGREEMENT_LEVELS,
    EnsembleAgreementResult,
    check_ensemble_agreement,
    run_ensemble_check_batch,
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
from .evidence_packet import (
    SimulationEvidencePacket,
    assemble_evidence_packet,
    evidence_packet_summary,
)
from .ci_reporter import (
    ScoreCI,
    ci_report,
    compare_cis,
    compute_score_ci,
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
    "SimulationEvidencePacket",
    "assemble_evidence_packet",
    "evidence_packet_summary",
    "ScopeCoverageResult",
    "check_scope_coverage",
    "check_result_scope",
    "scope_coverage_report",
    "BLOCKED_STATUSES",
    "DeprecationCheckResult",
    "check_module_deprecation",
    "enforce_deprecation",
    "run_deprecation_check_batch",
    "AdapterGateResult",
    "FAIL_CLOSED_REASONS",
    "evaluate_adapter_gate",
    "run_adapter_gate_batch",
    "AGREEMENT_LEVELS",
    "EnsembleAgreementResult",
    "check_ensemble_agreement",
    "run_ensemble_check_batch",
    "ScoreCI",
    "compute_score_ci",
    "compare_cis",
    "ci_report",
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

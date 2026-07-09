"""Simulation module registry — tracks status and evidence level of each
virtual assay module, preventing undocumented use of simulation outputs.

Dry-lab only. This is a registry of computational modules, not biological proof.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from openamp_foundry.evidence.synthetic_result_policy import PROOF_LADDER_LEVELS

SimulationModuleStatus = Literal["active", "experimental", "deprecated", "unavailable"]

VALID_STATUSES: set[str] = {"active", "experimental", "deprecated", "unavailable"}


@dataclass
class SimulationModuleEntry:
    module_id: str
    name: str
    description: str
    status: str
    evidence_level: int
    baseline_comparison: str
    scope: list[str] = field(default_factory=list)
    maintainer: str = "pipeline"
    notes: str = ""


SIMULATION_MODULE_REGISTRY: list[SimulationModuleEntry] = [
    SimulationModuleEntry(
        module_id="membrane_proxy",
        name="Membrane Proxy",
        description="Wimley-White interfacial/octanol scale coarse-grained bacterial and mammalian binding energy scores",
        status="active",
        evidence_level=2,
        baseline_comparison="charge density (net charge at pH 7.4)",
        scope=["bacterial_membrane_binding"],
        maintainer="pipeline",
        notes="",
    ),
    SimulationModuleEntry(
        module_id="structure_proxy",
        name="Structure Proxy",
        description="Chou-Fasman 3-state secondary structure prediction (helix/sheet/coil) with non-helical flag",
        status="experimental",
        evidence_level=2,
        baseline_comparison="length alone (no structural signal)",
        scope=["helical_structure_prediction"],
        maintainer="pipeline",
        notes="",
    ),
    SimulationModuleEntry(
        module_id="dummy_membrane_proxy",
        name="Dummy Membrane Proxy",
        description="Stub membrane proxy for testing only",
        status="deprecated",
        evidence_level=1,
        baseline_comparison="charge density (net charge at pH 7.4)",
        scope=["bacterial_membrane_binding"],
        maintainer="pipeline",
        notes="stub for testing only; do not use for scoring",
    ),
    SimulationModuleEntry(
        module_id="external_adapter_placeholder",
        name="External Adapter Placeholder",
        description="Placeholder for future third-party simulation adapters",
        status="unavailable",
        evidence_level=1,
        baseline_comparison="TBD",
        scope=["external_simulation"],
        maintainer="pipeline",
        notes="placeholder for future third-party adapters",
    ),
]


def get_module_entry(module_id: str) -> SimulationModuleEntry | None:
    for entry in SIMULATION_MODULE_REGISTRY:
        if entry.module_id == module_id:
            return entry
    return None


def list_module_entries(
    status: str | None = None,
    min_evidence_level: int | None = None,
) -> list[SimulationModuleEntry]:
    results = list(SIMULATION_MODULE_REGISTRY)
    if status is not None:
        results = [e for e in results if e.status == status]
    if min_evidence_level is not None:
        results = [e for e in results if e.evidence_level >= min_evidence_level]
    return results


def get_active_modules() -> list[SimulationModuleEntry]:
    return list_module_entries(status="active")


def registry_summary() -> dict:
    by_status: dict[str, int] = {}
    by_evidence_level: dict[str, int] = {}
    active_ids: list[str] = []

    for entry in SIMULATION_MODULE_REGISTRY:
        by_status[entry.status] = by_status.get(entry.status, 0) + 1
        key = str(entry.evidence_level)
        by_evidence_level[key] = by_evidence_level.get(key, 0) + 1
        if entry.status == "active":
            active_ids.append(entry.module_id)

    return {
        "total": len(SIMULATION_MODULE_REGISTRY),
        "by_status": dict(sorted(by_status.items())),
        "by_evidence_level": dict(sorted(by_evidence_level.items())),
        "active_module_ids": active_ids,
    }


def validate_registry() -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()

    for i, entry in enumerate(SIMULATION_MODULE_REGISTRY):
        if not entry.module_id:
            errors.append(f"Entry {i}: module_id is empty")
        if not entry.name:
            errors.append(f"Entry {i} ({entry.module_id}): name is empty")
        if not entry.baseline_comparison:
            errors.append(f"Entry {i} ({entry.module_id}): baseline_comparison is empty")
        if entry.evidence_level not in PROOF_LADDER_LEVELS:
            errors.append(
                f"Entry {i} ({entry.module_id}): evidence_level {entry.evidence_level} "
                f"must be 1..6"
            )
        if entry.status not in VALID_STATUSES:
            errors.append(
                f"Entry {i} ({entry.module_id}): unknown status '{entry.status}'"
            )
        if entry.module_id in seen_ids:
            errors.append(f"Duplicate module_id: '{entry.module_id}'")
        seen_ids.add(entry.module_id)

    return errors

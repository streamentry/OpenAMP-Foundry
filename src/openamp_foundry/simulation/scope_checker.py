"""Simulation-scope coverage checker — flags out-of-scope results as uncovered.

Dry-lab only. Scope checks are computational safeguards, not biological proof.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from openamp_foundry.simulation.interfaces import SimulationResult
from openamp_foundry.simulation.module_registry import get_module_entry


@dataclass
class ScopeCoverageResult:
    module_id: str
    requested_scopes: list[str]
    module_scopes: list[str]
    covered: list[str]
    uncovered: list[str]
    coverage_fraction: float
    is_fully_covered: bool
    dry_lab_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_scope_coverage(
    module_id: str,
    requested_scopes: list[str],
) -> ScopeCoverageResult:
    entry = get_module_entry(module_id)
    module_scopes = list(entry.scope) if entry is not None else []
    covered = [s for s in requested_scopes if s in module_scopes]
    uncovered = [s for s in requested_scopes if s not in module_scopes]
    coverage_fraction = len(covered) / len(requested_scopes) if requested_scopes else 1.0
    is_fully_covered = len(uncovered) == 0
    return ScopeCoverageResult(
        module_id=module_id,
        requested_scopes=list(requested_scopes),
        module_scopes=module_scopes,
        covered=covered,
        uncovered=uncovered,
        coverage_fraction=coverage_fraction,
        is_fully_covered=is_fully_covered,
    )


def check_result_scope(
    result: SimulationResult,
    requested_scopes: list[str],
) -> ScopeCoverageResult:
    entry = get_module_entry(result.module)
    registry_scopes = set(entry.scope) if entry is not None else set()
    result_scopes = set(result.scope)
    module_scopes = sorted(registry_scopes & result_scopes)
    covered = [s for s in requested_scopes if s in module_scopes]
    uncovered = [s for s in requested_scopes if s not in module_scopes]
    coverage_fraction = len(covered) / len(requested_scopes) if requested_scopes else 1.0
    is_fully_covered = len(uncovered) == 0
    return ScopeCoverageResult(
        module_id=result.module,
        requested_scopes=list(requested_scopes),
        module_scopes=module_scopes,
        covered=covered,
        uncovered=uncovered,
        coverage_fraction=coverage_fraction,
        is_fully_covered=is_fully_covered,
    )


def scope_coverage_report(
    module_id: str,
    requested_scopes: list[str],
) -> dict[str, Any]:
    result = check_scope_coverage(module_id, requested_scopes)
    return result.to_dict()

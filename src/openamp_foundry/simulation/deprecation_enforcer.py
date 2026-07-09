"""Deprecation enforcer for simulation modules — blocks deprecated or
unavailable modules from contributing to evidence packets.

Dry-lab only. Blocking decisions are based on registry status, not
biological validity.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from openamp_foundry.simulation.interfaces import SimulationResult
from openamp_foundry.simulation.module_registry import get_module_entry

BLOCKED_STATUSES: set[str] = {"deprecated", "unavailable"}


@dataclass
class DeprecationCheckResult:
    module_id: str
    status: str
    is_blocked: bool
    block_reason: str
    dry_lab_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_module_deprecation(module_id: str) -> DeprecationCheckResult:
    entry = get_module_entry(module_id)
    if entry is None:
        return DeprecationCheckResult(
            module_id=module_id,
            status="unknown",
            is_blocked=True,
            block_reason="Module not found in registry",
        )
    if entry.status in BLOCKED_STATUSES:
        return DeprecationCheckResult(
            module_id=module_id,
            status=entry.status,
            is_blocked=True,
            block_reason=f"Module status is '{entry.status}'",
        )
    return DeprecationCheckResult(
        module_id=module_id,
        status=entry.status,
        is_blocked=False,
        block_reason="",
    )


def enforce_deprecation(
    results: list[SimulationResult],
) -> dict[str, Any]:
    total_input = len(results)
    checks: list[DeprecationCheckResult] = []
    passed_results: list[SimulationResult] = []
    blocked_modules: set[str] = set()

    for result in results:
        check = check_module_deprecation(result.module)
        checks.append(check)
        if check.is_blocked:
            blocked_modules.add(result.module)
        else:
            passed_results.append(result)

    return {
        "total_input": total_input,
        "passed": len(passed_results),
        "blocked": total_input - len(passed_results),
        "blocked_modules": sorted(blocked_modules),
        "passed_results": passed_results,
        "checks": [c.to_dict() for c in checks],
        "dry_lab_only": True,
    }


def run_deprecation_check_batch(
    module_ids: list[str],
) -> dict[str, Any]:
    results = [check_module_deprecation(mid) for mid in module_ids]
    blocked = sum(1 for r in results if r.is_blocked)
    return {
        "total": len(results),
        "blocked": blocked,
        "allowed": len(results) - blocked,
        "any_blocked": blocked > 0,
        "results": [r.to_dict() for r in results],
        "dry_lab_only": True,
    }

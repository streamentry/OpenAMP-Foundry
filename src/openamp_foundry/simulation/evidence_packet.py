"""Simulation-evidence packet assembler — Phase H capstone.

Assembles all individual simulation discipline checks (baseline beaten,
adapter gate, scope coverage, deprecation, CI, ensemble agreement) into a
single auditable evidence packet showing exactly why a simulation result
is trustworthy (or not) enough to support a given evidence level claim.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from .interfaces import SimulationResult


@dataclass
class SimulationEvidencePacket:
    module_id: str
    result: SimulationResult
    requested_scopes: list[str]
    claimed_evidence_level: int
    baseline_beaten: bool
    deprecation_check: dict
    scope_check: dict
    baseline_check: dict
    adapter_gate: dict
    effective_evidence_level: int
    all_checks_passed: bool
    failure_reasons: list[str]
    dry_lab_only: bool = True


def assemble_evidence_packet(
    result: SimulationResult,
    requested_scopes: list[str],
    claimed_evidence_level: int,
    baseline_beaten: bool,
    *,
    adapter_timeout: bool = False,
    adapter_connection_refused: bool = False,
    adapter_schema_errors: list[str] | None = None,
) -> SimulationEvidencePacket:
    """Run all sub-checks and assemble into a single evidence packet.

    1. deprecation_check — check_module_deprecation(result.module)
    2. scope_check — check_scope_coverage(result.module, requested_scopes)
    3. baseline_check — check_baseline_requirement(result.module, claimed_evidence_level, baseline_beaten)
    4. adapter_gate — evaluate_adapter_gate(...)
    5. effective_evidence_level — from baseline_check
    6. failure_reasons and all_checks_passed — derived from all sub-checks
    """
    from dataclasses import asdict as _asdict

    from .adapter_gate import evaluate_adapter_gate
    from .baseline_registry import check_baseline_requirement
    from .deprecation_enforcer import check_module_deprecation
    from .scope_checker import check_scope_coverage

    deprecation_check = _asdict(check_module_deprecation(result.module))
    scope_check = _asdict(check_scope_coverage(result.module, requested_scopes))
    baseline_check = check_baseline_requirement(
        result.module, claimed_evidence_level, baseline_beaten,
    )

    adapter_gate = _asdict(evaluate_adapter_gate(
        module_id=result.module,
        result=result,
        timeout_occurred=adapter_timeout,
        connection_refused=adapter_connection_refused,
        schema_errors=adapter_schema_errors or [],
        module_unavailable=deprecation_check["is_blocked"],
        baseline_beaten=baseline_beaten,
    ))

    effective_evidence_level = baseline_check["effective_evidence_level"]

    failure_reasons: list[str] = []
    if deprecation_check["is_blocked"]:
        failure_reasons.append(
            f"Module '{result.module}' is deprecated or unavailable: "
            f"{deprecation_check['block_reason']}",
        )
    if not scope_check["is_fully_covered"]:
        uncovered = scope_check["uncovered"]
        failure_reasons.append(
            f"Scope(s) not covered: {', '.join(uncovered)}",
        )
    if baseline_check["capped"]:
        failure_reasons.append(
            f"Baseline not beaten — evidence level capped from "
            f"{claimed_evidence_level} to {effective_evidence_level}",
        )
    if not adapter_gate["passed"]:
        reason = adapter_gate["failure_reason"] or "unknown"
        detail = adapter_gate["failure_detail"]
        failure_reasons.append(
            f"Adapter gate failed: {reason} — {detail}",
        )

    all_checks_passed = len(failure_reasons) == 0

    return SimulationEvidencePacket(
        module_id=result.module,
        result=result,
        requested_scopes=list(requested_scopes),
        claimed_evidence_level=claimed_evidence_level,
        baseline_beaten=baseline_beaten,
        deprecation_check=deprecation_check,
        scope_check=scope_check,
        baseline_check=baseline_check,
        adapter_gate=adapter_gate,
        effective_evidence_level=effective_evidence_level,
        all_checks_passed=all_checks_passed,
        failure_reasons=failure_reasons,
    )


def evidence_packet_summary(packet: SimulationEvidencePacket) -> dict[str, Any]:
    """Return a compact summary dict."""
    return {
        "module_id": packet.module_id,
        "claimed_evidence_level": packet.claimed_evidence_level,
        "effective_evidence_level": packet.effective_evidence_level,
        "all_checks_passed": packet.all_checks_passed,
        "failure_reasons": packet.failure_reasons,
        "dry_lab_only": packet.dry_lab_only,
    }

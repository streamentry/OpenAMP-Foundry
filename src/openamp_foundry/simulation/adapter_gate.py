"""Fail-closed adapter gate for virtual assay simulation adapters.

When an adapter to an external simulation service is down or misbehaves,
the pipeline must fail loudly rather than silently passing garbage through.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from .interfaces import SimulationResult

FAIL_CLOSED_REASONS: dict[str, str] = {
    "timeout": "Adapter call timed out",
    "connection_refused": "Adapter endpoint refused connection",
    "invalid_response": "Adapter returned an unparseable response",
    "schema_violation": "Adapter response failed schema validation",
    "module_unavailable": "Simulation module is not available",
    "baseline_not_beaten": "Module did not beat its declared cheapest baseline",
}


@dataclass
class AdapterGateResult:
    module_id: str
    passed: bool
    failure_reason: str | None
    failure_detail: str
    dry_lab_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_adapter_gate(
    module_id: str,
    result: SimulationResult | None,
    *,
    timeout_occurred: bool = False,
    connection_refused: bool = False,
    schema_errors: list[str] | None = None,
    module_unavailable: bool = False,
    baseline_beaten: bool | None = None,
) -> AdapterGateResult:
    """Fail-closed: return passed=False on ANY failure signal.

    Priority order (first match wins):
    1. timeout_occurred → failure_reason="timeout"
    2. connection_refused → failure_reason="connection_refused"
    3. result is None → failure_reason="invalid_response"
    4. schema_errors (non-empty list) → failure_reason="schema_violation"
    5. module_unavailable → failure_reason="module_unavailable"
    6. baseline_beaten is False → failure_reason="baseline_not_beaten"
    7. Otherwise → passed=True
    """
    if timeout_occurred:
        return AdapterGateResult(
            module_id=module_id,
            passed=False,
            failure_reason="timeout",
            failure_detail=FAIL_CLOSED_REASONS["timeout"],
        )

    if connection_refused:
        return AdapterGateResult(
            module_id=module_id,
            passed=False,
            failure_reason="connection_refused",
            failure_detail=FAIL_CLOSED_REASONS["connection_refused"],
        )

    if result is None:
        return AdapterGateResult(
            module_id=module_id,
            passed=False,
            failure_reason="invalid_response",
            failure_detail=FAIL_CLOSED_REASONS["invalid_response"],
        )

    if schema_errors:
        detail = f"{FAIL_CLOSED_REASONS['schema_violation']}: {'; '.join(schema_errors)}"
        return AdapterGateResult(
            module_id=module_id,
            passed=False,
            failure_reason="schema_violation",
            failure_detail=detail,
        )

    if module_unavailable:
        return AdapterGateResult(
            module_id=module_id,
            passed=False,
            failure_reason="module_unavailable",
            failure_detail=FAIL_CLOSED_REASONS["module_unavailable"],
        )

    if baseline_beaten is False:
        return AdapterGateResult(
            module_id=module_id,
            passed=False,
            failure_reason="baseline_not_beaten",
            failure_detail=FAIL_CLOSED_REASONS["baseline_not_beaten"],
        )

    return AdapterGateResult(
        module_id=module_id,
        passed=True,
        failure_reason=None,
        failure_detail="All adapter gate checks passed.",
    )


def run_adapter_gate_batch(calls: list[dict]) -> dict:
    """Run evaluate_adapter_gate for multiple calls and aggregate results.

    Each dict in calls must have a "module_id" key plus any kwargs for
    evaluate_adapter_gate (result, timeout_occurred, connection_refused,
    schema_errors, module_unavailable, baseline_beaten).
    """
    results: list[dict] = []
    for call in calls:
        module_id = call.pop("module_id")
        result = call.pop("result", None)
        # Pop known kwargs; remaining are passed as-is
        gate_result = evaluate_adapter_gate(
            module_id=module_id,
            result=result,
            **call,
        )
        results.append(gate_result.to_dict())

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "any_failed": failed > 0,
        "results": results,
        "dry_lab_only": True,
    }

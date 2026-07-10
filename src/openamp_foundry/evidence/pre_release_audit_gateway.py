"""PRG- pre-release audit gateway schema.

Single-gate record asserting BRC (batch release checklist), PCC (pipeline
completeness), and ECI (evidence completeness index) all pass before external
sharing. Blocks release until all three gates are green.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_GATE_STATUSES: frozenset[str] = frozenset({"pass", "fail", "not_evaluated"})
VALID_RELEASE_VERDICTS: frozenset[str] = frozenset({"approved", "blocked"})

REQUIRED_GATES: tuple[str, ...] = ("BRC", "PCC", "ECI")


@dataclass
class GateResult:
    gate_type: str
    artifact_id: str
    status: str
    details: str


@dataclass
class PreReleaseAuditGateway:
    prg_id: str
    batch_id: str
    pipeline_version: str
    gate_results: list[GateResult]
    n_gates_total: int
    n_gates_passed: int
    n_gates_failed: int
    release_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_pre_release_audit_gateway(prg: PreReleaseAuditGateway) -> None:
    if not prg.prg_id.startswith("PRG-"):
        raise ValueError(f"prg_id must start with 'PRG-': {prg.prg_id!r}")
    if not prg.batch_id:
        raise ValueError("batch_id must be non-empty")
    if not prg.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    for gr in prg.gate_results:
        if gr.gate_type not in REQUIRED_GATES:
            raise ValueError(
                f"gate_type {gr.gate_type!r} must be one of {REQUIRED_GATES}"
            )
        if gr.status not in VALID_GATE_STATUSES:
            raise ValueError(
                f"gate status {gr.status!r} not in VALID_GATE_STATUSES"
            )
    gate_types = [gr.gate_type for gr in prg.gate_results]
    for req in REQUIRED_GATES:
        if gate_types.count(req) != 1:
            raise ValueError(f"Exactly one gate result required for {req!r}")
    if prg.release_verdict not in VALID_RELEASE_VERDICTS:
        raise ValueError(
            f"release_verdict {prg.release_verdict!r} not in VALID_RELEASE_VERDICTS"
        )
    if not prg.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not prg.limitations:
        raise ValueError("limitations must be non-empty")
    if not prg.created_at:
        raise ValueError("created_at must be non-empty")
    if prg.n_gates_total != len(prg.gate_results):
        raise ValueError("n_gates_total must equal len(gate_results)")
    n_passed = sum(1 for gr in prg.gate_results if gr.status == "pass")
    if prg.n_gates_passed != n_passed:
        raise ValueError("n_gates_passed mismatch")
    if prg.n_gates_failed != sum(
        1 for gr in prg.gate_results if gr.status == "fail"
    ):
        raise ValueError("n_gates_failed mismatch")


def build_pre_release_audit_gateway(
    *,
    prg_id: str,
    batch_id: str,
    pipeline_version: str,
    brc_artifact_id: str,
    brc_verdict: str,
    pcc_artifact_id: str,
    pcc_grade: str,
    eci_artifact_id: str,
    eci_grade: str,
    limitations: list[str],
    created_at: str,
) -> PreReleaseAuditGateway:
    """Build a pre-release audit gateway.

    brc_verdict: e.g. "approved", "blocked", "conditional"
    pcc_grade: "A"/"B"/"C"/"D" — pass if A or B
    eci_grade: "A"/"B"/"C"/"D" — pass if A or B
    """
    brc_pass = brc_verdict == "approved"
    pcc_pass = pcc_grade in ("A", "B")
    eci_pass = eci_grade in ("A", "B")

    gate_results = [
        GateResult(
            gate_type="BRC",
            artifact_id=brc_artifact_id,
            status="pass" if brc_pass else "fail",
            details=f"BRC verdict={brc_verdict!r} — {'pass' if brc_pass else 'fail'}",
        ),
        GateResult(
            gate_type="PCC",
            artifact_id=pcc_artifact_id,
            status="pass" if pcc_pass else "fail",
            details=f"PCC grade={pcc_grade!r} — {'pass' if pcc_pass else 'fail (need A or B)'}",
        ),
        GateResult(
            gate_type="ECI",
            artifact_id=eci_artifact_id,
            status="pass" if eci_pass else "fail",
            details=f"ECI grade={eci_grade!r} — {'pass' if eci_pass else 'fail (need A or B)'}",
        ),
    ]
    n_total = len(gate_results)
    n_passed = sum(1 for gr in gate_results if gr.status == "pass")
    n_failed = sum(1 for gr in gate_results if gr.status == "fail")
    verdict = "approved" if n_failed == 0 else "blocked"

    prg = PreReleaseAuditGateway(
        prg_id=prg_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        gate_results=gate_results,
        n_gates_total=n_total,
        n_gates_passed=n_passed,
        n_gates_failed=n_failed,
        release_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_pre_release_audit_gateway(prg)
    return prg


def format_pre_release_audit_gateway(prg: PreReleaseAuditGateway) -> str:
    lines = [
        f"Pre-Release Audit Gateway — {prg.prg_id}",
        f"Batch: {prg.batch_id}  |  Pipeline: {prg.pipeline_version}",
        f"Verdict: {prg.release_verdict}  |  Gates: {prg.n_gates_total}",
        f"Passed: {prg.n_gates_passed}  |  Failed: {prg.n_gates_failed}",
        "Gate results:",
    ]
    for gr in prg.gate_results:
        status_label = "PASS" if gr.status == "pass" else "FAIL"
        lines.append(f"  [{status_label}] {gr.gate_type} ({gr.artifact_id}): {gr.details}")
    lines.append(f"Created: {prg.created_at}")
    lines.append(f"Limitations: {'; '.join(prg.limitations)}")
    lines.append(f"dry_lab_only: {prg.dry_lab_only}")
    return "\n".join(lines)

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


REQUIRED_RECORD_TYPES = frozenset({
    "BSP",   # batch selection proposal — dry-lab nomination
    "WHR",   # wet-lab hit record — actual experimental result
    "PCU",   # post-experiment calibration update — model feedback
    "HCR",   # hit confirmation report — prediction vs actual bundle
})

VALID_LOOP_VERDICTS = frozenset({
    "loop_complete",       # all four record types present and cross-linked
    "loop_partial",        # some but not all record types present
    "loop_not_started",    # no wet-lab records (WHR/PCU/HCR) present
    "loop_broken",         # records present but cross-links fail
})


@dataclass
class PhaseQCompletenessGate:
    gate_id: str
    candidate_family_id: str
    bsp_ids: List[str]
    whr_ids: List[str]
    pcu_ids: List[str]
    hcr_ids: List[str]
    loop_verdict: str
    missing_record_types: List[str]
    cross_link_failures: List[str]
    n_candidates_with_whr: int
    n_candidates_with_hcr: int
    dry_lab_only: bool
    notes: str = ""


@dataclass
class PhaseQGateResult:
    passed: bool
    violations: List[str] = field(default_factory=list)


def validate_phase_q_completeness_gate(gate: PhaseQCompletenessGate) -> PhaseQGateResult:
    violations = []

    if not gate.gate_id.startswith("PQG-"):
        violations.append("gate_id must start with 'PQG-'")

    if not gate.candidate_family_id:
        violations.append("candidate_family_id is required")

    if gate.candidate_family_id.startswith("TOY-"):
        violations.append("TOY- candidate_family_id is not allowed in real PQG- records")

    if not gate.bsp_ids:
        violations.append("at least one bsp_id (BSP-) is required")

    for bid in gate.bsp_ids:
        if not bid.startswith("BSP-"):
            violations.append(f"bsp_id '{bid}' must start with 'BSP-'")

    if gate.loop_verdict not in VALID_LOOP_VERDICTS:
        violations.append(
            f"loop_verdict '{gate.loop_verdict}' must be one of {sorted(VALID_LOOP_VERDICTS)}"
        )

    # loop_complete requires all four record types to have at least one entry
    if gate.loop_verdict == "loop_complete":
        if not gate.bsp_ids:
            violations.append("loop_verdict='loop_complete' requires at least one bsp_id")
        if not gate.whr_ids:
            violations.append("loop_verdict='loop_complete' requires at least one whr_id")
        if not gate.pcu_ids:
            violations.append("loop_verdict='loop_complete' requires at least one pcu_id")
        if not gate.hcr_ids:
            violations.append("loop_verdict='loop_complete' requires at least one hcr_id")
        if gate.cross_link_failures:
            violations.append(
                "loop_verdict='loop_complete' requires no cross_link_failures"
            )
        if gate.missing_record_types:
            violations.append(
                "loop_verdict='loop_complete' requires no missing_record_types"
            )

    # loop_not_started must have no WHR/PCU/HCR
    if gate.loop_verdict == "loop_not_started":
        if gate.whr_ids or gate.pcu_ids or gate.hcr_ids:
            violations.append(
                "loop_verdict='loop_not_started' must have empty whr_ids, pcu_ids, and hcr_ids"
            )

    # WHR IDs must have correct prefix
    for wid in gate.whr_ids:
        if not wid.startswith("WHR-"):
            violations.append(f"whr_id '{wid}' must start with 'WHR-'")

    # PCU IDs must have correct prefix
    for pid in gate.pcu_ids:
        if not pid.startswith("PCU-"):
            violations.append(f"pcu_id '{pid}' must start with 'PCU-'")

    # HCR IDs must have correct prefix
    for hid in gate.hcr_ids:
        if not hid.startswith("HCR-"):
            violations.append(f"hcr_id '{hid}' must start with 'HCR-'")

    if gate.n_candidates_with_whr < 0:
        violations.append("n_candidates_with_whr must be >= 0")

    if gate.n_candidates_with_hcr < 0:
        violations.append("n_candidates_with_hcr must be >= 0")

    if gate.n_candidates_with_hcr > gate.n_candidates_with_whr:
        violations.append(
            f"n_candidates_with_hcr ({gate.n_candidates_with_hcr}) cannot exceed n_candidates_with_whr ({gate.n_candidates_with_whr})"
        )

    if gate.dry_lab_only:
        violations.append(
            "dry_lab_only must be False for PQG- records (real wet-lab loop required)"
        )

    return PhaseQGateResult(passed=len(violations) == 0, violations=violations)


def build_phase_q_completeness_gate(
    gate_id: str,
    candidate_family_id: str,
    bsp_ids: List[str],
    whr_ids: List[str],
    pcu_ids: List[str],
    hcr_ids: List[str],
    loop_verdict: str,
    missing_record_types: List[str],
    cross_link_failures: List[str],
    n_candidates_with_whr: int,
    n_candidates_with_hcr: int,
    notes: str = "",
) -> PhaseQCompletenessGate:
    gate = PhaseQCompletenessGate(
        gate_id=gate_id,
        candidate_family_id=candidate_family_id,
        bsp_ids=bsp_ids,
        whr_ids=whr_ids,
        pcu_ids=pcu_ids,
        hcr_ids=hcr_ids,
        loop_verdict=loop_verdict,
        missing_record_types=missing_record_types,
        cross_link_failures=cross_link_failures,
        n_candidates_with_whr=n_candidates_with_whr,
        n_candidates_with_hcr=n_candidates_with_hcr,
        dry_lab_only=False,
        notes=notes,
    )
    result = validate_phase_q_completeness_gate(gate)
    if not result.passed:
        raise ValueError(f"Invalid PQG: {result.violations}")
    return gate


def format_phase_q_completeness_gate(gate: PhaseQCompletenessGate) -> str:
    lines = [
        f"Phase Q Completeness Gate — {gate.gate_id}",
        f"Candidate Family: {gate.candidate_family_id}",
        f"Loop Verdict: {gate.loop_verdict}",
        f"BSP Records: {len(gate.bsp_ids)} ({', '.join(gate.bsp_ids) if gate.bsp_ids else 'none'})",
        f"WHR Records: {len(gate.whr_ids)} ({', '.join(gate.whr_ids) if gate.whr_ids else 'none'})",
        f"PCU Records: {len(gate.pcu_ids)} ({', '.join(gate.pcu_ids) if gate.pcu_ids else 'none'})",
        f"HCR Records: {len(gate.hcr_ids)} ({', '.join(gate.hcr_ids) if gate.hcr_ids else 'none'})",
        f"Candidates with WHR: {gate.n_candidates_with_whr}",
        f"Candidates with HCR: {gate.n_candidates_with_hcr}",
    ]
    if gate.missing_record_types:
        lines.append(f"Missing Record Types: {', '.join(gate.missing_record_types)}")
    if gate.cross_link_failures:
        lines.append(f"Cross-Link Failures: {'; '.join(gate.cross_link_failures)}")
    if gate.notes:
        lines.append(f"Notes: {gate.notes}")
    lines.append("dry_lab_only: False (real wet-lab loop required)")
    return "\n".join(lines)

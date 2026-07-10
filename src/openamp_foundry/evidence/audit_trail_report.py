from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


VALID_TRAIL_COMPLETENESS_STATUSES = frozenset({
    "complete",           # all required stages present and linked
    "partial",            # some stages missing — details in missing_stages
    "broken_chain",       # stages present but linkage fails
    "dry_lab_only",       # only pre-experiment stages present (BSP; no WHR/PCU/HCR)
})

REQUIRED_ATR_STAGES = frozenset({
    "BSP",   # batch selection proposal
    "WHR",   # wet-lab hit record
    "PCU",   # post-experiment calibration update
    "HCR",   # hit confirmation report
    "PQG",   # Phase Q completeness gate
})

VALID_CHAIN_INTEGRITY_GRADES = frozenset({
    "A",   # all cross-links verified; no gaps
    "B",   # minor gaps (e.g. PCU optional field absent); functionally complete
    "C",   # significant gaps; trail is partially traceable
    "D",   # major failures; trail cannot be used for reproducibility claims
    "N/A", # trail not yet complete; grading deferred
})


@dataclass
class AuditTrailReport:
    atr_id: str
    candidate_family_id: str
    bsp_ids: List[str]
    whr_ids: List[str]
    pcu_ids: List[str]
    hcr_ids: List[str]
    pqg_id: Optional[str]
    trail_completeness_status: str
    missing_stages: List[str]
    chain_integrity_grade: str
    n_stages_complete: int
    chain_link_failures: List[str]
    dry_lab_only: bool
    limitations: str
    notes: str = ""


@dataclass
class ATRValidationResult:
    valid: bool
    violations: List[str] = field(default_factory=list)


def validate_audit_trail_report(report: AuditTrailReport) -> ATRValidationResult:
    violations = []

    if not report.atr_id.startswith("ATR-"):
        violations.append("atr_id must start with 'ATR-'")

    if not report.candidate_family_id:
        violations.append("candidate_family_id is required")

    if report.candidate_family_id.startswith("TOY-"):
        violations.append("TOY- candidate_family_id is not allowed in real ATR- records")

    if not report.bsp_ids:
        violations.append("at least one bsp_id (BSP-) is required")

    for bid in report.bsp_ids:
        if not bid.startswith("BSP-"):
            violations.append(f"bsp_id '{bid}' must start with 'BSP-'")

    for wid in report.whr_ids:
        if not wid.startswith("WHR-"):
            violations.append(f"whr_id '{wid}' must start with 'WHR-'")

    for pid in report.pcu_ids:
        if not pid.startswith("PCU-"):
            violations.append(f"pcu_id '{pid}' must start with 'PCU-'")

    for hid in report.hcr_ids:
        if not hid.startswith("HCR-"):
            violations.append(f"hcr_id '{hid}' must start with 'HCR-'")

    if report.pqg_id is not None and not report.pqg_id.startswith("PQG-"):
        violations.append(f"pqg_id '{report.pqg_id}' must start with 'PQG-'")

    if report.trail_completeness_status not in VALID_TRAIL_COMPLETENESS_STATUSES:
        violations.append(
            f"trail_completeness_status '{report.trail_completeness_status}' must be one of "
            f"{sorted(VALID_TRAIL_COMPLETENESS_STATUSES)}"
        )

    if report.chain_integrity_grade not in VALID_CHAIN_INTEGRITY_GRADES:
        violations.append(
            f"chain_integrity_grade '{report.chain_integrity_grade}' must be one of "
            f"{sorted(VALID_CHAIN_INTEGRITY_GRADES)}"
        )

    if report.n_stages_complete < 0 or report.n_stages_complete > len(REQUIRED_ATR_STAGES):
        violations.append(
            f"n_stages_complete must be in [0, {len(REQUIRED_ATR_STAGES)}]"
        )

    # complete status requires all five stages
    if report.trail_completeness_status == "complete":
        if not report.whr_ids:
            violations.append("trail_completeness_status='complete' requires at least one whr_id")
        if not report.pcu_ids:
            violations.append("trail_completeness_status='complete' requires at least one pcu_id")
        if not report.hcr_ids:
            violations.append("trail_completeness_status='complete' requires at least one hcr_id")
        if report.pqg_id is None:
            violations.append("trail_completeness_status='complete' requires a pqg_id")
        if report.missing_stages:
            violations.append("trail_completeness_status='complete' requires empty missing_stages")
        if report.chain_link_failures:
            violations.append("trail_completeness_status='complete' requires empty chain_link_failures")

    # dry_lab_only status must have no WHR/PCU/HCR/PQG
    if report.trail_completeness_status == "dry_lab_only":
        if report.whr_ids or report.pcu_ids or report.hcr_ids or report.pqg_id:
            violations.append(
                "trail_completeness_status='dry_lab_only' must have empty whr_ids, pcu_ids, hcr_ids, and no pqg_id"
            )

    # grade D should not be on a complete trail
    if report.chain_integrity_grade == "D" and report.trail_completeness_status == "complete":
        violations.append(
            "chain_integrity_grade='D' is inconsistent with trail_completeness_status='complete'"
        )

    # grade A requires complete status
    if report.chain_integrity_grade == "A" and report.trail_completeness_status not in ("complete", "partial"):
        violations.append(
            "chain_integrity_grade='A' requires trail_completeness_status in ('complete', 'partial')"
        )

    if not report.dry_lab_only:
        violations.append(
            "dry_lab_only must be True for ATR- records (audit trail is a computational/documentation artifact)"
        )

    if not report.limitations or len(report.limitations.strip()) < 10:
        violations.append("limitations must be a non-empty string (at least 10 characters)")

    return ATRValidationResult(valid=len(violations) == 0, violations=violations)


def build_audit_trail_report(
    atr_id: str,
    candidate_family_id: str,
    bsp_ids: List[str],
    whr_ids: List[str],
    pcu_ids: List[str],
    hcr_ids: List[str],
    trail_completeness_status: str,
    missing_stages: List[str],
    chain_integrity_grade: str,
    chain_link_failures: List[str],
    limitations: str,
    pqg_id: Optional[str] = None,
    notes: str = "",
) -> AuditTrailReport:
    n_stages_complete = sum([
        bool(bsp_ids),
        bool(whr_ids),
        bool(pcu_ids),
        bool(hcr_ids),
        pqg_id is not None,
    ])
    report = AuditTrailReport(
        atr_id=atr_id,
        candidate_family_id=candidate_family_id,
        bsp_ids=bsp_ids,
        whr_ids=whr_ids,
        pcu_ids=pcu_ids,
        hcr_ids=hcr_ids,
        pqg_id=pqg_id,
        trail_completeness_status=trail_completeness_status,
        missing_stages=missing_stages,
        chain_integrity_grade=chain_integrity_grade,
        n_stages_complete=n_stages_complete,
        chain_link_failures=chain_link_failures,
        dry_lab_only=True,
        limitations=limitations,
        notes=notes,
    )
    result = validate_audit_trail_report(report)
    if not result.valid:
        raise ValueError(f"Invalid ATR: {result.violations}")
    return report


def format_audit_trail_report(report: AuditTrailReport) -> str:
    lines = [
        f"Audit Trail Report — {report.atr_id}",
        f"Candidate Family: {report.candidate_family_id}",
        f"Trail Status: {report.trail_completeness_status}",
        f"Chain Integrity: {report.chain_integrity_grade}",
        f"Stages Complete: {report.n_stages_complete}/{len(REQUIRED_ATR_STAGES)}",
        f"BSP: {', '.join(report.bsp_ids) if report.bsp_ids else 'none'}",
        f"WHR: {', '.join(report.whr_ids) if report.whr_ids else 'none'}",
        f"PCU: {', '.join(report.pcu_ids) if report.pcu_ids else 'none'}",
        f"HCR: {', '.join(report.hcr_ids) if report.hcr_ids else 'none'}",
        f"PQG: {report.pqg_id if report.pqg_id else 'none'}",
    ]
    if report.missing_stages:
        lines.append(f"Missing Stages: {', '.join(report.missing_stages)}")
    if report.chain_link_failures:
        lines.append(f"Chain Link Failures: {'; '.join(report.chain_link_failures)}")
    lines.append(f"Limitations: {report.limitations}")
    if report.notes:
        lines.append(f"Notes: {report.notes}")
    lines.append("dry_lab_only: True (audit trail is a documentation artifact)")
    return "\n".join(lines)

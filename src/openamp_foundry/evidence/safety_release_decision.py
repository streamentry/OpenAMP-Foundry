"""SRD- safety-release decision schema.

Machine-checkable record of whether a candidate package was authorized for
external release, which safety checks were passed, what restrictions apply,
and why it was rejected if not authorized.

Makes release review auditable: every external release of pipeline outputs
must reference an SRD- record. No release is implicit or unrecorded.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_SRD_DECISIONS: frozenset[str] = frozenset({
    "authorized",
    "rejected",
    "pending_review",
})

VALID_RELEASE_SCOPES: frozenset[str] = frozenset({
    "academic_collaboration",
    "public_preprint",
    "internal_only",
    "restricted_partner",
})

VALID_SAFETY_CHECK_IDS: frozenset[str] = frozenset({
    "dual_use_screened",
    "toxicity_flags_reviewed",
    "hemolysis_flags_reviewed",
    "novelty_claims_bounded",
    "dry_lab_only_label_present",
    "no_sequence_privacy_violation",
    "candidate_count_within_limit",
})

REQUIRED_SAFETY_CHECKS: tuple[str, ...] = (
    "dual_use_screened",
    "dry_lab_only_label_present",
    "novelty_claims_bounded",
)


@dataclass
class SafetyReleaseDecision:
    srd_id: str
    pipeline_version: str
    erp_id: str
    release_decision: str
    release_scope: str
    safety_checks_passed: list[str]
    restrictions: list[str]
    rejection_reason: str
    all_required_checks_passed: bool
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_safety_release_decision(srd: SafetyReleaseDecision) -> None:
    if not srd.srd_id.startswith("SRD-"):
        raise ValueError(f"srd_id must start with 'SRD-': {srd.srd_id!r}")
    if not srd.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if not srd.erp_id.startswith("ERP-"):
        raise ValueError(f"erp_id must start with 'ERP-': {srd.erp_id!r}")
    if srd.release_decision not in VALID_SRD_DECISIONS:
        raise ValueError(
            f"release_decision {srd.release_decision!r} not in VALID_SRD_DECISIONS"
        )
    if srd.release_scope not in VALID_RELEASE_SCOPES:
        raise ValueError(
            f"release_scope {srd.release_scope!r} not in VALID_RELEASE_SCOPES"
        )
    for check_id in srd.safety_checks_passed:
        if check_id not in VALID_SAFETY_CHECK_IDS:
            raise ValueError(
                f"safety check {check_id!r} not in VALID_SAFETY_CHECK_IDS"
            )
    required_passed = all(
        req in srd.safety_checks_passed for req in REQUIRED_SAFETY_CHECKS
    )
    if srd.all_required_checks_passed != required_passed:
        raise ValueError(
            "all_required_checks_passed mismatch with safety_checks_passed"
        )
    if srd.release_decision == "authorized" and not srd.all_required_checks_passed:
        raise ValueError(
            "release_decision='authorized' requires all_required_checks_passed=True"
        )
    if srd.release_decision == "rejected" and not srd.rejection_reason:
        raise ValueError(
            "rejection_reason must be non-empty when release_decision='rejected'"
        )
    if not srd.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not srd.limitations:
        raise ValueError("limitations must be non-empty")
    if not srd.created_at:
        raise ValueError("created_at must be non-empty")


def build_safety_release_decision(
    *,
    srd_id: str,
    pipeline_version: str,
    erp_id: str,
    release_decision: str,
    release_scope: str,
    safety_checks_passed: list[str],
    restrictions: list[str],
    rejection_reason: str = "",
    limitations: list[str],
    created_at: str,
) -> SafetyReleaseDecision:
    """Build a SafetyReleaseDecision.

    safety_checks_passed: list of VALID_SAFETY_CHECK_IDS that were verified.
    all_required_checks_passed is auto-computed from REQUIRED_SAFETY_CHECKS.
    """
    required_passed = all(
        req in safety_checks_passed for req in REQUIRED_SAFETY_CHECKS
    )
    srd = SafetyReleaseDecision(
        srd_id=srd_id,
        pipeline_version=pipeline_version,
        erp_id=erp_id,
        release_decision=release_decision,
        release_scope=release_scope,
        safety_checks_passed=list(safety_checks_passed),
        restrictions=list(restrictions),
        rejection_reason=rejection_reason,
        all_required_checks_passed=required_passed,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_safety_release_decision(srd)
    return srd


def format_safety_release_decision(srd: SafetyReleaseDecision) -> str:
    lines = [
        f"Safety-Release Decision — {srd.srd_id}",
        f"Pipeline: {srd.pipeline_version}  |  ERP: {srd.erp_id}",
        f"Decision: {srd.release_decision}  |  Scope: {srd.release_scope}",
        f"All required checks passed: {srd.all_required_checks_passed}",
    ]
    lines.append(f"Safety checks passed ({len(srd.safety_checks_passed)}):")
    for check in srd.safety_checks_passed:
        lines.append(f"  + {check}")
    missing = [r for r in REQUIRED_SAFETY_CHECKS if r not in srd.safety_checks_passed]
    if missing:
        lines.append("Required checks NOT passed:")
        for m in missing:
            lines.append(f"  ! {m}")
    if srd.restrictions:
        lines.append(f"Restrictions: {'; '.join(srd.restrictions)}")
    if srd.rejection_reason:
        lines.append(f"Rejection reason: {srd.rejection_reason}")
    lines.append(f"Created: {srd.created_at}")
    lines.append(f"Limitations: {'; '.join(srd.limitations)}")
    lines.append(f"dry_lab_only: {srd.dry_lab_only}")
    return "\n".join(lines)

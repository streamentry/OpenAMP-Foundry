"""CRS- certificate release-status schema.

Tracks which stage of the release lifecycle a certificate has reached:
draft → internal_review → external_review_ready → released → archived.

Staged release means a certificate cannot jump straight to "released" without
passing through review gates.  This makes the review chain machine-auditable
rather than implicit.

Every certificate that will be shared externally (academic, public, partner)
must have a corresponding CRS- record that documents its current stage and
any gate conditions that were satisfied.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_RELEASE_STATUSES: frozenset[str] = frozenset({
    "draft",
    "internal_review",
    "external_review_ready",
    "released",
    "archived",
})

STAGED_RELEASE_ORDER: tuple[str, ...] = (
    "draft",
    "internal_review",
    "external_review_ready",
    "released",
    "archived",
)

VALID_GATE_CONDITIONS: frozenset[str] = frozenset({
    "safety_checks_passed",
    "dual_use_screened",
    "dry_lab_label_confirmed",
    "internal_review_signed",
    "external_reviewer_assigned",
    "novelty_claims_bounded",
    "quality_tier_external_review_ready",
    "srd_authorized",
})

DRAFT_ALLOWED_NEXT: frozenset[str] = frozenset({"internal_review", "archived"})
INTERNAL_REVIEW_ALLOWED_NEXT: frozenset[str] = frozenset({
    "external_review_ready", "draft", "archived"
})
EXTERNAL_REVIEW_READY_ALLOWED_NEXT: frozenset[str] = frozenset({
    "released", "internal_review", "archived"
})
RELEASED_ALLOWED_NEXT: frozenset[str] = frozenset({"archived"})


@dataclass
class CertificateReleaseStatus:
    crs_id: str
    cert_id: str
    pipeline_version: str
    release_status: str
    gate_conditions_met: list[str]
    release_stage_index: int
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_certificate_release_status(crs: CertificateReleaseStatus) -> None:
    if not crs.crs_id.startswith("CRS-"):
        raise ValueError(f"crs_id must start with 'CRS-': {crs.crs_id!r}")
    if not crs.cert_id:
        raise ValueError("cert_id must be non-empty")
    if not crs.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if crs.release_status not in VALID_RELEASE_STATUSES:
        raise ValueError(
            f"release_status {crs.release_status!r} not in VALID_RELEASE_STATUSES"
        )
    expected_index = STAGED_RELEASE_ORDER.index(crs.release_status)
    if crs.release_stage_index != expected_index:
        raise ValueError(
            f"release_stage_index {crs.release_stage_index} inconsistent "
            f"with release_status {crs.release_status!r} (expected {expected_index})"
        )
    for condition in crs.gate_conditions_met:
        if condition not in VALID_GATE_CONDITIONS:
            raise ValueError(
                f"gate condition {condition!r} not in VALID_GATE_CONDITIONS"
            )
    if crs.release_status == "released" and "srd_authorized" not in crs.gate_conditions_met:
        raise ValueError(
            "release_status='released' requires 'srd_authorized' in gate_conditions_met"
        )
    if not crs.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not crs.limitations:
        raise ValueError("limitations must be non-empty")
    if not crs.created_at:
        raise ValueError("created_at must be non-empty")


def build_certificate_release_status(
    *,
    crs_id: str,
    cert_id: str,
    pipeline_version: str,
    release_status: str,
    gate_conditions_met: list[str] | None = None,
    limitations: list[str],
    created_at: str,
) -> CertificateReleaseStatus:
    """Build a CertificateReleaseStatus.

    release_stage_index is auto-computed from STAGED_RELEASE_ORDER.
    dry_lab_only is always True.
    """
    gate_conditions_met = list(gate_conditions_met) if gate_conditions_met else []
    if release_status not in VALID_RELEASE_STATUSES:
        raise ValueError(
            f"release_status {release_status!r} not in VALID_RELEASE_STATUSES"
        )
    stage_index = STAGED_RELEASE_ORDER.index(release_status)
    crs = CertificateReleaseStatus(
        crs_id=crs_id,
        cert_id=cert_id,
        pipeline_version=pipeline_version,
        release_status=release_status,
        gate_conditions_met=gate_conditions_met,
        release_stage_index=stage_index,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_certificate_release_status(crs)
    return crs


def can_advance_to(current_status: str, target_status: str) -> bool:
    """Return True if a certificate can advance from current_status to target_status."""
    _allowed: dict[str, frozenset[str]] = {
        "draft": DRAFT_ALLOWED_NEXT,
        "internal_review": INTERNAL_REVIEW_ALLOWED_NEXT,
        "external_review_ready": EXTERNAL_REVIEW_READY_ALLOWED_NEXT,
        "released": RELEASED_ALLOWED_NEXT,
        "archived": frozenset(),
    }
    return target_status in _allowed.get(current_status, frozenset())


def format_certificate_release_status(crs: CertificateReleaseStatus) -> str:
    lines = [
        f"Certificate Release Status — {crs.crs_id}",
        f"Certificate: {crs.cert_id}  |  Pipeline: {crs.pipeline_version}",
        f"Status: {crs.release_status} (stage {crs.release_stage_index})",
    ]
    if crs.gate_conditions_met:
        lines.append(f"Gate conditions met: {', '.join(crs.gate_conditions_met)}")
    else:
        lines.append("Gate conditions met: none")
    lines.append(f"Limitations: {'; '.join(crs.limitations)}")
    lines.append(f"Created: {crs.created_at}")
    lines.append(f"dry_lab_only: {crs.dry_lab_only}")
    return "\n".join(lines)

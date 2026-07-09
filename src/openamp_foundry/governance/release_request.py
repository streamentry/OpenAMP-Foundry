"""Release request validator — validates release requests before human review.

Ensures all required fields are present before a release request enters
the formal review queue.
Dry-lab only.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

VALID_RELEASE_TYPES: set[str] = {
    "candidate", "model", "dataset", "evidence_packet", "schema"
}

VALID_SAFETY_STATUSES: set[str] = {
    "pending", "approved", "not_required"
}

VALID_INTENDED_USES: set[str] = {
    "research", "internal", "external_partner", "public"
}

VALID_APPROVAL_STATUSES: set[str] = {
    "pending", "approved", "rejected", "deferred"
}

VALID_REVIEW_CLASSES: set[str] = {"A", "B", "C", "D"}


@dataclass
class ReleaseRequest:
    release_id: str           # e.g. "REL-2026-001"
    release_type: str         # from VALID_RELEASE_TYPES
    artifact_id: str
    artifact_version: str
    requestor_name: str
    requestor_institution: str
    request_date: str         # YYYY-MM-DD
    evidence_level: int       # 1-6
    dry_lab_only: bool        # must be True
    safety_review_status: str # from VALID_SAFETY_STATUSES
    benchmark_summary: str    # must not be empty
    known_limitations: str    # must not be empty
    intended_use: str         # from VALID_INTENDED_USES
    data_license: str         # must not be empty
    human_reviewer: str       # must not be empty
    review_class: str         # from VALID_REVIEW_CLASSES
    approval_status: str      # from VALID_APPROVAL_STATUSES


@dataclass
class ReleaseRequestValidationResult:
    release_id: str
    release_type: str
    passed: bool
    errors: list[str]
    warnings: list[str]
    dry_lab_only: bool = True


def validate_release_request(req: ReleaseRequest) -> ReleaseRequestValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not req.release_id or not req.release_id.startswith("REL-"):
        errors.append("release_id must not be empty and must start with 'REL-'")
    if req.release_type not in VALID_RELEASE_TYPES:
        errors.append(f"release_type={req.release_type!r} not in {sorted(VALID_RELEASE_TYPES)}")
    if not req.artifact_id:
        errors.append("artifact_id must not be empty")
    if not req.artifact_version:
        errors.append("artifact_version must not be empty")
    if not req.requestor_name:
        errors.append("requestor_name must not be empty")
    if not req.requestor_institution:
        errors.append("requestor_institution must not be empty")
    if not req.request_date or len(req.request_date) != 10 or req.request_date[4] != "-":
        errors.append("request_date must be in YYYY-MM-DD format")
    if not isinstance(req.evidence_level, int) or not (1 <= req.evidence_level <= 6):
        errors.append(f"evidence_level={req.evidence_level} must be int in 1-6")
    if not req.dry_lab_only:
        errors.append("dry_lab_only must be True")
    if req.safety_review_status not in VALID_SAFETY_STATUSES:
        errors.append(f"safety_review_status={req.safety_review_status!r} not in {sorted(VALID_SAFETY_STATUSES)}")
    if not req.benchmark_summary:
        errors.append("benchmark_summary must not be empty")
    if not req.known_limitations:
        errors.append("known_limitations must not be empty")
    if req.intended_use not in VALID_INTENDED_USES:
        errors.append(f"intended_use={req.intended_use!r} not in {sorted(VALID_INTENDED_USES)}")
    if not req.data_license:
        errors.append("data_license must not be empty")
    if not req.human_reviewer:
        errors.append("human_reviewer must not be empty")
    if req.review_class not in VALID_REVIEW_CLASSES:
        errors.append(f"review_class={req.review_class!r} not in {sorted(VALID_REVIEW_CLASSES)}")
    if req.approval_status not in VALID_APPROVAL_STATUSES:
        errors.append(f"approval_status={req.approval_status!r} not in {sorted(VALID_APPROVAL_STATUSES)}")

    # Evidence level check for dry-lab-only
    if req.dry_lab_only and req.evidence_level > 4:
        errors.append("dry_lab_only artifacts cannot have evidence_level > 4")

    # Safety check for public release
    if req.intended_use == "public" and req.safety_review_status == "pending":
        errors.append("public releases require safety_review_status != 'pending'")

    # Model releases require review_class D
    if req.release_type == "model" and req.review_class not in {"C", "D"}:
        warnings.append("model releases typically require review_class C or D")

    return ReleaseRequestValidationResult(
        release_id=req.release_id or "<unknown>",
        release_type=req.release_type,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_request_dict(d: dict[str, Any]) -> ReleaseRequestValidationResult:
    required = [
        "release_id", "release_type", "artifact_id", "artifact_version",
        "requestor_name", "requestor_institution", "request_date",
        "evidence_level", "dry_lab_only", "safety_review_status",
        "benchmark_summary", "known_limitations", "intended_use",
        "data_license", "human_reviewer", "review_class", "approval_status",
    ]
    missing = [f for f in required if f not in d]
    if missing:
        return ReleaseRequestValidationResult(
            release_id=d.get("release_id", "<unknown>"),
            release_type=d.get("release_type", "<unknown>"),
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            warnings=[],
            dry_lab_only=True,
        )
    req = ReleaseRequest(
        release_id=d.get("release_id", ""),
        release_type=d.get("release_type", ""),
        artifact_id=d.get("artifact_id", ""),
        artifact_version=d.get("artifact_version", ""),
        requestor_name=d.get("requestor_name", ""),
        requestor_institution=d.get("requestor_institution", ""),
        request_date=d.get("request_date", ""),
        evidence_level=d.get("evidence_level", 0),
        dry_lab_only=d.get("dry_lab_only", True),
        safety_review_status=d.get("safety_review_status", ""),
        benchmark_summary=d.get("benchmark_summary", ""),
        known_limitations=d.get("known_limitations", ""),
        intended_use=d.get("intended_use", ""),
        data_license=d.get("data_license", ""),
        human_reviewer=d.get("human_reviewer", ""),
        review_class=d.get("review_class", ""),
        approval_status=d.get("approval_status", ""),
    )
    return validate_release_request(req)

"""External advisory review process validation for OpenAMP Foundry."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

VALID_REVIEW_TYPES: set[str] = {
    "benchmark_audit",
    "candidate_review",
    "evidence_review",
    "governance_review",
    "safety_policy_review",
}
VALID_REVIEW_STATUSES: set[str] = {
    "assigned",
    "completed",
    "deferred",
    "in_progress",
    "pending",
}
VALID_FINDING_SEVERITIES: set[str] = {
    "critical",
    "informational",
    "major",
    "minor",
}
MINIMUM_REVIEWER_COUNTS: dict[str, int] = {
    "benchmark_audit": 1,
    "candidate_review": 2,
    "evidence_review": 1,
    "governance_review": 1,
    "safety_policy_review": 2,
}


@dataclass
class AdvisoryReview:
    """A single external advisory review entry."""

    review_id: str
    review_type: str
    artifact_id: str
    reviewer_handle: str
    assigned_date: str
    deadline_date: str
    status: str
    finding_severity: Optional[str] = None
    finding_summary: str = ""
    resolved: bool = False
    dry_lab_only: bool = True


@dataclass
class AdvisoryReviewResult:
    """Result of validating an AdvisoryReview."""

    review_id: str
    review_type: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_advisory_review(review: AdvisoryReview) -> AdvisoryReviewResult:
    """Validate an AdvisoryReview against policy rules."""
    errors: list[str] = []
    warnings: list[str] = []

    if not review.review_id or not str(review.review_id).strip():
        errors.append("review_id must be non-empty")
    elif not review.review_id.startswith("ADV-"):
        errors.append(
            f"review_id must start with 'ADV-', got: {review.review_id!r}"
        )

    if review.review_type not in VALID_REVIEW_TYPES:
        errors.append(
            f"review_type must be one of {sorted(VALID_REVIEW_TYPES)}, "
            f"got: {review.review_type!r}"
        )

    if not review.artifact_id or not review.artifact_id.strip():
        errors.append("artifact_id must be non-empty")

    if not review.reviewer_handle or not review.reviewer_handle.strip():
        errors.append("reviewer_handle must be non-empty")

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", review.assigned_date):
        errors.append(
            f"assigned_date must be YYYY-MM-DD, got: {review.assigned_date!r}"
        )

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", review.deadline_date):
        errors.append(
            f"deadline_date must be YYYY-MM-DD, got: {review.deadline_date!r}"
        )

    if review.status not in VALID_REVIEW_STATUSES:
        errors.append(
            f"status must be one of {sorted(VALID_REVIEW_STATUSES)}, "
            f"got: {review.status!r}"
        )

    if review.finding_severity is not None and review.finding_severity not in VALID_FINDING_SEVERITIES:
        errors.append(
            f"finding_severity must be one of {sorted(VALID_FINDING_SEVERITIES)}, "
            f"got: {review.finding_severity!r}"
        )

    if not review.dry_lab_only:
        errors.append("dry_lab_only must be True for advisory review entries")

    # Warnings
    if review.status == "completed" and review.finding_severity == "critical" and not review.resolved:
        warnings.append(
            "critical finding is unresolved: halt release until this is addressed"
        )

    if review.status == "completed" and not review.finding_summary:
        warnings.append(
            "status is 'completed' but finding_summary is empty: "
            "document the review outcome"
        )

    if review.status == "deferred":
        warnings.append(
            "review is 'deferred': document the reason and reschedule"
        )

    return AdvisoryReviewResult(
        review_id=review.review_id,
        review_type=review.review_type,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_advisory_review_dict(d: dict) -> AdvisoryReviewResult:
    """Validate a dict representation of an AdvisoryReview."""
    required = [
        "artifact_id",
        "assigned_date",
        "deadline_date",
        "review_id",
        "review_type",
        "reviewer_handle",
        "status",
    ]
    missing = [f for f in required if f not in d]
    if missing:
        return AdvisoryReviewResult(
            review_id=d.get("review_id", ""),
            review_type=d.get("review_type", ""),
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=True,
        )
    review = AdvisoryReview(
        review_id=d["review_id"],
        review_type=d["review_type"],
        artifact_id=d["artifact_id"],
        reviewer_handle=d["reviewer_handle"],
        assigned_date=d["assigned_date"],
        deadline_date=d["deadline_date"],
        status=d["status"],
        finding_severity=d.get("finding_severity"),
        finding_summary=d.get("finding_summary", ""),
        resolved=d.get("resolved", False),
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_advisory_review(review)

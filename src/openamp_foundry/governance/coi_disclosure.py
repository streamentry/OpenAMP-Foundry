"""COI disclosure validator — validates conflict-of-interest disclosures.

Ensures all required fields are present before a COI disclosure enters
the formal review queue.
Dry-lab only.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

VALID_DISCLOSURE_TYPES: set[str] = {
    "reviewer", "contributor", "maintainer", "external_advisor"
}

VALID_RELATIONSHIP_TYPES: set[str] = {
    "financial", "institutional", "competitive", "personal", "none"
}

VALID_REVIEW_STATUSES: set[str] = {
    "pending", "acknowledged", "resolved"
}


@dataclass
class COIDisclosure:
    disclosure_id: str          # e.g. "COI-2026-001"
    disclosure_type: str        # from VALID_DISCLOSURE_TYPES
    subject: str                # GitHub handle
    related_artifact: str       # artifact ID or PR number
    relationship_type: str      # from VALID_RELATIONSHIP_TYPES
    description: str            # required unless relationship_type == "none"
    disclosure_date: str        # YYYY-MM-DD
    recusal_required: bool
    reviewer: str               # GitHub handle of reviewer
    review_status: str          # from VALID_REVIEW_STATUSES
    dry_lab_only: bool = True


@dataclass
class COIValidationResult:
    disclosure_id: str
    disclosure_type: str
    passed: bool
    errors: list[str]
    warnings: list[str]
    dry_lab_only: bool = True


def validate_coi_disclosure(d: COIDisclosure) -> COIValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not d.disclosure_id or not d.disclosure_id.startswith("COI-"):
        errors.append("disclosure_id must not be empty and must start with 'COI-'")
    if d.disclosure_type not in VALID_DISCLOSURE_TYPES:
        errors.append(f"disclosure_type={d.disclosure_type!r} not in {sorted(VALID_DISCLOSURE_TYPES)}")
    if not d.subject:
        errors.append("subject must not be empty")
    if not d.related_artifact:
        errors.append("related_artifact must not be empty")
    if d.relationship_type not in VALID_RELATIONSHIP_TYPES:
        errors.append(f"relationship_type={d.relationship_type!r} not in {sorted(VALID_RELATIONSHIP_TYPES)}")
    if d.relationship_type != "none" and not d.description:
        errors.append("description must not be empty when relationship_type != 'none'")
    if not d.disclosure_date or len(d.disclosure_date) != 10 or d.disclosure_date[4] != "-":
        errors.append("disclosure_date must be in YYYY-MM-DD format")
    if not d.reviewer:
        errors.append("reviewer must not be empty")
    if d.review_status not in VALID_REVIEW_STATUSES:
        errors.append(f"review_status={d.review_status!r} not in {sorted(VALID_REVIEW_STATUSES)}")
    if not d.dry_lab_only:
        errors.append("dry_lab_only must be True")

    if d.relationship_type == "financial" and not d.recusal_required:
        warnings.append("financial relationships typically require recusal — verify with maintainer")

    return COIValidationResult(
        disclosure_id=d.disclosure_id or "<unknown>",
        disclosure_type=d.disclosure_type,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_coi_dict(data: dict[str, Any]) -> COIValidationResult:
    required = [
        "disclosure_id", "disclosure_type", "subject", "related_artifact",
        "relationship_type", "description", "disclosure_date",
        "recusal_required", "reviewer", "review_status",
    ]
    missing = [f for f in required if f not in data]
    if missing:
        return COIValidationResult(
            disclosure_id=data.get("disclosure_id", "<unknown>"),
            disclosure_type=data.get("disclosure_type", "<unknown>"),
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            warnings=[],
            dry_lab_only=True,
        )
    disclosure = COIDisclosure(
        disclosure_id=data.get("disclosure_id", ""),
        disclosure_type=data.get("disclosure_type", ""),
        subject=data.get("subject", ""),
        related_artifact=data.get("related_artifact", ""),
        relationship_type=data.get("relationship_type", ""),
        description=data.get("description", ""),
        disclosure_date=data.get("disclosure_date", ""),
        recusal_required=data.get("recusal_required", False),
        reviewer=data.get("reviewer", ""),
        review_status=data.get("review_status", ""),
        dry_lab_only=data.get("dry_lab_only", True),
    )
    return validate_coi_disclosure(disclosure)

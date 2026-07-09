"""Contribution intake validator for institutional contributors.

Validates that a proposed institutional contribution includes
the minimum required fields before it enters the review queue.
Dry-lab only.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

VALID_CONTRIBUTION_TYPES: set[str] = {
    "wet_lab_validation",
    "dataset_donation",
    "compute_sponsorship",
    "expert_review",
    "governance_participation",
    "algorithm_contribution",
}

VALID_REVIEW_CLASSES: set[str] = {"A", "B", "C", "D"}

# Minimum required fields per contribution type
REQUIRED_FIELDS_BY_TYPE: dict[str, list[str]] = {
    "wet_lab_validation": ["institution_name", "contact_email", "candidate_ids", "assay_type", "data_license"],
    "dataset_donation": ["institution_name", "contact_email", "dataset_description", "data_license", "record_count"],
    "compute_sponsorship": ["institution_name", "contact_email", "compute_hours", "platform"],
    "expert_review": ["institution_name", "contact_email", "reviewer_expertise", "scope"],
    "governance_participation": ["institution_name", "contact_email", "role", "availability"],
    "algorithm_contribution": ["institution_name", "contact_email", "algorithm_description", "has_tests", "data_license"],
}


@dataclass
class ContributionIntake:
    institution_name: str
    contact_email: str
    contribution_type: str
    proposed_scope: str
    human_review_required: bool
    dry_lab_only: bool = True
    extra_fields: dict[str, Any] | None = None


@dataclass
class IntakeValidationResult:
    institution_name: str
    contribution_type: str
    passed: bool
    errors: list[str]
    warnings: list[str]
    required_review_class: str
    dry_lab_only: bool = True


def validate_contribution_intake(
    intake: ContributionIntake,
) -> IntakeValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not intake.institution_name:
        errors.append("institution_name must not be empty")
    if not intake.contact_email or "@" not in intake.contact_email:
        errors.append("contact_email must be a valid email address")
    if intake.contribution_type not in VALID_CONTRIBUTION_TYPES:
        errors.append(
            f"contribution_type={intake.contribution_type!r} not in "
            f"{sorted(VALID_CONTRIBUTION_TYPES)}"
        )
    if not intake.proposed_scope:
        errors.append("proposed_scope must not be empty")
    if not intake.dry_lab_only:
        errors.append("dry_lab_only must be True")

    # Check type-specific required fields
    if intake.contribution_type in REQUIRED_FIELDS_BY_TYPE:
        required = REQUIRED_FIELDS_BY_TYPE[intake.contribution_type]
        extra = intake.extra_fields or {}
        missing = [f for f in required if f not in extra and f not in ("institution_name", "contact_email")]
        if missing:
            errors.append(f"Missing required fields for {intake.contribution_type}: {missing}")

    # wet_lab_validation always requires human review
    if intake.contribution_type == "wet_lab_validation" and not intake.human_review_required:
        errors.append("human_review_required must be True for wet_lab_validation")

    # Determine review class
    review_class_map = {
        "wet_lab_validation": "D",
        "dataset_donation": "B",
        "compute_sponsorship": "B",
        "expert_review": "D",
        "governance_participation": "A",
        "algorithm_contribution": "B",
    }
    required_review_class = review_class_map.get(intake.contribution_type, "B")

    if intake.contribution_type in {"dataset_donation", "algorithm_contribution"}:
        warnings.append("Data license will be verified by maintainers before acceptance")

    return IntakeValidationResult(
        institution_name=intake.institution_name or "<unknown>",
        contribution_type=intake.contribution_type,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        required_review_class=required_review_class,
        dry_lab_only=True,
    )


def validate_intake_dict(d: dict[str, Any]) -> IntakeValidationResult:
    """Validate a raw dict (e.g. from JSON)."""
    required_top = ["institution_name", "contact_email", "contribution_type", "proposed_scope", "human_review_required"]
    missing = [f for f in required_top if f not in d]
    if missing:
        return IntakeValidationResult(
            institution_name=d.get("institution_name", "<unknown>"),
            contribution_type=d.get("contribution_type", "<unknown>"),
            passed=False,
            errors=[f"Missing required top-level fields: {missing}"],
            warnings=[],
            required_review_class="B",
            dry_lab_only=True,
        )
    intake = ContributionIntake(
        institution_name=d.get("institution_name", ""),
        contact_email=d.get("contact_email", ""),
        contribution_type=d.get("contribution_type", ""),
        proposed_scope=d.get("proposed_scope", ""),
        human_review_required=d.get("human_review_required", False),
        dry_lab_only=d.get("dry_lab_only", True),
        extra_fields={k: v for k, v in d.items() if k not in required_top + ["dry_lab_only"]},
    )
    return validate_contribution_intake(intake)

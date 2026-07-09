"""Annual safety and benchmark review checklist validation for OpenAMP Foundry."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

VALID_REVIEW_SECTIONS: set[str] = {
    "benchmark_thresholds",
    "calibration_status",
    "data_governance",
    "governance_decisions",
    "safety_policy",
}
VALID_ENTRY_STATUSES: set[str] = {
    "completed",
    "deferred",
    "in_progress",
    "not_applicable",
    "pending",
}


@dataclass
class AnnualReviewEntry:
    """A single annual review checklist entry for one section."""

    review_id: str
    year: str
    section: str
    reviewer: str
    finding_count: int
    action_items_count: int
    status: str
    notes: str = ""
    completion_date: str = ""
    dry_lab_only: bool = True


@dataclass
class AnnualReviewResult:
    """Result of validating an AnnualReviewEntry."""

    review_id: str
    year: str
    section: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_annual_review_entry(entry: AnnualReviewEntry) -> AnnualReviewResult:
    """Validate an AnnualReviewEntry against policy rules."""
    errors: list[str] = []
    warnings: list[str] = []

    if not entry.review_id or not str(entry.review_id).strip():
        errors.append("review_id must be non-empty")
    elif not entry.review_id.startswith("ANN-"):
        errors.append(
            f"review_id must start with 'ANN-', got: {entry.review_id!r}"
        )

    if not re.match(r"^\d{4}$", str(entry.year)):
        errors.append(
            f"year must be a 4-digit string, got: {entry.year!r}"
        )

    if entry.section not in VALID_REVIEW_SECTIONS:
        errors.append(
            f"section must be one of {sorted(VALID_REVIEW_SECTIONS)}, "
            f"got: {entry.section!r}"
        )

    if not entry.reviewer or not str(entry.reviewer).strip():
        errors.append("reviewer must be non-empty")

    if not isinstance(entry.finding_count, int) or entry.finding_count < 0:
        errors.append(
            f"finding_count must be a non-negative integer, got: {entry.finding_count!r}"
        )

    if not isinstance(entry.action_items_count, int) or entry.action_items_count < 0:
        errors.append(
            f"action_items_count must be a non-negative integer, "
            f"got: {entry.action_items_count!r}"
        )

    if entry.status not in VALID_ENTRY_STATUSES:
        errors.append(
            f"status must be one of {sorted(VALID_ENTRY_STATUSES)}, "
            f"got: {entry.status!r}"
        )

    if entry.status == "completed" and not re.match(r"^\d{4}-\d{2}-\d{2}$", entry.completion_date):
        errors.append(
            f"completion_date must be YYYY-MM-DD when status is 'completed', "
            f"got: {entry.completion_date!r}"
        )

    if not entry.dry_lab_only:
        errors.append("dry_lab_only must be True for annual review entries")

    # Warnings
    if entry.status == "completed" and not entry.notes:
        warnings.append(
            "status is 'completed' but notes is empty: document the review outcome"
        )

    if entry.status == "deferred":
        warnings.append(
            "review is 'deferred': document the reason and reschedule before next release"
        )

    if (
        isinstance(entry.finding_count, int)
        and entry.finding_count > 0
        and isinstance(entry.action_items_count, int)
        and entry.action_items_count == 0
    ):
        warnings.append(
            f"finding_count is {entry.finding_count} but action_items_count is 0: "
            "findings must have corresponding action items"
        )

    return AnnualReviewResult(
        review_id=entry.review_id,
        year=entry.year,
        section=entry.section,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_annual_review_dict(d: dict) -> AnnualReviewResult:
    """Validate a dict representation of an AnnualReviewEntry."""
    required = [
        "action_items_count",
        "finding_count",
        "review_id",
        "reviewer",
        "section",
        "status",
        "year",
    ]
    missing = [f for f in required if f not in d]
    if missing:
        return AnnualReviewResult(
            review_id=d.get("review_id", ""),
            year=d.get("year", ""),
            section=d.get("section", ""),
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=True,
        )
    entry = AnnualReviewEntry(
        review_id=d["review_id"],
        year=d["year"],
        section=d["section"],
        reviewer=d["reviewer"],
        finding_count=d["finding_count"],
        action_items_count=d["action_items_count"],
        status=d["status"],
        notes=d.get("notes", ""),
        completion_date=d.get("completion_date", ""),
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_annual_review_entry(entry)

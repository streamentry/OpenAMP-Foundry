from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

MINIMUM_ARTIFACT_IDS: int = 3
MAX_SCOPE_LENGTH: int = 500
LONG_SCOPE_THRESHOLD: int = 300
LARGE_BATCH_THRESHOLD: int = 50
MAX_OPEN_QUESTIONS_WARNING: int = 5
MINIMAL_ARTIFACT_WARNING_COUNT: int = 3


@dataclass
class ReviewerBriefingEntry:
    briefing_id: str
    batch_id: str
    pipeline_version: str
    prepared_date: str
    reviewer_name: str
    candidate_count: int
    artifact_ids: List[str]
    open_questions: List[str]
    scope_description: str
    conflict_of_interest_declared: bool
    dry_lab_only: bool = True


@dataclass
class ReviewerBriefingResult:
    briefing_id: str
    batch_id: str
    reviewer_name: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_reviewer_briefing(entry: ReviewerBriefingEntry) -> ReviewerBriefingResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.briefing_id.startswith("RBP-"):
        errors.append(f"briefing_id must start with 'RBP-', got '{entry.briefing_id}'")

    if not entry.reviewer_name:
        errors.append("reviewer_name must not be empty")

    if entry.candidate_count < 1:
        errors.append(
            f"candidate_count must be at least 1, got {entry.candidate_count}"
        )

    if len(entry.artifact_ids) < MINIMUM_ARTIFACT_IDS:
        errors.append(
            f"artifact_ids must contain at least {MINIMUM_ARTIFACT_IDS} IDs, "
            f"got {len(entry.artifact_ids)}"
        )

    if not entry.scope_description:
        errors.append("scope_description must not be empty")
    elif len(entry.scope_description) > MAX_SCOPE_LENGTH:
        errors.append(
            f"scope_description exceeds {MAX_SCOPE_LENGTH} characters "
            f"(got {len(entry.scope_description)})"
        )

    if not entry.conflict_of_interest_declared:
        errors.append(
            "conflict_of_interest_declared must be True; "
            "reviewer must declare any conflict of interest before review begins"
        )

    if not entry.dry_lab_only:
        errors.append(
            "dry_lab_only must be True for reviewer briefing packages "
            "(computational pipeline only)"
        )

    if not errors:
        if entry.candidate_count > LARGE_BATCH_THRESHOLD:
            warnings.append(
                f"candidate_count={entry.candidate_count} exceeds {LARGE_BATCH_THRESHOLD}; "
                "large batch may create excessive review burden"
            )

        if len(entry.open_questions) > MAX_OPEN_QUESTIONS_WARNING:
            warnings.append(
                f"{len(entry.open_questions)} open questions exceed "
                f"{MAX_OPEN_QUESTIONS_WARNING}; briefing may be underfocused"
            )

        if entry.scope_description and len(entry.scope_description) > LONG_SCOPE_THRESHOLD:
            warnings.append(
                f"scope_description is long ({len(entry.scope_description)} chars > "
                f"{LONG_SCOPE_THRESHOLD}); consider tightening scope for the reviewer"
            )

        if len(entry.artifact_ids) == MINIMAL_ARTIFACT_WARNING_COUNT:
            warnings.append(
                f"only {MINIMAL_ARTIFACT_WARNING_COUNT} artifact IDs provided; "
                "consider adding more supporting artifacts for a thorough review"
            )

    passed = len(errors) == 0
    return ReviewerBriefingResult(
        briefing_id=entry.briefing_id,
        batch_id=entry.batch_id,
        reviewer_name=entry.reviewer_name,
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_reviewer_briefing_dict(d: dict) -> ReviewerBriefingResult:
    required_fields = [
        "briefing_id",
        "batch_id",
        "pipeline_version",
        "prepared_date",
        "reviewer_name",
        "candidate_count",
        "artifact_ids",
        "open_questions",
        "scope_description",
        "conflict_of_interest_declared",
    ]
    missing = [f for f in required_fields if f not in d]
    if missing:
        return ReviewerBriefingResult(
            briefing_id=d.get("briefing_id", "UNKNOWN"),
            batch_id=d.get("batch_id", "UNKNOWN"),
            reviewer_name=d.get("reviewer_name", "UNKNOWN"),
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=True,
        )

    entry = ReviewerBriefingEntry(
        briefing_id=d["briefing_id"],
        batch_id=d["batch_id"],
        pipeline_version=d["pipeline_version"],
        prepared_date=d["prepared_date"],
        reviewer_name=d["reviewer_name"],
        candidate_count=int(d["candidate_count"]),
        artifact_ids=d["artifact_ids"],
        open_questions=d["open_questions"],
        scope_description=d["scope_description"],
        conflict_of_interest_declared=bool(d["conflict_of_interest_declared"]),
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_reviewer_briefing(entry)

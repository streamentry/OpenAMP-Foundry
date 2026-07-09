"""Multi-candidate comparison schema (Phase L L4).

Validates structured side-by-side comparisons of two or more
candidates for publication-ready supplementary tables.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

MINIMUM_CANDIDATES: int = 2
MINIMUM_CRITERIA: int = 2
VALID_EVIDENCE_LEVELS: set[int] = {1, 2, 3, 4, 5, 6}
MAX_RATIONALE_LENGTH: int = 500
LARGE_CANDIDATE_SET_THRESHOLD: int = 10
RECOMMENDED_CRITERIA: int = 3

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class MultiCandidateComparisonEntry:
    """One multi-candidate comparison record."""

    comparison_id: str
    batch_id: str
    pipeline_version: str
    comparison_date: str
    candidate_ids: List[str]
    comparison_criteria: List[str]
    top_candidate_id: str
    top_candidate_rationale: str
    evidence_level: int
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class MultiCandidateComparisonResult:
    """Validation result for a MultiCandidateComparisonEntry."""

    comparison_id: str
    batch_id: str
    candidate_count: int
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_multi_candidate_comparison(
    entry: MultiCandidateComparisonEntry,
) -> MultiCandidateComparisonResult:
    """Validate a MultiCandidateComparisonEntry.  Returns a MultiCandidateComparisonResult."""
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.comparison_id.startswith("CMP-"):
        errors.append("comparison_id must start with 'CMP-'")

    if not entry.batch_id:
        errors.append("batch_id must not be empty")

    if not entry.pipeline_version:
        errors.append("pipeline_version must not be empty")

    if not _DATE_RE.match(entry.comparison_date):
        errors.append("comparison_date must be YYYY-MM-DD")

    if len(entry.candidate_ids) < MINIMUM_CANDIDATES:
        errors.append(
            f"candidate_ids must have at least {MINIMUM_CANDIDATES} entries"
        )

    if len(entry.comparison_criteria) < MINIMUM_CRITERIA:
        errors.append(
            f"comparison_criteria must have at least {MINIMUM_CRITERIA} entries"
        )

    if entry.top_candidate_id not in entry.candidate_ids:
        errors.append(
            f"top_candidate_id '{entry.top_candidate_id}' must be in candidate_ids"
        )

    if not entry.top_candidate_rationale:
        errors.append("top_candidate_rationale must not be empty")
    elif len(entry.top_candidate_rationale) > MAX_RATIONALE_LENGTH:
        errors.append(
            f"top_candidate_rationale exceeds {MAX_RATIONALE_LENGTH} characters "
            f"({len(entry.top_candidate_rationale)} chars)"
        )

    if entry.evidence_level not in VALID_EVIDENCE_LEVELS:
        errors.append(
            f"evidence_level {entry.evidence_level} is not valid; "
            f"must be one of {sorted(VALID_EVIDENCE_LEVELS)}"
        )

    if not entry.reviewer:
        errors.append("reviewer must not be empty")

    if entry.dry_lab_only is not True:
        errors.append("dry_lab_only must be True")

    if not errors:
        if entry.evidence_level <= 2:
            warnings.append(
                f"evidence_level {entry.evidence_level} is low (≤2); "
                "comparison may not be reliable."
            )

        if len(entry.candidate_ids) > LARGE_CANDIDATE_SET_THRESHOLD:
            warnings.append(
                f"Large candidate set ({len(entry.candidate_ids)} candidates); "
                "consider splitting into sub-groups for clarity."
            )

        if len(entry.comparison_criteria) < RECOMMENDED_CRITERIA:
            warnings.append(
                f"Only {len(entry.comparison_criteria)} comparison criterion/criteria; "
                f"consider adding more (recommended: {RECOMMENDED_CRITERIA}+) for depth."
            )

    return MultiCandidateComparisonResult(
        comparison_id=entry.comparison_id,
        batch_id=entry.batch_id,
        candidate_count=len(entry.candidate_ids),
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_multi_candidate_comparison_dict(d: dict) -> MultiCandidateComparisonResult:
    """Validate a dict representation of a MultiCandidateComparisonEntry."""
    required = [
        "comparison_id",
        "batch_id",
        "pipeline_version",
        "comparison_date",
        "candidate_ids",
        "comparison_criteria",
        "top_candidate_id",
        "top_candidate_rationale",
        "evidence_level",
        "reviewer",
    ]
    for key in required:
        if key not in d:
            return MultiCandidateComparisonResult(
                comparison_id=d.get("comparison_id", ""),
                batch_id=d.get("batch_id", ""),
                candidate_count=0,
                passed=False,
                errors=[f"missing required field: {key}"],
                warnings=[],
            )

    entry = MultiCandidateComparisonEntry(
        comparison_id=d["comparison_id"],
        batch_id=d["batch_id"],
        pipeline_version=d["pipeline_version"],
        comparison_date=d["comparison_date"],
        candidate_ids=d["candidate_ids"],
        comparison_criteria=d["comparison_criteria"],
        top_candidate_id=d["top_candidate_id"],
        top_candidate_rationale=d["top_candidate_rationale"],
        evidence_level=d["evidence_level"],
        reviewer=d["reviewer"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_multi_candidate_comparison(entry)

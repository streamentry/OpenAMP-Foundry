"""Expert review example package schema — Phase E E10.

A self-contained example of a complete expert-review submission, using only
toy/mock candidate data clearly labeled as such. This schema:

  1. Shows external reviewers what format to expect before they receive real data.
  2. Provides a CI-checkable template that cannot accidentally leak real candidates.
  3. Documents the full review workflow in a machine-readable, testable artifact.

All candidate data in this schema MUST be mock/toy. Real candidates must use
ReviewerQuestionnaire (RVQ-) and DomainReviewOutcome (DRO-) schemas instead.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

ERP_PREFIX = "ERP-"

VALID_REVIEW_DOMAINS = frozenset({
    "antimicrobial_activity",
    "toxicity_safety",
    "novelty_assessment",
    "simulation_quality",
    "evidence_completeness",
    "experimental_design",
})

VALID_SYNTHESIS_RECOMMENDATIONS = frozenset({
    "proceed",
    "proceed_with_conditions",
    "defer",
    "reject",
})

VALID_CLARITY_RATINGS = frozenset({1, 2, 3, 4, 5})  # Likert 1-5

MOCK_CANDIDATE_ID_PREFIXES = frozenset({
    "MOCK-", "TOY-", "EXAMPLE-", "DEMO-", "TEST-",
})

MIN_MOCK_CANDIDATES = 1
MAX_MOCK_CANDIDATES = 10
REVIEWER_COMMENTS_MAX_LENGTH = 500
SUMMARY_MAX_LENGTH = 400
NOTES_MAX_LENGTH = 300
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class MockCandidateSummary:
    """Summary of a single mock/toy candidate in an example review package."""
    candidate_id: str      # must start with a mock prefix
    sequence_length: int   # length of mock peptide (positive int)
    predicted_mic: float   # mock MIC value in µg/mL (positive)
    predicted_toxicity: str  # one of: "low", "moderate", "high"
    novelty_score: float   # [0.0, 1.0]
    include_in_example: bool  # True = shown to reviewer in this example


@dataclass
class ExpertReviewExamplePackage:
    erp_id: str
    pipeline_version: str
    example_version: str
    creation_date: str
    review_domain: str
    mock_candidates: List[MockCandidateSummary]
    overall_clarity_rating: int         # Likert 1-5
    synthesis_recommendation: str
    reviewer_comments: str
    dry_lab_only: bool
    is_example_data: bool               # must be True for this schema
    example_use_case: str               # what this example demonstrates
    summary: str
    notes: str = ""


def _validate_mock_candidate(
    candidate: MockCandidateSummary, index: int
) -> List[str]:
    errors: List[str] = []
    prefix_ok = any(
        candidate.candidate_id.startswith(p) for p in MOCK_CANDIDATE_ID_PREFIXES
    )
    if not prefix_ok:
        errors.append(
            f"mock_candidates[{index}].candidate_id must start with one of "
            f"{sorted(MOCK_CANDIDATE_ID_PREFIXES)}, got: {candidate.candidate_id!r}"
        )
    if candidate.sequence_length < 1:
        errors.append(
            f"mock_candidates[{index}].sequence_length must be >= 1, "
            f"got: {candidate.sequence_length}"
        )
    if candidate.predicted_mic <= 0:
        errors.append(
            f"mock_candidates[{index}].predicted_mic must be > 0, "
            f"got: {candidate.predicted_mic}"
        )
    valid_toxicities = frozenset({"low", "moderate", "high"})
    if candidate.predicted_toxicity not in valid_toxicities:
        errors.append(
            f"mock_candidates[{index}].predicted_toxicity must be one of "
            f"{sorted(valid_toxicities)}, got: {candidate.predicted_toxicity!r}"
        )
    if not (0.0 <= candidate.novelty_score <= 1.0):
        errors.append(
            f"mock_candidates[{index}].novelty_score must be in [0.0, 1.0], "
            f"got: {candidate.novelty_score}"
        )
    return errors


def validate(pkg: ExpertReviewExamplePackage) -> List[str]:
    """Return list of error strings; empty list means valid."""
    errors: List[str] = []

    # Rule 1: ID prefix
    if not pkg.erp_id.startswith(ERP_PREFIX):
        errors.append(
            f"erp_id must start with '{ERP_PREFIX}', got: {pkg.erp_id!r}"
        )

    # Rule 2: pipeline_version non-empty
    if not pkg.pipeline_version.strip():
        errors.append("pipeline_version must not be empty")

    # Rule 3: example_version non-empty
    if not pkg.example_version.strip():
        errors.append("example_version must not be empty")

    # Rule 4: creation_date ISO format
    if not _ISO_DATE_RE.match(pkg.creation_date):
        errors.append(
            f"creation_date must be YYYY-MM-DD, got: {pkg.creation_date!r}"
        )

    # Rule 5: review_domain vocabulary
    if pkg.review_domain not in VALID_REVIEW_DOMAINS:
        errors.append(
            f"review_domain must be one of {sorted(VALID_REVIEW_DOMAINS)}, "
            f"got: {pkg.review_domain!r}"
        )

    # Rule 6: mock_candidates count
    n = len(pkg.mock_candidates)
    if n < MIN_MOCK_CANDIDATES or n > MAX_MOCK_CANDIDATES:
        errors.append(
            f"mock_candidates must have between {MIN_MOCK_CANDIDATES} and "
            f"{MAX_MOCK_CANDIDATES} entries, got: {n}"
        )

    # Rule 7: validate each mock candidate
    for i, cand in enumerate(pkg.mock_candidates):
        errors.extend(_validate_mock_candidate(cand, i))

    # Rule 8: at least one candidate must be included in the example
    included = sum(1 for c in pkg.mock_candidates if c.include_in_example)
    if included < 1:
        errors.append(
            "At least one mock candidate must have include_in_example=True"
        )

    # Rule 9: overall_clarity_rating Likert 1-5
    if pkg.overall_clarity_rating not in VALID_CLARITY_RATINGS:
        errors.append(
            f"overall_clarity_rating must be in {{1,2,3,4,5}}, "
            f"got: {pkg.overall_clarity_rating}"
        )

    # Rule 10: synthesis_recommendation vocabulary
    if pkg.synthesis_recommendation not in VALID_SYNTHESIS_RECOMMENDATIONS:
        errors.append(
            f"synthesis_recommendation must be one of "
            f"{sorted(VALID_SYNTHESIS_RECOMMENDATIONS)}, "
            f"got: {pkg.synthesis_recommendation!r}"
        )

    # Rule 11: reviewer_comments non-empty and length
    if not pkg.reviewer_comments.strip():
        errors.append("reviewer_comments must not be empty")
    elif len(pkg.reviewer_comments) > REVIEWER_COMMENTS_MAX_LENGTH:
        errors.append(
            f"reviewer_comments exceeds {REVIEWER_COMMENTS_MAX_LENGTH} chars "
            f"(got {len(pkg.reviewer_comments)})"
        )

    # Rule 12: dry_lab_only must be True
    if not pkg.dry_lab_only:
        errors.append(
            "dry_lab_only must be True — expert review examples use only "
            "computational/dry-lab data"
        )

    # Rule 13: is_example_data must be True
    if not pkg.is_example_data:
        errors.append(
            "is_example_data must be True — this schema is for example packages "
            "only; use ReviewerQuestionnaire (RVQ-) for real review submissions"
        )

    # Rule 14: example_use_case non-empty
    if not pkg.example_use_case.strip():
        errors.append("example_use_case must not be empty")

    # Rule 15: summary non-empty and length
    if not pkg.summary.strip():
        errors.append("summary must not be empty")
    elif len(pkg.summary) > SUMMARY_MAX_LENGTH:
        errors.append(
            f"summary exceeds {SUMMARY_MAX_LENGTH} chars "
            f"(got {len(pkg.summary)})"
        )

    # Rule 16: notes length
    if len(pkg.notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"notes exceeds {NOTES_MAX_LENGTH} chars (got {len(pkg.notes)})"
        )

    # Warnings
    if pkg.overall_clarity_rating <= 2:
        errors.append(
            f"WARNING: overall_clarity_rating ({pkg.overall_clarity_rating}) is low — "
            "verify the example package is complete and well-structured"
        )
    excluded_count = sum(1 for c in pkg.mock_candidates if not c.include_in_example)
    if excluded_count > 0:
        errors.append(
            f"WARNING: {excluded_count} mock candidate(s) have "
            "include_in_example=False — verify exclusion is intentional"
        )
    if not pkg.notes.strip():
        errors.append(
            "WARNING: notes is empty — consider documenting the example context"
        )

    return errors


def validate_dict(data: dict) -> List[str]:
    """Validate a plain dict by constructing ExpertReviewExamplePackage first."""
    try:
        cands_raw = data.get("mock_candidates", [])
        cands = [MockCandidateSummary(**c) for c in cands_raw]
        pkg_data = {k: v for k, v in data.items() if k != "mock_candidates"}
        pkg = ExpertReviewExamplePackage(mock_candidates=cands, **pkg_data)
    except TypeError as exc:
        return [f"Schema construction error: {exc}"]
    return validate(pkg)

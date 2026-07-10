"""Reviewer questionnaire schema — Phase E E3.

Structured schema for external reviewer feedback on a PilotEvidencePackage
(PEP). Captures Likert-scale clarity ratings, a synthesis recommendation,
and structured comments. Makes external review machine-readable and enables
systematic improvement of the evidence package quality.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

RVQ_PREFIX = "RVQ-"
PEP_PREFIX = "PEP-"

VALID_RECOMMENDATIONS = frozenset({
    "yes",
    "no",
    "conditional",
    "insufficient_information",
})

LIKERT_MIN = 1
LIKERT_MAX = 5
COMMENTS_MAX_LENGTH = 600
LOW_QUALITY_THRESHOLD = 3


@dataclass
class ReviewerQuestionnaire:
    """Structured external reviewer feedback on a PilotEvidencePackage."""

    rvq_id: str
    pipeline_version: str
    pep_id: str  # must start with "PEP-"
    reviewer_token: str  # anonymized reviewer ID, no PII
    review_date: str  # ISO YYYY-MM-DD
    activity_prediction_clarity: int  # Likert 1-5
    safety_claim_clarity: int  # Likert 1-5
    novelty_claim_clarity: int  # Likert 1-5
    overall_package_quality: int  # Likert 1-5
    would_recommend_for_synthesis: str  # {yes, no, conditional, insufficient_information}
    missing_information: List[str]  # free-form list of gaps identified
    reviewer_comments: str  # max 600 chars
    dry_lab_only: bool = True


@dataclass
class ReviewerQuestionnaireResult:
    rvq_id: str
    pep_id: str
    overall_package_quality: int
    would_recommend_for_synthesis: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_reviewer_questionnaire(
    entry: ReviewerQuestionnaire,
) -> ReviewerQuestionnaireResult:
    errors: List[str] = []
    warnings: List[str] = []

    # Rule 1: RVQ- prefix
    if not entry.rvq_id.startswith(RVQ_PREFIX):
        errors.append(
            f"rvq_id must start with '{RVQ_PREFIX}', got '{entry.rvq_id}'"
        )

    # Rule 2: PEP- prefix
    if not entry.pep_id.startswith(PEP_PREFIX):
        errors.append(
            f"pep_id must start with '{PEP_PREFIX}', got '{entry.pep_id}'"
        )

    # Rule 3: non-empty required strings
    for fname, val in [
        ("pipeline_version", entry.pipeline_version),
        ("reviewer_token", entry.reviewer_token),
    ]:
        if not val or not val.strip():
            errors.append(f"{fname} must not be empty")

    # Rule 4: ISO date
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", entry.review_date):
        errors.append(
            f"review_date must be ISO format YYYY-MM-DD, got '{entry.review_date}'"
        )

    # Rule 5: activity_prediction_clarity in [1, 5]
    if not (LIKERT_MIN <= entry.activity_prediction_clarity <= LIKERT_MAX):
        errors.append(
            f"activity_prediction_clarity must be in [{LIKERT_MIN}, {LIKERT_MAX}], "
            f"got {entry.activity_prediction_clarity}"
        )

    # Rule 6: safety_claim_clarity in [1, 5]
    if not (LIKERT_MIN <= entry.safety_claim_clarity <= LIKERT_MAX):
        errors.append(
            f"safety_claim_clarity must be in [{LIKERT_MIN}, {LIKERT_MAX}], "
            f"got {entry.safety_claim_clarity}"
        )

    # Rule 7: novelty_claim_clarity in [1, 5]
    if not (LIKERT_MIN <= entry.novelty_claim_clarity <= LIKERT_MAX):
        errors.append(
            f"novelty_claim_clarity must be in [{LIKERT_MIN}, {LIKERT_MAX}], "
            f"got {entry.novelty_claim_clarity}"
        )

    # Rule 8: overall_package_quality in [1, 5]
    if not (LIKERT_MIN <= entry.overall_package_quality <= LIKERT_MAX):
        errors.append(
            f"overall_package_quality must be in [{LIKERT_MIN}, {LIKERT_MAX}], "
            f"got {entry.overall_package_quality}"
        )

    # Rule 9: valid recommendation
    if entry.would_recommend_for_synthesis not in VALID_RECOMMENDATIONS:
        errors.append(
            f"would_recommend_for_synthesis must be one of "
            f"{sorted(VALID_RECOMMENDATIONS)}, got '{entry.would_recommend_for_synthesis}'"
        )

    # Rule 10: reviewer_comments length
    if len(entry.reviewer_comments) > COMMENTS_MAX_LENGTH:
        errors.append(
            f"reviewer_comments must be at most {COMMENTS_MAX_LENGTH} characters, "
            f"got {len(entry.reviewer_comments)}"
        )

    # Warning 1: low overall quality score
    if (
        LIKERT_MIN <= entry.overall_package_quality < LOW_QUALITY_THRESHOLD
        and len(errors) == 0
    ):
        warnings.append(
            f"overall_package_quality is {entry.overall_package_quality}/5 — "
            "package needs significant improvement before external sharing"
        )

    # Warning 2: conditional recommendation without comments
    if (
        entry.would_recommend_for_synthesis == "conditional"
        and not entry.reviewer_comments.strip()
    ):
        warnings.append(
            "would_recommend_for_synthesis is 'conditional' but reviewer_comments is empty"
            " — document the conditions required"
        )

    # Warning 3: negative recommendation without missing_information
    if (
        entry.would_recommend_for_synthesis == "no"
        and not entry.missing_information
        and not entry.reviewer_comments.strip()
    ):
        warnings.append(
            "would_recommend_for_synthesis is 'no' with no missing_information or comments"
            " — document why synthesis is not recommended"
        )

    # Warning 4: insufficient_information without missing_information list
    if (
        entry.would_recommend_for_synthesis == "insufficient_information"
        and not entry.missing_information
    ):
        warnings.append(
            "would_recommend_for_synthesis is 'insufficient_information' but "
            "missing_information is empty — list the specific gaps"
        )

    passed = len(errors) == 0
    return ReviewerQuestionnaireResult(
        rvq_id=entry.rvq_id,
        pep_id=entry.pep_id,
        overall_package_quality=entry.overall_package_quality,
        would_recommend_for_synthesis=entry.would_recommend_for_synthesis,
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_reviewer_questionnaire_dict(data: dict) -> ReviewerQuestionnaireResult:
    entry = ReviewerQuestionnaire(
        rvq_id=data.get("rvq_id", ""),
        pipeline_version=data.get("pipeline_version", ""),
        pep_id=data.get("pep_id", ""),
        reviewer_token=data.get("reviewer_token", ""),
        review_date=data.get("review_date", ""),
        activity_prediction_clarity=int(data.get("activity_prediction_clarity", 0)),
        safety_claim_clarity=int(data.get("safety_claim_clarity", 0)),
        novelty_claim_clarity=int(data.get("novelty_claim_clarity", 0)),
        overall_package_quality=int(data.get("overall_package_quality", 0)),
        would_recommend_for_synthesis=data.get("would_recommend_for_synthesis", ""),
        missing_information=list(data.get("missing_information", [])),
        reviewer_comments=data.get("reviewer_comments", ""),
        dry_lab_only=bool(data.get("dry_lab_only", True)),
    )
    return validate_reviewer_questionnaire(entry)

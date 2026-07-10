"""Domain review outcome schema — Phase E E9.

Records the final verdict of a domain expert reviewer on a PilotEvidencePackage.
Uses a controlled taxonomy of expert domains and outcome verdicts, making expert
review decisions structured, auditable, and comparable across reviewers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

DRO_PREFIX = "DRO-"
RVQ_PREFIX = "RVQ-"
PEP_PREFIX = "PEP-"

VALID_REVIEW_DOMAINS = frozenset({
    "antimicrobial_activity",
    "toxicology",
    "structural_biology",
    "clinical_microbiology",
    "computational_chemistry",
    "general_biomedical",
})

VALID_OUTCOME_VERDICTS = frozenset({
    "approve",
    "reject",
    "conditional_approve",
    "request_revision",
    "insufficient_data",
})

VALID_OUTCOME_CONFIDENCES = frozenset({
    "high",
    "medium",
    "low",
})

RATIONALE_MAX_LENGTH = 400


@dataclass
class DomainReviewOutcome:
    """Formal expert verdict on a PilotEvidencePackage."""

    dro_id: str
    pipeline_version: str
    pep_id: str  # must start with "PEP-"
    rvq_id: str  # must start with "RVQ-" — the questionnaire that preceded this verdict
    reviewer_token: str  # anonymized reviewer ID, no PII
    review_domain: str  # controlled vocabulary
    review_date: str  # ISO YYYY-MM-DD
    outcome_verdict: str  # controlled vocabulary
    outcome_confidence: str  # {high, medium, low}
    outcome_rationale: str  # max 400 chars
    dry_lab_only: bool = True


@dataclass
class DomainReviewOutcomeResult:
    dro_id: str
    pep_id: str
    rvq_id: str
    review_domain: str
    outcome_verdict: str
    outcome_confidence: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_domain_review_outcome(
    entry: DomainReviewOutcome,
) -> DomainReviewOutcomeResult:
    errors: List[str] = []
    warnings: List[str] = []

    # Rule 1: DRO- prefix
    if not entry.dro_id.startswith(DRO_PREFIX):
        errors.append(
            f"dro_id must start with '{DRO_PREFIX}', got '{entry.dro_id}'"
        )

    # Rule 2: PEP- prefix
    if not entry.pep_id.startswith(PEP_PREFIX):
        errors.append(
            f"pep_id must start with '{PEP_PREFIX}', got '{entry.pep_id}'"
        )

    # Rule 3: RVQ- prefix
    if not entry.rvq_id.startswith(RVQ_PREFIX):
        errors.append(
            f"rvq_id must start with '{RVQ_PREFIX}', got '{entry.rvq_id}'"
        )

    # Rule 4: non-empty required strings
    for fname, val in [
        ("pipeline_version", entry.pipeline_version),
        ("reviewer_token", entry.reviewer_token),
    ]:
        if not val or not val.strip():
            errors.append(f"{fname} must not be empty")

    # Rule 5: valid review domain
    if entry.review_domain not in VALID_REVIEW_DOMAINS:
        errors.append(
            f"review_domain must be one of {sorted(VALID_REVIEW_DOMAINS)}, "
            f"got '{entry.review_domain}'"
        )

    # Rule 6: ISO date
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", entry.review_date):
        errors.append(
            f"review_date must be ISO format YYYY-MM-DD, got '{entry.review_date}'"
        )

    # Rule 7: valid outcome verdict
    if entry.outcome_verdict not in VALID_OUTCOME_VERDICTS:
        errors.append(
            f"outcome_verdict must be one of {sorted(VALID_OUTCOME_VERDICTS)}, "
            f"got '{entry.outcome_verdict}'"
        )

    # Rule 8: valid outcome confidence
    if entry.outcome_confidence not in VALID_OUTCOME_CONFIDENCES:
        errors.append(
            f"outcome_confidence must be one of {sorted(VALID_OUTCOME_CONFIDENCES)}, "
            f"got '{entry.outcome_confidence}'"
        )

    # Rule 9: rationale length
    if len(entry.outcome_rationale) > RATIONALE_MAX_LENGTH:
        errors.append(
            f"outcome_rationale must be at most {RATIONALE_MAX_LENGTH} characters, "
            f"got {len(entry.outcome_rationale)}"
        )

    # Warning 1: conditional_approve without rationale
    if (
        entry.outcome_verdict == "conditional_approve"
        and not entry.outcome_rationale.strip()
    ):
        warnings.append(
            "outcome_verdict is 'conditional_approve' but outcome_rationale is empty"
            " — document the conditions required for approval"
        )

    # Warning 2: reject with low confidence
    if (
        entry.outcome_verdict == "reject"
        and entry.outcome_confidence == "low"
    ):
        warnings.append(
            "outcome_verdict is 'reject' with outcome_confidence='low'"
            " — a low-confidence rejection may need additional expert review"
        )

    # Warning 3: insufficient_data without rationale
    if (
        entry.outcome_verdict == "insufficient_data"
        and not entry.outcome_rationale.strip()
    ):
        warnings.append(
            "outcome_verdict is 'insufficient_data' but outcome_rationale is empty"
            " — document what data is missing"
        )

    passed = len(errors) == 0
    return DomainReviewOutcomeResult(
        dro_id=entry.dro_id,
        pep_id=entry.pep_id,
        rvq_id=entry.rvq_id,
        review_domain=entry.review_domain,
        outcome_verdict=entry.outcome_verdict,
        outcome_confidence=entry.outcome_confidence,
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_domain_review_outcome_dict(data: dict) -> DomainReviewOutcomeResult:
    entry = DomainReviewOutcome(
        dro_id=data.get("dro_id", ""),
        pipeline_version=data.get("pipeline_version", ""),
        pep_id=data.get("pep_id", ""),
        rvq_id=data.get("rvq_id", ""),
        reviewer_token=data.get("reviewer_token", ""),
        review_domain=data.get("review_domain", ""),
        review_date=data.get("review_date", ""),
        outcome_verdict=data.get("outcome_verdict", ""),
        outcome_confidence=data.get("outcome_confidence", ""),
        outcome_rationale=data.get("outcome_rationale", ""),
        dry_lab_only=bool(data.get("dry_lab_only", True)),
    )
    return validate_domain_review_outcome(entry)

"""Rejection reason entry schema — Phase F F3.

Records why a candidate was rejected during the selection pipeline with a
controlled vocabulary of stages and reasons. Makes failure analysis
machine-readable and feeds the calibration loop with structured signal
about which screens catch which failure modes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

RJR_PREFIX = "RJR-"

VALID_REJECTION_STAGES = frozenset({
    "initial_screen",
    "toxicity_screen",
    "hemolysis_screen",
    "novelty_filter",
    "selection_gate",
    "safety_policy_block",
    "manual_exclusion",
})

VALID_REJECTION_REASONS = frozenset({
    "low_activity_score",
    "hemolysis_risk",
    "toxicity_risk",
    "insufficient_novelty",
    "data_quality_failure",
    "safety_policy_block",
    "duplicate",
    "out_of_scope",
    "manual_exclusion",
})

VALID_REJECTION_CONFIDENCES = frozenset({
    "high",
    "medium",
    "low",
    "uncertain",
})

NOTES_MAX_LENGTH = 400


@dataclass
class RejectionReasonEntry:
    """Structured record of why a candidate was rejected."""

    rjr_id: str
    pipeline_version: str
    candidate_id: str
    rejection_stage: str  # controlled vocabulary
    rejection_reason: str  # controlled vocabulary
    rejection_confidence: str  # {high, medium, low, uncertain}
    rejection_date: str  # ISO YYYY-MM-DD
    borderline: bool  # True if this was a close call
    reviewer: str
    rejection_notes: str  # max 400 chars
    dry_lab_only: bool = True


@dataclass
class RejectionReasonResult:
    rjr_id: str
    candidate_id: str
    rejection_stage: str
    rejection_reason: str
    rejection_confidence: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_rejection_reason(
    entry: RejectionReasonEntry,
) -> RejectionReasonResult:
    errors: List[str] = []
    warnings: List[str] = []

    # Rule 1: RJR- prefix
    if not entry.rjr_id.startswith(RJR_PREFIX):
        errors.append(
            f"rjr_id must start with '{RJR_PREFIX}', got '{entry.rjr_id}'"
        )

    # Rule 2: non-empty required strings
    for fname, val in [
        ("pipeline_version", entry.pipeline_version),
        ("candidate_id", entry.candidate_id),
        ("reviewer", entry.reviewer),
    ]:
        if not val or not val.strip():
            errors.append(f"{fname} must not be empty")

    # Rule 3: valid rejection stage
    if entry.rejection_stage not in VALID_REJECTION_STAGES:
        errors.append(
            f"rejection_stage must be one of {sorted(VALID_REJECTION_STAGES)}, "
            f"got '{entry.rejection_stage}'"
        )

    # Rule 4: valid rejection reason
    if entry.rejection_reason not in VALID_REJECTION_REASONS:
        errors.append(
            f"rejection_reason must be one of {sorted(VALID_REJECTION_REASONS)}, "
            f"got '{entry.rejection_reason}'"
        )

    # Rule 5: valid rejection confidence
    if entry.rejection_confidence not in VALID_REJECTION_CONFIDENCES:
        errors.append(
            f"rejection_confidence must be one of {sorted(VALID_REJECTION_CONFIDENCES)}, "
            f"got '{entry.rejection_confidence}'"
        )

    # Rule 6: rejection_date must be ISO YYYY-MM-DD
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", entry.rejection_date):
        errors.append(
            f"rejection_date must be ISO format YYYY-MM-DD, got '{entry.rejection_date}'"
        )

    # Rule 7: rejection_notes length
    if len(entry.rejection_notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"rejection_notes must be at most {NOTES_MAX_LENGTH} characters, "
            f"got {len(entry.rejection_notes)}"
        )

    # Rule 8: manual_exclusion reason requires notes
    if (
        entry.rejection_reason == "manual_exclusion"
        and not entry.rejection_notes.strip()
    ):
        errors.append(
            "rejection_notes must not be empty when rejection_reason is 'manual_exclusion'"
            " — always document manual exclusions"
        )

    # Rule 9: borderline=True requires confidence != high
    if entry.borderline and entry.rejection_confidence == "high":
        errors.append(
            "borderline=True is inconsistent with rejection_confidence='high'"
            " — borderline cases should have confidence 'medium', 'low', or 'uncertain'"
        )

    # Warning 1: uncertain confidence
    if entry.rejection_confidence == "uncertain":
        warnings.append(
            "rejection_confidence is 'uncertain' — this candidate may need re-evaluation"
        )

    # Warning 2: borderline without notes
    if entry.borderline and not entry.rejection_notes.strip():
        warnings.append(
            "borderline=True but rejection_notes is empty — document the borderline rationale"
        )

    # Warning 3: safety_policy_block without manual review note
    if entry.rejection_reason == "safety_policy_block" and not entry.rejection_notes.strip():
        warnings.append(
            "rejection_reason is 'safety_policy_block' with no rejection_notes"
            " — document which policy was triggered"
        )

    passed = len(errors) == 0
    return RejectionReasonResult(
        rjr_id=entry.rjr_id,
        candidate_id=entry.candidate_id,
        rejection_stage=entry.rejection_stage,
        rejection_reason=entry.rejection_reason,
        rejection_confidence=entry.rejection_confidence,
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_rejection_reason_dict(data: dict) -> RejectionReasonResult:
    entry = RejectionReasonEntry(
        rjr_id=data.get("rjr_id", ""),
        pipeline_version=data.get("pipeline_version", ""),
        candidate_id=data.get("candidate_id", ""),
        rejection_stage=data.get("rejection_stage", ""),
        rejection_reason=data.get("rejection_reason", ""),
        rejection_confidence=data.get("rejection_confidence", ""),
        rejection_date=data.get("rejection_date", ""),
        borderline=bool(data.get("borderline", False)),
        reviewer=data.get("reviewer", ""),
        rejection_notes=data.get("rejection_notes", ""),
        dry_lab_only=bool(data.get("dry_lab_only", True)),
    )
    return validate_rejection_reason(entry)

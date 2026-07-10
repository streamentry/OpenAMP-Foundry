"""Negative result entry schema — Phase F F1.

Records the outcome of a failed candidate at a specific pipeline stage.
Atomic failure record indexed by NAS- and aggregated by FCR-.
Uses controlled vocabulary for rejection stage, reason, and confidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

NRR_PREFIX = "NRR-"

VALID_REJECTION_STAGES = frozenset({
    "sequence_quality",
    "candidate_selection",
    "toxicity_screen",
    "hemolysis_screen",
    "novelty_check",
    "simulation",
    "manual_review",
})

VALID_REJECTION_REASONS = frozenset({
    "low_score",
    "failed_toxicity",
    "failed_hemolysis",
    "insufficient_novelty",
    "simulation_failure",
    "duplicate_sequence",
    "low_confidence",
    "borderline_unsafe",
    "manual_exclusion",
})

VALID_REJECTION_CONFIDENCES = frozenset({
    "high",
    "medium",
    "low",
    "uncertain",
})

OUTCOME_SUMMARY_MAX_LENGTH = 400
NOTES_MAX_LENGTH = 300
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class NegativeResultEntry:
    nrr_id: str
    pipeline_version: str
    candidate_id: str
    batch_id: str
    experiment_date: str
    stage_at_rejection: str
    rejection_reason: str
    rejection_confidence: str
    outcome_summary: str
    rejection_is_final: bool = True
    notes: str = ""
    dry_lab_only: bool = True


@dataclass
class NegativeResultEntryResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate(entry: NegativeResultEntry) -> NegativeResultEntryResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.nrr_id.startswith(NRR_PREFIX):
        errors.append(f"nrr_id must start with '{NRR_PREFIX}', got: {entry.nrr_id!r}")

    if not entry.pipeline_version.strip():
        errors.append("pipeline_version must be a non-empty string")

    if not entry.candidate_id.strip():
        errors.append("candidate_id must be a non-empty string")

    if not entry.batch_id.strip():
        errors.append("batch_id must be a non-empty string")

    if not _ISO_DATE_RE.match(entry.experiment_date):
        errors.append(
            f"experiment_date must be ISO format YYYY-MM-DD, got: {entry.experiment_date!r}"
        )

    if entry.stage_at_rejection not in VALID_REJECTION_STAGES:
        errors.append(
            f"stage_at_rejection {entry.stage_at_rejection!r} not in valid set: "
            f"{sorted(VALID_REJECTION_STAGES)}"
        )

    if entry.rejection_reason not in VALID_REJECTION_REASONS:
        errors.append(
            f"rejection_reason {entry.rejection_reason!r} not in valid set: "
            f"{sorted(VALID_REJECTION_REASONS)}"
        )

    if entry.rejection_confidence not in VALID_REJECTION_CONFIDENCES:
        errors.append(
            f"rejection_confidence {entry.rejection_confidence!r} not in valid set: "
            f"{sorted(VALID_REJECTION_CONFIDENCES)}"
        )

    if not entry.outcome_summary.strip():
        errors.append("outcome_summary must be a non-empty string")
    elif len(entry.outcome_summary) > OUTCOME_SUMMARY_MAX_LENGTH:
        errors.append(
            f"outcome_summary exceeds {OUTCOME_SUMMARY_MAX_LENGTH} chars "
            f"(got {len(entry.outcome_summary)})"
        )

    if len(entry.notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"notes exceeds {NOTES_MAX_LENGTH} chars (got {len(entry.notes)})"
        )

    # Warnings
    if not entry.rejection_is_final and entry.rejection_confidence == "high":
        warnings.append(
            "rejection_is_final=False with rejection_confidence='high' is unusual; "
            "verify this record is intentionally provisional"
        )

    if (
        entry.stage_at_rejection == "manual_review"
        and entry.rejection_reason != "manual_exclusion"
    ):
        warnings.append(
            "stage_at_rejection='manual_review' typically uses rejection_reason='manual_exclusion'; "
            f"got {entry.rejection_reason!r}"
        )

    if entry.rejection_confidence == "uncertain" and entry.rejection_is_final:
        warnings.append(
            "rejection_confidence='uncertain' with rejection_is_final=True; "
            "consider marking as non-final until confidence improves"
        )

    if entry.rejection_reason == "manual_exclusion" and not entry.notes.strip():
        warnings.append(
            "rejection_reason='manual_exclusion' without notes; "
            "human exclusion decisions should be explained"
        )

    return NegativeResultEntryResult(valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_dict(data: dict) -> NegativeResultEntryResult:
    try:
        entry = NegativeResultEntry(
            nrr_id=data.get("nrr_id", ""),
            pipeline_version=data.get("pipeline_version", ""),
            candidate_id=data.get("candidate_id", ""),
            batch_id=data.get("batch_id", ""),
            experiment_date=data.get("experiment_date", ""),
            stage_at_rejection=data.get("stage_at_rejection", ""),
            rejection_reason=data.get("rejection_reason", ""),
            rejection_confidence=data.get("rejection_confidence", ""),
            outcome_summary=data.get("outcome_summary", ""),
            rejection_is_final=bool(data.get("rejection_is_final", True)),
            notes=data.get("notes", ""),
            dry_lab_only=bool(data.get("dry_lab_only", True)),
        )
    except Exception as exc:
        return NegativeResultEntryResult(valid=False, errors=[f"Construction error: {exc}"])
    return validate(entry)

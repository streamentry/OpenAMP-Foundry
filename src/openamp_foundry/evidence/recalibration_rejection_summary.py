"""Recalibration rejection summary schema — Phase G G2.

Aggregates multiple recalibration refusal events across a pipeline period
to show that the calibration gate is working correctly — that the right
recalibrations were correctly refused, not rubber-stamped.

A healthy rejection summary shows refusals happening for documented reasons,
not silence or blanket approval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

RRS_PREFIX = "RRS-"

VALID_TOP_REFUSAL_REASONS = frozenset({
    "insufficient_data",
    "effect_within_noise",
    "recent_recalibration",
    "conflicting_signals",
    "reviewer_override",
    "multiple_reasons",
    "none_refused",
})

VALID_GATE_STATUSES = frozenset({
    "active",
    "suspended",
    "under_review",
})

REFUSAL_RATE_TOLERANCE = 0.01
HIGH_REFUSAL_RATE_WARNING = 0.9
ZERO_REFUSAL_WARNING_THRESHOLD = 0  # warn when zero refusals observed
SUMMARY_MAX_LENGTH = 400
NOTES_MAX_LENGTH = 300
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class RecalibrationRejectionSummary:
    rrs_id: str
    pipeline_version: str
    period_start: str
    period_end: str
    total_checkpoints_reviewed: int
    total_refused: int
    total_approved: int
    refusal_rate: float
    top_refusal_reason: str
    gate_status: str
    all_refusals_have_rrf: bool
    summary: str
    notes: str = ""


def validate(summary: RecalibrationRejectionSummary) -> List[str]:
    """Return list of error strings; empty list means valid."""
    errors: List[str] = []

    # Rule 1: ID prefix
    if not summary.rrs_id.startswith(RRS_PREFIX):
        errors.append(
            f"rrs_id must start with '{RRS_PREFIX}', got: {summary.rrs_id!r}"
        )

    # Rule 2: pipeline_version non-empty
    if not summary.pipeline_version.strip():
        errors.append("pipeline_version must not be empty")

    # Rule 3: period_start ISO format
    if not _ISO_DATE_RE.match(summary.period_start):
        errors.append(
            f"period_start must be YYYY-MM-DD, got: {summary.period_start!r}"
        )

    # Rule 4: period_end ISO format
    if not _ISO_DATE_RE.match(summary.period_end):
        errors.append(
            f"period_end must be YYYY-MM-DD, got: {summary.period_end!r}"
        )

    # Rule 5: total_checkpoints_reviewed >= 1
    if summary.total_checkpoints_reviewed < 1:
        errors.append(
            f"total_checkpoints_reviewed must be >= 1, "
            f"got: {summary.total_checkpoints_reviewed}"
        )

    # Rule 6: total_refused in [0, total_checkpoints_reviewed]
    if not (0 <= summary.total_refused <= summary.total_checkpoints_reviewed):
        errors.append(
            f"total_refused must be in [0, {summary.total_checkpoints_reviewed}], "
            f"got: {summary.total_refused}"
        )

    # Rule 7: total_approved in [0, total_checkpoints_reviewed]
    if not (0 <= summary.total_approved <= summary.total_checkpoints_reviewed):
        errors.append(
            f"total_approved must be in [0, {summary.total_checkpoints_reviewed}], "
            f"got: {summary.total_approved}"
        )

    # Rule 8: total_refused + total_approved == total_checkpoints_reviewed
    if (
        summary.total_refused + summary.total_approved
        != summary.total_checkpoints_reviewed
    ):
        errors.append(
            f"total_refused ({summary.total_refused}) + "
            f"total_approved ({summary.total_approved}) must equal "
            f"total_checkpoints_reviewed ({summary.total_checkpoints_reviewed})"
        )

    # Rule 9: refusal_rate in [0.0, 1.0]
    if not (0.0 <= summary.refusal_rate <= 1.0):
        errors.append(
            f"refusal_rate must be in [0.0, 1.0], got: {summary.refusal_rate}"
        )

    # Rule 10: refusal_rate consistency check (tolerance 0.01)
    if summary.total_checkpoints_reviewed >= 1:
        computed = summary.total_refused / summary.total_checkpoints_reviewed
        if abs(computed - summary.refusal_rate) > REFUSAL_RATE_TOLERANCE:
            errors.append(
                f"refusal_rate ({summary.refusal_rate:.4f}) inconsistent with "
                f"total_refused/total_checkpoints_reviewed "
                f"({summary.total_refused}/{summary.total_checkpoints_reviewed} "
                f"= {computed:.4f}); tolerance is {REFUSAL_RATE_TOLERANCE}"
            )

    # Rule 11: top_refusal_reason vocabulary
    if summary.top_refusal_reason not in VALID_TOP_REFUSAL_REASONS:
        errors.append(
            f"top_refusal_reason must be one of {sorted(VALID_TOP_REFUSAL_REASONS)}, "
            f"got: {summary.top_refusal_reason!r}"
        )

    # Rule 12: gate_status vocabulary
    if summary.gate_status not in VALID_GATE_STATUSES:
        errors.append(
            f"gate_status must be one of {sorted(VALID_GATE_STATUSES)}, "
            f"got: {summary.gate_status!r}"
        )

    # Rule 13: all_refusals_have_rrf must be True
    if not summary.all_refusals_have_rrf:
        errors.append(
            "all_refusals_have_rrf must be True — every refusal must "
            "have a corresponding RRF- artifact"
        )

    # Rule 14: summary non-empty and length
    if not summary.summary.strip():
        errors.append("summary must not be empty")
    elif len(summary.summary) > SUMMARY_MAX_LENGTH:
        errors.append(
            f"summary exceeds {SUMMARY_MAX_LENGTH} chars "
            f"(got {len(summary.summary)})"
        )

    # Rule 15: notes length
    if len(summary.notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"notes exceeds {NOTES_MAX_LENGTH} chars (got {len(summary.notes)})"
        )

    # Warnings
    if summary.refusal_rate >= HIGH_REFUSAL_RATE_WARNING:
        errors.append(
            f"WARNING: refusal_rate ({summary.refusal_rate:.2f}) > "
            f"{HIGH_REFUSAL_RATE_WARNING} — investigate whether gate thresholds "
            "are too strict"
        )
    if summary.total_refused == ZERO_REFUSAL_WARNING_THRESHOLD:
        errors.append(
            "WARNING: total_refused is 0 — verify that the gate is operating "
            "and not silently approving all recalibrations"
        )
    if not summary.notes.strip():
        errors.append(
            "WARNING: notes is empty — consider adding context for reviewers"
        )

    return errors


def validate_dict(data: dict) -> List[str]:
    """Validate a plain dict by constructing RecalibrationRejectionSummary first."""
    try:
        s = RecalibrationRejectionSummary(**data)
    except TypeError as exc:
        return [f"Schema construction error: {exc}"]
    return validate(s)

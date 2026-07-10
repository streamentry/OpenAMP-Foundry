"""Recalibration decision log schema — Phase G G1.

Records the governance decision at each recalibration checkpoint:
whether recalibration was approved or refused, the trigger artifact,
the deciding evidence, and who (or what process) made the call.

This schema enables audit trails across multiple calibration cycles
so patterns of approval/refusal can themselves be reviewed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

RDL_PREFIX = "RDL-"

VALID_DECISION_OUTCOMES = frozenset({
    "approved",
    "refused",
    "deferred",
    "partial_approved",
})

VALID_TRIGGER_TYPES = frozenset({
    "batch_outcome",
    "calibration_performance_summary",
    "scheduled_review",
    "anomaly_detected",
    "human_request",
})

VALID_TRIGGER_ID_PREFIXES = frozenset({
    "CPS-", "DRM-", "PCI-", "BSP-", "CIR-", "RRF-",
})

VALID_DECISION_AUTHORITIES = frozenset({
    "automated_gate",
    "pipeline_owner",
    "external_reviewer",
    "safety_officer",
    "committee",
})

RATIONALE_MAX_LENGTH = 500
NOTES_MAX_LENGTH = 300
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class RecalibrationDecisionLog:
    rdl_id: str
    pipeline_version: str
    calibration_checkpoint: str
    decision_date: str
    trigger_type: str
    trigger_artifact_id: str
    decision_outcome: str
    decision_authority: str
    evidence_summary: str
    rationale: str
    next_review_date: str
    conditions_if_deferred: str = ""
    notes: str = ""


def validate(log: RecalibrationDecisionLog) -> List[str]:
    """Return list of error strings; empty list means valid."""
    errors: List[str] = []
    warnings: List[str] = []

    # Rule 1: ID prefix
    if not log.rdl_id.startswith(RDL_PREFIX):
        errors.append(f"rdl_id must start with '{RDL_PREFIX}', got: {log.rdl_id!r}")

    # Rule 2: pipeline_version non-empty
    if not log.pipeline_version.strip():
        errors.append("pipeline_version must not be empty")

    # Rule 3: calibration_checkpoint non-empty
    if not log.calibration_checkpoint.strip():
        errors.append("calibration_checkpoint must not be empty")

    # Rule 4: decision_date ISO format
    if not _ISO_DATE_RE.match(log.decision_date):
        errors.append(f"decision_date must be YYYY-MM-DD, got: {log.decision_date!r}")

    # Rule 5: trigger_type vocabulary
    if log.trigger_type not in VALID_TRIGGER_TYPES:
        errors.append(
            f"trigger_type must be one of {sorted(VALID_TRIGGER_TYPES)}, "
            f"got: {log.trigger_type!r}"
        )

    # Rule 6: trigger_artifact_id must start with a known prefix
    if not any(log.trigger_artifact_id.startswith(p) for p in VALID_TRIGGER_ID_PREFIXES):
        errors.append(
            f"trigger_artifact_id must start with one of "
            f"{sorted(VALID_TRIGGER_ID_PREFIXES)}, got: {log.trigger_artifact_id!r}"
        )

    # Rule 7: decision_outcome vocabulary
    if log.decision_outcome not in VALID_DECISION_OUTCOMES:
        errors.append(
            f"decision_outcome must be one of {sorted(VALID_DECISION_OUTCOMES)}, "
            f"got: {log.decision_outcome!r}"
        )

    # Rule 8: decision_authority vocabulary
    if log.decision_authority not in VALID_DECISION_AUTHORITIES:
        errors.append(
            f"decision_authority must be one of {sorted(VALID_DECISION_AUTHORITIES)}, "
            f"got: {log.decision_authority!r}"
        )

    # Rule 9: evidence_summary non-empty
    if not log.evidence_summary.strip():
        errors.append("evidence_summary must not be empty")

    # Rule 10: rationale non-empty and length
    if not log.rationale.strip():
        errors.append("rationale must not be empty")
    elif len(log.rationale) > RATIONALE_MAX_LENGTH:
        errors.append(
            f"rationale exceeds {RATIONALE_MAX_LENGTH} chars "
            f"(got {len(log.rationale)})"
        )

    # Rule 11: next_review_date ISO format
    if not _ISO_DATE_RE.match(log.next_review_date):
        errors.append(
            f"next_review_date must be YYYY-MM-DD, got: {log.next_review_date!r}"
        )

    # Rule 12: deferred outcome requires conditions
    if log.decision_outcome == "deferred" and not log.conditions_if_deferred.strip():
        errors.append(
            "conditions_if_deferred must not be empty when decision_outcome is 'deferred'"
        )

    # Rule 13: notes length
    if len(log.notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"notes exceeds {NOTES_MAX_LENGTH} chars (got {len(log.notes)})"
        )

    # Warnings (returned with "WARNING:" prefix)
    if log.decision_outcome == "refused":
        warnings.append(
            "WARNING: decision_outcome is 'refused' — verify refusal rationale "
            "cites a specific RRF- artifact or documented reason"
        )
    if log.decision_outcome == "deferred" and not log.notes.strip():
        warnings.append(
            "WARNING: deferred decision has no notes — consider documenting "
            "the deferral context"
        )
    if not log.notes.strip():
        warnings.append(
            "WARNING: notes is empty — consider adding context for future reviewers"
        )

    return errors + warnings


def validate_dict(data: dict) -> List[str]:
    """Validate a plain dict by constructing RecalibrationDecisionLog first."""
    try:
        log = RecalibrationDecisionLog(**data)
    except TypeError as exc:
        return [f"Schema construction error: {exc}"]
    return validate(log)

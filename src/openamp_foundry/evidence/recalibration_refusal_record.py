"""Recalibration refusal record schema — Phase P P2.

Documents when calibration recalibration was correctly rejected because the
evidence was insufficient or the detected signal was within normal noise.

A refusal is a quality outcome, not a failure.  Refusing to recalibrate on
weak evidence preserves pipeline integrity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

RRF_PREFIX = "RRF-"
VALID_TRIGGER_PREFIXES = frozenset({"CPS-", "DRM-"})
VALID_REFUSAL_REASONS = frozenset(
    {
        "insufficient_data",
        "effect_within_noise",
        "recent_recalibration",
        "conflicting_signals",
        "reviewer_override",
    }
)
REFUSAL_NOTES_MAX_LENGTH = 400
MIN_BATCHES_FLOOR = 1
POOR_BRIER_THRESHOLD = 0.25


@dataclass
class RecalibrationRefusalEntry:
    """A record of a recalibration evaluation that was correctly rejected."""

    rrf_id: str
    pipeline_version: str
    trigger_id: str
    recalibration_refused: bool
    refusal_reason: str
    minimum_batches_required: int
    batches_evaluated: int
    refusal_notes: str
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class RecalibrationRefusalResult:
    rrf_id: str
    pipeline_version: str
    trigger_id: str
    recalibration_refused: bool
    refusal_reason: str
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_recalibration_refusal(
    entry: RecalibrationRefusalEntry,
) -> RecalibrationRefusalResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.rrf_id.startswith(RRF_PREFIX):
        errors.append(
            f"rrf_id must start with '{RRF_PREFIX}', got '{entry.rrf_id}'"
        )

    valid_trigger = any(
        entry.trigger_id.startswith(p) for p in VALID_TRIGGER_PREFIXES
    )
    if not valid_trigger:
        errors.append(
            f"trigger_id must start with one of {sorted(VALID_TRIGGER_PREFIXES)}, "
            f"got '{entry.trigger_id}'"
        )

    if not entry.recalibration_refused:
        errors.append(
            "recalibration_refused must be True — this schema documents refusals, "
            "not approvals (use CalibrationImprovementRecord for approved recalibrations)"
        )

    if entry.refusal_reason not in VALID_REFUSAL_REASONS:
        errors.append(
            f"refusal_reason must be one of {sorted(VALID_REFUSAL_REASONS)}, "
            f"got '{entry.refusal_reason}'"
        )

    if entry.minimum_batches_required < MIN_BATCHES_FLOOR:
        errors.append(
            f"minimum_batches_required must be >= {MIN_BATCHES_FLOOR}, "
            f"got {entry.minimum_batches_required}"
        )

    if entry.batches_evaluated < 0:
        errors.append(
            f"batches_evaluated must be >= 0, got {entry.batches_evaluated}"
        )

    if len(entry.refusal_notes) > REFUSAL_NOTES_MAX_LENGTH:
        errors.append(
            f"refusal_notes exceeds {REFUSAL_NOTES_MAX_LENGTH} characters "
            f"(got {len(entry.refusal_notes)})"
        )

    # Warnings
    if (
        entry.refusal_reason == "insufficient_data"
        and entry.batches_evaluated >= entry.minimum_batches_required
        and not errors
    ):
        warnings.append(
            "refusal_reason is 'insufficient_data' but batches_evaluated "
            f"({entry.batches_evaluated}) meets minimum_batches_required "
            f"({entry.minimum_batches_required}) — consider 'effect_within_noise' "
            "or 'conflicting_signals' as a more precise reason"
        )

    if entry.refusal_reason == "reviewer_override" and not errors:
        warnings.append(
            "refusal_reason is 'reviewer_override' — document the specific reason "
            "in refusal_notes to maintain auditability"
        )

    return RecalibrationRefusalResult(
        rrf_id=entry.rrf_id,
        pipeline_version=entry.pipeline_version,
        trigger_id=entry.trigger_id,
        recalibration_refused=entry.recalibration_refused,
        refusal_reason=entry.refusal_reason,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_recalibration_refusal_dict(d: dict) -> RecalibrationRefusalResult:
    missing = []
    for k in (
        "rrf_id",
        "pipeline_version",
        "trigger_id",
        "recalibration_refused",
        "refusal_reason",
        "minimum_batches_required",
        "batches_evaluated",
        "refusal_notes",
        "reviewer",
    ):
        if k not in d:
            missing.append(k)
    if missing:
        return RecalibrationRefusalResult(
            rrf_id=d.get("rrf_id", ""),
            pipeline_version=d.get("pipeline_version", ""),
            trigger_id=d.get("trigger_id", ""),
            recalibration_refused=d.get("recalibration_refused", False),
            refusal_reason=d.get("refusal_reason", ""),
            passed=False,
            errors=[f"missing required fields: {missing}"],
            warnings=[],
            dry_lab_only=d.get("dry_lab_only", True),
        )
    entry = RecalibrationRefusalEntry(
        rrf_id=d["rrf_id"],
        pipeline_version=d["pipeline_version"],
        trigger_id=d["trigger_id"],
        recalibration_refused=bool(d["recalibration_refused"]),
        refusal_reason=d["refusal_reason"],
        minimum_batches_required=int(d["minimum_batches_required"]),
        batches_evaluated=int(d["batches_evaluated"]),
        refusal_notes=d["refusal_notes"],
        reviewer=d["reviewer"],
        dry_lab_only=bool(d.get("dry_lab_only", True)),
    )
    return validate_recalibration_refusal(entry)

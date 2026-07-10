"""Post-experiment calibration update schema — Phase Q Q3.

PCU- (Post-Experiment Calibration Update): machine-readable record of how
wet-lab experimental results inform a calibration update decision.

Key safety invariants:
- dry_lab_only MUST be False (these are real-experiment-triggered updates)
- n_whr_records must be >= 1 (at least one WHR- record must justify the update)
- update_direction must be one of: "increase_threshold", "decrease_threshold",
  "no_change", "expand_candidate_pool", "restrict_candidate_pool"
- update_magnitude must be in [0.0, 1.0]
- rationale must be non-empty
- limitations must be non-empty
- human_reviewed must be True (calibration updates require human review sign-off)
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field


VALID_UPDATE_DIRECTIONS: frozenset[str] = frozenset({
    "increase_threshold",
    "decrease_threshold",
    "no_change",
    "expand_candidate_pool",
    "restrict_candidate_pool",
})

VALID_CALIBRATION_TRIGGER_TYPES: frozenset[str] = frozenset({
    "hit_rate_above_baseline",
    "hit_rate_below_baseline",
    "novel_family_detected",
    "safety_signal_observed",
    "systematic_prediction_error",
    "insufficient_data",
    "scheduled_review",
})

_PCU_RE = re.compile(r"^PCU-[A-Za-z0-9_-]+$")
MAX_RATIONALE_LEN = 1000
MAX_NOTES_LEN = 500


@dataclass
class PostExperimentCalibrationUpdate:
    """Machine-readable record of a post-experiment calibration update decision.

    human_reviewed must be True — calibration updates require human oversight.
    dry_lab_only must be False — this is triggered by real experimental results.
    """
    pcu_id: str
    update_date: str
    n_whr_records: int
    whr_ids: list[str]
    trigger_type: str
    update_direction: str
    update_magnitude: float
    rationale: str
    limitations: list[str]
    human_reviewed: bool
    dry_lab_only: bool
    reviewer_id: str = ""
    related_ccs_id: str = ""
    notes: str = ""
    prediction_error_before: float = 0.0
    prediction_error_after: float = 0.0


@dataclass
class PCUValidationResult:
    valid: bool
    violations: list[str]
    pcu_id: str | None


def validate_post_experiment_calibration_update(
    record: PostExperimentCalibrationUpdate,
) -> PCUValidationResult:
    """Validate a PostExperimentCalibrationUpdate and return violations."""
    violations: list[str] = []

    # ID format
    if not _PCU_RE.match(record.pcu_id):
        violations.append(
            f"pcu_id '{record.pcu_id}' must match PCU-[A-Za-z0-9_-]+"
        )

    # dry_lab_only must be False
    if record.dry_lab_only is True:
        violations.append(
            "dry_lab_only must be False: "
            "PCU- records are triggered by real experimental results"
        )

    # human_reviewed must be True
    if record.human_reviewed is not True:
        violations.append(
            "human_reviewed must be True: "
            "calibration updates require human review sign-off"
        )

    # n_whr_records must be >= 1
    if record.n_whr_records < 1:
        violations.append(
            f"n_whr_records {record.n_whr_records} must be >= 1: "
            "at least one WHR- record must justify the update"
        )

    # whr_ids must be non-empty and consistent with n_whr_records
    if not record.whr_ids:
        violations.append("whr_ids must be non-empty")
    elif len(record.whr_ids) != record.n_whr_records:
        violations.append(
            f"whr_ids length {len(record.whr_ids)} must equal "
            f"n_whr_records {record.n_whr_records}"
        )

    # update_date must be non-empty
    if not record.update_date:
        violations.append("update_date must be non-empty")

    # trigger_type must be valid
    if record.trigger_type not in VALID_CALIBRATION_TRIGGER_TYPES:
        violations.append(
            f"trigger_type '{record.trigger_type}' is not in "
            f"VALID_CALIBRATION_TRIGGER_TYPES"
        )

    # update_direction must be valid
    if record.update_direction not in VALID_UPDATE_DIRECTIONS:
        violations.append(
            f"update_direction '{record.update_direction}' is not in "
            f"VALID_UPDATE_DIRECTIONS"
        )

    # update_magnitude must be in [0.0, 1.0]
    if not math.isfinite(record.update_magnitude):
        violations.append(
            f"update_magnitude {record.update_magnitude} must be finite"
        )
    elif not (0.0 <= record.update_magnitude <= 1.0):
        violations.append(
            f"update_magnitude {record.update_magnitude} must be in [0.0, 1.0]"
        )

    # rationale must be non-empty and within length limit
    if not record.rationale:
        violations.append("rationale must be non-empty")
    elif len(record.rationale) > MAX_RATIONALE_LEN:
        violations.append(
            f"rationale length {len(record.rationale)} exceeds "
            f"maximum {MAX_RATIONALE_LEN}"
        )

    # limitations must be non-empty
    if not record.limitations:
        violations.append(
            "limitations must be non-empty: "
            "every calibration update has scope and data limitations"
        )

    # prediction_error values must be finite and non-negative
    for field_name, val in [
        ("prediction_error_before", record.prediction_error_before),
        ("prediction_error_after", record.prediction_error_after),
    ]:
        if not math.isfinite(val):
            violations.append(f"{field_name} {val} must be finite")
        elif val < 0.0:
            violations.append(f"{field_name} {val} must be non-negative")

    # notes length cap
    if len(record.notes) > MAX_NOTES_LEN:
        violations.append(
            f"notes length {len(record.notes)} exceeds maximum {MAX_NOTES_LEN}"
        )

    return PCUValidationResult(
        valid=len(violations) == 0,
        violations=violations,
        pcu_id=record.pcu_id if _PCU_RE.match(record.pcu_id) else None,
    )


def build_post_experiment_calibration_update(
    pcu_id: str,
    update_date: str,
    whr_ids: list[str],
    trigger_type: str,
    update_direction: str,
    update_magnitude: float,
    rationale: str,
    limitations: list[str],
    reviewer_id: str = "",
    related_ccs_id: str = "",
    notes: str = "",
    prediction_error_before: float = 0.0,
    prediction_error_after: float = 0.0,
) -> PostExperimentCalibrationUpdate:
    """Build a PCU record with dry_lab_only=False and human_reviewed=True enforced."""
    return PostExperimentCalibrationUpdate(
        pcu_id=pcu_id,
        update_date=update_date,
        n_whr_records=len(whr_ids),
        whr_ids=whr_ids,
        trigger_type=trigger_type,
        update_direction=update_direction,
        update_magnitude=update_magnitude,
        rationale=rationale,
        limitations=limitations,
        human_reviewed=True,
        dry_lab_only=False,
        reviewer_id=reviewer_id,
        related_ccs_id=related_ccs_id,
        notes=notes,
        prediction_error_before=prediction_error_before,
        prediction_error_after=prediction_error_after,
    )


def format_post_experiment_calibration_update(
    record: PostExperimentCalibrationUpdate,
) -> str:
    """Return a human-readable summary of the calibration update record."""
    result = validate_post_experiment_calibration_update(record)
    lines = [
        f"PCU Record: {record.pcu_id}",
        f"  Date: {record.update_date}",
        f"  WHR records: {record.n_whr_records} ({', '.join(record.whr_ids[:3])}{'...' if len(record.whr_ids) > 3 else ''})",
        f"  Trigger: {record.trigger_type}",
        f"  Direction: {record.update_direction} (magnitude: {record.update_magnitude:.3f})",
        f"  human_reviewed: {record.human_reviewed}",
        f"  dry_lab_only: {record.dry_lab_only}",
        f"  Rationale: {record.rationale[:100]}{'...' if len(record.rationale) > 100 else ''}",
        f"  Limitations ({len(record.limitations)}):",
    ]
    for lim in record.limitations:
        lines.append(f"    - {lim}")
    if result.valid:
        lines.append("  Status: VALID")
    else:
        lines.append(f"  Status: INVALID ({len(result.violations)} violation(s))")
        for v in result.violations:
            lines.append(f"    VIOLATION: {v}")
    return "\n".join(lines)

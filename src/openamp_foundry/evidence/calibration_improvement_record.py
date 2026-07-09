from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

ACTION_TAKEN_MAX_LENGTH: int = 500
VALID_ACTION_CATEGORIES: Set[str] = {
    "threshold_adjustment",
    "retraining",
    "feature_removal",
    "feature_addition",
    "data_augmentation",
    "weighting_change",
}
VALID_TRIGGER_PREFIXES: Set[str] = {"CPS-", "DRM-"}
POOR_BRIER_THRESHOLD: float = 0.25


@dataclass
class CalibrationImprovementEntry:
    improvement_id: str
    pipeline_version_before: str
    pipeline_version_after: str
    trigger_ids: List[str]
    action_taken: str
    action_category: str
    brier_score_before: float
    brier_score_after: float
    improvement_confirmed: bool
    reviewer: str
    dry_lab_only: bool = False


@dataclass
class CalibrationImprovementResult:
    improvement_id: str
    pipeline_version_before: str
    pipeline_version_after: str
    brier_score_before: float
    brier_score_after: float
    improvement_confirmed: bool
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = False


def validate_calibration_improvement(
    entry: CalibrationImprovementEntry,
) -> CalibrationImprovementResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.improvement_id.startswith("CIR-"):
        errors.append(
            f"improvement_id must start with 'CIR-', got '{entry.improvement_id}'"
        )

    if entry.pipeline_version_before == entry.pipeline_version_after:
        errors.append(
            "pipeline_version_before and pipeline_version_after must differ"
        )

    if not entry.trigger_ids:
        errors.append("trigger_ids must contain at least 1 entry")
    else:
        bad_triggers = [
            tid for tid in entry.trigger_ids
            if not any(tid.startswith(p) for p in VALID_TRIGGER_PREFIXES)
        ]
        if bad_triggers:
            errors.append(
                f"trigger_ids must start with CPS- or DRM-: {bad_triggers}"
            )

    if len(entry.action_taken) > ACTION_TAKEN_MAX_LENGTH:
        errors.append(
            f"action_taken exceeds {ACTION_TAKEN_MAX_LENGTH} chars "
            f"(got {len(entry.action_taken)})"
        )

    if entry.action_category not in VALID_ACTION_CATEGORIES:
        errors.append(
            f"action_category must be one of {sorted(VALID_ACTION_CATEGORIES)}, "
            f"got '{entry.action_category}'"
        )

    if not (0.0 <= entry.brier_score_before <= 1.0):
        errors.append(
            f"brier_score_before must be in [0.0, 1.0], "
            f"got {entry.brier_score_before}"
        )

    if not (0.0 <= entry.brier_score_after <= 1.0):
        errors.append(
            f"brier_score_after must be in [0.0, 1.0], "
            f"got {entry.brier_score_after}"
        )

    expected_confirmed = entry.brier_score_after < entry.brier_score_before
    if entry.improvement_confirmed != expected_confirmed:
        errors.append(
            f"improvement_confirmed ({entry.improvement_confirmed}) is inconsistent: "
            f"brier_score_after ({entry.brier_score_after}) "
            f"{'<' if expected_confirmed else '>='} "
            f"brier_score_before ({entry.brier_score_before})"
        )

    # Warnings
    if entry.brier_score_after >= POOR_BRIER_THRESHOLD:
        warnings.append(
            f"brier_score_after ({entry.brier_score_after}) >= "
            f"{POOR_BRIER_THRESHOLD} — calibration still poor after action"
        )

    return CalibrationImprovementResult(
        improvement_id=entry.improvement_id,
        pipeline_version_before=entry.pipeline_version_before,
        pipeline_version_after=entry.pipeline_version_after,
        brier_score_before=entry.brier_score_before,
        brier_score_after=entry.brier_score_after,
        improvement_confirmed=entry.improvement_confirmed,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_calibration_improvement_dict(data: dict) -> CalibrationImprovementResult:
    required = [
        "improvement_id", "pipeline_version_before", "pipeline_version_after",
        "trigger_ids", "action_taken", "action_category",
        "brier_score_before", "brier_score_after", "improvement_confirmed", "reviewer",
    ]
    errors: List[str] = []
    for key in required:
        if key not in data:
            errors.append(f"Missing required field: {key}")
    if errors:
        return CalibrationImprovementResult(
            improvement_id=data.get("improvement_id", ""),
            pipeline_version_before=data.get("pipeline_version_before", ""),
            pipeline_version_after=data.get("pipeline_version_after", ""),
            brier_score_before=float(data.get("brier_score_before", 0.0)),
            brier_score_after=float(data.get("brier_score_after", 0.0)),
            improvement_confirmed=bool(data.get("improvement_confirmed", False)),
            passed=False,
            errors=errors,
            warnings=[],
        )
    entry = CalibrationImprovementEntry(
        improvement_id=str(data["improvement_id"]),
        pipeline_version_before=str(data["pipeline_version_before"]),
        pipeline_version_after=str(data["pipeline_version_after"]),
        trigger_ids=list(data["trigger_ids"]),
        action_taken=str(data["action_taken"]),
        action_category=str(data["action_category"]),
        brier_score_before=float(data["brier_score_before"]),
        brier_score_after=float(data["brier_score_after"]),
        improvement_confirmed=bool(data["improvement_confirmed"]),
        reviewer=str(data["reviewer"]),
        dry_lab_only=bool(data.get("dry_lab_only", False)),
    )
    return validate_calibration_improvement(entry)

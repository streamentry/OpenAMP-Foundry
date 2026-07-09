from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

GATE_NOTES_MAX_LENGTH: int = 400
VALID_TRENDS: Set[str] = {"improving", "stable", "degrading"}
PASS_BRIER_THRESHOLD: float = 0.25
WARN_BRIER_THRESHOLD: float = 0.2
MIN_BATCHES: int = 2


@dataclass
class CalibrationReadinessEntry:
    gate_id: str
    pipeline_version: str
    aggregator_id: str
    mean_brier_score: float
    trend: str
    total_batches_evaluated: int
    gate_passed: bool
    failure_reasons: List[str]
    gate_notes: str
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class CalibrationReadinessResult:
    gate_id: str
    pipeline_version: str
    mean_brier_score: float
    trend: str
    gate_passed: bool
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_calibration_readiness(
    entry: CalibrationReadinessEntry,
) -> CalibrationReadinessResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.gate_id.startswith("CRG-"):
        errors.append(
            f"gate_id must start with 'CRG-', got '{entry.gate_id}'"
        )

    if not entry.aggregator_id.startswith("CBA-"):
        errors.append(
            f"aggregator_id must start with 'CBA-', got '{entry.aggregator_id}'"
        )

    if not (0.0 <= entry.mean_brier_score <= 1.0):
        errors.append(
            f"mean_brier_score must be in [0.0, 1.0], got {entry.mean_brier_score}"
        )

    if entry.trend not in VALID_TRENDS:
        errors.append(
            f"trend must be one of {sorted(VALID_TRENDS)}, got '{entry.trend}'"
        )

    if entry.total_batches_evaluated < MIN_BATCHES:
        errors.append(
            f"total_batches_evaluated must be >= {MIN_BATCHES}, "
            f"got {entry.total_batches_evaluated}"
        )

    if len(entry.gate_notes) > GATE_NOTES_MAX_LENGTH:
        errors.append(
            f"gate_notes exceeds {GATE_NOTES_MAX_LENGTH} chars "
            f"(got {len(entry.gate_notes)})"
        )

    expected_passed = len(entry.failure_reasons) == 0
    if entry.gate_passed != expected_passed:
        errors.append(
            f"gate_passed ({entry.gate_passed}) is inconsistent with "
            f"failure_reasons (length={len(entry.failure_reasons)}): "
            f"gate_passed must be True iff failure_reasons is empty"
        )

    if not entry.gate_passed and not entry.failure_reasons:
        errors.append(
            "failure_reasons must be non-empty when gate_passed=False"
        )

    # Warnings
    if entry.trend == "degrading" and entry.gate_passed:
        warnings.append(
            "gate_passed=True despite trend=degrading -- monitor closely"
        )

    if (
        WARN_BRIER_THRESHOLD <= entry.mean_brier_score < PASS_BRIER_THRESHOLD
        and entry.gate_passed
    ):
        warnings.append(
            f"mean_brier_score ({entry.mean_brier_score}) >= {WARN_BRIER_THRESHOLD} "
            "-- marginal pass, consider recalibration"
        )

    return CalibrationReadinessResult(
        gate_id=entry.gate_id,
        pipeline_version=entry.pipeline_version,
        mean_brier_score=entry.mean_brier_score,
        trend=entry.trend,
        gate_passed=entry.gate_passed,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_calibration_readiness_dict(data: dict) -> CalibrationReadinessResult:
    required = [
        "gate_id", "pipeline_version", "aggregator_id", "mean_brier_score",
        "trend", "total_batches_evaluated", "gate_passed", "failure_reasons",
        "gate_notes", "reviewer",
    ]
    errors: List[str] = []
    for key in required:
        if key not in data:
            errors.append(f"Missing required field: {key}")
    if errors:
        return CalibrationReadinessResult(
            gate_id=data.get("gate_id", ""),
            pipeline_version=data.get("pipeline_version", ""),
            mean_brier_score=float(data.get("mean_brier_score", 0.0)),
            trend=data.get("trend", ""),
            gate_passed=bool(data.get("gate_passed", False)),
            passed=False,
            errors=errors,
            warnings=[],
        )
    entry = CalibrationReadinessEntry(
        gate_id=str(data["gate_id"]),
        pipeline_version=str(data["pipeline_version"]),
        aggregator_id=str(data["aggregator_id"]),
        mean_brier_score=float(data["mean_brier_score"]),
        trend=str(data["trend"]),
        total_batches_evaluated=int(data["total_batches_evaluated"]),
        gate_passed=bool(data["gate_passed"]),
        failure_reasons=list(data["failure_reasons"]),
        gate_notes=str(data["gate_notes"]),
        reviewer=str(data["reviewer"]),
        dry_lab_only=bool(data.get("dry_lab_only", True)),
    )
    return validate_calibration_readiness(entry)

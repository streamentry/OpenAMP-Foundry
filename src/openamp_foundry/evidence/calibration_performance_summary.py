from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

MAX_CALIBRATION_NOTES_LENGTH: int = 400
MIN_CANDIDATES_FOR_RELIABLE_ESTIMATE: int = 10
HIGH_FP_RATE_THRESHOLD: float = 0.5
LOW_RECALL_THRESHOLD: float = 0.3
POOR_BRIER_SCORE_THRESHOLD: float = 0.25


@dataclass
class CalibrationPerformanceEntry:
    summary_id: str
    pipeline_version: str
    evaluation_date: str
    batch_ids_evaluated: List[str]
    total_candidates_evaluated: int
    true_positive_count: int
    false_positive_count: int
    true_negative_count: int
    false_negative_count: int
    brier_score: float
    calibration_notes: str
    reviewer: str
    dry_lab_only: bool = False


@dataclass
class CalibrationPerformanceResult:
    summary_id: str
    pipeline_version: str
    total_candidates_evaluated: int
    brier_score: float
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = False


def validate_calibration_performance(
    entry: CalibrationPerformanceEntry,
) -> CalibrationPerformanceResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.summary_id.startswith("CPS-"):
        errors.append(
            f"summary_id must start with 'CPS-', got '{entry.summary_id}'"
        )

    if not entry.batch_ids_evaluated:
        errors.append("batch_ids_evaluated must contain at least 1 batch")

    if entry.total_candidates_evaluated < 1:
        errors.append(
            f"total_candidates_evaluated must be at least 1, "
            f"got {entry.total_candidates_evaluated}"
        )

    for field_name in (
        "true_positive_count",
        "false_positive_count",
        "true_negative_count",
        "false_negative_count",
    ):
        val = getattr(entry, field_name)
        if val < 0:
            errors.append(f"{field_name} must be >= 0, got {val}")

    confusion_sum = (
        entry.true_positive_count
        + entry.false_positive_count
        + entry.true_negative_count
        + entry.false_negative_count
    )
    if (
        entry.total_candidates_evaluated >= 1
        and all(
            getattr(entry, f) >= 0
            for f in (
                "true_positive_count",
                "false_positive_count",
                "true_negative_count",
                "false_negative_count",
            )
        )
        and confusion_sum != entry.total_candidates_evaluated
    ):
        errors.append(
            f"total_candidates_evaluated ({entry.total_candidates_evaluated}) must equal "
            f"TP + FP + TN + FN ({confusion_sum})"
        )

    if not (0.0 <= entry.brier_score <= 1.0):
        errors.append(
            f"brier_score must be between 0.0 and 1.0, got {entry.brier_score}"
        )

    if len(entry.calibration_notes) > MAX_CALIBRATION_NOTES_LENGTH:
        errors.append(
            f"calibration_notes exceeds {MAX_CALIBRATION_NOTES_LENGTH} characters "
            f"(got {len(entry.calibration_notes)})"
        )

    if not entry.reviewer:
        errors.append("reviewer must not be empty")

    if entry.dry_lab_only:
        errors.append(
            "dry_lab_only must be False for calibration performance summaries "
            "(requires real experimental outcome data)"
        )

    if not errors:
        fp = entry.false_positive_count
        tn = entry.true_negative_count
        tp = entry.true_positive_count
        fn = entry.false_negative_count

        if (fp + tn) > 0:
            fp_rate = fp / (fp + tn)
            if fp_rate > HIGH_FP_RATE_THRESHOLD:
                warnings.append(
                    f"false positive rate = {fp_rate:.2f} > {HIGH_FP_RATE_THRESHOLD}; "
                    "pipeline is over-predicting activity"
                )

        if (tp + fn) > 0:
            recall = tp / (tp + fn)
            if recall < LOW_RECALL_THRESHOLD:
                warnings.append(
                    f"recall = {recall:.2f} < {LOW_RECALL_THRESHOLD}; "
                    "pipeline is missing many active candidates"
                )

        if entry.brier_score > POOR_BRIER_SCORE_THRESHOLD:
            warnings.append(
                f"brier_score = {entry.brier_score:.3f} > {POOR_BRIER_SCORE_THRESHOLD}; "
                "probability calibration is poor"
            )

        if entry.total_candidates_evaluated < MIN_CANDIDATES_FOR_RELIABLE_ESTIMATE:
            warnings.append(
                f"only {entry.total_candidates_evaluated} candidates evaluated "
                f"(< {MIN_CANDIDATES_FOR_RELIABLE_ESTIMATE}); "
                "sample too small for reliable calibration assessment"
            )

    passed = len(errors) == 0
    return CalibrationPerformanceResult(
        summary_id=entry.summary_id,
        pipeline_version=entry.pipeline_version,
        total_candidates_evaluated=entry.total_candidates_evaluated,
        brier_score=entry.brier_score,
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=False,
    )


def validate_calibration_performance_dict(d: dict) -> CalibrationPerformanceResult:
    required_fields = [
        "summary_id",
        "pipeline_version",
        "evaluation_date",
        "batch_ids_evaluated",
        "total_candidates_evaluated",
        "true_positive_count",
        "false_positive_count",
        "true_negative_count",
        "false_negative_count",
        "brier_score",
        "calibration_notes",
        "reviewer",
    ]
    missing = [f for f in required_fields if f not in d]
    if missing:
        return CalibrationPerformanceResult(
            summary_id=d.get("summary_id", "UNKNOWN"),
            pipeline_version=d.get("pipeline_version", "UNKNOWN"),
            total_candidates_evaluated=0,
            brier_score=0.0,
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=False,
        )

    entry = CalibrationPerformanceEntry(
        summary_id=d["summary_id"],
        pipeline_version=d["pipeline_version"],
        evaluation_date=d["evaluation_date"],
        batch_ids_evaluated=list(d["batch_ids_evaluated"]),
        total_candidates_evaluated=int(d["total_candidates_evaluated"]),
        true_positive_count=int(d["true_positive_count"]),
        false_positive_count=int(d["false_positive_count"]),
        true_negative_count=int(d["true_negative_count"]),
        false_negative_count=int(d["false_negative_count"]),
        brier_score=float(d["brier_score"]),
        calibration_notes=d["calibration_notes"],
        reviewer=d["reviewer"],
        dry_lab_only=d.get("dry_lab_only", False),
    )
    return validate_calibration_performance(entry)

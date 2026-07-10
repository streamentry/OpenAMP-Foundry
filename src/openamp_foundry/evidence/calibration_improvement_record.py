"""Calibration improvement record schema — Phase O O3.

Documents what changed in the calibration model and by how much.
Records the before/after metric values, improvement direction validation,
and the data source used for recalibration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

CIR_PREFIX = "CIR-"

VALID_METRIC_NAMES = frozenset({
    "auroc",
    "auprc",
    "brier_score",
    "calibration_error",
    "precision_at_k",
    "recall_at_k",
    "f1_at_threshold",
    "expected_calibration_error",
})

HIGHER_IS_BETTER = frozenset({
    "auroc",
    "auprc",
    "precision_at_k",
    "recall_at_k",
    "f1_at_threshold",
})

LOWER_IS_BETTER = frozenset({
    "brier_score",
    "calibration_error",
    "expected_calibration_error",
})

RATIONALE_MAX_LENGTH = 400
NOTES_MAX_LENGTH = 300
MINIMUM_MEANINGFUL_IMPROVEMENT = 0.005
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class CalibrationImprovementRecord:
    cir_id: str
    pipeline_version: str
    calibration_version_before: str
    calibration_version_after: str
    improvement_date: str
    metric_name: str
    metric_value_before: float
    metric_value_after: float
    improvement_confirmed: bool
    improvement_rationale: str
    data_source_id: str
    notes: str = ""


@dataclass
class CalibrationImprovementRecordResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate(record: CalibrationImprovementRecord) -> CalibrationImprovementRecordResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not record.cir_id.startswith(CIR_PREFIX):
        errors.append(f"cir_id must start with '{CIR_PREFIX}', got: {record.cir_id!r}")

    if not record.pipeline_version.strip():
        errors.append("pipeline_version must be a non-empty string")

    if not record.calibration_version_before.strip():
        errors.append("calibration_version_before must be a non-empty string")

    if not record.calibration_version_after.strip():
        errors.append("calibration_version_after must be a non-empty string")

    if (
        record.calibration_version_before.strip()
        and record.calibration_version_after.strip()
        and record.calibration_version_before.strip() == record.calibration_version_after.strip()
    ):
        errors.append(
            "calibration_version_before and calibration_version_after must differ; "
            f"got the same value: {record.calibration_version_before!r}"
        )

    if not _ISO_DATE_RE.match(record.improvement_date):
        errors.append(
            f"improvement_date must be ISO format YYYY-MM-DD, got: {record.improvement_date!r}"
        )

    if record.metric_name not in VALID_METRIC_NAMES:
        errors.append(
            f"metric_name {record.metric_name!r} not in valid set: "
            f"{sorted(VALID_METRIC_NAMES)}"
        )

    if not record.improvement_confirmed:
        errors.append(
            "improvement_confirmed must be True; "
            "do not record a CIR- unless the improvement is confirmed"
        )

    if not record.improvement_rationale.strip():
        errors.append("improvement_rationale must be a non-empty string")
    elif len(record.improvement_rationale) > RATIONALE_MAX_LENGTH:
        errors.append(
            f"improvement_rationale exceeds {RATIONALE_MAX_LENGTH} chars "
            f"(got {len(record.improvement_rationale)})"
        )

    if not record.data_source_id.strip():
        errors.append("data_source_id must be a non-empty string")

    if len(record.notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"notes exceeds {NOTES_MAX_LENGTH} chars (got {len(record.notes)})"
        )

    # Warnings — direction and magnitude checks
    if record.metric_name in HIGHER_IS_BETTER:
        if record.metric_value_after <= record.metric_value_before:
            warnings.append(
                f"metric '{record.metric_name}' is higher-is-better but "
                f"metric_value_after ({record.metric_value_after}) <= "
                f"metric_value_before ({record.metric_value_before}); "
                "verify this is a genuine improvement"
            )
        elif (record.metric_value_after - record.metric_value_before) < MINIMUM_MEANINGFUL_IMPROVEMENT:
            warnings.append(
                f"improvement in '{record.metric_name}' is very small "
                f"({record.metric_value_after - record.metric_value_before:.4f}); "
                "verify the change is scientifically meaningful"
            )
    elif record.metric_name in LOWER_IS_BETTER:
        if record.metric_value_after >= record.metric_value_before:
            warnings.append(
                f"metric '{record.metric_name}' is lower-is-better but "
                f"metric_value_after ({record.metric_value_after}) >= "
                f"metric_value_before ({record.metric_value_before}); "
                "verify this is a genuine improvement"
            )
        elif (record.metric_value_before - record.metric_value_after) < MINIMUM_MEANINGFUL_IMPROVEMENT:
            warnings.append(
                f"improvement in '{record.metric_name}' is very small "
                f"({record.metric_value_before - record.metric_value_after:.4f}); "
                "verify the change is scientifically meaningful"
            )

    if not record.notes.strip():
        warnings.append(
            "notes is empty; consider documenting the calibration change context"
        )

    return CalibrationImprovementRecordResult(
        valid=len(errors) == 0, errors=errors, warnings=warnings
    )


def validate_dict(data: dict) -> CalibrationImprovementRecordResult:
    try:
        record = CalibrationImprovementRecord(
            cir_id=data.get("cir_id", ""),
            pipeline_version=data.get("pipeline_version", ""),
            calibration_version_before=data.get("calibration_version_before", ""),
            calibration_version_after=data.get("calibration_version_after", ""),
            improvement_date=data.get("improvement_date", ""),
            metric_name=data.get("metric_name", ""),
            metric_value_before=float(data.get("metric_value_before", 0.0)),
            metric_value_after=float(data.get("metric_value_after", 0.0)),
            improvement_confirmed=bool(data.get("improvement_confirmed", False)),
            improvement_rationale=data.get("improvement_rationale", ""),
            data_source_id=data.get("data_source_id", ""),
            notes=data.get("notes", ""),
        )
    except Exception as exc:
        return CalibrationImprovementRecordResult(
            valid=False, errors=[f"Construction error: {exc}"]
        )
    return validate(record)

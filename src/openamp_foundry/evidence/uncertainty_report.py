"""Uncertainty quantification report schema (Phase K K5).

Validates prediction intervals and confidence levels for dry-lab
candidate recommendations presented to external reviewers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

VALID_METRIC_NAMES: set[str] = {
    "cytotoxicity_score",
    "hemolysis_fraction",
    "mic",
    "selectivity_index",
    "stability_score",
}

WIDE_INTERVAL_THRESHOLD: float = 10.0

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class UncertaintyReportEntry:
    """One uncertainty quantification report record."""

    report_id: str
    batch_id: str
    candidate_id: str
    pipeline_version: str
    metric_name: str
    point_estimate: float
    lower_bound: float
    upper_bound: float
    confidence_level: float
    calibration_source: str
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class UncertaintyReportResult:
    """Validation result for an UncertaintyReportEntry."""

    report_id: str
    candidate_id: str
    interval_width: float
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_uncertainty_report(entry: UncertaintyReportEntry) -> UncertaintyReportResult:
    """Validate an UncertaintyReportEntry.  Returns an UncertaintyReportResult."""
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.report_id.startswith("UQ-"):
        errors.append("report_id must start with 'UQ-'")

    if not entry.batch_id:
        errors.append("batch_id must not be empty")

    if not entry.candidate_id:
        errors.append("candidate_id must not be empty")

    if not entry.pipeline_version:
        errors.append("pipeline_version must not be empty")

    if entry.metric_name not in VALID_METRIC_NAMES:
        errors.append(
            f"metric_name '{entry.metric_name}' is not valid; "
            f"must be one of {sorted(VALID_METRIC_NAMES)}"
        )

    if entry.lower_bound > entry.point_estimate:
        errors.append(
            f"lower_bound ({entry.lower_bound}) must be <= point_estimate ({entry.point_estimate})"
        )

    if entry.upper_bound < entry.point_estimate:
        errors.append(
            f"upper_bound ({entry.upper_bound}) must be >= point_estimate ({entry.point_estimate})"
        )

    if not (0.0 <= entry.confidence_level <= 1.0):
        errors.append("confidence_level must be between 0.0 and 1.0")

    if not entry.calibration_source:
        errors.append("calibration_source must not be empty")

    if not entry.reviewer:
        errors.append("reviewer must not be empty")

    if entry.dry_lab_only is not True:
        errors.append("dry_lab_only must be True")

    interval_width = entry.upper_bound - entry.lower_bound

    if not errors:
        if interval_width > WIDE_INTERVAL_THRESHOLD:
            warnings.append(
                f"Interval width ({interval_width:.2f}) exceeds threshold "
                f"({WIDE_INTERVAL_THRESHOLD}); low predictive precision."
            )

        if entry.confidence_level < 0.80:
            warnings.append(
                f"confidence_level {entry.confidence_level:.2f} is below 0.80; "
                "results may be unreliable."
            )

        if entry.confidence_level > 0.99:
            warnings.append(
                f"confidence_level {entry.confidence_level:.2f} is above 0.99; "
                "verify calibration method is not overfitting."
            )

    return UncertaintyReportResult(
        report_id=entry.report_id,
        candidate_id=entry.candidate_id,
        interval_width=interval_width,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_uncertainty_report_dict(d: dict) -> UncertaintyReportResult:
    """Validate a dict representation of an UncertaintyReportEntry."""
    required = [
        "report_id",
        "batch_id",
        "candidate_id",
        "pipeline_version",
        "metric_name",
        "point_estimate",
        "lower_bound",
        "upper_bound",
        "confidence_level",
        "calibration_source",
        "reviewer",
    ]
    for key in required:
        if key not in d:
            return UncertaintyReportResult(
                report_id=d.get("report_id", ""),
                candidate_id=d.get("candidate_id", ""),
                interval_width=0.0,
                passed=False,
                errors=[f"missing required field: {key}"],
                warnings=[],
            )

    entry = UncertaintyReportEntry(
        report_id=d["report_id"],
        batch_id=d["batch_id"],
        candidate_id=d["candidate_id"],
        pipeline_version=d["pipeline_version"],
        metric_name=d["metric_name"],
        point_estimate=d["point_estimate"],
        lower_bound=d["lower_bound"],
        upper_bound=d["upper_bound"],
        confidence_level=d["confidence_level"],
        calibration_source=d["calibration_source"],
        reviewer=d["reviewer"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_uncertainty_report(entry)

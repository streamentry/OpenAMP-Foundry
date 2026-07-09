"""Post-experiment calibration intake schema (Phase K K4).

Captures the structured comparison of a pipeline dry-lab prediction
against an actual experimental outcome returned by an external lab.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

VALID_ASSAY_TYPES: set[str] = {
    "cytotoxicity_assay",
    "hemolysis_assay",
    "membrane_disruption_assay",
    "mic_assay",
    "stability_assay",
}

VALID_OUTCOME_VALUES: set[str] = {
    "active",
    "inactive",
    "inconclusive",
    "not_tested",
}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class CalibrationIntakeEntry:
    """One post-experiment calibration intake record."""

    intake_id: str
    batch_id: str
    candidate_id: str
    pipeline_version: str
    assay_type: str
    predicted_outcome: str
    observed_outcome: str
    predicted_confidence: float
    intake_date: str
    reviewer: str
    dry_lab_only: bool = False


@dataclass
class CalibrationIntakeResult:
    """Validation result for a CalibrationIntakeEntry."""

    intake_id: str
    candidate_id: str
    prediction_correct: bool
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = False


def validate_calibration_intake(entry: CalibrationIntakeEntry) -> CalibrationIntakeResult:
    """Validate a CalibrationIntakeEntry.  Returns a CalibrationIntakeResult."""
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.intake_id.startswith("CAL-"):
        errors.append("intake_id must start with 'CAL-'")

    if not entry.batch_id:
        errors.append("batch_id must not be empty")

    if not entry.candidate_id:
        errors.append("candidate_id must not be empty")

    if not entry.pipeline_version:
        errors.append("pipeline_version must not be empty")

    if entry.assay_type not in VALID_ASSAY_TYPES:
        errors.append(
            f"assay_type '{entry.assay_type}' is not valid; "
            f"must be one of {sorted(VALID_ASSAY_TYPES)}"
        )

    if entry.predicted_outcome not in VALID_OUTCOME_VALUES:
        errors.append(
            f"predicted_outcome '{entry.predicted_outcome}' is not valid; "
            f"must be one of {sorted(VALID_OUTCOME_VALUES)}"
        )

    if entry.observed_outcome not in VALID_OUTCOME_VALUES:
        errors.append(
            f"observed_outcome '{entry.observed_outcome}' is not valid; "
            f"must be one of {sorted(VALID_OUTCOME_VALUES)}"
        )

    if not (0.0 <= entry.predicted_confidence <= 1.0):
        errors.append("predicted_confidence must be between 0.0 and 1.0")

    if not _DATE_RE.match(entry.intake_date):
        errors.append("intake_date must be YYYY-MM-DD")

    if not entry.reviewer:
        errors.append("reviewer must not be empty")

    if entry.dry_lab_only is not False:
        errors.append(
            "dry_lab_only must be False for calibration intake records "
            "(they contain real experimental outcomes)"
        )

    prediction_correct = entry.predicted_outcome == entry.observed_outcome

    if (
        not prediction_correct
        and entry.predicted_confidence >= 0.90
        and not errors
    ):
        warnings.append(
            f"High-confidence misprediction: predicted '{entry.predicted_outcome}' "
            f"(confidence {entry.predicted_confidence:.2f}) but observed "
            f"'{entry.observed_outcome}'. Review model calibration."
        )

    if entry.observed_outcome == "inconclusive" and not errors:
        warnings.append(
            "observed_outcome is 'inconclusive'; this result should not be "
            "counted as a calibration signal until resolved."
        )

    return CalibrationIntakeResult(
        intake_id=entry.intake_id,
        candidate_id=entry.candidate_id,
        prediction_correct=prediction_correct,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=False,
    )


def validate_calibration_intake_dict(d: dict) -> CalibrationIntakeResult:
    """Validate a dict representation of a CalibrationIntakeEntry."""
    required = [
        "intake_id",
        "batch_id",
        "candidate_id",
        "pipeline_version",
        "assay_type",
        "predicted_outcome",
        "observed_outcome",
        "predicted_confidence",
        "intake_date",
        "reviewer",
    ]
    for key in required:
        if key not in d:
            return CalibrationIntakeResult(
                intake_id=d.get("intake_id", ""),
                candidate_id=d.get("candidate_id", ""),
                prediction_correct=False,
                passed=False,
                errors=[f"missing required field: {key}"],
                warnings=[],
                dry_lab_only=False,
            )

    entry = CalibrationIntakeEntry(
        intake_id=d["intake_id"],
        batch_id=d["batch_id"],
        candidate_id=d["candidate_id"],
        pipeline_version=d["pipeline_version"],
        assay_type=d["assay_type"],
        predicted_outcome=d["predicted_outcome"],
        observed_outcome=d["observed_outcome"],
        predicted_confidence=d["predicted_confidence"],
        intake_date=d["intake_date"],
        reviewer=d["reviewer"],
        dry_lab_only=d.get("dry_lab_only", False),
    )
    return validate_calibration_intake(entry)

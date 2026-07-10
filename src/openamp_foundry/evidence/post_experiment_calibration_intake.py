"""Post-experiment calibration intake schema — Phase K K4.

Structured result-to-prediction comparison record after wet-lab experiments.
Captures candidates tested, observed activity, hit rate, and whether calibration
update is warranted. Closes the wet-lab→calibration feedback loop.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

PCI_PREFIX = "PCI-"

HIT_RATE_TOLERANCE = 0.01
RATIONALE_MAX_LENGTH = 400
NOTES_MAX_LENGTH = 300
LOW_HIT_RATE_THRESHOLD = 0.3
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class PostExperimentCalibrationIntake:
    pci_id: str
    pipeline_version: str
    batch_id: str
    experiment_date: str
    candidates_tested: int
    candidates_with_results: int
    predicted_active_count: int
    observed_active_count: int
    prediction_hit_rate: float
    calibration_update_warranted: bool
    calibration_update_rationale: str
    data_quality_confirmed: bool
    notes: str = ""


@dataclass
class PostExperimentCalibrationIntakeResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate(record: PostExperimentCalibrationIntake) -> PostExperimentCalibrationIntakeResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not record.pci_id.startswith(PCI_PREFIX):
        errors.append(f"pci_id must start with '{PCI_PREFIX}', got: {record.pci_id!r}")

    if not record.pipeline_version.strip():
        errors.append("pipeline_version must be a non-empty string")

    if not record.batch_id.strip():
        errors.append("batch_id must be a non-empty string")

    if not _ISO_DATE_RE.match(record.experiment_date):
        errors.append(
            f"experiment_date must be ISO format YYYY-MM-DD, got: {record.experiment_date!r}"
        )

    if record.candidates_tested < 1:
        errors.append(
            f"candidates_tested must be at least 1, got: {record.candidates_tested}"
        )

    if record.candidates_with_results < 1:
        errors.append(
            f"candidates_with_results must be at least 1, got: {record.candidates_with_results}"
        )
    elif record.candidates_with_results > record.candidates_tested:
        errors.append(
            f"candidates_with_results ({record.candidates_with_results}) "
            f"cannot exceed candidates_tested ({record.candidates_tested})"
        )

    if record.observed_active_count < 0:
        errors.append(
            f"observed_active_count must be >= 0, got: {record.observed_active_count}"
        )
    elif (
        record.candidates_with_results >= 1
        and record.observed_active_count > record.candidates_with_results
    ):
        errors.append(
            f"observed_active_count ({record.observed_active_count}) "
            f"cannot exceed candidates_with_results ({record.candidates_with_results})"
        )

    if not (0.0 <= record.prediction_hit_rate <= 1.0):
        errors.append(
            f"prediction_hit_rate must be in [0, 1], got: {record.prediction_hit_rate}"
        )
    elif record.candidates_with_results >= 1:
        computed = record.observed_active_count / record.candidates_with_results
        if abs(computed - record.prediction_hit_rate) > HIT_RATE_TOLERANCE:
            errors.append(
                f"prediction_hit_rate ({record.prediction_hit_rate:.4f}) is inconsistent with "
                f"observed_active_count/candidates_with_results "
                f"({record.observed_active_count}/{record.candidates_with_results} = {computed:.4f}); "
                f"tolerance is {HIT_RATE_TOLERANCE}"
            )

    if not record.calibration_update_rationale.strip():
        errors.append("calibration_update_rationale must be a non-empty string")
    elif len(record.calibration_update_rationale) > RATIONALE_MAX_LENGTH:
        errors.append(
            f"calibration_update_rationale exceeds {RATIONALE_MAX_LENGTH} chars "
            f"(got {len(record.calibration_update_rationale)})"
        )

    if not record.data_quality_confirmed:
        errors.append(
            "data_quality_confirmed must be True; "
            "do not record a PCI- unless data quality has been verified"
        )

    if len(record.notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"notes exceeds {NOTES_MAX_LENGTH} chars (got {len(record.notes)})"
        )

    # Warnings
    if record.candidates_with_results < record.candidates_tested:
        missing = record.candidates_tested - record.candidates_with_results
        warnings.append(
            f"{missing} candidate(s) have no results "
            f"({record.candidates_with_results}/{record.candidates_tested} with results); "
            "verify missing results are documented as negative or inconclusive"
        )

    if record.observed_active_count == 0:
        warnings.append(
            "observed_active_count=0; no active candidates found — "
            "verify experimental conditions were correct and result is not a false negative"
        )

    if (
        not record.calibration_update_warranted
        and record.prediction_hit_rate < LOW_HIT_RATE_THRESHOLD
    ):
        warnings.append(
            f"prediction_hit_rate={record.prediction_hit_rate:.2f} is low "
            f"(below {LOW_HIT_RATE_THRESHOLD}) but calibration_update_warranted=False; "
            "consider whether calibration update is needed"
        )

    return PostExperimentCalibrationIntakeResult(
        valid=len(errors) == 0, errors=errors, warnings=warnings
    )


def validate_dict(data: dict) -> PostExperimentCalibrationIntakeResult:
    try:
        record = PostExperimentCalibrationIntake(
            pci_id=data.get("pci_id", ""),
            pipeline_version=data.get("pipeline_version", ""),
            batch_id=data.get("batch_id", ""),
            experiment_date=data.get("experiment_date", ""),
            candidates_tested=int(data.get("candidates_tested", 0)),
            candidates_with_results=int(data.get("candidates_with_results", 0)),
            predicted_active_count=int(data.get("predicted_active_count", 0)),
            observed_active_count=int(data.get("observed_active_count", 0)),
            prediction_hit_rate=float(data.get("prediction_hit_rate", 0.0)),
            calibration_update_warranted=bool(data.get("calibration_update_warranted", False)),
            calibration_update_rationale=data.get("calibration_update_rationale", ""),
            data_quality_confirmed=bool(data.get("data_quality_confirmed", False)),
            notes=data.get("notes", ""),
        )
    except Exception as exc:
        return PostExperimentCalibrationIntakeResult(
            valid=False, errors=[f"Construction error: {exc}"]
        )
    return validate(record)

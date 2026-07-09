from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

DRIFT_NOTES_MAX_LENGTH: int = 400
MEAN_SHIFT_TOLERANCE: float = 0.001
SIGNIFICANT_DRIFT_THRESHOLD: float = 0.1
MIN_POPULATION_FOR_RELIABLE_DRIFT: int = 10
VARIANCE_EXPLOSION_RATIO: float = 2.0


@dataclass
class PredictionDriftEntry:
    monitor_id: str
    pipeline_version: str
    reference_batch_id: str
    evaluation_batch_id: str
    reference_mean_score: float
    reference_std_score: float
    evaluation_mean_score: float
    evaluation_std_score: float
    mean_shift_magnitude: float
    population_size_reference: int
    population_size_evaluation: int
    drift_flag: bool
    drift_notes: str
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class PredictionDriftResult:
    monitor_id: str
    pipeline_version: str
    mean_shift_magnitude: float
    drift_flag: bool
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_prediction_drift(
    entry: PredictionDriftEntry,
) -> PredictionDriftResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.monitor_id.startswith("DRM-"):
        errors.append(
            f"monitor_id must start with 'DRM-', got '{entry.monitor_id}'"
        )

    if entry.reference_batch_id == entry.evaluation_batch_id:
        errors.append(
            "reference_batch_id and evaluation_batch_id must differ"
        )

    if not (0.0 <= entry.reference_mean_score <= 1.0):
        errors.append(
            f"reference_mean_score must be in [0.0, 1.0], "
            f"got {entry.reference_mean_score}"
        )

    if not (0.0 <= entry.evaluation_mean_score <= 1.0):
        errors.append(
            f"evaluation_mean_score must be in [0.0, 1.0], "
            f"got {entry.evaluation_mean_score}"
        )

    if entry.reference_std_score < 0.0:
        errors.append(
            f"reference_std_score must be >= 0.0, "
            f"got {entry.reference_std_score}"
        )

    if entry.evaluation_std_score < 0.0:
        errors.append(
            f"evaluation_std_score must be >= 0.0, "
            f"got {entry.evaluation_std_score}"
        )

    expected_shift = abs(
        entry.evaluation_mean_score - entry.reference_mean_score
    )
    if abs(entry.mean_shift_magnitude - expected_shift) > MEAN_SHIFT_TOLERANCE:
        errors.append(
            f"mean_shift_magnitude ({entry.mean_shift_magnitude:.4f}) does not "
            f"match |evaluation_mean - reference_mean| "
            f"({expected_shift:.4f}) within tolerance {MEAN_SHIFT_TOLERANCE}"
        )

    if entry.population_size_reference < 1:
        errors.append(
            f"population_size_reference must be >= 1, "
            f"got {entry.population_size_reference}"
        )

    if entry.population_size_evaluation < 1:
        errors.append(
            f"population_size_evaluation must be >= 1, "
            f"got {entry.population_size_evaluation}"
        )

    if len(entry.drift_notes) > DRIFT_NOTES_MAX_LENGTH:
        errors.append(
            f"drift_notes exceeds {DRIFT_NOTES_MAX_LENGTH} chars "
            f"(got {len(entry.drift_notes)})"
        )

    if entry.drift_flag and not entry.drift_notes.strip():
        errors.append(
            "drift_notes must be non-empty when drift_flag=True"
        )

    if (
        entry.mean_shift_magnitude >= SIGNIFICANT_DRIFT_THRESHOLD
        and not entry.drift_flag
    ):
        warnings.append(
            f"mean_shift_magnitude ({entry.mean_shift_magnitude:.3f}) >= "
            f"{SIGNIFICANT_DRIFT_THRESHOLD} but drift_flag=False -- "
            "possible unreported drift"
        )

    if entry.population_size_reference < MIN_POPULATION_FOR_RELIABLE_DRIFT:
        warnings.append(
            f"population_size_reference ({entry.population_size_reference}) < "
            f"{MIN_POPULATION_FOR_RELIABLE_DRIFT} -- drift estimate unreliable"
        )

    if entry.population_size_evaluation < MIN_POPULATION_FOR_RELIABLE_DRIFT:
        warnings.append(
            f"population_size_evaluation ({entry.population_size_evaluation}) < "
            f"{MIN_POPULATION_FOR_RELIABLE_DRIFT} -- drift estimate unreliable"
        )

    if (
        entry.reference_std_score > 0.0
        and entry.evaluation_std_score
        > VARIANCE_EXPLOSION_RATIO * entry.reference_std_score
    ):
        warnings.append(
            f"evaluation_std_score ({entry.evaluation_std_score:.3f}) > "
            f"{VARIANCE_EXPLOSION_RATIO}x reference_std_score "
            f"({entry.reference_std_score:.3f}) -- variance explosion detected"
        )

    return PredictionDriftResult(
        monitor_id=entry.monitor_id,
        pipeline_version=entry.pipeline_version,
        mean_shift_magnitude=entry.mean_shift_magnitude,
        drift_flag=entry.drift_flag,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_prediction_drift_dict(data: dict) -> PredictionDriftResult:
    required = [
        "monitor_id", "pipeline_version", "reference_batch_id",
        "evaluation_batch_id", "reference_mean_score", "reference_std_score",
        "evaluation_mean_score", "evaluation_std_score",
        "mean_shift_magnitude", "population_size_reference",
        "population_size_evaluation", "drift_flag", "drift_notes", "reviewer",
    ]
    errors: List[str] = []
    for key in required:
        if key not in data:
            errors.append(f"Missing required field: {key}")
    if errors:
        return PredictionDriftResult(
            monitor_id=data.get("monitor_id", ""),
            pipeline_version=data.get("pipeline_version", ""),
            mean_shift_magnitude=float(data.get("mean_shift_magnitude", 0.0)),
            drift_flag=bool(data.get("drift_flag", False)),
            passed=False,
            errors=errors,
            warnings=[],
        )
    entry = PredictionDriftEntry(
        monitor_id=str(data["monitor_id"]),
        pipeline_version=str(data["pipeline_version"]),
        reference_batch_id=str(data["reference_batch_id"]),
        evaluation_batch_id=str(data["evaluation_batch_id"]),
        reference_mean_score=float(data["reference_mean_score"]),
        reference_std_score=float(data["reference_std_score"]),
        evaluation_mean_score=float(data["evaluation_mean_score"]),
        evaluation_std_score=float(data["evaluation_std_score"]),
        mean_shift_magnitude=float(data["mean_shift_magnitude"]),
        population_size_reference=int(data["population_size_reference"]),
        population_size_evaluation=int(data["population_size_evaluation"]),
        drift_flag=bool(data["drift_flag"]),
        drift_notes=str(data["drift_notes"]),
        reviewer=str(data["reviewer"]),
        dry_lab_only=bool(data.get("dry_lab_only", True)),
    )
    return validate_prediction_drift(entry)

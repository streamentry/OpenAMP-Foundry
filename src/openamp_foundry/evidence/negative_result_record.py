from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

VALID_FAILURE_CATEGORIES: set[str] = {
    "assay_quality_failure",
    "below_activity_threshold",
    "excessive_toxicity",
    "model_overprediction",
    "pipeline_error",
    "stability_failure",
}

VALID_ASSAY_TYPES: set[str] = {
    "cytotoxicity_assay",
    "hemolysis_assay",
    "membrane_disruption_assay",
    "mic_assay",
    "stability_assay",
}

MAX_FAILURE_DESCRIPTION_LENGTH: int = 500
MAX_HYPOTHESIS_IMPACT_LENGTH: int = 300
LARGE_FAILURE_SET_THRESHOLD: int = 10
RECALIBRATION_HINT: str = "calibrat"


@dataclass
class NegativeResultEntry:
    record_id: str
    batch_id: str
    pipeline_version: str
    record_date: str
    failure_category: str
    failure_description: str
    candidate_ids: List[str]
    assay_type: str
    expected_outcome: str
    observed_outcome: str
    hypothesis_impact: str
    will_be_reported: bool
    recorded_by: str
    dry_lab_only: bool = True


@dataclass
class NegativeResultResult:
    record_id: str
    batch_id: str
    failure_category: str
    candidate_count: int
    will_be_reported: bool
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_negative_result(entry: NegativeResultEntry) -> NegativeResultResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.record_id.startswith("NRR-"):
        errors.append(
            f"record_id must start with 'NRR-', got '{entry.record_id}'"
        )

    if entry.failure_category not in VALID_FAILURE_CATEGORIES:
        errors.append(
            f"failure_category '{entry.failure_category}' is not valid; "
            f"must be one of {sorted(VALID_FAILURE_CATEGORIES)}"
        )

    if not entry.failure_description:
        errors.append("failure_description must not be empty")
    elif len(entry.failure_description) > MAX_FAILURE_DESCRIPTION_LENGTH:
        errors.append(
            f"failure_description exceeds {MAX_FAILURE_DESCRIPTION_LENGTH} characters "
            f"(got {len(entry.failure_description)})"
        )

    if not entry.candidate_ids:
        errors.append("candidate_ids must contain at least 1 candidate")

    if entry.assay_type not in VALID_ASSAY_TYPES:
        errors.append(
            f"assay_type '{entry.assay_type}' is not valid; "
            f"must be one of {sorted(VALID_ASSAY_TYPES)}"
        )

    if not entry.expected_outcome:
        errors.append("expected_outcome must not be empty")

    if not entry.observed_outcome:
        errors.append("observed_outcome must not be empty")

    if not entry.hypothesis_impact:
        errors.append("hypothesis_impact must not be empty")
    elif len(entry.hypothesis_impact) > MAX_HYPOTHESIS_IMPACT_LENGTH:
        errors.append(
            f"hypothesis_impact exceeds {MAX_HYPOTHESIS_IMPACT_LENGTH} characters "
            f"(got {len(entry.hypothesis_impact)})"
        )

    if not entry.recorded_by:
        errors.append("recorded_by must not be empty")

    if not errors:
        if not entry.will_be_reported:
            warnings.append(
                "will_be_reported=False; suppressing negative results contributes "
                "to publication bias — ensure this omission is documented and justified"
            )

        if len(entry.candidate_ids) > LARGE_FAILURE_SET_THRESHOLD:
            warnings.append(
                f"{len(entry.candidate_ids)} candidates failed "
                f"(> {LARGE_FAILURE_SET_THRESHOLD}); this may indicate a systematic "
                "pipeline issue; consider recalibration"
            )

        if (
            entry.failure_category == "model_overprediction"
            and RECALIBRATION_HINT not in entry.hypothesis_impact.lower()
        ):
            warnings.append(
                "failure_category='model_overprediction' but hypothesis_impact does "
                "not mention recalibration; model overprediction should trigger a "
                "calibration review"
            )

    passed = len(errors) == 0
    return NegativeResultResult(
        record_id=entry.record_id,
        batch_id=entry.batch_id,
        failure_category=entry.failure_category,
        candidate_count=len(entry.candidate_ids),
        will_be_reported=entry.will_be_reported,
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_negative_result_dict(d: dict) -> NegativeResultResult:
    required_fields = [
        "record_id",
        "batch_id",
        "pipeline_version",
        "record_date",
        "failure_category",
        "failure_description",
        "candidate_ids",
        "assay_type",
        "expected_outcome",
        "observed_outcome",
        "hypothesis_impact",
        "will_be_reported",
        "recorded_by",
    ]
    missing = [f for f in required_fields if f not in d]
    if missing:
        return NegativeResultResult(
            record_id=d.get("record_id", "UNKNOWN"),
            batch_id=d.get("batch_id", "UNKNOWN"),
            failure_category=d.get("failure_category", "UNKNOWN"),
            candidate_count=0,
            will_be_reported=False,
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=d.get("dry_lab_only", True),
        )

    entry = NegativeResultEntry(
        record_id=d["record_id"],
        batch_id=d["batch_id"],
        pipeline_version=d["pipeline_version"],
        record_date=d["record_date"],
        failure_category=d["failure_category"],
        failure_description=d["failure_description"],
        candidate_ids=list(d["candidate_ids"]),
        assay_type=d["assay_type"],
        expected_outcome=d["expected_outcome"],
        observed_outcome=d["observed_outcome"],
        hypothesis_impact=d["hypothesis_impact"],
        will_be_reported=bool(d["will_be_reported"]),
        recorded_by=d["recorded_by"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_negative_result(entry)

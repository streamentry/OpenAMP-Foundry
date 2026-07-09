from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List

VALID_OUTCOME_VERDICTS: set[str] = {
    "confirmed",
    "inconclusive",
    "partially_confirmed",
    "refuted",
}

MAX_INTERPRETATION_LENGTH: int = 500
MIN_INTERPRETATION_LENGTH: int = 50
REGISTRATION_ID_PREFIX: str = "PRE-"
OUTCOME_ID_PREFIX: str = "HOR-"


@dataclass
class HypothesisOutcomeEntry:
    outcome_id: str
    registration_id: str
    batch_id: str
    pipeline_version: str
    outcome_date: str
    outcome_verdict: str
    observed_metric_value: float
    success_threshold_met: bool
    interpretation: str
    deviation_from_plan: str
    recorded_by: str
    dry_lab_only: bool = True


@dataclass
class HypothesisOutcomeResult:
    outcome_id: str
    registration_id: str
    outcome_verdict: str
    success_threshold_met: bool
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_hypothesis_outcome(entry: HypothesisOutcomeEntry) -> HypothesisOutcomeResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.outcome_id.startswith(OUTCOME_ID_PREFIX):
        errors.append(
            f"outcome_id must start with '{OUTCOME_ID_PREFIX}', got '{entry.outcome_id}'"
        )

    if not entry.registration_id.startswith(REGISTRATION_ID_PREFIX):
        errors.append(
            f"registration_id must start with '{REGISTRATION_ID_PREFIX}', "
            f"got '{entry.registration_id}'"
        )

    if entry.outcome_verdict not in VALID_OUTCOME_VERDICTS:
        errors.append(
            f"outcome_verdict '{entry.outcome_verdict}' is not valid; "
            f"must be one of {sorted(VALID_OUTCOME_VERDICTS)}"
        )

    if math.isnan(entry.observed_metric_value) or math.isinf(entry.observed_metric_value):
        errors.append(
            f"observed_metric_value must be finite, got {entry.observed_metric_value}"
        )

    if not entry.interpretation:
        errors.append("interpretation must not be empty")
    elif len(entry.interpretation) > MAX_INTERPRETATION_LENGTH:
        errors.append(
            f"interpretation exceeds {MAX_INTERPRETATION_LENGTH} characters "
            f"(got {len(entry.interpretation)})"
        )

    if not entry.recorded_by:
        errors.append("recorded_by must not be empty")

    if not errors:
        if entry.success_threshold_met and entry.outcome_verdict == "refuted":
            warnings.append(
                "success_threshold_met=True but outcome_verdict='refuted'; "
                "these are inconsistent — verify threshold logic and verdict"
            )

        if not entry.success_threshold_met and entry.outcome_verdict == "confirmed":
            warnings.append(
                "success_threshold_met=False but outcome_verdict='confirmed'; "
                "these are inconsistent — verify threshold logic and verdict"
            )

        if entry.outcome_verdict == "inconclusive" and not entry.deviation_from_plan:
            warnings.append(
                "outcome_verdict='inconclusive' but deviation_from_plan is empty; "
                "document what went wrong or deviated so the inconclusive result is interpretable"
            )

        if entry.interpretation and len(entry.interpretation) < MIN_INTERPRETATION_LENGTH:
            warnings.append(
                f"interpretation is short ({len(entry.interpretation)} chars < "
                f"{MIN_INTERPRETATION_LENGTH}); may be underspecified"
            )

    passed = len(errors) == 0
    return HypothesisOutcomeResult(
        outcome_id=entry.outcome_id,
        registration_id=entry.registration_id,
        outcome_verdict=entry.outcome_verdict,
        success_threshold_met=entry.success_threshold_met,
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_hypothesis_outcome_dict(d: dict) -> HypothesisOutcomeResult:
    required_fields = [
        "outcome_id",
        "registration_id",
        "batch_id",
        "pipeline_version",
        "outcome_date",
        "outcome_verdict",
        "observed_metric_value",
        "success_threshold_met",
        "interpretation",
        "deviation_from_plan",
        "recorded_by",
    ]
    missing = [f for f in required_fields if f not in d]
    if missing:
        return HypothesisOutcomeResult(
            outcome_id=d.get("outcome_id", "UNKNOWN"),
            registration_id=d.get("registration_id", "UNKNOWN"),
            outcome_verdict=d.get("outcome_verdict", "UNKNOWN"),
            success_threshold_met=False,
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=d.get("dry_lab_only", True),
        )

    entry = HypothesisOutcomeEntry(
        outcome_id=d["outcome_id"],
        registration_id=d["registration_id"],
        batch_id=d["batch_id"],
        pipeline_version=d["pipeline_version"],
        outcome_date=d["outcome_date"],
        outcome_verdict=d["outcome_verdict"],
        observed_metric_value=float(d["observed_metric_value"]),
        success_threshold_met=bool(d["success_threshold_met"]),
        interpretation=d["interpretation"],
        deviation_from_plan=d["deviation_from_plan"],
        recorded_by=d["recorded_by"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_hypothesis_outcome(entry)

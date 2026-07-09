from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List

VALID_PRIMARY_OUTCOME_METRICS: set[str] = {
    "fold_change_mic",
    "hemolysis_fraction",
    "hit_rate",
    "mic_value",
    "selectivity_index",
    "survival_improvement",
}

VALID_ASSAY_TYPES: set[str] = {
    "cytotoxicity_assay",
    "hemolysis_assay",
    "membrane_disruption_assay",
    "mic_assay",
    "stability_assay",
}

MAX_HYPOTHESIS_LENGTH: int = 500
MIN_HYPOTHESIS_LENGTH: int = 50
MAX_STATISTICAL_TEST_LENGTH: int = 200
LARGE_CANDIDATE_SET_THRESHOLD: int = 20
PLACEHOLDER_TEST_TOKENS: set[str] = {"tbd", "n/a", "na", "none"}
RANDOM_BASELINE_HINT: str = "random"


@dataclass
class PreRegistrationEntry:
    registration_id: str
    batch_id: str
    pipeline_version: str
    registration_date: str
    primary_hypothesis: str
    primary_outcome_metric: str
    success_threshold: float
    baseline_comparators: List[str]
    candidate_ids: List[str]
    assay_type: str
    statistical_test: str
    registered_by: str
    dry_lab_only: bool = True


@dataclass
class PreRegistrationResult:
    registration_id: str
    batch_id: str
    primary_outcome_metric: str
    candidate_count: int
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_pre_registration(entry: PreRegistrationEntry) -> PreRegistrationResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.registration_id.startswith("PRE-"):
        errors.append(
            f"registration_id must start with 'PRE-', got '{entry.registration_id}'"
        )

    if not entry.primary_hypothesis:
        errors.append("primary_hypothesis must not be empty")
    elif len(entry.primary_hypothesis) > MAX_HYPOTHESIS_LENGTH:
        errors.append(
            f"primary_hypothesis exceeds {MAX_HYPOTHESIS_LENGTH} characters "
            f"(got {len(entry.primary_hypothesis)})"
        )

    if entry.primary_outcome_metric not in VALID_PRIMARY_OUTCOME_METRICS:
        errors.append(
            f"primary_outcome_metric '{entry.primary_outcome_metric}' is not valid; "
            f"must be one of {sorted(VALID_PRIMARY_OUTCOME_METRICS)}"
        )

    if math.isnan(entry.success_threshold) or math.isinf(entry.success_threshold):
        errors.append(
            f"success_threshold must be a finite number, "
            f"got {entry.success_threshold}"
        )

    if not entry.baseline_comparators:
        errors.append(
            "baseline_comparators must contain at least 1 baseline comparator"
        )

    if not entry.candidate_ids:
        errors.append("candidate_ids must contain at least 1 candidate")

    if entry.assay_type not in VALID_ASSAY_TYPES:
        errors.append(
            f"assay_type '{entry.assay_type}' is not valid; "
            f"must be one of {sorted(VALID_ASSAY_TYPES)}"
        )

    if not entry.statistical_test:
        errors.append("statistical_test must not be empty")
    elif len(entry.statistical_test) > MAX_STATISTICAL_TEST_LENGTH:
        errors.append(
            f"statistical_test exceeds {MAX_STATISTICAL_TEST_LENGTH} characters "
            f"(got {len(entry.statistical_test)})"
        )

    if not entry.registered_by:
        errors.append("registered_by must not be empty")

    if not entry.dry_lab_only:
        errors.append(
            "dry_lab_only must be True for pre-registration forms "
            "(computational pre-commitment only)"
        )

    if not errors:
        has_random = any(
            RANDOM_BASELINE_HINT in c.lower() for c in entry.baseline_comparators
        )
        if not has_random:
            warnings.append(
                "no random selection baseline found in baseline_comparators; "
                "a random baseline is the cheapest disconfirming test and should always be included"
            )

        if len(entry.candidate_ids) > LARGE_CANDIDATE_SET_THRESHOLD:
            warnings.append(
                f"{len(entry.candidate_ids)} candidates exceeds "
                f"{LARGE_CANDIDATE_SET_THRESHOLD}; "
                "large sets increase multiple-comparisons burden; consider splitting"
            )

        if entry.primary_hypothesis and len(entry.primary_hypothesis) < MIN_HYPOTHESIS_LENGTH:
            warnings.append(
                f"primary_hypothesis is short ({len(entry.primary_hypothesis)} chars < "
                f"{MIN_HYPOTHESIS_LENGTH}); hypothesis may be underspecified"
            )

        if entry.statistical_test and entry.statistical_test.strip().lower() in PLACEHOLDER_TEST_TOKENS:
            warnings.append(
                f"statistical_test is a placeholder ('{entry.statistical_test}'); "
                "name the specific statistical test before experiments begin"
            )

    passed = len(errors) == 0
    return PreRegistrationResult(
        registration_id=entry.registration_id,
        batch_id=entry.batch_id,
        primary_outcome_metric=entry.primary_outcome_metric,
        candidate_count=len(entry.candidate_ids),
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_pre_registration_dict(d: dict) -> PreRegistrationResult:
    required_fields = [
        "registration_id",
        "batch_id",
        "pipeline_version",
        "registration_date",
        "primary_hypothesis",
        "primary_outcome_metric",
        "success_threshold",
        "baseline_comparators",
        "candidate_ids",
        "assay_type",
        "statistical_test",
        "registered_by",
    ]
    missing = [f for f in required_fields if f not in d]
    if missing:
        return PreRegistrationResult(
            registration_id=d.get("registration_id", "UNKNOWN"),
            batch_id=d.get("batch_id", "UNKNOWN"),
            primary_outcome_metric=d.get("primary_outcome_metric", "UNKNOWN"),
            candidate_count=0,
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=True,
        )

    entry = PreRegistrationEntry(
        registration_id=d["registration_id"],
        batch_id=d["batch_id"],
        pipeline_version=d["pipeline_version"],
        registration_date=d["registration_date"],
        primary_hypothesis=d["primary_hypothesis"],
        primary_outcome_metric=d["primary_outcome_metric"],
        success_threshold=float(d["success_threshold"]),
        baseline_comparators=list(d["baseline_comparators"]),
        candidate_ids=list(d["candidate_ids"]),
        assay_type=d["assay_type"],
        statistical_test=d["statistical_test"],
        registered_by=d["registered_by"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_pre_registration(entry)

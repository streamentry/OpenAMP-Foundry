"""Pilot package completeness checker (Phase K K3).

Validates that all required artifacts are present before an experiment
batch is submitted to an external collaborating lab.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

MINIMUM_REQUIRED_ARTIFACTS: int = 3
READINESS_SCORE_THRESHOLD: float = 0.80

MANDATORY_ARTIFACT_TYPES: set[str] = {
    "batch_priority",
    "evidence_certificate",
    "selection_rationale",
}

VALID_ARTIFACT_TYPES: set[str] = {
    "batch_priority",
    "benchmark_card",
    "candidate_manifest",
    "evidence_certificate",
    "model_card",
    "safety_assessment",
    "selection_rationale",
    "uncertainty_report",
}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class PilotPackageEntry:
    """One pilot package completeness record."""

    package_id: str
    batch_id: str
    submission_date: str
    pipeline_version: str
    included_artifacts: List[str]
    missing_artifacts: List[str]
    reviewer: str
    approver: str
    completeness_score: float
    ready_to_submit: bool
    dry_lab_only: bool = True


@dataclass
class PilotPackageResult:
    """Validation result for a PilotPackageEntry."""

    package_id: str
    batch_id: str
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_pilot_package(entry: PilotPackageEntry) -> PilotPackageResult:
    """Validate a PilotPackageEntry.  Returns a PilotPackageResult."""
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.package_id.startswith("PKG-"):
        errors.append("package_id must start with 'PKG-'")

    if not entry.batch_id:
        errors.append("batch_id must not be empty")

    if not _DATE_RE.match(entry.submission_date):
        errors.append("submission_date must be YYYY-MM-DD")

    if not entry.pipeline_version:
        errors.append("pipeline_version must not be empty")

    if len(entry.included_artifacts) < MINIMUM_REQUIRED_ARTIFACTS:
        errors.append(
            f"included_artifacts must have at least {MINIMUM_REQUIRED_ARTIFACTS} entries"
        )

    missing_mandatory = MANDATORY_ARTIFACT_TYPES - set(entry.included_artifacts)
    if missing_mandatory:
        errors.append(
            f"included_artifacts is missing mandatory types: {sorted(missing_mandatory)}"
        )

    if not entry.reviewer:
        errors.append("reviewer must not be empty")

    if not entry.approver:
        errors.append("approver must not be empty")

    if not (0.0 <= entry.completeness_score <= 1.0):
        errors.append("completeness_score must be between 0.0 and 1.0")

    if entry.ready_to_submit and entry.completeness_score < READINESS_SCORE_THRESHOLD:
        errors.append(
            f"ready_to_submit cannot be True when completeness_score "
            f"({entry.completeness_score:.2f}) < {READINESS_SCORE_THRESHOLD}"
        )

    if entry.dry_lab_only is not True:
        errors.append("dry_lab_only must be True")

    if entry.missing_artifacts:
        warnings.append(
            f"Package has {len(entry.missing_artifacts)} missing artifact(s): "
            f"{entry.missing_artifacts}"
        )

    if 0.0 <= entry.completeness_score < 0.90:
        warnings.append(
            f"completeness_score {entry.completeness_score:.2f} is below 0.90; "
            "consider completing optional artifacts before submission"
        )

    if entry.reviewer and entry.approver and entry.reviewer == entry.approver:
        warnings.append(
            "reviewer and approver are the same person; consider independent approval"
        )

    return PilotPackageResult(
        package_id=entry.package_id,
        batch_id=entry.batch_id,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_pilot_package_dict(d: dict) -> PilotPackageResult:
    """Validate a dict representation of a PilotPackageEntry."""
    required = [
        "package_id",
        "batch_id",
        "submission_date",
        "pipeline_version",
        "included_artifacts",
        "missing_artifacts",
        "reviewer",
        "approver",
        "completeness_score",
        "ready_to_submit",
    ]
    for key in required:
        if key not in d:
            return PilotPackageResult(
                package_id=d.get("package_id", ""),
                batch_id=d.get("batch_id", ""),
                passed=False,
                errors=[f"missing required field: {key}"],
                warnings=[],
            )

    entry = PilotPackageEntry(
        package_id=d["package_id"],
        batch_id=d["batch_id"],
        submission_date=d["submission_date"],
        pipeline_version=d["pipeline_version"],
        included_artifacts=d["included_artifacts"],
        missing_artifacts=d["missing_artifacts"],
        reviewer=d["reviewer"],
        approver=d["approver"],
        completeness_score=d["completeness_score"],
        ready_to_submit=d["ready_to_submit"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_pilot_package(entry)

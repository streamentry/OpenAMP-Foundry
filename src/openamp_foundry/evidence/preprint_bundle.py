"""Preprint evidence bundle schema (Phase L L1).

Validates the structured evidence bundle that accompanies a scientific
preprint describing computationally-nominated AMP candidates.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

MINIMUM_ARTIFACTS: int = 3
VALID_EVIDENCE_LEVELS: set[int] = {1, 2, 3, 4, 5, 6}
MAX_TITLE_LENGTH: int = 300
RECOMMENDED_ARTIFACT_COUNT: int = 5

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class PreprintBundleEntry:
    """One preprint evidence bundle record."""

    bundle_id: str
    batch_id: str
    pipeline_version: str
    submission_date: str
    title: str
    artifact_ids: List[str]
    evidence_level: int
    preprint_doi: str
    contact_email: str
    release_approved: bool
    dry_lab_only: bool = True


@dataclass
class PreprintBundleResult:
    """Validation result for a PreprintBundleEntry."""

    bundle_id: str
    batch_id: str
    artifact_count: int
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_preprint_bundle(entry: PreprintBundleEntry) -> PreprintBundleResult:
    """Validate a PreprintBundleEntry.  Returns a PreprintBundleResult."""
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.bundle_id.startswith("BND-"):
        errors.append("bundle_id must start with 'BND-'")

    if not entry.batch_id:
        errors.append("batch_id must not be empty")

    if not entry.pipeline_version:
        errors.append("pipeline_version must not be empty")

    if not _DATE_RE.match(entry.submission_date):
        errors.append("submission_date must be YYYY-MM-DD")

    if not entry.title:
        errors.append("title must not be empty")
    elif len(entry.title) > MAX_TITLE_LENGTH:
        errors.append(
            f"title exceeds {MAX_TITLE_LENGTH} characters ({len(entry.title)} chars)"
        )

    if len(entry.artifact_ids) < MINIMUM_ARTIFACTS:
        errors.append(
            f"artifact_ids must have at least {MINIMUM_ARTIFACTS} entries"
        )

    if entry.evidence_level not in VALID_EVIDENCE_LEVELS:
        errors.append(
            f"evidence_level {entry.evidence_level} is not valid; "
            f"must be one of {sorted(VALID_EVIDENCE_LEVELS)}"
        )

    if not entry.contact_email:
        errors.append("contact_email must not be empty")

    if not entry.release_approved:
        errors.append("release_approved must be True for a valid preprint bundle")

    if entry.dry_lab_only is not True:
        errors.append("dry_lab_only must be True")

    if not errors:
        if entry.evidence_level <= 2:
            warnings.append(
                f"evidence_level {entry.evidence_level} is low (≤2); "
                "reviewers should apply extra scrutiny to computational claims."
            )

        if not entry.preprint_doi:
            warnings.append(
                "preprint_doi is empty; update this field once the DOI is assigned."
            )

        if len(entry.artifact_ids) < RECOMMENDED_ARTIFACT_COUNT:
            warnings.append(
                f"Only {len(entry.artifact_ids)} artifact(s) referenced; "
                f"consider adding uncertainty reports and calibration records "
                f"(recommended: {RECOMMENDED_ARTIFACT_COUNT}+)."
            )

    return PreprintBundleResult(
        bundle_id=entry.bundle_id,
        batch_id=entry.batch_id,
        artifact_count=len(entry.artifact_ids),
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_preprint_bundle_dict(d: dict) -> PreprintBundleResult:
    """Validate a dict representation of a PreprintBundleEntry."""
    required = [
        "bundle_id",
        "batch_id",
        "pipeline_version",
        "submission_date",
        "title",
        "artifact_ids",
        "evidence_level",
        "preprint_doi",
        "contact_email",
        "release_approved",
    ]
    for key in required:
        if key not in d:
            return PreprintBundleResult(
                bundle_id=d.get("bundle_id", ""),
                batch_id=d.get("batch_id", ""),
                artifact_count=0,
                passed=False,
                errors=[f"missing required field: {key}"],
                warnings=[],
            )

    entry = PreprintBundleEntry(
        bundle_id=d["bundle_id"],
        batch_id=d["batch_id"],
        pipeline_version=d["pipeline_version"],
        submission_date=d["submission_date"],
        title=d["title"],
        artifact_ids=d["artifact_ids"],
        evidence_level=d["evidence_level"],
        preprint_doi=d["preprint_doi"],
        contact_email=d["contact_email"],
        release_approved=d["release_approved"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_preprint_bundle(entry)

"""Dataset release package checker (Phase L L5).

Validates that an open dataset release meets all data governance
requirements before publication.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

VALID_LICENSE_IDENTIFIERS: set[str] = {
    "Apache-2.0",
    "CC-BY-4.0",
    "CC-BY-NC-4.0",
    "CC0-1.0",
    "MIT",
}

MINIMUM_DATA_SOURCES: int = 1

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class DatasetReleaseEntry:
    """One dataset release package record."""

    release_id: str
    dataset_name: str
    dataset_version: str
    release_date: str
    license_identifier: str
    data_sources: List[str]
    contains_sequences: bool
    contains_activity_data: bool
    dual_use_assessed: bool
    usage_policy_url: str
    contact_email: str
    release_approved: bool
    dry_lab_only: bool = True


@dataclass
class DatasetReleaseResult:
    """Validation result for a DatasetReleaseEntry."""

    release_id: str
    dataset_name: str
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_dataset_release(entry: DatasetReleaseEntry) -> DatasetReleaseResult:
    """Validate a DatasetReleaseEntry.  Returns a DatasetReleaseResult."""
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.release_id.startswith("DSR-"):
        errors.append("release_id must start with 'DSR-'")

    if not entry.dataset_name:
        errors.append("dataset_name must not be empty")

    if not entry.dataset_version:
        errors.append("dataset_version must not be empty")

    if not _DATE_RE.match(entry.release_date):
        errors.append("release_date must be YYYY-MM-DD")

    if entry.license_identifier not in VALID_LICENSE_IDENTIFIERS:
        errors.append(
            f"license_identifier '{entry.license_identifier}' is not valid; "
            f"must be one of {sorted(VALID_LICENSE_IDENTIFIERS)}"
        )

    if len(entry.data_sources) < MINIMUM_DATA_SOURCES:
        errors.append(
            f"data_sources must have at least {MINIMUM_DATA_SOURCES} entry"
        )

    if not entry.dual_use_assessed:
        errors.append(
            "dual_use_assessed must be True; complete a dual-use risk assessment "
            "before releasing any dataset"
        )

    if not entry.usage_policy_url:
        errors.append("usage_policy_url must not be empty")

    if not entry.contact_email:
        errors.append("contact_email must not be empty")

    if not entry.release_approved:
        errors.append("release_approved must be True for a valid dataset release")

    if entry.dry_lab_only is not True:
        errors.append("dry_lab_only must be True")

    if not errors:
        if entry.license_identifier == "CC-BY-NC-4.0":
            warnings.append(
                "license_identifier is CC-BY-NC-4.0 (non-commercial); "
                "this may restrict some academic and commercial research uses."
            )

        if len(entry.data_sources) == 1:
            warnings.append(
                "Only one data source declared; consider whether additional "
                "provenance documentation is needed."
            )

    return DatasetReleaseResult(
        release_id=entry.release_id,
        dataset_name=entry.dataset_name,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_dataset_release_dict(d: dict) -> DatasetReleaseResult:
    """Validate a dict representation of a DatasetReleaseEntry."""
    required = [
        "release_id",
        "dataset_name",
        "dataset_version",
        "release_date",
        "license_identifier",
        "data_sources",
        "contains_sequences",
        "contains_activity_data",
        "dual_use_assessed",
        "usage_policy_url",
        "contact_email",
        "release_approved",
    ]
    for key in required:
        if key not in d:
            return DatasetReleaseResult(
                release_id=d.get("release_id", ""),
                dataset_name=d.get("dataset_name", ""),
                passed=False,
                errors=[f"missing required field: {key}"],
                warnings=[],
            )

    entry = DatasetReleaseEntry(
        release_id=d["release_id"],
        dataset_name=d["dataset_name"],
        dataset_version=d["dataset_version"],
        release_date=d["release_date"],
        license_identifier=d["license_identifier"],
        data_sources=d["data_sources"],
        contains_sequences=d["contains_sequences"],
        contains_activity_data=d["contains_activity_data"],
        dual_use_assessed=d["dual_use_assessed"],
        usage_policy_url=d["usage_policy_url"],
        contact_email=d["contact_email"],
        release_approved=d["release_approved"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_dataset_release(entry)

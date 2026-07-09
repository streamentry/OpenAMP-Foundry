"""Reproducibility manifest schema (Phase L L2).

Captures exact software versions, data checksums, and random seeds
for a pipeline run to enable third-party reproduction.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

MINIMUM_PACKAGES: int = 3
MINIMUM_DATA_FILES: int = 1
RECOMMENDED_PACKAGES: int = 5

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class ReproducibilityManifestEntry:
    """One reproducibility manifest record."""

    manifest_id: str
    batch_id: str
    pipeline_version: str
    run_date: str
    python_version: str
    package_checksums: Dict[str, str]
    data_checksums: Dict[str, str]
    random_seeds: Dict[str, int]
    hardware_summary: str
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class ReproducibilityManifestResult:
    """Validation result for a ReproducibilityManifestEntry."""

    manifest_id: str
    batch_id: str
    package_count: int
    data_file_count: int
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_reproducibility_manifest(
    entry: ReproducibilityManifestEntry,
) -> ReproducibilityManifestResult:
    """Validate a ReproducibilityManifestEntry.  Returns a ReproducibilityManifestResult."""
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.manifest_id.startswith("RPM-"):
        errors.append("manifest_id must start with 'RPM-'")

    if not entry.batch_id:
        errors.append("batch_id must not be empty")

    if not entry.pipeline_version:
        errors.append("pipeline_version must not be empty")

    if not _DATE_RE.match(entry.run_date):
        errors.append("run_date must be YYYY-MM-DD")

    if not entry.python_version:
        errors.append("python_version must not be empty")

    if len(entry.package_checksums) < MINIMUM_PACKAGES:
        errors.append(
            f"package_checksums must have at least {MINIMUM_PACKAGES} entries"
        )

    if len(entry.data_checksums) < MINIMUM_DATA_FILES:
        errors.append(
            f"data_checksums must have at least {MINIMUM_DATA_FILES} entry"
        )

    if not entry.hardware_summary:
        errors.append("hardware_summary must not be empty")

    if not entry.reviewer:
        errors.append("reviewer must not be empty")

    if entry.dry_lab_only is not True:
        errors.append("dry_lab_only must be True")

    if not errors:
        if not entry.random_seeds:
            warnings.append(
                "random_seeds is empty; stochastic steps cannot be reproduced exactly. "
                "Record seeds for all sampling operations."
            )

        if len(entry.package_checksums) < RECOMMENDED_PACKAGES:
            warnings.append(
                f"Only {len(entry.package_checksums)} package(s) recorded; "
                f"consider adding key dependencies (recommended: {RECOMMENDED_PACKAGES}+)."
            )

        if "unknown" in entry.hardware_summary.lower():
            warnings.append(
                "hardware_summary contains 'unknown'; reproducibility may vary across platforms."
            )

    return ReproducibilityManifestResult(
        manifest_id=entry.manifest_id,
        batch_id=entry.batch_id,
        package_count=len(entry.package_checksums),
        data_file_count=len(entry.data_checksums),
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_reproducibility_manifest_dict(d: dict) -> ReproducibilityManifestResult:
    """Validate a dict representation of a ReproducibilityManifestEntry."""
    required = [
        "manifest_id",
        "batch_id",
        "pipeline_version",
        "run_date",
        "python_version",
        "package_checksums",
        "data_checksums",
        "random_seeds",
        "hardware_summary",
        "reviewer",
    ]
    for key in required:
        if key not in d:
            return ReproducibilityManifestResult(
                manifest_id=d.get("manifest_id", ""),
                batch_id=d.get("batch_id", ""),
                package_count=0,
                data_file_count=0,
                passed=False,
                errors=[f"missing required field: {key}"],
                warnings=[],
            )

    entry = ReproducibilityManifestEntry(
        manifest_id=d["manifest_id"],
        batch_id=d["batch_id"],
        pipeline_version=d["pipeline_version"],
        run_date=d["run_date"],
        python_version=d["python_version"],
        package_checksums=d["package_checksums"],
        data_checksums=d["data_checksums"],
        random_seeds=d["random_seeds"],
        hardware_summary=d["hardware_summary"],
        reviewer=d["reviewer"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_reproducibility_manifest(entry)

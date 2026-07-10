"""Pilot evidence package schema — Phase Q Q1.

The external export artifact for a pilot package.  References all required
evidence artifacts and validates package completeness before external sharing.

A complete package (is_complete=True) means every required artifact ID is
present and the safety clearance is confirmed.  Incomplete packages can be
saved but not released for external review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

PEP_PREFIX = "PEP-"
CCS_PREFIX = "CCS-"
BSP_PREFIX = "BSP-"
PSC_PREFIX = "PSC-"
PRE_PREFIX = "PRE-"
BCM_PREFIX = "BCM-"
PACKAGE_NOTES_MAX_LENGTH = 400
MIN_CANDIDATES = 1


@dataclass
class PilotEvidencePackageEntry:
    """Evidence package for external pilot sharing."""

    pep_id: str
    pipeline_version: str
    ccs_id: str
    bsp_id: str
    psc_id: str
    pre_registration_id: str
    baseline_comparison_id: str
    candidate_count: int
    cleared_for_synthesis: bool
    is_complete: bool
    missing_artifacts: List[str]
    package_notes: str
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class PilotEvidencePackageResult:
    pep_id: str
    pipeline_version: str
    ccs_id: str
    bsp_id: str
    psc_id: str
    candidate_count: int
    cleared_for_synthesis: bool
    is_complete: bool
    missing_artifact_count: int
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_pilot_evidence_package(
    entry: PilotEvidencePackageEntry,
) -> PilotEvidencePackageResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.pep_id.startswith(PEP_PREFIX):
        errors.append(
            f"pep_id must start with '{PEP_PREFIX}', got '{entry.pep_id}'"
        )

    if not entry.ccs_id.startswith(CCS_PREFIX):
        errors.append(
            f"ccs_id must start with '{CCS_PREFIX}', got '{entry.ccs_id}'"
        )

    if not entry.bsp_id.startswith(BSP_PREFIX):
        errors.append(
            f"bsp_id must start with '{BSP_PREFIX}', got '{entry.bsp_id}'"
        )

    if not entry.psc_id.startswith(PSC_PREFIX):
        errors.append(
            f"psc_id must start with '{PSC_PREFIX}', got '{entry.psc_id}'"
        )

    if not entry.pre_registration_id.startswith(PRE_PREFIX):
        errors.append(
            f"pre_registration_id must start with '{PRE_PREFIX}', "
            f"got '{entry.pre_registration_id}'"
        )

    if not entry.baseline_comparison_id.startswith(BCM_PREFIX):
        errors.append(
            f"baseline_comparison_id must start with '{BCM_PREFIX}', "
            f"got '{entry.baseline_comparison_id}'"
        )

    if entry.candidate_count < MIN_CANDIDATES:
        errors.append(
            f"candidate_count must be >= {MIN_CANDIDATES}, "
            f"got {entry.candidate_count}"
        )

    if not entry.cleared_for_synthesis:
        errors.append(
            "cleared_for_synthesis must be True — a pilot package requires a "
            "confirmed safety clearance (PSC) before external sharing"
        )

    # is_complete consistency
    has_missing = len(entry.missing_artifacts) > 0
    if entry.is_complete and has_missing:
        errors.append(
            "is_complete cannot be True when missing_artifacts is non-empty "
            f"(missing: {entry.missing_artifacts})"
        )
    if not entry.is_complete and not has_missing:
        errors.append(
            "is_complete must be True when missing_artifacts is empty"
        )

    if len(entry.package_notes) > PACKAGE_NOTES_MAX_LENGTH:
        errors.append(
            f"package_notes exceeds {PACKAGE_NOTES_MAX_LENGTH} characters "
            f"(got {len(entry.package_notes)})"
        )

    # Warnings
    if entry.dry_lab_only and entry.is_complete and not errors:
        warnings.append(
            "dry_lab_only=True: this package is based on computational screening "
            "only — external lab partners must be informed that no real experimental "
            "validation has been performed"
        )

    if entry.candidate_count == 1 and not errors:
        warnings.append(
            "candidate_count is 1 — a single-candidate pilot provides minimal "
            "diversity; consider whether a larger batch better serves the "
            "experiment design"
        )

    return PilotEvidencePackageResult(
        pep_id=entry.pep_id,
        pipeline_version=entry.pipeline_version,
        ccs_id=entry.ccs_id,
        bsp_id=entry.bsp_id,
        psc_id=entry.psc_id,
        candidate_count=entry.candidate_count,
        cleared_for_synthesis=entry.cleared_for_synthesis,
        is_complete=entry.is_complete,
        missing_artifact_count=len(entry.missing_artifacts),
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_pilot_evidence_package_dict(d: dict) -> PilotEvidencePackageResult:
    missing = []
    for k in (
        "pep_id",
        "pipeline_version",
        "ccs_id",
        "bsp_id",
        "psc_id",
        "pre_registration_id",
        "baseline_comparison_id",
        "candidate_count",
        "cleared_for_synthesis",
        "is_complete",
        "missing_artifacts",
        "package_notes",
        "reviewer",
    ):
        if k not in d:
            missing.append(k)
    if missing:
        return PilotEvidencePackageResult(
            pep_id=d.get("pep_id", ""),
            pipeline_version=d.get("pipeline_version", ""),
            ccs_id=d.get("ccs_id", ""),
            bsp_id=d.get("bsp_id", ""),
            psc_id=d.get("psc_id", ""),
            candidate_count=d.get("candidate_count", 0),
            cleared_for_synthesis=d.get("cleared_for_synthesis", False),
            is_complete=d.get("is_complete", False),
            missing_artifact_count=0,
            passed=False,
            errors=[f"missing required fields: {missing}"],
            warnings=[],
            dry_lab_only=d.get("dry_lab_only", True),
        )
    entry = PilotEvidencePackageEntry(
        pep_id=d["pep_id"],
        pipeline_version=d["pipeline_version"],
        ccs_id=d["ccs_id"],
        bsp_id=d["bsp_id"],
        psc_id=d["psc_id"],
        pre_registration_id=d["pre_registration_id"],
        baseline_comparison_id=d["baseline_comparison_id"],
        candidate_count=int(d["candidate_count"]),
        cleared_for_synthesis=bool(d["cleared_for_synthesis"]),
        is_complete=bool(d["is_complete"]),
        missing_artifacts=list(d["missing_artifacts"]),
        package_notes=d["package_notes"],
        reviewer=d["reviewer"],
        dry_lab_only=bool(d.get("dry_lab_only", True)),
    )
    return validate_pilot_evidence_package(entry)

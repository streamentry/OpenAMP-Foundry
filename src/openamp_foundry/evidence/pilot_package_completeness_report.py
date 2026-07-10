"""Pilot package completeness report schema — Phase K K3.

Records the completeness gate for a PilotEvidencePackage before external sharing.
Confirms all five required component IDs are present and an external sharing
clearance exists. Completeness must be explicitly confirmed before this record
is valid.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

PPC_PREFIX = "PPC-"
PEP_PREFIX = "PEP-"
ESC_PREFIX = "ESC-"
CCS_PREFIX = "CCS-"
BSP_PREFIX = "BSP-"
PSC_PREFIX = "PSC-"
PRE_PREFIX = "PRE-"
BCM_PREFIX = "BCM-"

NOTES_MAX_LENGTH = 300
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class PilotPackageCompletenessReport:
    ppc_id: str
    pipeline_version: str
    pep_id: str
    esc_id: str
    ccs_id: str
    bsp_id: str
    psc_id: str
    pre_id: str
    bcm_id: str
    checked_date: str
    completeness_confirmed: bool
    notes: str = ""


@dataclass
class PilotPackageCompletenessReportResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate(report: PilotPackageCompletenessReport) -> PilotPackageCompletenessReportResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not report.ppc_id.startswith(PPC_PREFIX):
        errors.append(f"ppc_id must start with '{PPC_PREFIX}', got: {report.ppc_id!r}")

    if not report.pipeline_version.strip():
        errors.append("pipeline_version must be a non-empty string")

    if not report.pep_id.startswith(PEP_PREFIX):
        errors.append(f"pep_id must start with '{PEP_PREFIX}', got: {report.pep_id!r}")

    if not report.esc_id.startswith(ESC_PREFIX):
        errors.append(f"esc_id must start with '{ESC_PREFIX}', got: {report.esc_id!r}")

    if not report.ccs_id.startswith(CCS_PREFIX):
        errors.append(f"ccs_id must start with '{CCS_PREFIX}', got: {report.ccs_id!r}")

    if not report.bsp_id.startswith(BSP_PREFIX):
        errors.append(f"bsp_id must start with '{BSP_PREFIX}', got: {report.bsp_id!r}")

    if not report.psc_id.startswith(PSC_PREFIX):
        errors.append(f"psc_id must start with '{PSC_PREFIX}', got: {report.psc_id!r}")

    if not report.pre_id.startswith(PRE_PREFIX):
        errors.append(f"pre_id must start with '{PRE_PREFIX}', got: {report.pre_id!r}")

    if not report.bcm_id.startswith(BCM_PREFIX):
        errors.append(f"bcm_id must start with '{BCM_PREFIX}', got: {report.bcm_id!r}")

    if not _ISO_DATE_RE.match(report.checked_date):
        errors.append(
            f"checked_date must be ISO format YYYY-MM-DD, got: {report.checked_date!r}"
        )

    if not report.completeness_confirmed:
        errors.append(
            "completeness_confirmed must be True; "
            "do not record a PPC- unless the package is confirmed complete"
        )

    if len(report.notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"notes exceeds {NOTES_MAX_LENGTH} chars (got {len(report.notes)})"
        )

    # Warnings
    if not report.notes.strip():
        warnings.append(
            "notes is empty; consider documenting the completeness review process"
        )

    component_ids = [report.ccs_id, report.bsp_id, report.psc_id, report.pre_id, report.bcm_id]
    if len(set(component_ids)) < len(component_ids):
        warnings.append(
            "two or more component IDs are identical; "
            "each component (CCS-, BSP-, PSC-, PRE-, BCM-) should have a unique ID"
        )

    if report.pep_id in component_ids:
        warnings.append(
            f"pep_id {report.pep_id!r} appears as a component ID; "
            "PEP- IDs should not be reused as component IDs"
        )

    return PilotPackageCompletenessReportResult(
        valid=len(errors) == 0, errors=errors, warnings=warnings
    )


def validate_dict(data: dict) -> PilotPackageCompletenessReportResult:
    try:
        report = PilotPackageCompletenessReport(
            ppc_id=data.get("ppc_id", ""),
            pipeline_version=data.get("pipeline_version", ""),
            pep_id=data.get("pep_id", ""),
            esc_id=data.get("esc_id", ""),
            ccs_id=data.get("ccs_id", ""),
            bsp_id=data.get("bsp_id", ""),
            psc_id=data.get("psc_id", ""),
            pre_id=data.get("pre_id", ""),
            bcm_id=data.get("bcm_id", ""),
            checked_date=data.get("checked_date", ""),
            completeness_confirmed=bool(data.get("completeness_confirmed", False)),
            notes=data.get("notes", ""),
        )
    except Exception as exc:
        return PilotPackageCompletenessReportResult(
            valid=False, errors=[f"Construction error: {exc}"]
        )
    return validate(report)

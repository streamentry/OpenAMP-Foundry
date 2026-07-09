"""Calibration cycle summary schema — Phase P P5.

Index record for one complete calibration cycle.  References all artifacts
from the cycle: the opening gate, the selection proposal, the safety clearance,
the experimental outcomes, the performance summary, the aggregator, and the
closing gate.

One CCS per completed cycle creates an auditable history of the learning loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

CCS_PREFIX = "CCS-"
BSP_PREFIX = "BSP-"
PSC_PREFIX = "PSC-"
BOS_PREFIX = "BOS-"
CPS_PREFIX = "CPS-"
CBA_PREFIX = "CBA-"
CRG_PREFIX = "CRG-"
VALID_CYCLE_OUTCOMES = frozenset({"improved", "stable", "degraded"})
CYCLE_NOTES_MAX_LENGTH = 400


@dataclass
class CalibrationCycleSummaryEntry:
    """Index record for one complete calibration feedback cycle."""

    ccs_id: str
    pipeline_version: str
    bsp_id: str
    psc_id: str
    bos_id: str
    cps_id: str
    cba_id: str
    crg_id_previous: str
    crg_id_next: str
    cycle_outcome: str
    cycle_notes: str
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class CalibrationCycleSummaryResult:
    ccs_id: str
    pipeline_version: str
    bsp_id: str
    psc_id: str
    bos_id: str
    cps_id: str
    cba_id: str
    crg_id_previous: str
    crg_id_next: str
    cycle_outcome: str
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_calibration_cycle_summary(
    entry: CalibrationCycleSummaryEntry,
) -> CalibrationCycleSummaryResult:
    errors: List[str] = []
    warnings: List[str] = []

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

    if not entry.bos_id.startswith(BOS_PREFIX):
        errors.append(
            f"bos_id must start with '{BOS_PREFIX}', got '{entry.bos_id}'"
        )

    if not entry.cps_id.startswith(CPS_PREFIX):
        errors.append(
            f"cps_id must start with '{CPS_PREFIX}', got '{entry.cps_id}'"
        )

    if not entry.cba_id.startswith(CBA_PREFIX):
        errors.append(
            f"cba_id must start with '{CBA_PREFIX}', got '{entry.cba_id}'"
        )

    if not entry.crg_id_previous.startswith(CRG_PREFIX):
        errors.append(
            f"crg_id_previous must start with '{CRG_PREFIX}', "
            f"got '{entry.crg_id_previous}'"
        )

    if not entry.crg_id_next.startswith(CRG_PREFIX):
        errors.append(
            f"crg_id_next must start with '{CRG_PREFIX}', "
            f"got '{entry.crg_id_next}'"
        )

    if entry.crg_id_previous == entry.crg_id_next:
        errors.append(
            "crg_id_previous and crg_id_next must differ — a completed cycle "
            "must open a new calibration gate"
        )

    if entry.cycle_outcome not in VALID_CYCLE_OUTCOMES:
        errors.append(
            f"cycle_outcome must be one of {sorted(VALID_CYCLE_OUTCOMES)}, "
            f"got '{entry.cycle_outcome}'"
        )

    if len(entry.cycle_notes) > CYCLE_NOTES_MAX_LENGTH:
        errors.append(
            f"cycle_notes exceeds {CYCLE_NOTES_MAX_LENGTH} characters "
            f"(got {len(entry.cycle_notes)})"
        )

    # Warnings
    if entry.cycle_outcome == "degraded" and not errors:
        warnings.append(
            "cycle_outcome is 'degraded' — calibration quality decreased this cycle; "
            "consider whether a recalibration refusal was the right decision or "
            "whether additional data is needed before next selection"
        )

    if entry.dry_lab_only and not errors:
        warnings.append(
            "dry_lab_only=True: this cycle summary covers a synthetic or "
            "computational-only calibration loop — no real experimental data "
            "was used to update calibration"
        )

    return CalibrationCycleSummaryResult(
        ccs_id=entry.ccs_id,
        pipeline_version=entry.pipeline_version,
        bsp_id=entry.bsp_id,
        psc_id=entry.psc_id,
        bos_id=entry.bos_id,
        cps_id=entry.cps_id,
        cba_id=entry.cba_id,
        crg_id_previous=entry.crg_id_previous,
        crg_id_next=entry.crg_id_next,
        cycle_outcome=entry.cycle_outcome,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_calibration_cycle_summary_dict(d: dict) -> CalibrationCycleSummaryResult:
    missing = []
    for k in (
        "ccs_id",
        "pipeline_version",
        "bsp_id",
        "psc_id",
        "bos_id",
        "cps_id",
        "cba_id",
        "crg_id_previous",
        "crg_id_next",
        "cycle_outcome",
        "cycle_notes",
        "reviewer",
    ):
        if k not in d:
            missing.append(k)
    if missing:
        return CalibrationCycleSummaryResult(
            ccs_id=d.get("ccs_id", ""),
            pipeline_version=d.get("pipeline_version", ""),
            bsp_id=d.get("bsp_id", ""),
            psc_id=d.get("psc_id", ""),
            bos_id=d.get("bos_id", ""),
            cps_id=d.get("cps_id", ""),
            cba_id=d.get("cba_id", ""),
            crg_id_previous=d.get("crg_id_previous", ""),
            crg_id_next=d.get("crg_id_next", ""),
            cycle_outcome=d.get("cycle_outcome", ""),
            passed=False,
            errors=[f"missing required fields: {missing}"],
            warnings=[],
            dry_lab_only=d.get("dry_lab_only", True),
        )
    entry = CalibrationCycleSummaryEntry(
        ccs_id=d["ccs_id"],
        pipeline_version=d["pipeline_version"],
        bsp_id=d["bsp_id"],
        psc_id=d["psc_id"],
        bos_id=d["bos_id"],
        cps_id=d["cps_id"],
        cba_id=d["cba_id"],
        crg_id_previous=d["crg_id_previous"],
        crg_id_next=d["crg_id_next"],
        cycle_outcome=d["cycle_outcome"],
        cycle_notes=d["cycle_notes"],
        reviewer=d["reviewer"],
        dry_lab_only=bool(d.get("dry_lab_only", True)),
    )
    return validate_calibration_cycle_summary(entry)

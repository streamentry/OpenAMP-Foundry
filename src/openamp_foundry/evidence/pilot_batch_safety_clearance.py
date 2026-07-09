"""Pilot batch safety clearance schema — Phase P P4.

Documents that a proposed batch has been safety-reviewed before wet-lab synthesis.
This schema prevents the pipeline from clearing hazardous sequences for synthesis
by requiring all four safety screens to complete and blocking high-risk batches.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

PSC_PREFIX = "PSC-"
BSP_PREFIX = "BSP-"
VALID_RISK_TIERS = frozenset({"low", "moderate", "high"})
SAFETY_NOTES_MAX_LENGTH = 400
HIGH_RISK_TIER = "high"
MODERATE_RISK_TIER = "moderate"


@dataclass
class PilotBatchSafetyClearanceEntry:
    """Safety clearance record for a proposed batch before wet-lab synthesis."""

    psc_id: str
    bsp_id: str
    pipeline_version: str
    dual_use_risk_checked: bool
    novelty_verified: bool
    toxicity_screened: bool
    hemolysis_screened: bool
    max_safety_risk_tier: str
    cleared_for_synthesis: bool
    rejection_ids: List[str]
    safety_notes: str
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class PilotBatchSafetyClearanceResult:
    psc_id: str
    bsp_id: str
    pipeline_version: str
    max_safety_risk_tier: str
    cleared_for_synthesis: bool
    rejection_count: int
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_pilot_batch_safety_clearance(
    entry: PilotBatchSafetyClearanceEntry,
) -> PilotBatchSafetyClearanceResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.psc_id.startswith(PSC_PREFIX):
        errors.append(
            f"psc_id must start with '{PSC_PREFIX}', got '{entry.psc_id}'"
        )

    if not entry.bsp_id.startswith(BSP_PREFIX):
        errors.append(
            f"bsp_id must start with '{BSP_PREFIX}', got '{entry.bsp_id}'"
        )

    if not entry.dual_use_risk_checked:
        errors.append(
            "dual_use_risk_checked must be True — dual-use risk review is mandatory "
            "before any batch is cleared for synthesis"
        )

    if not entry.novelty_verified:
        errors.append(
            "novelty_verified must be True — novelty verification is mandatory "
            "to confirm candidates are not re-synthesis of known hazardous sequences"
        )

    if not entry.toxicity_screened:
        errors.append(
            "toxicity_screened must be True — toxicity screening is mandatory "
            "before any batch is cleared for synthesis"
        )

    if not entry.hemolysis_screened:
        errors.append(
            "hemolysis_screened must be True — hemolysis screening is mandatory "
            "before any batch is cleared for synthesis"
        )

    if entry.max_safety_risk_tier not in VALID_RISK_TIERS:
        errors.append(
            f"max_safety_risk_tier must be one of {sorted(VALID_RISK_TIERS)}, "
            f"got '{entry.max_safety_risk_tier}'"
        )

    if entry.max_safety_risk_tier == HIGH_RISK_TIER and entry.cleared_for_synthesis:
        errors.append(
            "cleared_for_synthesis must be False when max_safety_risk_tier='high' — "
            "high-risk batches cannot be cleared for wet-lab synthesis"
        )

    if len(entry.safety_notes) > SAFETY_NOTES_MAX_LENGTH:
        errors.append(
            f"safety_notes exceeds {SAFETY_NOTES_MAX_LENGTH} characters "
            f"(got {len(entry.safety_notes)})"
        )

    # Warnings
    if (
        entry.max_safety_risk_tier == MODERATE_RISK_TIER
        and entry.cleared_for_synthesis
        and not errors
    ):
        warnings.append(
            "max_safety_risk_tier is 'moderate' but batch is cleared — ensure "
            "moderate-risk candidates have been individually reviewed and documented "
            "in safety_notes or rejection_ids"
        )

    if entry.rejection_ids and not errors:
        warnings.append(
            f"{len(entry.rejection_ids)} candidate(s) rejected for safety: "
            f"{entry.rejection_ids[:3]}{'...' if len(entry.rejection_ids) > 3 else ''}"
        )

    if entry.dry_lab_only and entry.cleared_for_synthesis and not errors:
        warnings.append(
            "dry_lab_only=True: this clearance is based on computational safety "
            "screening only — wet-lab synthesis should receive additional "
            "qualified human review before proceeding"
        )

    return PilotBatchSafetyClearanceResult(
        psc_id=entry.psc_id,
        bsp_id=entry.bsp_id,
        pipeline_version=entry.pipeline_version,
        max_safety_risk_tier=entry.max_safety_risk_tier,
        cleared_for_synthesis=entry.cleared_for_synthesis,
        rejection_count=len(entry.rejection_ids),
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_pilot_batch_safety_clearance_dict(
    d: dict,
) -> PilotBatchSafetyClearanceResult:
    missing = []
    for k in (
        "psc_id",
        "bsp_id",
        "pipeline_version",
        "dual_use_risk_checked",
        "novelty_verified",
        "toxicity_screened",
        "hemolysis_screened",
        "max_safety_risk_tier",
        "cleared_for_synthesis",
        "rejection_ids",
        "safety_notes",
        "reviewer",
    ):
        if k not in d:
            missing.append(k)
    if missing:
        return PilotBatchSafetyClearanceResult(
            psc_id=d.get("psc_id", ""),
            bsp_id=d.get("bsp_id", ""),
            pipeline_version=d.get("pipeline_version", ""),
            max_safety_risk_tier=d.get("max_safety_risk_tier", ""),
            cleared_for_synthesis=d.get("cleared_for_synthesis", False),
            rejection_count=0,
            passed=False,
            errors=[f"missing required fields: {missing}"],
            warnings=[],
            dry_lab_only=d.get("dry_lab_only", True),
        )
    entry = PilotBatchSafetyClearanceEntry(
        psc_id=d["psc_id"],
        bsp_id=d["bsp_id"],
        pipeline_version=d["pipeline_version"],
        dual_use_risk_checked=bool(d["dual_use_risk_checked"]),
        novelty_verified=bool(d["novelty_verified"]),
        toxicity_screened=bool(d["toxicity_screened"]),
        hemolysis_screened=bool(d["hemolysis_screened"]),
        max_safety_risk_tier=d["max_safety_risk_tier"],
        cleared_for_synthesis=bool(d["cleared_for_synthesis"]),
        rejection_ids=list(d["rejection_ids"]),
        safety_notes=d["safety_notes"],
        reviewer=d["reviewer"],
        dry_lab_only=bool(d.get("dry_lab_only", True)),
    )
    return validate_pilot_batch_safety_clearance(entry)

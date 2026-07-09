"""Batch selection proposal schema — Phase P P1.

Links a passed calibration readiness gate (CRG-) to an explicit next-batch
selection plan.  A proposal is only valid when gate_passed=True, enforcing
that the pipeline cannot propose candidates when calibration is poor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

BSP_PREFIX = "BSP-"
CRG_PREFIX = "CRG-"
VALID_SELECTION_STRATEGIES = frozenset(
    {"exploitation", "exploration", "diversity", "uncertainty_sampling", "hybrid"}
)
PROPOSAL_NOTES_MAX_LENGTH = 400
FRACTION_SUM_TOLERANCE = 0.001
MIN_CANDIDATES = 1
POOR_CALIBRATION_BRIER_THRESHOLD = 0.25
PURE_EXPLOITATION_THRESHOLD = 0.99


@dataclass
class BatchSelectionProposalEntry:
    """Proposed next-batch selection linked to a passed calibration gate."""

    bsp_id: str
    pipeline_version: str
    gate_id: str
    gate_passed: bool
    candidate_ids: List[str]
    selection_strategy: str
    exploitation_fraction: float
    exploration_fraction: float
    max_brier_score_allowed: float
    proposal_notes: str
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class BatchSelectionProposalResult:
    bsp_id: str
    pipeline_version: str
    gate_id: str
    gate_passed: bool
    candidate_count: int
    selection_strategy: str
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_batch_selection_proposal(
    entry: BatchSelectionProposalEntry,
) -> BatchSelectionProposalResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.bsp_id.startswith(BSP_PREFIX):
        errors.append(
            f"bsp_id must start with '{BSP_PREFIX}', got '{entry.bsp_id}'"
        )

    if not entry.gate_id.startswith(CRG_PREFIX):
        errors.append(
            f"gate_id must start with '{CRG_PREFIX}', got '{entry.gate_id}'"
        )

    if not entry.gate_passed:
        errors.append(
            "gate_passed must be True — a batch proposal requires a passed "
            "calibration readiness gate"
        )

    if not entry.candidate_ids:
        errors.append(
            f"candidate_ids must contain at least {MIN_CANDIDATES} entry"
        )

    if entry.selection_strategy not in VALID_SELECTION_STRATEGIES:
        errors.append(
            f"selection_strategy must be one of {sorted(VALID_SELECTION_STRATEGIES)}, "
            f"got '{entry.selection_strategy}'"
        )

    if not (0.0 <= entry.exploitation_fraction <= 1.0):
        errors.append(
            f"exploitation_fraction must be in [0.0, 1.0], "
            f"got {entry.exploitation_fraction}"
        )

    if not (0.0 <= entry.exploration_fraction <= 1.0):
        errors.append(
            f"exploration_fraction must be in [0.0, 1.0], "
            f"got {entry.exploration_fraction}"
        )

    fraction_sum = entry.exploitation_fraction + entry.exploration_fraction
    if abs(fraction_sum - 1.0) > FRACTION_SUM_TOLERANCE:
        errors.append(
            f"exploitation_fraction + exploration_fraction must sum to 1.0 "
            f"(within {FRACTION_SUM_TOLERANCE}), got {fraction_sum:.4f}"
        )

    if not (0.0 <= entry.max_brier_score_allowed <= 1.0):
        errors.append(
            f"max_brier_score_allowed must be in [0.0, 1.0], "
            f"got {entry.max_brier_score_allowed}"
        )

    if len(entry.proposal_notes) > PROPOSAL_NOTES_MAX_LENGTH:
        errors.append(
            f"proposal_notes exceeds {PROPOSAL_NOTES_MAX_LENGTH} characters "
            f"(got {len(entry.proposal_notes)})"
        )

    # Warnings
    if (
        entry.exploitation_fraction >= PURE_EXPLOITATION_THRESHOLD
        and not errors
    ):
        warnings.append(
            "exploitation_fraction is near 1.0 — pure exploitation risks "
            "missing high-uncertainty candidates that could improve calibration"
        )

    if len(entry.candidate_ids) == 1 and not errors:
        warnings.append(
            "only one candidate selected — diversity and calibration coverage "
            "may be reduced with a single-candidate batch"
        )

    if (
        entry.max_brier_score_allowed >= POOR_CALIBRATION_BRIER_THRESHOLD
        and not errors
    ):
        warnings.append(
            f"max_brier_score_allowed ({entry.max_brier_score_allowed:.3f}) "
            f"is at or above the poor-calibration threshold "
            f"({POOR_CALIBRATION_BRIER_THRESHOLD}) — the gate may have passed "
            "with marginal calibration quality"
        )

    return BatchSelectionProposalResult(
        bsp_id=entry.bsp_id,
        pipeline_version=entry.pipeline_version,
        gate_id=entry.gate_id,
        gate_passed=entry.gate_passed,
        candidate_count=len(entry.candidate_ids),
        selection_strategy=entry.selection_strategy,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_batch_selection_proposal_dict(d: dict) -> BatchSelectionProposalResult:
    missing = []
    for k in (
        "bsp_id",
        "pipeline_version",
        "gate_id",
        "gate_passed",
        "candidate_ids",
        "selection_strategy",
        "exploitation_fraction",
        "exploration_fraction",
        "max_brier_score_allowed",
        "proposal_notes",
        "reviewer",
    ):
        if k not in d:
            missing.append(k)
    if missing:
        return BatchSelectionProposalResult(
            bsp_id=d.get("bsp_id", ""),
            pipeline_version=d.get("pipeline_version", ""),
            gate_id=d.get("gate_id", ""),
            gate_passed=d.get("gate_passed", False),
            candidate_count=0,
            selection_strategy=d.get("selection_strategy", ""),
            passed=False,
            errors=[f"missing required fields: {missing}"],
            warnings=[],
            dry_lab_only=d.get("dry_lab_only", True),
        )
    entry = BatchSelectionProposalEntry(
        bsp_id=d["bsp_id"],
        pipeline_version=d["pipeline_version"],
        gate_id=d["gate_id"],
        gate_passed=bool(d["gate_passed"]),
        candidate_ids=list(d["candidate_ids"]),
        selection_strategy=d["selection_strategy"],
        exploitation_fraction=float(d["exploitation_fraction"]),
        exploration_fraction=float(d["exploration_fraction"]),
        max_brier_score_allowed=float(d["max_brier_score_allowed"]),
        proposal_notes=d["proposal_notes"],
        reviewer=d["reviewer"],
        dry_lab_only=bool(d.get("dry_lab_only", True)),
    )
    return validate_batch_selection_proposal(entry)

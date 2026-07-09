"""Batch outcome summary schema — Phase P P3.

Documents aggregate experimental outcomes for a batch proposed by a
BatchSelectionProposal (BSP).  This schema closes the loop from proposal
to results and enforces the synthetic/real evidence boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

BOS_PREFIX = "BOS-"
BSP_PREFIX = "BSP-"
OUTCOME_NOTES_MAX_LENGTH = 400
UNTESTED_WARNING_THRESHOLD = 0.25


@dataclass
class BatchOutcomeSummaryEntry:
    """Aggregate experimental outcomes for a proposed batch."""

    bos_id: str
    pipeline_version: str
    bsp_id: str
    batch_id: str
    candidates_proposed: int
    candidates_tested: int
    candidates_active: int
    candidates_inactive: int
    is_synthetic: bool
    outcome_notes: str
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class BatchOutcomeSummaryResult:
    bos_id: str
    pipeline_version: str
    bsp_id: str
    batch_id: str
    candidates_proposed: int
    candidates_tested: int
    candidates_active: int
    candidates_inactive: int
    candidates_untested: int
    is_synthetic: bool
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_batch_outcome_summary(
    entry: BatchOutcomeSummaryEntry,
) -> BatchOutcomeSummaryResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.bos_id.startswith(BOS_PREFIX):
        errors.append(
            f"bos_id must start with '{BOS_PREFIX}', got '{entry.bos_id}'"
        )

    if not entry.bsp_id.startswith(BSP_PREFIX):
        errors.append(
            f"bsp_id must start with '{BSP_PREFIX}', got '{entry.bsp_id}'"
        )

    if entry.candidates_proposed < 1:
        errors.append(
            f"candidates_proposed must be >= 1, got {entry.candidates_proposed}"
        )

    if entry.candidates_tested < 0:
        errors.append(
            f"candidates_tested must be >= 0, got {entry.candidates_tested}"
        )

    if entry.candidates_active < 0:
        errors.append(
            f"candidates_active must be >= 0, got {entry.candidates_active}"
        )

    if entry.candidates_inactive < 0:
        errors.append(
            f"candidates_inactive must be >= 0, got {entry.candidates_inactive}"
        )

    # active + inactive must equal tested
    if entry.candidates_active + entry.candidates_inactive != entry.candidates_tested:
        errors.append(
            f"candidates_active ({entry.candidates_active}) + "
            f"candidates_inactive ({entry.candidates_inactive}) must equal "
            f"candidates_tested ({entry.candidates_tested})"
        )

    # tested cannot exceed proposed
    if entry.candidates_tested > entry.candidates_proposed:
        errors.append(
            f"candidates_tested ({entry.candidates_tested}) cannot exceed "
            f"candidates_proposed ({entry.candidates_proposed})"
        )

    # synthetic/dry_lab_only consistency
    if entry.is_synthetic and not entry.dry_lab_only:
        errors.append(
            "is_synthetic=True requires dry_lab_only=True — synthetic results "
            "cannot be treated as real lab data"
        )

    if len(entry.outcome_notes) > OUTCOME_NOTES_MAX_LENGTH:
        errors.append(
            f"outcome_notes exceeds {OUTCOME_NOTES_MAX_LENGTH} characters "
            f"(got {len(entry.outcome_notes)})"
        )

    candidates_untested = max(
        0, entry.candidates_proposed - entry.candidates_tested
    )

    # Warnings
    if (
        candidates_untested > 0
        and entry.candidates_proposed > 0
        and not errors
    ):
        fraction_untested = candidates_untested / entry.candidates_proposed
        if fraction_untested >= UNTESTED_WARNING_THRESHOLD:
            warnings.append(
                f"{candidates_untested}/{entry.candidates_proposed} candidates "
                f"({fraction_untested:.0%}) were not tested — calibration coverage "
                "may be reduced"
            )
        else:
            warnings.append(
                f"{candidates_untested} candidate(s) from the proposal were not tested"
            )

    if not entry.is_synthetic and entry.dry_lab_only and not errors:
        warnings.append(
            "is_synthetic=False (real results) but dry_lab_only=True — "
            "consider setting dry_lab_only=False for real experimental outcomes"
        )

    if entry.candidates_active == 0 and entry.candidates_tested > 0 and not errors:
        warnings.append(
            "no active candidates in this batch — consider whether this is "
            "expected given the selection strategy"
        )

    return BatchOutcomeSummaryResult(
        bos_id=entry.bos_id,
        pipeline_version=entry.pipeline_version,
        bsp_id=entry.bsp_id,
        batch_id=entry.batch_id,
        candidates_proposed=entry.candidates_proposed,
        candidates_tested=entry.candidates_tested,
        candidates_active=entry.candidates_active,
        candidates_inactive=entry.candidates_inactive,
        candidates_untested=candidates_untested,
        is_synthetic=entry.is_synthetic,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_batch_outcome_summary_dict(d: dict) -> BatchOutcomeSummaryResult:
    missing = []
    for k in (
        "bos_id",
        "pipeline_version",
        "bsp_id",
        "batch_id",
        "candidates_proposed",
        "candidates_tested",
        "candidates_active",
        "candidates_inactive",
        "is_synthetic",
        "outcome_notes",
        "reviewer",
    ):
        if k not in d:
            missing.append(k)
    if missing:
        return BatchOutcomeSummaryResult(
            bos_id=d.get("bos_id", ""),
            pipeline_version=d.get("pipeline_version", ""),
            bsp_id=d.get("bsp_id", ""),
            batch_id=d.get("batch_id", ""),
            candidates_proposed=d.get("candidates_proposed", 0),
            candidates_tested=d.get("candidates_tested", 0),
            candidates_active=d.get("candidates_active", 0),
            candidates_inactive=d.get("candidates_inactive", 0),
            candidates_untested=0,
            is_synthetic=d.get("is_synthetic", True),
            passed=False,
            errors=[f"missing required fields: {missing}"],
            warnings=[],
            dry_lab_only=d.get("dry_lab_only", True),
        )
    entry = BatchOutcomeSummaryEntry(
        bos_id=d["bos_id"],
        pipeline_version=d["pipeline_version"],
        bsp_id=d["bsp_id"],
        batch_id=d["batch_id"],
        candidates_proposed=int(d["candidates_proposed"]),
        candidates_tested=int(d["candidates_tested"]),
        candidates_active=int(d["candidates_active"]),
        candidates_inactive=int(d["candidates_inactive"]),
        is_synthetic=bool(d["is_synthetic"]),
        outcome_notes=d["outcome_notes"],
        reviewer=d["reviewer"],
        dry_lab_only=bool(d.get("dry_lab_only", True)),
    )
    return validate_batch_outcome_summary(entry)

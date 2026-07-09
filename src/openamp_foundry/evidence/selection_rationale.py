"""Selection rationale schema for OpenAMP Foundry candidate selection accountability."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

VALID_EVIDENCE_LEVELS: set[int] = {1, 2, 3, 4, 5, 6}
MINIMUM_SAFETY_FLAGS: int = 1


@dataclass
class SelectionRationaleEntry:
    """A selection rationale entry documenting why a candidate was chosen."""

    selection_id: str
    batch_id: str
    candidate_id: str
    pipeline_version: str
    selection_date: str
    evidence_level: int
    baseline_comparison: str
    primary_criterion: str
    safety_flags_checked: List[str]
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class SelectionRationaleResult:
    """Result of validating a SelectionRationaleEntry."""

    selection_id: str
    candidate_id: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_selection_rationale(entry: SelectionRationaleEntry) -> SelectionRationaleResult:
    """Validate a SelectionRationaleEntry against policy rules."""
    errors: list[str] = []
    warnings: list[str] = []

    if not entry.selection_id or not str(entry.selection_id).strip():
        errors.append("selection_id must be non-empty")
    elif not entry.selection_id.startswith("SEL-"):
        errors.append(
            f"selection_id must start with 'SEL-', got: {entry.selection_id!r}"
        )

    if not entry.batch_id or not str(entry.batch_id).strip():
        errors.append("batch_id must be non-empty")

    if not entry.candidate_id or not str(entry.candidate_id).strip():
        errors.append("candidate_id must be non-empty")

    if not entry.pipeline_version or not str(entry.pipeline_version).strip():
        errors.append("pipeline_version must be non-empty")

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", entry.selection_date):
        errors.append(
            f"selection_date must be YYYY-MM-DD, got: {entry.selection_date!r}"
        )

    if not isinstance(entry.evidence_level, int) or entry.evidence_level not in VALID_EVIDENCE_LEVELS:
        errors.append(
            f"evidence_level must be one of {sorted(VALID_EVIDENCE_LEVELS)}, "
            f"got: {entry.evidence_level!r}"
        )

    if not entry.baseline_comparison or not str(entry.baseline_comparison).strip():
        errors.append("baseline_comparison must be non-empty")

    if not entry.primary_criterion or not str(entry.primary_criterion).strip():
        errors.append("primary_criterion must be non-empty")

    if not isinstance(entry.safety_flags_checked, list):
        errors.append("safety_flags_checked must be a list")
    elif len(entry.safety_flags_checked) < MINIMUM_SAFETY_FLAGS:
        errors.append(
            f"safety_flags_checked must have at least {MINIMUM_SAFETY_FLAGS} entry, "
            f"got: {len(entry.safety_flags_checked)}"
        )

    if not entry.reviewer or not str(entry.reviewer).strip():
        errors.append("reviewer must be non-empty")

    if not entry.dry_lab_only:
        errors.append("dry_lab_only must be True for selection rationale entries")

    # Warnings
    if isinstance(entry.evidence_level, int) and entry.evidence_level <= 2:
        warnings.append(
            f"evidence_level is {entry.evidence_level} (sequence-only): "
            "consider additional filters before synthesis selection"
        )

    if isinstance(entry.baseline_comparison, str) and entry.baseline_comparison.strip().lower() in (
        "none", "n/a", "na", ""
    ):
        warnings.append(
            "baseline_comparison appears empty or N/A: "
            "document what score baseline was used for comparison"
        )

    return SelectionRationaleResult(
        selection_id=entry.selection_id,
        candidate_id=entry.candidate_id,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_selection_rationale_dict(d: dict) -> SelectionRationaleResult:
    """Validate a dict representation of a SelectionRationaleEntry."""
    required = [
        "batch_id",
        "baseline_comparison",
        "candidate_id",
        "evidence_level",
        "pipeline_version",
        "primary_criterion",
        "reviewer",
        "safety_flags_checked",
        "selection_date",
        "selection_id",
    ]
    missing = [f for f in required if f not in d]
    if missing:
        return SelectionRationaleResult(
            selection_id=d.get("selection_id", ""),
            candidate_id=d.get("candidate_id", ""),
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=True,
        )
    entry = SelectionRationaleEntry(
        selection_id=d["selection_id"],
        batch_id=d["batch_id"],
        candidate_id=d["candidate_id"],
        pipeline_version=d["pipeline_version"],
        selection_date=d["selection_date"],
        evidence_level=d["evidence_level"],
        baseline_comparison=d["baseline_comparison"],
        primary_criterion=d["primary_criterion"],
        safety_flags_checked=d["safety_flags_checked"],
        reviewer=d["reviewer"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_selection_rationale(entry)

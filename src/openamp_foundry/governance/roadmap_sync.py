"""Roadmap-to-issue sync validation for OpenAMP Foundry."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

VALID_SYNC_STATUSES: set[str] = {
    "synced",
    "missing_issue",
    "orphaned_issue",
    "stale",
    "completed",
}
VALID_PRIORITY_LEVELS: set[str] = {"A", "B", "C", "D"}
VALID_PHASES: set[str] = {
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
}


@dataclass
class RoadmapSyncEntry:
    """A single roadmap item with its sync status."""

    item_id: str
    phase: str
    description: str
    priority: str
    sync_status: str
    issue_number: Optional[int] = None
    pr_number: Optional[int] = None
    completed: bool = False
    completion_date: str = ""
    dry_lab_only: bool = True


@dataclass
class RoadmapSyncResult:
    """Result of validating a RoadmapSyncEntry."""

    item_id: str
    phase: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_roadmap_sync_entry(entry: RoadmapSyncEntry) -> RoadmapSyncResult:
    """Validate a RoadmapSyncEntry against policy rules."""
    errors: list[str] = []
    warnings: list[str] = []

    if not entry.item_id or not entry.item_id.strip():
        errors.append("item_id must be non-empty")

    if entry.phase not in VALID_PHASES:
        errors.append(
            f"phase must be one of {sorted(VALID_PHASES)}, got: {entry.phase!r}"
        )

    if not entry.description or not entry.description.strip():
        errors.append("description must be non-empty")

    if entry.priority not in VALID_PRIORITY_LEVELS:
        errors.append(
            f"priority must be one of {sorted(VALID_PRIORITY_LEVELS)}, "
            f"got: {entry.priority!r}"
        )

    if entry.sync_status not in VALID_SYNC_STATUSES:
        errors.append(
            f"sync_status must be one of {sorted(VALID_SYNC_STATUSES)}, "
            f"got: {entry.sync_status!r}"
        )

    if not entry.dry_lab_only:
        errors.append("dry_lab_only must be True for roadmap sync entries")

    # Completed items must have a completion_date
    if entry.completed and not entry.completion_date:
        errors.append(
            "completed items must have a non-empty completion_date"
        )

    # completion_date must be YYYY-MM-DD if provided
    if entry.completion_date and not re.match(r"^\d{4}-\d{2}-\d{2}$", entry.completion_date):
        errors.append(
            f"completion_date must be YYYY-MM-DD, got: {entry.completion_date!r}"
        )

    # Warnings
    if entry.sync_status == "missing_issue" and entry.priority == "A":
        warnings.append(
            "priority A item has sync_status 'missing_issue': "
            "file a GitHub issue immediately"
        )

    if entry.sync_status == "stale":
        warnings.append(
            "sync_status is 'stale': this item may have drifted from the "
            "roadmap — review and update"
        )

    if entry.sync_status == "orphaned_issue":
        warnings.append(
            "sync_status is 'orphaned_issue': a GitHub issue exists with "
            "no matching roadmap item — add to roadmap or close the issue"
        )

    if entry.issue_number is None and not entry.completed:
        warnings.append(
            "no issue_number: open a GitHub issue to track this roadmap item"
        )

    return RoadmapSyncResult(
        item_id=entry.item_id,
        phase=entry.phase,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_roadmap_sync_dict(d: dict) -> RoadmapSyncResult:
    """Validate a dict representation of a RoadmapSyncEntry."""
    required = [
        "item_id",
        "phase",
        "description",
        "priority",
        "sync_status",
    ]
    missing = [f for f in required if f not in d]
    if missing:
        return RoadmapSyncResult(
            item_id=d.get("item_id", ""),
            phase=d.get("phase", ""),
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=True,
        )
    entry = RoadmapSyncEntry(
        item_id=d["item_id"],
        phase=d["phase"],
        description=d["description"],
        priority=d["priority"],
        sync_status=d["sync_status"],
        issue_number=d.get("issue_number"),
        pr_number=d.get("pr_number"),
        completed=d.get("completed", False),
        completion_date=d.get("completion_date", ""),
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_roadmap_sync_entry(entry)

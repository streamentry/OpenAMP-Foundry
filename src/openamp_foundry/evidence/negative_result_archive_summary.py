"""Negative result archive summary schema — Phase F F2.

An index record that validates a collection of NegativeResultRecord (NRR-)
entries is complete and ready for long-term archiving. Enforces that all
negative results from a batch have been captured before archiving.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

NAS_PREFIX = "NAS-"
NRR_PREFIX = "NRR-"

NOTES_MAX_LENGTH = 400
LARGE_ARCHIVE_THRESHOLD = 50


@dataclass
class NegativeResultArchiveSummary:
    """Index record validating a batch of NRR- entries is ready for archiving."""

    nas_id: str
    pipeline_version: str
    batch_id: str
    archive_date: str  # ISO YYYY-MM-DD
    negative_result_count: int  # must equal len(negative_result_ids)
    negative_result_ids: List[str]  # each must start with "NRR-"
    completeness_confirmed: bool  # must be True
    all_results_have_reason: bool  # must be True
    archive_notes: str  # max 400 chars
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class NegativeResultArchiveSummaryResult:
    nas_id: str
    batch_id: str
    negative_result_count: int
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_negative_result_archive_summary(
    entry: NegativeResultArchiveSummary,
) -> NegativeResultArchiveSummaryResult:
    errors: List[str] = []
    warnings: List[str] = []

    # Rule 1: NAS- prefix
    if not entry.nas_id.startswith(NAS_PREFIX):
        errors.append(
            f"nas_id must start with '{NAS_PREFIX}', got '{entry.nas_id}'"
        )

    # Rule 2: non-empty required strings
    for fname, val in [
        ("pipeline_version", entry.pipeline_version),
        ("batch_id", entry.batch_id),
        ("reviewer", entry.reviewer),
    ]:
        if not val or not val.strip():
            errors.append(f"{fname} must not be empty")

    # Rule 3: archive_date ISO YYYY-MM-DD
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", entry.archive_date):
        errors.append(
            f"archive_date must be ISO format YYYY-MM-DD, got '{entry.archive_date}'"
        )

    # Rule 4: negative_result_count >= 0
    if entry.negative_result_count < 0:
        errors.append(
            f"negative_result_count must be >= 0, got {entry.negative_result_count}"
        )

    # Rule 5: negative_result_ids count matches negative_result_count
    actual_count = len(entry.negative_result_ids)
    if actual_count != entry.negative_result_count:
        errors.append(
            f"negative_result_count ({entry.negative_result_count}) does not match "
            f"len(negative_result_ids) ({actual_count})"
        )

    # Rule 6: all ids in negative_result_ids start with NRR-
    bad_ids = [
        nid for nid in entry.negative_result_ids
        if not nid.startswith(NRR_PREFIX)
    ]
    if bad_ids:
        errors.append(
            f"all negative_result_ids must start with '{NRR_PREFIX}', "
            f"invalid: {bad_ids[:5]}"
        )

    # Rule 7: completeness_confirmed must be True
    if not entry.completeness_confirmed:
        errors.append(
            "completeness_confirmed must be True — all negative results from this "
            "batch must be captured before archiving"
        )

    # Rule 8: all_results_have_reason must be True
    if not entry.all_results_have_reason:
        errors.append(
            "all_results_have_reason must be True — every NRR in the archive must "
            "document a rejection reason before archiving"
        )

    # Rule 9: archive_notes length
    if len(entry.archive_notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"archive_notes must be at most {NOTES_MAX_LENGTH} characters, "
            f"got {len(entry.archive_notes)}"
        )

    # Warning 1: empty negative_result_ids
    if entry.negative_result_count == 0:
        warnings.append(
            "negative_result_count is 0 — a batch with no negative results is unusual; "
            "confirm all results were tracked"
        )

    # Warning 2: empty archive_notes
    if not entry.archive_notes.strip():
        warnings.append(
            "archive_notes is empty — consider documenting the scope of this archive"
        )

    # Warning 3: large archive
    if entry.negative_result_count > LARGE_ARCHIVE_THRESHOLD:
        warnings.append(
            f"negative_result_count ({entry.negative_result_count}) exceeds "
            f"{LARGE_ARCHIVE_THRESHOLD} — large archives warrant extra curation review"
        )

    passed = len(errors) == 0
    return NegativeResultArchiveSummaryResult(
        nas_id=entry.nas_id,
        batch_id=entry.batch_id,
        negative_result_count=entry.negative_result_count,
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_negative_result_archive_summary_dict(
    data: dict,
) -> NegativeResultArchiveSummaryResult:
    entry = NegativeResultArchiveSummary(
        nas_id=data.get("nas_id", ""),
        pipeline_version=data.get("pipeline_version", ""),
        batch_id=data.get("batch_id", ""),
        archive_date=data.get("archive_date", ""),
        negative_result_count=int(data.get("negative_result_count", 0)),
        negative_result_ids=list(data.get("negative_result_ids", [])),
        completeness_confirmed=bool(data.get("completeness_confirmed", False)),
        all_results_have_reason=bool(data.get("all_results_have_reason", False)),
        archive_notes=data.get("archive_notes", ""),
        reviewer=data.get("reviewer", ""),
        dry_lab_only=bool(data.get("dry_lab_only", True)),
    )
    return validate_negative_result_archive_summary(entry)

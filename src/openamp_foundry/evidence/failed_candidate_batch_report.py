"""Failed candidate batch report schema — Phase F F4.

Summarizes all failed candidates from a screening batch, linking
RejectionReasonEntry (RJR-) records and the NegativeResultArchiveSummary
(NAS-) into a single auditable report. Makes failed batches reviewable
and enables calibration loop learning from structured failure statistics.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

FCR_PREFIX = "FCR-"
NAS_PREFIX = "NAS-"
RJR_PREFIX = "RJR-"

VALID_REJECTION_REASONS = frozenset({
    "low_activity_score",
    "hemolysis_risk",
    "toxicity_risk",
    "insufficient_novelty",
    "data_quality_failure",
    "safety_policy_block",
    "duplicate",
    "out_of_scope",
    "manual_exclusion",
})

REPORT_NOTES_MAX_LENGTH = 400
FAILURE_RATE_TOLERANCE = 0.01


@dataclass
class FailedCandidateBatchReport:
    """Batch-level summary of failed candidates and their rejection reasons."""

    fcr_id: str
    pipeline_version: str
    batch_id: str
    report_date: str  # ISO YYYY-MM-DD
    total_candidates_screened: int  # >= 1
    failed_candidate_count: int  # >= 0, <= total_candidates_screened
    failure_rate: float  # in [0.0, 1.0], must be consistent with counts
    top_rejection_reasons: List[str]  # each in VALID_REJECTION_REASONS
    rejection_reason_ids: List[str]  # each starts with "RJR-"
    negative_result_archive_id: str  # must start with "NAS-" if provided
    report_notes: str  # max 400 chars
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class FailedCandidateBatchReportResult:
    fcr_id: str
    batch_id: str
    total_candidates_screened: int
    failed_candidate_count: int
    failure_rate: float
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_failed_candidate_batch_report(
    entry: FailedCandidateBatchReport,
) -> FailedCandidateBatchReportResult:
    errors: List[str] = []
    warnings: List[str] = []

    # Rule 1: FCR- prefix
    if not entry.fcr_id.startswith(FCR_PREFIX):
        errors.append(
            f"fcr_id must start with '{FCR_PREFIX}', got '{entry.fcr_id}'"
        )

    # Rule 2: non-empty required strings
    for fname, val in [
        ("pipeline_version", entry.pipeline_version),
        ("batch_id", entry.batch_id),
        ("reviewer", entry.reviewer),
    ]:
        if not val or not val.strip():
            errors.append(f"{fname} must not be empty")

    # Rule 3: report_date ISO YYYY-MM-DD
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", entry.report_date):
        errors.append(
            f"report_date must be ISO format YYYY-MM-DD, got '{entry.report_date}'"
        )

    # Rule 4: total_candidates_screened >= 1
    if entry.total_candidates_screened < 1:
        errors.append(
            f"total_candidates_screened must be >= 1, got {entry.total_candidates_screened}"
        )

    # Rule 5: failed_candidate_count in [0, total_candidates_screened]
    if entry.failed_candidate_count < 0:
        errors.append(
            f"failed_candidate_count must be >= 0, got {entry.failed_candidate_count}"
        )
    elif entry.failed_candidate_count > entry.total_candidates_screened:
        errors.append(
            f"failed_candidate_count ({entry.failed_candidate_count}) cannot exceed "
            f"total_candidates_screened ({entry.total_candidates_screened})"
        )

    # Rule 6: failure_rate in [0.0, 1.0]
    if not (0.0 <= entry.failure_rate <= 1.0):
        errors.append(
            f"failure_rate must be in [0.0, 1.0], got {entry.failure_rate}"
        )

    # Rule 7: failure_rate consistent with counts
    if (
        entry.total_candidates_screened >= 1
        and 0.0 <= entry.failure_rate <= 1.0
        and entry.failed_candidate_count >= 0
    ):
        expected_rate = entry.failed_candidate_count / entry.total_candidates_screened
        if abs(expected_rate - entry.failure_rate) > FAILURE_RATE_TOLERANCE:
            errors.append(
                f"failure_rate ({entry.failure_rate:.4f}) is inconsistent with "
                f"failed_candidate_count/total_candidates_screened "
                f"({entry.failed_candidate_count}/{entry.total_candidates_screened} "
                f"= {expected_rate:.4f}); tolerance is {FAILURE_RATE_TOLERANCE}"
            )

    # Rule 8: top_rejection_reasons all in valid set
    bad_reasons = [
        r for r in entry.top_rejection_reasons
        if r not in VALID_REJECTION_REASONS
    ]
    if bad_reasons:
        errors.append(
            f"top_rejection_reasons contains invalid values: {bad_reasons}; "
            f"must be from {sorted(VALID_REJECTION_REASONS)}"
        )

    # Rule 9: rejection_reason_ids start with RJR- (if any provided)
    bad_rjr = [
        rid for rid in entry.rejection_reason_ids
        if not rid.startswith(RJR_PREFIX)
    ]
    if bad_rjr:
        errors.append(
            f"all rejection_reason_ids must start with '{RJR_PREFIX}', "
            f"invalid: {bad_rjr[:5]}"
        )

    # Rule 10: negative_result_archive_id starts with NAS- (if non-empty)
    if entry.negative_result_archive_id and not entry.negative_result_archive_id.startswith(
        NAS_PREFIX
    ):
        errors.append(
            f"negative_result_archive_id must start with '{NAS_PREFIX}', "
            f"got '{entry.negative_result_archive_id}'"
        )

    # Rule 11: report_notes length
    if len(entry.report_notes) > REPORT_NOTES_MAX_LENGTH:
        errors.append(
            f"report_notes must be at most {REPORT_NOTES_MAX_LENGTH} characters, "
            f"got {len(entry.report_notes)}"
        )

    # Warning 1: no rejection_reason_ids provided
    if not entry.rejection_reason_ids:
        warnings.append(
            "rejection_reason_ids is empty — link RJR- records for each failed candidate"
        )

    # Warning 2: no negative_result_archive_id
    if not entry.negative_result_archive_id:
        warnings.append(
            "negative_result_archive_id is empty — link the NAS- archive for this batch"
        )

    # Warning 3: 100% failure rate
    if entry.failure_rate >= 1.0 and entry.total_candidates_screened >= 1:
        warnings.append(
            "failure_rate is 1.0 — all candidates failed; review screening thresholds"
        )

    # Warning 4: empty report_notes
    if not entry.report_notes.strip():
        warnings.append(
            "report_notes is empty — document the batch screening context"
        )

    passed = len(errors) == 0
    return FailedCandidateBatchReportResult(
        fcr_id=entry.fcr_id,
        batch_id=entry.batch_id,
        total_candidates_screened=entry.total_candidates_screened,
        failed_candidate_count=entry.failed_candidate_count,
        failure_rate=entry.failure_rate,
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_failed_candidate_batch_report_dict(
    data: dict,
) -> FailedCandidateBatchReportResult:
    entry = FailedCandidateBatchReport(
        fcr_id=data.get("fcr_id", ""),
        pipeline_version=data.get("pipeline_version", ""),
        batch_id=data.get("batch_id", ""),
        report_date=data.get("report_date", ""),
        total_candidates_screened=int(data.get("total_candidates_screened", 0)),
        failed_candidate_count=int(data.get("failed_candidate_count", 0)),
        failure_rate=float(data.get("failure_rate", 0.0)),
        top_rejection_reasons=list(data.get("top_rejection_reasons", [])),
        rejection_reason_ids=list(data.get("rejection_reason_ids", [])),
        negative_result_archive_id=data.get("negative_result_archive_id", ""),
        report_notes=data.get("report_notes", ""),
        reviewer=data.get("reviewer", ""),
        dry_lab_only=bool(data.get("dry_lab_only", True)),
    )
    return validate_failed_candidate_batch_report(entry)

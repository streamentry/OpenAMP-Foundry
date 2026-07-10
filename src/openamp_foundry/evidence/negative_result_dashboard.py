"""Negative result dashboard schema — Phase F F9.

Aggregates rejection statistics across a batch to show failure patterns.
Records top rejection stage and reason, high-confidence rejection count,
and enforces that all rejections have NRR- records.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

NRD_PREFIX = "NRD-"

VALID_REJECTION_STAGES = frozenset({
    "sequence_quality",
    "candidate_selection",
    "toxicity_screen",
    "hemolysis_screen",
    "novelty_check",
    "simulation",
    "manual_review",
})

VALID_REJECTION_REASONS = frozenset({
    "low_score",
    "failed_toxicity",
    "failed_hemolysis",
    "insufficient_novelty",
    "simulation_failure",
    "duplicate_sequence",
    "low_confidence",
    "borderline_unsafe",
    "manual_exclusion",
})

REJECTION_RATE_TOLERANCE = 0.01
HIGH_REJECTION_RATE_WARNING = 0.8
SUMMARY_MAX_LENGTH = 400
NOTES_MAX_LENGTH = 300
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class NegativeResultDashboard:
    nrd_id: str
    pipeline_version: str
    batch_id: str
    report_date: str
    total_candidates_evaluated: int
    total_rejections: int
    rejection_rate: float
    top_rejection_stage: str
    top_rejection_reason: str
    high_confidence_rejections: int
    all_rejections_have_nrr: bool
    summary: str
    notes: str = ""


@dataclass
class NegativeResultDashboardResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate(dashboard: NegativeResultDashboard) -> NegativeResultDashboardResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not dashboard.nrd_id.startswith(NRD_PREFIX):
        errors.append(f"nrd_id must start with '{NRD_PREFIX}', got: {dashboard.nrd_id!r}")

    if not dashboard.pipeline_version.strip():
        errors.append("pipeline_version must be a non-empty string")

    if not dashboard.batch_id.strip():
        errors.append("batch_id must be a non-empty string")

    if not _ISO_DATE_RE.match(dashboard.report_date):
        errors.append(
            f"report_date must be ISO format YYYY-MM-DD, got: {dashboard.report_date!r}"
        )

    if dashboard.total_candidates_evaluated < 1:
        errors.append(
            f"total_candidates_evaluated must be at least 1, got: {dashboard.total_candidates_evaluated}"
        )

    if dashboard.total_rejections < 0:
        errors.append(
            f"total_rejections must be >= 0, got: {dashboard.total_rejections}"
        )
    elif dashboard.total_rejections > dashboard.total_candidates_evaluated:
        errors.append(
            f"total_rejections ({dashboard.total_rejections}) cannot exceed "
            f"total_candidates_evaluated ({dashboard.total_candidates_evaluated})"
        )

    if not (0.0 <= dashboard.rejection_rate <= 1.0):
        errors.append(
            f"rejection_rate must be in [0, 1], got: {dashboard.rejection_rate}"
        )
    elif dashboard.total_candidates_evaluated >= 1:
        computed = dashboard.total_rejections / dashboard.total_candidates_evaluated
        if abs(computed - dashboard.rejection_rate) > REJECTION_RATE_TOLERANCE:
            errors.append(
                f"rejection_rate ({dashboard.rejection_rate:.4f}) is inconsistent with "
                f"total_rejections/total_candidates_evaluated "
                f"({dashboard.total_rejections}/{dashboard.total_candidates_evaluated} = {computed:.4f}); "
                f"tolerance is {REJECTION_RATE_TOLERANCE}"
            )

    if dashboard.top_rejection_stage not in VALID_REJECTION_STAGES:
        errors.append(
            f"top_rejection_stage {dashboard.top_rejection_stage!r} not in valid set: "
            f"{sorted(VALID_REJECTION_STAGES)}"
        )

    if dashboard.top_rejection_reason not in VALID_REJECTION_REASONS:
        errors.append(
            f"top_rejection_reason {dashboard.top_rejection_reason!r} not in valid set: "
            f"{sorted(VALID_REJECTION_REASONS)}"
        )

    if dashboard.high_confidence_rejections < 0:
        errors.append(
            f"high_confidence_rejections must be >= 0, got: {dashboard.high_confidence_rejections}"
        )
    elif dashboard.high_confidence_rejections > dashboard.total_rejections:
        errors.append(
            f"high_confidence_rejections ({dashboard.high_confidence_rejections}) "
            f"cannot exceed total_rejections ({dashboard.total_rejections})"
        )

    if not dashboard.all_rejections_have_nrr:
        errors.append(
            "all_rejections_have_nrr must be True; "
            "every rejection must have a corresponding NRR- record before a dashboard is created"
        )

    if not dashboard.summary.strip():
        errors.append("summary must be a non-empty string")
    elif len(dashboard.summary) > SUMMARY_MAX_LENGTH:
        errors.append(
            f"summary exceeds {SUMMARY_MAX_LENGTH} chars (got {len(dashboard.summary)})"
        )

    if len(dashboard.notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"notes exceeds {NOTES_MAX_LENGTH} chars (got {len(dashboard.notes)})"
        )

    # Warnings
    if dashboard.rejection_rate > HIGH_REJECTION_RATE_WARNING:
        warnings.append(
            f"rejection_rate={dashboard.rejection_rate:.2f} is unusually high "
            f"(>{HIGH_REJECTION_RATE_WARNING}); verify the selection pipeline is not too strict"
        )

    if (
        dashboard.total_candidates_evaluated >= 1
        and dashboard.total_rejections == dashboard.total_candidates_evaluated
    ):
        warnings.append(
            "total_rejections equals total_candidates_evaluated; "
            "all candidates rejected — verify no systematic pipeline failure"
        )

    if not dashboard.notes.strip():
        warnings.append(
            "notes is empty; consider documenting the batch failure context"
        )

    return NegativeResultDashboardResult(
        valid=len(errors) == 0, errors=errors, warnings=warnings
    )


def validate_dict(data: dict) -> NegativeResultDashboardResult:
    try:
        dashboard = NegativeResultDashboard(
            nrd_id=data.get("nrd_id", ""),
            pipeline_version=data.get("pipeline_version", ""),
            batch_id=data.get("batch_id", ""),
            report_date=data.get("report_date", ""),
            total_candidates_evaluated=int(data.get("total_candidates_evaluated", 0)),
            total_rejections=int(data.get("total_rejections", 0)),
            rejection_rate=float(data.get("rejection_rate", 0.0)),
            top_rejection_stage=data.get("top_rejection_stage", ""),
            top_rejection_reason=data.get("top_rejection_reason", ""),
            high_confidence_rejections=int(data.get("high_confidence_rejections", 0)),
            all_rejections_have_nrr=bool(data.get("all_rejections_have_nrr", False)),
            summary=data.get("summary", ""),
            notes=data.get("notes", ""),
        )
    except Exception as exc:
        return NegativeResultDashboardResult(
            valid=False, errors=[f"Construction error: {exc}"]
        )
    return validate(dashboard)

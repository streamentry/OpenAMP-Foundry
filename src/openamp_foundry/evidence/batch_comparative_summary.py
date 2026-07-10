"""Comparative summary schema across multiple candidate batches."""

from __future__ import annotations

from dataclasses import dataclass, field

BATCH_COMPARATIVE_SUMMARY_ID_PREFIX = "BCS-"

VALID_TREND_DIRECTIONS: frozenset = frozenset(
    {"improving", "stable", "declining", "insufficient_data"}
)

VALID_COMPARISON_STATUSES: frozenset = frozenset(
    {"draft", "complete", "under_review", "finalized"}
)

VALID_QUALITY_TIERS: frozenset = frozenset(
    {"high", "medium", "low", "insufficient"}
)

MIN_BATCHES_FOR_TREND: int = 2
MAX_BATCHES_PER_SUMMARY: int = 20


@dataclass
class BatchSnapshotEntry:
    batch_id: str
    batch_index: int
    total_candidates: int
    n_nominated: int
    n_rejected: int
    hit_rate: float
    primary_rejection_reason: str
    has_calibration_update: bool
    snapshot_note: str = ""


@dataclass
class BatchComparativeSummary:
    summary_id: str
    batches: list = field(default_factory=list)
    total_batches: int = 0
    overall_trend: str = "insufficient_data"
    comparison_status: str = "draft"
    dry_lab_only: bool = True
    quality_tier: str = "insufficient"
    trend_note: str = ""
    improvement_observed: bool = False
    is_example_data: bool = True


@dataclass
class ComparativeSummaryValidationResult:
    is_valid: bool
    violations: list = field(default_factory=list)


def build_batch_snapshot_entry(
    batch_id: str,
    batch_index: int,
    total_candidates: int,
    n_nominated: int,
    n_rejected: int,
    hit_rate: float,
    primary_rejection_reason: str,
    has_calibration_update: bool = False,
    snapshot_note: str = "",
) -> BatchSnapshotEntry:
    return BatchSnapshotEntry(
        batch_id=batch_id,
        batch_index=batch_index,
        total_candidates=total_candidates,
        n_nominated=n_nominated,
        n_rejected=n_rejected,
        hit_rate=hit_rate,
        primary_rejection_reason=primary_rejection_reason,
        has_calibration_update=has_calibration_update,
        snapshot_note=snapshot_note,
    )


def build_batch_comparative_summary(
    summary_id: str,
    batches: list,
    overall_trend: str,
    comparison_status: str,
    dry_lab_only: bool,
    quality_tier: str,
    trend_note: str = "",
    improvement_observed: bool = False,
    is_example_data: bool = True,
) -> BatchComparativeSummary:
    return BatchComparativeSummary(
        summary_id=summary_id,
        batches=list(batches),
        total_batches=len(batches),
        overall_trend=overall_trend,
        comparison_status=comparison_status,
        dry_lab_only=dry_lab_only,
        quality_tier=quality_tier,
        trend_note=trend_note,
        improvement_observed=improvement_observed,
        is_example_data=is_example_data,
    )


def validate_batch_comparative_summary(
    summary: BatchComparativeSummary,
) -> ComparativeSummaryValidationResult:
    violations: list[str] = []

    if not summary.summary_id.startswith(BATCH_COMPARATIVE_SUMMARY_ID_PREFIX):
        violations.append(
            f"summary_id must start with '{BATCH_COMPARATIVE_SUMMARY_ID_PREFIX}', "
            f"got '{summary.summary_id}'"
        )

    if summary.overall_trend not in VALID_TREND_DIRECTIONS:
        violations.append(
            f"overall_trend '{summary.overall_trend}' not in VALID_TREND_DIRECTIONS"
        )

    if summary.comparison_status not in VALID_COMPARISON_STATUSES:
        violations.append(
            f"comparison_status '{summary.comparison_status}' not in VALID_COMPARISON_STATUSES"
        )

    if summary.quality_tier not in VALID_QUALITY_TIERS:
        violations.append(
            f"quality_tier '{summary.quality_tier}' not in VALID_QUALITY_TIERS"
        )

    if summary.total_batches != len(summary.batches):
        violations.append(
            f"total_batches={summary.total_batches} does not match len(batches)={len(summary.batches)}"
        )

    if summary.total_batches > MAX_BATCHES_PER_SUMMARY:
        violations.append(
            f"total_batches={summary.total_batches} exceeds MAX_BATCHES_PER_SUMMARY={MAX_BATCHES_PER_SUMMARY}"
        )

    if (
        summary.overall_trend in {"improving", "declining"}
        and summary.total_batches < MIN_BATCHES_FOR_TREND
    ):
        violations.append(
            f"overall_trend='{summary.overall_trend}' requires at least "
            f"{MIN_BATCHES_FOR_TREND} batches, got {summary.total_batches}"
        )

    if not summary.dry_lab_only:
        violations.append(
            "dry_lab_only must be True; wet-lab comparative summaries require human review"
        )

    if summary.improvement_observed and summary.overall_trend not in {"improving", "stable"}:
        violations.append(
            "improvement_observed=True requires overall_trend in {'improving', 'stable'}"
        )

    for i, batch in enumerate(summary.batches):
        prefix = f"batch[{i}] (id={batch.batch_id})"

        if not batch.batch_id:
            violations.append(f"{prefix}: batch_id must not be empty")

        if batch.total_candidates < 0:
            violations.append(f"{prefix}: total_candidates must be >= 0")

        if batch.n_nominated + batch.n_rejected > batch.total_candidates:
            violations.append(
                f"{prefix}: n_nominated + n_rejected "
                f"({batch.n_nominated + batch.n_rejected}) "
                f"> total_candidates ({batch.total_candidates})"
            )

        if not (0.0 <= batch.hit_rate <= 1.0):
            violations.append(
                f"{prefix}: hit_rate={batch.hit_rate} outside [0.0, 1.0]"
            )

    return ComparativeSummaryValidationResult(
        is_valid=len(violations) == 0,
        violations=violations,
    )


def format_batch_comparative_summary(summary: BatchComparativeSummary) -> str:
    lines: list[str] = []
    lines.append(f"Batch Comparative Summary ({summary.summary_id})")
    lines.append(f"  Status: {summary.comparison_status}")
    lines.append(f"  Quality tier: {summary.quality_tier}")
    lines.append(f"  Overall trend: {summary.overall_trend}")
    lines.append(f"  Improvement observed: {summary.improvement_observed}")
    lines.append(f"  Total batches: {summary.total_batches}")
    lines.append(f"  Dry-lab only: {summary.dry_lab_only}")
    if summary.trend_note:
        lines.append(f"  Note: {summary.trend_note}")
    if summary.batches:
        lines.append("  Batch snapshots:")
        for b in summary.batches:
            lines.append(
                f"    [{b.batch_index}] {b.batch_id}: "
                f"total={b.total_candidates}, "
                f"nominated={b.n_nominated}, "
                f"rejected={b.n_rejected}, "
                f"hit_rate={b.hit_rate:.2f}"
            )
            if b.has_calibration_update:
                lines.append(f"        calibration update applied")
    return "\n".join(lines) + "\n"

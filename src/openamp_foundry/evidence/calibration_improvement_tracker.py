"""CIT- calibration improvement tracker schema.

Aggregates MBL- records across batches and computes whether the pipeline's
prediction quality is trending in the right direction. Requires at least 2
batches with wet-lab data to compute a trend. Flags when calibration is not
producing measurable improvement.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_CIT_TREND_DIRECTIONS: frozenset[str] = frozenset({
    "improving",
    "stable",
    "degrading",
    "insufficient_data",
})

VALID_CIT_SUMMARY_GRADES: frozenset[str] = frozenset({
    "A",
    "B",
    "C",
    "D",
    "N/A",
})

MIN_BATCHES_FOR_TREND: int = 2
IMPROVEMENT_THRESHOLD: float = 0.05
DEGRADATION_THRESHOLD: float = -0.05


@dataclass
class BatchHitRateEntry:
    batch_id: str
    mbl_id: str
    hit_rate: float
    quality_grade: str


@dataclass
class CalibrationImprovementTracker:
    cit_id: str
    pipeline_version: str
    batch_entries: list[BatchHitRateEntry]
    n_batches: int
    n_batches_with_data: int
    first_batch_hit_rate: float
    latest_batch_hit_rate: float
    hit_rate_delta: float
    trend_direction: str
    summary_grade: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_calibration_improvement_tracker(cit: CalibrationImprovementTracker) -> None:
    if not cit.cit_id.startswith("CIT-"):
        raise ValueError(f"cit_id must start with 'CIT-': {cit.cit_id!r}")
    if not cit.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    for entry in cit.batch_entries:
        if not (0.0 <= entry.hit_rate <= 1.0):
            raise ValueError(
                f"hit_rate must be in [0, 1] for batch {entry.batch_id!r}: {entry.hit_rate}"
            )
    if cit.n_batches != len(cit.batch_entries):
        raise ValueError("n_batches must equal len(batch_entries)")
    entries_with_data = [e for e in cit.batch_entries if e.quality_grade != "N/A"]
    if cit.n_batches_with_data != len(entries_with_data):
        raise ValueError("n_batches_with_data mismatch")
    if cit.trend_direction not in VALID_CIT_TREND_DIRECTIONS:
        raise ValueError(
            f"trend_direction {cit.trend_direction!r} not in VALID_CIT_TREND_DIRECTIONS"
        )
    if cit.summary_grade not in VALID_CIT_SUMMARY_GRADES:
        raise ValueError(
            f"summary_grade {cit.summary_grade!r} not in VALID_CIT_SUMMARY_GRADES"
        )
    if cit.trend_direction == "insufficient_data" and cit.summary_grade != "N/A":
        raise ValueError(
            "summary_grade must be 'N/A' when trend_direction='insufficient_data'"
        )
    if not cit.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not cit.limitations:
        raise ValueError("limitations must be non-empty")
    if not cit.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_trend(
    entries_with_data: list[BatchHitRateEntry],
) -> tuple[float, float, float, str]:
    if len(entries_with_data) < MIN_BATCHES_FOR_TREND:
        first = entries_with_data[0].hit_rate if entries_with_data else 0.0
        latest = entries_with_data[-1].hit_rate if entries_with_data else 0.0
        return first, latest, 0.0, "insufficient_data"
    first = entries_with_data[0].hit_rate
    latest = entries_with_data[-1].hit_rate
    delta = round(latest - first, 6)
    if delta >= IMPROVEMENT_THRESHOLD:
        direction = "improving"
    elif delta <= DEGRADATION_THRESHOLD:
        direction = "degrading"
    else:
        direction = "stable"
    return first, latest, delta, direction


def _compute_summary_grade(
    trend: str,
    latest_hit_rate: float,
) -> str:
    if trend == "insufficient_data":
        return "N/A"
    if trend == "improving" and latest_hit_rate >= 0.25:
        return "A"
    if trend in ("improving", "stable") and latest_hit_rate >= 0.10:
        return "B"
    if trend == "stable" or latest_hit_rate >= 0.05:
        return "C"
    return "D"


def build_calibration_improvement_tracker(
    *,
    cit_id: str,
    pipeline_version: str,
    batch_entry_dicts: list[dict],
    limitations: list[str],
    created_at: str,
) -> CalibrationImprovementTracker:
    """Build a CalibrationImprovementTracker.

    batch_entry_dicts: list of dicts with keys:
        batch_id, mbl_id, hit_rate, quality_grade
    """
    entries = [
        BatchHitRateEntry(
            batch_id=d["batch_id"],
            mbl_id=d["mbl_id"],
            hit_rate=float(d["hit_rate"]),
            quality_grade=d["quality_grade"],
        )
        for d in batch_entry_dicts
    ]
    entries_with_data = [e for e in entries if e.quality_grade != "N/A"]
    first_hr, latest_hr, delta, trend = _compute_trend(entries_with_data)
    grade = _compute_summary_grade(trend, latest_hr)
    cit = CalibrationImprovementTracker(
        cit_id=cit_id,
        pipeline_version=pipeline_version,
        batch_entries=entries,
        n_batches=len(entries),
        n_batches_with_data=len(entries_with_data),
        first_batch_hit_rate=first_hr,
        latest_batch_hit_rate=latest_hr,
        hit_rate_delta=delta,
        trend_direction=trend,
        summary_grade=grade,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_calibration_improvement_tracker(cit)
    return cit


def format_calibration_improvement_tracker(cit: CalibrationImprovementTracker) -> str:
    lines = [
        f"Calibration Improvement Tracker — {cit.cit_id}",
        f"Pipeline: {cit.pipeline_version}",
        f"Trend: {cit.trend_direction}  |  Grade: {cit.summary_grade}",
        f"Batches: {cit.n_batches} total, {cit.n_batches_with_data} with data",
        f"Hit rate: first={cit.first_batch_hit_rate:.1%}  "
        f"latest={cit.latest_batch_hit_rate:.1%}  "
        f"delta={cit.hit_rate_delta:+.1%}",
    ]
    if cit.batch_entries:
        lines.append("Batch history:")
        for entry in cit.batch_entries:
            lines.append(
                f"  {entry.batch_id} ({entry.mbl_id}): "
                f"hr={entry.hit_rate:.1%}  grade={entry.quality_grade}"
            )
    lines.append(f"Created: {cit.created_at}")
    lines.append(f"Limitations: {'; '.join(cit.limitations)}")
    lines.append(f"dry_lab_only: {cit.dry_lab_only}")
    return "\n".join(lines)

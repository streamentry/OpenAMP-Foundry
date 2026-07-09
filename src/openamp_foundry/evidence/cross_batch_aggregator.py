from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

AGGREGATION_NOTES_MAX_LENGTH: int = 400
VALID_TRENDS: Set[str] = {"improving", "stable", "degrading"}
POOR_BRIER_THRESHOLD: float = 0.25
HIGH_VARIANCE_THRESHOLD: float = 0.2
MIN_BATCHES: int = 2
SUMMARY_ID_PREFIX: str = "CBA-"
CPS_PREFIX: str = "CPS-"


@dataclass
class CrossBatchAggregatorEntry:
    aggregator_id: str
    pipeline_version: str
    batch_ids_included: List[str]
    summary_ids_included: List[str]
    mean_brier_score: float
    min_brier_score: float
    max_brier_score: float
    trend: str
    total_candidates_evaluated: int
    aggregation_notes: str
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class CrossBatchAggregatorResult:
    aggregator_id: str
    pipeline_version: str
    mean_brier_score: float
    trend: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_cross_batch_aggregator(
    entry: CrossBatchAggregatorEntry,
) -> CrossBatchAggregatorResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.aggregator_id.startswith(SUMMARY_ID_PREFIX):
        errors.append(
            f"aggregator_id must start with '{SUMMARY_ID_PREFIX}', "
            f"got '{entry.aggregator_id}'"
        )

    if len(entry.batch_ids_included) < MIN_BATCHES:
        errors.append(
            f"batch_ids_included must have at least {MIN_BATCHES} entries, "
            f"got {len(entry.batch_ids_included)}"
        )

    if len(entry.summary_ids_included) < MIN_BATCHES:
        errors.append(
            f"summary_ids_included must have at least {MIN_BATCHES} entries, "
            f"got {len(entry.summary_ids_included)}"
        )
    else:
        bad_summaries = [
            sid for sid in entry.summary_ids_included
            if not sid.startswith(CPS_PREFIX)
        ]
        if bad_summaries:
            errors.append(
                f"summary_ids_included entries must start with '{CPS_PREFIX}': "
                f"{bad_summaries}"
            )

    if (
        len(entry.batch_ids_included) >= MIN_BATCHES
        and len(entry.summary_ids_included) >= MIN_BATCHES
        and len(entry.batch_ids_included) != len(entry.summary_ids_included)
    ):
        errors.append(
            f"batch_ids_included ({len(entry.batch_ids_included)}) and "
            f"summary_ids_included ({len(entry.summary_ids_included)}) must have equal length"
        )

    for name, score in [
        ("mean_brier_score", entry.mean_brier_score),
        ("min_brier_score", entry.min_brier_score),
        ("max_brier_score", entry.max_brier_score),
    ]:
        if not (0.0 <= score <= 1.0):
            errors.append(
                f"{name} must be in [0.0, 1.0], got {score}"
            )

    if (
        0.0 <= entry.min_brier_score <= 1.0
        and 0.0 <= entry.mean_brier_score <= 1.0
        and 0.0 <= entry.max_brier_score <= 1.0
    ):
        if not (entry.min_brier_score <= entry.mean_brier_score <= entry.max_brier_score):
            errors.append(
                f"min_brier_score ({entry.min_brier_score}) <= "
                f"mean_brier_score ({entry.mean_brier_score}) <= "
                f"max_brier_score ({entry.max_brier_score}) must hold"
            )

    if entry.trend not in VALID_TRENDS:
        errors.append(
            f"trend must be one of {sorted(VALID_TRENDS)}, got '{entry.trend}'"
        )

    if entry.total_candidates_evaluated < MIN_BATCHES:
        errors.append(
            f"total_candidates_evaluated must be >= {MIN_BATCHES}, "
            f"got {entry.total_candidates_evaluated}"
        )

    if len(entry.aggregation_notes) > AGGREGATION_NOTES_MAX_LENGTH:
        errors.append(
            f"aggregation_notes exceeds {AGGREGATION_NOTES_MAX_LENGTH} chars "
            f"(got {len(entry.aggregation_notes)})"
        )

    # Warnings
    if entry.mean_brier_score >= POOR_BRIER_THRESHOLD:
        warnings.append(
            f"mean_brier_score ({entry.mean_brier_score}) >= {POOR_BRIER_THRESHOLD} "
            "-- calibration below par"
        )

    brier_range = entry.max_brier_score - entry.min_brier_score
    if brier_range >= HIGH_VARIANCE_THRESHOLD:
        warnings.append(
            f"Brier score range ({brier_range:.3f}) >= {HIGH_VARIANCE_THRESHOLD} "
            "-- high variance across batches"
        )

    if entry.trend == "degrading":
        warnings.append("trend=degrading -- performance getting worse")

    return CrossBatchAggregatorResult(
        aggregator_id=entry.aggregator_id,
        pipeline_version=entry.pipeline_version,
        mean_brier_score=entry.mean_brier_score,
        trend=entry.trend,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_cross_batch_aggregator_dict(data: dict) -> CrossBatchAggregatorResult:
    required = [
        "aggregator_id", "pipeline_version", "batch_ids_included",
        "summary_ids_included", "mean_brier_score", "min_brier_score",
        "max_brier_score", "trend", "total_candidates_evaluated",
        "aggregation_notes", "reviewer",
    ]
    errors: List[str] = []
    for key in required:
        if key not in data:
            errors.append(f"Missing required field: {key}")
    if errors:
        return CrossBatchAggregatorResult(
            aggregator_id=data.get("aggregator_id", ""),
            pipeline_version=data.get("pipeline_version", ""),
            mean_brier_score=float(data.get("mean_brier_score", 0.0)),
            trend=data.get("trend", ""),
            passed=False,
            errors=errors,
            warnings=[],
        )
    entry = CrossBatchAggregatorEntry(
        aggregator_id=str(data["aggregator_id"]),
        pipeline_version=str(data["pipeline_version"]),
        batch_ids_included=list(data["batch_ids_included"]),
        summary_ids_included=list(data["summary_ids_included"]),
        mean_brier_score=float(data["mean_brier_score"]),
        min_brier_score=float(data["min_brier_score"]),
        max_brier_score=float(data["max_brier_score"]),
        trend=str(data["trend"]),
        total_candidates_evaluated=int(data["total_candidates_evaluated"]),
        aggregation_notes=str(data["aggregation_notes"]),
        reviewer=str(data["reviewer"]),
        dry_lab_only=bool(data.get("dry_lab_only", True)),
    )
    return validate_cross_batch_aggregator(entry)

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List

VALID_METRIC_NAMES: set[str] = {
    "fold_change_mic",
    "hemolysis_fraction",
    "hit_rate",
    "mic_value",
    "novelty_score",
    "selectivity_index",
}

VALID_COMPARISON_DIRECTIONS: set[str] = {
    "higher_is_better",
    "lower_is_better",
}

MAX_NOTES_LENGTH: int = 300
P_VALUE_NOT_COMPUTED: float = -1.0
LARGE_EFFECT_THRESHOLD: float = 10.0


def _is_finite(v: float) -> bool:
    return not (math.isnan(v) or math.isinf(v))


@dataclass
class BaselineComparisonEntry:
    manifest_id: str
    batch_id: str
    pipeline_version: str
    comparison_date: str
    metric_name: str
    pipeline_score: float
    baseline_scores: Dict[str, float]
    pipeline_beats_all_baselines: bool
    effect_size: float
    p_value: float
    comparison_direction: str
    notes: str
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class BaselineComparisonResult:
    manifest_id: str
    batch_id: str
    metric_name: str
    pipeline_beats_all_baselines: bool
    baseline_count: int
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def _pipeline_actually_beats(
    pipeline_score: float,
    baseline_scores: Dict[str, float],
    direction: str,
) -> bool:
    for score in baseline_scores.values():
        if direction == "higher_is_better":
            if pipeline_score <= score:
                return False
        else:
            if pipeline_score >= score:
                return False
    return True


def validate_baseline_comparison(
    entry: BaselineComparisonEntry,
) -> BaselineComparisonResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.manifest_id.startswith("BCM-"):
        errors.append(
            f"manifest_id must start with 'BCM-', got '{entry.manifest_id}'"
        )

    if entry.metric_name not in VALID_METRIC_NAMES:
        errors.append(
            f"metric_name '{entry.metric_name}' is not valid; "
            f"must be one of {sorted(VALID_METRIC_NAMES)}"
        )

    if not _is_finite(entry.pipeline_score):
        errors.append(
            f"pipeline_score must be finite, got {entry.pipeline_score}"
        )

    if not entry.baseline_scores:
        errors.append("baseline_scores must contain at least 1 baseline")
    else:
        non_finite = [
            k for k, v in entry.baseline_scores.items() if not _is_finite(v)
        ]
        if non_finite:
            errors.append(
                f"baseline_scores contains non-finite values for: {sorted(non_finite)}"
            )

    if not _is_finite(entry.effect_size):
        errors.append(f"effect_size must be finite, got {entry.effect_size}")

    if not (
        (0.0 <= entry.p_value <= 1.0) or entry.p_value == P_VALUE_NOT_COMPUTED
    ):
        errors.append(
            f"p_value must be in [0.0, 1.0] or exactly {P_VALUE_NOT_COMPUTED} "
            f"(not computed), got {entry.p_value}"
        )

    if entry.comparison_direction not in VALID_COMPARISON_DIRECTIONS:
        errors.append(
            f"comparison_direction '{entry.comparison_direction}' is not valid; "
            f"must be one of {sorted(VALID_COMPARISON_DIRECTIONS)}"
        )

    if len(entry.notes) > MAX_NOTES_LENGTH:
        errors.append(
            f"notes exceeds {MAX_NOTES_LENGTH} characters (got {len(entry.notes)})"
        )

    if not entry.reviewer:
        errors.append("reviewer must not be empty")

    if not entry.dry_lab_only:
        errors.append(
            "dry_lab_only must be True for baseline comparison manifests "
            "(computational comparison only)"
        )

    if not errors:
        if not entry.pipeline_beats_all_baselines:
            warnings.append(
                "pipeline_beats_all_baselines=False; "
                "the pipeline underperforms at least one baseline on this metric"
            )

        if (
            entry.pipeline_beats_all_baselines
            and entry.baseline_scores
            and entry.comparison_direction in VALID_COMPARISON_DIRECTIONS
            and _is_finite(entry.pipeline_score)
            and all(_is_finite(v) for v in entry.baseline_scores.values())
        ):
            actual_beats = _pipeline_actually_beats(
                entry.pipeline_score,
                entry.baseline_scores,
                entry.comparison_direction,
            )
            if not actual_beats:
                warnings.append(
                    "pipeline_beats_all_baselines=True but pipeline score does not "
                    "actually outperform all baselines given the comparison_direction; "
                    "verify the verdict and scores"
                )

        if entry.p_value == P_VALUE_NOT_COMPUTED:
            warnings.append(
                "p_value=-1.0 (not computed); statistical significance of the "
                "comparison has not been established"
            )

        if (
            _is_finite(entry.effect_size)
            and abs(entry.effect_size) > LARGE_EFFECT_THRESHOLD
            and entry.p_value == P_VALUE_NOT_COMPUTED
        ):
            warnings.append(
                f"effect_size={entry.effect_size:.2f} is large (>{LARGE_EFFECT_THRESHOLD}) "
                "but p_value was not computed; large claimed effects require statistical validation"
            )

    passed = len(errors) == 0
    return BaselineComparisonResult(
        manifest_id=entry.manifest_id,
        batch_id=entry.batch_id,
        metric_name=entry.metric_name,
        pipeline_beats_all_baselines=entry.pipeline_beats_all_baselines,
        baseline_count=len(entry.baseline_scores),
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_baseline_comparison_dict(d: dict) -> BaselineComparisonResult:
    required_fields = [
        "manifest_id",
        "batch_id",
        "pipeline_version",
        "comparison_date",
        "metric_name",
        "pipeline_score",
        "baseline_scores",
        "pipeline_beats_all_baselines",
        "effect_size",
        "p_value",
        "comparison_direction",
        "notes",
        "reviewer",
    ]
    missing = [f for f in required_fields if f not in d]
    if missing:
        return BaselineComparisonResult(
            manifest_id=d.get("manifest_id", "UNKNOWN"),
            batch_id=d.get("batch_id", "UNKNOWN"),
            metric_name=d.get("metric_name", "UNKNOWN"),
            pipeline_beats_all_baselines=False,
            baseline_count=0,
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=True,
        )

    entry = BaselineComparisonEntry(
        manifest_id=d["manifest_id"],
        batch_id=d["batch_id"],
        pipeline_version=d["pipeline_version"],
        comparison_date=d["comparison_date"],
        metric_name=d["metric_name"],
        pipeline_score=float(d["pipeline_score"]),
        baseline_scores={k: float(v) for k, v in d["baseline_scores"].items()},
        pipeline_beats_all_baselines=bool(d["pipeline_beats_all_baselines"]),
        effect_size=float(d["effect_size"]),
        p_value=float(d["p_value"]),
        comparison_direction=d["comparison_direction"],
        notes=d["notes"],
        reviewer=d["reviewer"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_baseline_comparison(entry)

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

VALID_SCORING_METHODS: set[str] = {
    "additive_weighted",
    "geometric_mean",
    "harmonic_mean",
    "max_component",
    "min_component",
    "rank_aggregation",
}

MINIMUM_COMPONENTS: int = 2
WEIGHT_SUM_TOLERANCE: float = 0.01
DOMINANT_WEIGHT_THRESHOLD: float = 0.6
UNBALANCED_RATIO_THRESHOLD: float = 5.0
MAX_COMPONENTS_WARNING: int = 8
LOW_SCORE_FRACTION: float = 0.2


@dataclass
class ScoreDecompositionEntry:
    report_id: str
    batch_id: str
    candidate_id: str
    pipeline_version: str
    composite_score: float
    component_scores: Dict[str, float]
    component_weights: Dict[str, float]
    scoring_method: str
    score_range_min: float
    score_range_max: float
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class ScoreDecompositionResult:
    report_id: str
    batch_id: str
    candidate_id: str
    scoring_method: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_score_decomposition(entry: ScoreDecompositionEntry) -> ScoreDecompositionResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.report_id.startswith("SDR-"):
        errors.append(f"report_id must start with 'SDR-', got '{entry.report_id}'")

    if entry.score_range_min >= entry.score_range_max:
        errors.append(
            f"score_range_min ({entry.score_range_min}) must be less than "
            f"score_range_max ({entry.score_range_max})"
        )

    if not errors:
        if not (entry.score_range_min <= entry.composite_score <= entry.score_range_max):
            errors.append(
                f"composite_score {entry.composite_score} is outside "
                f"[{entry.score_range_min}, {entry.score_range_max}]"
            )

    if len(entry.component_scores) < MINIMUM_COMPONENTS:
        errors.append(
            f"component_scores must have at least {MINIMUM_COMPONENTS} components, "
            f"got {len(entry.component_scores)}"
        )

    score_keys = set(entry.component_scores.keys())
    weight_keys = set(entry.component_weights.keys())
    if score_keys != weight_keys:
        missing_in_weights = score_keys - weight_keys
        extra_in_weights = weight_keys - score_keys
        if missing_in_weights:
            errors.append(
                f"component_weights missing keys present in component_scores: "
                f"{sorted(missing_in_weights)}"
            )
        if extra_in_weights:
            errors.append(
                f"component_weights has keys not in component_scores: "
                f"{sorted(extra_in_weights)}"
            )

    if entry.component_weights:
        weight_sum = sum(entry.component_weights.values())
        if abs(weight_sum - 1.0) > WEIGHT_SUM_TOLERANCE:
            errors.append(
                f"component_weights must sum to 1.0 (tolerance ±{WEIGHT_SUM_TOLERANCE}), "
                f"got {weight_sum:.4f}"
            )

    if entry.scoring_method not in VALID_SCORING_METHODS:
        errors.append(
            f"scoring_method '{entry.scoring_method}' is not valid; "
            f"must be one of {sorted(VALID_SCORING_METHODS)}"
        )

    if not entry.reviewer:
        errors.append("reviewer must not be empty")

    if not entry.dry_lab_only:
        errors.append(
            "dry_lab_only must be True for score decomposition reports "
            "(computational scoring only)"
        )

    if not errors and entry.component_weights:
        weights = list(entry.component_weights.values())
        max_weight = max(weights)
        min_weight = min(weights)

        if max_weight > DOMINANT_WEIGHT_THRESHOLD:
            dominant_key = max(entry.component_weights, key=entry.component_weights.__getitem__)
            warnings.append(
                f"component '{dominant_key}' has weight {max_weight:.2f} > "
                f"{DOMINANT_WEIGHT_THRESHOLD}; composite score is dominated by one component"
            )

        if min_weight > 0 and max_weight / min_weight > UNBALANCED_RATIO_THRESHOLD:
            warnings.append(
                f"weight ratio max/min = {max_weight / min_weight:.1f} > "
                f"{UNBALANCED_RATIO_THRESHOLD}; scoring weights are highly unbalanced"
            )

        if len(entry.component_scores) > MAX_COMPONENTS_WARNING:
            warnings.append(
                f"{len(entry.component_scores)} components is complex (> {MAX_COMPONENTS_WARNING}); "
                "consider simplifying the scoring model"
            )

        if not errors:
            score_range = entry.score_range_max - entry.score_range_min
            low_threshold = entry.score_range_min + LOW_SCORE_FRACTION * score_range
            if entry.composite_score < low_threshold:
                warnings.append(
                    f"composite_score {entry.composite_score:.3f} is in the bottom "
                    f"{int(LOW_SCORE_FRACTION * 100)}% of the score range; "
                    "candidate is weakly ranked"
                )

    passed = len(errors) == 0
    return ScoreDecompositionResult(
        report_id=entry.report_id,
        batch_id=entry.batch_id,
        candidate_id=entry.candidate_id,
        scoring_method=entry.scoring_method,
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_score_decomposition_dict(d: dict) -> ScoreDecompositionResult:
    required_fields = [
        "report_id",
        "batch_id",
        "candidate_id",
        "pipeline_version",
        "composite_score",
        "component_scores",
        "component_weights",
        "scoring_method",
        "score_range_min",
        "score_range_max",
        "reviewer",
    ]
    missing = [f for f in required_fields if f not in d]
    if missing:
        return ScoreDecompositionResult(
            report_id=d.get("report_id", "UNKNOWN"),
            batch_id=d.get("batch_id", "UNKNOWN"),
            candidate_id=d.get("candidate_id", "UNKNOWN"),
            scoring_method=d.get("scoring_method", "UNKNOWN"),
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=True,
        )

    entry = ScoreDecompositionEntry(
        report_id=d["report_id"],
        batch_id=d["batch_id"],
        candidate_id=d["candidate_id"],
        pipeline_version=d["pipeline_version"],
        composite_score=float(d["composite_score"]),
        component_scores={k: float(v) for k, v in d["component_scores"].items()},
        component_weights={k: float(v) for k, v in d["component_weights"].items()},
        scoring_method=d["scoring_method"],
        score_range_min=float(d["score_range_min"]),
        score_range_max=float(d["score_range_max"]),
        reviewer=d["reviewer"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_score_decomposition(entry)

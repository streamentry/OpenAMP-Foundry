"""Adoption scorecard — aggregates Phase I adoption signals into a dashboard.

Measures real adoption readiness, not vanity metrics.
Dry-lab only.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

# Scorecard dimensions and their weights (must sum to 1.0)
SCORECARD_DIMENSIONS: dict[str, float] = {
    "integration_check": 0.25,
    "license_compliance": 0.20,
    "adapter_validation": 0.20,
    "schema_compatibility": 0.20,
    "contribution_readiness": 0.15,
}

ADOPTION_TIERS: dict[str, tuple[float, float]] = {
    "not_ready":   (0.0, 0.40),
    "emerging":    (0.40, 0.65),
    "established": (0.65, 0.85),
    "mature":      (0.85, 1.01),
}


@dataclass
class DimensionScore:
    dimension: str
    weight: float
    raw_score: float
    weighted_score: float
    passed_checks: int
    total_checks: int
    notes: str = ""
    dry_lab_only: bool = True


@dataclass
class AdoptionScorecard:
    total_score: float
    adoption_tier: str
    dimensions: list[DimensionScore]
    summary: str
    recommendations: list[str]
    dry_lab_only: bool = True


def compute_adoption_tier(score: float) -> str:
    for tier, (low, high) in ADOPTION_TIERS.items():
        if low <= score < high:
            return tier
    return "not_ready"


def build_scorecard(dimension_inputs: dict[str, dict[str, Any]]) -> AdoptionScorecard:
    dimensions: list[DimensionScore] = []
    total_weighted = 0.0
    recommendations: list[str] = []

    for dim_name, weight in SCORECARD_DIMENSIONS.items():
        inp = dimension_inputs.get(dim_name, {})
        passed = inp.get("passed_checks", 0)
        total = inp.get("total_checks", 0)
        notes = inp.get("notes", "")
        raw = passed / total if total > 0 else 0.0
        weighted = raw * weight
        total_weighted += weighted
        dimensions.append(DimensionScore(
            dimension=dim_name,
            weight=weight,
            raw_score=raw,
            weighted_score=weighted,
            passed_checks=passed,
            total_checks=total,
            notes=notes,
            dry_lab_only=True,
        ))
        if raw < 1.0 and total > 0:
            failed = total - passed
            recommendations.append(
                f"Fix {failed} failing check(s) in {dim_name} (current: {passed}/{total})"
            )

    tier = compute_adoption_tier(total_weighted)
    tier_descriptions = {
        "not_ready":   "Pipeline does not yet meet minimum adoption standards.",
        "emerging":    "Pipeline is emerging but has significant gaps.",
        "established": "Pipeline meets most adoption standards.",
        "mature":      "Pipeline is fully adoption-ready.",
    }
    summary = f"Adoption score: {total_weighted:.2f} ({tier}). {tier_descriptions[tier]}"

    return AdoptionScorecard(
        total_score=round(total_weighted, 4),
        adoption_tier=tier,
        dimensions=dimensions,
        summary=summary,
        recommendations=recommendations,
        dry_lab_only=True,
    )

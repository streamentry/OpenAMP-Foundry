"""Confidence interval reporter for simulation results.

Raw scores without uncertainty ranges make it impossible to judge
whether two candidates are distinguishable. A CI reporter makes the
uncertainty explicit and auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from .interfaces import SimulationResult


@dataclass
class ScoreCI:
    module_id: str
    score_key: str
    point_estimate: float
    uncertainty: float
    ci_lower: float
    ci_upper: float
    ci_width: float
    overlaps_with: list[str] = field(default_factory=list)
    dry_lab_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_score_ci(
    result: SimulationResult,
    score_key: str = "binding_energy",
) -> ScoreCI | None:
    """Return ScoreCI for the given score_key, or None if score_key missing.

    ci_lower = score - uncertainty, ci_upper = score + uncertainty.
    overlaps_with starts as empty list (populated by compare_cis).
    """
    if score_key not in result.scores:
        return None

    point_estimate = result.scores[score_key]
    uncertainty = result.uncertainty
    ci_lower = point_estimate - uncertainty
    ci_upper = point_estimate + uncertainty
    ci_width = ci_upper - ci_lower

    return ScoreCI(
        module_id=result.module,
        score_key=score_key,
        point_estimate=point_estimate,
        uncertainty=uncertainty,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        ci_width=ci_width,
    )


def compare_cis(
    cis: list[ScoreCI],
) -> list[ScoreCI]:
    """For each CI, populate overlaps_with with module_ids whose CIs overlap.

    Two CIs [a_lo, a_hi] and [b_lo, b_hi] overlap iff a_lo <= b_hi and b_lo <= a_hi.
    Returns new list of ScoreCI with overlaps_with populated (no in-place mutation).
    """
    result: list[ScoreCI] = []
    for i, ci_a in enumerate(cis):
        overlapping_ids: list[str] = []
        for j, ci_b in enumerate(cis):
            if i == j:
                continue
            if ci_a.ci_lower <= ci_b.ci_upper and ci_b.ci_lower <= ci_a.ci_upper:
                overlapping_ids.append(ci_b.module_id)
        result.append(ScoreCI(
            module_id=ci_a.module_id,
            score_key=ci_a.score_key,
            point_estimate=ci_a.point_estimate,
            uncertainty=ci_a.uncertainty,
            ci_lower=ci_a.ci_lower,
            ci_upper=ci_a.ci_upper,
            ci_width=ci_a.ci_width,
            overlaps_with=overlapping_ids,
            dry_lab_only=True,
        ))
    return result


def ci_report(
    results: list[SimulationResult],
    score_key: str = "binding_energy",
) -> dict:
    """Compute CIs for all results and compare them.

    Returns:
    - "score_key": str
    - "n_results": int
    - "cis": list of ScoreCI as dicts (with overlaps_with populated)
    - "any_overlap": bool  (True if any CI has at least one overlap)
    - "dry_lab_only": True
    """
    score_cis: list[ScoreCI] = []
    for result in results:
        ci = compute_score_ci(result, score_key=score_key)
        if ci is not None:
            score_cis.append(ci)

    compared = compare_cis(score_cis) if score_cis else []

    any_overlap = any(len(c.overlaps_with) > 0 for c in compared)

    return {
        "score_key": score_key,
        "n_results": len(results),
        "cis": [c.to_dict() for c in compared],
        "any_overlap": any_overlap,
        "dry_lab_only": True,
    }

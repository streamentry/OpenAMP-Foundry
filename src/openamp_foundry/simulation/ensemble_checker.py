"""Ensemble agreement checker for simulation modules.

When multiple simulation modules independently agree on a candidate,
that agreement is stronger evidence than a single module alone.
This module makes agreement explicit and auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from statistics import mean
from typing import Any

from .interfaces import SimulationResult


AGREEMENT_LEVELS: dict[str, str] = {
    "strong": "≥3 modules agree within threshold",
    "moderate": "2 modules agree within threshold",
    "weak": "Only 1 module; no ensemble signal",
    "conflict": "Modules disagree beyond threshold",
    "insufficient": "No results provided",
}


@dataclass
class EnsembleAgreementResult:
    sequence: str
    modules_checked: list[str]
    agreement_level: str
    agreement_description: str
    mean_score: float | None
    score_range: float | None
    scores_by_module: dict[str, float]
    threshold: float
    dry_lab_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_ensemble_agreement(
    sequence: str,
    results: list[SimulationResult],
    score_key: str = "binding_energy",
    threshold: float = 0.2,
) -> EnsembleAgreementResult:
    """Check agreement across multiple simulation results.

    Logic:
    - If results is empty -> agreement_level="insufficient"
    - Extract score_key from each result's scores dict (skip if missing)
    - If only 1 score found -> agreement_level="weak"
    - Compute score_range = max(scores) - min(scores)
    - If score_range <= threshold:
        n = len(scores)
        agreement_level = "strong" if n >= 3 else "moderate"
    - Else: agreement_level = "conflict"
    - mean_score = mean of available scores (None if 0 scores)
    - score_range = None if 0 scores
    - scores_by_module: dict mapping result.module -> score for results with score_key
    """
    modules_checked = [r.module for r in results]
    scores_by_module: dict[str, float] = {}

    for result in results:
        if score_key in result.scores:
            scores_by_module[result.module] = result.scores[score_key]

    scores = list(scores_by_module.values())
    n = len(scores)

    if n == 0:
        return EnsembleAgreementResult(
            sequence=sequence,
            modules_checked=modules_checked,
            agreement_level="insufficient",
            agreement_description=AGREEMENT_LEVELS["insufficient"],
            mean_score=None,
            score_range=None,
            scores_by_module=scores_by_module,
            threshold=threshold,
        )

    if n == 1:
        score = scores[0]
        return EnsembleAgreementResult(
            sequence=sequence,
            modules_checked=modules_checked,
            agreement_level="weak",
            agreement_description=AGREEMENT_LEVELS["weak"],
            mean_score=score,
            score_range=0.0,
            scores_by_module=scores_by_module,
            threshold=threshold,
        )

    score_range_val = max(scores) - min(scores)
    mean_score_val = mean(scores)

    if score_range_val <= threshold:
        agreement_key = "strong" if n >= 3 else "moderate"
    else:
        agreement_key = "conflict"

    return EnsembleAgreementResult(
        sequence=sequence,
        modules_checked=modules_checked,
        agreement_level=agreement_key,
        agreement_description=AGREEMENT_LEVELS[agreement_key],
        mean_score=mean_score_val,
        score_range=score_range_val,
        scores_by_module=scores_by_module,
        threshold=threshold,
    )


def run_ensemble_check_batch(
    calls: list[dict],
) -> dict:
    """Run ensemble agreement checks for a batch of calls.

    Each call dict has:
    - "sequence": str (required)
    - "results": list[SimulationResult] (required)
    - "score_key": str (optional, default "binding_energy")
    - "threshold": float (optional, default 0.2)

    Returns dict with:
    - total, strong, moderate, weak, conflict, insufficient counts
    - any_conflict: True if any call returns "conflict"
    - results: list[EnsembleAgreementResult as dict]
    - dry_lab_only: True
    """
    results_list: list[EnsembleAgreementResult] = []
    counts: dict[str, int] = {
        "strong": 0,
        "moderate": 0,
        "weak": 0,
        "conflict": 0,
        "insufficient": 0,
    }

    for call in calls:
        result = check_ensemble_agreement(
            sequence=call["sequence"],
            results=call["results"],
            score_key=call.get("score_key", "binding_energy"),
            threshold=call.get("threshold", 0.2),
        )
        results_list.append(result)
        counts[result.agreement_level] += 1

    return {
        "total": len(calls),
        "strong": counts["strong"],
        "moderate": counts["moderate"],
        "weak": counts["weak"],
        "conflict": counts["conflict"],
        "insufficient": counts["insufficient"],
        "any_conflict": counts["conflict"] > 0,
        "results": [r.to_dict() for r in results_list],
        "dry_lab_only": True,
    }

from __future__ import annotations

from openamp_foundry.types import ScoredCandidate


def rank_candidates(
    candidates: list[ScoredCandidate],
    ranking_mode: str = "ensemble",
) -> list[ScoredCandidate]:
    """Rank candidates by the specified scoring mode.

    Args:
        candidates: List of ScoredCandidate objects.
        ranking_mode: "ensemble" (default) or "expert". The expert mode
            ranks by the expert composite score, which incorporates
            selectivity, hemolysis risk, and helix-hinge analysis. It is a
            safety-aware alternative ranking, not a validated safety predictor;
            benchmark evidence must be checked before giving it selection authority.

    Returns:
        Candidates sorted by the chosen score, highest first.
    """
    key = "expert_composite" if ranking_mode == "expert" else "ensemble"
    return sorted(candidates, key=lambda c: c.scores.get(key, 0.0), reverse=True)


def select_top(
    candidates: list[ScoredCandidate],
    top_n: int,
    ranking_mode: str = "ensemble",
) -> list[ScoredCandidate]:
    return rank_candidates(candidates, ranking_mode=ranking_mode)[:top_n]

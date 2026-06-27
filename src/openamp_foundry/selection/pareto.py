from __future__ import annotations

from openamp_foundry.types import ScoredCandidate


def rank_candidates(candidates: list[ScoredCandidate]) -> list[ScoredCandidate]:
    return sorted(candidates, key=lambda c: c.scores.get("ensemble", 0.0), reverse=True)


def select_top(candidates: list[ScoredCandidate], top_n: int) -> list[ScoredCandidate]:
    return rank_candidates(candidates)[:top_n]

from __future__ import annotations

from openamp_foundry.types import ScoredCandidate


def top_k_ids(scored: list[ScoredCandidate], k: int) -> set[str]:
    ranked = sorted(scored, key=lambda x: x.scores.get("ensemble", 0.0), reverse=True)
    return {item.candidate.candidate_id for item in ranked[:k]}

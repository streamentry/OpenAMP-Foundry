from __future__ import annotations

from openamp_foundry.scoring.novelty import normalized_similarity
from openamp_foundry.types import ScoredCandidate


def greedy_diverse_select(
    ranked: list[ScoredCandidate], top_n: int, max_pairwise_similarity: float = 0.85
) -> list[ScoredCandidate]:
    selected: list[ScoredCandidate] = []
    for cand in ranked:
        if len(selected) >= top_n:
            break
        if all(
            normalized_similarity(cand.candidate.sequence, chosen.candidate.sequence)
            <= max_pairwise_similarity
            for chosen in selected
        ):
            selected.append(cand)
    return selected

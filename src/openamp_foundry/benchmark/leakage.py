from __future__ import annotations

from openamp_foundry.scoring.novelty import normalized_similarity
from openamp_foundry.types import PeptideCandidate


def find_near_duplicates(
    candidates: list[PeptideCandidate], references: list[PeptideCandidate], threshold: float = 0.90
) -> list[dict]:
    hits: list[dict] = []
    for cand in candidates:
        for ref in references:
            sim = normalized_similarity(cand.sequence, ref.sequence)
            if sim >= threshold:
                hits.append(
                    {
                        "candidate_id": cand.candidate_id,
                        "reference_id": ref.candidate_id,
                        "similarity": round(sim, 4),
                    }
                )
    return hits

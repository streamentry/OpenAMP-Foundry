from __future__ import annotations

from openamp_foundry.types import PeptideCandidate


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cur.append(
                min(
                    prev[j] + 1,
                    cur[j - 1] + 1,
                    prev[j - 1] + (0 if ca == cb else 1),
                )
            )
        prev = cur
    return prev[-1]


def normalized_similarity(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    denom = max(len(a), len(b), 1)
    return 1.0 - levenshtein(a, b) / denom


def novelty_score(sequence: str, references: list[PeptideCandidate]) -> tuple[float, dict | None]:
    if not references:
        return 1.0, None
    best_ref = None
    best_sim = -1.0
    for ref in references:
        sim = normalized_similarity(sequence, ref.sequence)
        if sim > best_sim:
            best_sim = sim
            best_ref = ref
    novelty = 1.0 - max(best_sim, 0.0)
    nearest = None
    if best_ref is not None:
        nearest = {
            "candidate_id": best_ref.candidate_id,
            "source": best_ref.source,
            "similarity": round(best_sim, 4),
            "sequence": best_ref.sequence,
        }
    return round(max(0.0, min(1.0, novelty)), 4), nearest

from __future__ import annotations

from openamp_foundry.scoring.novelty import normalized_similarity
from openamp_foundry.types import ScoredCandidate


def top_k_ids(scored: list[ScoredCandidate], k: int) -> set[str]:
    ranked = sorted(scored, key=lambda x: x.scores.get("ensemble", 0.0), reverse=True)
    return {item.candidate.candidate_id for item in ranked[:k]}


def recall_at_k(
    scored: list[ScoredCandidate],
    positive_ids: set[str],
    k: int,
) -> float:
    """Fraction of known positives recovered in the top-k ranked candidates.

    Recall@k = |positives in top-k| / |total positives|

    A random baseline would recover roughly k / |all candidates| of the positives.
    The pipeline is meaningful if recall@k significantly exceeds the random baseline.
    """
    if not positive_ids:
        return 0.0
    top = top_k_ids(scored, k)
    recovered = len(top & positive_ids)
    return round(recovered / len(positive_ids), 4)


def random_recall_at_k(n_candidates: int, n_positives: int, k: int) -> float:
    """Expected recall@k for a random ranker.

    E[recall@k] = min(k, n_positives) / n_positives when sampling without replacement.
    """
    if n_positives == 0 or n_candidates == 0:
        return 0.0
    expected_hits = min(k, n_positives) * min(k, n_candidates) / max(n_candidates, 1)
    return round(min(1.0, expected_hits / n_positives), 4)


def enrichment_factor(
    scored: list[ScoredCandidate],
    positive_ids: set[str],
    k: int,
) -> float:
    """Enrichment factor at k: recall@k relative to random baseline recall@k.

    EF > 1.0 means the pipeline outperforms random.
    EF = 1.0 is random.
    EF < 1.0 is worse than random (anti-enrichment).
    """
    n = len(scored)
    n_pos = len(positive_ids)
    rc = recall_at_k(scored, positive_ids, k)
    random_rc = random_recall_at_k(n, n_pos, k)
    if random_rc == 0.0:
        return 0.0
    return round(rc / random_rc, 4)


def benchmark_summary(
    scored: list[ScoredCandidate],
    positive_ids: set[str],
    ks: list[int] | None = None,
) -> dict:
    """Produce a benchmark summary comparing pipeline vs random ranker.

    Returns recall@k and enrichment factor at each k, plus a verdict.
    All results are computational only — they do not prove biological activity.
    """
    if ks is None:
        n = len(scored)
        ks = sorted({max(1, n // 10), max(1, n // 5), max(1, n // 2), n})

    results = []
    for k in ks:
        rc = recall_at_k(scored, positive_ids, k)
        rrc = random_recall_at_k(len(scored), len(positive_ids), k)
        ef = enrichment_factor(scored, positive_ids, k)
        results.append(
            {
                "k": k,
                "recall_at_k": rc,
                "random_recall_at_k": rrc,
                "enrichment_factor": ef,
            }
        )

    any_enrichment = any(r["enrichment_factor"] > 1.0 for r in results)
    verdict = "pipeline outperforms random" if any_enrichment else "pipeline does not outperform random"

    return {
        "disclaimer": (
            "These are retrospective benchmark results on demo data. "
            "They do not prove biological efficacy. "
            "They only measure whether the pipeline recovers known positives "
            "better than a random ranker would."
        ),
        "n_candidates": len(scored),
        "n_positives": len(positive_ids),
        "results": results,
        "verdict": verdict,
    }


def find_contaminated_references(
    candidate_sequences: list[str],
    reference_sequences: list[str],
    positive_ids: set[str],
    candidate_ids: list[str],
    threshold: float = 0.70,
) -> set[int]:
    """Return indices of references that are near-duplicates of test positives.

    Used to build a cluster-split reference set: removing contaminated references
    ensures benchmark performance is not inflated by reference-set memorization.
    """
    contaminated: set[int] = set()
    positive_seqs = {
        seq
        for seq, cid in zip(candidate_sequences, candidate_ids)
        if cid in positive_ids
    }
    for ref_idx, ref_seq in enumerate(reference_sequences):
        for pos_seq in positive_seqs:
            if normalized_similarity(ref_seq, pos_seq) >= threshold:
                contaminated.add(ref_idx)
                break
    return contaminated

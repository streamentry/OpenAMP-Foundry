from __future__ import annotations

from openamp_foundry.scoring.novelty import normalized_similarity
from openamp_foundry.types import PeptideCandidate


def deterministic_split(
    candidates: list[PeptideCandidate], holdout_mod: int = 5
) -> tuple[list[PeptideCandidate], list[PeptideCandidate]]:
    train: list[PeptideCandidate] = []
    holdout: list[PeptideCandidate] = []
    for i, cand in enumerate(candidates):
        if i % holdout_mod == 0:
            holdout.append(cand)
        else:
            train.append(cand)
    return train, holdout


def cluster_by_similarity(
    sequences: list[str],
    threshold: float = 0.70,
) -> list[list[int]]:
    """Greedy single-linkage clustering: sequences within threshold go to the same cluster.

    Returns a list of clusters, where each cluster is a list of indices into `sequences`.
    The first sequence assigned to a cluster becomes its center for subsequent comparisons.
    threshold: sequences with normalized_similarity >= threshold are co-clustered.
    """
    clusters: list[list[int]] = []
    centers: list[str] = []

    for idx, seq in enumerate(sequences):
        assigned = False
        for ci, center in enumerate(centers):
            if normalized_similarity(seq, center) >= threshold:
                clusters[ci].append(idx)
                assigned = True
                break
        if not assigned:
            clusters.append([idx])
            centers.append(seq)

    return clusters


def cluster_split(
    sequences: list[str],
    threshold: float = 0.70,
) -> tuple[list[int], list[int]]:
    """Split sequences into reference and test partitions by cluster membership.

    The first member of each cluster becomes the reference representative.
    All subsequent cluster members become test (held-out) sequences.

    This ensures no test sequence has a near-duplicate in the reference set,
    preventing benchmark inflation from reference-set memorization.

    Returns (reference_indices, test_indices).
    """
    clusters = cluster_by_similarity(sequences, threshold)
    reference_indices: list[int] = []
    test_indices: list[int] = []
    for cluster in clusters:
        reference_indices.append(cluster[0])
        test_indices.extend(cluster[1:])
    return reference_indices, test_indices

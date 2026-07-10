from __future__ import annotations
from dataclasses import dataclass, field


SIMILARITY_SHORTCUT_THRESHOLD = 0.80
SHORTCUT_FRACTION_THRESHOLD = 0.50


def _sequence_similarity(seq_a: str, seq_b: str) -> float:
    """Compute simple character-overlap similarity (Jaccard on amino acid counts)."""
    if not seq_a or not seq_b:
        return 0.0
    len_a = len(seq_a)
    len_b = len(seq_b)
    matches = sum(1 for a, b in zip(seq_a, seq_b) if a == b)
    longer = max(len_a, len_b)
    return matches / longer


def _nearest_neighbor_similarity(query: str, references: list[str]) -> float:
    """Return the highest similarity between query and any reference."""
    if not references:
        return 0.0
    return max(_sequence_similarity(query, ref) for ref in references)


@dataclass
class SimilarityNeighborReport:
    n_positives: int
    n_negatives: int
    n_references: int
    positive_nn_similarities: list[float] = field(default_factory=list)
    negative_nn_similarities: list[float] = field(default_factory=list)
    positive_mean_nn: float = 0.0
    positive_median_nn: float = 0.0
    negative_mean_nn: float = 0.0
    negative_median_nn: float = 0.0
    positive_high_similarity_fraction: float = 0.0
    negative_high_similarity_fraction: float = 0.0
    novelty_shortcut_likely: bool = False
    shortcut_explanation: str = ""
    similarity_threshold_used: float = SIMILARITY_SHORTCUT_THRESHOLD
    shortcut_fraction_threshold: float = SHORTCUT_FRACTION_THRESHOLD


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 0:
        return (s[mid - 1] + s[mid]) / 2.0
    return s[mid]


def _high_similarity_fraction(similarities: list[float], threshold: float) -> float:
    if not similarities:
        return 0.0
    return sum(1 for s in similarities if s >= threshold) / len(similarities)


def compute_similarity_report(
    sequences: list[str],
    labels: list[int],
    reference_sequences: list[str],
    similarity_threshold: float = SIMILARITY_SHORTCUT_THRESHOLD,
    shortcut_fraction_threshold: float = SHORTCUT_FRACTION_THRESHOLD,
) -> SimilarityNeighborReport:
    """Compute nearest-neighbor similarity report between benchmark sequences and references.

    Args:
        sequences: List of amino acid sequences in the benchmark.
        labels: Binary labels (1=positive/AMP, 0=negative/non-AMP) for each sequence.
        reference_sequences: Known AMP reference sequences to compare against.
        similarity_threshold: Fraction similarity above which a sequence is "high-similarity."
        shortcut_fraction_threshold: Fraction of positives above threshold that triggers novelty shortcut warning.

    Returns:
        SimilarityNeighborReport with per-group statistics and shortcut flag.

    Raises:
        ValueError: If sequences and labels have different lengths.
    """
    if len(sequences) != len(labels):
        raise ValueError(
            f"sequences and labels must have the same length, "
            f"got {len(sequences)} and {len(labels)}"
        )

    positives = [seq for seq, lbl in zip(sequences, labels) if lbl == 1]
    negatives = [seq for seq, lbl in zip(sequences, labels) if lbl == 0]

    pos_nn = [_nearest_neighbor_similarity(seq, reference_sequences) for seq in positives]
    neg_nn = [_nearest_neighbor_similarity(seq, reference_sequences) for seq in negatives]

    pos_high_frac = _high_similarity_fraction(pos_nn, similarity_threshold)
    neg_high_frac = _high_similarity_fraction(neg_nn, similarity_threshold)

    novelty_shortcut_likely = pos_high_frac >= shortcut_fraction_threshold

    if novelty_shortcut_likely:
        explanation = (
            f"{pos_high_frac:.1%} of positives have nearest-neighbor similarity "
            f">= {similarity_threshold:.0%} to reference AMPs "
            f"(threshold: {shortcut_fraction_threshold:.0%}). "
            "Benchmark improvements may reflect similarity to known AMPs, not genuine novelty."
        )
    else:
        explanation = (
            f"No novelty shortcut detected: only {pos_high_frac:.1%} of positives "
            f"have nearest-neighbor similarity >= {similarity_threshold:.0%} to references."
        )

    return SimilarityNeighborReport(
        n_positives=len(positives),
        n_negatives=len(negatives),
        n_references=len(reference_sequences),
        positive_nn_similarities=pos_nn,
        negative_nn_similarities=neg_nn,
        positive_mean_nn=_mean(pos_nn),
        positive_median_nn=_median(pos_nn),
        negative_mean_nn=_mean(neg_nn),
        negative_median_nn=_median(neg_nn),
        positive_high_similarity_fraction=pos_high_frac,
        negative_high_similarity_fraction=neg_high_frac,
        novelty_shortcut_likely=novelty_shortcut_likely,
        shortcut_explanation=explanation,
        similarity_threshold_used=similarity_threshold,
        shortcut_fraction_threshold=shortcut_fraction_threshold,
    )


def format_similarity_report(report: SimilarityNeighborReport) -> str:
    """Format a SimilarityNeighborReport as a human-readable string."""
    lines = [
        "=== SIMILARITY-NEIGHBOR DISTRIBUTION REPORT ===",
        f"Sequences: {report.n_positives} positives, {report.n_negatives} negatives",
        f"Reference database size: {report.n_references} sequences",
        f"Similarity threshold: {report.similarity_threshold_used:.0%}",
        "",
        "-- POSITIVE (AMP) NEAREST-NEIGHBOR SIMILARITY TO REFERENCES --",
        f"  Mean:   {report.positive_mean_nn:.4f}",
        f"  Median: {report.positive_median_nn:.4f}",
        f"  Fraction >= threshold: {report.positive_high_similarity_fraction:.1%}",
        "",
        "-- NEGATIVE (non-AMP) NEAREST-NEIGHBOR SIMILARITY TO REFERENCES --",
        f"  Mean:   {report.negative_mean_nn:.4f}",
        f"  Median: {report.negative_median_nn:.4f}",
        f"  Fraction >= threshold: {report.negative_high_similarity_fraction:.1%}",
        "",
        f"NOVELTY SHORTCUT LIKELY: {'YES -- see explanation below' if report.novelty_shortcut_likely else 'no'}",
        "",
        report.shortcut_explanation,
        "",
        "NOTICE: Similarity computed as character-overlap (positional match / max length).",
        "Use a full alignment tool for publication-grade analysis.",
    ]
    return "\n".join(lines)

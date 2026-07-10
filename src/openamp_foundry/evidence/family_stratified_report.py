"""Family-stratified precision@k report — Phase C C7.

Evaluates whether benchmark precision@k is inflated by over-representation
of a single AMP family. If one family dominates the top-k predictions,
apparent performance may be a family-fitting artifact rather than genuine
activity prediction.

Raises 'family_inflation_likely' when the top-k ranked sequences are
disproportionately drawn from a single family.
"""

from __future__ import annotations

from dataclasses import dataclass, field


FAMILY_INFLATION_FRACTION_THRESHOLD = 0.50
FAMILY_INFLATION_DOMINANCE_THRESHOLD = 0.60


@dataclass
class FamilyStratifiedReport:
    k: int
    n_sequences: int
    n_families: int
    top_k_family_counts: dict[str, int] = field(default_factory=dict)
    top_k_family_fractions: dict[str, float] = field(default_factory=dict)
    dominant_family: str = ""
    dominant_family_fraction: float = 0.0
    family_inflation_likely: bool = False
    inflation_explanation: str = ""
    dominance_threshold: float = FAMILY_INFLATION_DOMINANCE_THRESHOLD
    fraction_threshold: float = FAMILY_INFLATION_FRACTION_THRESHOLD
    precision_at_k: float = 0.0
    family_precision_at_k: dict[str, float] = field(default_factory=dict)


def _precision_at_k(labels: list[int], k: int) -> float:
    """Compute precision@k: fraction of true positives in top-k ranked items."""
    if k <= 0 or not labels:
        return 0.0
    top = labels[:k]
    return sum(top) / len(top)


def _family_counts_in_top_k(
    families: list[str], k: int
) -> dict[str, int]:
    """Count occurrences of each family in the top-k ranked items."""
    top = families[:k]
    counts: dict[str, int] = {}
    for fam in top:
        counts[fam] = counts.get(fam, 0) + 1
    return counts


def _family_fractions(counts: dict[str, int], k: int) -> dict[str, float]:
    """Convert counts to fractions of top-k."""
    if k <= 0:
        return {}
    return {fam: count / k for fam, count in counts.items()}


def compute_family_stratified_report(
    sequences: list[str],
    labels: list[int],
    families: list[str],
    k: int,
    dominance_threshold: float = FAMILY_INFLATION_DOMINANCE_THRESHOLD,
    fraction_threshold: float = FAMILY_INFLATION_FRACTION_THRESHOLD,
) -> FamilyStratifiedReport:
    """Compute family-stratified precision@k report.

    Args:
        sequences: Amino acid sequences in ranked order (index 0 = top-ranked).
        labels: Binary labels (1=positive/AMP, 0=negative) in ranked order.
        families: AMP family label for each sequence (e.g. "defensin", "cathelicidin").
        k: Number of top-ranked sequences to evaluate.
        dominance_threshold: Fraction of top-k from single family that flags inflation.
        fraction_threshold: Minimum fraction of any one family in top-k to trigger check.

    Returns:
        FamilyStratifiedReport with per-family statistics and inflation flag.

    Raises:
        ValueError: If sequences, labels, and families have different lengths.
        ValueError: If k <= 0.
    """
    if len(sequences) != len(labels):
        raise ValueError(
            f"sequences and labels must have the same length, "
            f"got {len(sequences)} and {len(labels)}"
        )
    if len(sequences) != len(families):
        raise ValueError(
            f"sequences and families must have the same length, "
            f"got {len(sequences)} and {len(families)}"
        )
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")

    effective_k = min(k, len(sequences))
    n_families = len(set(families)) if families else 0

    pak = _precision_at_k(labels, effective_k)
    top_counts = _family_counts_in_top_k(families, effective_k)
    top_fracs = _family_fractions(top_counts, effective_k)

    dominant_family = ""
    dominant_fraction = 0.0
    if top_fracs:
        dominant_family = max(top_fracs, key=lambda f: top_fracs[f])
        dominant_fraction = top_fracs[dominant_family]

    family_inflation_likely = (
        dominant_fraction >= dominance_threshold
        and dominant_fraction >= fraction_threshold
    )

    # Compute per-family precision@k (fraction of that family's top-k entries that are positive)
    family_pak: dict[str, float] = {}
    top_labels = labels[:effective_k]
    top_families = families[:effective_k]
    for fam in set(top_families):
        fam_labels = [lbl for lbl, f in zip(top_labels, top_families) if f == fam]
        family_pak[fam] = sum(fam_labels) / len(fam_labels) if fam_labels else 0.0

    if family_inflation_likely:
        explanation = (
            f"Family '{dominant_family}' accounts for {dominant_fraction:.1%} of top-{effective_k} "
            f"ranked sequences (threshold: {dominance_threshold:.0%}). "
            f"Precision@{effective_k}={pak:.3f} may be inflated by within-family fitting, "
            "not genuine cross-family activity prediction."
        )
    else:
        explanation = (
            f"No family inflation detected: dominant family '{dominant_family}' "
            f"accounts for only {dominant_fraction:.1%} of top-{effective_k} "
            f"(threshold: {dominance_threshold:.0%}). "
            f"Precision@{effective_k}={pak:.3f}."
        )

    return FamilyStratifiedReport(
        k=effective_k,
        n_sequences=len(sequences),
        n_families=n_families,
        top_k_family_counts=top_counts,
        top_k_family_fractions=top_fracs,
        dominant_family=dominant_family,
        dominant_family_fraction=dominant_fraction,
        family_inflation_likely=family_inflation_likely,
        inflation_explanation=explanation,
        dominance_threshold=dominance_threshold,
        fraction_threshold=fraction_threshold,
        precision_at_k=pak,
        family_precision_at_k=family_pak,
    )


def format_family_stratified_report(report: FamilyStratifiedReport) -> str:
    """Format a FamilyStratifiedReport as a human-readable string."""
    lines = [
        "=== FAMILY-STRATIFIED PRECISION@K REPORT ===",
        f"Sequences: {report.n_sequences} total, {report.n_families} families",
        f"k = {report.k}",
        f"Precision@{report.k} = {report.precision_at_k:.4f}",
        "",
        f"-- TOP-{report.k} FAMILY BREAKDOWN --",
    ]
    for fam, frac in sorted(report.top_k_family_fractions.items(), key=lambda x: -x[1]):
        count = report.top_k_family_counts.get(fam, 0)
        lines.append(f"  {fam}: {count} / {report.k} ({frac:.1%})")
    if report.family_precision_at_k:
        lines.append("")
        lines.append(f"-- PER-FAMILY PRECISION@{report.k} (within top-k) --")
        for fam, pak in sorted(report.family_precision_at_k.items()):
            lines.append(f"  {fam}: {pak:.4f}")
    lines.extend([
        "",
        f"Dominant family: '{report.dominant_family}' ({report.dominant_family_fraction:.1%})",
        f"Dominance threshold: {report.dominance_threshold:.0%}",
        f"FAMILY INFLATION LIKELY: {'YES -- see explanation below' if report.family_inflation_likely else 'no'}",
        "",
        report.inflation_explanation,
        "",
        "NOTICE: Family-stratified analysis requires reliable family annotations.",
        "Use cross-family split (BMC-0004) for publication-grade leakage testing.",
    ])
    return "\n".join(lines)

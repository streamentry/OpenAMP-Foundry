"""Length distribution report — Phase C C5.

Detects whether benchmark improvements could be explained by a length shortcut:
the model predicts positives because AMPs tend to be 10–40 residues long,
not because of genuine activity signal.

Raises a 'length_shortcut_likely' flag when the fraction of positives in the
typical AMP length range significantly exceeds the fraction of negatives in the
same range.
"""

from __future__ import annotations

from dataclasses import dataclass, field


AMP_LENGTH_MIN = 10
AMP_LENGTH_MAX = 40
SHORTCUT_RATIO_THRESHOLD = 1.5
SHORTCUT_FRACTION_THRESHOLD = 0.60


@dataclass
class LengthDistributionReport:
    n_positives: int
    n_negatives: int
    positive_lengths: list[int] = field(default_factory=list)
    negative_lengths: list[int] = field(default_factory=list)
    positive_mean_length: float = 0.0
    positive_median_length: float = 0.0
    negative_mean_length: float = 0.0
    negative_median_length: float = 0.0
    positive_in_amp_range_fraction: float = 0.0
    negative_in_amp_range_fraction: float = 0.0
    length_ratio: float = 0.0
    length_shortcut_likely: bool = False
    shortcut_explanation: str = ""
    amp_length_min: int = AMP_LENGTH_MIN
    amp_length_max: int = AMP_LENGTH_MAX
    ratio_threshold: float = SHORTCUT_RATIO_THRESHOLD
    fraction_threshold: float = SHORTCUT_FRACTION_THRESHOLD


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


def _in_range_fraction(lengths: list[int], lo: int, hi: int) -> float:
    if not lengths:
        return 0.0
    return sum(1 for ln in lengths if lo <= ln <= hi) / len(lengths)


def compute_length_report(
    sequences: list[str],
    labels: list[int],
    amp_length_min: int = AMP_LENGTH_MIN,
    amp_length_max: int = AMP_LENGTH_MAX,
    ratio_threshold: float = SHORTCUT_RATIO_THRESHOLD,
    fraction_threshold: float = SHORTCUT_FRACTION_THRESHOLD,
) -> LengthDistributionReport:
    """Compute length-distribution shortcut report for a benchmark dataset.

    Args:
        sequences: Amino acid sequences in the benchmark.
        labels: Binary labels (1=positive/AMP, 0=negative/non-AMP).
        amp_length_min: Lower bound of typical AMP length range.
        amp_length_max: Upper bound of typical AMP length range.
        ratio_threshold: Ratio of pos/neg in-range fraction above which shortcut is flagged.
        fraction_threshold: Fraction of positives in range above which shortcut is flagged
                            (combined with ratio check).

    Returns:
        LengthDistributionReport with per-group statistics and shortcut flag.

    Raises:
        ValueError: If sequences and labels have different lengths.
    """
    if len(sequences) != len(labels):
        raise ValueError(
            f"sequences and labels must have the same length, "
            f"got {len(sequences)} and {len(labels)}"
        )

    pos_lengths = [len(seq) for seq, lbl in zip(sequences, labels) if lbl == 1]
    neg_lengths = [len(seq) for seq, lbl in zip(sequences, labels) if lbl == 0]

    pos_frac = _in_range_fraction(pos_lengths, amp_length_min, amp_length_max)
    neg_frac = _in_range_fraction(neg_lengths, amp_length_min, amp_length_max)

    if neg_frac > 0:
        ratio = pos_frac / neg_frac
    elif pos_frac > 0:
        ratio = float("inf")
    else:
        ratio = 1.0

    length_shortcut_likely = (
        pos_frac >= fraction_threshold
        and (ratio >= ratio_threshold or neg_frac == 0.0)
    )

    if length_shortcut_likely:
        if neg_frac == 0.0:
            explanation = (
                f"{pos_frac:.1%} of positives fall in the AMP length range "
                f"[{amp_length_min}, {amp_length_max}] while 0.0% of negatives do. "
                "Length is a perfect separator — benchmark improvements may reflect "
                "the length shortcut, not genuine activity signal."
            )
        else:
            explanation = (
                f"{pos_frac:.1%} of positives vs {neg_frac:.1%} of negatives "
                f"fall in the AMP length range [{amp_length_min}, {amp_length_max}] "
                f"(ratio: {ratio:.2f}x, threshold: {ratio_threshold:.1f}x). "
                "Benchmark improvements may reflect the length shortcut, "
                "not genuine activity signal."
            )
    else:
        explanation = (
            f"No length shortcut detected: {pos_frac:.1%} of positives vs "
            f"{neg_frac:.1%} of negatives in range [{amp_length_min}, {amp_length_max}] "
            f"(ratio: {ratio:.2f}x, threshold: {ratio_threshold:.1f}x)."
        )

    return LengthDistributionReport(
        n_positives=len(pos_lengths),
        n_negatives=len(neg_lengths),
        positive_lengths=pos_lengths,
        negative_lengths=neg_lengths,
        positive_mean_length=_mean([float(x) for x in pos_lengths]),
        positive_median_length=_median([float(x) for x in pos_lengths]),
        negative_mean_length=_mean([float(x) for x in neg_lengths]),
        negative_median_length=_median([float(x) for x in neg_lengths]),
        positive_in_amp_range_fraction=pos_frac,
        negative_in_amp_range_fraction=neg_frac,
        length_ratio=ratio,
        length_shortcut_likely=length_shortcut_likely,
        shortcut_explanation=explanation,
        amp_length_min=amp_length_min,
        amp_length_max=amp_length_max,
        ratio_threshold=ratio_threshold,
        fraction_threshold=fraction_threshold,
    )


def format_length_report(report: LengthDistributionReport) -> str:
    """Format a LengthDistributionReport as a human-readable string."""
    ratio_str = (
        f"{report.length_ratio:.2f}x"
        if report.length_ratio != float("inf")
        else "inf (no negatives in range)"
    )
    lines = [
        "=== LENGTH DISTRIBUTION REPORT ===",
        f"Sequences: {report.n_positives} positives, {report.n_negatives} negatives",
        f"AMP length range: [{report.amp_length_min}, {report.amp_length_max}]",
        "",
        "-- POSITIVE (AMP) LENGTH STATS --",
        f"  Mean:   {report.positive_mean_length:.2f}",
        f"  Median: {report.positive_median_length:.2f}",
        f"  Fraction in AMP range: {report.positive_in_amp_range_fraction:.1%}",
        "",
        "-- NEGATIVE (non-AMP) LENGTH STATS --",
        f"  Mean:   {report.negative_mean_length:.2f}",
        f"  Median: {report.negative_median_length:.2f}",
        f"  Fraction in AMP range: {report.negative_in_amp_range_fraction:.1%}",
        "",
        f"Pos/neg in-range ratio: {ratio_str}",
        f"LENGTH SHORTCUT LIKELY: {'YES -- see explanation below' if report.length_shortcut_likely else 'no'}",
        "",
        report.shortcut_explanation,
        "",
        "NOTICE: Length is one of several cheap-explanation dimensions.",
        "Combine with charge and similarity reports for full shortcut audit.",
    ]
    return "\n".join(lines)

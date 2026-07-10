"""Combined charge-length shortcut report — Phase C C6.

Tests whether benchmark improvements can be explained by the conjunction of
two cheap heuristics: short length (10-40 aa) AND positive charge (>=4).
A sequence that satisfies BOTH heuristics simultaneously is a strong cheap
AMP predictor and represents the strongest one-feature explanation for
apparent model skill.

Raises 'combined_shortcut_likely' when the positive group has a significantly
higher fraction of charge-AND-length-matched sequences than the negative group.
"""

from __future__ import annotations

from dataclasses import dataclass, field


COMBINED_CHARGE_THRESHOLD = 4
COMBINED_LENGTH_MIN = 10
COMBINED_LENGTH_MAX = 40
COMBINED_SHORTCUT_RATIO_THRESHOLD = 1.5
COMBINED_SHORTCUT_FRACTION_THRESHOLD = 0.50


def _net_charge_proxy(sequence: str) -> float:
    """Estimate net charge: count K/R as +1, D/E as -1."""
    pos = sequence.upper().count("K") + sequence.upper().count("R")
    neg = sequence.upper().count("D") + sequence.upper().count("E")
    return float(pos - neg)


def _is_charge_length_match(
    sequence: str,
    charge_threshold: float,
    length_min: int,
    length_max: int,
) -> bool:
    """Return True if sequence satisfies both charge and length criteria."""
    return (
        _net_charge_proxy(sequence) >= charge_threshold
        and length_min <= len(sequence) <= length_max
    )


@dataclass
class ChargeLengthReport:
    n_positives: int
    n_negatives: int
    positive_combined_match_fraction: float = 0.0
    negative_combined_match_fraction: float = 0.0
    combined_ratio: float = 0.0
    combined_shortcut_likely: bool = False
    shortcut_explanation: str = ""
    charge_threshold: float = COMBINED_CHARGE_THRESHOLD
    length_min: int = COMBINED_LENGTH_MIN
    length_max: int = COMBINED_LENGTH_MAX
    ratio_threshold: float = COMBINED_SHORTCUT_RATIO_THRESHOLD
    fraction_threshold: float = COMBINED_SHORTCUT_FRACTION_THRESHOLD
    positive_match_count: int = 0
    negative_match_count: int = 0


def _match_fraction(sequences: list[str], charge_threshold: float, length_min: int, length_max: int) -> tuple[float, int]:
    """Return (fraction, count) of sequences satisfying charge-AND-length criteria."""
    if not sequences:
        return 0.0, 0
    matched = sum(
        1 for seq in sequences
        if _is_charge_length_match(seq, charge_threshold, length_min, length_max)
    )
    return matched / len(sequences), matched


def compute_charge_length_report(
    sequences: list[str],
    labels: list[int],
    charge_threshold: float = COMBINED_CHARGE_THRESHOLD,
    length_min: int = COMBINED_LENGTH_MIN,
    length_max: int = COMBINED_LENGTH_MAX,
    ratio_threshold: float = COMBINED_SHORTCUT_RATIO_THRESHOLD,
    fraction_threshold: float = COMBINED_SHORTCUT_FRACTION_THRESHOLD,
) -> ChargeLengthReport:
    """Compute combined charge+length shortcut report for a benchmark dataset.

    Args:
        sequences: Amino acid sequences in the benchmark.
        labels: Binary labels (1=positive/AMP, 0=negative/non-AMP).
        charge_threshold: Minimum net charge (K+R-D-E) to count as 'charged'.
        length_min: Minimum sequence length for the AMP length range.
        length_max: Maximum sequence length for the AMP length range.
        ratio_threshold: Ratio of pos/neg combined-match fraction above which shortcut is flagged.
        fraction_threshold: Minimum fraction of positives matching BOTH criteria to trigger warning.

    Returns:
        ChargeLengthReport with per-group statistics and shortcut flag.

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

    pos_frac, pos_count = _match_fraction(positives, charge_threshold, length_min, length_max)
    neg_frac, neg_count = _match_fraction(negatives, charge_threshold, length_min, length_max)

    if neg_frac > 0:
        ratio = pos_frac / neg_frac
    elif pos_frac > 0:
        ratio = float("inf")
    else:
        ratio = 1.0

    combined_shortcut_likely = (
        pos_frac >= fraction_threshold
        and (ratio >= ratio_threshold or neg_frac == 0.0)
    )

    if combined_shortcut_likely:
        if neg_frac == 0.0:
            explanation = (
                f"{pos_frac:.1%} of positives satisfy BOTH charge>={charge_threshold:.0f} "
                f"AND length [{length_min}, {length_max}], while 0.0% of negatives do. "
                "Combined charge+length is a perfect separator — benchmark improvements "
                "may reflect this conjunction shortcut, not genuine activity signal."
            )
        else:
            explanation = (
                f"{pos_frac:.1%} of positives vs {neg_frac:.1%} of negatives satisfy "
                f"BOTH charge>={charge_threshold:.0f} AND length [{length_min}, {length_max}] "
                f"(ratio: {ratio:.2f}x, threshold: {ratio_threshold:.1f}x). "
                "Benchmark improvements may reflect the combined charge+length shortcut."
            )
    else:
        explanation = (
            f"No combined shortcut detected: {pos_frac:.1%} of positives vs "
            f"{neg_frac:.1%} of negatives satisfy BOTH charge>={charge_threshold:.0f} "
            f"AND length [{length_min}, {length_max}] "
            f"(ratio: {ratio:.2f}x, threshold: {ratio_threshold:.1f}x)."
        )

    return ChargeLengthReport(
        n_positives=len(positives),
        n_negatives=len(negatives),
        positive_combined_match_fraction=pos_frac,
        negative_combined_match_fraction=neg_frac,
        combined_ratio=ratio,
        combined_shortcut_likely=combined_shortcut_likely,
        shortcut_explanation=explanation,
        charge_threshold=charge_threshold,
        length_min=length_min,
        length_max=length_max,
        ratio_threshold=ratio_threshold,
        fraction_threshold=fraction_threshold,
        positive_match_count=pos_count,
        negative_match_count=neg_count,
    )


def format_charge_length_report(report: ChargeLengthReport) -> str:
    """Format a ChargeLengthReport as a human-readable string."""
    ratio_str = (
        f"{report.combined_ratio:.2f}x"
        if report.combined_ratio != float("inf")
        else "inf (no negatives match both criteria)"
    )
    lines = [
        "=== COMBINED CHARGE+LENGTH SHORTCUT REPORT ===",
        f"Sequences: {report.n_positives} positives, {report.n_negatives} negatives",
        f"Combined criteria: charge >= {report.charge_threshold:.0f} AND length in [{report.length_min}, {report.length_max}]",
        "",
        "-- POSITIVE (AMP) --",
        f"  Sequences matching BOTH criteria: {report.positive_match_count} / {report.n_positives}",
        f"  Combined-match fraction: {report.positive_combined_match_fraction:.1%}",
        "",
        "-- NEGATIVE (non-AMP) --",
        f"  Sequences matching BOTH criteria: {report.negative_match_count} / {report.n_negatives}",
        f"  Combined-match fraction: {report.negative_combined_match_fraction:.1%}",
        "",
        f"Pos/neg combined-match ratio: {ratio_str}",
        f"COMBINED SHORTCUT LIKELY: {'YES -- see explanation below' if report.combined_shortcut_likely else 'no'}",
        "",
        report.shortcut_explanation,
        "",
        "NOTICE: Combined charge+length is the strongest single-conjunction shortcut.",
        "Pair with individual charge and length reports for full shortcut audit.",
    ]
    return "\n".join(lines)

"""Charge-distribution report for benchmark shortcut visibility — Phase C C3.

Every benchmark should be analyzed for the charge shortcut: if benchmark
positives have much higher average charge than negatives, a simple charge
threshold rule (charge >= 4) might explain most of the apparent discrimination.

Usage:
    from openamp_foundry.evidence.charge_distribution_report import (
        ChargeDistributionReport,
        compute_charge_report,
    )

    # Given benchmark sequences and binary labels (1=positive, 0=negative):
    sequences = ["KWKLFKK", "GSGSGS", ...]
    labels = [1, 0, ...]

    report = compute_charge_report(sequences, labels)
    if report.charge_shortcut_likely:
        print("WARNING: charge shortcut detected")
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import List


# Amino acid net charge contributions at pH ~7 (proxy)
_POSITIVE_AA = frozenset("KRH")
_NEGATIVE_AA = frozenset("DE")

# Threshold for "high charge" (same as AMP baseline heuristic)
CHARGE_THRESHOLD = 4

# Fraction of positives with charge >= threshold that triggers shortcut warning
SHORTCUT_WARNING_FRACTION = 0.60

# Ratio of positive mean charge to negative mean charge that triggers warning
SHORTCUT_RATIO_THRESHOLD = 1.5


def _net_charge_proxy(sequence: str) -> float:
    """Compute net charge proxy (count of positive AA minus negative AA)."""
    seq = sequence.upper()
    return float(sum(1 for aa in seq if aa in _POSITIVE_AA) -
                 sum(1 for aa in seq if aa in _NEGATIVE_AA))


@dataclass
class ChargeDistributionReport:
    """Charge distribution analysis for a set of benchmark candidates.

    Fields:
        n_positive: Number of positive (active) candidates
        n_negative: Number of negative (inactive) candidates
        mean_charge_positive: Mean charge of positives (None if n_positive == 0)
        mean_charge_negative: Mean charge of negatives (None if n_negative == 0)
        median_charge_positive: Median charge of positives (None if n_positive == 0)
        median_charge_negative: Median charge of negatives (None if n_negative == 0)
        fraction_positive_high_charge: Fraction of positives with charge >= CHARGE_THRESHOLD
        fraction_negative_high_charge: Fraction of negatives with charge >= CHARGE_THRESHOLD
        charge_shortcut_likely: True if charge distribution suggests shortcut
        shortcut_warning: Human-readable warning string (empty if no shortcut)
        charge_ratio: Ratio of mean_charge_positive to mean_charge_negative (None if either 0)
    """
    n_positive: int
    n_negative: int
    mean_charge_positive: float | None
    mean_charge_negative: float | None
    median_charge_positive: float | None
    median_charge_negative: float | None
    fraction_positive_high_charge: float
    fraction_negative_high_charge: float
    charge_shortcut_likely: bool
    shortcut_warning: str
    charge_ratio: float | None
    positive_charges: List[float] = field(default_factory=list)
    negative_charges: List[float] = field(default_factory=list)


def compute_charge_report(
    sequences: list[str],
    labels: list[int],
) -> ChargeDistributionReport:
    """Compute charge-distribution report for a benchmark dataset.

    Args:
        sequences: List of peptide sequences (strings of amino acid single-letter codes).
        labels: List of binary labels (1 = positive/active, 0 = negative/inactive).
                Must be same length as sequences.

    Returns:
        ChargeDistributionReport with charge statistics and shortcut assessment.

    Raises:
        ValueError: If sequences and labels have different lengths.
    """
    if len(sequences) != len(labels):
        raise ValueError(
            f"sequences and labels must have the same length, "
            f"got {len(sequences)} and {len(labels)}"
        )

    positive_charges: list[float] = []
    negative_charges: list[float] = []

    for seq, label in zip(sequences, labels):
        charge = _net_charge_proxy(seq)
        if label == 1:
            positive_charges.append(charge)
        else:
            negative_charges.append(charge)

    n_pos = len(positive_charges)
    n_neg = len(negative_charges)

    # Mean and median
    mean_pos = statistics.mean(positive_charges) if n_pos > 0 else None
    mean_neg = statistics.mean(negative_charges) if n_neg > 0 else None
    median_pos = statistics.median(positive_charges) if n_pos > 0 else None
    median_neg = statistics.median(negative_charges) if n_neg > 0 else None

    # High-charge fractions
    frac_pos_high = (
        sum(1 for c in positive_charges if c >= CHARGE_THRESHOLD) / n_pos
        if n_pos > 0
        else 0.0
    )
    frac_neg_high = (
        sum(1 for c in negative_charges if c >= CHARGE_THRESHOLD) / n_neg
        if n_neg > 0
        else 0.0
    )

    # Charge ratio (mean_pos / mean_neg — only if both non-zero)
    charge_ratio: float | None = None
    if mean_pos is not None and mean_neg is not None and mean_neg > 0:
        charge_ratio = mean_pos / mean_neg

    # Shortcut detection
    shortcut_likely = False
    shortcut_warning = ""

    if frac_pos_high >= SHORTCUT_WARNING_FRACTION:
        shortcut_likely = True
        shortcut_warning += (
            f"CHARGE SHORTCUT LIKELY: {frac_pos_high:.0%} of positives have "
            f"charge >= {CHARGE_THRESHOLD} (threshold: {SHORTCUT_WARNING_FRACTION:.0%}). "
        )

    if charge_ratio is not None and charge_ratio >= SHORTCUT_RATIO_THRESHOLD:
        shortcut_likely = True
        shortcut_warning += (
            f"Mean charge ratio (pos/neg) = {charge_ratio:.2f} "
            f"(threshold: {SHORTCUT_RATIO_THRESHOLD:.1f}). "
            "A simple charge threshold rule may explain most of the discrimination. "
            "Run charge-matched benchmark (BMC-0002) to verify residual signal."
        )

    return ChargeDistributionReport(
        n_positive=n_pos,
        n_negative=n_neg,
        mean_charge_positive=mean_pos,
        mean_charge_negative=mean_neg,
        median_charge_positive=median_pos,
        median_charge_negative=median_neg,
        fraction_positive_high_charge=frac_pos_high,
        fraction_negative_high_charge=frac_neg_high,
        charge_shortcut_likely=shortcut_likely,
        shortcut_warning=shortcut_warning.strip(),
        charge_ratio=charge_ratio,
        positive_charges=positive_charges,
        negative_charges=negative_charges,
    )


def format_charge_report(report: ChargeDistributionReport) -> str:
    """Format a ChargeDistributionReport as human-readable text."""
    lines = [
        "=" * 60,
        "CHARGE DISTRIBUTION REPORT",
        "=" * 60,
        f"Positives (n={report.n_positive}):",
        f"  Mean charge:    {report.mean_charge_positive:.2f}" if report.mean_charge_positive is not None else "  Mean charge:    N/A",
        f"  Median charge:  {report.median_charge_positive:.2f}" if report.median_charge_positive is not None else "  Median charge:  N/A",
        f"  Fraction ≥{CHARGE_THRESHOLD}: {report.fraction_positive_high_charge:.1%}",
        f"Negatives (n={report.n_negative}):",
        f"  Mean charge:    {report.mean_charge_negative:.2f}" if report.mean_charge_negative is not None else "  Mean charge:    N/A",
        f"  Median charge:  {report.median_charge_negative:.2f}" if report.median_charge_negative is not None else "  Median charge:  N/A",
        f"  Fraction ≥{CHARGE_THRESHOLD}: {report.fraction_negative_high_charge:.1%}",
        f"Charge ratio (pos/neg): {report.charge_ratio:.2f}" if report.charge_ratio is not None else "Charge ratio (pos/neg): N/A",
        "",
        f"Shortcut likely: {'YES — ' + report.shortcut_warning if report.charge_shortcut_likely else 'No'}",
        "=" * 60,
    ]
    return "\n".join(lines)

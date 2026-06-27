from __future__ import annotations

import math
from collections import Counter

HYDROPHOBIC = set("AILMFWVY")
POSITIVE = set("KRH")
NEGATIVE = set("DE")
AROMATIC = set("FWY")
CYS = "C"

# Eisenberg consensus hydrophobicity scale (normalized, 0-centred removed, shifted to 0..1 range)
# Source: Eisenberg et al. (1984) J Mol Biol. Used for hydrophobic moment only.
_HYDROPHOBICITY: dict[str, float] = {
    "A": 0.620, "R": -2.530, "N": -0.780, "D": -0.900, "C": 0.290,
    "Q": -0.850, "E": -0.740, "G": 0.480, "H": -0.400, "I": 1.380,
    "L": 1.060, "K": -1.500, "M": 0.640, "F": 1.190, "P": 0.120,
    "S": -0.180, "T": -0.050, "W": 0.810, "Y": 0.260, "V": 1.080,
}


def net_charge_proxy(sequence: str) -> int:
    return sum(1 for aa in sequence if aa in POSITIVE) - sum(1 for aa in sequence if aa in NEGATIVE)


def fraction(sequence: str, alphabet: set[str]) -> float:
    if not sequence:
        return 0.0
    return sum(1 for aa in sequence if aa in alphabet) / len(sequence)


def longest_repeat_run(sequence: str) -> int:
    if not sequence:
        return 0
    best = 1
    current = 1
    for prev, aa in zip(sequence, sequence[1:]):
        if aa == prev:
            current += 1
            best = max(best, current)
        else:
            current = 1
    return best


def hydrophobic_moment(sequence: str, angle_deg: float = 100.0) -> float:
    """Compute mean hydrophobic moment for an assumed alpha-helical conformation.

    Uses the Eisenberg (1984) consensus scale. Angle of 100° per residue is the
    standard helical wheel projection used in AMP literature.

    Returns a value in [0, ∞); typical AMPs have μH > 0.4. Not normalised to [0,1]
    because the range is sequence-length-dependent — callers should normalise if needed.
    """
    if not sequence:
        return 0.0
    angle_rad = math.radians(angle_deg)
    sin_sum = 0.0
    cos_sum = 0.0
    for i, aa in enumerate(sequence):
        h = _HYDROPHOBICITY.get(aa, 0.0)
        theta = i * angle_rad
        sin_sum += h * math.sin(theta)
        cos_sum += h * math.cos(theta)
    moment = math.sqrt(sin_sum ** 2 + cos_sum ** 2) / len(sequence)
    return round(moment, 4)


def compute_features(sequence: str) -> dict[str, float | int | dict[str, int]]:
    counts = Counter(sequence)
    length = len(sequence)
    charge = net_charge_proxy(sequence)
    hydrophobic_fraction = fraction(sequence, HYDROPHOBIC)
    aromatic_fraction = fraction(sequence, AROMATIC)
    cys_fraction = counts.get(CYS, 0) / length if length else 0.0
    gly_fraction = counts.get("G", 0) / length if length else 0.0
    pro_fraction = counts.get("P", 0) / length if length else 0.0
    repeat_run = longest_repeat_run(sequence)
    mu_h = hydrophobic_moment(sequence)
    return {
        "length": length,
        "net_charge_proxy": charge,
        "charge_density": charge / length if length else 0.0,
        "hydrophobic_fraction": round(hydrophobic_fraction, 4),
        "aromatic_fraction": round(aromatic_fraction, 4),
        "cysteine_fraction": round(cys_fraction, 4),
        "glycine_fraction": round(gly_fraction, 4),
        "proline_fraction": round(pro_fraction, 4),
        "longest_repeat_run": repeat_run,
        "hydrophobic_moment": mu_h,
        "residue_counts": dict(sorted(counts.items())),
    }

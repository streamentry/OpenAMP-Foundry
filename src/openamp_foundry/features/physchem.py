from __future__ import annotations

import math
from collections import Counter

from openamp_foundry.scoring.boman import boman_index, gravy_score

HYDROPHOBIC = set("AILMFWVY")
POSITIVE = set("KRH")
NEGATIVE = set("DE")
AROMATIC = set("FWY")
CYS = "C"
# Trypsin cleaves after K or R; chymotrypsin after F, W, Y (interior sites only)
TRYPSIN_SITES = set("KR")
CHYMOTRYPSIN_SITES = set("FWY")  # identical to AROMATIC — kept separate for semantic clarity

# Eisenberg consensus hydrophobicity scale (normalized, 0-centred removed, shifted to 0..1 range)
# Source: Eisenberg et al. (1984) J Mol Biol. Used for hydrophobic moment only.
_HYDROPHOBICITY: dict[str, float] = {
    "A": 0.620, "R": -2.530, "N": -0.780, "D": -0.900, "C": 0.290,
    "Q": -0.850, "E": -0.740, "G": 0.480, "H": -0.400, "I": 1.380,
    "L": 1.060, "K": -1.500, "M": 0.640, "F": 1.190, "P": 0.120,
    "S": -0.180, "T": -0.050, "W": 0.810, "Y": 0.260, "V": 1.080,
}

# Chou-Fasman helix propensity parameters (Pα values).
# Source: Chou PY & Fasman GD (1974) Biochemistry 13:222-245 (Table IV).
# Values > 1.0 are helix-forming; 0.75–1.0 indifferent; < 0.75 helix-breaking.
# Proline (0.57) and Glycine (0.57) are the canonical helix breakers.
_HELIX_PROPENSITY: dict[str, float] = {
    "A": 1.42, "R": 0.98, "N": 0.67, "D": 1.01, "C": 0.70,
    "Q": 1.11, "E": 1.51, "G": 0.57, "H": 1.00, "I": 1.08,
    "L": 1.21, "K": 1.16, "M": 1.45, "F": 1.13, "P": 0.57,
    "S": 0.77, "T": 0.83, "W": 1.08, "Y": 0.69, "V": 1.06,
}


def helix_propensity_score(sequence: str) -> float:
    """Mean Chou-Fasman alpha-helix propensity (Pα) for the sequence.

    Returns the mean Pα across all residues. Values > 1.03 indicate a helix-forming
    tendency over the full sequence. The reference midpoint is 1.0 (indifferent).

    Source: Chou & Fasman (1974) Biochemistry 13:222-245.
    Unknown residues are assigned the indifferent value (1.0).
    """
    if not sequence:
        return 0.0
    total = sum(_HELIX_PROPENSITY.get(aa, 1.0) for aa in sequence)
    return round(total / len(sequence), 4)


def net_charge_proxy(sequence: str) -> int:
    return sum(1 for aa in sequence if aa in POSITIVE) - sum(1 for aa in sequence if aa in NEGATIVE)


def net_charge_at_ph74(sequence: str) -> float:
    """Net peptide charge at physiological pH 7.4 using Henderson-Hasselbalch equation.

    Side-chain pKa values (in peptide context):
      Arg (R): 12.50  → +1.000 at pH 7.4
      Lys (K): 10.50  → +1.000 at pH 7.4
      His (H):  6.50  → +0.114 at pH 7.4 (partial protonation)
      Asp (D):  3.90  → -1.000 at pH 7.4
      Glu (E):  4.10  → -1.000 at pH 7.4

    Reference: Bjellqvist et al. (1993) Electrophoresis 14:1023; pKa values for His
    in peptides are shifted vs free amino acid (6.0) to 6.5 to account for context.
    """
    charge = 0.0
    for aa in sequence:
        if aa == "R":
            charge += 1.0
        elif aa == "K":
            charge += 1.0
        elif aa == "H":
            # Fraction protonated = 1 / (1 + 10^(pH - pKa)) at pH 7.4, pKa 6.5
            charge += 1.0 / (1.0 + 10.0 ** (7.4 - 6.5))
        elif aa == "D":
            charge -= 1.0
        elif aa == "E":
            charge -= 1.0
    return round(charge, 4)


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


def interior_protease_sites(sequence: str, cleavage_set: set[str]) -> int:
    """Count interior residues susceptible to a protease (excludes C-terminal position).

    Trypsin cleaves after K or R; the C-terminal residue generates no downstream
    fragment, so it is excluded from the interior site count.  N-terminal position
    is included because cleavage there still produces a truncated product.
    """
    if len(sequence) < 2:
        return 0
    return sum(1 for aa in sequence[:-1] if aa in cleavage_set)


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
    n_trypsin = interior_protease_sites(sequence, TRYPSIN_SITES)
    n_chymotrypsin = interior_protease_sites(sequence, CHYMOTRYPSIN_SITES)
    # site density: interior cleavage sites per residue (0 = stable, 1 = all residues cleave)
    trypsin_density = round(n_trypsin / length if length else 0.0, 4)
    chymotrypsin_density = round(n_chymotrypsin / length if length else 0.0, 4)
    charge_ph74 = net_charge_at_ph74(sequence)
    helix_pa = helix_propensity_score(sequence)
    return {
        "length": length,
        "net_charge_proxy": charge,
        "charge_density": charge / length if length else 0.0,
        "net_charge_ph74": charge_ph74,
        "charge_density_ph74": round(charge_ph74 / length if length else 0.0, 4),
        "hydrophobic_fraction": round(hydrophobic_fraction, 4),
        "aromatic_fraction": round(aromatic_fraction, 4),
        "cysteine_fraction": round(cys_fraction, 4),
        "glycine_fraction": round(gly_fraction, 4),
        "proline_fraction": round(pro_fraction, 4),
        "longest_repeat_run": repeat_run,
        "hydrophobic_moment": mu_h,
        "helix_propensity": helix_pa,
        "boman_index": boman_index(sequence),
        "gravy": gravy_score(sequence),
        "residue_counts": dict(sorted(counts.items())),
        "trypsin_site_density": trypsin_density,
        "chymotrypsin_site_density": chymotrypsin_density,
        "interior_trypsin_sites": n_trypsin,
        "interior_chymotrypsin_sites": n_chymotrypsin,
    }

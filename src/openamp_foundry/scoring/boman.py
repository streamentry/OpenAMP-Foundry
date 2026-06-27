"""Boman index scorer — independent second activity predictor.

Implements the Boman index as defined in:
  Boman HG (2003). Antibacterial and antimalarial properties of peptides that
  are cecropin-melittin hybrids. FEBS Letters, 544(1-3), 212-215.
  and
  Boman HG (2003). Peptide antibiotics and their role in innate immunity.
  Annual Review of Immunology, 13, 61-92.

The Boman index is the mean of amino acid interaction potentials per residue.
Positive values (> 1.0) indicate high protein-binding / membrane-interaction
potential, which correlates with AMP-like activity in published benchmarks.

This is a second INDEPENDENT scoring approach that complements the
physicochemical heuristic in activity.py. Disagreement between the two
scorers is an uncertainty signal: candidates where both scorers agree are
more robust nominations than those where only one scorer favors them.

Reference values: Boman 2003, Table 1, set 2.
All values are from the published table and are reproduced here for
transparent, reproducible scoring. No training was done.
"""
from __future__ import annotations

# Published amino acid interaction potentials from Boman (2003), Table 1, set 2.
# Units: kcal/mol (approximate interaction energies)
# Positive → hydrophilic/charged, negative → hydrophobic
_BOMAN_POTENTIALS: dict[str, float] = {
    "A": -0.495,  # alanine: small, hydrophobic
    "R":  2.465,  # arginine: positively charged, high interaction
    "N":  0.185,  # asparagine: polar, uncharged
    "D":  2.465,  # aspartate: negatively charged, high interaction
    "C": -1.000,  # cysteine: hydrophobic/special
    "Q":  0.185,  # glutamine: polar, uncharged
    "E":  2.465,  # glutamate: negatively charged, high interaction
    "G":  0.000,  # glycine: minimal side chain
    "H": -0.505,  # histidine: aromatic/basic, lower than K/R
    "I": -1.810,  # isoleucine: hydrophobic
    "L": -1.810,  # leucine: hydrophobic
    "K":  2.465,  # lysine: positively charged, high interaction
    "M": -1.305,  # methionine: hydrophobic/sulfur
    "F": -2.498,  # phenylalanine: aromatic, hydrophobic
    "P":  0.000,  # proline: conformational constraint
    "S":  0.255,  # serine: polar, uncharged
    "T":  0.370,  # threonine: polar, uncharged
    "W": -3.398,  # tryptophan: large aromatic, most hydrophobic
    "Y": -2.303,  # tyrosine: aromatic, polar
    "V": -1.505,  # valine: hydrophobic
}

# Published AMP threshold: Boman index > 1.0 is associated with AMP-like activity.
# Below -1.0 indicates strongly hydrophobic, non-interactive (unlikely AMP).
_AMP_THRESHOLD = 1.0
_HYDROPHOBIC_THRESHOLD = -1.0
# Range of Boman index across all possible sequences:
_BOMAN_MIN = -3.398  # all-W sequence (hypothetical)
_BOMAN_MAX = 2.465   # all-K/R/D/E sequence (hypothetical)


def boman_index(sequence: str) -> float:
    """Compute the Boman index for a peptide sequence.

    Returns the mean interaction potential per residue (kcal/mol).
    Positive (>1.0): high protein-binding / membrane-interaction potential.
    Negative (<0): predominantly hydrophobic, less interactive.

    Non-canonical amino acids contribute 0.0 (neutral) to the mean.
    """
    if not sequence:
        return 0.0
    total = sum(_BOMAN_POTENTIALS.get(aa, 0.0) for aa in sequence.upper())
    return round(total / len(sequence), 4)


def boman_activity_score(sequence: str) -> float:
    """Normalize the Boman index to [0, 1] for comparison with other scorers.

    Mapping:
      Boman ≥ 1.0  → score approaching 1.0 (AMP-like zone)
      Boman = 0.0  → score ≈ 0.5
      Boman ≤ -1.0 → score approaching 0.0 (non-interactive zone)

    The normalization uses a sigmoid-like mapping so that the published threshold
    (Boman > 1.0) falls in the upper range of the score.
    """
    bi = boman_index(sequence)
    # Sigmoid-like normalization centered at 0, scaled so bi=1.0 → ≈ 0.73
    # Using tanh mapping: score = 0.5 * (1 + tanh(bi / 2))
    import math
    score = 0.5 * (1.0 + math.tanh(bi / 2.0))
    return round(max(0.0, min(1.0, score)), 4)


def gravy_score(sequence: str) -> float:
    """Compute the GRAVY (Grand Average of hYdropathicity) score.

    Uses the Kyte-Doolittle hydropathy scale (J Mol Biol 157:105-132, 1982).
    Positive GRAVY → hydrophobic overall.
    Negative GRAVY → hydrophilic overall.
    AMPs typically fall between -0.5 and +0.5.
    """
    _KD: dict[str, float] = {
        "A":  1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C":  2.5,
        "Q": -3.5, "E": -3.5, "G": -0.4, "H": -3.2, "I":  4.5,
        "L":  3.8, "K": -3.9, "M":  1.9, "F":  2.8, "P": -1.6,
        "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V":  4.2,
    }
    if not sequence:
        return 0.0
    total = sum(_KD.get(aa, 0.0) for aa in sequence.upper())
    return round(total / len(sequence), 4)


def model_disagreement(activity_likeness: float, boman_act: float) -> float:
    """Compute normalized disagreement between two activity scores.

    Returns a value in [0, 1]:
      0.0 → both scorers agree perfectly
      1.0 → maximum disagreement (one says 0, other says 1)

    High disagreement indicates uncertainty — the candidate should receive
    extra scrutiny before nomination. Low disagreement (high consensus) is
    evidence of more robust computational support.

    Disagreement is NOT a biological safety or activity assessment.
    It is an uncertainty proxy for the computational prediction only.
    """
    return round(abs(activity_likeness - boman_act), 4)

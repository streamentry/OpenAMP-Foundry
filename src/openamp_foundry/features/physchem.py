from __future__ import annotations

import math
from collections import Counter

# Deferred import: see compute_features for rationale (circular-import safety).
HYDROPHOBIC = set("AILMFWVY")
POSITIVE = set("KRH")
NEGATIVE = set("DE")
AROMATIC = set("FWY")
CYS = "C"
# Trypsin cleaves after K or R; chymotrypsin after F, W, Y (interior sites only)
TRYPSIN_SITES = set("KR")
CHYMOTRYPSIN_SITES = set("FWY")  # identical to AROMATIC — kept separate for semantic clarity
# Human neutrophil elastase (HNE) primary P1 substrates: Ala > Val > Ser
# Reference: Bieth (1986) Bull Eur Physiopathol Respir; Doherty et al. (1991) Biochemistry
ELASTASE_SITES = {"A", "V", "S"}
# Hydrophobic residues that drive aggregation in synthetic peptides: Val, Ile, Leu, Met, Phe, Trp
AGG_HYDROPHOBIC = set("VILMFW")

# Eisenberg (1984) consensus hydrophobicity scale. Raw signed values: R=-2.530 (most hydrophilic)
# to I=+1.380 (most hydrophobic). DO NOT normalize to [0,1] — the hydrophobic moment calculation
# requires signed values so that polar/charged residues (negative) cancel apolar residues (positive).
# Source: Eisenberg et al. (1984) J Mol Biol 179:125-142, Table 2. Used for hydrophobic moment only.
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

    Note: α-amino N-terminus (+≈0.80 at pH 7.4, pKa ≈ 8.0) and α-carboxyl C-terminus
    (−≈1.00 at pH 7.4, pKa ≈ 3.1) are excluded — only side-chain charges are computed.
    The net terminal offset is ≈ −0.20 per peptide (~7% underestimation for a 10-mer).
    This is the standard convention for relative charge comparisons across candidates
    synthesized under the same conditions.
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


def max_windowed_hydrophobic_moment(
    sequence: str,
    window: int = 11,
    angle_deg: float = 100.0,
) -> float:
    """Maximum hydrophobic moment over any contiguous window of `window` residues.

    Returns a value in [0, ∞); NOT bounded at 1.0 — individual residue Eisenberg
    values can be large for tightly packed hydrophobic windows.

    For short sequences (len <= window), this equals the full-sequence mu_h because
    only one window exists. For longer sequences, this captures the most concentrated
    amphipathic helical segment (Eisenberg 1984, window=11) rather than averaging over
    the entire chain, which dilutes the signal near non-helical termini or linkers.

    NOTE: `max_windowed_hydrophobic_moment` is NOT guaranteed to be >= `hydrophobic_moment`
    (the full-sequence value). For non-amphipathic or uniform sequences longer than the
    window, the fixed-window value (normalised by `window`) can be LESS than the
    full-sequence average (normalised by `len(sequence)`). `activity_likeness_score()`
    handles this correctly via `max(hydrophobic_moment, max_hydrophobic_moment)`;
    direct callers that read both keys from the feature dict must not assume otherwise.

    This value is stored as `max_hydrophobic_moment` in the feature dict and used by
    `activity_likeness_score()` to improve discrimination for longer helical AMPs such
    as magainin-2, cecropin-A, and LL-37 class peptides.
    """
    if not sequence:
        return 0.0
    w = min(window, len(sequence))
    angle_rad = math.radians(angle_deg)
    best = 0.0
    for start in range(len(sequence) - w + 1):
        sub = sequence[start : start + w]
        sin_sum = cos_sum = 0.0
        for i, aa in enumerate(sub):
            h = _HYDROPHOBICITY.get(aa, 0.0)
            theta = i * angle_rad
            sin_sum += h * math.sin(theta)
            cos_sum += h * math.cos(theta)
        moment = math.sqrt(sin_sum ** 2 + cos_sum ** 2) / w
        if moment > best:
            best = moment
    return round(best, 4)


def helix_wheel_faces(
    sequence: str,
    angle_deg: float = 100.0,
) -> dict[str, float]:
    """Moment-oriented amphipathic face analysis on an α-helix wheel.

    Uses the hydrophobic moment vector (Eisenberg 1984) to define the hydrophobic face
    direction for the specific peptide's N-terminal convention. This is NOT independent
    of circular permutation: because the angle model assigns θ = i × angle_deg to each
    position index, shifting the N-terminus changes the moment vector direction and can
    change face assignments. Results are meaningful for designed peptides with a fixed
    N-terminal residue (which is the case for all synthesis candidates in this pipeline).

    Algorithm:
      1. Compute the hydrophobic moment vector (mu_x, mu_y) from Eisenberg hydrophobicities
      2. The direction of this vector defines the hydrophobic face axis for this sequence
      3. Each residue i is assigned to the "hydrophobic face" if its projection onto the
         moment vector is positive: dot = cos(i*θ) × mu_x + sin(i*θ) × mu_y > 0
         (the / mu_mag division doesn't affect sign classification — it normalises dot to
         the cosine similarity range [-1, 1] for interpretability)
      4. Compute mean Eisenberg hydrophobicity for each face, cationic fraction, and contrast

    Returns a dict with:
      - hydrophobic_face_mean_h: mean Eisenberg H of residues on the hydrophobic face
      - hydrophilic_face_mean_h: mean Eisenberg H of residues on the hydrophilic face
      - face_contrast: hydrophobic_face_mean_h − hydrophilic_face_mean_h (positive for AMPs)
      - h_face_cationic_fraction: fraction of K/R/H on the hydrophobic face (undesirable)
      - ph_face_cationic_fraction: fraction of K/R/H on the hydrophilic face (ideal for AMPs)
      - amphipathic_score: normalised [0, 1] over contrast range [0, 2.0]; > 0.4 is AMP-like
        (Histidine is counted in cationic fractions at its standard K/R/H convention —
        note this overestimates H's charge contribution vs the pH-7.4 model)

    For sequences < 4 AA, amphipathic character is ill-defined; returns zeros.

    Reference: Schiffer & Edmundson (1967) Biophys J 7(2):121-135; Eisenberg (1984).
    """
    if len(sequence) < 4:
        return {
            "hydrophobic_face_mean_h": 0.0, "hydrophilic_face_mean_h": 0.0,
            "face_contrast": 0.0, "h_face_cationic_fraction": 0.0,
            "ph_face_cationic_fraction": 0.0, "amphipathic_score": 0.0,
        }

    angle_rad = math.radians(angle_deg)
    n = len(sequence)

    # Step 1: compute moment vector
    sin_sum = cos_sum = 0.0
    for i, aa in enumerate(sequence):
        h = _HYDROPHOBICITY.get(aa, 0.0)
        theta = i * angle_rad
        sin_sum += h * math.sin(theta)
        cos_sum += h * math.cos(theta)
    mu_x = cos_sum / n
    mu_y = sin_sum / n
    mu_mag = math.sqrt(mu_x ** 2 + mu_y ** 2)

    # If moment is near zero, the sequence has no amphipathic character
    if mu_mag < 1e-9:
        return {
            "hydrophobic_face_mean_h": 0.0, "hydrophilic_face_mean_h": 0.0,
            "face_contrast": 0.0, "h_face_cationic_fraction": 0.0,
            "ph_face_cationic_fraction": 0.0, "amphipathic_score": 0.0,
        }

    # Step 2: classify each residue relative to the moment vector direction
    h_face_vals: list[float] = []
    ph_face_vals: list[float] = []
    h_face_pos = 0
    ph_face_pos = 0

    for i, aa in enumerate(sequence):
        theta = i * angle_rad
        # Dot product of residue unit vector with moment unit vector
        dot = (math.cos(theta) * mu_x + math.sin(theta) * mu_y) / mu_mag
        h_val = _HYDROPHOBICITY.get(aa, 0.0)
        if dot >= 0:
            h_face_vals.append(h_val)
            if aa in POSITIVE:
                h_face_pos += 1
        else:
            ph_face_vals.append(h_val)
            if aa in POSITIVE:
                ph_face_pos += 1

    hf_mean = sum(h_face_vals) / len(h_face_vals) if h_face_vals else 0.0
    phf_mean = sum(ph_face_vals) / len(ph_face_vals) if ph_face_vals else 0.0
    contrast = hf_mean - phf_mean

    h_face_cat = h_face_pos / len(h_face_vals) if h_face_vals else 0.0
    ph_face_cat = ph_face_pos / len(ph_face_vals) if ph_face_vals else 0.0

    # Normalise contrast over [0, 2.0]: empirical AMP range is ~0.7 (cecropin-A) to ~2.0
    # (short cationic helices like SEED-003). Raising the reference from 1.2 to 2.0 prevents
    # the majority of high-quality reference AMPs (magainin, LL-37) from saturating at 1.0.
    # Threshold interpretation: < 0.2 poor, 0.2-0.4 marginal, > 0.4 AMP-like, > 0.8 excellent.
    amphipathic_score = round(max(0.0, min(1.0, contrast / 2.0)), 4)

    return {
        "hydrophobic_face_mean_h": round(hf_mean, 4),
        "hydrophilic_face_mean_h": round(phf_mean, 4),
        "face_contrast": round(contrast, 4),
        "h_face_cationic_fraction": round(h_face_cat, 4),
        "ph_face_cationic_fraction": round(ph_face_cat, 4),
        "amphipathic_score": amphipathic_score,
    }


def interior_protease_sites(sequence: str, cleavage_set: set[str]) -> int:
    """Count interior residues susceptible to a protease (excludes C-terminal position).

    Trypsin cleaves after K or R; the C-terminal residue generates no downstream
    fragment, so it is excluded from the interior site count.  N-terminal position
    is included because cleavage there still produces a truncated product.
    """
    if len(sequence) < 2:
        return 0
    return sum(1 for aa in sequence[:-1] if aa in cleavage_set)


def selectivity_proxy(charge: float, gravy: float) -> float:
    """Heuristic selectivity proxy [0, 1]: likelihood of selective bacterial killing
    without mammalian cytotoxicity.

    Based on Dathe & Wieprecht (1999) Biochim Biophys Acta 1462:71-87 (GRAVY/cytotox
    correlation) and Shai (2002) Biochim Biophys Acta 1462:55-70 (charge selectivity).

    Selectivity optimum: net charge +2 to +7, GRAVY ≤ 0.5.

    - Charge < +2: insufficient electrostatic attraction to anionic bacterial membranes
      (phosphatidylglycerol, cardiolipin) → reduced bacterial killing, not cytotoxic.
    - Charge > +8: non-specific disruption of zwitterionic mammalian membranes
      (phosphatidylcholine) → cytotoxicity risk.
    - GRAVY > 0.5: hydrophobic-driven non-specific membrane disruption →
      cytotoxicity risk (Dathe & Wieprecht 1999; Chen et al. 2005 J Biol Chem).
    - GRAVY > 1.0: severe cytotoxicity, likely haemolytic.

    Args:
        charge: Net charge at pH 7.4 (float).
        gravy: Grand Average of hYdropathicity (GRAVY) score.

    Returns:
        Selectivity proxy in [0.0, 1.0]. Values below 0.5 indicate high cytotoxicity risk.
    """
    # Charge selectivity component (weight 0.6)
    if charge <= 2.0:
        charge_sel = max(0.0, charge / 2.0)
    elif charge <= 7.0:
        charge_sel = 1.0
    else:
        charge_sel = max(0.0, 1.0 - (charge - 7.0) / 5.0)

    # GRAVY hydrophobicity selectivity component (weight 0.4)
    if gravy <= 0.5:
        gravy_sel = 1.0
    elif gravy <= 1.0:
        gravy_sel = max(0.0, 1.0 - (gravy - 0.5) / 0.5)
    else:
        gravy_sel = 0.0

    return round(0.6 * charge_sel + 0.4 * gravy_sel, 4)


def aggregation_propensity(sequence: str) -> float:
    """Heuristic aggregation propensity for short synthetic peptides [0, 1].

    Two-component model:
    1. Hydrophobic run length: consecutive residues from {V,I,L,M,F,W} ≥ 4 drive
       self-association during SPPS, solubilisation, and assay buffers.
       Risk onset at run ≥ 4 (same threshold as QC HYDROPHOBIC_RUN_RE flag; same
       residue set AGG_HYDROPHOBIC). Ramp: 0.0 at run < 4, 0.20 at run=4, 1.0 at run ≥ 8.
    2. Beta-branched residue density (Val, Ile, Thr) > 20% promotes β-strand over
       α-helix and intermolecular β-sheet aggregation in concentrated solutions.

    Limitation: Ala-rich sequences score 0.0 despite documented on-resin aggregation
    issues (Sarin et al. 1984; Tam et al. 1988). Ala aggregation arises from apolar
    solvation collapse rather than the hydrophobic-run / β-branched mechanisms here.

    References:
    - Quittot et al. (2017) Protein Sci 26:720-735 (hydrophobic run aggregation)
    - Wurth et al. (2006) J Mol Biol 355:524-536 (Val/Ile beta-strand aggregation)

    Returns 0.0 (no risk) to 1.0 (severe aggregation risk).
    """
    if not sequence:
        return 0.0
    n = len(sequence)

    # Component 1: longest hydrophobic run across full sequence (mirrors QC regex)
    max_run = 0
    current_run = 0
    for aa in sequence:
        if aa in AGG_HYDROPHOBIC:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 0
    # Ramp: 0.0 at run < 4, 0.20 at run=4, …, 1.0 at run ≥ 8
    run_risk = min(1.0, max(0.0, (max_run - 3) / 5.0))

    # Component 2: beta-branched residue density (Val, Ile, Thr)
    beta_branched = {"V", "I", "T"}
    beta_density = sum(1 for aa in sequence if aa in beta_branched) / n
    # Risk onset at >20%, full risk at >50%
    beta_risk = min(1.0, max(0.0, (beta_density - 0.20) / 0.30)) if beta_density > 0.20 else 0.0

    return round(0.7 * run_risk + 0.3 * beta_risk, 4)


def compute_features(sequence: str) -> dict[str, float | int | dict[str, int]]:
    # Lazy import: openamp_foundry.scoring.boman pulls in this module via
    # scoring.expert at package init time, so top-level imports would cycle.
    from openamp_foundry.scoring.boman import boman_index, gravy_score
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
    max_mu_h = max_windowed_hydrophobic_moment(sequence)
    hw_faces = helix_wheel_faces(sequence)
    from openamp_foundry.features.dipeptide import dipeptide_order_score
    n_trypsin = interior_protease_sites(sequence, TRYPSIN_SITES)
    n_chymotrypsin = interior_protease_sites(sequence, CHYMOTRYPSIN_SITES)
    n_elastase = interior_protease_sites(sequence, ELASTASE_SITES)
    # site density: interior cleavage sites per residue (0 = stable, 1 = all residues cleave)
    trypsin_density = round(n_trypsin / length if length else 0.0, 4)
    chymotrypsin_density = round(n_chymotrypsin / length if length else 0.0, 4)
    elastase_density = round(n_elastase / length if length else 0.0, 4)
    charge_ph74 = net_charge_at_ph74(sequence)
    helix_pa = helix_propensity_score(sequence)
    gravy = gravy_score(sequence)
    sel_proxy = selectivity_proxy(charge_ph74, gravy)
    agg = aggregation_propensity(sequence)
    dio = dipeptide_order_score(sequence)
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
        "max_hydrophobic_moment": max_mu_h,
        "helix_propensity": helix_pa,
        "boman_index": boman_index(sequence),
        "gravy": gravy,
        "selectivity_proxy": sel_proxy,
        "aggregation_propensity": agg,
        "residue_counts": dict(sorted(counts.items())),
        "trypsin_site_density": trypsin_density,
        "chymotrypsin_site_density": chymotrypsin_density,
        "elastase_site_density": elastase_density,
        "interior_trypsin_sites": n_trypsin,
        "interior_chymotrypsin_sites": n_chymotrypsin,
        "interior_elastase_sites": n_elastase,
        "helix_wheel_hydrophobic_face_mean_h": hw_faces["hydrophobic_face_mean_h"],
        "helix_wheel_hydrophilic_face_mean_h": hw_faces["hydrophilic_face_mean_h"],
        "helix_wheel_face_contrast": hw_faces["face_contrast"],
        "helix_wheel_h_face_cationic_fraction": hw_faces["h_face_cationic_fraction"],
        "helix_wheel_ph_face_cationic_fraction": hw_faces["ph_face_cationic_fraction"],
        "helix_wheel_amphipathic_score": hw_faces["amphipathic_score"],
        "dipeptide_order_score": dio,
    }

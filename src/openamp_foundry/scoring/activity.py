from __future__ import annotations


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def activity_likeness_score(features: dict) -> float:
    """Transparent baseline activity-likeness score.

    This is NOT a validated biological predictor. It combines known physicochemical
    correlates of AMP activity: length, cationic charge density, hydrophobic fraction,
    aromatic content, and hydrophobic moment (amphipathicity). All weights and thresholds
    are documented and fixed before any benchmark evaluation.

    Literature basis:
    - Charge: Zasloff (2002) Nature; most AMPs carry net charge +2 to +9
    - Hydrophobicity: Hancock & Sahl (2006) Nat Biotechnol; ~30-50% hydrophobic
    - Amphipathicity (μH): Eisenberg et al. (1984); helical amphipathicity correlates
      with membrane disruption
    - Length: Jenssen et al. (2006) Clin Microbiol Rev; typical 8-50 AA
    """
    length = features["length"]
    # Prefer physiologically accurate pH-7.4 charge density; fall back to proxy for
    # manually constructed feature dicts that predate this field.
    charge_density = features.get("charge_density_ph74", features["charge_density"])
    hydrophobic = features["hydrophobic_fraction"]
    aromatic = features["aromatic_fraction"]
    mu_h = features.get("hydrophobic_moment", 0.0)
    # Chou-Fasman mean Pα: range ~0.57 (all Pro/Gly) to ~1.51 (all Glu)
    # AMP-relevant range: 1.0 (indifferent) to ~1.20 (good helical sequence)
    helix_pa = features.get("helix_propensity", 1.0)

    # Length: peak at ~18 residues, broad tolerance
    length_score = 1.0 - min(abs(length - 18) / 25, 1.0)

    # Charge: AMPs typically have positive charge density 0.1–0.5
    charge_score = clamp01((charge_density + 0.05) / 0.55)

    # Hydrophobicity: 40-50% is a sweet spot for membrane interaction
    hydro_score = 1.0 - min(abs(hydrophobic - 0.45) / 0.45, 1.0)

    # Aromatic residues (F, W, Y) aid membrane insertion.
    # Trp is weighted 1.5× vs Phe/Tyr: Trp's indole ring preferentially anchors at the
    # lipid-water interface (Wimley-White W=-1.85 kcal/mol; Wimley & White 1996 Nat Struct Biol),
    # a mechanism distinct from and more membrane-favorable than Phe/Tyr's hydrophobic stacking.
    # This differentiates puroindoline-a/indolicidin-class Trp-rich AMPs from Phe-rich peptides.
    _counts = features.get("residue_counts", {})
    _length = features["length"] or 1
    trp_fraction = _counts.get("W", 0) / _length
    non_trp_aromatic = max(0.0, aromatic - trp_fraction)
    weighted_aromatic = trp_fraction * 1.5 + non_trp_aromatic
    aromatic_bonus = min(weighted_aromatic / 0.20, 1.0) * 0.10

    # Amphipathicity: helical hydrophobic moment > 0.4 is associated with activity
    # Typical range for AMPs: 0.3–0.8; scale to [0,1] over 0–0.8 range
    amphipathicity_score = clamp01(mu_h / 0.8) * 0.14

    # Cross-term: simultaneous high charge AND high amphipathicity is synergistic.
    # Electrostatic attraction (charge) + hydrophobic bilayer insertion (mu_h) are both
    # required for the carpet/pore-forming mechanism; neither alone is sufficient.
    # Normalizer 0.15 ≈ typical pH 7.4 charge density (0.25–0.30) × typical μH (0.50–0.60);
    # chosen so cross_bonus = 1.0 when both charge and amphipathicity are at their canonical AMP optimum.
    cross_bonus = clamp01(charge_density * mu_h / 0.15) * 0.02

    # Helix propensity: Chou-Fasman Pα > 1.00 rewards helix-forming sequences.
    # Scale: indifferent (1.0) → 0.0; strong helix-former (1.20+) → 1.0 (capped at 1.0).
    # Weight increased 0.01 → 0.03: helical AMPs (LL-37, magainin, mastoparan) represent
    # ~70% of membrane-active AMP families; this bonus better distinguishes them from
    # structurally disordered or beta-sheet peptides at otherwise equal composition scores.
    # Literature: Huang (2000) Biochim Biophys Acta; Tossi et al. (2000) Biopolymers.
    helix_bonus = clamp01((helix_pa - 1.0) / 0.20) * 0.03

    # ceiling = 0.24+0.27+0.17+0.10+0.14+0.03+0.02 = 0.97 < 1.0
    score = (
        0.24 * length_score
        + 0.27 * charge_score
        + 0.17 * hydro_score
        + aromatic_bonus
        + amphipathicity_score
        + helix_bonus
        + cross_bonus
    )
    return round(clamp01(score), 4)

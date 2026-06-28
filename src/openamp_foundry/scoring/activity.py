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

    # Aromatic residues (F, W, Y) aid membrane insertion
    aromatic_bonus = min(aromatic / 0.20, 1.0) * 0.10

    # Amphipathicity: helical hydrophobic moment > 0.4 is associated with activity
    # Typical range for AMPs: 0.3–0.8; scale to [0,1] over 0–0.8 range
    amphipathicity_score = clamp01(mu_h / 0.8) * 0.14

    # Helix propensity: Chou-Fasman Pα > 1.03 rewards helix-forming sequences
    # Scale: indifferent (1.0) → 0.0; strong helix-former (1.20+) → 1.0
    helix_bonus = clamp01((helix_pa - 1.0) / 0.20) * 0.01

    # Base weights (0.24+0.27+0.17 = 0.68) leave headroom for bonuses
    # aromatic max 0.10 + amphipathicity max 0.14 + helix max 0.01 = 0.25 → ceiling 0.93
    score = (
        0.24 * length_score
        + 0.27 * charge_score
        + 0.17 * hydro_score
        + aromatic_bonus
        + amphipathicity_score
        + helix_bonus
    )
    return round(clamp01(score), 4)

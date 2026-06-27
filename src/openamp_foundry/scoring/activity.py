from __future__ import annotations


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def activity_likeness_score(features: dict) -> float:
    """Transparent baseline, not a validated biological predictor."""
    length = features["length"]
    charge_density = features["charge_density"]
    hydrophobic = features["hydrophobic_fraction"]
    aromatic = features["aromatic_fraction"]

    length_score = 1.0 - min(abs(length - 18) / 25, 1.0)
    charge_score = clamp01((charge_density + 0.05) / 0.55)
    hydro_score = 1.0 - min(abs(hydrophobic - 0.45) / 0.45, 1.0)
    aromatic_bonus = min(aromatic / 0.20, 1.0) * 0.10

    score = 0.30 * length_score + 0.35 * charge_score + 0.25 * hydro_score + aromatic_bonus
    return round(clamp01(score), 4)

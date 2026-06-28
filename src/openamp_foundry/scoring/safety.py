from __future__ import annotations

from openamp_foundry.scoring.activity import clamp01


def safety_score(features: dict) -> float:
    """Higher is safer. Coarse pre-lab hemolysis/toxicity risk proxy.

    Known limitation: melittin-like peptides (bent amphipathic helix, Habermann 1972)
    may not be correctly penalised because their hemolytic character arises from
    structural features not captured by a 1D hydrophobic moment calculation.
    All results are heuristic — no biological safety claim is made.

    v0.4 change: hydrophobic moment (μH) added as a primary hemolysis signal.
    Reference: Dathe & Wieprecht (1999) BBA 1462:71-87.
    Threshold μH > 0.55 targets strongly amphipathic sequences while preserving
    typical AMP-like candidates (μH ≈ 0.35–0.50).
    """
    length = features["length"]
    # Prefer pH 7.4 charge density. Positive charge drives hemolysis (electrostatic membrane
    # disruption); negatively charged peptides are repelled from both mammalian and bacterial
    # membranes and pose no hemolysis risk. Do NOT use abs() here.
    charge_density = features.get("charge_density_ph74", features["charge_density"])
    hydrophobic = features["hydrophobic_fraction"]
    cys = features["cysteine_fraction"]
    repeat_run = features["longest_repeat_run"]
    mu_h = features.get("hydrophobic_moment", 0.0)

    risk = 0.0

    # Strongly amphipathic sequences (μH > 0.55) have increased capacity for
    # non-selective membrane disruption, elevating hemolysis risk.
    if mu_h > 0.55:
        risk += (mu_h - 0.55) * 1.5

    if hydrophobic > 0.65:
        risk += (hydrophobic - 0.65) * 1.8
    if charge_density > 0.55:
        risk += (charge_density - 0.55) * 1.2
    if length > 35:
        risk += 0.25
    if cys > 0.25:
        risk += 0.20
    if repeat_run >= 6:
        risk += 0.15

    return round(1.0 - clamp01(risk), 4)

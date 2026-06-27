from __future__ import annotations

from openamp_foundry.scoring.activity import clamp01


def safety_score(features: dict) -> float:
    """Higher is safer. This is a coarse pre-lab risk proxy, not a toxicity proof."""
    length = features["length"]
    charge_density = abs(features["charge_density"])
    hydrophobic = features["hydrophobic_fraction"]
    cys = features["cysteine_fraction"]
    repeat_run = features["longest_repeat_run"]

    risk = 0.0
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

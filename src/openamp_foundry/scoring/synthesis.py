from __future__ import annotations

from openamp_foundry.scoring.activity import clamp01


def synthesis_feasibility_score(features: dict, valid_sequence: bool = True) -> float:
    if not valid_sequence:
        return 0.0
    length = features["length"]
    repeat_run = features["longest_repeat_run"]
    cys = features["cysteine_fraction"]

    score = 1.0
    if length > 30:
        score -= min((length - 30) * 0.04, 0.40)
    if length < 8:
        score -= 0.30
    if repeat_run >= 5:
        score -= 0.10
    if cys > 0.20:
        score -= 0.15
    return round(clamp01(score), 4)

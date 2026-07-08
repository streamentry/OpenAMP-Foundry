from __future__ import annotations

import warnings


def ensemble_score(scores: dict[str, float], weights: dict[str, float]) -> float:
    """Compute weighted sum of component scores, normalised to [0, 1].

    Weights are passed in at runtime from the pipeline config file.
    Default weights (configs/pipeline.yaml):
        activity=0.40, safety=0.25, synthesis=0.15, novelty=0.20
    Phase-3 weights (configs/phase3.yaml):
        activity=0.35, safety=0.30, synthesis=0.20, novelty=0.15

    Calibration warning: ensemble scores are ranking heuristics computed
    from physicochemical features. They are NOT calibrated probability
    estimates. The calibration benchmark (make bench-calibration) reports
    Brier score ~0.32 and calibration slope ~0.43 on the standard set,
    meaning scores consistently overstate confidence. A score of 0.8 does
    NOT mean "80% likely to be active." Scores are valid only for relative
    ranking within a single batch.
    """
    missing = [name for name in weights if name not in scores]
    if missing:
        warnings.warn(
            f"ensemble_score: weight keys missing from scores, defaulting to 0.0: {missing}",
            UserWarning,
            stacklevel=2,
        )
    total_weight = sum(weights.values()) or 1.0
    value = sum(scores.get(name, 0.0) * weight for name, weight in weights.items()) / total_weight
    return round(max(0.0, min(1.0, value)), 4)


def selection_reasons(scores: dict[str, float]) -> list[str]:
    reasons: list[str] = []
    if scores["activity"] >= 0.70:
        reasons.append("High transparent activity-likeness score")
    if scores["safety"] >= 0.75:
        reasons.append("Low predicted safety risk by baseline proxy")
    if scores["synthesis"] >= 0.80:
        reasons.append("Likely feasible under simple synthesis constraints")
    if scores["novelty"] >= 0.25:
        reasons.append("Not an exact or near-exact duplicate of demo references")
    boman_act = scores.get("boman_activity")
    disagreement = scores.get("disagreement")
    if boman_act is not None and boman_act >= 0.60 and (disagreement is None or disagreement <= 0.20):
        reasons.append("Independent Boman index scorer agrees: high interaction potential (low disagreement)")
    if not reasons:
        reasons.append("Selected only by ensemble rank; requires skeptical review")
    return reasons


def known_failure_modes(scores: dict[str, float]) -> list[str]:
    failures = [
        "No wet-lab antimicrobial activity assay has been run.",
        "Baseline scores are heuristics, not validated biological predictors.",
    ]
    if scores["novelty"] < 0.20:
        failures.append("Candidate is close to a known reference sequence.")
    if scores["safety"] < 0.70:
        failures.append("Candidate has elevated pre-lab safety-risk proxy.")
    if scores["synthesis"] < 0.75:
        failures.append("Candidate may be harder to synthesize or handle.")
    disagreement = scores.get("disagreement")
    if disagreement is not None and disagreement >= 0.30:
        failures.append(
            f"High scorer disagreement ({disagreement:.2f}): "
            "Boman index and physicochemical activity scores diverge. "
            "Extra scrutiny recommended before nomination."
        )
    return failures

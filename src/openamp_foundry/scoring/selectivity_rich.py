"""Rich composite selectivity scorer — combines evidence-identified features.

The feature decomposition benchmark (v0.5.15, PR #129) tested all 30 scalar
physicochemical features individually for selective_vs_hemolytic AUROC on the
expanded 238-peptide hemolysis reference set (54 hemolytic vs 125 selective).
It found 8 statistically significant features (CI excludes 0.5).

The current ``selectivity_proxy`` (charge + GRAVY) uses only 2 inputs and
achieves detection AUROC = 0.6095. Six of the 8 significant features are
completely ignored.

This module builds a composite selectivity scorer from the evidence. It
combines all 8 significant features. Each feature's direction
(risk-indicator or protective-indicator) is handled so the composite output
is in [0, 1] where higher = more selective (lower hemolysis risk).

Design principles:
  1. Only features with CI-excludes-0.5 significance are included.
  2. Each feature is normalised to [0, 1] contribution.
  3. Risk indicators are inverted (higher raw → lower selectivity score).
  4. Weighting is simple — equal weights unless evidence justifies otherwise.
  5. The scorer is transparent: every component and its direction are exposed.

This score is a triage signal, NOT a hemolysis predictor.
Wet-lab hemolysis assay remains mandatory for all candidates.
"""
from __future__ import annotations

from openamp_foundry.scoring.activity import clamp01


# ─────────────────────────────────────────────────────────────────────────────
# Significant features from feature_decomposition benchmark (v0.5.15)
# Each entry: (feature_key, detection_auroc, direction)
# direction = "risk_indicator" (higher value → more hemolytic)
#          or "protective_indicator" (higher value → more selective)
# ─────────────────────────────────────────────────────────────────────────────

# Detection AUROCs from the expanded n=179 benchmark (54 hemolytic vs 125 selective).
# Features are listed in descending detection AUROC order.
_RICH_SELECTIVITY_FEATURES: list[tuple[str, float, str]] = [
    ("hydrophobic_fraction",      0.6745, "risk_indicator"),
    ("helix_propensity",          0.6489, "risk_indicator"),
    ("net_charge_ph74",           0.6332, "risk_indicator"),
    ("net_charge_proxy",          0.6394, "risk_indicator"),
    ("interior_trypsin_sites",    0.6089, "risk_indicator"),
    ("longest_repeat_run",        0.5946, "risk_indicator"),
    ("length",                   0.5900, "risk_indicator"),
    ("selectivity_proxy",         0.6095, "protective_indicator"),
]

# Normalisation thresholds for each feature. These are empirical ranges
# observed across the AMP/reference corpus. A feature value at or beyond
# the high end maps to full risk (for risk indicators) or full protection
# (for protective indicators). The thresholds are intentionally wide to
# avoid overfitting to the reference set.
#
# Sources: observed ranges examples/validation/hemolysis_reference.csv.
_NORM_THRESHOLDS: dict[str, tuple[float, float]] = {
    # (low, high) — feature mapped to [0, 1] via linear interpolation/clamp
    "hydrophobic_fraction":   (0.20, 0.60),   # selective ~0.35, hemolytic ~0.55
    "helix_propensity":       (0.50, 1.50),   # selective ~0.8, hemolytic ~1.2
    "net_charge_ph74":        (1.0, 10.0),    # selective ~3, hemolytic ~6+
    "net_charge_proxy":       (1.0, 10.0),    # similar to ph74
    "interior_trypsin_sites": (0.0, 10.0),    # 0 = no sites, 10+ = many
    "longest_repeat_run":     (1.0, 8.0),     # 1 = no repeats, 8+ = extreme
    "length":                 (10, 40),       # 10 = short, 40 = long
    "selectivity_proxy":      (0.0, 1.0),     # already in [0, 1]
}


def _normalise_linear(value: float, lo: float, hi: float) -> float:
    """Linear normalisation to [0, 1], clamped."""
    if hi == lo:
        return 0.5
    return clamp01((value - lo) / (hi - lo))


def rich_selectivity_score(features: dict) -> float:
    """Composite selectivity score [0, 1]. Higher = more selective (lower hemolysis risk).

    Combines 8 physicochemical features that the feature decomposition benchmark
    (v0.5.15) identified as statistically significant for distinguishing hemolytic
    AMPs from selective AMPs (CI excludes 0.5 on n=179).

    For each risk-indicator feature, the normalised value is inverted (high raw
    value → low selectivity). For the protective indicator (the existing
    selectivity_proxy), the raw value is used directly.

    The final score is the weighted mean, with weights proportional to each
    feature's detection AUROC so that stronger discriminators contribute more.

    Args:
        features: dict from compute_features().

    Returns:
        Selectivity score in [0, 1]. Higher = more selective.
        This is a triage signal, NOT a hemolysis predictor.

    Limitations:
        - Individual feature AUROCs are 0.59-0.67 (weak signal);
          the composite may or may not exceed the best single feature.
        - Normalisation thresholds are empirical and may not generalise.
        - The benchmark uses n=179 (54 hemolytic vs 125 selective); CIs are wide.
        - All significant features are risk indicators except selectivity_proxy;
          the composite may simply approximate "high charge + low hydrophobicity".
        - Does not model 3D structure, oligomeric state, or membrane curvature.
    """
    components: dict[str, float] = {}
    total_weight = 0.0

    for feat_name, detection_auroc, direction in _RICH_SELECTIVITY_FEATURES:
        raw = float(features.get(feat_name, 0.0))
        lo, hi = _NORM_THRESHOLDS[feat_name]
        normed = _normalise_linear(raw, lo, hi)

        if direction == "risk_indicator":
            # High raw value → high hemolysis risk → low selectivity
            component = 1.0 - normed
        else:
            # Protective indicator: high raw → high selectivity
            component = normed

        # Weight proportional to detection AUROC (stronger signal = higher weight).
        weight = detection_auroc
        components[feat_name] = round(component, 4)
        total_weight += weight

    if total_weight == 0:
        return 0.5

    score = sum(components[f] * w for (f, w, _) in _RICH_SELECTIVITY_FEATURES) / total_weight
    # Recompute using the components dict to match rounded values
    score = (
        sum(components[feat_name] * det_auroc
            for feat_name, det_auroc, _ in _RICH_SELECTIVITY_FEATURES)
        / total_weight
    )
    return round(clamp01(score), 4)


def rich_selectivity_breakdown(features: dict) -> dict:
    """Return the per-component breakdown of the rich selectivity score.

    Exposes every feature's normalised value, direction, weight, and contribution.
    This makes the score fully auditable: an expert can trace exactly which
    feature axes push a candidate toward or away from selectivity.
    """
    components: dict[str, dict] = {}
    total_weight = 0.0

    for feat_name, detection_auroc, direction in _RICH_SELECTIVITY_FEATURES:
        raw = float(features.get(feat_name, 0.0))
        lo, hi = _NORM_THRESHOLDS[feat_name]
        normed = _normalise_linear(raw, lo, hi)

        if direction == "risk_indicator":
            component = round(1.0 - normed, 4)
        else:
            component = round(normed, 4)

        weight = round(detection_auroc, 4)
        contribution = round(component * detection_auroc, 4)
        total_weight += detection_auroc

        components[feat_name] = {
            "raw_value": raw,
            "normalised": round(normed, 4),
            "direction": direction,
            "component": component,
            "weight": weight,
            "contribution": contribution,
        }

    score = rich_selectivity_score(features)
    return {
        "rich_selectivity_score": score,
        "n_features": len(components),
        "total_weight": round(total_weight, 4),
        "components": components,
        "verdict_source": "feature_decomposition_benchmark_v0.5.15",
        "reference_n": 179,
    }

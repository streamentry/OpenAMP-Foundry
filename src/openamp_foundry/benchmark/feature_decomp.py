"""Feature-decomposition benchmark: which individual physicochemical features
carry selective_vs_hemolytic signal?

The strict triage benchmark (v0.5.14) proved that NO pipeline scorer passes the
selective_vs_hemolytic discrimination test (AUROC 0.43-0.54 for all scorers).
But that benchmark reports only aggregate scores. It does not decompose WHY
the discrimination fails or identify which individual features have signal that
the composite scorers fail to exploit.

This benchmark tests every scalar feature from ``compute_features()`` individually
for selective_vs_hemolytic AUROC, with bootstrap confidence intervals. It answers:

  - Which features have *any* signal for distinguishing selective from hemolytic AMPs?
  - Which direction does each feature's signal point (higher = selective, or higher = hemolytic)?
  - Is the signal statistically significant (CI excludes 0.5)?
  - Which features are being used by the current selectivity proxy, and which are ignored?

The goal is to turn a known aggregate failure into actionable diagnostic information:
the next loop should know exactly which feature axes to combine into a better
selectivity scorer.

Design:
  - Positives (hemolytic): AMPs with HC50 < 25 ug/mL (HEMOLYTIC class).
  - Negatives (selective): AMPs with HC50 >= 100 ug/mL (SELECTIVE class).
  - MODERATE (25 <= HC50 < 100) excluded from binary task, reported separately.
  - For each scalar feature, compute AUROC(hemolytic_scores, selective_scores).
  - AUROC > 0.5 means the feature is higher in hemolytic peptides (risk indicator).
  - AUROC < 0.5 means the feature is higher in selective peptides (protective indicator).
  - The "detection AUROC" for a protective feature is 1 - raw AUROC (so higher = better detection).

All results are computational. No biological activity is implied.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from openamp_foundry.benchmark.retrospective import _auc_wilcoxon, _bootstrap_auroc_ci
from openamp_foundry.features.physchem import compute_features


# Scalar features to test. Excludes residue_counts (dict), which is not scalar.
SCALAR_FEATURES: list[str] = [
    "length",
    "net_charge_proxy",
    "charge_density",
    "net_charge_ph74",
    "charge_density_ph74",
    "hydrophobic_fraction",
    "aromatic_fraction",
    "cysteine_fraction",
    "glycine_fraction",
    "proline_fraction",
    "longest_repeat_run",
    "hydrophobic_moment",
    "max_hydrophobic_moment",
    "helix_propensity",
    "boman_index",
    "gravy",
    "selectivity_proxy",
    "aggregation_propensity",
    "trypsin_site_density",
    "chymotrypsin_site_density",
    "elastase_site_density",
    "interior_trypsin_sites",
    "interior_chymotrypsin_sites",
    "interior_elastase_sites",
    "helix_wheel_hydrophobic_face_mean_h",
    "helix_wheel_hydrophilic_face_mean_h",
    "helix_wheel_face_contrast",
    "helix_wheel_h_face_cationic_fraction",
    "helix_wheel_ph_face_cationic_fraction",
    "helix_wheel_amphipathic_score",
]

# Features used by selectivity_proxy(charge, gravy). These are the features
# the pipeline *currently* relies on for selectivity decisions.
SELECTIVITY_PROXY_INPUTS = {"net_charge_ph74", "gravy", "selectivity_proxy"}


def _load_hemolysis_reference(path: str | Path) -> list[dict[str, Any]]:
    """Load hemolysis_reference.csv and return rows with parsed hc50 and class."""
    rows: list[dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seq = row["sequence"].strip().upper()
            if not all(aa in "ACDEFGHIKLMNPQRSTVWY" for aa in seq):
                continue
            hc50 = float(row["hc50_ugml"])
            hemo_class = row["hemolysis_class"].strip().upper()
            rows.append({
                "id": row["id"],
                "sequence": seq,
                "family": row.get("family", ""),
                "hc50_ugml": hc50,
                "hemolysis_class": hemo_class,
                "reference": row.get("reference", ""),
            })
    return rows


def run_feature_decomposition_benchmark(
    hemolysis_csv: str | Path,
    n_bootstrap: int = 2000,
) -> dict[str, Any]:
    """Test every scalar physicochemical feature for selective_vs_hemolytic signal.

    This benchmark answers: "Which individual features have signal for
    distinguishing hemolytic AMPs from selective AMPs, and which direction?"

    The strict triage benchmark proved no composite scorer passes this test.
    This decomposition identifies which feature axes carry signal that is
    either unused or canceled out by the composite scorers.

    Args:
        hemolysis_csv: CSV with columns id, sequence, family, hc50_ugml,
            hemolysis_class, reference.
        n_bootstrap: Bootstrap resample count for confidence intervals.

    Returns:
        Dict with per-feature AUROC, detection AUROC, CIs, direction,
        significance flags, and an honest verdict.
    """
    rows = _load_hemolysis_reference(hemolysis_csv)

    hemolytic = [r for r in rows if r["hemolysis_class"] == "HEMOLYTIC"]
    selective = [r for r in rows if r["hemolysis_class"] == "SELECTIVE"]
    border = [r for r in rows if r["hemolysis_class"] == "MODERATE"]

    # Compute features for every peptide.
    hemo_features = [
        {**r, "_features": compute_features(r["sequence"])}
        for r in hemolytic
    ]
    sel_features = [
        {**r, "_features": compute_features(r["sequence"])}
        for r in selective
    ]

    per_feature: dict[str, dict[str, Any]] = {}

    for feat_name in SCALAR_FEATURES:
        hemo_vals = [float(r["_features"][feat_name]) for r in hemo_features if feat_name in r["_features"]]
        sel_vals = [float(r["_features"][feat_name]) for r in sel_features if feat_name in r["_features"]]

        if not hemo_vals or not sel_vals:
            continue

        # Raw AUROC: P(hemolytic feature value > selective feature value).
        # > 0.5 means feature is higher in hemolytic peptides (risk indicator).
        # < 0.5 means feature is higher in selective peptides (protective indicator).
        raw_auroc = round(_auc_wilcoxon(hemo_vals, sel_vals), 4)
        ci = _bootstrap_auroc_ci(hemo_vals, sel_vals, n_bootstrap=n_bootstrap)

        # Detection AUROC: always normalized so higher = better hemolysis detection.
        # For risk indicators (raw > 0.5), detection = raw.
        # For protective indicators (raw < 0.5), detection = 1 - raw.
        if raw_auroc >= 0.5:
            direction = "risk_indicator"
            detection_auroc = raw_auroc
            ci_lo = ci["ci_lo"]
            ci_hi = ci["ci_hi"]
        else:
            direction = "protective_indicator"
            detection_auroc = round(1.0 - raw_auroc, 4)
            ci_lo = round(1.0 - ci["ci_hi"], 4)
            ci_hi = round(1.0 - ci["ci_lo"], 4)

        significant = ci_lo > 0.5

        per_feature[feat_name] = {
            "raw_auroc": raw_auroc,
            "detection_auroc": detection_auroc,
            "ci_lo": round(ci_lo, 4),
            "ci_hi": round(ci_hi, 4),
            "direction": direction,
            "significant": significant,
            "n_hemolytic": len(hemo_vals),
            "n_selective": len(sel_vals),
            "used_by_selectivity_proxy": feat_name in SELECTIVITY_PROXY_INPUTS,
        }

    # Rank by detection AUROC (descending).
    ranked = sorted(
        per_feature.items(),
        key=lambda x: x[1]["detection_auroc"],
        reverse=True,
    )

    # Identify features with significant signal.
    significant_features = [
        {
            "feature": name,
            "detection_auroc": info["detection_auroc"],
            "direction": info["direction"],
            "ci": [info["ci_lo"], info["ci_hi"]],
        }
        for name, info in ranked
        if info["significant"]
    ]

    # Identify features used by selectivity_proxy.
    proxy_features = [
        name for name, info in per_feature.items()
        if info["used_by_selectivity_proxy"]
    ]
    # Features with signal NOT used by the selectivity proxy.
    unused_signal = [
        {
            "feature": name,
            "detection_auroc": info["detection_auroc"],
            "direction": info["direction"],
            "ci": [info["ci_lo"], info["ci_hi"]],
        }
        for name, info in ranked
        if info["significant"] and not info["used_by_selectivity_proxy"]
    ]

    # Features used by proxy but with no significant signal.
    proxy_no_signal = [
        name for name, info in per_feature.items()
        if info["used_by_selectivity_proxy"] and not info["significant"]
    ]

    best_feature = ranked[0][0] if ranked else "none"
    best_auroc = ranked[0][1]["detection_auroc"] if ranked else 0.5

    # Honest verdict.
    n_sig = len(significant_features)
    if n_sig == 0:
        verdict = (
            "No individual physicochemical feature has statistically significant "
            "signal for selective_vs_hemolytic discrimination (all CIs include 0.5). "
            "The selectivity failure is not caused by a single unused feature — it "
            "reflects a fundamental limitation of 1D physicochemical descriptors "
            "for this task. 3D structural modelling or sequence-pattern features "
            "may be needed."
        )
    elif n_sig <= 3:
        verdict = (
            f"Only {n_sig} feature(s) have significant selective_vs_hemolytic signal "
            f"(best: {best_feature} at {best_auroc:.4f}). The signal is weak and "
            "sparse. The selectivity proxy currently relies on charge and GRAVY, "
            "which may miss the structural specificity of membrane interaction. "
            f"{len(unused_signal)} significant feature(s) are NOT used by the "
            "selectivity proxy — combining these may improve discrimination."
        )
    else:
        verdict = (
            f"{n_sig} features have significant selective_vs_hemolytic signal "
            f"(best: {best_feature} at {best_auroc:.4f}). The selectivity proxy "
            f"uses only {len(proxy_features)} of these ({', '.join(proxy_features)}). "
            f"{len(unused_signal)} significant feature(s) are NOT used. A richer "
            "selectivity scorer combining these axes could outperform the current proxy."
        )

    return {
        "benchmark": "feature_decomposition_selectivity",
        "n_hemolytic": len(hemolytic),
        "n_selective": len(selective),
        "n_border": len(border),
        "n_features_tested": len(per_feature),
        "n_significant": n_sig,
        "best_feature": best_feature,
        "best_detection_auroc": best_auroc,
        "significant_features": significant_features,
        "unused_signal_features": unused_signal,
        "proxy_features_without_signal": proxy_no_signal,
        "per_feature": {
            name: {
                "raw_auroc": info["raw_auroc"],
                "detection_auroc": info["detection_auroc"],
                "ci_lo": info["ci_lo"],
                "ci_hi": info["ci_hi"],
                "direction": info["direction"],
                "significant": info["significant"],
                "used_by_selectivity_proxy": info["used_by_selectivity_proxy"],
            }
            for name, info in ranked
        },
        "verdict": verdict,
    }

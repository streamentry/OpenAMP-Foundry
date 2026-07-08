"""Calibration benchmark: does the pipeline's ensemble score mean anything probabilistically?

AUROC measures ranking quality but says nothing about calibration.
A score of 0.8 should mean ~80% of candidates with that score are truly active.

This benchmark computes:
  - Brier score (mean squared error between prediction and label)
  - Brier skill score (vs always-predicting-mean)
  - Reliability diagram bins (predicted vs actual frequency)
  - Calibration slope and intercept (ideal: slope=1, intercept=0)

Usage:
    python scripts/benchmarks/benchmark_calibration.py
    make bench-calibration
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from openamp_foundry.data.loaders import load_candidates_csv
from openamp_foundry.pipeline import score_candidates


def compute_calibration_metrics(
    amp_csv: str = "examples/validation/known_amps.csv",
    decoy_csv: str = "examples/validation/random_background.csv",
    config_path: str = "configs/pipeline.yaml",
    n_bins: int = 10,
) -> dict:
    amps = load_candidates_csv(amp_csv)
    amped_ids = {a.candidate_id for a in amps}
    decoys = load_candidates_csv(decoy_csv)

    # Score all candidates together (pipeline doesn't need labels)
    all_candidates = amps + decoys
    tmp_csv = Path("/tmp/_calib_candidates.csv")
    tmp_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp_csv, "w") as f:
        f.write("id,sequence,source\n")
        for c in all_candidates:
            f.write(f"{c.candidate_id},{c.sequence},calib\n")

    scored, _ = score_candidates(str(tmp_csv), config_path=config_path)

    predictions = []
    labels = []
    for item in scored:
        pred = item.scores.get("ensemble", 0.5)
        label = 1.0 if item.candidate.candidate_id in amped_ids else 0.0
        predictions.append(pred)
        labels.append(label)

    n = len(predictions)
    if n == 0:
        return {"error": "no candidates scored"}

    # Brier score = mean((pred - label)^2)
    brier = sum((p - l) ** 2 for p, l in zip(predictions, labels)) / n
    base_rate = sum(labels) / n
    brier_ref = base_rate * (1.0 - base_rate)  # always-predict-mean
    brier_skill = 1.0 - (brier / brier_ref) if brier_ref > 0 else 0.0

    # Reliability diagram
    bin_edges = [i / n_bins for i in range(n_bins + 1)]
    bins = {i: {"count": 0, "sum_pred": 0.0, "sum_label": 0.0} for i in range(n_bins)}
    for pred, label in zip(predictions, labels):
        bin_idx = min(int(pred * n_bins), n_bins - 1)
        bins[bin_idx]["count"] += 1
        bins[bin_idx]["sum_pred"] += pred
        bins[bin_idx]["sum_label"] += label

    reliability = []
    for i in range(n_bins):
        b = bins[i]
        if b["count"] == 0:
            continue
        mean_pred = b["sum_pred"] / b["count"]
        actual = b["sum_label"] / b["count"]
        reliability.append({
            "bin": i,
            "range": f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}",
            "count": b["count"],
            "mean_prediction": round(mean_pred, 4),
            "actual_fraction": round(actual, 4),
            "gap": round(mean_pred - actual, 4),
        })

    # Calibration slope and intercept (linear regression: actual ~ prediction)
    weighted_sum_pred = 0.0
    weighted_sum_actual = 0.0
    weighted_sum_pred2 = 0.0
    weighted_sum_pred_actual = 0.0
    total_weight = 0.0
    for p, a in zip(predictions, labels):
        w = 1.0
        weighted_sum_pred += w * p
        weighted_sum_actual += w * a
        weighted_sum_pred2 += w * p * p
        weighted_sum_pred_actual += w * p * a
        total_weight += w
    if total_weight * weighted_sum_pred2 - weighted_sum_pred ** 2 > 0:
        slope = (
            (total_weight * weighted_sum_pred_actual - weighted_sum_pred * weighted_sum_actual)
            / (total_weight * weighted_sum_pred2 - weighted_sum_pred ** 2)
        )
        intercept = (weighted_sum_actual - slope * weighted_sum_pred) / total_weight
    else:
        slope = 0.0
        intercept = 0.0

    # Decomposition: Brier = reliability + resolution + uncertainty
    reliability_term = 0.0
    resolution_term = 0.0
    for b in reliability:
        n_k = b["count"]
        p_k = b["mean_prediction"]
        o_k = b["actual_fraction"]
        reliability_term += n_k * (p_k - o_k) ** 2
        resolution_term += n_k * (o_k - base_rate) ** 2
    reliability_term /= n
    resolution_term /= n
    uncertainty_term = base_rate * (1.0 - base_rate)

    return {
        "n_candidates": n,
        "n_amps": sum(labels),
        "n_decoys": n - sum(labels),
        "brier_score": round(brier, 4),
        "brier_skill_score": round(brier_skill, 4),
        "base_rate": round(base_rate, 4),
        "brier_decomposition": {
            "reliability": round(reliability_term, 4),
            "resolution": round(resolution_term, 4),
            "uncertainty": round(uncertainty_term, 4),
        },
        "calibration_slope": round(slope, 4),
        "calibration_intercept": round(intercept, 4),
        "reliability_diagram": reliability,
    }


def print_report(metrics: dict) -> None:
    if "error" in metrics:
        print(f"Error: {metrics['error']}")
        return

    print("=" * 65)
    print("PIPELINE CALIBRATION BENCHMARK")
    print("=" * 65)
    print(f"\nDataset: {metrics['n_amps']} AMPs, {metrics['n_decoys']} decoys")
    print(f"Base rate: {metrics['base_rate']}")
    print()
    print("--- Brier Score ---")
    print(f"  Brier score:         {metrics['brier_score']} (0=perfect, >0.25=uninformative)")
    print(f"  Brier skill score:   {metrics['brier_skill_score']} (1=perfect, 0=no better than mean)")
    print()
    d = metrics["brier_decomposition"]
    print("  Decomposition:")
    print(f"    Reliability:  {d['reliability']} (calibration error)")
    print(f"    Resolution:   {d['resolution']} (ability to separate)")
    print(f"    Uncertainty:  {d['uncertainty']} (base rate entropy)")
    print(f"    Sum:          {round(d['reliability'] - d['resolution'] + d['uncertainty'], 4)} (should = Brier)")
    print()
    print("--- Calibration Slope ---")
    print(f"  Slope:     {metrics['calibration_slope']} (ideal=1.0)")
    print(f"  Intercept: {metrics['calibration_intercept']} (ideal=0.0)")
    if metrics['calibration_slope'] < 0.8:
        print("  ⚠ Slope < 0.8: scores may be over-confident (too extreme)")
    elif metrics['calibration_slope'] > 1.2:
        print("  ⚠ Slope > 1.2: scores may be under-confident (too conservative)")
    else:
        print("  ✓ Slope near 1.0: scores approximately calibrated")
    print()
    print("--- Reliability Diagram ---")
    print(f"  {'Bin':>5s} {'Range':>10s} {'Count':>7s} {'Predicted':>10s} {'Actual':>10s} {'Gap':>8s}")
    print(f"  {'-'*5} {'-'*10} {'-'*7} {'-'*10} {'-'*10} {'-'*8}")
    for b in metrics["reliability_diagram"]:
        gap_mark = " ⚠" if abs(b["gap"]) > 0.1 else ""
        print(f"  {b['bin']:>5d} {b['range']:>10s} {b['count']:>7d} {b['mean_prediction']:>10.4f} {b['actual_fraction']:>10.4f} {b['gap']:>8.4f}{gap_mark}")
    print()
    print("Limitations:")
    print("  - Binary labels (AMP vs decoy) are proxies for 'activity'.")
    print("  - Decoys are random sequences — real inactives may differ.")
    print("  - Calibration on benchmark data may not generalize to novel candidates.")
    print("  - Low Brier score does not imply biological validity.")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline calibration benchmark")
    parser.add_argument("--amp-csv", default="examples/validation/known_amps.csv")
    parser.add_argument("--decoy-csv", default="examples/validation/random_background.csv")
    parser.add_argument("--config", default="configs/pipeline.yaml")
    args = parser.parse_args()

    metrics = compute_calibration_metrics(
        amp_csv=args.amp_csv,
        decoy_csv=args.decoy_csv,
        config_path=args.config,
    )
    print_report(metrics)
    return 0


if __name__ == "__main__":
    sys.exit(main())

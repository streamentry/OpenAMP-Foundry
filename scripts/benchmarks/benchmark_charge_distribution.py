"""Report charge distribution for AMP and decoy sets in a benchmark.

Usage:
    python scripts/benchmarks/benchmark_charge_distribution.py \\
        --amp-csv examples/validation/known_amps_500.csv \\
        --decoy-csv examples/validation/random_background_500.csv
    make bench-charge-distribution
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from openamp_foundry.data.loaders import load_candidates_csv
from openamp_foundry.features.physchem import compute_features


def charge_distribution(csv_path: str, label: str) -> dict:
    candidates = load_candidates_csv(csv_path)
    charges = []
    for c in candidates:
        features = compute_features(c.sequence)
        charges.append(features.get("charge_density_ph74", 0.0))
    if not charges:
        return {"label": label, "count": 0}
    n = len(charges)
    mean = sum(charges) / n
    sorted_c = sorted(charges)
    median = sorted_c[n // 2] if n % 2 else (sorted_c[n // 2 - 1] + sorted_c[n // 2]) / 2
    return {
        "label": label,
        "count": n,
        "mean_charge": round(mean, 4),
        "median_charge": round(median, 4),
        "min_charge": round(min(charges), 4),
        "max_charge": round(max(charges), 4),
        "fraction_positive": round(sum(1 for c in charges if c > 0) / n, 4),
        "fraction_negative": round(sum(1 for c in charges if c < 0) / n, 4),
        "fraction_neutral": round(sum(1 for c in charges if c == 0) / n, 4),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark charge distribution report")
    parser.add_argument("--amp-csv", required=True, help="CSV of known AMPs")
    parser.add_argument("--decoy-csv", required=True, help="CSV of decoy peptides")
    args = parser.parse_args(argv)

    amp = charge_distribution(args.amp_csv, "AMP")
    decoy = charge_distribution(args.decoy_csv, "Decoy")

    print("=== Charge Distribution Report ===")
    print()
    print(f"{'Metric':25s} {'AMP':>12s} {'Decoy':>12s}")
    print("-" * 51)
    for key in ["count", "mean_charge", "median_charge", "min_charge", "max_charge",
                "fraction_positive", "fraction_negative", "fraction_neutral"]:
        a = amp.get(key, "")
        d = decoy.get(key, "")
        print(f"{key:25s} {str(a):>12s} {str(d):>12s}")
    print()
    overlap = "HIGH" if abs(amp["mean_charge"] - decoy["mean_charge"]) < 0.1 else "LOW"
    print(f"Charge overlap risk: {overlap}")
    print("(HIGH overlap means charge-based shortcuts may not inflate benchmark scores)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

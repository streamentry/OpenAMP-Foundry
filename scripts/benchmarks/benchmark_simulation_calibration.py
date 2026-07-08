"""Simulation uncertainty calibration report.

Evaluates whether simulation proxy uncertainty estimates are
meaningful (non-constant, correlated with sequence properties)
or suspicious (constant across all inputs, too low for edge cases).

Usage:
    python scripts/benchmarks/benchmark_simulation_calibration.py
    make bench-simulation-calibration
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from openamp_foundry.simulation.membrane import MembraneProxy
from openamp_foundry.simulation.structure import StructureProxy

TEST_SEQUENCES = [
    ("Helical AMP (Magainin-2)", "GIGKFLHSAKKFGKAFVGEIMNS"),
    ("Hemolytic (Melittin)", "GIGAVLKVLTTGLPALISWIKRKRQQ"),
    ("Beta-sheet (Protegrin)", "RGGRLCYCRRRFCVCVGR"),
    ("Human cathelicidin (LL-37)", "LLGDFFRKSKEKIGKEFKRIVQRIKDFLRNLVPRTES"),
    ("Pro-rich (Indolicidin)", "ILPWKWPWWPWRR"),
    ("Short poly-K", "KKK"),
    ("Short poly-G", "GGG"),
    ("Single alanine", "A"),
    ("Poly-proline (15-mer)", "P" * 15),
    ("Poly-cysteine (10-mer)", "C" * 10),
    ("Mixed 20-mer", "ACDEFGHIKLMNPQRSTVWY"),
    ("Long poly-K (50-mer)", "K" * 50),
]

UNCERTAINTY_TIER = [
    (0.0, 0.2, "low"),
    (0.2, 0.5, "moderate"),
    (0.5, 0.8, "high"),
    (0.8, 1.01, "very_high"),
]


def _tier_name(val: float) -> str:
    for lo, hi, name in UNCERTAINTY_TIER:
        if lo <= val < hi:
            return name
    return "unknown"


def compute_calibration() -> dict:
    membrane = MembraneProxy()
    structure = StructureProxy()
    proxy_results = {"membrane_proxy": [], "structure_proxy": []}

    for label, seq in TEST_SEQUENCES:
        mem_result = membrane.simulate(seq)
        struct_result = structure.simulate(seq)
        proxy_results["membrane_proxy"].append({
            "label": label,
            "length": len(seq),
            "uncertainty": mem_result.uncertainty,
            "tier": _tier_name(mem_result.uncertainty),
        })
        proxy_results["structure_proxy"].append({
            "label": label,
            "length": len(seq),
            "uncertainty": struct_result.uncertainty,
            "tier": _tier_name(struct_result.uncertainty),
        })

    report = {"proxies": {}, "flags": []}
    for proxy_name, results in proxy_results.items():
        uncertainties = [r["uncertainty"] for r in results]
        n = len(uncertainties)
        mean = sum(uncertainties) / n
        sorted_u = sorted(uncertainties)
        median = sorted_u[n // 2] if n % 2 else (sorted_u[n // 2 - 1] + sorted_u[n // 2]) / 2
        variance = sum((u - mean) ** 2 for u in uncertainties) / n
        std_dev = math.sqrt(variance)

        lengths = [r["length"] for r in results]
        # Pearson correlation between length and uncertainty
        if n > 2 and std_dev > 0 and max(uncertainties) > min(uncertainties):
            n_float = float(n)
            sum_x = sum(lengths)
            sum_y = sum(uncertainties)
            sum_xy = sum(x * y for x, y in zip(lengths, uncertainties))
            sum_x2 = sum(x * x for x in lengths)
            sum_y2 = sum(y * y for y in uncertainties)
            r_num = n_float * sum_xy - sum_x * sum_y
            r_den = math.sqrt((n_float * sum_x2 - sum_x * sum_x) * (n_float * sum_y2 - sum_y * sum_y))
            length_corr = round(r_num / r_den, 4) if r_den > 0 else 0.0
        else:
            length_corr = 0.0

        unique_tiers = set(r["tier"] for r in results)
        tier_counts = {}
        for r in results:
            tier_counts[r["tier"]] = tier_counts.get(r["tier"], 0) + 1

        report["proxies"][proxy_name] = {
            "n_sequences": n,
            "mean_uncertainty": round(mean, 4),
            "median_uncertainty": round(median, 4),
            "min_uncertainty": round(min(uncertainties), 4),
            "max_uncertainty": round(max(uncertainties), 4),
            "std_uncertainty": round(std_dev, 4),
            "length_correlation": length_corr,
            "tier_counts": tier_counts,
            "samples": results,
        }

        # Flag suspicious patterns
        if std_dev < 0.01:
            report["flags"].append(
                f"{proxy_name}: uncertainty variance near zero ({std_dev:.4f}) — "
                "estimate may not be informative"
            )
        if max(uncertainties) < 0.3:
            report["flags"].append(
                f"{proxy_name}: max uncertainty {max(uncertainties):.4f} is below 0.3 — "
                "may under-report uncertainty for edge cases"
            )
        if length_corr > -0.1:
            report["flags"].append(
                f"{proxy_name}: length correlation is {length_corr} (expected negative) — "
                "uncertainty should decrease with length"
            )

    return report


def print_report(report: dict) -> None:
    print("=" * 70)
    print("SIMULATION UNCERTAINTY CALIBRATION REPORT")
    print("=" * 70)
    print()

    for proxy_name, proxy_data in report["proxies"].items():
        print(f"--- {proxy_name} ---")
        print(f"  Sequences tested:      {proxy_data['n_sequences']}")
        print(f"  Mean uncertainty:      {proxy_data['mean_uncertainty']}")
        print(f"  Median uncertainty:    {proxy_data['median_uncertainty']}")
        print(f"  Min uncertainty:       {proxy_data['min_uncertainty']}")
        print(f"  Max uncertainty:       {proxy_data['max_uncertainty']}")
        print(f"  Std uncertainty:       {proxy_data['std_uncertainty']}")
        print(f"  Length correlation:    {proxy_data['length_correlation']} (negative = uncertainty drops as length increases)")
        print(f"  Tier distribution:     {proxy_data['tier_counts']}")
        print()
        print(f"  {'Label':30s} {'Length':>7s} {'Uncertainty':>12s} {'Tier':>12s}")
        print(f"  {'-'*30} {'-'*7} {'-'*12} {'-'*12}")
        for s in proxy_data["samples"]:
            print(f"  {s['label']:30s} {s['length']:>7d} {s['uncertainty']:>12.4f} {s['tier']:>12s}")
        print()

    if report["flags"]:
        print("--- FLAGS (potential issues) ---")
        for flag in report["flags"]:
            print(f"  ⚠ {flag}")
        print()
    else:
        print("No flags — uncertainty estimates appear well-calibrated.")
        print()

    print("Limitations:")
    print("  - Report uses toy/demo sequences, not validated against wet-lab data.")
    print("  - 'Calibration' here means internal consistency, not biological accuracy.")
    print("  - Low uncertainty does not imply biological accuracy.")
    print("  - High uncertainty for short sequences is expected and appropriate.")


def main() -> int:
    report = compute_calibration()
    print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())

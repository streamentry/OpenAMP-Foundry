"""Compare all advanced scorers/simulators against declared cheap baselines.

Usage:
    python scripts/benchmarks/benchmark_cheap_enemy_comparison.py
    make bench-cheap-enemies
"""
from __future__ import annotations

import sys
from pathlib import Path

from openamp_foundry.simulation.membrane import MembraneProxy
from openamp_foundry.simulation.structure import StructureProxy

TEST_SEQUENCES = [
    ("Magainin-2 (helical AMP)", "GIGKFLHSAKKFGKAFVGEIMNS"),
    ("Melittin (hemolytic)", "GIGAVLKVLTTGLPALISWIKRKRQQ"),
    ("Protegrin-1 (beta-sheet AMP)", "RGGRLCYCRRRFCVCVGR"),
    ("LL-37 (human cathelicidin)", "LLGDFFRKSKEKIGKEFKRIVQRIKDFLRNLVPRTES"),
    ("Indolicidin (proline-rich)", "ILPWKWPWWPWRR"),
    ("Poly-K (charge control)", "KKKKKKKKKK"),
    ("Poly-G (neutral control)", "GGGGGGGGGG"),
    ("Poly-A (minimal)", "AAAAAAAAAA"),
]

REMOTE_SCORERS = [
    ("activity_likeness", "charge density alone"),
    ("safety_score", "sequence length alone"),
]


def run_comparison() -> list[dict]:
    results = []
    proxies = [
        ("MembraneProxy", MembraneProxy()),
        ("StructureProxy", StructureProxy()),
    ]
    for name, proxy in proxies:
        baseline_desc = proxy.cheapest_baseline_description
        baseline = proxy.get_baseline()
        for label, seq in TEST_SEQUENCES:
            sim_result = proxy.simulate(seq)
            baseline_score = baseline.evaluate(seq)
            results.append({
                "proxy": name,
                "sequence_label": label,
                "baseline_description": baseline_desc,
                "sim_score": sim_result.scores,
                "baseline_score": round(baseline_score, 4),
                "uncertainty": sim_result.uncertainty,
            })
    return results


def main() -> int:
    results = run_comparison()
    print(f"Cheap enemy comparison ({len(results)} rows)\n")
    print(f"{'Proxy':20s} {'Sequence':30s} {'Baseline':40s} {'Sim Score':30s} {'Base Score':10s} {'Uncertainty':10s}")
    print("-" * 140)
    for r in results:
        sim_str = str(r["sim_score"])[:28]
        print(f"{r['proxy']:20s} {r['sequence_label']:30s} {r['baseline_description']:40s} {sim_str:30s} {r['baseline_score']:<10.4f} {r['uncertainty']:<10.4f}")
    print()
    beat_count = sum(1 for r in results if r["baseline_score"] < 0.5)
    total = len(results)
    print(f"Results where baseline score < 0.5 (sim beats weak baseline): {beat_count}/{total}")
    print("Note: This comparison is informational. Beating a weak baseline does not imply biological validity.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

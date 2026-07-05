#!/usr/bin/env python3
"""Per-family benchmark breakdown: stratify AMP benchmark by structural class.

The current benchmark reports a single AUROC for all 500 AMPs. This benchmark
splits the AMP set by heuristic structural class and reports per-class AUROC
to identify which AMP classes the pipeline handles well/poorly.

Classification rules (mutually exclusive, priority order):
  1. cysteine_rich: ≥2 C residues (β-sheet / disulfide-stabilised)
  2. proline_rich: Pro fraction ≥ 0.15 (polyproline / extended)
  3. short: length ≤ 12 AA
  4. highly_cationic: net charge pH 7.4 ≥ 4.0
  5. moderately_cationic: net charge pH 7.4 2.0–3.9
  6. low_charge: net charge pH 7.4 < 2.0
  7. all_amps: full set (baseline comparison)

Usage:
  python scripts/benchmark_per_family.py [--out report.json]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

from openamp_foundry.features.physchem import compute_features
from openamp_foundry.selection.structural_class import classify_structural_class
from openamp_foundry.scoring.activity import activity_likeness_score
from openamp_foundry.scoring.boman import boman_activity_score
from openamp_foundry.scoring.ensemble import ensemble_score
from openamp_foundry.scoring.novelty import novelty_score
from openamp_foundry.scoring.safety import safety_score
from openamp_foundry.scoring.synthesis import synthesis_feasibility_score
from openamp_foundry.config import load_config

STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")
DECOY_CSV = "examples/validation/random_background_500.csv"
MIN_CLASS_SIZE = 5


def _auc_wilcoxon(pos_scores: list[float], neg_scores: list[float]) -> float:
    n_pos, n_neg = len(pos_scores), len(neg_scores)
    if n_pos == 0 or n_neg == 0:
        return 0.5
    concordant = sum(
        1 for p in pos_scores for n in neg_scores if p > n
    ) + 0.5 * sum(
        1 for p in pos_scores for n in neg_scores if p == n
    )
    return concordant / (n_pos * n_neg)


def _bootstrap_auroc_ci(
    pos_scores: list[float],
    neg_scores: list[float],
    n_bootstrap: int = 2000,
    seed: int = 0,
) -> dict:
    import random as _random
    rng = _random.Random(seed)
    n_pos, n_neg = len(pos_scores), len(neg_scores)
    if n_pos == 0 or n_neg == 0:
        return {"mean": 0.5, "ci_lo": 0.5, "ci_hi": 0.5, "n_bootstrap": 0}
    samples = []
    for _ in range(n_bootstrap):
        pos_s = [rng.choice(pos_scores) for _ in range(n_pos)]
        neg_s = [rng.choice(neg_scores) for _ in range(n_neg)]
        samples.append(_auc_wilcoxon(pos_s, neg_s))
    samples.sort()
    lo_idx = int(0.025 * n_bootstrap)
    hi_idx = int(0.975 * n_bootstrap)
    return {
        "mean": round(sum(samples) / len(samples), 4),
        "ci_lo": round(samples[lo_idx], 4),
        "ci_hi": round(samples[hi_idx], 4),
        "n_bootstrap": n_bootstrap,
    }


def classify_amp(seq: str, features: dict) -> str:
    return classify_structural_class(seq, features)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Per-family benchmark breakdown by structural class."
    )
    parser.add_argument("--out", default=None, help="Path to write JSON report")
    parser.add_argument("--config", default="configs/pipeline.yaml", help="Pipeline config")
    parser.add_argument(
        "--amp-csv", default="examples/validation/known_amps_500.csv",
        help="AMP set CSV",
    )
    parser.add_argument(
        "--decoy-csv", default=DECOY_CSV,
        help="Decoy set CSV",
    )
    args = parser.parse_args(argv)

    print("=== Per-Family Benchmark Breakdown ===")
    config = load_config(args.config)
    weights = config["weights"]
    t_start = time.time()

    # 1. Load and score all AMPs
    amp_classes: dict[str, list[dict]] = {}
    amp_all: list[dict] = []

    with open(args.amp_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seq = row["sequence"].strip().upper()
            if not all(c in STANDARD_AA for c in seq):
                continue
            features = compute_features(seq)
            cls = classify_amp(seq, features)
            act = activity_likeness_score(features)
            safe = safety_score(features)
            valid = all(c in STANDARD_AA for c in seq)
            synth = synthesis_feasibility_score(features, valid_sequence=valid)
            nov, _ = novelty_score(seq, [])
            boman_act = boman_activity_score(seq)
            raw = {
                "activity": act, "safety": safe,
                "synthesis": synth, "novelty": nov,
                "boman_activity": boman_act,
                "disagreement": abs(act - boman_act),
            }
            raw["ensemble"] = ensemble_score(raw, weights)
            entry = {
                "id": row["id"],
                "sequence": seq,
                "class": cls,
                "family": row.get("family", ""),
                "ensemble": raw["ensemble"],
                "length": features.get("length", len(seq)),
                "net_charge": features.get("net_charge_ph74", 0.0),
                "cysteine_count": seq.upper().count("C"),
                "proline_fraction": round(features.get("proline_fraction", 0.0) or 0.0, 3),
            }
            amp_classes.setdefault(cls, []).append(entry)
            amp_all.append(entry)

    # 2. Load and score decoys
    decoy_all: list[dict] = []
    with open(args.decoy_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seq = row["sequence"].strip().upper()
            if not all(c in STANDARD_AA for c in seq):
                continue
            features = compute_features(seq)
            act = activity_likeness_score(features)
            safe = safety_score(features)
            valid = all(c in STANDARD_AA for c in seq)
            synth = synthesis_feasibility_score(features, valid_sequence=valid)
            nov, _ = novelty_score(seq, [])
            boman_act = boman_activity_score(seq)
            raw = {
                "activity": act, "safety": safe,
                "synthesis": synth, "novelty": nov,
                "boman_activity": boman_act,
                "disagreement": abs(act - boman_act),
            }
            raw["ensemble"] = ensemble_score(raw, weights)
            decoy_all.append({
                "id": row["id"],
                "sequence": seq,
                "ensemble": raw["ensemble"],
            })

    decoy_scores = [r["ensemble"] for r in decoy_all]

    # 3. Per-class AUROC
    results: dict[str, dict] = {}

    # Baseline: all AMPs vs all decoys
    all_pos = [r["ensemble"] for r in amp_all]
    results["all_amps"] = {
        "label": "all_amps",
        "description": "Full AMP set (baseline)",
        "n_amps": len(amp_all),
        "n_decoys": len(decoy_all),
        "auroc": round(_auc_wilcoxon(all_pos, decoy_scores), 4),
        "ci95_lo": _bootstrap_auroc_ci(all_pos, decoy_scores)["ci_lo"],
        "ci95_hi": _bootstrap_auroc_ci(all_pos, decoy_scores)["ci_hi"],
        "mean_ensemble": round(sum(all_pos) / len(all_pos), 4),
    }

    class_order = [
        "cysteine_rich", "proline_rich", "short",
        "highly_cationic", "moderately_cationic", "low_charge",
    ]
    class_descriptions = {
        "cysteine_rich": "≥2 Cys residues — β-sheet / disulfide-stabilised",
        "proline_rich": "Pro fraction ≥ 0.15 — polyproline / extended",
        "short": "Length ≤ 12 AA",
        "highly_cationic": "Net charge pH 7.4 ≥ 4.0",
        "moderately_cationic": "Net charge pH 7.4 2.0–3.9",
        "low_charge": "Net charge pH 7.4 < 2.0",
    }

    for cls in class_order:
        members = amp_classes.get(cls, [])
        if len(members) < MIN_CLASS_SIZE:
            continue
        pos = [r["ensemble"] for r in members]
        auroc = round(_auc_wilcoxon(pos, decoy_scores), 4)
        ci = _bootstrap_auroc_ci(pos, decoy_scores)
        delta = round(auroc - results["all_amps"]["auroc"], 4)
        n_cys_2plus = sum(1 for r in members if r["cysteine_count"] >= 2)
        n_pro_rich = sum(1 for r in members if r["proline_fraction"] >= 0.15)
        results[cls] = {
            "label": cls,
            "description": class_descriptions.get(cls, ""),
            "n_amps": len(members),
            "n_decoys": len(decoy_all),
            "auroc": auroc,
            "ci95_lo": ci["ci_lo"],
            "ci95_hi": ci["ci_hi"],
            "delta_vs_all": delta,
            "mean_ensemble": round(sum(pos) / len(pos), 4),
            "mean_length": round(sum(r["length"] for r in members) / len(members), 1),
            "mean_charge": round(sum(r["net_charge"] for r in members) / len(members), 2),
            "cysteine_amp_count": n_cys_2plus,
            "proline_amp_count": n_pro_rich,
        }

    # 4. Print report
    print(f"\n{'='*70}")
    print(f"Per-Class Benchmark (n={len(amp_all)} AMPs, {len(decoy_all)} decoys)")
    print(f"{'='*70}")

    print(f"\nBaseline (all AMPs): AUROC {results['all_amps']['auroc']:.4f} "
          f"(CI: {results['all_amps']['ci95_lo']:.4f}-{results['all_amps']['ci95_hi']:.4f})")

    print(f"\n{'Class':<22} {'N':>4} {'AUROC':>8} {'CI_lo':>8} {'CI_hi':>8} {'ΔvsAll':>8} {'MeanEns':>8} {'Len':>4}")
    print("-" * 70)
    for cls in class_order:
        r = results.get(cls)
        if r is None:
            continue
        print(f"{cls:<22} {r['n_amps']:>4} {r['auroc']:>8.4f} {r['ci95_lo']:>8.4f} {r['ci95_hi']:>8.4f} "
              f"{r['delta_vs_all']:>+8.4f} {r['mean_ensemble']:>8.4f} {r['mean_length']:>4.0f}")

    # 5. Class distribution (all classes, including below MIN_CLASS_SIZE)
    print("\nClass distribution (all AMPs):")
    all_class_counts = Counter(r["class"] for r in amp_all)
    for cls, count in all_class_counts.most_common():
        r = results.get(cls)
        auroc_str = f"AUROC {r['auroc']:.4f}" if r else "N/A (< min size)"
        delta_str = f"(Δ={r['delta_vs_all']:+.4f})" if r else ""
        print(f"  {cls:<22} {count:>4} AMPs  {auroc_str} {delta_str}")

    # 6. Key findings
    print(f"\n{'='*70}")
    print("Key Findings")
    print(f"{'='*70}")

    best_cls = max(class_order, key=lambda c: results[c]["auroc"] if c in results else 0)
    worst_cls = min(class_order, key=lambda c: results[c]["auroc"] if c in results else 1)

    print(f"  Best-handled class: {best_cls} (AUROC {results[best_cls]['auroc']:.4f}, "
          f"Δ={results[best_cls]['delta_vs_all']:+.4f})")
    print(f"  Worst-handled class: {worst_cls} (AUROC {results[worst_cls]['auroc']:.4f}, "
          f"Δ={results[worst_cls]['delta_vs_all']:+.4f})")

    weak_classes = [c for c in class_order if c in results and results[c]["auroc"] < 0.70]
    strong_classes = [c for c in class_order if c in results and results[c]["auroc"] >= 0.80]

    if weak_classes:
        print("  Weak discrimination (AUROC < 0.70):")
        for c in weak_classes:
            r = results[c]
            print(f"    - {c} ({r['auroc']:.4f}, n={r['n_amps']}): {r['description']}")

    if strong_classes:
        print("  Strong discrimination (AUROC ≥ 0.80):")
        for c in strong_classes:
            r = results[c]
            print(f"    - {c} ({r['auroc']:.4f}, n={r['n_amps']}): {r['description']}")

    print(f"\nElapsed: {time.time() - t_start:.1f}s")

    # 7. Compile report
    report = {
        "benchmark": "per_family_breakdown",
        "config": args.config,
        "amp_csv": args.amp_csv,
        "decoy_csv": args.decoy_csv,
        "n_amps_total": len(amp_all),
        "n_decoys": len(decoy_all),
        "class_distribution": dict(all_class_counts.most_common()),
        "min_class_size": MIN_CLASS_SIZE,
        "results": results,
        "weak_classes": weak_classes,
        "strong_classes": strong_classes,
        "best_class": best_cls if best_cls in results else None,
        "worst_class": worst_cls if worst_cls in results else None,
        "interpretation": (
            f"Best class: {best_cls} (AUROC {results[best_cls]['auroc']:.4f}). "
            f"Worst class: {worst_cls} (AUROC {results[worst_cls]['auroc']:.4f}). "
            + (f"Classes below 0.70: {', '.join(weak_classes)}. Potential blind spots."
               if weak_classes else "No classes below 0.70 — pipeline generalises across structural classes.")
        ),
        "elapsed_seconds": round(time.time() - t_start, 1),
    }

    print("\n" + json.dumps(report, indent=2))

    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())

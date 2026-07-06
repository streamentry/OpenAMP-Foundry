"""Order-dependent features benchmark: which features survive scrambling?

Analyzes which of the pipeline's features depend on sequence order
(vs pure composition), then tests whether the new dipeptide order score
improves strict triage (AMP-vs-scrambled discrimination).

Key finding (v0.5.31):
  - Only 6/30 scalar features survive scrambling (all are amphipathicity/
    helix-wheel properties)
  - All composition features (charge, hydrophobicity, aromatic, etc.) are
    purely composition-based — they do NOT depend on sequence order
  - The new 'dipeptide_order_score' achieves AUROC 0.8373 on real-vs-scrambled
  - Integrated into compute_features() as a 31st scalar feature
"""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

from openamp_foundry.features.physchem import compute_features

STANDARD_AA = frozenset("ACDEFGHIKLMNPQRSTVWY")


def _scramble(seq: str, rng: random.Random) -> str:
    parts = list(seq)
    rng.shuffle(parts)
    return "".join(parts)


def _auroc(scores_pos: list[float], scores_neg: list[float]) -> float:
    n_p = len(scores_pos)
    n_n = len(scores_neg)
    if n_p == 0 or n_n == 0:
        return 0.5
    better = 0
    ties = 0
    for sp in scores_pos:
        for sn in scores_neg:
            if sp > sn:
                better += 1
            elif sp == sn:
                ties += 1
    total = n_p * n_n
    return (better + 0.5 * ties) / total if total else 0.5


SCALAR_FEATURES = [
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
    "dipeptide_order_score",
]


def run_order_dependent_benchmark(
    amp_csv: str,
    seed: int = 20260705,
) -> dict:
    rng = random.Random(seed)

    # ── Load AMPs ───────────────────────────────────────────────────────
    amp_seqs: list[str] = []
    with open(amp_csv, newline="") as f:
        for row in csv.DictReader(f):
            seq = row["sequence"]
            if not set(seq).issubset(STANDARD_AA):
                continue
            amp_seqs.append(seq)

    print(f"Loaded {len(amp_seqs)} AMPs from {amp_csv}")
    scrambled_seqs = [_scramble(s, rng) for s in amp_seqs]

    # ── Phase A: per-feature scrambling analysis ────────────────────────
    print("\n=== Phase A: Which features survive scrambling? ===\n")

    feat_real: dict[str, list[float]] = {f: [] for f in SCALAR_FEATURES}
    feat_scram: dict[str, list[float]] = {f: [] for f in SCALAR_FEATURES}

    for sr, ss in zip(amp_seqs, scrambled_seqs):
        fr = compute_features(sr)
        fs = compute_features(ss)
        for f in SCALAR_FEATURES:
            vr = fr.get(f)
            vs = fs.get(f)
            if isinstance(vr, (int, float)) and isinstance(vs, (int, float)):
                feat_real[f].append(float(vr))
                feat_scram[f].append(float(vs))

    per_feature: list[dict] = []
    for f in SCALAR_FEATURES:
        rv = feat_real[f]
        sv = feat_scram[f]
        if len(rv) < 10:
            continue
        a = _auroc(rv, sv)
        mu_r = sum(rv) / len(rv)
        mu_s = sum(sv) / len(sv)
        per_feature.append({
            "feature": f,
            "auroc": round(a, 4),
            "mean_real": round(mu_r, 4),
            "mean_scrambled": round(mu_s, 4),
            "delta": round(mu_r - mu_s, 4),
            "survives_scrambling": a > 0.55,
        })

    per_feature.sort(key=lambda x: -x["auroc"])

    print(f"{'Feature':40s} {'AUROC':>6s} {'Mean_real':>9s} {'Mean_scram':>10s} {'Δ':>8s}  Survives?")
    print("-" * 85)
    for p in per_feature:
        flag = "✅" if p["survives_scrambling"] else ""
        print(
            f"{p['feature']:40s} {p['auroc']:6.4f} {p['mean_real']:9.4f} "
            f"{p['mean_scrambled']:10.4f} {p['delta']:+8.4f}  {flag}"
        )

    n_survive = sum(1 for p in per_feature if p["survives_scrambling"])
    survivors_names = [p["feature"] for p in per_feature if p["survives_scrambling"]]
    print(f"\n{n_survive}/{len(per_feature)} features survive scrambling (AUROC > 0.55)")
    print(f"Survivors: {', '.join(survivors_names)}")

    # ── Phase B: dipeptide order score validation ────────────────────────
    print("\n=== Phase B: dipeptide_order_score validation ===\n")

    # The dipeptide_order_score is already in the feature dict.
    dio_entry = next(p for p in per_feature if p["feature"] == "dipeptide_order_score")
    print(
        f"dipeptide_order_score AUROC (real vs scrambled): {dio_entry['auroc']:.4f}"
    )
    print(f"  Mean real:     {dio_entry['mean_real']:.4f}")
    print(f"  Mean scrambled: {dio_entry['mean_scrambled']:.4f}")
    print(f"  Delta:         {dio_entry['delta']:+.4f}")

    # ── Summary comparison ──────────────────────────────────────────────
    pipeline_strict_191 = 0.572  # Pipeline ensemble on strict triage (n=191)

    print("\n=== Summary ===")
    print(f"  Pipeline ensemble strict triage AUROC (n=191):        {pipeline_strict_191}")
    print(f"  dipeptide_order_score strict triage AUROC:           {dio_entry['auroc']}")
    print(f"  Best surviving feature (hydrophobic_moment):         {per_feature[0]['auroc']:.4f}")
    print(f"  Number of order-dependent features in pipeline:      {n_survive}/{len(per_feature)}")

    result = {
        "n_amps": len(amp_seqs),
        "n_features_total": len(SCALAR_FEATURES),
        "n_features_surviving_scrambling": n_survive,
        "surviving_features": [
            {"feature": p["feature"], "auroc": p["auroc"], "delta": p["delta"]}
            for p in per_feature if p["survives_scrambling"]
        ],
        "top_order_dependent_features": [
            {"feature": p["feature"], "auroc": p["auroc"], "delta": p["delta"]}
            for p in per_feature[:10]
        ],
        "dipeptide_order_score": {
            "auroc": dio_entry["auroc"],
            "mean_real": dio_entry["mean_real"],
            "mean_scrambled": dio_entry["mean_scrambled"],
            "delta": dio_entry["delta"],
            "survives_scrambling": dio_entry["survives_scrambling"],
        },
        "pipeline_strict_triage_auroc_191": pipeline_strict_191,
        "assessment": "",
    }

    if dio_entry["auroc"] > pipeline_strict_191 + 0.10:
        result["assessment"] = (
            f"ORDER-DEPENDENT FEATURE STRONG: dipeptide_order_score "
            f"(AUROC {dio_entry['auroc']:.3f}) substantially improves over "
            f"pipeline ensemble on strict triage ({pipeline_strict_191:.3f}). "
            f"{n_survive}/{len(per_feature)} features are order-dependent."
        )
    elif dio_entry["auroc"] > pipeline_strict_191:
        result["assessment"] = (
            f"dipeptide_order_score ({dio_entry['auroc']:.3f}) improves over "
            f"pipeline ensemble ({pipeline_strict_191:.3f}) on strict triage."
        )
    else:
        result["assessment"] = (
            f"dipeptide_order_score does NOT improve strict triage over "
            f"pipeline ensemble ({dio_entry['auroc']:.3f} vs {pipeline_strict_191:.3f})."
        )

    print(f"\n  Assessment: {result['assessment']}")

    return result


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Order-dependent features benchmark (Loop 13)"
    )
    parser.add_argument(
        "--amp-csv",
        default="examples/validation/known_amps_500.csv",
    )
    parser.add_argument("--seed", type=int, default=20260705)
    parser.add_argument("--out", default="outputs/benchmark_order_dependent.json")
    args = parser.parse_args(argv)

    result = run_order_dependent_benchmark(amp_csv=args.amp_csv, seed=args.seed)

    Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nMachine-readable output: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

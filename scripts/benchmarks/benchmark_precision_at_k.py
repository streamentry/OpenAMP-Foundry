"""Precision@k calibration benchmark: operating characteristic for candidate selection.

Translates the pipeline's AUROC into actionable operational guidance:
  - At a given precision (e.g., top-20), what recall can we expect?
  - At a given recall (e.g., 80%), what threshold should we use?
  - What enrichment factor does the pipeline achieve at various k?

Usage:
    python scripts/benchmark_precision_at_k.py
    make bench-precision-at-k
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from openamp_foundry.pipeline import score_candidates


def _auroc(scores_pos: list[float], scores_neg: list[float]) -> float:
    n_p = len(scores_pos)
    n_n = len(scores_neg)
    if n_p == 0 or n_n == 0:
        return 0.5
    better = sum(1 for p in scores_pos for n in scores_neg if p > n)
    ties = sum(1 for p in scores_pos for n in scores_neg if p == n)
    total = n_p * n_n
    return (better + 0.5 * ties) / total if total else 0.5


def run_precision_at_k_benchmark(
    amp_csv: str,
    decoy_csv: str,
    config_path: str = "configs/pipeline.yaml",
    max_k: int = 200,
) -> dict:
    """Compute precision@k, recall@k, enrichment, and operating characteristic."""

    # ── Score sequences via pipeline ─────────────────────────────────────
    scored_amps, _ = score_candidates(amp_csv, config_path=config_path)
    scored_decoys, _ = score_candidates(decoy_csv, config_path=config_path)

    amps: list[dict] = []
    for s in scored_amps:
        amps.append({
            "id": s.candidate.candidate_id,
            "sequence": s.candidate.sequence,
            "ensemble": s.scores.get("ensemble", 0.5),
        })

    decoys: list[dict] = []
    for s in scored_decoys:
        decoys.append({
            "id": s.candidate.candidate_id,
            "sequence": s.candidate.sequence,
            "ensemble": s.scores.get("ensemble", 0.5),
        })

    n_pos = len(amps)
    n_neg = len(decoys)
    total = n_pos + n_neg
    base_rate = n_pos / total if total else 0.0

    print(f"Scored {n_pos} AMPs + {n_neg} decoys")
    print(f"Base rate (AMP fraction): {base_rate:.4f}")

    # ── AUROC ────────────────────────────────────────────────────────────
    amp_scores = [a["ensemble"] for a in amps]
    decoy_scores = [d["ensemble"] for d in decoys]
    auroc_val = _auroc(amp_scores, decoy_scores)

    # ── Rank all sequences by ensemble score ─────────────────────────────
    all_seq = [(a, 1) for a in amps] + [(d, 0) for d in decoys]
    all_seq.sort(key=lambda x: -x[0]["ensemble"])

    # ── Precision@k, recall@k, enrichment@k ─────────────────────────────
    precision_at_k: list[dict] = []
    n_amps_found = 0
    for k in range(1, min(max_k, total) + 1):
        if k <= len(all_seq):
            top_k = all_seq[:k]
            n_amps_found = sum(label for _, label in top_k)
        precision = n_amps_found / k if k > 0 else 0.0
        recall = n_amps_found / n_pos if n_pos > 0 else 0.0
        enrichment = precision / base_rate if base_rate > 0 else 0.0
        precision_at_k.append({
            "k": k,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "enrichment_factor": round(enrichment, 4),
            "n_amps_found": n_amps_found,
        })

    # ── Operating characteristic (threshold-based) ───────────────────────
    scores_unique = sorted(set(a["ensemble"] for a in amps + decoys))
    thresholds = [round(t, 4) for t in scores_unique]

    oc: list[dict] = []
    for thresh in thresholds:
        tp = sum(1 for a in amps if a["ensemble"] >= thresh)
        fn = n_pos - tp
        fp = sum(1 for d in decoys if d["ensemble"] >= thresh)
        tn = n_neg - fp
        tpr = tp / n_pos if n_pos > 0 else 0.0
        fpr = fp / n_neg if n_neg > 0 else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1 = 2 * prec * tpr / (prec + tpr) if (prec + tpr) > 0 else 0.0
        oc.append({
            "threshold": thresh,
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "tpr": round(tpr, 4),
            "fpr": round(fpr, 4),
            "precision": round(prec, 4),
            "recall": round(tpr, 4),
            "f1": round(f1, 4),
        })

    oc.sort(key=lambda x: x["threshold"])

    # ── Recommend threshold for 80% recall ───────────────────────────────
    rec80_candidates = [o for o in oc if o["recall"] >= 0.80]
    best_rec80 = min(rec80_candidates, key=lambda o: o["threshold"]) if rec80_candidates else oc[-1]
    rec80_threshold = best_rec80["threshold"]
    rec80_precision = best_rec80["precision"]
    rec80_f1 = best_rec80["f1"]

    # ── Find best F1 threshold ───────────────────────────────────────────
    best_f1_entry = max(oc, key=lambda o: o["f1"])
    best_f1_threshold = best_f1_entry["threshold"]
    best_f1_val = best_f1_entry["f1"]

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n=== Loop 14: Precision@k Calibration ===")
    print(f"  AUROC (standard): {auroc_val:.4f}")
    print(f"  Base rate (balanced): {base_rate:.1%}")
    print()
    print(f"  {'k':>5s} {'Precision':>10s} {'Recall':>7s} {'Enrichment':>11s}")
    print(f"  {'-'*5} {'-'*10} {'-'*7} {'-'*11}")
    for pk in precision_at_k:
        if pk["k"] in [1, 5, 10, 20, 50, 100, 200] or pk["k"] == len(all_seq):
            sign = "▸" if pk["precision"] > base_rate else "▹"
            print(
                f"  {sign} {pk['k']:3d} {pk['precision']:10.4f} {pk['recall']:7.4f} "
                f"{pk['enrichment_factor']:11.2f}"
            )

    print("\n  Operating characteristic (threshold):")
    print(f"  Threshold for 80% recall:  {rec80_threshold:.4f}")
    print(f"    => Precision at this threshold: {rec80_precision:.4f}")
    print(f"    => F1 at this threshold:        {rec80_f1:.4f}")
    print(f"    => Total candidates above:       {best_rec80['true_positives'] + best_rec80['false_positives']}")
    print(f"    => Expected AMPs in top set:     {best_rec80['true_positives']}")
    print()
    print(f"  Best F1 threshold:         {best_f1_threshold:.4f}")
    print(f"    => F1:            {best_f1_val:.4f}")
    print(f"    => Precision:     {best_f1_entry['precision']:.4f}")
    print(f"    => Recall:        {best_f1_entry['recall']:.4f}")
    print(f"    => Total AMPs above: {best_f1_entry['true_positives']}/{n_pos}")

    result = {
        "benchmark": "precision_at_k",
        "n_amps": n_pos,
        "n_decoys": n_neg,
        "base_rate": round(base_rate, 4),
        "auroc": round(auroc_val, 4),
        "precision_recall_curve": oc,
        "precision_at_k": precision_at_k,
        "rec80_threshold": round(rec80_threshold, 4),
        "rec80_precision": round(rec80_precision, 4),
        "rec80_f1": round(rec80_f1, 4),
        "best_f1_threshold": round(best_f1_threshold, 4),
        "best_f1": round(best_f1_val, 4),
        "best_f1_precision": round(best_f1_entry["precision"], 4),
        "best_f1_recall": round(best_f1_entry["recall"], 4),
        "assessment": "",
    }

    if rec80_precision >= 0.5:
        result["assessment"] = (
            f"At 80% recall, precision is {rec80_precision:.1%} — "
            f"above random ({base_rate:.1%}). "
            f"Threshold recommendation: {rec80_threshold:.3f}"
        )
    else:
        result["assessment"] = (
            f"At 80% recall, precision is {rec80_precision:.1%} — "
            f"below random ({base_rate:.1%}). "
            f"Suggests the pipeline cannot reliably triage at high recall."
        )

    print(f"\n  {result['assessment']}")

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Precision@k calibration benchmark (Loop 14)"
    )
    parser.add_argument(
        "--amp-csv", default="examples/validation/known_amps_500.csv"
    )
    parser.add_argument(
        "--decoy-csv", default="examples/validation/random_background_500.csv"
    )
    parser.add_argument(
        "--config", default="configs/pipeline.yaml"
    )
    parser.add_argument("--max-k", type=int, default=200)
    parser.add_argument("--out", default="outputs/benchmark_precision_at_k.json")

    args = parser.parse_args(argv)
    result = run_precision_at_k_benchmark(
        amp_csv=args.amp_csv,
        decoy_csv=args.decoy_csv,
        config_path=args.config,
        max_k=args.max_k,
    )

    Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nMachine-readable output: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

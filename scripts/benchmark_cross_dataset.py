#!/usr/bin/env python3
"""Cross-dataset generalisation benchmark: does pipeline generalise to DRAMP AMPs?

Usage:
  python scripts/benchmark_cross_dataset.py [--out report.json]
  python scripts/benchmark_cross_dataset.py --full-set  # includes full DRAMP (6000 seqs)
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

from openamp_foundry.features.physchem import compute_features
from openamp_foundry.scoring.activity import activity_likeness_score
from openamp_foundry.scoring.boman import boman_activity_score
from openamp_foundry.scoring.ensemble import ensemble_score
from openamp_foundry.scoring.novelty import novelty_score
from openamp_foundry.scoring.safety import safety_score
from openamp_foundry.scoring.synthesis import synthesis_feasibility_score
from openamp_foundry.config import load_config

STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")

UNIPROT_FREQ = {
    "A": 0.0826, "R": 0.0553, "N": 0.0406, "D": 0.0546, "C": 0.0138,
    "Q": 0.0393, "E": 0.0675, "G": 0.0708, "H": 0.0227, "I": 0.0594,
    "L": 0.0965, "K": 0.0581, "M": 0.0242, "F": 0.0386, "P": 0.0474,
    "S": 0.0656, "T": 0.0534, "W": 0.0109, "Y": 0.0292, "V": 0.0687,
}
AA_TYPES = list(UNIPROT_FREQ.keys())

DECOY_SEED = 1729
SAMPLE_SEED = 42
SUBSAMPLE_N = 500


def parse_fasta(path: Path) -> list[dict]:
    records = []
    with open(path) as f:
        header = None
        seq_parts = []
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                if header is not None and seq_parts:
                    seq = "".join(seq_parts).upper()
                    records.append({"id": header, "sequence": seq})
                header = line[1:].split()[0]
                seq_parts = []
            elif line:
                seq_parts.append(line)
        if header is not None and seq_parts:
            seq = "".join(seq_parts).upper()
            records.append({"id": header, "sequence": seq})
    return records


def is_valid_amp(seq: str) -> bool:
    return 10 <= len(seq) <= 30 and all(c in STANDARD_AA for c in seq)


def load_amp_sequences_csv(path: str | Path) -> list[dict]:
    amps = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            amps.append(row)
    return amps


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
    rng = random.Random(seed)
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


def score_sequences(seqs: list[dict], config: dict, desc: str = "") -> list[dict]:
    weights = config["weights"]
    results = []
    t0 = time.time()
    for idx, entry in enumerate(seqs):
        seq = entry["sequence"].strip().upper()
        seq_id = entry["id"]
        valid = all(c in STANDARD_AA for c in seq)
        features = compute_features(seq)
        act = activity_likeness_score(features)
        safe = safety_score(features)
        synth = synthesis_feasibility_score(features, valid_sequence=valid)
        nov, _ = novelty_score(seq, [])
        boman_act = boman_activity_score(seq)
        raw_scores = {
            "activity": act, "safety": safe,
            "synthesis": synth, "novelty": nov,
            "boman_activity": boman_act,
            "disagreement": abs(act - boman_act),
        }
        raw_scores["ensemble"] = ensemble_score(raw_scores, weights)
        results.append({
            "id": seq_id,
            "sequence": seq,
            "ensemble": raw_scores["ensemble"],
            "activity": act,
            "safety": safe,
            "boman_activity": boman_act,
        })
        if (idx + 1) % 500 == 0:
            elapsed = time.time() - t0
            rate = (idx + 1) / elapsed if elapsed > 0 else 0
            print(f"  {desc}: scored {idx+1}/{len(seqs)} ({rate:.0f}/s)")
    return results


def generate_decoys(amps: list[dict], rng: random.Random) -> list[dict]:
    decoys = []
    for i, amp in enumerate(amps):
        seq_len = len(amp["sequence"])
        seq = "".join(rng.choices(AA_TYPES, weights=[UNIPROT_FREQ[aa] for aa in AA_TYPES], k=seq_len))
        decoys.append({
            "id": f"DECOY-{i+1:04d}",
            "sequence": seq,
        })
    return decoys


def _auprc(pos_scores: list[float], neg_scores: list[float]) -> float:
    n_pos = len(pos_scores)
    if n_pos == 0:
        return 0.0
    all_scored = sorted(
        [(s, 1) for s in pos_scores] + [(s, 0) for s in neg_scores],
        key=lambda x: (-x[0], x[1]),
    )
    tp = fp = 0
    recalls = [0.0]
    precisions = [1.0]
    for _score, label in all_scored:
        if label == 1:
            tp += 1
        else:
            fp += 1
        recalls.append(tp / n_pos)
        precisions.append(tp / (tp + fp))
    area = sum(
        (recalls[i] - recalls[i - 1]) * (precisions[i] + precisions[i - 1]) / 2
        for i in range(1, len(recalls))
    )
    return round(area, 4)


def compute_auroc_for_set(
    dramp_amps: list[dict],
    decoys: list[dict],
    config: dict,
    label: str,
) -> dict:
    all_amps = score_sequences(dramp_amps, config, desc=label)
    all_decoys = score_sequences(decoys, config, desc=f"{label}_decoys")
    pos_scores = [r["ensemble"] for r in all_amps]
    neg_scores = [r["ensemble"] for r in all_decoys]
    auroc = round(_auc_wilcoxon(pos_scores, neg_scores), 4)
    ci = _bootstrap_auroc_ci(pos_scores, neg_scores)
    auprc_val = _auprc(pos_scores, neg_scores)
    n_total = len(pos_scores) + len(neg_scores)
    auprc_random = round(len(pos_scores) / n_total, 4) if n_total > 0 else 0.0
    return {
        "label": label,
        "n_amps": len(dramp_amps),
        "n_decoys": len(decoys),
        "auroc": auroc,
        "ci95_lo": ci["ci_lo"],
        "ci95_hi": ci["ci_hi"],
        "auprc": auprc_val,
        "auprc_random_baseline": auprc_random,
        "mean_amp_score": round(sum(pos_scores) / len(pos_scores), 4) if pos_scores else None,
        "mean_decoy_score": round(sum(neg_scores) / len(neg_scores), 4) if neg_scores else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cross-dataset generalisation benchmark: DRAMP vs baseline."
    )
    parser.add_argument("--out", default=None, help="Path to write JSON report")
    parser.add_argument("--config", default="configs/pipeline.yaml", help="Pipeline config")
    parser.add_argument(
        "--dramp-fasta", default="data/novelty_db/dramp_general.fasta",
        help="DRAMP FASTA path",
    )
    parser.add_argument(
        "--amp-csv", default="examples/validation/known_amps_500.csv",
        help="Current AMP set CSV",
    )
    parser.add_argument(
        "--full-set", action="store_true",
        help="Also run full DRAMP (6000 seqs, ~8 min). Default: subsample only."
    )
    args = parser.parse_args(argv)

    print("=== Cross-Dataset Generalization Benchmark ===")
    config = load_config(args.config)

    t_start = time.time()

    # 1. Load current benchmark AMPs
    current_amps = load_amp_sequences_csv(args.amp_csv)
    current_seqs = {r["sequence"].strip().upper() for r in current_amps if is_valid_amp(r["sequence"])}
    print(f"\nCurrent AMP set: {len(current_seqs)} valid sequences")

    # 2. Parse DRAMP FASTA
    dramp_all = parse_fasta(Path(args.dramp_fasta))
    dramp_valid = [r for r in dramp_all if is_valid_amp(r["sequence"])]
    print(f"DRAMP total: {len(dramp_all)} seqs, valid (10-30 AA): {len(dramp_valid)}")

    # 3. Split DRAMP into overlap and DRAMP-only
    dramp_only = [r for r in dramp_valid if r["sequence"] not in current_seqs]
    dramp_overlap = [r for r in dramp_valid if r["sequence"] in current_seqs]
    print(f"DRAMP-only: {len(dramp_only)}, Overlap: {len(dramp_overlap)}")

    if len(dramp_only) == 0:
        print("ERROR: no DRAMP-only sequences available")
        return 1

    # 4. Size-matched subsample (PRIMARY comparison — size-matched to current benchmark)
    rng_sample = random.Random(SAMPLE_SEED)
    sample_n = min(SUBSAMPLE_N, len(dramp_only))
    sampled_indices = rng_sample.sample(range(len(dramp_only)), sample_n)
    dramp_sampled = [dramp_only[i] for i in sampled_indices]
    rng_decoy_s = random.Random(DECOY_SEED)
    decoys_sampled = generate_decoys(dramp_sampled, rng_decoy_s)
    print(f"\n--- PRIMARY: DRAMP-only (size-matched n={len(dramp_sampled)}) ---")
    sampled_result = compute_auroc_for_set(dramp_sampled, decoys_sampled, config, "dramp_sampled")
    print(f"  AUROC: {sampled_result['auroc']:.4f} (CI: {sampled_result['ci95_lo']:.4f}-{sampled_result['ci95_hi']:.4f})")
    print(f"  AUPRC: {sampled_result['auprc']:.4f} (random: {sampled_result['auprc_random_baseline']:.4f})")
    print(f"  Mean AMP score: {sampled_result['mean_amp_score']:.4f}")
    print(f"  Mean decoy score: {sampled_result['mean_decoy_score']:.4f}")

    # 5. Overlap set consistency check (quick)
    if dramp_overlap:
        rng_over = random.Random(DECOY_SEED)
        decoys_over = generate_decoys(dramp_overlap, rng_over)
        print(f"\n--- Overlap (also in current set, n={len(dramp_overlap)}) ---")
        overlap_result = compute_auroc_for_set(dramp_overlap, decoys_over, config, "dramp_overlap")
        print(f"  AUROC: {overlap_result['auroc']:.4f} (CI: {overlap_result['ci95_lo']:.4f}-{overlap_result['ci95_hi']:.4f})")
        print(f"  Mean AMP score: {overlap_result['mean_amp_score']:.4f}")
    else:
        overlap_result = None

    # 6. Full DRAMP-only set (OPTIONAL — requires --full-set flag)
    full_result = None
    if args.full_set:
        rng_full = random.Random(DECOY_SEED)
        decoys_full = generate_decoys(dramp_only, rng_full)
        print(f"\n--- FULL: DRAMP-only (n={len(dramp_only)}) ---")
        full_result = compute_auroc_for_set(dramp_only, decoys_full, config, "dramp_full")
        print(f"  AUROC: {full_result['auroc']:.4f} (CI: {full_result['ci95_lo']:.4f}-{full_result['ci95_hi']:.4f})")
        print(f"  AUPRC: {full_result['auprc']:.4f}")
    else:
        print(f"\n(Skipping full DRAMP-only set — use --full-set to run {len(dramp_only)} seqs)")

    # 7. Full DRAMP set (all valid, including overlap)
    full_dramp_result = None
    if args.full_set:
        rng_all = random.Random(DECOY_SEED)
        decoys_all = generate_decoys(dramp_valid, rng_all)
        print(f"\n--- DRAMP all (n={len(dramp_valid)}) ---")
        full_dramp_result = compute_auroc_for_set(dramp_valid, decoys_all, config, "dramp_all")
        print(f"  AUROC: {full_dramp_result['auroc']:.4f} (CI: {full_dramp_result['ci95_lo']:.4f}-{full_dramp_result['ci95_hi']:.4f})")
        print(f"  AUPRC: {full_dramp_result['auprc']:.4f}")

    # 8. Compare to known benchmark AUROC
    baseline_auroc = 0.7832
    baseline_label = "standard_apd6_uniprot"

    comparisons = [
        ("DRAMP-only (size-matched)", sampled_result),
        ("DRAMP overlap", overlap_result),
    ]
    if full_result:
        comparisons.append(("DRAMP-only (full set)", full_result))
    if full_dramp_result:
        comparisons.append(("DRAMP all valid", full_dramp_result))

    for label, result in comparisons:
        if result is None:
            continue
        delta = round(result["auroc"] - baseline_auroc, 4)
        print(f"\n  {label}: AUROC {result['auroc']:.4f} vs baseline {baseline_auroc:.4f} (Δ={delta:+.4f})")
        if result["auroc"] >= 0.75:
            print("  ✓ Generalizes well (AUROC ≥ 0.75)")
        elif result["auroc"] >= 0.70:
            print("  ~ Modest generalization (AUROC 0.70-0.75)")
        else:
            print("  ✗ Poor generalization (AUROC < 0.70)")

    # 9. Report
    results = {
        "dramp_only_sampled": sampled_result,
    }
    deltas = {
        "dramp_only_sampled": round(sampled_result["auroc"] - baseline_auroc, 4),
    }
    if overlap_result:
        results["dramp_overlap"] = overlap_result
        deltas["dramp_overlap"] = round(overlap_result["auroc"] - baseline_auroc, 4)
    if full_result:
        results["dramp_only_full"] = full_result
        deltas["dramp_only_full"] = round(full_result["auroc"] - baseline_auroc, 4)
    if full_dramp_result:
        results["dramp_full"] = full_dramp_result
        deltas["dramp_full"] = round(full_dramp_result["auroc"] - baseline_auroc, 4)

    report = {
        "benchmark": "cross_dataset_generalization",
        "config": args.config,
        "dramp_source": str(args.dramp_fasta),
        "current_amp_set": str(args.amp_csv),
        "n_current_amps": len(current_seqs),
        "n_dramp_total": len(dramp_all),
        "n_dramp_valid": len(dramp_valid),
        "n_dramp_only": len(dramp_only),
        "n_dramp_overlap": len(dramp_overlap),
        "n_decoys": sample_n,
        "decoy_method": "swissprot_frequency",
        "decoy_seed": DECOY_SEED,
        "baseline_auroc": baseline_auroc,
        "baseline_label": baseline_label,
        "results": results,
        "deltas": deltas,
        "elapsed_seconds": round(time.time() - t_start, 1),
    }

    # Verdict
    auroc = sampled_result["auroc"]
    if auroc >= 0.75:
        report["generalization_verdict"] = "strong"
        report["interpretation"] = (
            f"Pipeline generalises strongly to DRAMP (AUROC={auroc:.4f}, Δ={auroc-baseline_auroc:+.4f}). "
            "Heuristic features discriminate DRAMP AMPs from Swiss-Prot decoys nearly as well as "
            "APD6/UniProt AMPs. Source bias is minimal."
        )
    elif auroc >= 0.70:
        report["generalization_verdict"] = "moderate"
        report["interpretation"] = (
            f"Pipeline generalises moderately to DRAMP (AUROC={auroc:.4f}, Δ={auroc-baseline_auroc:+.4f}). "
            "Discriminative power drops but remains above 0.70. "
            "DRAMP AMPs may differ in composition but the pipeline still captures meaningful signal."
        )
    else:
        report["generalization_verdict"] = "weak"
        report["interpretation"] = (
            f"Pipeline generalises poorly to DRAMP (AUROC={auroc:.4f}, Δ={auroc-baseline_auroc:+.4f}). "
            "Heuristic features tuned to APD6/UniProt do not transfer to DRAMP. "
            "Significant source bias detected."
        )

    print(f"\n{'='*60}")
    print(f"Generalization: {report['generalization_verdict'].upper()}")
    print(report["interpretation"])
    print(f"Elapsed: {report['elapsed_seconds']:.0f}s")
    print(f"{'='*60}")

    print(json.dumps(report, indent=2))

    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())

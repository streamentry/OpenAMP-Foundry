"""Retrospective AUROC benchmark: known AMPs vs decoy peptides.

Two complementary benchmark modes:

  STANDARD (primary gate):
    Positives — confirmed literature AMPs (original 43; expanded to 95 in PR #110)
    Negatives — 44 length-matched peptides drawn from UniProt Swiss-Prot
                background amino acid frequencies (RNG seed=43)
    Tests: can the model distinguish AMP-like composition/structure from
           random protein-like sequences?
    Expected AUROC: 0.70–0.90 for a working composition-based scorer.
    Gate: AUROC > 0.70 → proceed; 0.55–0.70 → caution; < 0.55 → STOP.

  STRICT (order-sensitivity test, secondary):
    Positives — 43 confirmed literature AMPs
    Negatives — 43 per-sequence composition-matched shuffled decoys (RNG seed=42)
    Tests: does the model have order-dependent signal beyond composition?
    Expected AUROC: 0.50–0.65 for any composition-heavy scorer. This is
    intentionally difficult — it tests ONLY the hydrophobic moment term
    since all composition features are identical per pair.
    NOT used as the synthesis gate; reported for scientific transparency.

Key metric: AUROC (area under receiver operating characteristic curve)
  = P(random AMP scores higher than random decoy)
"""
from __future__ import annotations

import csv
from pathlib import Path


def _auc_wilcoxon(pos_scores: list[float], neg_scores: list[float]) -> float:
    """Compute AUROC via the Wilcoxon-Mann-Whitney statistic (O(n*m) but n is small)."""
    n_pos = len(pos_scores)
    n_neg = len(neg_scores)
    if n_pos == 0 or n_neg == 0:
        return 0.5
    concordant = sum(
        1 for p in pos_scores for n in neg_scores if p > n
    ) + 0.5 * sum(
        1 for p in pos_scores for n in neg_scores if p == n
    )
    return concordant / (n_pos * n_neg)


def _auprc(pos_scores: list[float], neg_scores: list[float]) -> float:
    """Compute AUPRC via the trapezoidal rule on the precision-recall curve.

    Random baseline = n_pos / (n_pos + n_neg) = prevalence.
    AUPRC = 1.0 for a perfect classifier, prevalence for a random ranker.
    """
    n_pos = len(pos_scores)
    if n_pos == 0:
        return 0.0
    # Pessimistic tie-breaking: negatives (label=0) sort before positives (label=1)
    # on equal scores, matching sklearn average_precision_score convention.
    # Without this, a random classifier with all-equal scores returns AUPRC=1.0
    # instead of the correct prevalence baseline.
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
    # trapezoidal integration
    area = sum(
        (recalls[i] - recalls[i - 1]) * (precisions[i] + precisions[i - 1]) / 2
        for i in range(1, len(recalls))
    )
    return round(area, 4)


def _bootstrap_auroc_ci(
    pos_scores: list[float],
    neg_scores: list[float],
    n_bootstrap: int = 2000,
    seed: int = 0,
) -> dict:
    """Bootstrap 95% CI for AUROC via percentile method."""
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


def _recall_at_k(labels: list[int], k: int) -> float:
    """Fraction of true positives in the top-k ranked items."""
    n_pos = sum(labels)
    if n_pos == 0:
        return 0.0
    top_k_pos = sum(labels[:k])
    return top_k_pos / n_pos


_DESIGN_NOTES = {
    "standard": (
        "Negatives are length-matched peptides drawn from UniProt Swiss-Prot background "
        "amino acid frequencies (RNG seed=43). AUROC reflects the model's ability to "
        "distinguish AMP-like composition and structure from random protein sequences. "
        "This is the primary synthesis gate."
    ),
    "strict": (
        "Negatives are amino-acid-composition-matched shuffled decoys (RNG seed=42). "
        "AUROC reflects discrimination by ORDER-DEPENDENT features only "
        "(primarily hydrophobic moment). Composition-based features "
        "(charge, hydrophobic fraction, Boman index, GRAVY) are identical "
        "for each AMP/decoy pair and do NOT contribute to discrimination. "
        "This is a secondary scientific transparency benchmark, NOT the synthesis gate."
    ),
}


def run_retrospective_benchmark(
    amp_csv: str | Path,
    decoy_csv: str | Path,
    config_path: str | Path = "configs/pipeline.yaml",
    recall_ks: list[int] | None = None,
    benchmark_type: str = "standard",
    n_bootstrap: int = 2000,
) -> dict:
    """Score known AMPs and shuffled decoys and compute AUROC + recall@k.

    Returns a dict with AUROC, per-k recall, and the full ranked list.
    """
    from openamp_foundry.features.physchem import compute_features
    from openamp_foundry.scoring.activity import activity_likeness_score
    from openamp_foundry.scoring.boman import boman_activity_score
    from openamp_foundry.scoring.ensemble import ensemble_score
    from openamp_foundry.scoring.novelty import novelty_score
    from openamp_foundry.scoring.safety import safety_score
    from openamp_foundry.scoring.synthesis import synthesis_feasibility_score
    from openamp_foundry.config import load_config

    config = load_config(config_path)
    weights = config["weights"]

    rows = []

    for path, true_label in [(amp_csv, 1), (decoy_csv, 0)]:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                seq = row["sequence"].strip().upper()
                seq_id = row["id"]
                valid = all(aa in "ACDEFGHIKLMNPQRSTVWY" for aa in seq)
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
                rows.append({
                    "id": seq_id,
                    "sequence": seq,
                    "label": true_label,
                    "ensemble": raw_scores["ensemble"],
                    "activity": act,
                    "safety": safe,
                    "boman_activity": boman_act,
                    "hydrophobic_moment": features.get("hydrophobic_moment", 0.0),
                })

    rows.sort(key=lambda r: r["ensemble"], reverse=True)

    pos_scores = [r["ensemble"] for r in rows if r["label"] == 1]
    neg_scores = [r["ensemble"] for r in rows if r["label"] == 0]
    auroc = round(_auc_wilcoxon(pos_scores, neg_scores), 4)
    auroc_ci = _bootstrap_auroc_ci(pos_scores, neg_scores, n_bootstrap=n_bootstrap)
    auprc = _auprc(pos_scores, neg_scores)
    n_total_for_prev = len(pos_scores) + len(neg_scores)
    auprc_random = round(len(pos_scores) / n_total_for_prev, 4) if n_total_for_prev > 0 else 0.0

    n_total = len(rows)
    n_pos = sum(r["label"] for r in rows)
    labels_ranked = [r["label"] for r in rows]

    if recall_ks is None:
        recall_ks = [10, 20, 43]
    recall = {f"recall_at_{k}": round(_recall_at_k(labels_ranked, k), 4) for k in recall_ks}

    random_auroc = 0.5
    interpretation = (
        "STRONG — model has meaningful discriminative power (AUROC > 0.70)"
        if auroc >= 0.70
        else "WEAK — model has modest signal; proceed with caution (AUROC 0.55–0.70)"
        if auroc >= 0.55
        else "POOR — model is near-random (AUROC < 0.55); do NOT proceed to synthesis"
    )

    return {
        "benchmark": "retrospective_auroc",
        "n_positives": n_pos,
        "n_negatives": n_total - n_pos,
        "n_total": n_total,
        "auroc": auroc,
        "auroc_ci95_lo": auroc_ci["ci_lo"],
        "auroc_ci95_hi": auroc_ci["ci_hi"],
        "auroc_bootstrap_mean": auroc_ci["mean"],
        "n_bootstrap": auroc_ci["n_bootstrap"],
        "random_auroc": random_auroc,
        "auroc_above_random": round(auroc - random_auroc, 4),
        "auprc": auprc,
        "auprc_random_baseline": auprc_random,
        "auprc_above_random": round(auprc - auprc_random, 4),
        **recall,
        "interpretation": interpretation,
        "benchmark_type": benchmark_type,
        "design_note": _DESIGN_NOTES.get(benchmark_type, _DESIGN_NOTES["standard"]),
        "known_blind_spots": [
            "Melittin-like bent-helix peptides: hemolytic character not captured "
            "by simple 1D hydrophobic moment (Habermann 1972).",
            "Proline-rich AMPs (PR-39): activity relies on intracellular targets, "
            "not membrane disruption; hydrophobic moment is low but activity is real.",
        ],
        "top_ranked": rows[:10],
        "disclaimer": (
            "AUROC > 0.70 does NOT imply the nominated candidates are antimicrobial. "
            "It implies the model has some discriminative power over composition-matched "
            "controls. Wet-lab validation remains mandatory."
        ),
    }

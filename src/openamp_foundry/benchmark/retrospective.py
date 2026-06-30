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


def _cluster_aware_bootstrap_auroc_ci(
    pos_scores: list[float],
    neg_scores: list[float],
    cluster_assignments: list[int],
    n_bootstrap: int = 2000,
    seed: int = 0,
) -> dict:
    """Bootstrap 95% CI for AUROC that resamples clusters, not individual sequences.

    Standard bootstrap resampling treats every sample as independent. When the
    positive set contains near-duplicate sequences (e.g. magainin-1, magainin-2,
    magainin-3), this underestimates variance and produces artificially narrow CIs.

    Cluster-aware bootstrap:
      1. Group positive scores by cluster ID.
      2. Resample clusters with replacement (not individual scores).
      3. Flatten the resampled cluster scores into a new positive score list.
      4. Compute AUROC on the resampled set.

    Args:
        pos_scores: ensemble scores of positive (AMP) sequences.
        neg_scores: ensemble scores of negative (decoy) sequences.
        cluster_assignments: cluster ID for each positive sequence (same order as pos_scores).
            Negative sequences are always treated as independent (random decoys have no
            near-duplicate clusters by construction).
        n_bootstrap: number of bootstrap resamples.
        seed: RNG seed for reproducibility.

    Returns:
        Dict with mean, ci_lo, ci_hi, n_bootstrap.
    """
    import random as _random
    rng = _random.Random(seed)
    n_pos = len(pos_scores)
    n_neg = len(neg_scores)
    if n_pos == 0 or n_neg == 0:
        return {"mean": 0.5, "ci_lo": 0.5, "ci_hi": 0.5, "n_bootstrap": 0}

    # Group positive scores by cluster
    clusters: dict[int, list[float]] = {}
    for score, cid in zip(pos_scores, cluster_assignments):
        clusters.setdefault(cid, []).append(score)

    unique_cluster_ids = list(clusters.keys())
    n_clusters = len(unique_cluster_ids)

    samples = []
    for _ in range(n_bootstrap):
        # Resample clusters with replacement
        resampled_pos: list[float] = []
        for _ in range(n_clusters):
            cid = rng.choice(unique_cluster_ids)
            resampled_pos.extend(clusters[cid])
        # Resample negatives normally (they are independent)
        neg_s = [rng.choice(neg_scores) for _ in range(n_neg)]
        samples.append(_auc_wilcoxon(resampled_pos, neg_s))

    samples.sort()
    lo_idx = int(0.025 * n_bootstrap)
    hi_idx = int(0.975 * n_bootstrap)
    return {
        "mean": round(sum(samples) / len(samples), 4),
        "ci_lo": round(samples[lo_idx], 4),
        "ci_hi": round(samples[hi_idx], 4),
        "n_bootstrap": n_bootstrap,
    }


def run_cluster_split_benchmark(
    amp_csv: str | Path,
    decoy_csv: str | Path,
    config_path: str | Path = "configs/pipeline.yaml",
    similarity_threshold: float = 0.70,
    n_bootstrap: int = 2000,
) -> dict:
    """Cluster-split retrospective benchmark: honest AUROC with leakage control.

    The standard benchmark (run_retrospective_benchmark) scores all AMPs against
    all decoys and computes AUROC + bootstrap CI. This is the primary synthesis gate.

    However, the standard benchmark treats near-duplicate AMPs as independent
    samples. When the positive set contains families of nearly identical sequences
    (e.g. magainin-1/2/3 at 91-96% identity, protegrin-1/2/3 at 89-94% identity),
    two problems arise:

    1. **Inflated AUROC**: near-duplicates that share composition features will
       all score similarly, so getting one right means getting all right. This
       inflates the apparent concordance count.
    2. **Artificially narrow CI**: bootstrap resampling treats each sequence as
       an independent draw. Resampling a cluster of 3 near-identical magainins
       as 3 independent observations underestimates the true variance.

    This benchmark addresses both:

    - **Cluster-aware AUROC**: scores all AMPs and decoys, but computes the
      bootstrap CI by resampling clusters (not individual sequences).
    - **Held-out recovery**: clusters the AMP set, holds out near-duplicate
      members, and reports AUROC on the held-out set vs decoys. This tests
      whether the scorer generalises beyond the cluster representatives.

    The cluster-aware CI is the primary honesty improvement. The held-out
    recovery is a secondary diagnostic.

    Args:
        amp_csv: CSV of known AMPs (id, sequence, family, reference, label).
        decoy_csv: CSV of decoy peptides (id, sequence, ...).
        config_path: Pipeline config for scoring weights.
        similarity_threshold: Normalized similarity threshold for clustering (default 0.70).
        n_bootstrap: Bootstrap resample count.

    Returns:
        Dict with full cluster-split benchmark results.
    """
    from openamp_foundry.benchmark.splits import cluster_by_similarity
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

    # Load and score all AMPs
    amp_rows = []
    with open(amp_csv, newline="", encoding="utf-8") as f:
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
            amp_rows.append({
                "id": seq_id,
                "sequence": seq,
                "family": row.get("family", ""),
                "label": 1,
                "ensemble": raw_scores["ensemble"],
            })

    # Load and score all decoys
    decoy_rows = []
    with open(decoy_csv, newline="", encoding="utf-8") as f:
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
            decoy_rows.append({
                "id": seq_id,
                "sequence": seq,
                "label": 0,
                "ensemble": raw_scores["ensemble"],
            })

    # Cluster the AMP set
    amp_seqs = [r["sequence"] for r in amp_rows]
    clusters = cluster_by_similarity(amp_seqs, threshold=similarity_threshold)

    # Map each AMP index to its cluster ID
    index_to_cluster: dict[int, int] = {}
    for cluster_id, cluster_members in enumerate(clusters):
        for member_idx in cluster_members:
            index_to_cluster[member_idx] = cluster_id

    n_clusters = len(clusters)
    multi_member_clusters = [c for c in clusters if len(c) > 1]
    n_in_multi = sum(len(c) for c in multi_member_clusters)

    # Cluster-aware AUROC: full set, but CI resamples clusters
    all_pos_scores = [r["ensemble"] for r in amp_rows]
    all_neg_scores = [r["ensemble"] for r in decoy_rows]
    full_auroc = round(_auc_wilcoxon(all_pos_scores, all_neg_scores), 4)
    cluster_assignments = [index_to_cluster[i] for i in range(len(amp_rows))]
    cluster_aware_ci = _cluster_aware_bootstrap_auroc_ci(
        all_pos_scores, all_neg_scores, cluster_assignments,
        n_bootstrap=n_bootstrap,
    )

    # Standard CI for comparison (to show the inflation)
    standard_ci = _bootstrap_auroc_ci(all_pos_scores, all_neg_scores, n_bootstrap=n_bootstrap)

    # Held-out recovery: non-representative cluster members vs decoys
    ref_indices = [c[0] for c in clusters]
    test_indices = [i for c in clusters for i in c[1:]]

    held_out_auroc = None
    held_out_ci = None
    held_out_n_pos = 0
    if test_indices:
        held_out_pos = [amp_rows[i]["ensemble"] for i in test_indices]
        held_out_auroc = round(_auc_wilcoxon(held_out_pos, all_neg_scores), 4)
        held_out_ci = _bootstrap_auroc_ci(held_out_pos, all_neg_scores, n_bootstrap=n_bootstrap)
        held_out_n_pos = len(test_indices)

    # Representative-only AUROC: one per cluster vs decoys
    rep_pos = [amp_rows[i]["ensemble"] for i in ref_indices]
    rep_auroc = round(_auc_wilcoxon(rep_pos, all_neg_scores), 4)
    rep_ci = _bootstrap_auroc_ci(rep_pos, all_neg_scores, n_bootstrap=n_bootstrap)

    # Interpretation based on cluster-aware CI lower bound
    ci_lo = cluster_aware_ci["ci_lo"]
    if full_auroc >= 0.70 and ci_lo >= 0.65:
        interpretation = (
            "STRONG — AUROC > 0.70 and cluster-aware CI lower bound > 0.65. "
            "Signal survives near-duplicate de-inflation."
        )
    elif full_auroc >= 0.70:
        interpretation = (
            "STRONG-AUROC-BUT-WIDE-CI — point estimate > 0.70 but cluster-aware CI "
            f"lower bound = {ci_lo:.4f} < 0.65. Near-duplicate clusters inflate apparent "
            "precision. Signal is real but less certain than standard CI suggests."
        )
    elif full_auroc >= 0.55:
        interpretation = (
            "WEAK — AUROC 0.55-0.70. Modest signal; proceed with caution."
        )
    else:
        interpretation = (
            "POOR — AUROC < 0.55. Model is near-random. Do NOT proceed to synthesis."
        )

    return {
        "benchmark": "cluster_split_retrospective",
        "n_positives": len(amp_rows),
        "n_negatives": len(decoy_rows),
        "n_total": len(amp_rows) + len(decoy_rows),
        "similarity_threshold": similarity_threshold,
        "n_clusters": n_clusters,
        "n_multi_member_clusters": len(multi_member_clusters),
        "n_amps_in_multi_member_clusters": n_in_multi,
        "n_independent_amps": n_clusters,
        "n_held_out_amps": held_out_n_pos,
        # Full-set AUROC (same as standard benchmark)
        "full_auroc": full_auroc,
        # Standard bootstrap CI (treats all sequences as independent — inflated)
        "standard_ci95_lo": standard_ci["ci_lo"],
        "standard_ci95_hi": standard_ci["ci_hi"],
        "standard_ci_note": (
            "Standard bootstrap treats near-duplicate sequences as independent. "
            "When the positive set contains near-duplicate clusters, this CI is "
            "artificially narrow."
        ),
        # Cluster-aware bootstrap CI (resamples clusters, not sequences)
        "cluster_aware_ci95_lo": cluster_aware_ci["ci_lo"],
        "cluster_aware_ci95_hi": cluster_aware_ci["ci_hi"],
        "cluster_aware_ci_mean": cluster_aware_ci["mean"],
        "cluster_aware_ci_note": (
            "Cluster-aware bootstrap resamples clusters (not individual sequences). "
            "This is the honest CI when the positive set contains near-duplicate families."
        ),
        # Held-out recovery: near-duplicate AMPs held out, scored vs decoys
        "held_out_auroc": held_out_auroc,
        "held_out_ci95_lo": held_out_ci["ci_lo"] if held_out_ci else None,
        "held_out_ci95_hi": held_out_ci["ci_hi"] if held_out_ci else None,
        "held_out_n_positives": held_out_n_pos,
        # Representative-only: one AMP per cluster vs decoys
        "representative_auroc": rep_auroc,
        "representative_ci95_lo": rep_ci["ci_lo"],
        "representative_ci95_hi": rep_ci["ci_hi"],
        "representative_n_positives": n_clusters,
        "interpretation": interpretation,
        "near_duplicate_clusters": [
            {
                "cluster_id": idx,
                "size": len(c),
                "members": [amp_rows[i]["id"] for i in c],
                "families": [amp_rows[i]["family"] for i in c],
            }
            for idx, c in enumerate(clusters) if len(c) > 1
        ],
        "disclaimer": (
            "Cluster-split benchmark controls for near-duplicate contamination in the "
            "positive set. The cluster-aware CI is the honest confidence interval. "
            "The standard CI is shown for comparison to reveal the inflation. "
            "AUROC > 0.70 does NOT imply nominated candidates are antimicrobial. "
            "Wet-lab validation remains mandatory."
        ),
    }


def run_expert_ablation_benchmark(
    amp_csv: str | Path,
    decoy_csv: str | Path,
    config_path: str | Path = "configs/pipeline.yaml",
    n_bootstrap: int = 2000,
) -> dict:
    """Expert-vs-ensemble ablation: does the expert composite beat the simple ensemble?

    The expert composite (scoring/expert.py) adds four components beyond the simple
    ensemble: selectivity, serum stability, helix-hinge, and k-mer motif novelty.
    The simple ensemble uses only activity, safety, synthesis, novelty, and Boman.

    If the expert composite does not outperform the simple ensemble on AUROC, the
    added complexity is not earning its keep — it may be noise dressed as sophistication.

    This benchmark also computes per-component AUROC (each component score alone vs
    the label) to identify which axes carry discriminative signal and which do not.

    Per AGENTS.md §7 (Benchmarks must be adversarial) and §7.5 (No simulation theater):
    every added modeling layer must justify itself against simpler baselines.

    Args:
        amp_csv: CSV of known AMPs (id, sequence, ...).
        decoy_csv: CSV of decoy peptides.
        config_path: Pipeline config for the simple ensemble weights.
        n_bootstrap: Bootstrap resample count for CIs.

    Returns:
        Dict with AUROC for ensemble and expert composite, per-component AUROCs,
        delta, bootstrap CIs, and an honest verdict.
    """
    from openamp_foundry.config import load_config
    from openamp_foundry.features.physchem import compute_features
    from openamp_foundry.scoring.activity import activity_likeness_score
    from openamp_foundry.scoring.boman import boman_activity_score, model_disagreement
    from openamp_foundry.scoring.ensemble import ensemble_score
    from openamp_foundry.scoring.expert import EXPERT_WEIGHTS, expert_score
    from openamp_foundry.scoring.novelty import novelty_score
    from openamp_foundry.scoring.safety import safety_score
    from openamp_foundry.scoring.stability import serum_stability_score
    from openamp_foundry.scoring.synthesis import synthesis_feasibility_score

    config = load_config(config_path)
    weights = config["weights"]

    rows = []
    for path, label in [(amp_csv, 1), (decoy_csv, 0)]:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                seq = row["sequence"].strip().upper()
                features = compute_features(seq)
                act = activity_likeness_score(features)
                safe = safety_score(features)
                valid = all(aa in "ACDEFGHIKLMNPQRSTVWY" for aa in seq)
                synth = synthesis_feasibility_score(features, valid_sequence=valid)
                nov, _ = novelty_score(seq, [])
                boman_act = boman_activity_score(seq)
                stability = serum_stability_score(features)
                raw = {
                    "activity": act, "safety": safe,
                    "synthesis": synth, "novelty": nov,
                    "boman_activity": boman_act,
                    "disagreement": model_disagreement(act, boman_act),
                    "serum_stability": stability,
                    "selectivity_proxy": features.get("selectivity_proxy", 1.0),
                }
                ens = ensemble_score(raw, weights)

                # Expert composite — no k-mer index (benchmark measures composition-based
                # signal only; motif novelty defaults to 1.0 for all sequences equally,
                # which correctly removes it as a discriminator and tests the other 6 axes).
                exp = expert_score(seq, features=features)

                rows.append({
                    "id": row["id"],
                    "label": label,
                    "ensemble": ens,
                    "expert_composite": exp.composite,
                    # Per-component scores for signal attribution
                    "activity": act,
                    "safety": safe,
                    "synthesis": synth,
                    "novelty": nov,
                    "boman_activity": boman_act,
                    "serum_stability": stability,
                    "selectivity_proxy": features.get("selectivity_proxy", 1.0),
                    "hinge_selectivity": exp.components["hinge_selectivity"],
                    "motif_novelty": exp.components["motif_novelty"],
                })

    pos = [r for r in rows if r["label"] == 1]
    neg = [r for r in rows if r["label"] == 0]

    ens_auroc = round(_auc_wilcoxon(
        [r["ensemble"] for r in pos], [r["ensemble"] for r in neg]
    ), 4)
    exp_auroc = round(_auc_wilcoxon(
        [r["expert_composite"] for r in pos], [r["expert_composite"] for r in neg]
    ), 4)

    ens_ci = _bootstrap_auroc_ci(
        [r["ensemble"] for r in pos], [r["ensemble"] for r in neg],
        n_bootstrap=n_bootstrap,
    )
    exp_ci = _bootstrap_auroc_ci(
        [r["expert_composite"] for r in pos], [r["expert_composite"] for r in neg],
        n_bootstrap=n_bootstrap,
    )

    delta = round(exp_auroc - ens_auroc, 4)

    # Per-component AUROC: which individual axes discriminate AMPs from decoys?
    component_cols = [
        "activity", "safety", "synthesis", "novelty",
        "boman_activity", "serum_stability", "selectivity_proxy",
        "hinge_selectivity", "motif_novelty",
    ]
    per_component = {}
    for col in component_cols:
        pos_vals = [r[col] for r in pos]
        neg_vals = [r[col] for r in neg]
        auroc = round(_auc_wilcoxon(pos_vals, neg_vals), 4)
        per_component[col] = {
            "auroc": auroc,
            "above_random": round(auroc - 0.5, 4),
        }

    # Honest verdict: does the expert composite earn its complexity?
    if delta > 0.02 and exp_ci["ci_lo"] > ens_ci["ci_lo"]:
        verdict = (
            f"Expert composite outperforms ensemble by {delta:+.4f} AUROC. "
            "Added complexity is justified by improved discrimination."
        )
    elif abs(delta) <= 0.02:
        verdict = (
            f"Expert composite ({exp_auroc:.4f}) and ensemble ({ens_auroc:.4f}) "
            f"are within ±0.02 AUROC. The expert composite's additional components "
            "(selectivity, serum stability, helix hinge, motif novelty) do NOT "
            "materially improve AMP-vs-decoy discrimination on this benchmark. "
            "They may still add value for candidate selection within the AMP-like "
            "envelope (e.g. safety ranking), but they are not better at the binary "
            "AMP/non-AMP task. The simple ensemble remains the primary synthesis gate."
        )
    else:
        verdict = (
            f"Expert composite ({exp_auroc:.4f}) scores LOWER than ensemble "
            f"({ens_auroc:.4f}) by {delta:+.4f} AUROC. The added components "
            "degrade discrimination on this benchmark. The expert composite should "
            "NOT replace the ensemble for AMP/non-AMP triage without further evidence."
        )

    # Component signal summary: which axes carry the discrimination?
    sorted_components = sorted(
        per_component.items(), key=lambda x: x[1]["above_random"], reverse=True
    )
    signal_bearing = [
        name for name, info in sorted_components if info["above_random"] > 0.05
    ]
    noise_components = [
        name for name, info in sorted_components if abs(info["above_random"]) <= 0.05
    ]
    anti_signal = [
        name for name, info in sorted_components if info["above_random"] < -0.05
    ]

    return {
        "benchmark": "expert_ablation",
        "n_positives": len(pos),
        "n_negatives": len(neg),
        "n_total": len(rows),
        "config_path": str(config_path),
        "expert_weights": EXPERT_WEIGHTS,
        "ensemble_auroc": ens_auroc,
        "ensemble_ci95_lo": ens_ci["ci_lo"],
        "ensemble_ci95_hi": ens_ci["ci_hi"],
        "expert_auroc": exp_auroc,
        "expert_ci95_lo": exp_ci["ci_lo"],
        "expert_ci95_hi": exp_ci["ci_hi"],
        "delta_auroc": delta,
        "per_component_auroc": per_component,
        "signal_bearing_components": signal_bearing,
        "near_zero_components": noise_components,
        "anti_signal_components": anti_signal,
        "verdict": verdict,
        "design_note": (
            "The expert composite (scoring/expert.py) adds selectivity, serum stability, "
            "hinge selectivity, and k-mer motif novelty on top of the ensemble axes. "
            "This ablation measures whether those additions improve binary AMP-vs-decoy "
            "discrimination. No k-mer index is used (motif_novelty = 1.0 for all), "
            "isolating the composition-based components. AUROC > 0.70 does NOT imply "
            "nominated candidates are antimicrobial."
        ),
        "disclaimer": (
            "Ablation results are computational only. A negative result does not mean "
            "the expert components are useless — they may improve within-AMP ranking "
            "(safety, selectivity) even if they do not improve AMP-vs-decoy separation. "
            "Wet-lab validation remains mandatory."
        ),
    }

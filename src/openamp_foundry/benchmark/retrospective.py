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
                    "hemolysis_safety": exp.components["hemolysis_safety"],
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
        "hinge_selectivity", "motif_novelty", "hemolysis_safety",
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


# ─────────────────────────────────────────────────────────────────────────────
# Within-AMP selectivity benchmark
# ─────────────────────────────────────────────────────────────────────────────

def run_selectivity_benchmark(
    hemolysis_csv: str | Path,
    config_path: str | Path = "configs/pipeline.yaml",
    n_bootstrap: int = 2000,
) -> dict:
    """Within-AMP selectivity benchmark: can scorers distinguish hemolytic from selective AMPs?

    The standard and expert-ablation benchmarks measure AMP-vs-decoy discrimination:
    can the pipeline tell AMPs from random peptides? The expert ablation found that
    safety, synthesis, and serum stability are anti-signal on that task — real AMPs
    have extreme biophysical properties that safety/stability scorers penalise.

    But those scorers were not designed for AMP-vs-decoy discrimination. They were
    designed for *within-AMP ranking*: given two peptides that are both AMP-like,
    which one is more likely to spare mammalian cells? This benchmark tests that.

    Design:
      - Positives (hemolytic): AMPs with literature HC50 < 25 µg/mL (HEMOLYTIC + MODERATE
        classes with HC50 ≤ 25).
      - Negatives (selective): AMPs with literature HC50 ≥ 100 µg/mL (SELECTIVE class).
      - MODERATE peptides with HC50 25–100 are excluded from the binary task to create
        a cleaner separation, but are reported separately as a "border zone" diagnostic.
      - The benchmark computes AUROC for every pipeline score (ensemble, activity,
        safety, selectivity_proxy, synthesis, serum_stability, boman_activity) and
        the expert composite, asking: which scores rank hemolytic AMPs *higher* than
        selective AMPs?

    A score that ranks hemolytic AMPs higher has AUROC > 0.5 (it detects hemolysis
    risk). A score that ranks selective AMPs higher has AUROC < 0.5 (it detects
    selectivity). The sign matters: for a safety scorer, AUROC < 0.5 is correct
    (safety should be lower for hemolytic peptides). We report both the raw AUROC
    and a "hemolysis-detection AUROC" where low-safety → high-risk is the correct
    direction.

    Args:
        hemolysis_csv: CSV with columns id, sequence, family, hc50_ugml,
            hemolysis_class, reference.
        config_path: Pipeline config for scoring weights.
        n_bootstrap: Bootstrap resample count for CIs.

    Returns:
        Dict with per-score AUROC, bootstrap CIs, hemolytic vs selective score
        distributions, border-zone diagnostics, and an honest verdict.
    """
    from openamp_foundry.config import load_config
    from openamp_foundry.features.physchem import compute_features
    from openamp_foundry.scoring.activity import activity_likeness_score
    from openamp_foundry.scoring.boman import boman_activity_score, model_disagreement
    from openamp_foundry.scoring.ensemble import ensemble_score
    from openamp_foundry.scoring.expert import expert_score
    from openamp_foundry.scoring.novelty import novelty_score
    from openamp_foundry.scoring.hemolysis import hemolysis_risk_score
    from openamp_foundry.scoring.safety import safety_score
    from openamp_foundry.scoring.selectivity_rich import rich_selectivity_score
    from openamp_foundry.scoring.stability import serum_stability_score
    from openamp_foundry.scoring.synthesis import synthesis_feasibility_score

    config = load_config(config_path)
    weights = config["weights"]

    rows: list[dict] = []
    with open(hemolysis_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seq = row["sequence"].strip().upper()
            if not all(aa in "ACDEFGHIKLMNPQRSTVWY" for aa in seq):
                continue
            hc50 = float(row["hc50_ugml"])
            hemo_class = row["hemolysis_class"].strip().upper()
            features = compute_features(seq)
            act = activity_likeness_score(features)
            safe = safety_score(features)
            synth = synthesis_feasibility_score(features, valid_sequence=True)
            nov, _ = novelty_score(seq, [])
            boman_act = boman_activity_score(seq)
            stability = serum_stability_score(features)
            sel_proxy = float(features.get("selectivity_proxy", 0.0))
            rich_sel = rich_selectivity_score(features)
            hemo_risk = hemolysis_risk_score(features)
            raw = {
                "activity": act, "safety": safe,
                "synthesis": synth, "novelty": nov,
                "boman_activity": boman_act,
                "disagreement": model_disagreement(act, boman_act),
                "serum_stability": stability,
                "selectivity_proxy": sel_proxy,
            }
            ens = ensemble_score(raw, weights)
            exp = expert_score(seq, features=features)

            rows.append({
                "id": row["id"],
                "sequence": seq,
                "family": row.get("family", ""),
                "hc50": hc50,
                "hemolysis_class": hemo_class,
                "ensemble": ens,
                "expert_composite": exp.composite,
                "activity": act,
                "safety": safe,
                "synthesis": synth,
                "novelty": nov,
                "boman_activity": boman_act,
                "serum_stability": stability,
                "selectivity_proxy": sel_proxy,
                "hemolysis_risk": hemo_risk,
                "rich_selectivity": rich_sel,
                "hinge_selectivity": exp.components["hinge_selectivity"],
            })

    # Binary task: hemolytic (HC50 < 25) vs selective (HC50 >= 100)
    hemolytic = [r for r in rows if r["hc50"] < 25]
    selective = [r for r in rows if r["hc50"] >= 100]
    border = [r for r in rows if 25 <= r["hc50"] < 100]

    n_hemo = len(hemolytic)
    n_sel = len(selective)
    n_border = len(border)

    # Score columns to evaluate
    score_cols = [
        "ensemble", "expert_composite", "activity", "safety",
        "synthesis", "novelty", "boman_activity", "serum_stability",
        "selectivity_proxy", "rich_selectivity", "hemolysis_risk", "hinge_selectivity",
    ]

    per_score: dict[str, dict] = {}
    for col in score_cols:
        hemo_scores = [r[col] for r in hemolytic]
        sel_scores = [r[col] for r in selective]
        auroc = round(_auc_wilcoxon(hemo_scores, sel_scores), 4)
        ci = _bootstrap_auroc_ci(hemo_scores, sel_scores, n_bootstrap=n_bootstrap)

        # For safety/selectivity scorers, the CORRECT direction is:
        # hemolytic AMPs should score LOWER (less safe, less selective).
        # So the "hemolysis-detection AUROC" = 1 - raw AUROC for those axes.
        # For risk-direction scorers (hemolysis_risk, synthesis), the CORRECT
        # direction is: hemolytic AMPs should score HIGHER (more risk).
        # So the "hemolysis-detection AUROC" = raw AUROC for those axes.
        # We report both and let the verdict interpret.
        if col in ("hemolysis_risk",):
            # Risk score: higher = more risk. Raw AUROC is already detection AUROC.
            detection_auroc = auroc
            detection_ci = {"ci_lo": ci["ci_lo"], "ci_hi": ci["ci_hi"]}
        else:
            detection_auroc = round(1.0 - auroc, 4)
            detection_ci = {
                "ci_lo": round(1.0 - ci["ci_hi"], 4),
                "ci_hi": round(1.0 - ci["ci_lo"], 4),
            }

        per_score[col] = {
            "auroc": auroc,
            "ci95_lo": ci["ci_lo"],
            "ci95_hi": ci["ci_hi"],
            # hemolysis_detection_auroc: AUROC when the positive class is "hemolytic"
            # and higher score = higher risk. For safety, detection_auroc = 1 - auroc
            # because lower safety = higher risk.
            "hemolysis_detection_auroc": detection_auroc,
            "detection_ci95_lo": detection_ci["ci_lo"],
            "detection_ci95_hi": detection_ci["ci_hi"],
            "mean_hemolytic": round(sum(hemo_scores) / n_hemo, 4) if hemo_scores else None,
            "mean_selective": round(sum(sel_scores) / n_sel, 4) if sel_scores else None,
            "direction": "higher_is_risk" if auroc > 0.5 else "higher_is_safe",
        }

    # Identify which scores detect hemolysis risk (detection AUROC > 0.5 with CI lo > 0.5)
    risk_detectors = [
        col for col, info in per_score.items()
        if info["hemolysis_detection_auroc"] > 0.5
        and info["detection_ci95_lo"] > 0.5
    ]
    risk_indicators = [
        col for col, info in per_score.items()
        if info["hemolysis_detection_auroc"] > 0.5
        and info["detection_ci95_lo"] <= 0.5
    ]

    # Key question: does the safety scorer detect hemolysis?
    safety_detection = per_score["safety"]["hemolysis_detection_auroc"]
    safety_ci_lo = per_score["safety"]["detection_ci95_lo"]

    if safety_detection > 0.5 and safety_ci_lo > 0.5:
        safety_verdict = (
            f"Safety scorer detects hemolysis risk (detection AUROC={safety_detection:.4f}, "
            f"CI lo={safety_ci_lo:.4f}). This is the first evidence that the safety scorer "
            "earns its keep on the within-AMP selectivity task."
        )
    elif safety_detection > 0.5:
        safety_verdict = (
            f"Safety scorer shows weak hemolysis detection (detection AUROC={safety_detection:.4f}, "
            f"CI lo={safety_ci_lo:.4f} < 0.5). Signal is present but not statistically significant. "
            "The melittin blind spot remains: 1D hydrophobic moment cannot capture all hemolysis mechanisms."
        )
    else:
        safety_verdict = (
            f"Safety scorer FAILS to detect hemolysis risk (detection AUROC={safety_detection:.4f}). "
            "This confirms the expert ablation finding: the safety scorer does not distinguish "
            "hemolytic from selective AMPs. Hemolysis must be assayed experimentally."
        )

    # Selectivity proxy assessment
    sel_detection = per_score["selectivity_proxy"]["hemolysis_detection_auroc"]
    sel_ci_lo = per_score["selectivity_proxy"]["detection_ci95_lo"]

    if sel_detection > 0.5 and sel_ci_lo > 0.5:
        sel_verdict = (
            f"Selectivity proxy detects hemolysis risk (detection AUROC={sel_detection:.4f}, "
            f"CI lo={sel_ci_lo:.4f}). The charge/GRAVY heuristic captures the selectivity signal."
        )
    elif sel_detection > 0.5:
        sel_verdict = (
            f"Selectivity proxy shows weak hemolysis detection (detection AUROC={sel_detection:.4f}, "
            f"CI lo={sel_ci_lo:.4f}). Trend is correct but not significant at this sample size."
        )
    else:
        sel_verdict = (
            f"Selectivity proxy does NOT detect hemolysis risk (detection AUROC={sel_detection:.4f}). "
            "The charge/GRAVY heuristic does not capture hemolysis on this reference set."
        )

    # Expert composite assessment
    exp_detection = per_score["expert_composite"]["hemolysis_detection_auroc"]
    ens_detection = per_score["ensemble"]["hemolysis_detection_auroc"]

    if exp_detection > ens_detection + 0.02:
        expert_verdict = (
            f"Expert composite detects hemolysis risk better than ensemble "
            f"(detection AUROC {exp_detection:.4f} vs {ens_detection:.4f}). "
            "The added selectivity/safety components earn their keep on within-AMP ranking."
        )
    elif abs(exp_detection - ens_detection) <= 0.02:
        expert_verdict = (
            f"Expert composite ({exp_detection:.4f}) and ensemble ({ens_detection:.4f}) "
            "are within ±0.02 on hemolysis detection. The expert components do not materially "
            "improve within-AMP selectivity on this reference set."
        )
    else:
        expert_verdict = (
            f"Expert composite detects hemolysis risk worse than ensemble "
            f"(detection AUROC {exp_detection:.4f} vs {ens_detection:.4f}). "
            "The expert components degrade within-AMP selectivity on this reference set."
        )

    # Hemolysis risk score assessment
    hemo_risk_detection = per_score["hemolysis_risk"]["hemolysis_detection_auroc"]
    hemo_risk_ci_lo = per_score["hemolysis_risk"]["detection_ci95_lo"]
    hemo_risk_ci_hi = per_score["hemolysis_risk"]["detection_ci95_hi"]

    if hemo_risk_detection > 0.5 and hemo_risk_ci_lo > 0.5:
        hemo_risk_verdict = (
            f"Dedicated hemolysis risk scorer detects hemolysis risk "
            f"(detection AUROC={hemo_risk_detection:.4f}, CI=[{hemo_risk_ci_lo:.4f}, {hemo_risk_ci_hi:.4f}]). "
            "This is the first pipeline score with a statistically significant hemolysis detection signal "
            "on this reference set. It complements (not replaces) the safety scorer, which fails this task. "
            "The safety scorer retains its role for AMP-vs-decoy discrimination; this score adds "
            "within-AMP hemolysis risk triage."
        )
    elif hemo_risk_detection > 0.5:
        hemo_risk_verdict = (
            f"Dedicated hemolysis risk scorer shows trend (detection AUROC={hemo_risk_detection:.4f}, "
            f"CI lo={hemo_risk_ci_lo:.4f}). Signal is present but not statistically significant."
        )
    else:
        hemo_risk_verdict = (
            f"Dedicated hemolysis risk scorer fails (detection AUROC={hemo_risk_detection:.4f}). "
            "No pipeline score can distinguish hemolytic from selective AMPs."
        )

    # Rich selectivity scorer assessment (evidence-driven composite from feature decomposition)
    rich_detection = per_score["rich_selectivity"]["hemolysis_detection_auroc"]
    rich_ci_lo = per_score["rich_selectivity"]["detection_ci95_lo"]
    rich_ci_hi = per_score["rich_selectivity"]["detection_ci95_hi"]

    if rich_detection > 0.5 and rich_ci_lo > 0.5:
        rich_verdict = (
            f"Rich selectivity scorer detects hemolysis risk "
            f"(detection AUROC={rich_detection:.4f}, CI=[{rich_ci_lo:.4f}, {rich_ci_hi:.4f}]). "
            "This is the first composite selectivity score built from evidence-identified features "
            "(feature decomposition benchmark v0.5.15) that achieves statistically significant "
            "selective_vs_hemolytic discrimination. It outperforms the old selectivity_proxy "
            f"(detection AUROC={sel_detection:.4f}). The signal comes from combining 8 significant "
            "physicochemical features that the old proxy ignored."
        )
    elif rich_detection > 0.5:
        rich_verdict = (
            f"Rich selectivity scorer shows trend (detection AUROC={rich_detection:.4f}, "
            f"CI lo={rich_ci_lo:.4f}). Signal is present but not statistically significant."
        )
    else:
        rich_verdict = (
            f"Rich selectivity scorer fails (detection AUROC={rich_detection:.4f}). "
            "Combining significant features did not improve selective_vs_hemolytic discrimination."
        )

    # Rank hemolytic AMPs by safety score to find blind spots
    hemolytic_by_safety = sorted(hemolytic, key=lambda r: r["safety"], reverse=True)
    blind_spots = [
        {"id": r["id"], "sequence": r["sequence"], "family": r["family"],
         "hc50": r["hc50"], "safety": r["safety"], "selectivity_proxy": r["selectivity_proxy"],
         "hemolysis_risk": r["hemolysis_risk"]}
        for r in hemolytic_by_safety if r["safety"] >= 0.8
    ]

    return {
        "benchmark": "within_amp_selectivity",
        "n_total": len(rows),
        "n_hemolytic": n_hemo,
        "n_selective": n_sel,
        "n_border": n_border,
        "hemolytic_threshold_hc50": 25,
        "selective_threshold_hc50": 100,
        "per_score_auroc": per_score,
        "risk_detectors": risk_detectors,
        "risk_indicators": risk_indicators,
        "safety_verdict": safety_verdict,
        "selectivity_proxy_verdict": sel_verdict,
        "expert_composite_verdict": expert_verdict,
        "hemolysis_risk_verdict": hemo_risk_verdict,
        "rich_selectivity_verdict": rich_verdict,
        "blind_spots": blind_spots,
        "border_zone": [
            {"id": r["id"], "sequence": r["sequence"], "family": r["family"],
             "hc50": r["hc50"], "safety": r["safety"],
             "selectivity_proxy": r["selectivity_proxy"]}
            for r in sorted(border, key=lambda r: r["hc50"])
        ],
        "hemolysis_risk_scores": [
            {"id": r["id"], "sequence": r["sequence"], "family": r["family"],
             "hc50": r["hc50"], "hemolysis_class": r["hemolysis_class"],
             "hemolysis_risk": r["hemolysis_risk"], "safety": r["safety"]}
            for r in sorted(rows, key=lambda r: r["hemolysis_risk"], reverse=True)
        ],
        "design_note": (
            "Within-AMP selectivity benchmark: all sequences are confirmed AMPs. "
            "The task is NOT 'is this an AMP?' but 'is this AMP likely to be hemolytic?'. "
            "Hemolytic class: HC50 < 25 µg/mL. Selective class: HC50 >= 100 µg/mL. "
            "Border zone (25-100) excluded from binary AUROC, reported separately. "
            "HC50 values are approximate literature values from multiple sources; "
            "they vary with assay conditions (RBC source, buffer, incubation time). "
            "This is a coarse triage benchmark, not a calibrated hemolysis predictor."
        ),
        "disclaimer": (
            "HC50 values are approximate literature values with high inter-assay variability. "
            "This benchmark tests whether the pipeline's physicochemical scorers can distinguish "
            "hemolytic from selective AMPs. It does NOT predict any individual candidate's "
            "hemolysis. Hemolysis must be assayed experimentally for every candidate. "
            "Wet-lab validation remains mandatory."
        ),
    }

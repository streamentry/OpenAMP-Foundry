"""Batch pack report generator for Phase 3 lab-ready candidate batches.

Reads the ranked JSONL output and produces all four required sub-reports:
  1. Diversity clustering report
  2. Novelty report
  3. Toxicity/hemolysis risk report
  4. Synthesis feasibility report

All sub-reports are computational heuristics only.
No biological claims are made. The lab is the judge.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openamp_foundry.benchmark.splits import cluster_by_similarity
from openamp_foundry.scoring.stability import serum_stability_score


def _load_ranked_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _selected(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rows if r.get("selected", False)]


# ---------------------------------------------------------------------------
# 1. Diversity clustering report
# ---------------------------------------------------------------------------

def diversity_clustering_report(
    selected: list[dict[str, Any]],
    threshold: float = 0.80,
) -> dict[str, Any]:
    """Cluster the selected candidates by pairwise similarity.

    Reports how many distinct clusters exist and the within-cluster size distribution.
    A higher number of singleton clusters indicates greater diversity.
    """
    seqs = [r["sequence"] for r in selected]
    ids = [r["candidate_id"] for r in selected]
    clusters = cluster_by_similarity(seqs, threshold=threshold)

    cluster_details = []
    for cluster in clusters:
        cluster_details.append({
            "size": len(cluster),
            "members": [ids[i] for i in cluster],
            "representative": ids[cluster[0]],
        })

    n_singletons = sum(1 for c in cluster_details if c["size"] == 1)
    max_cluster_size = max(c["size"] for c in cluster_details) if cluster_details else 0

    return {
        "report_type": "diversity_clustering",
        "disclaimer": (
            "Pairwise similarity is computed by normalised Levenshtein distance. "
            "Structural or functional diversity is not assessed. "
            "This is a sequence-level diversity proxy only."
        ),
        "n_selected": len(selected),
        "similarity_threshold": threshold,
        "n_clusters": len(cluster_details),
        "n_singleton_clusters": n_singletons,
        "max_cluster_size": max_cluster_size,
        "singleton_fraction": round(n_singletons / len(cluster_details), 4) if cluster_details else 0.0,
        "clusters": cluster_details,
    }


# ---------------------------------------------------------------------------
# 2. Novelty report
# ---------------------------------------------------------------------------

def novelty_report(selected: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarise novelty scores across the selected batch.

    Novelty is the fraction of positions that differ from the nearest known reference.
    A novelty of 0.0 means the sequence is identical to a reference.
    A novelty of 1.0 means no similar reference exists.
    """
    novelty_scores = [r["scores"]["novelty"] for r in selected]

    n_high_novelty = sum(1 for s in novelty_scores if s >= 0.30)
    n_mid_novelty = sum(1 for s in novelty_scores if 0.10 <= s < 0.30)
    n_low_novelty = sum(1 for s in novelty_scores if s < 0.10)

    mean_novelty = sum(novelty_scores) / len(novelty_scores) if novelty_scores else 0.0
    min_novelty = min(novelty_scores) if novelty_scores else 0.0
    max_novelty = max(novelty_scores) if novelty_scores else 0.0

    # Per-candidate detail
    details = []
    for r in sorted(selected, key=lambda x: x["scores"]["novelty"], reverse=True):
        details.append({
            "candidate_id": r["candidate_id"],
            "novelty": r["scores"]["novelty"],
            "nearest_reference": r.get("nearest_reference"),
        })

    return {
        "report_type": "novelty_report",
        "disclaimer": (
            "Novelty is computed as 1 - normalised_Levenshtein_similarity against the nearest "
            "reference sequence. This is a sequence-level proxy. Structural or functional "
            "novelty is not assessed. A high novelty score does not guarantee biological novelty."
        ),
        "n_selected": len(selected),
        "mean_novelty": round(mean_novelty, 4),
        "min_novelty": round(min_novelty, 4),
        "max_novelty": round(max_novelty, 4),
        "n_high_novelty_ge_0_30": n_high_novelty,
        "n_mid_novelty_0_10_to_0_30": n_mid_novelty,
        "n_low_novelty_lt_0_10": n_low_novelty,
        "candidates": details,
    }


# ---------------------------------------------------------------------------
# 3. Toxicity / hemolysis risk report
# ---------------------------------------------------------------------------

_TOXICITY_THRESHOLDS = {
    "hydrophobic_fraction_high": 0.65,
    "charge_density_high": 0.55,
    "cysteine_fraction_high": 0.25,
    "longest_repeat_run_high": 6,
    "length_high": 35,
}


def _toxicity_flags(features: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    if features.get("hydrophobic_fraction", 0.0) > _TOXICITY_THRESHOLDS["hydrophobic_fraction_high"]:
        flags.append("high_hydrophobic_fraction")
    if features.get("charge_density", 0.0) > _TOXICITY_THRESHOLDS["charge_density_high"]:
        flags.append("high_charge_density")
    if features.get("cysteine_fraction", 0.0) > _TOXICITY_THRESHOLDS["cysteine_fraction_high"]:
        flags.append("high_cysteine_fraction")
    if features.get("longest_repeat_run", 0) >= _TOXICITY_THRESHOLDS["longest_repeat_run_high"]:
        flags.append("long_repeat_run")
    if features.get("length", 0) > _TOXICITY_THRESHOLDS["length_high"]:
        flags.append("length_exceeds_35aa")
    return flags


def toxicity_hemolysis_risk_report(selected: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarise predicted toxicity/hemolysis risk signals for selected candidates.

    Risk signals are computational proxies based on physicochemical features.
    They are NOT validated hemolysis or cytotoxicity predictors.
    """
    safety_scores = [r["scores"]["safety"] for r in selected]
    mean_safety = sum(safety_scores) / len(safety_scores) if safety_scores else 0.0

    per_candidate = []
    n_flagged = 0
    for r in selected:
        flags = _toxicity_flags(r.get("features", {}))
        if flags:
            n_flagged += 1
        per_candidate.append({
            "candidate_id": r["candidate_id"],
            "safety_score": r["scores"]["safety"],
            "hydrophobic_fraction": r.get("features", {}).get("hydrophobic_fraction"),
            "charge_density": r.get("features", {}).get("charge_density"),
            "cysteine_fraction": r.get("features", {}).get("cysteine_fraction"),
            "longest_repeat_run": r.get("features", {}).get("longest_repeat_run"),
            "risk_flags": flags,
        })

    per_candidate.sort(key=lambda x: x["safety_score"])

    return {
        "report_type": "toxicity_hemolysis_risk",
        "disclaimer": (
            "Risk flags are physicochemical heuristics — they are NOT validated predictors "
            "of hemolysis, cytotoxicity, or mammalian toxicity. "
            "All candidates require wet-lab safety profiling before any use. "
            "High safety score does not mean the peptide is safe."
        ),
        "n_selected": len(selected),
        "mean_safety_score": round(mean_safety, 4),
        "n_with_risk_flags": n_flagged,
        "risk_thresholds": _TOXICITY_THRESHOLDS,
        "candidates": per_candidate,
    }


# ---------------------------------------------------------------------------
# 4. Synthesis feasibility report
# ---------------------------------------------------------------------------

def synthesis_feasibility_report(selected: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarise predicted synthesis feasibility for selected candidates.

    Synthesis score is a heuristic based on sequence composition and length.
    It is not a validated synthesis prediction.
    """
    synth_scores = [r["scores"]["synthesis"] for r in selected]
    mean_synth = sum(synth_scores) / len(synth_scores) if synth_scores else 0.0

    n_high = sum(1 for s in synth_scores if s >= 0.80)
    n_mid = sum(1 for s in synth_scores if 0.50 <= s < 0.80)
    n_low = sum(1 for s in synth_scores if s < 0.50)

    per_candidate = []
    for r in sorted(selected, key=lambda x: x["scores"]["synthesis"]):
        features = r.get("features", {})
        per_candidate.append({
            "candidate_id": r["candidate_id"],
            "synthesis_score": r["scores"]["synthesis"],
            "sequence": r["sequence"],
            "length": features.get("length"),
            "cysteine_fraction": features.get("cysteine_fraction"),
            "proline_fraction": features.get("proline_fraction"),
            "longest_repeat_run": features.get("longest_repeat_run"),
        })

    return {
        "report_type": "synthesis_feasibility",
        "disclaimer": (
            "Synthesis feasibility score is a heuristic based on length, cysteine content, "
            "proline content, and repeat runs. It is not a validated synthesis prediction. "
            "All candidates should be reviewed by a peptide synthesis expert before ordering."
        ),
        "n_selected": len(selected),
        "mean_synthesis_score": round(mean_synth, 4),
        "n_high_feasibility_ge_0_80": n_high,
        "n_mid_feasibility_0_50_to_0_80": n_mid,
        "n_low_feasibility_lt_0_50": n_low,
        "candidates": per_candidate,
    }


# ---------------------------------------------------------------------------
# 5. Scorer consensus (Boman index vs. activity-likeness disagreement)
# ---------------------------------------------------------------------------

def scorer_consensus_report(selected: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarise dual-scorer consensus across selected candidates.

    Disagreement = |activity_likeness − boman_activity|.
    Low disagreement (< 0.20): both independent scorers agree → more robust nomination.
    High disagreement (≥ 0.30): scorers diverge → extra scrutiny recommended.
    """
    per_candidate = []
    for r in selected:
        scores = r.get("scores", {})
        act = scores.get("activity")
        boman_act = scores.get("boman_activity")
        disagreement = scores.get("disagreement")
        if act is None or boman_act is None:
            continue
        per_candidate.append({
            "candidate_id": r["candidate_id"],
            "activity_likeness": act,
            "boman_activity": boman_act,
            "disagreement": disagreement,
            "consensus_label": (
                "high_consensus" if (disagreement is not None and disagreement < 0.20)
                else "uncertain" if (disagreement is not None and disagreement >= 0.30)
                else "moderate"
            ),
        })

    per_candidate.sort(key=lambda x: x.get("disagreement") or 1.0)

    n_high_consensus = sum(1 for c in per_candidate if c["consensus_label"] == "high_consensus")
    n_uncertain = sum(1 for c in per_candidate if c["consensus_label"] == "uncertain")
    n_moderate = sum(1 for c in per_candidate if c["consensus_label"] == "moderate")

    disagreements = [c["disagreement"] for c in per_candidate if c["disagreement"] is not None]
    mean_disagreement = sum(disagreements) / len(disagreements) if disagreements else 0.0

    return {
        "report_type": "scorer_consensus",
        "disclaimer": (
            "Model disagreement is a computational uncertainty proxy only. "
            "It is NOT a biological activity or safety measure. "
            "High consensus means two independent heuristics agree; "
            "it does not increase the probability of lab activity. "
            "The lab is the judge."
        ),
        "n_selected": len(selected),
        "n_scored_with_boman": len(per_candidate),
        "n_high_consensus_lt_0_20": n_high_consensus,
        "n_moderate_0_20_to_0_30": n_moderate,
        "n_uncertain_ge_0_30": n_uncertain,
        "mean_disagreement": round(mean_disagreement, 4),
        "candidates": per_candidate,
    }


# ---------------------------------------------------------------------------
# Full batch pack
# ---------------------------------------------------------------------------

def generate_batch_pack(
    ranked_jsonl_path: str | Path,
    diversity_threshold: float = 0.80,
) -> dict[str, Any]:
    """Generate the complete Phase 3 batch pack.

    Returns a single dict containing all four sub-reports and a top-level summary.
    """
    rows = _load_ranked_jsonl(ranked_jsonl_path)
    sel = _selected(rows)

    diversity = diversity_clustering_report(sel, threshold=diversity_threshold)
    novelty = novelty_report(sel)
    toxicity = toxicity_hemolysis_risk_report(sel)
    synthesis = synthesis_feasibility_report(sel)
    consensus = scorer_consensus_report(sel)

    ensemble_scores = [r["scores"]["ensemble"] for r in sel]
    mean_ensemble = sum(ensemble_scores) / len(ensemble_scores) if ensemble_scores else 0.0

    stability_scores = [
        serum_stability_score(r["features"])
        for r in sel
        if r.get("features")
    ]
    mean_stability = sum(stability_scores) / len(stability_scores) if stability_scores else 0.0
    n_high_stability = sum(1 for s in stability_scores if s >= 0.50)

    return {
        "batch_pack_version": "1.1",
        "disclaimer": (
            "All reports in this batch pack are based on computational heuristics. "
            "No biological activity has been demonstrated. "
            "These candidates are nominated for possible expert review and wet-lab assay. "
            "The lab is the judge."
        ),
        "summary": {
            "n_candidates_scored": len(rows),
            "n_candidates_selected": len(sel),
            "mean_ensemble_score": round(mean_ensemble, 4),
            "n_diversity_clusters": diversity["n_clusters"],
            "n_singleton_clusters": diversity["n_singleton_clusters"],
            "mean_novelty": novelty["mean_novelty"],
            "mean_safety": toxicity["mean_safety_score"],
            "mean_synthesis": synthesis["mean_synthesis_score"],
            "n_high_consensus": consensus["n_high_consensus_lt_0_20"],
            "n_uncertain_disagreement": consensus["n_uncertain_ge_0_30"],
            "mean_scorer_disagreement": consensus["mean_disagreement"],
            "mean_serum_stability": round(mean_stability, 4),
            "n_high_serum_stability": n_high_stability,
        },
        "diversity_clustering": diversity,
        "novelty_report": novelty,
        "toxicity_hemolysis_risk": toxicity,
        "synthesis_feasibility": synthesis,
        "scorer_consensus": consensus,
    }


def write_batch_pack_markdown(pack: dict[str, Any], path: str | Path) -> None:
    """Write a human-readable markdown version of the batch pack."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    s = pack["summary"]
    div = pack["diversity_clustering"]
    nov = pack["novelty_report"]
    tox = pack["toxicity_hemolysis_risk"]
    syn = pack["synthesis_feasibility"]
    con = pack.get("scorer_consensus", {})

    lines = [
        "# OpenAMP Foundry — Phase 3 Batch Pack",
        "",
        f"> **{pack['disclaimer']}**",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Candidates scored | {s['n_candidates_scored']} |",
        f"| Candidates selected | {s['n_candidates_selected']} |",
        f"| Mean ensemble score | {s['mean_ensemble_score']:.4f} |",
        f"| Diversity clusters | {s['n_diversity_clusters']} |",
        f"| Singleton clusters | {s['n_singleton_clusters']} |",
        f"| Mean novelty | {s['mean_novelty']:.4f} |",
        f"| Mean safety | {s['mean_safety']:.4f} |",
        f"| Mean synthesis feasibility | {s['mean_synthesis']:.4f} |",
        f"| Mean predicted serum stability | {s.get('mean_serum_stability', 0.0):.4f} |",
        f"| High serum stability (≥0.50) | {s.get('n_high_serum_stability', 'N/A')} |",
        f"| High scorer consensus (disagreement <0.20) | {s.get('n_high_consensus', 'N/A')} |",
        f"| Uncertain (disagreement ≥0.30) | {s.get('n_uncertain_disagreement', 'N/A')} |",
        f"| Mean scorer disagreement | {s.get('mean_scorer_disagreement', 0.0):.4f} |",
        "",
        "---",
        "",
        "## 1. Diversity Clustering Report",
        "",
        f"> {div['disclaimer']}",
        "",
        f"- Similarity threshold: {div['similarity_threshold']}",
        f"- Number of clusters: {div['n_clusters']}",
        f"- Singleton clusters: {div['n_singleton_clusters']} ({div['singleton_fraction']:.1%})",
        f"- Largest cluster size: {div['max_cluster_size']}",
        "",
        "| Cluster | Size | Representative |",
        "|---------|------|----------------|",
    ]
    for i, cluster in enumerate(div["clusters"][:20], start=1):
        lines.append(f"| {i} | {cluster['size']} | {cluster['representative']} |")
    if len(div["clusters"]) > 20:
        lines.append(f"| … | … | ({len(div['clusters']) - 20} more clusters) |")

    lines += [
        "",
        "---",
        "",
        "## 2. Novelty Report",
        "",
        f"> {nov['disclaimer']}",
        "",
        f"- Mean novelty: {nov['mean_novelty']:.4f}",
        f"- Min novelty: {nov['min_novelty']:.4f}",
        f"- Max novelty: {nov['max_novelty']:.4f}",
        f"- High novelty (≥0.30): {nov['n_high_novelty_ge_0_30']}",
        f"- Mid novelty (0.10–0.30): {nov['n_mid_novelty_0_10_to_0_30']}",
        f"- Low novelty (<0.10): {nov['n_low_novelty_lt_0_10']}",
        "",
        "Top 10 most novel candidates:",
        "",
        "| Candidate | Novelty | Nearest Reference |",
        "|-----------|---------|-------------------|",
    ]
    for c in nov["candidates"][:10]:
        ref = c["nearest_reference"] or "none"
        lines.append(f"| {c['candidate_id']} | {c['novelty']:.4f} | {ref} |")

    lines += [
        "",
        "---",
        "",
        "## 3. Toxicity / Hemolysis Risk Report",
        "",
        f"> {tox['disclaimer']}",
        "",
        f"- Mean safety score: {tox['mean_safety_score']:.4f}",
        f"- Candidates with risk flags: {tox['n_with_risk_flags']} / {tox['n_selected']}",
        "",
        "Risk thresholds:",
        "",
    ]
    for k, v in tox["risk_thresholds"].items():
        lines.append(f"- {k}: {v}")
    lines += [
        "",
        "Candidates by ascending safety score (lowest safety first):",
        "",
        "| Candidate | Safety | Hydrophobic | Charge density | Risk flags |",
        "|-----------|--------|-------------|----------------|------------|",
    ]
    for c in tox["candidates"][:15]:
        flags = ", ".join(c["risk_flags"]) if c["risk_flags"] else "none"
        lines.append(
            f"| {c['candidate_id']} | {c['safety_score']:.4f} | "
            f"{c['hydrophobic_fraction']:.2f} | {c['charge_density']:.2f} | {flags} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 4. Synthesis Feasibility Report",
        "",
        f"> {syn['disclaimer']}",
        "",
        f"- Mean synthesis score: {syn['mean_synthesis_score']:.4f}",
        f"- High feasibility (≥0.80): {syn['n_high_feasibility_ge_0_80']}",
        f"- Mid feasibility (0.50–0.80): {syn['n_mid_feasibility_0_50_to_0_80']}",
        f"- Low feasibility (<0.50): {syn['n_low_feasibility_lt_0_50']}",
        "",
        "Candidates by ascending synthesis score (lowest feasibility first):",
        "",
        "| Candidate | Synthesis | Length | Cys% | Pro% | Repeat |",
        "|-----------|-----------|--------|------|------|--------|",
    ]
    for c in syn["candidates"][:15]:
        cys = f"{(c['cysteine_fraction'] or 0):.2f}"
        pro = f"{(c['proline_fraction'] or 0):.2f}"
        repeat = c["longest_repeat_run"] or 0
        lines.append(
            f"| {c['candidate_id']} | {c['synthesis_score']:.4f} | "
            f"{c['length']} | {cys} | {pro} | {repeat} |"
        )

    if con:
        lines += [
            "",
            "---",
            "",
            "## 5. Scorer Consensus Report",
            "",
            f"> {con.get('disclaimer', '')}",
            "",
            f"- High consensus (disagreement <0.20): {con.get('n_high_consensus_lt_0_20', 'N/A')} candidates",
            f"- Moderate disagreement (0.20–0.30): {con.get('n_moderate_0_20_to_0_30', 'N/A')} candidates",
            f"- Uncertain (disagreement ≥0.30): {con.get('n_uncertain_ge_0_30', 'N/A')} candidates",
            f"- Mean disagreement: {con.get('mean_disagreement', 0.0):.4f}",
            "",
            "Candidates sorted by disagreement (lowest = strongest dual-scorer consensus):",
            "",
            "| Candidate | Activity | Boman Activity | Disagreement | Consensus |",
            "|-----------|----------|----------------|--------------|-----------|",
        ]
        for c in con.get("candidates", [])[:20]:
            lines.append(
                f"| {c['candidate_id']} | {c['activity_likeness']:.4f} | "
                f"{c['boman_activity']:.4f} | {c.get('disagreement', 0.0):.4f} | "
                f"{c['consensus_label']} |"
            )

    lines += [
        "",
        "---",
        "",
        "## Next Steps (Human Review Required)",
        "",
        "Before any candidate proceeds to wet-lab assay:",
        "",
        "- [ ] Expert peptide chemist reviews synthesis feasibility for each candidate",
        "- [ ] Microbiologist reviews candidate selection and target organisms",
        "- [ ] Safety officer reviews toxicity risk flags",
        "- [ ] PI or qualified reviewer approves batch release",
        "- [ ] CRO or lab partner is selected and contacted",
        "- [ ] Pre-registered pass/fail criteria locked (see `docs/evidence/SELECTION_RULE.md`)",
        "",
        "**No candidate may proceed without human expert sign-off.**",
        "",
    ]

    p.write_text("\n".join(lines), encoding="utf-8")

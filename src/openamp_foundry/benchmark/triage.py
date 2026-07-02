"""Multi-class triage benchmark: can the pipeline rank selective AMPs above
hemolytic AMPs above random decoys in a single combined panel?

This benchmark directly addresses the v1.1 ROADMAP item:
  "benchmark candidate triage against a reference panel that includes
   selective AMPs, hemolytic positives, inactive peptides, and random controls."

The existing benchmarks test two separate 2-class problems:
  - AMP vs decoy (retrospective AUROC)
  - Hemolytic vs selective (within-AMP selectivity)

But the virtual assay layer must solve a *combined* triage task: given a mixed
panel, rank candidates that are both active AND selective above those that are
active but hemolytic, and both above non-AMP random controls. No existing
benchmark tests this.

The benchmark assembles three classes from existing datasets:
  1. SELECTIVE — AMPs with HC50 >= 100 µg/mL (from hemolysis_reference.csv)
  2. HEMOLYTIC — AMPs with HC50 < 25 µg/mL (from hemolysis_reference.csv)
  3. DECOY    — random background peptides (from random_background.csv)

For each pair of classes, we compute AUROC. The key question is whether the
pipeline ranks SELECTIVE > HEMOLYTIC (currently it does NOT — the ensemble has
an anti-selective bias documented in METRICS_CURRENT.md).

We also compute a "triage score" = activity * (1 - hemolysis_risk), which
combines activity with hemolysis penalty. This is the simplest possible
virtual-assay-style composite, and the benchmark tests whether it improves
triage over the raw ensemble.

All results are computational. No biological activity is implied.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from openamp_foundry.benchmark.retrospective import _auc_wilcoxon, _bootstrap_auroc_ci
from openamp_foundry.config import load_config
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.scoring.activity import activity_likeness_score
from openamp_foundry.scoring.boman import boman_activity_score, model_disagreement
from openamp_foundry.scoring.ensemble import ensemble_score
from openamp_foundry.scoring.expert import expert_score
from openamp_foundry.scoring.hemolysis import hemolysis_risk_score
from openamp_foundry.scoring.novelty import novelty_score
from openamp_foundry.scoring.safety import safety_score
from openamp_foundry.scoring.stability import serum_stability_score
from openamp_foundry.scoring.synthesis import synthesis_feasibility_score


def _load_hemolysis_reference(path: str | Path) -> list[dict[str, Any]]:
    """Load hemolysis_reference.csv and return rows with parsed hc50 and class."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seq = row["sequence"].strip().upper()
            if not all(aa in "ACDEFGHIKLMNPQRSTVWY" for aa in seq):
                continue
            hc50 = float(row["hc50_ugml"])
            hemo_class = row["hemolysis_class"].strip().upper()
            rows.append({
                "id": row["id"],
                "sequence": seq,
                "family": row.get("family", ""),
                "hc50_ugml": hc50,
                "hemolysis_class": hemo_class,
                "reference": row.get("reference", ""),
            })
    return rows


def _load_random_background(path: str | Path) -> list[dict[str, Any]]:
    """Load random_background.csv."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seq = row["sequence"].strip().upper()
            if not all(aa in "ACDEFGHIKLMNPQRSTVWY" for aa in seq):
                continue
            rows.append({
                "id": row["id"],
                "sequence": seq,
                "family": row.get("family", "background"),
                "source": row.get("source", ""),
            })
    return rows


def _score_all(rows: list[dict[str, Any]], weights: dict[str, float]) -> list[dict[str, Any]]:
    """Score all rows with the full pipeline + triage composite."""
    scored = []
    for row in rows:
        seq = row["sequence"]
        features = compute_features(seq)
        act = activity_likeness_score(features)
        safe = safety_score(features)
        synth = synthesis_feasibility_score(features, valid_sequence=True)
        nov, _ = novelty_score(seq, [])
        boman_act = boman_activity_score(seq)
        stability = serum_stability_score(features)
        sel_proxy = float(features.get("selectivity_proxy", 0.0))
        hemo_risk = hemolysis_risk_score(features)
        exp = expert_score(seq, features=features)
        raw = {
            "activity": act, "safety": safe,
            "synthesis": synth, "novelty": nov,
            "boman_activity": boman_act,
            "disagreement": model_disagreement(act, boman_act),
            "serum_stability": stability,
            "selectivity_proxy": sel_proxy,
        }
        ens = ensemble_score(raw, weights)
        # Triage composite: activity penalized by hemolysis risk.
        # This is the simplest virtual-assay-style score: it rewards activity
        # but penalizes candidates with high hemolysis risk.
        triage_score = round(act * (1.0 - hemo_risk), 4)
        # Safety-weighted ensemble: same weights but safety replaced by
        # safety * (1 - hemolysis_risk) to penalize hemolytic candidates.
        safe_adjusted = round(safe * (1.0 - hemo_risk), 4)
        raw_adjusted = dict(raw)
        raw_adjusted["safety"] = safe_adjusted
        safe_weighted_ens = ensemble_score(raw_adjusted, weights)
        scored.append({
            **row,
            "ensemble": round(ens, 4),
            "activity": round(act, 4),
            "safety": round(safe, 4),
            "synthesis": round(synth, 4),
            "boman_activity": round(boman_act, 4),
            "serum_stability": round(stability, 4),
            "selectivity_proxy": round(sel_proxy, 4),
            "hemolysis_risk": round(hemo_risk, 4),
            "expert_composite": exp.composite,
            "triage_score": triage_score,
            "safe_weighted_ensemble": round(safe_weighted_ens, 4),
        })
    return scored


def _pairwise_auroc(
    pos_scores: list[float], neg_scores: list[float], n_bootstrap: int = 2000,
) -> dict[str, Any]:
    """Compute AUROC and bootstrap CI for a pair of score distributions."""
    auroc = round(_auc_wilcoxon(pos_scores, neg_scores), 4)
    ci = _bootstrap_auroc_ci(pos_scores, neg_scores, n_bootstrap=n_bootstrap)
    return {
        "auroc": auroc,
        "ci_lo": ci["ci_lo"],
        "ci_hi": ci["ci_hi"],
        "n_pos": len(pos_scores),
        "n_neg": len(neg_scores),
    }


def run_triage_benchmark(
    hemolysis_csv: str | Path,
    decoy_csv: str | Path,
    config_path: str | Path = "configs/pipeline.yaml",
    n_bootstrap: int = 2000,
) -> dict[str, Any]:
    """Run the multi-class triage benchmark.

    Tests whether the pipeline can rank:
      SELECTIVE AMPs > HEMOLYTIC AMPs > DECOY random peptides

    For each scorer, computes pairwise AUROC for all three class pairs.
    A scorer that triages correctly should have:
      - AUROC(selective vs decoy) > 0.5 (selective rank above decoy)
      - AUROC(hemolytic vs decoy) > 0.5 (hemolytic rank above decoy)
      - AUROC(selective vs hemolytic) > 0.5 (selective rank above hemolytic)

    The last condition is the hardest: the existing ensemble has an anti-selective
    bias (it ranks hemolytic AMPs above selective AMPs because hemolytic AMPs have
    stronger amphipathic helices).

    Returns a dict with per-scorer pairwise AUROCs, class distributions, and
    an honest verdict.
    """
    config = load_config(config_path)
    weights = config["weights"]

    hemo_rows = _load_hemolysis_reference(hemolysis_csv)
    decoy_rows = _load_random_background(decoy_csv)

    selective = [r for r in hemo_rows if r["hemolysis_class"] == "SELECTIVE"]
    hemolytic = [r for r in hemo_rows if r["hemolysis_class"] == "HEMOLYTIC"]

    selective_scored = _score_all(selective, weights)
    hemolytic_scored = _score_all(hemolytic, weights)
    decoy_scored = _score_all(decoy_rows, weights)

    scorers = [
        "ensemble", "activity", "safety", "synthesis",
        "selectivity_proxy", "hemolysis_risk", "serum_stability",
        "expert_composite", "triage_score", "safe_weighted_ensemble",
    ]

    per_scorer = {}
    for scorer in scorers:
        sel_vals = [s[scorer] for s in selective_scored]
        hemo_vals = [s[scorer] for s in hemolytic_scored]
        decoy_vals = [s[scorer] for s in decoy_scored]

        # For hemolysis_risk, lower is better (selective should be lower)
        # For all others, higher is better
        if scorer == "hemolysis_risk":
            # Invert: 1 - score so higher = better (lower risk)
            sel_vals = [1.0 - v for v in sel_vals]
            hemo_vals = [1.0 - v for v in hemo_vals]
            decoy_vals = [1.0 - v for v in decoy_vals]

        sel_vs_decoy = _pairwise_auroc(sel_vals, decoy_vals, n_bootstrap)
        hemo_vs_decoy = _pairwise_auroc(hemo_vals, decoy_vals, n_bootstrap)
        sel_vs_hemo = _pairwise_auroc(sel_vals, hemo_vals, n_bootstrap)

        # Triage success: all three AUROCs > 0.5
        all_above = all(
            r["auroc"] > 0.5
            for r in [sel_vs_decoy, hemo_vs_decoy, sel_vs_hemo]
        )
        # Strong triage: all three > 0.60
        all_strong = all(
            r["auroc"] > 0.60
            for r in [sel_vs_decoy, hemo_vs_decoy, sel_vs_hemo]
        )

        per_scorer[scorer] = {
            "selective_vs_decoy": sel_vs_decoy,
            "hemolytic_vs_decoy": hemo_vs_decoy,
            "selective_vs_hemolytic": sel_vs_hemo,
            "triages_correctly": all_above,
            "strong_triage": all_strong,
        }

    # Identify the best triage scorer
    best_scorer = max(
        per_scorer,
        key=lambda k: (
            per_scorer[k]["selective_vs_hemolytic"]["auroc"]
            + per_scorer[k]["selective_vs_decoy"]["auroc"]
        ) / 2,
    )

    # Per-sequence detail (top/bottom from each class)
    all_scored = selective_scored + hemolytic_scored + decoy_scored
    for s in all_scored:
        s["triage_class"] = (
            "SELECTIVE" if s.get("hemolysis_class") == "SELECTIVE"
            else "HEMOLYTIC" if s.get("hemolysis_class") == "HEMOLYTIC"
            else "DECOY"
        )

    # Rank by ensemble and show class distribution in top-k
    by_ensemble = sorted(all_scored, key=lambda x: x["ensemble"], reverse=True)
    top_20_classes = [r["triage_class"] for r in by_ensemble[:20]]
    top_20_dist = {
        "SELECTIVE": top_20_classes.count("SELECTIVE"),
        "HEMOLYTIC": top_20_classes.count("HEMOLYTIC"),
        "DECOY": top_20_classes.count("DECOY"),
    }

    by_triage = sorted(all_scored, key=lambda x: x["triage_score"], reverse=True)
    top_20_triage_classes = [r["triage_class"] for r in by_triage[:20]]
    top_20_triage_dist = {
        "SELECTIVE": top_20_triage_classes.count("SELECTIVE"),
        "HEMOLYTIC": top_20_triage_classes.count("HEMOLYTIC"),
        "DECOY": top_20_triage_classes.count("DECOY"),
    }

    by_expert = sorted(all_scored, key=lambda x: x["expert_composite"], reverse=True)
    top_20_expert_classes = [r["triage_class"] for r in by_expert[:20]]
    top_20_expert_dist = {
        "SELECTIVE": top_20_expert_classes.count("SELECTIVE"),
        "HEMOLYTIC": top_20_expert_classes.count("HEMOLYTIC"),
        "DECOY": top_20_expert_classes.count("DECOY"),
    }

    return {
        "benchmark": "multi_class_triage",
        "n_selective": len(selective_scored),
        "n_hemolytic": len(hemolytic_scored),
        "n_decoy": len(decoy_scored),
        "n_total": len(all_scored),
        "per_scorer": per_scorer,
        "best_scorer": best_scorer,
        "top_20_by_ensemble": top_20_dist,
        "top_20_by_triage_score": top_20_triage_dist,
        "top_20_by_expert_composite": top_20_expert_dist,
        "known_blind_spots": [
            "The ensemble ranks hemolytic AMPs above selective AMPs "
            "(anti-selective bias) because hemolytic AMPs have stronger "
            "amphipathic helices, higher hydrophobic moment, and higher charge "
            "— exactly the features the activity scorer rewards.",
            "The safety scorer cannot distinguish hemolytic from selective AMPs "
            "(detection AUROC ~0.51 on expanded benchmark).",
            "The hemolysis_risk scorer has only weak directional signal "
            "(detection AUROC ~0.57, CI includes 0.5 on expanded benchmark).",
            "The triage_score (activity * (1 - hemolysis_risk)) is a simple "
            "composite that may not outperform the ensemble on selective_vs_decoy "
            "because hemolysis_risk is not a significant detector.",
            "The expert_composite is now included in this benchmark because it is "
            "available as a ranking mode. It must earn selection authority on the "
            "same mixed-panel task as simpler scorers.",
        ],
        "disclaimer": (
            "These are computational benchmark results on literature-curated "
            "AMP sequences and random decoy peptides. They do not prove "
            "biological activity, safety, or hemolysis. They measure whether "
            "the pipeline's scorers can triage a mixed panel correctly. "
            "Wet-lab validation remains mandatory for all candidates."
        ),
    }


def _scramble_sequence(seq: str, seed: int = 42) -> str:
    """Scramble a sequence while preserving amino acid composition.

    Uses a deterministic RNG seed so results are reproducible.
    Returns a permutation of the input sequence's residues.
    If the sequence is too short to scramble meaningfully (< 4 residues),
    returns the original sequence.
    """
    import random as _random
    if len(seq) < 4:
        return seq
    rng = _random.Random(seed)
    chars = list(seq)
    rng.shuffle(chars)
    result = "".join(chars)
    # If the scramble accidentally equals the original (rare for short seqs),
    # try again with a different seed
    if result == seq:
        rng2 = _random.Random(seed + 1)
        rng2.shuffle(chars)
        result = "".join(chars)
    return result


def _generate_scrambled_decoys(
    selective_rows: list[dict[str, Any]],
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Create composition-matched decoys by scrambling each selective AMP.

    Each decoy has the exact same amino acid composition as its parent
    selective AMP, but with a random permutation of residue order. This
    destroys amphipathic helical phase, hydrophobic moment, and charge
    distribution patterns while preserving all composition-based features
    (charge, hydrophobicity, aromatic content, length).

    The resulting triage benchmark tests whether the pipeline has any
    ORDER-DEPENDENT signal: can it distinguish real selective AMPs from
    their composition-matched scrambled versions?

    For most composition-heavy scorers (activity, ensemble, safety), the
    answer is expected to be NO — they will collapse to ~0.5 AUROC on
    selective vs scrambled decoy. This is the honest finding that the
    standard triage benchmark masks by using random protein-like decoys.
    """
    decoys = []
    for i, row in enumerate(selective_rows):
        parent_seq = row["sequence"]
        scrambled = _scramble_sequence(parent_seq, seed=seed + i)
        decoys.append({
            "id": f"SCR-{row['id']}",
            "sequence": scrambled,
            "family": f"scrambled_{row.get('family', 'amp')}",
            "source": f"composition_matched_seed{seed + i}",
            "parent_id": row["id"],
            "parent_sequence": parent_seq,
        })
    return decoys


def run_strict_triage_benchmark(
    hemolysis_csv: str | Path,
    seed: int = 42,
    n_bootstrap: int = 2000,
) -> dict[str, Any]:
    """Run the strict triage benchmark with composition-matched decoys.

    This benchmark replaces the random background decoys from
    run_triage_benchmark with composition-matched scrambled versions of
    the selective AMPs. It tests whether the pipeline's scorers have any
    order-dependent triage signal — beyond what raw composition provides.

    The standard triage benchmark uses random background peptides that are
    trivially distinguishable from AMPs (composition is protein-like, not
    AMP-like). This inflates selective_vs_decoy and hemolytic_vs_decoy
    AUROCs, making scorers appear to triage well when they are really only
    solving the easy "AMP vs random" problem.

    The strict triage benchmark reveals:
      - Which scorers have genuine order-dependent signal (hydrophobic
        moment, amphipathic phase, charge distribution)
      - Which scorers are purely composition-driven and collapse when
        composition is controlled for
      - Whether the selective_vs_hemolytic signal is composition-driven
        (should be similar in strict and standard) or order-driven

    Expected honest findings:
      - activity, ensemble: selective_vs_decoy collapses toward 0.5 because
        they are composition-based scorers
      - hydrophobic_moment-driven components: some signal may remain
      - selectivity_proxy: may retain weak signal because it uses GRAVY
        (a composition metric) but also charge distribution
      - selective_vs_hemolytic should be SIMILAR to standard triage because
        both selective and hemolytic AMPs are real sequences; only the
        decoy class changes

    All results are computational. No biological activity is implied.
    """
    config = load_config("configs/pipeline.yaml")
    weights = config["weights"]

    hemo_rows = _load_hemolysis_reference(hemolysis_csv)

    selective = [r for r in hemo_rows if r["hemolysis_class"] == "SELECTIVE"]
    hemolytic = [r for r in hemo_rows if r["hemolysis_class"] == "HEMOLYTIC"]

    # Generate composition-matched decoys from selective AMPs
    scrambled_decoys = _generate_scrambled_decoys(selective, seed=seed)
    decoy_rows = scrambled_decoys

    selective_scored = _score_all(selective, weights)
    hemolytic_scored = _score_all(hemolytic, weights)
    decoy_scored = _score_all(decoy_rows, weights)

    scorers = [
        "ensemble", "activity", "safety", "synthesis",
        "selectivity_proxy", "hemolysis_risk", "serum_stability",
        "expert_composite", "triage_score", "safe_weighted_ensemble",
    ]

    per_scorer = {}
    for scorer in scorers:
        sel_vals = [s[scorer] for s in selective_scored]
        hemo_vals = [s[scorer] for s in hemolytic_scored]
        decoy_vals = [s[scorer] for s in decoy_scored]

        if scorer == "hemolysis_risk":
            sel_vals = [1.0 - v for v in sel_vals]
            hemo_vals = [1.0 - v for v in hemo_vals]
            decoy_vals = [1.0 - v for v in decoy_vals]

        sel_vs_decoy = _pairwise_auroc(sel_vals, decoy_vals, n_bootstrap)
        hemo_vs_decoy = _pairwise_auroc(hemo_vals, decoy_vals, n_bootstrap)
        sel_vs_hemo = _pairwise_auroc(sel_vals, hemo_vals, n_bootstrap)

        all_above = all(
            r["auroc"] > 0.5
            for r in [sel_vs_decoy, hemo_vs_decoy, sel_vs_hemo]
        )
        all_strong = all(
            r["auroc"] > 0.60
            for r in [sel_vs_decoy, hemo_vs_decoy, sel_vs_hemo]
        )

        per_scorer[scorer] = {
            "selective_vs_decoy": sel_vs_decoy,
            "hemolytic_vs_decoy": hemo_vs_decoy,
            "selective_vs_hemolytic": sel_vs_hemo,
            "triages_correctly": all_above,
            "strong_triage": all_strong,
        }

    best_scorer = max(
        per_scorer,
        key=lambda k: (
            per_scorer[k]["selective_vs_hemolytic"]["auroc"]
            + per_scorer[k]["selective_vs_decoy"]["auroc"]
        ) / 2,
    )

    # Class distribution in top-k
    all_scored = selective_scored + hemolytic_scored + decoy_scored
    for s in all_scored:
        s["triage_class"] = (
            "SELECTIVE" if s.get("hemolysis_class") == "SELECTIVE"
            else "HEMOLYTIC" if s.get("hemolysis_class") == "HEMOLYTIC"
            else "DECOY"
        )

    by_ensemble = sorted(all_scored, key=lambda x: x["ensemble"], reverse=True)
    top_20_classes = [r["triage_class"] for r in by_ensemble[:20]]
    top_20_dist = {
        "SELECTIVE": top_20_classes.count("SELECTIVE"),
        "HEMOLYTIC": top_20_classes.count("HEMOLYTIC"),
        "DECOY": top_20_classes.count("DECOY"),
    }

    by_triage = sorted(all_scored, key=lambda x: x["triage_score"], reverse=True)
    top_20_triage_classes = [r["triage_class"] for r in by_triage[:20]]
    top_20_triage_dist = {
        "SELECTIVE": top_20_triage_classes.count("SELECTIVE"),
        "HEMOLYTIC": top_20_triage_classes.count("HEMOLYTIC"),
        "DECOY": top_20_triage_classes.count("DECOY"),
    }

    by_expert = sorted(all_scored, key=lambda x: x["expert_composite"], reverse=True)
    top_20_expert_classes = [r["triage_class"] for r in by_expert[:20]]
    top_20_expert_dist = {
        "SELECTIVE": top_20_expert_classes.count("SELECTIVE"),
        "HEMOLYTIC": top_20_expert_classes.count("HEMOLYTIC"),
        "DECOY": top_20_expert_classes.count("DECOY"),
    }

    return {
        "benchmark": "strict_multi_class_triage",
        "decoy_type": "composition_matched_scrambled",
        "decoy_source": "scrambled_selective_amps",
        "decoy_seed": seed,
        "n_selective": len(selective_scored),
        "n_hemolytic": len(hemolytic_scored),
        "n_decoy": len(decoy_scored),
        "n_total": len(all_scored),
        "per_scorer": per_scorer,
        "best_scorer": best_scorer,
        "top_20_by_ensemble": top_20_dist,
        "top_20_by_triage_score": top_20_triage_dist,
        "top_20_by_expert_composite": top_20_expert_dist,
        "known_blind_spots": [
            "Composition-matched decoys control for amino acid composition, "
            "so only order-dependent features (hydrophobic moment, amphipathic "
            "phase, charge distribution) can distinguish selective AMPs from "
            "their scrambled versions.",
            "Scorers that are purely composition-driven (charge density, GRAVY, "
            "hydrophobic fraction) will collapse to ~0.5 AUROC on "
            "selective_vs_decoy because the scrambled decoy has identical "
            "composition to the parent selective AMP.",
            "The selective_vs_hemolytic AUROC should be similar to the standard "
            "triage benchmark because both classes are real AMP sequences; only "
            "the decoy class changes.",
            "If NO scorer achieves selective_vs_decoy > 0.55, the pipeline has "
            "no order-dependent triage signal beyond composition, which means "
            "the current selection is entirely composition-driven and cannot "
            "distinguish a real AMP from a scrambled version of itself.",
        ],
        "disclaimer": (
            "These are computational benchmark results on literature-curated "
            "AMP sequences and their composition-matched scrambled versions. "
            "They do not prove biological activity, safety, or hemolysis. "
            "They measure whether the pipeline's scorers have order-dependent "
            "triage signal beyond composition. Wet-lab validation remains "
            "mandatory for all candidates."
        ),
    }

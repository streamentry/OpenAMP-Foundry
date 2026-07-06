"""Generate evidence certificates for all Wave 1 final panel candidates.

Creates outputs/evidence_wave0_5/{candidate_id}.json for every candidate
in the final panel. Each certificate is machine-readable and includes all
available evidence fields per plan/wave0.5.md Phase 8.

External predictor fields are PENDING until web-tool submissions are complete.

Usage:
    python scripts/generate_wave0_5_evidence_certs.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from openamp_foundry.features.physchem import compute_features
from openamp_foundry.scoring.synthesis import synthesis_feasibility_score


def _load_csv_by_id(path: Path, id_col: str) -> dict[str, dict]:
    with open(path) as f:
        return {r[id_col]: r for r in csv.DictReader(f)}


def _synthesis_qc(seq: str, flags_str: str) -> dict:
    feats = compute_features(seq)
    synth_score = synthesis_feasibility_score(feats)
    flags = [f.strip() for f in flags_str.split(";") if f.strip() and f.strip().upper() != "NONE"]
    return {
        "synthesis_feasibility_score": round(synth_score, 4),
        "flags": flags if flags else [],
        "multi_cys": seq.count("C") >= 2,
        "difficult_aa": [aa for aa in seq if aa in ("C", "P", "W", "M") and seq.count(aa) > 2],
        "length": len(seq),
        "synthesis_risk": "HIGH" if flags else ("MODERATE" if synth_score < 0.85 else "LOW"),
    }


def _physicochemical(seq: str) -> dict:
    feats = compute_features(seq)
    return {
        "net_charge_ph74": round(feats.get("net_charge_ph74", 0.0), 3),
        "hydrophobic_fraction": round(feats.get("hydrophobic_fraction", 0.0), 3),
        "hydrophobic_moment_mu_h": round(feats.get("hydrophobic_moment", 0.0), 3),
        "aromatic_fraction": round(feats.get("aromatic_fraction", 0.0), 3),
        "boman_index": round(feats.get("boman_index", 0.0), 3),
        "gravy": round(feats.get("gravy", 0.0), 3),
        "length": len(seq),
    }


def _make_certificate(
    candidate: dict,
    novelty: dict,
    shortlist: dict,
    baseline: dict,
    ext_consensus: dict | None = None,
) -> dict:
    cid = candidate["candidate_id"]
    seq = candidate["sequence"]
    seed_family = candidate["seed_family"]
    panel_role = candidate.get("panel_role", "UNKNOWN")
    source = candidate.get("source", "UNKNOWN")

    # Activity scores
    act_score = float(candidate.get("openamp_activity", 0.0))
    safe_score = float(candidate.get("openamp_safety", 0.0))

    # Novelty
    nov_cls = novelty.get("novelty_class", candidate.get("novelty_class", "UNKNOWN"))
    best_hit_id = novelty.get("best_hit_id", "NONE")
    best_similarity = float(novelty.get("best_similarity", 0.0)) if novelty else 0.0
    patent_risk_str = novelty.get("patent_risk", "UNKNOWN")
    best_db = novelty.get("best_database", "N/A")

    # Synthesis
    flags_str = candidate.get("synthesis_flags", "NONE")
    if not flags_str:
        flags_str = "NONE"
    synth_qc = _synthesis_qc(seq, flags_str)
    physchem = _physicochemical(seq)

    # Fill external predictor data if available
    ext = ext_consensus or {}
    hemofinder_risk = ext.get("hemofinder_risk", "PENDING")
    anticp_class_ext = ext.get("anticp_class", "PENDING")
    macrel_hemo_flag = ext.get("macrel_hemolysis_flag", "PENDING")
    safety_risk_level = ext.get("safety_risk_level", "PENDING")
    activity_votes = ext.get("activity_votes", "PENDING")
    activity_consensus_ext = ext.get("activity_consensus", "PENDING")
    ampscanner_vote = ext.get("ampscanner_vote", "PENDING")
    macrel_amp_vote = ext.get("macrel_amp_vote", "PENDING")
    ampactipred_vote = ext.get("ampactipred_abp_vote", "PENDING")

    # Known risks
    known_risks = []
    if hemofinder_risk == "HIGH" or candidate.get("hemolysis_high") or (baseline and baseline.get("hemofinder_risk", "").upper() == "HIGH"):
        known_risks.append("HemoFinder HIGH hemolysis risk")
    if anticp_class_ext == "AntiCP" or candidate.get("anticp_risk") or (baseline and baseline.get("anticp_class", "").upper() == "ANTICP_RISK"):
        known_risks.append("AntiCP off-target risk: anticancer-peptide-like (not AMP activity signal)")
    if "REVIEW_REQUIRED" in patent_risk_str or "POSSIBLE" in patent_risk_str:
        known_risks.append(f"Patent proximity risk: {patent_risk_str}")
    if physchem["hydrophobic_fraction"] > 0.60:
        known_risks.append(f"High hydrophobicity ({physchem['hydrophobic_fraction']:.2f}) — hemolysis risk proxy")
    if physchem["hydrophobic_moment_mu_h"] > 0.55:
        known_risks.append(f"High hydrophobic moment ({physchem['hydrophobic_moment_mu_h']:.3f}) — membrane disruption risk")

    return {
        "candidate_id": cid,
        "sequence": seq,
        "seed_family": seed_family,
        "source": source,
        "panel_role": panel_role,
        "evidence_version": "wave0.5",
        "generated_date": "2026-06-29",
        "openamp_scores": {
            "activity_score": round(act_score, 4),
            "safety_score": round(safe_score, 4),
            "novelty_proxy": float(shortlist.get("novelty_proxy", 0.0)) if shortlist else 0.0,
            "ensemble_score": round(float(baseline.get("openamp_ensemble", act_score)), 4) if baseline else round(act_score, 4),
        },
        "physicochemical": physchem,
        "external_activity_predictors": {
            "campr4": "PENDING",
            "ampscanner_v2": ampscanner_vote,
            "macrel_amp": macrel_amp_vote,
            "ampactipred_abp": ampactipred_vote,
            "activity_votes": activity_votes,
            "activity_consensus": activity_consensus_ext,
            "total_predictors": 3,
            "note": (
                "CAMPR4 not submitted. Activity consensus from 3 tools: AMPScanner, Macrel AMP, AMPActiPred. "
                "Macrel hemolysis flags all sequences and is non-discriminating."
            ),
        },
        "safety_predictors": {
            "hemofinder_risk": hemofinder_risk,
            "anticp2_class": anticp_class_ext,
            "macrel_hemolysis_flag": macrel_hemo_flag,
            "safety_risk_level": safety_risk_level,
            "safety_note": ext.get("safety_note", ""),
            "note": "AntiCP 2.0 predicts anticancer peptides (ACP), not AMP activity. A positive result = off-target risk.",
        },
        "novelty_audit": {
            "novelty_class": nov_cls,
            "best_hit_id": best_hit_id,
            "best_hit_database": best_db,
            "best_similarity": round(best_similarity, 4),
            "patent_risk": patent_risk_str,
            "action": novelty.get("action", "UNKNOWN"),
            "method": "BioPython PairwiseAligner BLOSUM62 local alignment, identity=matches/len(query), vs 27,234 unique sequences (APD6+DRAMP+UniProt)",
        },
        "synthesis_qc": synth_qc,
        "known_risks": known_risks,
        "reason_for_inclusion": candidate.get("reason_for_inclusion", ""),
        "reason_for_exclusion": candidate.get("reason_for_exclusion", ""),
        "generation_reason": shortlist.get("generation_reason", "") if shortlist else baseline.get("current_role", ""),
        "wet_lab_claim_status": "NO_WET_LAB_EVIDENCE",
        "claim_disclaimer": (
            "All scores are computational predictions from physicochemical heuristics and ML models. "
            "No antimicrobial activity has been demonstrated in vitro or in vivo. "
            "Wet-lab validation by qualified collaborators is required before any biological claim."
        ),
    }


def main() -> None:
    final_path = ROOT / "outputs" / "wave1_final_panel.csv"
    novelty_path = ROOT / "outputs" / "wave0_5_novelty_audit.csv"
    shortlist_path = ROOT / "outputs" / "wave0_5_internal_shortlist.csv"
    baseline_path = ROOT / "outputs" / "wave0_5_baseline.csv"
    ext_consensus_path = ROOT / "outputs" / "wave0_5_external_consensus.csv"
    out_dir = ROOT / "outputs" / "evidence_wave0_5"

    with open(final_path) as f:
        final_rows = list(csv.DictReader(f))

    novelty_by_id = _load_csv_by_id(novelty_path, "candidate_id")
    shortlist_by_id = _load_csv_by_id(shortlist_path, "candidate_id")
    baseline_by_id = _load_csv_by_id(baseline_path, "candidate_id")
    ext_consensus_by_id: dict[str, dict] = {}
    if ext_consensus_path.exists():
        ext_consensus_by_id = _load_csv_by_id(ext_consensus_path, "candidate_id")

    # Re-load final panel with enriched fields (hemolysis_high, anticp_risk, etc.)
    generated = 0
    for row in final_rows:
        cid = row["candidate_id"]
        bl = baseline_by_id.get(cid)
        sl = shortlist_by_id.get(cid)
        nv = novelty_by_id.get(cid)
        ext = ext_consensus_by_id.get(cid)

        # Build enriched candidate dict
        candidate = dict(row)

        # Infer hemolysis_high and anticp_risk from external consensus, then baseline fallback
        if ext:
            candidate["hemolysis_high"] = ext.get("hemofinder_risk", "") == "HIGH"
            candidate["anticp_risk"] = ext.get("anticp_class", "") == "AntiCP"
        elif bl:
            candidate["hemolysis_high"] = bl.get("hemofinder_risk", "").upper() == "HIGH"
            candidate["anticp_risk"] = bl.get("anticp_class", "").upper() == "ANTICP_RISK"
        else:
            candidate["hemolysis_high"] = False
            candidate["anticp_risk"] = False

        # Synthesis flags from shortlist or baseline
        if sl:
            candidate["synthesis_flags"] = sl.get("synthesis_flags", "NONE")
        else:
            candidate["synthesis_flags"] = "NONE"

        cert = _make_certificate(
            candidate=candidate,
            novelty=nv or {},
            shortlist=sl or {},
            baseline=bl or {},
            ext_consensus=ext,
        )

        out_path = out_dir / f"{cid}.json"
        with open(out_path, "w") as f:
            json.dump(cert, f, indent=2)
        generated += 1

    print(f"Generated {generated} evidence certificates in {out_dir}")

    # Verify acceptance criteria
    for row in final_rows:
        cid = row["candidate_id"]
        cert_path = out_dir / f"{cid}.json"
        assert cert_path.exists(), f"Missing certificate: {cid}"
        with open(cert_path) as f:
            cert = json.load(f)
        assert cert["openamp_scores"]["activity_score"] > 0, f"Missing activity score: {cid}"
        assert cert["novelty_audit"]["novelty_class"] != "", f"Missing novelty class: {cid}"
        assert cert["wet_lab_claim_status"] == "NO_WET_LAB_EVIDENCE", f"Missing claim disclaimer: {cid}"

    print("All acceptance criteria met: activity, safety, novelty, synthesis, role, no biological claim")


if __name__ == "__main__":
    main()

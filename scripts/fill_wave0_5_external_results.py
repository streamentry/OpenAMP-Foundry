"""Fill wave0_5_external_predict_results.csv and wave0_5_external_consensus.csv
from the uploaded wave05_combined_consensus.csv.

CAMPR4 was not submitted — treated as PENDING (not counted in activity votes).
Activity consensus uses 3 tools: AMPScanner, Macrel AMP, AMPActiPred.
Macrel hemolysis flags every sequence and is non-discriminating — recorded but
not used as a standalone exclusion gate per expert verdict.

Usage:
    python scripts/fill_wave0_5_external_results.py
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    src = ROOT / "outputs" / "wave05_combined_consensus.csv"
    results_out = ROOT / "outputs" / "wave0_5_external_predict_results.csv"
    consensus_out = ROOT / "outputs" / "wave0_5_external_consensus.csv"
    safety_out = ROOT / "outputs" / "wave0_5_safety_consensus.csv"
    shortlist_path = ROOT / "outputs" / "wave0_5_internal_shortlist.csv"

    with open(src) as f:
        src_rows = {r["candidate_id"]: r for r in csv.DictReader(f)}

    with open(shortlist_path) as f:
        shortlist = {r["candidate_id"]: r for r in csv.DictReader(f)}

    # -------------------------------------------------------------------------
    # Fill external predict results
    # -------------------------------------------------------------------------
    results_fieldnames = [
        "candidate_id", "sequence", "seed_family",
        "campr4_vote",           # PENDING — not submitted
        "ampscanner_vote",       # AMP / Non-AMP
        "macrel_amp_vote",       # True/False → AMP/NAMP
        "ampactipred_abp_vote",  # True/False → ABP/non-ABP
        "anticp2_class",         # AntiCP / Non-AntiCP
        "hemofinder_risk",       # LOW / HIGH (hemofinder_pred: 0=LOW, 1=HIGH)
        "macrel_hemolysis_flag", # Hemo / Non-Hemo
        "ampscanner_prob",
        "macrel_amp_prob",
        "anticp_score",
        "macrel_hemo_prob",
    ]

    results_rows = []
    for cid, sl in shortlist.items():
        s = src_rows.get(cid)
        if s:
            row = {
                "candidate_id": cid,
                "sequence": sl["sequence"],
                "seed_family": sl["seed_family"],
                "campr4_vote": "PENDING",
                "ampscanner_vote": "AMP" if s["ampscanner_class"] == "AMP" else "Non-AMP",
                "macrel_amp_vote": "AMP" if s["macrel_amp"] == "True" else "NAMP",
                "ampactipred_abp_vote": "ABP" if s["ampactipred_abp"] == "True" else "non-ABP",
                "anticp2_class": s["anticp_class"],
                "hemofinder_risk": "HIGH" if s["hemofinder_pred"] == "1" else "LOW",
                "macrel_hemolysis_flag": "Hemo" if s["macrel_hemo"] == "Hemo" else "Non-Hemo",
                "ampscanner_prob": s["ampscanner_prob"],
                "macrel_amp_prob": s["macrel_amp_prob"],
                "anticp_score": s["anticp_score"],
                "macrel_hemo_prob": s["macrel_hemo_prob"],
            }
        else:
            row = {
                "candidate_id": cid,
                "sequence": sl["sequence"],
                "seed_family": sl["seed_family"],
                "campr4_vote": "PENDING",
                "ampscanner_vote": "PENDING",
                "macrel_amp_vote": "PENDING",
                "ampactipred_abp_vote": "PENDING",
                "anticp2_class": "PENDING",
                "hemofinder_risk": "PENDING",
                "macrel_hemolysis_flag": "PENDING",
                "ampscanner_prob": "",
                "macrel_amp_prob": "",
                "anticp_score": "",
                "macrel_hemo_prob": "",
            }
        results_rows.append(row)

    with open(results_out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results_fieldnames)
        w.writeheader()
        w.writerows(results_rows)
    print(f"Filled: {results_out}")

    # -------------------------------------------------------------------------
    # Recompute consensus
    # CAMPR4 missing → total_activity_predictors = 3 (AMPScanner + Macrel + AMPActiPred)
    # activity_consensus: STRONG=3, MODERATE=2, WEAK≤1
    # safety_risk_level per verdict:
    #   safety_level from merged CSV is authoritative
    #   MIXED = only Macrel hemo (non-discriminating per verdict) → treat as LOW_RISK for selection
    #   HIGH = AntiCP OR HemoFinder HIGH → caution
    #   VERY_HIGH = both AntiCP AND HemoFinder HIGH → exclude from leads unless very high activity
    # -------------------------------------------------------------------------
    consensus_fieldnames = [
        "candidate_id", "sequence", "seed_family",
        "campr4_vote", "ampscanner_vote", "macrel_amp_vote", "ampactipred_abp_vote",
        "activity_votes", "total_activity_predictors", "activity_consensus",
        "anticp_class", "hemofinder_risk", "macrel_hemolysis_flag",
        "safety_risk_level", "safety_note",
        "openamp_activity_score", "openamp_safety_score", "shortlist_role",
    ]

    consensus_rows = []
    for r in results_rows:
        cid = r["candidate_id"]
        s = src_rows.get(cid)
        sl = shortlist.get(cid, {})
        activity_votes = int(s["activity_votes"]) if s else 0
        # Activity consensus (3 predictors, CAMPR4 excluded)
        if activity_votes >= 3:
            act_consensus = "STRONG_ACTIVITY"
        elif activity_votes == 2:
            act_consensus = "MODERATE_ACTIVITY"
        else:
            act_consensus = "WEAK_ACTIVITY"

        # Safety risk level — use merged CSV safety_level as ground truth
        # Reclassify MIXED (macrel-only) as LOW_EFFECTIVE since Macrel hemo is non-discriminating
        raw_safety = s["safety_level"] if s else "UNKNOWN"
        if raw_safety == "MIXED":
            safety_risk = "LOW_EFFECTIVE"  # only Macrel hemo flagged, which is non-discriminating
            safety_note = "Only Macrel hemolysis flagged (non-discriminating; flags all sequences)"
        elif raw_safety == "HIGH":
            safety_risk = "MODERATE_RISK"
            safety_note = "AntiCP positive OR HemoFinder HIGH (one signal)"
        elif raw_safety == "VERY_HIGH":
            safety_risk = "HIGH_RISK"
            safety_note = "AntiCP positive AND HemoFinder HIGH (two signals)"
        else:
            safety_risk = "UNKNOWN"
            safety_note = ""

        consensus_rows.append({
            "candidate_id": cid,
            "sequence": r["sequence"],
            "seed_family": r["seed_family"],
            "campr4_vote": "PENDING",
            "ampscanner_vote": r["ampscanner_vote"],
            "macrel_amp_vote": r["macrel_amp_vote"],
            "ampactipred_abp_vote": r["ampactipred_abp_vote"],
            "activity_votes": str(activity_votes),
            "total_activity_predictors": "3",
            "activity_consensus": act_consensus,
            "anticp_class": r["anticp2_class"],
            "hemofinder_risk": r["hemofinder_risk"],
            "macrel_hemolysis_flag": r["macrel_hemolysis_flag"],
            "safety_risk_level": safety_risk,
            "safety_note": safety_note,
            "openamp_activity_score": sl.get("initial_activity_score", ""),
            "openamp_safety_score": sl.get("initial_safety_score", ""),
            "shortlist_role": sl.get("shortlist_role", ""),
        })

    with open(consensus_out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=consensus_fieldnames)
        w.writeheader()
        w.writerows(consensus_rows)
    print(f"Filled: {consensus_out}")

    # -------------------------------------------------------------------------
    # Safety consensus
    # -------------------------------------------------------------------------
    safety_fieldnames = [
        "candidate_id", "sequence", "seed_family",
        "hemofinder_risk", "anticp_class", "anticp_score",
        "macrel_hemolysis_flag", "macrel_hemo_prob",
        "safety_risk_level", "safety_note",
        "internal_safety_estimate",
    ]

    safety_rows = []
    for r in consensus_rows:
        cid = r["candidate_id"]
        s = src_rows.get(cid, {})
        sl = shortlist.get(cid, {})
        internal_safe = float(sl.get("initial_safety_score", 0))
        if internal_safe >= 0.90:
            internal_est = "LIKELY_LOW_RISK"
        elif internal_safe >= 0.75:
            internal_est = "UNCERTAIN"
        else:
            internal_est = "LIKELY_HIGH_RISK"
        safety_rows.append({
            "candidate_id": cid,
            "sequence": r["sequence"],
            "seed_family": r["seed_family"],
            "hemofinder_risk": r["hemofinder_risk"],
            "anticp_class": r["anticp_class"],
            "anticp_score": s.get("anticp_score", ""),
            "macrel_hemolysis_flag": r["macrel_hemolysis_flag"],
            "macrel_hemo_prob": s.get("macrel_hemo_prob", ""),
            "safety_risk_level": r["safety_risk_level"],
            "safety_note": r["safety_note"],
            "internal_safety_estimate": internal_est,
        })

    with open(safety_out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=safety_fieldnames)
        w.writeheader()
        w.writerows(safety_rows)
    print(f"Filled: {safety_out}")

    # Summary
    from collections import Counter
    act_counts = Counter(r["activity_consensus"] for r in consensus_rows)
    safe_counts = Counter(r["safety_risk_level"] for r in consensus_rows)
    anticp_counts = Counter(r["anticp_class"] for r in consensus_rows)
    hemo_counts = Counter(r["hemofinder_risk"] for r in consensus_rows)
    print(f"\nActivity consensus: {dict(act_counts)}")
    print(f"Safety risk level: {dict(safe_counts)}")
    print(f"AntiCP class: {dict(anticp_counts)}")
    print(f"HemoFinder risk: {dict(hemo_counts)}")


if __name__ == "__main__":
    main()

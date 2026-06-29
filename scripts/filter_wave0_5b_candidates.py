"""Wave 0.5b shortlist filter.

Selects Wave 0.5b candidates from the raw pool for external predictor submission.

Design-based safety expectations (no aromatics, helix-broken):
    - AntiCP expected < 0.50 (no W/Y/F that trigger ACP-like predictions)
    - HemoFinder expected LOW for most (no long amphipathic helix)

Tier criteria (more relaxed activity threshold than Wave 0.5a,
because the safety/activity trade-off is explicit for this wave):
    Tier 1 — Both thresholds (primary leads):
        activity ≥ 0.70 AND safety ≥ 0.75
    Tier 2 — Safety-optimized leads (near activity threshold):
        activity ≥ 0.60 AND safety ≥ 0.90
    Tier 3 — High activity, moderate safety (for annotation, not primary):
        activity ≥ 0.70 AND safety ≥ 0.45

Exclusion:
    - Ultrashort peptides (SEED-022 family) with internal safety < 0.35
      → despite no aromatics, their hemolytic amphipathic index is high

Usage:
    python scripts/filter_wave0_5b_candidates.py
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TIER1_ACTIVITY = 0.70
TIER1_SAFETY = 0.75

TIER2_ACTIVITY = 0.60
TIER2_SAFETY = 0.90

TIER3_ACTIVITY = 0.70
TIER3_SAFETY = 0.45

EXCLUDE_SAFETY_BELOW = 0.35  # SEED-022 range — too hemolytic


def _tier(act: float, safe: float) -> str:
    if safe < EXCLUDE_SAFETY_BELOW:
        return "EXCLUDE"
    if act >= TIER1_ACTIVITY and safe >= TIER1_SAFETY:
        return "TIER1"
    if act >= TIER2_ACTIVITY and safe >= TIER2_SAFETY:
        return "TIER2"
    if act >= TIER3_ACTIVITY and safe >= TIER3_SAFETY:
        return "TIER3"
    return "EXCLUDE"


def main() -> None:
    raw_path = ROOT / "outputs" / "wave0_5b_raw_candidates.csv"
    out_path = ROOT / "outputs" / "wave0_5b_shortlist.csv"
    fasta_path = ROOT / "outputs" / "wave0_5b_shortlist.fasta"

    with open(raw_path) as f:
        rows = list(csv.DictReader(f))

    shortlist = []
    excluded = []

    for r in rows:
        act = float(r["initial_activity_score"])
        safe = float(r["initial_safety_score"])
        t = _tier(act, safe)
        r["shortlist_tier"] = t
        if t != "EXCLUDE":
            r["shortlist_role"] = "PASS"
            r["shortlist_exclusion_reason"] = ""
            shortlist.append(r)
        else:
            r["shortlist_role"] = "FAIL"
            if safe < EXCLUDE_SAFETY_BELOW:
                r["shortlist_exclusion_reason"] = (
                    f"safety {safe:.3f} < {EXCLUDE_SAFETY_BELOW}: hemolytic amphipathic character despite no aromatics"
                )
            else:
                r["shortlist_exclusion_reason"] = (
                    f"activity {act:.3f} and safety {safe:.3f} below all tiers"
                )
            excluded.append(r)

    # Sort: TIER1 first, then TIER2, then TIER3, by act+safe desc within tier
    tier_order = {"TIER1": 0, "TIER2": 1, "TIER3": 2}
    shortlist.sort(
        key=lambda r: (
            tier_order.get(r["shortlist_tier"], 9),
            -(float(r["initial_activity_score"]) + float(r["initial_safety_score"])),
        )
    )

    out_fieldnames = [
        "candidate_id", "seed_family", "sequence", "length", "source_type",
        "initial_activity_score", "initial_safety_score", "novelty_proxy",
        "synthesis_flags", "shortlist_tier", "shortlist_role",
        "shortlist_exclusion_reason", "generation_reason",
    ]

    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(shortlist)

    with open(fasta_path, "w") as f:
        for r in shortlist:
            f.write(f">{r['candidate_id']} | {r['seed_family']} | tier={r['shortlist_tier']}\n")
            f.write(f"{r['sequence']}\n")

    from collections import Counter
    tier_counts = Counter(r["shortlist_tier"] for r in shortlist)
    fam_counts = Counter(r["seed_family"] for r in shortlist)

    print(f"Wave 0.5b shortlist: {len(shortlist)} candidates")
    print(f"Excluded: {len(excluded)} candidates")
    print(f"\nTier breakdown: {dict(tier_counts)}")
    print(f"Family breakdown: {dict(fam_counts)}")
    print(f"\nShortlist CSV: {out_path}")
    print(f"FASTA: {fasta_path}")
    print()
    print("Design safety expectations (all have no aromatic residues W/Y/F):")
    print("  - AntiCP 2.0 score expected < 0.50")
    print("  - HemoFinder risk expected LOW for Tier 1 and Tier 2")
    print("  - Submit to external predictors to confirm")

    print("\nTop 10 candidates:")
    for r in shortlist[:10]:
        act = float(r["initial_activity_score"])
        safe = float(r["initial_safety_score"])
        print(
            f"  {r['candidate_id']:22} {r['seed_family']:8} "
            f"{r['sequence']:16} act={act:.3f} safe={safe:.3f} [{r['shortlist_tier']}]"
        )


if __name__ == "__main__":
    main()

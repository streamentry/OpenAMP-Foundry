"""Wave 0.5 internal candidate filter.

Reads outputs/wave0_5_raw_candidates.csv and applies internal gates to produce
outputs/wave0_5_internal_shortlist.csv (target: 30–60 candidates).

Thresholds are committed constants. They are NOT tuned after seeing results.
See plan/wave0.5.md Phase 4 for threshold rationale.

Gate thresholds:
    activity_score  >= 0.70   (primary gate)
    safety_score    >= 0.75   (hemolysis/off-target proxy)
    synthesis_score >= 0.75   (synthesis feasibility)
    novelty_proxy   >= 0.50   (not near-copy of Wave 0 panel)
    max_similarity_to_wave0  < 0.80  (redundancy gate)

High-upside exception:
    activity_score >= 0.80 AND safety_score >= 0.65
    Requires explicit HIGH_UPSIDE_RISKY label.

Additional portfolio gate:
    Max 6 variants per family in the shortlist.

Usage:
    python scripts/filter_wave0_5_candidates.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from openamp_foundry.scoring.synthesis import synthesis_feasibility_score
from openamp_foundry.features.physchem import compute_features

# ---------------------------------------------------------------------------
# Thresholds — fixed before filtering
# ---------------------------------------------------------------------------
ACTIVITY_THRESHOLD = 0.70
SAFETY_THRESHOLD = 0.75
SYNTHESIS_THRESHOLD = 0.75
NOVELTY_PROXY_THRESHOLD = 0.50
MAX_SIMILARITY_TO_PANEL = 0.80
MAX_FAMILY_VARIANTS = 6

# High-upside exception: high activity but lower safety is allowed if labeled
HIGH_UPSIDE_ACTIVITY = 0.80
HIGH_UPSIDE_SAFETY = 0.65

VALID_AA = set("ACDEFGHIKLMNPQRSTVWY")


def _is_valid_seq(seq: str) -> bool:
    return all(aa in VALID_AA for aa in seq) and 8 <= len(seq) <= 35


def _determine_role(row: dict) -> tuple[str, str]:
    """Return (role, exclusion_reason). role is empty string if included."""
    seq = row["sequence"]
    act = float(row["initial_activity_score"])
    safe = float(row["initial_safety_score"])
    nov = float(row["novelty_proxy"])
    best_sim = 1.0 - nov  # wave0 similarity (novelty_proxy = 1 - best_sim)

    if not _is_valid_seq(seq):
        return "DROP", "invalid_amino_acid_characters"

    if best_sim >= MAX_SIMILARITY_TO_PANEL:
        return "DROP", f"too_similar_to_wave0_panel (best_sim={best_sim:.3f} ≥ {MAX_SIMILARITY_TO_PANEL})"

    if nov < NOVELTY_PROXY_THRESHOLD:
        return "DROP", f"novelty_proxy_too_low ({nov:.3f} < {NOVELTY_PROXY_THRESHOLD})"

    # Synthesis gate (recompute to be safe)
    feats = compute_features(seq)
    synth = synthesis_feasibility_score(feats)
    if synth < SYNTHESIS_THRESHOLD:
        return "DROP", f"synthesis_score_too_low ({synth:.3f} < {SYNTHESIS_THRESHOLD})"

    # Primary gate
    if act >= ACTIVITY_THRESHOLD and safe >= SAFETY_THRESHOLD:
        return "PASS", ""

    # High-upside exception
    if act >= HIGH_UPSIDE_ACTIVITY and safe >= HIGH_UPSIDE_SAFETY:
        return "PASS_HIGH_UPSIDE", ""

    # Fail
    reasons = []
    if act < ACTIVITY_THRESHOLD:
        reasons.append(f"activity_too_low ({act:.3f} < {ACTIVITY_THRESHOLD})")
    if safe < SAFETY_THRESHOLD:
        reasons.append(f"safety_too_low ({safe:.3f} < {SAFETY_THRESHOLD})")
    return "DROP", "; ".join(reasons)


def main() -> None:
    in_path = ROOT / "outputs" / "wave0_5_raw_candidates.csv"
    shortlist_path = ROOT / "outputs" / "wave0_5_internal_shortlist.csv"
    excluded_path = ROOT / "outputs" / "wave0_5_internal_excluded.csv"

    with open(in_path) as fh:
        reader = csv.DictReader(fh)
        raw = list(reader)

    shortlist_fieldnames = [
        "candidate_id", "seed_family", "sequence", "length", "source_type",
        "initial_activity_score", "initial_safety_score", "novelty_proxy",
        "synthesis_flags", "shortlist_role", "shortlist_exclusion_reason",
        "generation_reason",
    ]
    excluded_fieldnames = shortlist_fieldnames[:]

    shortlist_rows: list[dict] = []
    excluded_rows: list[dict] = []
    family_shortlist_count: dict[str, int] = {}

    for row in raw:
        role, excl_reason = _determine_role(row)
        fam = row["seed_family"]

        if role in ("PASS", "PASS_HIGH_UPSIDE"):
            # Portfolio cap: max 6 per family
            count = family_shortlist_count.get(fam, 0)
            if count >= MAX_FAMILY_VARIANTS:
                role = "DROP"
                excl_reason = f"family_cap_exceeded ({fam} already has {count} shortlisted)"
            else:
                family_shortlist_count[fam] = count + 1

        out_row = {
            "candidate_id": row["candidate_id"],
            "seed_family": fam,
            "sequence": row["sequence"],
            "length": row["length"],
            "source_type": row["source_type"],
            "initial_activity_score": row["initial_activity_score"],
            "initial_safety_score": row["initial_safety_score"],
            "novelty_proxy": row["novelty_proxy"],
            "synthesis_flags": row["synthesis_flags"],
            "shortlist_role": role,
            "shortlist_exclusion_reason": excl_reason,
            "generation_reason": row["generation_reason"],
        }

        if role in ("PASS", "PASS_HIGH_UPSIDE"):
            shortlist_rows.append(out_row)
        else:
            excluded_rows.append(out_row)

    with open(shortlist_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=shortlist_fieldnames)
        writer.writeheader()
        writer.writerows(shortlist_rows)

    with open(excluded_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=excluded_fieldnames)
        writer.writeheader()
        writer.writerows(excluded_rows)

    total = len(shortlist_rows)
    n_families = len(family_shortlist_count)
    n_high_upside = sum(1 for r in shortlist_rows if r["shortlist_role"] == "PASS_HIGH_UPSIDE")
    n_excluded = len(excluded_rows)

    print(f"Shortlist: {total} candidates across {n_families} families")
    print(f"  Standard PASS:   {total - n_high_upside}")
    print(f"  HIGH_UPSIDE:     {n_high_upside}")
    print(f"  Excluded:        {n_excluded}")
    print()
    for fam, n in sorted(family_shortlist_count.items()):
        print(f"  {fam}: {n} shortlisted")
    print(f"\nShortlist output: {shortlist_path}")
    print(f"Excluded output:  {excluded_path}")

    # Acceptance criteria checks
    assert total >= 30, f"FAIL: shortlist has {total} candidates (need ≥30)"
    assert total <= 60, f"FAIL: shortlist has {total} candidates (need ≤60)"
    assert n_families >= 8, f"FAIL: only {n_families} families (need ≥8)"
    assert all(bool(r["shortlist_exclusion_reason"])
               for r in excluded_rows if r["shortlist_role"] == "DROP"), \
        "FAIL: excluded candidate missing reason"
    print("All acceptance criteria MET.")


if __name__ == "__main__":
    main()

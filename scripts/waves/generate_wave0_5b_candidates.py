"""Wave 0.5b candidate generation.

Design goal (per external verdict):
    "Do not optimize for more AMP signal. You already have too much AMP signal.
    Optimize for: activity still positive but safety less scary."

Key structural principle from SEED-019_VAR_004 (RVRIRLVKRLLK):
    - Arg-Val/Ile alternating pattern breaks pure amphipathic helicity
    - No aromatic residues (no Trp, Tyr, Phe) → avoids AntiCP trigger
    - Scattered charge (Arg/Lys every 3rd-4th position, not clustered)
    - Moderate length 9–13 residues (below long amphipathic helix threshold)
    - HemoFinder LOW despite being cationic

Five new seed families:
    SEED-020: Extended Arg-Ile/Val alternating (modeled on SEED-019)
    SEED-021: Gly-rich interspersed Arg/Lys with Ile/Leu pairs
    SEED-022: Short 8–10mer Arg-dominant no-aromatic (ultrashort AMPs)
    SEED-023: Lys-Leu-Ala interspersed (KLA-type without full helix)
    SEED-024: Pro-kink breaker (single Pro prevents full helix formation)

Target: 30–40 candidates, AntiCP < 0.50 by design (no aromatic, broken helix)

Usage:
    python scripts/generate_wave0_5b_candidates.py
"""

from __future__ import annotations

import csv
import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from openamp_foundry.features.physchem import compute_features  # noqa: E402
from openamp_foundry.scoring.safety import safety_score as _safety_score  # noqa: E402
from openamp_foundry.scoring.activity import activity_likeness_score  # noqa: E402
from openamp_foundry.scoring.synthesis import synthesis_feasibility_score  # noqa: E402


# ---------------------------------------------------------------------------
# Seed families — design rationale
# ---------------------------------------------------------------------------
SEEDS: dict[str, dict] = {
    "SEED-020": {
        "template": "RVRIRVLKRLLK",  # extended SEED-019 with Leu at 7
        "description": "Arg-Ile/Val/Leu alternating; extended SEED-019 pattern",
        "design_principle": "No aromatics; alternating cationic/hydrophobic; broken helix",
        "source_type": "DESIGN_INSPIRED",
        "reference": "Extension of SEED-019_VAR_004 structural logic",
    },
    "SEED-021": {
        "template": "GKRKILIKRLK",
        "description": "Gly-Lys-Arg interspersed with Ile/Leu (Gly as helix breaker)",
        "design_principle": "Gly interrupts amphipathic helix; Ile/Leu hydrophobic core",
        "source_type": "DESIGN_INSPIRED",
        "reference": "Gly-interrupted cationic peptide design (no helix = lower AntiCP risk)",
    },
    "SEED-022": {
        "template": "RLLKRLLK",
        "description": "Ultrashort 8-10mer Arg-Leu-Leu-Lys repeat",
        "design_principle": "Short length limits hemolytic amphipathic helix; Leu not aromatic",
        "source_type": "DESIGN_INSPIRED",
        "reference": "Ultrashort AMP design below 12-mer hemolytic threshold",
    },
    "SEED-023": {
        "template": "KLALKLALK",
        "description": "KLA-type Lys-Leu-Ala repeat (no aromatics, lower hydrophobicity)",
        "design_principle": "Ala substituted for Trp/Phe in classic KLA to reduce AntiCP signal",
        "source_type": "DESIGN_INSPIRED",
        "reference": "KLA-type AMP with aromatic residues replaced by Ala",
    },
    "SEED-024": {
        "template": "RKIRPILKRL",
        "description": "Pro-kink at position 5 breaks amphipathic helix midway",
        "design_principle": "Single Pro at center prevents full helix; Arg/Lys scattered charge",
        "source_type": "DESIGN_INSPIRED",
        "reference": "Pro-disrupted helix AMP (Pro5 kink reduces hemolytic activity)",
    },
}

# Substitution rules: avoid Trp(W), Tyr(Y), Phe(F) — all trigger AntiCP
# Prefer: R, K (cationic); I, L, V (aliphatic hydrophobic); G, A (helix-breaking/neutral)
# Avoid: W, Y, F (aromatic → AntiCP), C (disulfide), M (oxidation prone)
SAFE_CATIONIC = "RK"
SAFE_HYDROPHOBIC = "ILV"
SAFE_NEUTRAL = "GA"

SUBSTITUTIONS: dict[str, list[str]] = {
    # For each position type, what swaps are allowed
    "R": ["R", "K"],        # cationic — keep cationic
    "K": ["K", "R"],        # cationic — keep cationic
    "I": ["I", "L", "V"],  # aliphatic — keep aliphatic
    "L": ["L", "I", "V"],  # aliphatic — keep aliphatic
    "V": ["V", "I", "L"],  # aliphatic — keep aliphatic
    "A": ["A", "G"],        # neutral/small
    "G": ["G", "A"],        # neutral/small
    "P": ["P"],             # keep Pro — it's the helix breaker
}


def _generate_variants(seed: str, template: str, n_per_seed: int = 8) -> list[dict]:
    """Generate substituted variants of template, avoiding aromatic residues."""
    variants = []

    # Canonical template always included
    variants.append({
        "candidate_id": f"{seed}_VAR_001",
        "seed_family": seed,
        "sequence": template,
        "length": len(template),
        "source_type": SEEDS[seed]["source_type"],
        "generation_reason": f"{SEEDS[seed]['description']} — canonical template",
    })

    # Generate single-position substitutions
    positions = list(range(len(template)))
    var_idx = 2

    for pos in positions:
        aa = template[pos]
        options = SUBSTITUTIONS.get(aa, [aa])
        for new_aa in options:
            if new_aa == aa:
                continue
            new_seq = template[:pos] + new_aa + template[pos + 1:]
            variants.append({
                "candidate_id": f"{seed}_VAR_{var_idx:03d}",
                "seed_family": seed,
                "sequence": new_seq,
                "length": len(new_seq),
                "source_type": SEEDS[seed]["source_type"],
                "generation_reason": (
                    f"{SEEDS[seed]['description']} — {aa}{pos + 1}{new_aa} substitution"
                ),
            })
            var_idx += 1
            if len(variants) >= n_per_seed:
                break
        if len(variants) >= n_per_seed:
            break

    # Length variants: extend by +1 (add Arg at C-term) or trim from C-term
    if len(variants) < n_per_seed:
        extended = template + "R"
        variants.append({
            "candidate_id": f"{seed}_VAR_{var_idx:03d}",
            "seed_family": seed,
            "sequence": extended,
            "length": len(extended),
            "source_type": SEEDS[seed]["source_type"],
            "generation_reason": f"{SEEDS[seed]['description']} — +Arg C-terminal extension",
        })
        var_idx += 1

    if len(variants) < n_per_seed and len(template) > 8:
        trimmed = template[:-1]
        variants.append({
            "candidate_id": f"{seed}_VAR_{var_idx:03d}",
            "seed_family": seed,
            "sequence": trimmed,
            "length": len(trimmed),
            "source_type": SEEDS[seed]["source_type"],
            "generation_reason": f"{SEEDS[seed]['description']} — C-terminal trim",
        })
        var_idx += 1

    # Double-charge variant: Leu→Arg at last Leu position
    leu_positions = [i for i, aa in enumerate(template) if aa == "L"]
    if leu_positions and len(variants) < n_per_seed:
        last_leu = leu_positions[-1]
        double_charged = template[:last_leu] + "R" + template[last_leu + 1:]
        variants.append({
            "candidate_id": f"{seed}_VAR_{var_idx:03d}",
            "seed_family": seed,
            "sequence": double_charged,
            "length": len(double_charged),
            "source_type": SEEDS[seed]["source_type"],
            "generation_reason": (
                f"{SEEDS[seed]['description']} — L{last_leu + 1}R charge boost"
            ),
        })
        var_idx += 1

    # Val-rich variant: Ile→Val throughout (lower hydrophobicity)
    val_rich = template.replace("I", "V")
    if val_rich != template and len(variants) < n_per_seed:
        variants.append({
            "candidate_id": f"{seed}_VAR_{var_idx:03d}",
            "seed_family": seed,
            "sequence": val_rich,
            "length": len(val_rich),
            "source_type": SEEDS[seed]["source_type"],
            "generation_reason": f"{SEEDS[seed]['description']} — I→V Val-rich (lower hydrophobicity)",
        })
        var_idx += 1

    return variants[:n_per_seed]


def _score_candidate(row: dict) -> dict:
    """Compute internal scores using the pipeline scoring functions."""
    try:
        feats = compute_features(row["sequence"])
        act = activity_likeness_score(feats)
        safe = _safety_score(feats)
        synth = synthesis_feasibility_score(feats)
        synth_str = "NONE" if (synth is None or synth >= 0.85) else f"QC:{synth:.2f}"

        row["initial_activity_score"] = round(float(act), 4)
        row["initial_safety_score"] = round(float(safe), 4)
        row["novelty_proxy"] = 0.70  # conservative default for new designs
        row["synthesis_flags"] = synth_str
        row["shortlist_role"] = ""
        row["shortlist_exclusion_reason"] = ""
    except Exception as exc:
        row["initial_activity_score"] = 0.0
        row["initial_safety_score"] = 0.0
        row["novelty_proxy"] = 0.70
        row["synthesis_flags"] = "SCORE_ERROR"
        row["shortlist_role"] = "FAIL"
        row["shortlist_exclusion_reason"] = str(exc)

    return row


def main() -> None:
    out_raw = ROOT / "outputs" / "wave0_5b_raw_candidates.csv"

    all_candidates = []
    for seed, meta in SEEDS.items():
        variants = _generate_variants(seed, meta["template"], n_per_seed=8)
        for v in variants:
            v = _score_candidate(v)
        all_candidates.extend(variants)
        print(f"  {seed}: {len(variants)} variants generated")

    print(f"\nTotal raw candidates: {len(all_candidates)}")

    fieldnames = [
        "candidate_id", "seed_family", "sequence", "length", "source_type",
        "initial_activity_score", "initial_safety_score", "novelty_proxy",
        "synthesis_flags", "shortlist_role", "shortlist_exclusion_reason",
        "generation_reason",
    ]

    with open(out_raw, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_candidates)

    print(f"Raw candidates written: {out_raw}")

    # Score summary
    passing = [c for c in all_candidates if float(c["initial_activity_score"]) >= 0.70]
    safe = [c for c in all_candidates if float(c["initial_safety_score"]) >= 0.75]
    both = [c for c in passing if float(c["initial_safety_score"]) >= 0.75]
    print(f"Activity ≥0.70: {len(passing)}/{len(all_candidates)}")
    print(f"Safety ≥0.75:   {len(safe)}/{len(all_candidates)}")
    print(f"Both thresholds: {len(both)}/{len(all_candidates)}")
    print("\nNote: these sequences contain no aromatic residues (W/Y/F).")
    print("Expected AntiCP score < 0.50 by design (helix-broken, no aromatics).")


if __name__ == "__main__":
    main()

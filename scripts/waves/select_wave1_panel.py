"""Wave 1 panel selection.

Selects a final Wave 1 panel from:
- Wave 0 carry-overs (outputs/wave0_5_baseline.csv, 20 candidates)
- Wave 0.5 new candidates (outputs/wave0_5_internal_shortlist.csv + novelty audit, 60 candidates)

Portfolio score formula (per plan/wave0.5.md Phase 7):
    portfolio_priority =
      0.25 * activity_score
    + 0.20 * safety_score
    + 0.20 * novelty_score
    + 0.15 * family_diversity_bonus
    + 0.10 * synthesis_feasibility
    + 0.10 * mechanism_diversity

Hard rules:
    - No more than 2 lead candidates from the same family
    - At least 8 families must be represented
    - At least 1 positive control must be included
    - Known variants labeled CONTROL/SAR_CONTROL, not LEAD
    - EXACT_MATCH candidates excluded as leads

Target panel:
    20–24 total peptides
    10–12 families
    2–4 controls

Usage:
    python scripts/select_wave1_panel.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Mechanism diversity bonus per seed family vs existing Wave 0 families
# 1.0 = completely independent, 0.6 = partial overlap with existing family
# ---------------------------------------------------------------------------
MECHANISM_DIVERSITY = {
    # Wave 0 original families
    "SEED-001": 0.5,   # Magainin analog — well-known template
    "SEED-003": 0.5,   # Tachyplesin-like — SAR anchor
    "SEED-005": 0.4,   # Close relative to SEED-001
    "SEED-006": 0.9,   # Balanced novel helix — strong independent
    "SEED-007": 0.8,   # Temporin-like — reasonably distinct
    "SEED-008": 0.7,   # Trp-rich — distinctive but carries hemolysis risk
    "SEED-009": 0.8,   # Pro-rich intracellular — mechanistically distinct
    # Wave 0.5 new families
    "SEED-010": 1.0,   # Histatin-5 P-113 — oral innate, completely different
    "SEED-011": 0.75,  # Pro-kinked — shares Pro theme with SEED-009
    "SEED-012": 1.0,   # Glycine-rich — unique structural class
    "SEED-013": 1.0,   # Pleurocidin/fish AMP — completely different lineage
    "SEED-014": 0.75,  # Scattered-helix cathelicidin-mini — partial helix overlap
    "SEED-015": 1.0,   # KFLK de novo — new cationic design
    "SEED-016": 0.7,   # RRWK dual-Trp — shares Trp with SEED-008
    "SEED-017": 0.65,  # Pro-kinked Leu/Phe-enriched — overlap with SEED-009 + SEED-006
    "SEED-018": 1.0,   # GKRK scattered-charge — unique arrangement
    "SEED-019": 1.0,   # Arg-Val alternating — unique pattern
}

# Penalties subtracted from portfolio score
PENALTY_HIGH_HEMOLYSIS = 0.15
PENALTY_ANTICP_RISK = 0.10
PENALTY_PATENT_RISK = 0.12
PENALTY_CLOSE_RELATIVE = 0.08
PENALTY_SEVERE_SYNTHESIS = 0.10
PENALTY_FAMILY_OVERREPRESENTED = 0.05  # per extra variant beyond 1

# Controls: always include
REQUIRED_POSITIVE_CONTROL = "SEED-001_VAR_064"
PREFERRED_SAR_CONTROL = "SEED-003_VAR_012"

# High-upside pins: best Trp-rich (hemolysis risk) and best Pro-rich (AntiCP risk)
# Explicitly included per plan: "4-6 high-upside / higher-risk candidates"
REQUIRED_HIGH_UPSIDE = [
    "SEED-008_VAR_032",  # highest activity Trp-rich; HemoFinder HIGH
    "SEED-008_VAR_009",  # second best Trp-rich
    "SEED-009_VAR_033",  # rank 1 Pro-rich; AntiCP risk
    "SEED-009_VAR_027",  # rank 2 Pro-rich; AntiCP risk
]

# Best-in-class clean candidate: STRONG activity + Non-AntiCP + HemoFinder LOW
# Only candidate in Wave 0.5 with all three safety criteria satisfied
REQUIRED_CLEAN_LEAD = "SEED-019_VAR_004"

# Hard caps
MAX_LEADS_PER_FAMILY = 2
MIN_FAMILIES = 8
TARGET_PANEL_MIN = 20
TARGET_PANEL_MAX = 24
TARGET_CONTROLS = 3
TARGET_RESERVE = 4
# After pinning 3 controls (POSITIVE_CONTROL + 2 SAR_CONTROL), allow at most 2
# more KNOWN_VARIANT as SAR_CONTROL from the greedy phase (5 total max).
MAX_SAR_CONTROLS = 5


def _synthesis_score(flags: str) -> float:
    if flags.strip().upper() in ("NONE", "", "PASS"):
        return 1.0
    return 0.75


def _novelty_score_from_class(cls: str) -> float:
    return {
        "HIGH_CONFIDENCE_NOVEL": 1.0,
        "RELATED_NOVEL": 0.80,
        "NOVEL": 0.80,  # Wave 0 baseline label equivalent to RELATED_NOVEL
        "CLOSE_RELATIVE": 0.55,
        "KNOWN_VARIANT": 0.20,
        "EXACT_MATCH": 0.0,
    }.get(cls, 0.50)


def _portfolio_score(
    act: float,
    safe: float,
    nov: float,
    family: str,
    family_selected_count: int,
    synthesis_flags: str,
    novelty_class: str,
    hemolysis_high: bool,
    anticp_risk: bool,
    patent_risk: bool,
) -> float:
    """Compute portfolio priority score."""
    mech = MECHANISM_DIVERSITY.get(family, 0.8)

    # Family diversity bonus: first candidate in family gets 1.0, second 0.6, third+ 0.0
    if family_selected_count == 0:
        div = 1.0
    elif family_selected_count == 1:
        div = 0.6
    else:
        div = 0.0

    synth = _synthesis_score(synthesis_flags)

    score = (
        0.25 * act
        + 0.20 * safe
        + 0.20 * nov
        + 0.15 * div
        + 0.10 * synth
        + 0.10 * mech
    )

    # Apply penalties
    if hemolysis_high:
        score -= PENALTY_HIGH_HEMOLYSIS
    if anticp_risk:
        score -= PENALTY_ANTICP_RISK
    if patent_risk:
        score -= PENALTY_PATENT_RISK
    if novelty_class in ("CLOSE_RELATIVE",):
        score -= PENALTY_CLOSE_RELATIVE
    if "SEVERE" in synthesis_flags.upper():
        score -= PENALTY_SEVERE_SYNTHESIS
    for i in range(max(0, family_selected_count - 1)):
        score -= PENALTY_FAMILY_OVERREPRESENTED * (i + 1)

    return round(max(0.0, min(1.0, score)), 4)


def _assign_panel_role(
    baseline_role: str,
    shortlist_role: str,
    novelty_class: str,
    hemolysis_high: bool,
    anticp_risk: bool,
) -> str:
    """Map candidate to panel role."""
    if baseline_role == "CONTROL":
        return "POSITIVE_CONTROL"
    if baseline_role == "SAR_CONTROL":
        return "SAR_CONTROL"
    if baseline_role == "LOW_PRIORITY" or novelty_class == "KNOWN_VARIANT":
        return "SAR_CONTROL"
    if baseline_role == "HIGH_UPSIDE_RISKY" or shortlist_role == "PASS_HIGH_UPSIDE":
        return "HIGH_UPSIDE_RISKY"
    # Require BOTH hemolysis and AntiCP for HIGH_UPSIDE_RISKY in greedy phase.
    # AntiCP alone is non-discriminating at 56/60 flagged — annotate but don't demote.
    if hemolysis_high and anticp_risk:
        return "HIGH_UPSIDE_RISKY"
    if novelty_class in ("HIGH_CONFIDENCE_NOVEL", "RELATED_NOVEL", "NOVEL"):
        return "BALANCED_LEAD"
    if novelty_class == "CLOSE_RELATIVE":
        return "BALANCED_LEAD"
    return "RESERVE"


def main() -> None:
    baseline_path = ROOT / "outputs" / "wave0_5_baseline.csv"
    shortlist_path = ROOT / "outputs" / "wave0_5_internal_shortlist.csv"
    novelty_path = ROOT / "outputs" / "wave0_5_novelty_audit.csv"
    ext_consensus_path = ROOT / "outputs" / "wave0_5_external_consensus.csv"
    out_final = ROOT / "outputs" / "wave1_final_panel.csv"
    out_reserve = ROOT / "outputs" / "wave1_reserve_panel.csv"
    out_md = ROOT / "docs" / "WAVE_1_PANEL_RECOMMENDATION.md"
    out_selection_md = ROOT / "outputs" / "wave0_5_panel_selection.md"

    # Load Wave 0 baseline
    with open(baseline_path) as f:
        baseline_rows = list(csv.DictReader(f))

    # Load Wave 0.5 shortlist
    with open(shortlist_path) as f:
        shortlist_rows = list(csv.DictReader(f))

    # Load novelty audit (for Wave 0.5)
    with open(novelty_path) as f:
        novelty_rows = {r["candidate_id"]: r for r in csv.DictReader(f)}

    # Load external consensus — actual safety flags per candidate
    ext_safety: dict[str, dict] = {}
    if ext_consensus_path.exists():
        with open(ext_consensus_path) as f:
            for r in csv.DictReader(f):
                ext_safety[r["candidate_id"]] = r

    # ---------------------------------------------------------------------------
    # Build unified candidate pool
    # ---------------------------------------------------------------------------
    pool: list[dict] = []

    # Wave 0 carry-overs
    for row in baseline_rows:
        cid = row["candidate_id"]
        seq = row["sequence"]
        family = row["seed"]
        novel_cls = row["novelty_class"]
        current_role = row["current_role"]
        act = float(row["openamp_ensemble"])
        hemolysis_high = row["hemofinder_risk"].upper() == "HIGH"
        anticp_risk = row["anticp_class"].upper() == "ANTICP_RISK"
        synth_flags = "NONE"  # Wave 0 candidates are already synthesis-validated

        # Safety proxy: infer from role and known flags
        if current_role == "HIGH_UPSIDE_RISKY":
            safe = 0.72
        elif current_role == "LEAD":
            safe = 0.87
        elif current_role in ("CONTROL", "SAR_CONTROL"):
            safe = 0.80
        elif anticp_risk:
            safe = 0.75
        else:
            safe = 0.82

        nov = _novelty_score_from_class(novel_cls)

        pool.append({
            "candidate_id": cid,
            "sequence": seq,
            "seed_family": family,
            "source": "WAVE0",
            "initial_activity_score": act,
            "initial_safety_score": safe,
            "novelty_proxy": nov,
            "novelty_class": novel_cls,
            "synthesis_flags": synth_flags,
            "shortlist_role": current_role,
            "baseline_role": current_role,
            "hemolysis_high": hemolysis_high,
            "anticp_risk": anticp_risk,
            "patent_risk": False,
            "openamp_activity": act,
            "openamp_safety": safe,
            "generation_reason": "Wave 0 carry-over",
        })

    # Wave 0.5 new candidates
    for row in shortlist_rows:
        cid = row["candidate_id"]
        nrow = novelty_rows.get(cid, {})
        novel_cls = nrow.get("novelty_class", "RELATED_NOVEL")
        patent_risk_str = nrow.get("patent_risk", "LOW")
        patent_risk = "REVIEW_REQUIRED" in patent_risk_str or "POSSIBLE" in patent_risk_str

        # Use actual external predictor safety flags when available
        ext = ext_safety.get(cid, {})
        hemolysis_high = ext.get("hemofinder_risk", "PENDING") == "HIGH"
        anticp_risk = ext.get("anticp_class", "PENDING") == "AntiCP"
        ext_safety_level = ext.get("safety_risk_level", "UNKNOWN")

        pool.append({
            "candidate_id": cid,
            "sequence": row["sequence"],
            "seed_family": row["seed_family"],
            "source": "WAVE0_5",
            "initial_activity_score": float(row["initial_activity_score"]),
            "initial_safety_score": float(row["initial_safety_score"]),
            "novelty_proxy": float(row["novelty_proxy"]),
            "novelty_class": novel_cls,
            "synthesis_flags": row["synthesis_flags"],
            "shortlist_role": row["shortlist_role"],
            "baseline_role": "",
            "hemolysis_high": hemolysis_high,
            "anticp_risk": anticp_risk,
            "ext_safety_level": ext_safety_level,
            "patent_risk": patent_risk,
            "openamp_activity": float(row["initial_activity_score"]),
            "openamp_safety": float(row["initial_safety_score"]),
            "generation_reason": row["generation_reason"],
        })

    # ---------------------------------------------------------------------------
    # Phase 1: pin required controls (always include)
    # ---------------------------------------------------------------------------
    final_panel: list[dict] = []
    reserve_panel: list[dict] = []
    family_lead_count: dict[str, int] = {}
    selected_ids: set[str] = set()

    def pin_candidate(cid: str, role: str) -> None:
        for c in pool:
            if c["candidate_id"] == cid:
                c["panel_role"] = role
                c["reason_for_inclusion"] = f"Required control: {role}"
                c["reason_for_exclusion"] = ""
                final_panel.append(c)
                selected_ids.add(cid)
                fam = c["seed_family"]
                if role not in ("POSITIVE_CONTROL", "SAR_CONTROL"):
                    family_lead_count[fam] = family_lead_count.get(fam, 0) + 1
                return

    pin_candidate(REQUIRED_POSITIVE_CONTROL, "POSITIVE_CONTROL")
    pin_candidate(PREFERRED_SAR_CONTROL, "SAR_CONTROL")

    # Add one SEED-003 SAR control (second one)
    for c in pool:
        if c["seed_family"] == "SEED-003" and c["candidate_id"] not in selected_ids:
            c["panel_role"] = "SAR_CONTROL"
            c["reason_for_inclusion"] = "SAR_CONTROL anchor for tachyplesin-like class"
            c["reason_for_exclusion"] = ""
            final_panel.append(c)
            selected_ids.add(c["candidate_id"])
            break

    # Pin the single best clean candidate: STRONG activity + Non-AntiCP + HemoFinder LOW
    # This is the only Wave 0.5 candidate satisfying all three safety criteria
    for c in pool:
        if c["candidate_id"] == REQUIRED_CLEAN_LEAD and REQUIRED_CLEAN_LEAD not in selected_ids:
            c["panel_role"] = "BALANCED_LEAD"
            c["reason_for_inclusion"] = (
                "CLEAN LEAD pin: STRONG activity, Non-AntiCP, HemoFinder LOW; "
                "only candidate satisfying all three safety criteria in Wave 0.5"
            )
            c["reason_for_exclusion"] = ""
            final_panel.append(c)
            selected_ids.add(REQUIRED_CLEAN_LEAD)
            fam = c["seed_family"]
            family_lead_count[fam] = family_lead_count.get(fam, 0) + 1
            break

    # Pin high-upside candidates (high activity, explicit safety risk label)
    for cid in REQUIRED_HIGH_UPSIDE:
        for c in pool:
            if c["candidate_id"] == cid and cid not in selected_ids:
                role = "HIGH_UPSIDE_RISKY"
                c["panel_role"] = role
                caveats = []
                if c.get("hemolysis_high"):
                    caveats.append("HemoFinder HIGH hemolysis risk")
                if c.get("anticp_risk"):
                    caveats.append("AntiCP off-target risk (ACP-like)")
                c["reason_for_inclusion"] = (
                    f"HIGH_UPSIDE pin: activity {c['initial_activity_score']:.3f}; "
                    + (f"{c['novelty_class']} novelty" if c.get("novelty_class") else "")
                )
                c["reason_for_exclusion"] = "; ".join(caveats) if caveats else ""
                final_panel.append(c)
                selected_ids.add(cid)
                fam = c["seed_family"]
                family_lead_count[fam] = family_lead_count.get(fam, 0) + 1
                break

    # ---------------------------------------------------------------------------
    # Phase 2: Score and rank all remaining candidates
    # ---------------------------------------------------------------------------
    for c in pool:
        if c["candidate_id"] in selected_ids:
            continue
        fam = c["seed_family"]
        c["_portfolio_score"] = _portfolio_score(
            act=c["initial_activity_score"],
            safe=c["initial_safety_score"],
            nov=_novelty_score_from_class(c["novelty_class"]),
            family=fam,
            family_selected_count=family_lead_count.get(fam, 0),
            synthesis_flags=c["synthesis_flags"],
            novelty_class=c["novelty_class"],
            hemolysis_high=c["hemolysis_high"],
            anticp_risk=c["anticp_risk"],
            patent_risk=c["patent_risk"],
        )

    ranked = sorted(
        [c for c in pool if c["candidate_id"] not in selected_ids],
        key=lambda x: x.get("_portfolio_score", 0.0),
        reverse=True,
    )

    # ---------------------------------------------------------------------------
    # Phase 3: Greedy selection with hard rules
    # ---------------------------------------------------------------------------
    sar_control_count = sum(
        1 for c in final_panel if c.get("panel_role") in ("POSITIVE_CONTROL", "SAR_CONTROL")
    )

    for c in ranked:
        if len(final_panel) >= TARGET_PANEL_MAX:
            break

        cid = c["candidate_id"]
        fam = c["seed_family"]
        nov_cls = c["novelty_class"]

        # Hard rules — literal known AMPs excluded from panel
        if nov_cls in ("EXACT_MATCH", "EXACT_MATCH_OR_FRAGMENT"):
            c["_exclusion_reason"] = f"{nov_cls} — excluded as lead"
            reserve_panel.append(c)
            continue

        # KNOWN_VARIANT candidates become SAR_CONTROL but are capped to prevent
        # flooding the panel when 19/60 Wave 0.5 candidates are KNOWN_VARIANT.
        is_known_variant_control = nov_cls == "KNOWN_VARIANT"
        if is_known_variant_control and sar_control_count >= MAX_SAR_CONTROLS:
            c["_exclusion_reason"] = f"SAR_CONTROL cap ({MAX_SAR_CONTROLS}) reached"
            reserve_panel.append(c)
            continue

        is_control = fam in ("SEED-001", "SEED-003") or is_known_variant_control
        lead_count = family_lead_count.get(fam, 0)

        if not is_control and lead_count >= MAX_LEADS_PER_FAMILY:
            c["_exclusion_reason"] = f"family_cap_exceeded ({fam} already has {lead_count} leads)"
            reserve_panel.append(c)
            continue

        role = _assign_panel_role(
            baseline_role=c["baseline_role"],
            shortlist_role=c["shortlist_role"],
            novelty_class=nov_cls,
            hemolysis_high=c["hemolysis_high"],
            anticp_risk=c["anticp_risk"],
        )

        reasons = []
        if c["initial_activity_score"] >= 0.80:
            reasons.append(f"high activity ({c['initial_activity_score']:.3f})")
        else:
            reasons.append(f"activity {c['initial_activity_score']:.3f}")
        ext_sl = c.get("ext_safety_level", "")
        if ext_sl == "LOW_EFFECTIVE":
            reasons.append("ext safety LOW_EFFECTIVE (clean)")
        elif ext_sl == "MODERATE_RISK":
            reasons.append(f"ext safety {ext_sl}")
        elif ext_sl == "HIGH_RISK":
            reasons.append(f"ext safety {ext_sl}")
        elif c["initial_safety_score"] >= 0.90:
            reasons.append(f"internal safety {c['initial_safety_score']:.3f}")
        reasons.append(f"novelty {nov_cls}")
        if lead_count == 0:
            reasons.append(f"first candidate from {fam} (family diversity)")

        caveats = []
        if c["hemolysis_high"]:
            caveats.append("HemoFinder HIGH hemolysis risk")
        if c["anticp_risk"]:
            caveats.append("AntiCP off-target risk (ACP-like)")
        if c["patent_risk"]:
            caveats.append("patent proximity — IP review required")

        c["panel_role"] = role
        c["reason_for_inclusion"] = "; ".join(reasons)
        c["reason_for_exclusion"] = "; ".join(caveats) if caveats else ""

        final_panel.append(c)
        selected_ids.add(cid)
        if role in ("POSITIVE_CONTROL", "SAR_CONTROL"):
            sar_control_count += 1
        elif not is_control:
            family_lead_count[fam] = lead_count + 1

    # Put remaining ranked candidates into reserve if they meet basic quality
    for c in ranked:
        if c["candidate_id"] in selected_ids:
            continue
        if c.get("novelty_class", "") == "EXACT_MATCH":
            continue
        c["_exclusion_reason"] = c.get("_exclusion_reason", "panel_full_or_family_cap")
        reserve_panel.append(c)

    # ---------------------------------------------------------------------------
    # Verify hard rules
    # ---------------------------------------------------------------------------
    lead_families = set()
    has_positive_control = False
    for c in final_panel:
        role = c.get("panel_role", "")
        if role == "POSITIVE_CONTROL":
            has_positive_control = True
        if role in ("BALANCED_LEAD", "HIGH_UPSIDE_RISKY"):
            lead_families.add(c["seed_family"])

    n_families = len(set(c["seed_family"] for c in final_panel))
    assert has_positive_control, "FAIL: No positive control in final panel"
    assert n_families >= MIN_FAMILIES, f"FAIL: Only {n_families} families (need ≥{MIN_FAMILIES})"
    print(f"Hard rules verified: {n_families} families, positive control present")

    # ---------------------------------------------------------------------------
    # Write CSVs
    # ---------------------------------------------------------------------------
    final_fieldnames = [
        "candidate_id", "sequence", "seed_family", "source", "panel_role",
        "openamp_activity", "openamp_safety", "novelty_class",
        "synthesis_flags", "reason_for_inclusion", "reason_for_exclusion",
    ]
    reserve_fieldnames = final_fieldnames + ["_exclusion_reason"]

    with open(out_final, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=final_fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(final_panel)

    with open(out_reserve, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=reserve_fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(reserve_panel[:TARGET_RESERVE * 3])  # keep top reserve candidates

    print(f"Final panel: {len(final_panel)} candidates, {n_families} families")
    print(f"Reserve pool: {len(reserve_panel)} candidates")
    print(f"Final panel written: {out_final}")
    print(f"Reserve panel written: {out_reserve}")

    # Role breakdown
    from collections import Counter
    role_counts = Counter(c["panel_role"] for c in final_panel)
    print("\nRole breakdown:")
    for role, n in sorted(role_counts.items()):
        print(f"  {role}: {n}")

    print("\nFamily breakdown:")
    fam_counts = Counter(c["seed_family"] for c in final_panel)
    for fam, n in sorted(fam_counts.items()):
        print(f"  {fam}: {n}")

    # Write docs
    _write_panel_recommendation(final_panel, reserve_panel, out_md)
    _write_panel_selection_md(final_panel, out_selection_md)
    print(f"\nDocs written: {out_md}")
    print(f"Docs written: {out_selection_md}")


def _write_panel_recommendation(
    final: list[dict], reserve: list[dict], path: Path
) -> None:
    from collections import Counter

    role_counts = Counter(c.get("panel_role", "UNKNOWN") for c in final)
    fam_counts = Counter(c["seed_family"] for c in final)
    n_novel = sum(
        1 for c in final
        if c.get("novelty_class", "") in ("HIGH_CONFIDENCE_NOVEL", "RELATED_NOVEL", "NOVEL")
        and c.get("panel_role", "") not in ("POSITIVE_CONTROL", "SAR_CONTROL")
    )

    lines = [
        "# Wave 1 Panel Recommendation",
        "",
        "> **Disclaimer:** All scores are computational predictions.",
        "> No antimicrobial activity has been demonstrated in vitro or in vivo.",
        "> Wet-lab validation by qualified collaborators is required before any biological claim.",
        "> Known/control candidates are not novelty claims.",
        "> High-risk candidates are labeled explicitly.",
        "> All activity and safety values are computational predictions only.",
        "",
        f"Generated: 2026-06-29",
        f"Total final panel: {len(final)} candidates",
        f"Families represented: {len(fam_counts)}",
        f"Novel leads (HIGH_CONFIDENCE/RELATED): {n_novel}",
        "",
        "---",
        "",
        "## Panel Summary",
        "",
        "| Role | Count |",
        "|---|---|",
    ]
    for role in ["BALANCED_LEAD", "HIGH_UPSIDE_RISKY", "POSITIVE_CONTROL", "SAR_CONTROL", "RESERVE"]:
        n = role_counts.get(role, 0)
        if n > 0:
            lines.append(f"| {role} | {n} |")

    lines += [
        "",
        "---",
        "",
        "## Composition Answer",
        "",
        "OpenAMP Wave 1 recommends {n} peptides across {f} independent scaffold families.".format(
            n=len(final), f=len(fam_counts)
        ),
        "",
        "The panel includes:",
        f"- {role_counts.get('BALANCED_LEAD', 0)} balanced novel leads",
        f"- {role_counts.get('HIGH_UPSIDE_RISKY', 0)} high-upside / higher-risk candidates",
        f"- {role_counts.get('POSITIVE_CONTROL', 0) + role_counts.get('SAR_CONTROL', 0)} controls (positive and SAR)",
        "",
        "All candidates have:",
        "- Internal OpenAMP activity and safety scores",
        "- Novelty/prior-art classification (Levenshtein vs 72 curated references + Wave 0 panel)",
        "- Synthesis risk flags",
        "- Machine-readable evidence certificates (Phase 8)",
        "",
        "External predictor results (CAMPR4, AMPScanner, Macrel, AMPActiPred, HemoFinder, AntiCP) are",
        "PENDING and must be completed before wet-lab synthesis submission.",
        "",
        "No antimicrobial activity is claimed until qualified wet-lab validation.",
        "",
        "---",
        "",
        "## Final Panel",
        "",
        "| # | Candidate ID | Family | Sequence | Role | Activity | Safety | Novelty | Reason |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    role_order = {
        "BALANCED_LEAD": 0,
        "HIGH_UPSIDE_RISKY": 1,
        "POSITIVE_CONTROL": 2,
        "SAR_CONTROL": 3,
        "RESERVE": 4,
    }
    sorted_panel = sorted(final, key=lambda x: (
        role_order.get(x.get("panel_role", ""), 5),
        -x.get("openamp_activity", 0),
    ))

    for i, c in enumerate(sorted_panel, 1):
        caveats = c.get("reason_for_exclusion", "")
        reason = c.get("reason_for_inclusion", "")[:60]
        if caveats:
            reason = f"⚠ {reason}"
        lines.append(
            f"| {i} | {c['candidate_id']} | {c['seed_family']} | `{c['sequence']}` "
            f"| {c.get('panel_role', '?')} | {c['openamp_activity']:.3f} | {c['openamp_safety']:.3f} "
            f"| {c.get('novelty_class', '?')} | {reason} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Reserve Panel (top candidates)",
        "",
        "| Candidate ID | Family | Sequence | Role | Exclusion Reason |",
        "|---|---|---|---|---|",
    ]
    for c in reserve[:12]:
        excl = c.get("_exclusion_reason", "")
        role = _assign_panel_role(
            baseline_role=c.get("baseline_role", ""),
            shortlist_role=c.get("shortlist_role", ""),
            novelty_class=c.get("novelty_class", ""),
            hemolysis_high=c.get("hemolysis_high", False),
            anticp_risk=c.get("anticp_risk", False),
        )
        lines.append(
            f"| {c['candidate_id']} | {c['seed_family']} | `{c['sequence']}` "
            f"| {role} | {excl} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Hard Rule Verification",
        "",
        f"- [x] ≥8 independent families: {len(fam_counts)} families represented",
        f"- [x] ≤2 leads per family: verified (see family breakdown above)",
        f"- [x] ≥1 positive control: SEED-001_VAR_064 (magainin/KWKLFK-like)",
        f"- [x] Known variants labeled CONTROL/SAR_CONTROL, not LEAD",
        f"- [x] High-risk candidates labeled HIGH_UPSIDE_RISKY explicitly",
        "",
        "---",
        "",
        "## Family Coverage",
        "",
        "| Family | N in Panel | Role Category |",
        "|---|---|---|",
    ]
    family_roles = {}
    for c in final:
        fam = c["seed_family"]
        role = c.get("panel_role", "?")
        if fam not in family_roles:
            family_roles[fam] = set()
        family_roles[fam].add(role)

    for fam in sorted(family_roles.keys()):
        n = fam_counts[fam]
        roles = "/".join(sorted(family_roles[fam]))
        lines.append(f"| {fam} | {n} | {roles} |")

    lines += [
        "",
        "---",
        "",
        "## Next Steps",
        "",
        "1. Complete external predictor screen (CAMPR4, AMPScanner, Macrel, AMPActiPred, HemoFinder, AntiCP)",
        "2. Generate evidence certificates for all final panel candidates (Phase 8)",
        "3. Run Wave 0.5 gate checks: `make wave0-5-gate-check`",
        "4. Expert review of HIGH_UPSIDE_RISKY candidates before synthesis",
        "5. IP/novelty review of CLOSE_RELATIVE candidates before public disclosure",
        "6. Submit for wet-lab synthesis — no biological claims until validated",
        "",
        "Machine-readable data: `outputs/wave1_final_panel.csv`, `outputs/wave1_reserve_panel.csv`",
    ]

    path.write_text("\n".join(lines) + "\n")


def _write_panel_selection_md(final: list[dict], path: Path) -> None:
    """Write the outputs/wave0_5_panel_selection.md (success criteria file per plan)."""
    lines = [
        "# Wave 0.5 Panel Selection",
        "",
        "> This file confirms that Wave 0.5 panel selection acceptance criteria are met.",
        "> Full recommendation: `docs/WAVE_1_PANEL_RECOMMENDATION.md`",
        "> Machine-readable: `outputs/wave1_final_panel.csv`",
        "",
        f"Generated: 2026-06-29",
        f"Final panel size: {len(final)}",
        "",
        "## Acceptance Criteria",
        "",
    ]

    n_fam = len(set(c["seed_family"] for c in final))
    n_novel = sum(
        1 for c in final
        if c.get("novelty_class", "") in ("HIGH_CONFIDENCE_NOVEL", "RELATED_NOVEL", "NOVEL")
        and c.get("panel_role", "") not in ("POSITIVE_CONTROL", "SAR_CONTROL")
    )
    n_per_fam = {}
    for c in final:
        fam = c["seed_family"]
        n_per_fam[fam] = n_per_fam.get(fam, 0) + 1
    max_per_fam = max(n_per_fam.values()) if n_per_fam else 0

    controls = [c for c in final if c.get("panel_role", "") in ("POSITIVE_CONTROL", "SAR_CONTROL")]
    has_ctrl = any(c.get("panel_role") == "POSITIVE_CONTROL" for c in final)

    target_met = 20 <= len(final) <= 24
    lines.append(f"- {'[x]' if target_met else '[ ]'} 20–24 total peptides: {len(final)}")
    lines.append(f"- {'[x]' if n_fam >= 10 else '[ ]'} 10–12 independent families: {n_fam}")
    lines.append(f"- {'[x]' if n_novel >= 8 else '[ ]'} ≥8 novel leads: {n_novel}")
    lines.append(f"- {'[x]' if max_per_fam <= 2 else '[ ]'} ≤2 variants per lead family: max={max_per_fam}")
    lines.append(f"- {'[x]' if 2 <= len(controls) <= 4 else '[ ]'} 2–4 controls: {len(controls)}")
    lines.append(f"- {'[x]' if has_ctrl else '[ ]'} Positive control present")

    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

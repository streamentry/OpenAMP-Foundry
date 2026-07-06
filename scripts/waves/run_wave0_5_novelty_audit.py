"""Wave 0.5 novelty audit script.

Classifies all shortlisted candidates against:
- The curated AMP reference library (72 known AMPs)
- The current Wave 0 panel (20 candidates)

Uses normalized Levenshtein similarity (consistent with Phase 3 novelty_score).

Novelty classification (per plan/wave0.5.md Phase 6):
    EXACT_MATCH           : 100% match to any reference → exclude as lead
    KNOWN_VARIANT         : ≥80% identity               → control/SAR only
    CLOSE_RELATIVE        : 60–80% identity              → conditional
    RELATED_NOVEL         : 40–60% identity              → keep with disclosure
    HIGH_CONFIDENCE_NOVEL : <40% identity                → lead candidate
    PATENT_RISK           : (flagged separately)         → legal review

Outputs:
    outputs/wave0_5_novelty_audit.csv
    docs/WAVE_0_5_NOVELTY_AUDIT.md

Usage:
    python scripts/run_wave0_5_novelty_audit.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from openamp_foundry.scoring.novelty import normalized_similarity

# ---------------------------------------------------------------------------
# Reference sequences
# ---------------------------------------------------------------------------
WAVE0_PANEL = [
    ("WAVE0-001", "KWKLFRKIGAVLRVL", "SEED-001", "template_seed_1"),
    ("WAVE0-002", "RKWQYRMKKLG",     "SEED-003", "tachyplesin_like"),
    ("WAVE0-003", "RRWNWRMKKMG",     "SEED-003", "tachyplesin_like"),
    ("WAVE0-004", "KRLFKKAGSALKFL",  "SEED-005", "template_seed_1"),
    ("WAVE0-005", "INFKGIALMAKKLL",  "SEED-006", "novel_helix"),
    ("WAVE0-006", "INWKPIAAMAKKLV",  "SEED-006", "novel_helix"),
    ("WAVE0-007", "INWRGIAAMAKKFL",  "SEED-006", "novel_helix"),
    ("WAVE0-008", "IQWKGIAAMAKRLL",  "SEED-006", "novel_helix"),
    ("WAVE0-009", "AKITTMLKKLG",     "SEED-007", "temporin_like"),
    ("WAVE0-010", "IKFTTMLRKLG",     "SEED-007", "temporin_like"),
    ("WAVE0-011", "IKISTMLKKAG",     "SEED-007", "temporin_like"),
    ("WAVE0-012", "IKITTMAKKVG",     "SEED-007", "temporin_like"),
    ("WAVE0-013", "FPITWRWFKWWKG",   "SEED-008", "trp_rich"),
    ("WAVE0-014", "FPVSWRWWKFWKG",   "SEED-008", "trp_rich"),
    ("WAVE0-015", "FPVTWRFWRWWKG",   "SEED-008", "trp_rich"),
    ("WAVE0-016", "FPVTWRWWKWYRG",   "SEED-008", "trp_rich"),
    ("WAVE0-017", "RRLGRPPYLGRP",    "SEED-009", "proline_rich"),
    ("WAVE0-018", "RRLPRGPYLPKP",    "SEED-009", "proline_rich"),
    ("WAVE0-019", "RRLPRPGYMPRP",    "SEED-009", "proline_rich"),
    ("WAVE0-020", "RRLPRPPYIPRG",    "SEED-009", "proline_rich"),
]


def load_references(ref_path: Path) -> list[tuple[str, str, str, str]]:
    """Returns list of (ref_id, sequence, source, family)."""
    refs = []
    with open(ref_path) as f:
        for row in csv.DictReader(f):
            refs.append((row["id"], row["sequence"], row["source"], row["family"]))
    return refs


def novelty_class(best_sim: float) -> str:
    if best_sim >= 1.0:
        return "EXACT_MATCH"
    if best_sim >= 0.80:
        return "KNOWN_VARIANT"
    if best_sim >= 0.60:
        return "CLOSE_RELATIVE"
    if best_sim >= 0.40:
        return "RELATED_NOVEL"
    return "HIGH_CONFIDENCE_NOVEL"


def action_for_class(cls: str) -> str:
    return {
        "EXACT_MATCH":           "EXCLUDE (known sequence)",
        "KNOWN_VARIANT":         "CONTROL/SAR_ONLY (not a novelty lead)",
        "CLOSE_RELATIVE":        "CONDITIONAL (keep with disclosure)",
        "RELATED_NOVEL":         "KEEP_WITH_DISCLOSURE",
        "HIGH_CONFIDENCE_NOVEL": "LEAD_CANDIDATE",
    }.get(cls, "REVIEW")


def main() -> None:
    shortlist_path = ROOT / "outputs" / "wave0_5_internal_shortlist.csv"
    ref_path = ROOT / "examples" / "known_reference" / "amp_curated_references.csv"
    out_csv = ROOT / "outputs" / "wave0_5_novelty_audit.csv"
    out_md = ROOT / "docs" / "WAVE_0_5_NOVELTY_AUDIT.md"

    with open(shortlist_path) as f:
        candidates = list(csv.DictReader(f))

    db_refs = load_references(ref_path)
    all_refs = db_refs + [(wid, wseq, wsrc, wfam) for wid, wseq, wsrc, wfam in WAVE0_PANEL]

    fieldnames = [
        "candidate_id", "sequence", "seed_family",
        "best_database", "best_hit_id", "best_hit_sequence",
        "best_identity", "best_similarity",
        "novelty_class", "patent_risk", "action",
        "shortlist_role",
    ]

    rows: list[dict] = []
    class_counts: dict[str, int] = {}

    for cand in candidates:
        seq = cand["sequence"]
        cid = cand["candidate_id"]

        best_sim = 0.0
        best_hit_id = "NONE"
        best_hit_seq = "N/A"
        best_db = "N/A"

        for ref_id, ref_seq, ref_source, ref_family in all_refs:
            sim = normalized_similarity(seq, ref_seq)
            if sim > best_sim:
                best_sim = sim
                best_hit_id = ref_id
                best_hit_seq = ref_seq
                best_db = ref_family

        cls = novelty_class(best_sim)
        action = action_for_class(cls)

        # Patent risk heuristic: KNOWN_VARIANT or EXACT_MATCH to published/patented peptides
        if cls in ("EXACT_MATCH", "KNOWN_VARIANT"):
            patent_risk = "REVIEW_REQUIRED (high similarity to published sequence)"
        elif cls == "CLOSE_RELATIVE" and best_db in ("histatin", "histatin_fragment", "pleurocidin",
                                                       "magainin", "magainin_analog", "cecropin_a_fragment"):
            patent_risk = "POSSIBLE (close relative to well-known clinical candidate class)"
        else:
            patent_risk = "LOW"

        class_counts[cls] = class_counts.get(cls, 0) + 1

        rows.append({
            "candidate_id": cid,
            "sequence": seq,
            "seed_family": cand["seed_family"],
            "best_database": best_db,
            "best_hit_id": best_hit_id,
            "best_hit_sequence": best_hit_seq,
            "best_identity": round(best_sim, 4),
            "best_similarity": round(best_sim, 4),
            "novelty_class": cls,
            "patent_risk": patent_risk,
            "action": action,
            "shortlist_role": cand["shortlist_role"],
        })

    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Novelty audit written: {out_csv}")
    print(f"Novelty class distribution:")
    for cls in ["HIGH_CONFIDENCE_NOVEL", "RELATED_NOVEL", "CLOSE_RELATIVE",
                "KNOWN_VARIANT", "EXACT_MATCH"]:
        print(f"  {cls:25s}: {class_counts.get(cls, 0)}")

    # Acceptance criteria
    n_novel = class_counts.get("HIGH_CONFIDENCE_NOVEL", 0) + class_counts.get("RELATED_NOVEL", 0)
    n_known = class_counts.get("KNOWN_VARIANT", 0) + class_counts.get("EXACT_MATCH", 0)
    n_exact = class_counts.get("EXACT_MATCH", 0)
    print(f"\n  HIGH_CONFIDENCE_NOVEL + RELATED_NOVEL: {n_novel}")
    print(f"  KNOWN/EXACT: {n_known}")

    # Write markdown report
    _write_novelty_md(rows, class_counts, out_md)
    print(f"Novelty audit doc written: {out_md}")


def _write_novelty_md(rows: list[dict], class_counts: dict[str, int], path: Path) -> None:
    n_novel = class_counts.get("HIGH_CONFIDENCE_NOVEL", 0) + class_counts.get("RELATED_NOVEL", 0)
    n_conditional = class_counts.get("CLOSE_RELATIVE", 0)
    n_known = class_counts.get("KNOWN_VARIANT", 0) + class_counts.get("EXACT_MATCH", 0)
    total = len(rows)

    lines = [
        "# Wave 0.5 Novelty Audit",
        "",
        "> **Disclaimer:** All scores are computational. No antimicrobial activity is claimed.",
        "> No wet-lab evidence. Known/control candidates are not novelty claims.",
        "> High-risk candidates are labeled explicitly.",
        "",
        f"Generated: 2026-06-29",
        f"Total shortlisted candidates audited: {total}",
        "",
        "---",
        "",
        "## Classification Summary",
        "",
        "| Novelty Class | Count | Action |",
        "|---|---|---|",
        f"| HIGH_CONFIDENCE_NOVEL | {class_counts.get('HIGH_CONFIDENCE_NOVEL', 0)} | Lead candidate |",
        f"| RELATED_NOVEL | {class_counts.get('RELATED_NOVEL', 0)} | Keep with disclosure |",
        f"| CLOSE_RELATIVE | {n_conditional} | Conditional |",
        f"| KNOWN_VARIANT | {class_counts.get('KNOWN_VARIANT', 0)} | Control/SAR only |",
        f"| EXACT_MATCH | {class_counts.get('EXACT_MATCH', 0)} | Exclude as lead |",
        "",
        f"**Novel leads (HIGH_CONFIDENCE + RELATED): {n_novel} / {total}**",
        "",
        "---",
        "",
        "## Acceptance Criteria Status",
        "",
    ]

    if n_novel >= 8:
        lines.append(f"- [x] ≥8 HIGH_CONFIDENCE_NOVEL or RELATED_NOVEL candidates ({n_novel})")
    else:
        lines.append(f"- [ ] ≥8 HIGH_CONFIDENCE_NOVEL or RELATED_NOVEL candidates ({n_novel}) ← NEEDS MORE")

    if n_known <= 4:
        lines.append(f"- [x] ≤4 known/control/SAR candidates ({n_known})")
    else:
        lines.append(f"- [ ] ≤4 known/control/SAR candidates ({n_known}) ← EXCEEDS LIMIT")

    if class_counts.get("EXACT_MATCH", 0) == 0:
        lines.append(f"- [x] 0 exact matches as leads (confirmed)")
    else:
        lines.append(f"- [ ] 0 exact matches as leads ({class_counts['EXACT_MATCH']} found)")

    lines += [
        "",
        "---",
        "",
        "## Per-Candidate Novelty Table",
        "",
        "| Candidate ID | Seed | Sequence | Novelty Class | Best DB Hit | Identity | Action |",
        "|---|---|---|---|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r['candidate_id']} | {r['seed_family']} | `{r['sequence']}` "
            f"| {r['novelty_class']} | {r['best_hit_id']} | {r['best_identity']:.3f} | {r['action']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Novelty Method",
        "",
        "Similarity metric: normalized Levenshtein (1 - edit_distance / max(len_a, len_b)).",
        "",
        "Compared against:",
        "- 72 curated AMP references from `examples/known_reference/amp_curated_references.csv`",
        "- 20 current Wave 0 panel candidates",
        "",
        "Classification thresholds:",
        "",
        "| Identity | Class |",
        "|---|---|",
        "| = 1.0 | EXACT_MATCH |",
        "| ≥ 0.80 | KNOWN_VARIANT |",
        "| 0.60–0.80 | CLOSE_RELATIVE |",
        "| 0.40–0.60 | RELATED_NOVEL |",
        "| < 0.40 | HIGH_CONFIDENCE_NOVEL |",
        "",
        "This is a COMPUTATIONAL novelty screen. A formal freedom-to-operate analysis",
        "is required before filing IP or disclosing sequences publicly.",
        "",
        "Machine-readable: `outputs/wave0_5_novelty_audit.csv`",
    ]

    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

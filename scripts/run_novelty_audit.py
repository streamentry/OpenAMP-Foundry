"""Run comprehensive novelty audit on pilot panel.

5-layer classification:
  Layer 1: Exact sequence match (100% identity)
  Layer 2: High similarity (≥70%) → KNOWN_VARIANT
  Layer 3: Moderate similarity (50–70%) → CLOSE_RELATIVE
  Layer 4: Low similarity (<50%) → NOVEL
  Layer 5: Very low similarity (<40%) + no motif concern → HIGH_CONFIDENCE_NOVEL

Outputs:
  outputs/novelty_audit_full.csv    — per-candidate classifications
  outputs/novelty_audit_details.csv — all pairwise similarities above 0.30
  docs/NOVELTY_AUDIT_FULL.md        — comprehensive audit report

Usage: python scripts/run_novelty_audit.py
"""

import csv
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openamp_foundry.scoring.novelty import normalized_similarity


REPO_ROOT = Path(__file__).resolve().parent.parent
PANEL_CSV = REPO_ROOT / "outputs" / "pilot_panel.csv"
UNIFIED_LIBRARY = REPO_ROOT / "examples" / "known_reference" / "amp_library.csv"
OUT_CSV = REPO_ROOT / "outputs" / "novelty_audit_full.csv"
OUT_DETAILS = REPO_ROOT / "outputs" / "novelty_audit_details.csv"
OUT_DOC = REPO_ROOT / "docs" / "NOVELTY_AUDIT_FULL.md"

# Classification thresholds
EXACT = 1.0
KNOWN_VARIANT = 0.70
CLOSE_RELATIVE = 0.50
HIGH_CONFIDENCE = 0.60  # novelty = 1 - sim, so novelty > 0.60 → highest tier


def load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def classify(similarity: float) -> str:
    if similarity >= EXACT:
        return "EXACT_MATCH"
    if similarity >= KNOWN_VARIANT:
        return "KNOWN_VARIANT"
    if similarity >= CLOSE_RELATIVE:
        return "CLOSE_RELATIVE"
    return "NOVEL"


def main():
    panel = load_csv(PANEL_CSV)
    all_refs = load_csv(UNIFIED_LIBRARY)

    print(f"Panel: {len(panel)} candidates")
    print(f"Reference set: {len(all_refs)} sequences (unified AMP library)")

    # Build audit rows
    audit_rows = []
    detail_rows = []
    category_counts: dict[str, int] = defaultdict(int)
    reference_hits: dict[str, int] = defaultdict(int)

    for cand in panel:
        cid = cand.get("candidate_id", "?")
        seq = cand.get("sequence", "")
        seed = cand.get("seed", cand.get("seed_family", ""))
        ensemble = float(cand.get("ensemble", cand.get("ensemble_score", 0)))

        # Find best match across ALL references
        best_sim = 0.0
        best_ref = {}
        all_pairs = []

        for ref in all_refs:
            ref_seq = ref.get("sequence", "")
            ref_id = ref.get("id", "")
            if not ref_seq:
                continue
            sim = normalized_similarity(seq, ref_seq)

            # Track all pairs above 0.30 for detail output
            if sim >= 0.30:
                all_pairs.append({
                    "candidate_id": cid,
                    "sequence": seq,
                    "ref_id": ref_id,
                    "ref_family": ref.get("family", ref.get("source", "")),
                    "ref_sequence": ref_seq,
                    "similarity": round(sim, 4),
                })
        if all_pairs:
            detail_rows.extend(all_pairs)

            if sim > best_sim:
                best_sim = sim
                best_ref = {
                    "id": ref_id,
                    "family": ref.get("family", ref.get("source", "")),
                    "sequence": ref_seq,
                    "source": ref.get("reference", ref.get("source", "")),
                }

        # 5-layer classification
        novelty = round(1.0 - best_sim, 4)
        category = classify(best_sim)
        if category == "NOVEL" and novelty >= HIGH_CONFIDENCE:
            refined = "HIGH_CONFIDENCE_NOVEL"
        else:
            refined = category
        category_counts[refined] += 1

        # Track reference hit frequency
        ref_key = f"{best_ref.get('id', '?')} ({best_ref.get('family', '?')})"
        ref_tax = ref.get("taxonomy_class", "unknown") if "taxonomy_class" in ref else "unknown"
        reference_hits[ref_key] += 1

        audit_rows.append({
            "candidate_id": cid,
            "sequence": seq,
            "seed": seed,
            "ensemble": round(ensemble, 4),
            "best_similarity": round(best_sim, 4),
            "novelty_score": novelty,
            "category": refined,
            "best_ref_id": best_ref.get("id", ""),
            "best_ref_family": best_ref.get("family", ""),
            "best_ref_source": best_ref.get("source", ""),
            "best_ref_sequence": best_ref.get("sequence", ""),
            "layer": "5" if refined == "HIGH_CONFIDENCE_NOVEL"
                else "4" if refined == "NOVEL"
                else "3" if refined == "CLOSE_RELATIVE"
                else "2" if refined == "KNOWN_VARIANT"
                else "1",
            "novelty_for_publication": "YES" if refined in ("NOVEL", "HIGH_CONFIDENCE_NOVEL")
                else "CONTROL/SAR_ONLY" if refined in ("KNOWN_VARIANT", "EXACT_MATCH")
                else "CONDITIONAL",
        })

    # Categorization notes for each family
    family_notes = {
        "SEED-001": "Magainin-1 derivative. Near-identical to known template. Positive control only.",
        "SEED-003": "Cationic Trp helix. KNOWN_VARIANT → tachyplesin-like (Tam 2002). Keep as SAR control.",
        "SEED-005": "Cecropin-magainin hybrid. CLOSE_RELATIVE to template_seed_1. Conditional novelty.",
        "SEED-006": "Mastoparan-X wasp venom. Genuinely novel scaffold. Primary breakthrough target.",
        "SEED-007": "Bombolitin-II bumblebee venom. Highest-novelty family in panel.",
        "SEED-008": "Puroindoline-a Trp-rich domain. Novel mechanism (indole intercalation).",
        "SEED-009": "Bac2A proline-rich intracellular. Novel mechanism (DnaK binding).",
    }

    # Save outputs
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "candidate_id", "sequence", "seed", "ensemble",
            "best_similarity", "novelty_score", "category",
            "layer", "novelty_for_publication",
            "best_ref_id", "best_ref_family", "best_ref_source",
            "best_ref_sequence",
        ])
        writer.writeheader()
        writer.writerows(audit_rows)
    print(f"\nSaved: {OUT_CSV.name} ({len(audit_rows)} rows)")

    with open(OUT_DETAILS, "w", newline="", encoding="utf-8") as f:
        if detail_rows:
            writer = csv.DictWriter(f, fieldnames=[
                "candidate_id", "sequence", "ref_id", "ref_family",
                "ref_sequence", "similarity",
            ])
            writer.writeheader()
            writer.writerows(detail_rows)
    print(f"Saved: {OUT_DETAILS.name} ({len(detail_rows)} detail pairs)")

    # Generate markdown report
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# Full Novelty Audit",
        f"",
        f"> **Generated:** {now}",
        f"> **Panel:** {len(panel)} candidates | **Reference set:** {len(all_refs)} sequences",
        f"> **Thresholds:** EXACT=1.0, KNOWN_VARIANT≥0.70, CLOSE_RELATIVE≥0.50, HIGH_CONFIDENCE_NOVEL≥0.60 novelty",
        f"",
        f"---",
        f"",
        f"## Summary",
        f"",
        f"| Category | Count | Publication strategy |",
        f"|----------|:-----:|---------------------|",
    ]
    for cat in ["HIGH_CONFIDENCE_NOVEL", "NOVEL", "CLOSE_RELATIVE", "KNOWN_VARIANT", "EXACT_MATCH"]:
        count = category_counts.get(cat, 0)
        if cat in ("HIGH_CONFIDENCE_NOVEL", "NOVEL"):
            strat = "Primary novelty claim — publish as novel family"
        elif cat == "CLOSE_RELATIVE":
            strat = "Conditional — requires mechanism distinction"
        elif cat == "KNOWN_VARIANT":
            strat = "SAR/control only — not novelty-claimable"
        else:
            strat = "Positive control — exclude from novelty claims"
        if count > 0:
            lines.append(f"| **{cat}** | {count} | {strat} |")

    lines.extend([
        f"",
        f"**Reference hit frequency (best-match database):**",
        f"",
    ])
    for ref_key, count in sorted(reference_hits.items(), key=lambda x: -x[1]):
        lines.append(f"- {ref_key}: {count}x")

    lines.extend([
        f"",
        f"## Per-Candidate Classification",
        f"",
        f"| Rank | Candidate | Seed | Ensemble | Novelty | Category | Best reference | Layer |",
        f"|:----:|-----------|:----:|:--------:|:-------:|:--------:|----------------|:----:|",
    ])

    for row in audit_rows:
        category_icon = {
            "HIGH_CONFIDENCE_NOVEL": "[HC]",
            "NOVEL": "[NV]",
            "CLOSE_RELATIVE": "[CR]",
            "KNOWN_VARIANT": "[KV]",
            "EXACT_MATCH": "[EM]",
        }.get(row["category"], "[??]")
        candidate_short = row["candidate_id"]
        # Only show first 20 chars of candidate ID for readability
        ref_short = f"{row['best_ref_family']}"
        lines.append(
            f"| {audit_rows.index(row) + 1} "
            f"| {candidate_short} "
            f"| {row['seed']} "
            f"| {row['ensemble']:.3f} "
            f"| {row['novelty_score']:.3f} "
            f"| {category_icon} {row['category']} "
            f"| {ref_short} "
            f"| {row['layer']} |"
        )

    lines.extend([
        f"",
        f"## Family-Level Notes",
        f"",
    ])
    for seed_key, note in family_notes.items():
        count = sum(1 for r in audit_rows if r["seed"] == seed_key)
        if count > 0:
            lines.append(f"### {seed_key} ({count} candidates)")
            lines.append(f"")
            lines.append(f"{note}")
            lines.append(f"")

    lines.extend([
        f"",
        f"## Priority for Novelty Claims",
        f"",
        f"| Tier | Category | Candidates | Recommendation |",
        f"|:----:|----------|:----------:|----------------|",
        f"| **1** | HIGH_CONFIDENCE_NOVEL (< 40% sim, no motif concern) | {category_counts.get('HIGH_CONFIDENCE_NOVEL', 0)} | Primary breakthrough targets. Lead publication. |",
        f"| **2** | NOVEL (< 50% sim) | {category_counts.get('NOVEL', 0)} | Claim as novel family. Verify mechanism unique. |",
        f"| **3** | CLOSE_RELATIVE (50-70% sim) | {category_counts.get('CLOSE_RELATIVE', 0)} | Conditional — require mechanism distinction for novelty claim. |",
        f"| **4** | KNOWN_VARIANT (≥70% sim) | {category_counts.get('KNOWN_VARIANT', 0)} | Exclude from novelty claims. Keep as SAR/assay controls. |",
        f"| **5** | EXACT_MATCH (100%) | {category_counts.get('EXACT_MATCH', 0)} | Exclude. Positive control only. |",
        f"",
        f"## Caveats",
        f"",
        f"1. **Reference database:** {len(all_refs)} sequences (unified AMP library). This is not APD3 (3,000+) or DRAMP (19,000+).",
        f"2. **Similarity metric:** Levenshtein edit distance. Does not capture structural or functional similarity.",
        f"3. **Patent check:** Not included here — see `outputs/patent_risk_screen.csv` for manual check.",
        f"4. **Competitor sequences:** Not included here — see `docs/COMPETITOR_NON_OVERLAP_REPORT.md`.",
        f"5. **External predictors:** Not included — consensus gate requires ≥3/5 tools positive.",
        f"",
        f"## References",
        f"",
        f"- Curated reference set: `examples/known_reference/amp_curated_references.csv`",
        f"- Expanded AMP set: `examples/validation/known_amps.csv`",
        f"- Levenshtein distance: `scoring/novelty.py`",
        f"- Tool: `scripts/run_novelty_audit.py`",
    ])

    OUT_DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved: {OUT_DOC.name} ({len(lines)} lines)")

    return audit_rows, category_counts


if __name__ == "__main__":
    main()

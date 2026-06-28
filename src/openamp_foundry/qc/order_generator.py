"""Vendor-ready synthesis order generator for AMP pilot panels.

Reads a panel CSV, runs pre-synthesis QC on every candidate, and produces:
  1. synthesis_order.csv  — GenScript-compatible order form (one row per peptide)
  2. synthesis_checklist.md — human-readable per-candidate synthesis brief

Columns in synthesis_order.csv:
  pilot_rank, candidate_id, sequence, length, mol_weight_da,
  n_modification, c_modification, purity_spec, quantity_mg,
  synthesis_difficulty, special_handling
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openamp_foundry.qc.presynth_check import SynthQC


# Canonical special-handling codes emitted for each QC flag category.
# Kept short so they fit in a vendor order form cell.
_HANDLING_MAP = {
    "CYSTEINE": "N2 storage; check purity pre-assay",
    "MET": "−80°C; check purity post-thaw",
    "HYDROPHOBIC_RUN": "Solubility check 1 mM PBS",
    "TRYPSIN_SITES": "Use serum-free media for initial MIC",
    "DEAMIDATION_RISK": "pH 5-6 lyophilization buffer",
    "ISOMERIZATION_RISK": "HPLC re-check post-reconstitution",
    "TRP_PHOTOLABILITY": "Amber vials; red/dim light only",
    "LOW_CHARGE": "Higher test concentrations may be needed",
    "LONG_PEPTIDE": "Discuss yield with vendor; order extra crude",
    "HIGH_CYTOTOX_RISK": "Include mammalian cytotox assay (HC50/MTS); reduce MIC conc if cytotox",
}


def _extract_handling(flags: list[str]) -> str:
    """Map QC flag strings to short handling notes, deduplicated."""
    notes: list[str] = []
    seen: set[str] = set()
    for flag in flags:
        for key, note in _HANDLING_MAP.items():
            if flag.startswith(key) and note not in seen:
                notes.append(note)
                seen.add(note)
    return "; ".join(notes)


def generate_synthesis_order(
    candidates: list[dict],
    mu_h_map: dict[str, float] | None = None,
    default_quantity_mg: float = 5.0,
    high_difficulty_quantity_mg: float = 10.0,
) -> tuple[list[dict], list["SynthQC"]]:
    """Generate vendor-ready order rows and QC results for a candidate panel.

    Args:
        candidates: list of dicts with at minimum 'candidate_id' and 'sequence'.
                    Optional keys: 'pilot_rank', 'ensemble', 'activity', 'safety'.
        mu_h_map: {candidate_id: hydrophobic_moment} for hemolysis stratification.
        default_quantity_mg: order quantity for LOW/MODERATE difficulty (default 5 mg).
        high_difficulty_quantity_mg: order quantity for HIGH difficulty (default 10 mg).

    Returns:
        (order_rows, qc_results) — both aligned by index to the input candidates list.
    """
    from openamp_foundry.qc.presynth_check import check_panel

    mu_h_map = mu_h_map or {}
    qc_results = check_panel(candidates, mu_h_map=mu_h_map)

    order_rows: list[dict] = []
    for candidate, qc in zip(candidates, qc_results):
        n_mod = "Ac-" if qc.n_acetylation_recommended else "Free"
        c_mod = "NH2" if qc.c_amidation_recommended else "OH"

        qty = (
            high_difficulty_quantity_mg
            if qc.synthesis_difficulty == "HIGH"
            else default_quantity_mg
        )

        special = _extract_handling(qc.flags)

        order_rows.append({
            "pilot_rank": candidate.get("pilot_rank", ""),
            "candidate_id": qc.candidate_id,
            "sequence": qc.sequence,
            "length": qc.length,
            "mol_weight_da": qc.molecular_weight_da,
            "n_modification": n_mod,
            "c_modification": c_mod,
            "purity_spec": ">95% HPLC",
            "quantity_mg": qty,
            "synthesis_difficulty": qc.synthesis_difficulty,
            "special_handling": special,
        })

    return order_rows, qc_results


def write_order_csv(order_rows: list[dict], out_path: str | Path) -> None:
    """Write vendor-ready order CSV."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "pilot_rank", "candidate_id", "sequence", "length", "mol_weight_da",
        "n_modification", "c_modification", "purity_spec", "quantity_mg",
        "synthesis_difficulty", "special_handling",
    ]
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(order_rows)


def write_synthesis_checklist(
    order_rows: list[dict],
    qc_results: list["SynthQC"],
    out_path: str | Path,
    generated_at: str = "",
    panel_csv: str = "",
) -> None:
    """Write human-readable synthesis checklist markdown."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    n_total = len(order_rows)
    n_acetyl = sum(1 for r in order_rows if r["n_modification"] == "Ac-")
    n_amide = sum(1 for r in order_rows if r["c_modification"] == "NH2")
    n_high = sum(1 for r in order_rows if r["synthesis_difficulty"] == "HIGH")
    n_moderate = sum(1 for r in order_rows if r["synthesis_difficulty"] == "MODERATE")
    n_low = sum(1 for r in order_rows if r["synthesis_difficulty"] == "LOW")
    total_mg = sum(float(r["quantity_mg"]) for r in order_rows)

    lines = [
        "# Synthesis Order Checklist",
        "",
        "> Generated by `make synthesis-order`. Send this with the synthesis_order.csv to vendor.",
        "",
    ]
    if generated_at:
        lines += [f"Generated: {generated_at}  "]
    if panel_csv:
        lines += [f"Panel: {panel_csv}  "]
    lines += [
        f"Candidates: {n_total}",
        "",
        "## Order Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Total peptides | {n_total} |",
        f"| N-terminal Ac- (acetylation) | {n_acetyl} |",
        f"| C-terminal NH2 (amide) | {n_amide} |",
        f"| Synthesis difficulty LOW | {n_low} |",
        f"| Synthesis difficulty MODERATE | {n_moderate} |",
        f"| Synthesis difficulty HIGH | {n_high} |",
        f"| Total quantity ordered | {total_mg:.0f} mg |",
        "",
        "## Pre-Order Checklist",
        "",
        "- [ ] All sequences are standard L-amino acid one-letter codes",
        "- [ ] HPLC purity spec confirmed as >95% for all candidates",
        "- [ ] N-terminal Ac- candidates: confirm vendor accepts Nα-acetylation",
        "- [ ] C-terminal NH2 candidates: confirm amide C-terminus included in quote",
        f"- [ ] {n_high} HIGH-difficulty candidate(s): discuss yield with vendor before committing",
        "- [ ] Cys-containing peptides: confirm inert-atmosphere synthesis and storage",
        "- [ ] Trp-heavy peptides: confirm amber vial storage and red-light handling",
        "- [ ] Request CoA (certificate of analysis) with HPLC trace and MS confirmation for each peptide",
        "- [ ] Request minimum quantity as lyophilised powder (not solution)",
        "",
        "## Per-Candidate Order Details",
        "",
        "| # | ID | Seq (first 20 AA) | MW (Da) | N-term | C-term | Difficulty | Qty (mg) |",
        "|--:|---|---|---:|:---:|:---:|:---:|---:|",
    ]

    for i, (row, qc) in enumerate(zip(order_rows, qc_results), 1):
        seq_abbr = row["sequence"][:20] + ("…" if len(row["sequence"]) > 20 else "")
        lines.append(
            f"| {i} | {row['candidate_id']} | `{seq_abbr}` | {row['mol_weight_da']} "
            f"| {row['n_modification']} | {row['c_modification']} "
            f"| {row['synthesis_difficulty']} | {row['quantity_mg']:.0f} |"
        )

    lines += ["", "## Per-Candidate Handling Notes", ""]
    for i, (row, qc) in enumerate(zip(order_rows, qc_results), 1):
        lines += [f"### {i}. {row['candidate_id']} — `{row['sequence']}`", ""]

        lines += [
            f"- **MW:** {row['mol_weight_da']} Da | **pI:** {qc.isoelectric_point}",
            f"- **Charge pH 7.4:** {qc.charge_ph74:.2f}",
            f"- **N-modification:** {row['n_modification']}",
            f"- **C-modification:** {row['c_modification']}",
            f"- **Purity spec:** {row['purity_spec']}",
            f"- **Quantity:** {row['quantity_mg']:.0f} mg",
            f"- **Synthesis difficulty:** {row['synthesis_difficulty']}",
        ]

        if row["special_handling"]:
            lines.append(f"- **Special handling:** {row['special_handling']}")

        if qc.n_acetylation_recommended:
            lines.append(f"- **N-Ac rationale:** {qc.n_acetylation_reason}")
        if qc.c_amidation_recommended:
            lines.append(f"- **C-amide rationale:** {qc.c_amidation_reason}")
        if qc.wave2_d_substitutions:
            lines.append("- **Wave 2 D-amino acid sites (future):**")
            for s in qc.wave2_d_substitutions:
                lines.append(f"  - {s}")

        if qc.flags:
            lines.append("- **QC flags:**")
            for flag in qc.flags:
                lines.append(f"  - ⚠ {flag}")
        else:
            lines.append("- **QC flags:** None")
        lines.append("")

    lines += [
        "## Wave 2 D-Amino Acid Substitution Guide",
        "",
        "For any Wave 1 candidate with interior trypsin sites and demonstrated MIC ≤ 16 μg/mL:",
        "",
        "1. Identify the `wave2_d_substitutions` positions (listed per-candidate above).",
        "2. Order D-Lys or D-Arg substituted variants from the same vendor.",
        "3. Expected serum t½ improvement: 3–10× (Wade et al. 1990 PNAS).",
        "4. Re-assay at same concentration range; compare MIC shift.",
        "",
        "## Disclaimer",
        "",
        "This checklist is computationally generated. QC flags are heuristic and do not",
        "guarantee synthesis success or biological activity. Always request vendor review",
        "for HIGH-difficulty sequences. No antimicrobial activity has been demonstrated",
        "until wet-lab confirmation.",
    ]

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

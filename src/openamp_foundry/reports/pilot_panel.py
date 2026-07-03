from __future__ import annotations

import csv
from pathlib import Path

_CSV_FIELDS = [
    "pilot_rank",
    "candidate_id",
    "sequence",
    "length",
    "seed",
    "ensemble",
    "activity",
    "boman_activity",
    "disagreement",
    "safety",
    "synthesis",
    "novelty",
    "serum_stability",
    "selectivity_proxy",
    "rich_selectivity",
    "pilot_priority",
    "amphipathic_score",
    "charge_ph74",
]

_DISCLAIMER = (
    "All scores are transparent physicochemical heuristics. "
    "No antimicrobial activity has been demonstrated in vitro or in vivo. "
    "These candidates are hypotheses for possible future expert review and assay only. "
    "Human expert review and institutional biosafety sign-off are required before synthesis."
)


def _row(c: dict) -> dict:
    scores = c.get("scores", {})
    features = c.get("features", {})

    def _f(key: str, fallback: float = 0.0) -> float:
        # Accept values from a nested scores dict OR directly on the row (CSV round-trip).
        v = scores.get(key, c.get(key, fallback))
        return float(v) if v is not None else fallback

    def _feat(key: str, fallback: float = 0.0) -> float:
        v = features.get(key, c.get(key, fallback))
        return float(v) if v is not None else fallback

    return {
        "pilot_rank": c.get("pilot_rank", ""),
        "candidate_id": c.get("candidate_id", ""),
        "sequence": c.get("sequence", ""),
        "length": len(c.get("sequence", "")),
        "seed": c.get("seed", ""),
        "ensemble": round(_f("ensemble"), 4),
        "activity": round(_f("activity"), 4),
        "boman_activity": round(_f("boman_activity"), 4),
        "disagreement": round(_f("disagreement"), 4),
        "safety": round(_f("safety"), 4),
        "synthesis": round(_f("synthesis"), 4),
        "novelty": round(_f("novelty"), 4),
        "serum_stability": round(_f("serum_stability"), 4),
        "selectivity_proxy": round(_f("selectivity_proxy", 1.0), 4),
        "rich_selectivity": round(_f("rich_selectivity", 0.5), 4),
        "pilot_priority": round(_f("pilot_priority"), 4),
        "amphipathic_score": round(_feat("helix_wheel_amphipathic_score"), 4),
        "charge_ph74": round(_feat("net_charge_ph74"), 4),
    }


def write_pilot_csv(panel: list[dict], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for c in panel:
            writer.writerow(_row(c))


def write_pilot_markdown(panel: list[dict], path: str | Path, generated_at: str = "") -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    seeds = sorted({c.get("seed", "") for c in panel})
    disagreements = [c.get("scores", {}).get("disagreement", 0.0) for c in panel]
    n_consensus = sum(1 for d in disagreements if d < 0.20)

    lines = [
        "# OpenAMP Foundry — Pilot Synthesis Panel",
        "",
        "> **Disclaimer:** " + _DISCLAIMER,
        "",
    ]
    if generated_at:
        lines += [f"Generated: {generated_at}", ""]

    lines += [
        f"**Panel size:** {len(panel)} candidates  ",
        f"**Seeds represented:** {len(seeds)} ({', '.join(seeds)})  ",
        f"**Dual-scorer consensus (disagreement < 0.20):** {n_consensus}/{len(panel)}  ",
        "",
        "## Selection method",
        "",
        "Priority score = `ensemble − 0.3 × disagreement + 0.05 × serum_stability + 0.05 × novelty + 0.05 × rich_selectivity`  ",
        "Rules: one representative per seed (highest priority), then remaining slots filled by priority rank.",
        "Stability, novelty, and rich_selectivity act as equal-weight tiebreakers (max ±0.05 each) — ensemble remains the dominant term.",
        "`rich_selectivity` (v0.5.16): evidence-based 8-feature composite (detection AUROC=0.7138, CI 0.63-0.80, significant). `selectivity_proxy` shown for comparison.",
        "",
        "## Candidates",
        "",
        "| # | ID | Sequence | Len | Seed | Ensemble | Activity | Boman | Disagree | Safety | Synth | SerumStab | Sel.Px | RichSel |",
        "|--:|---|---|--:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for c in panel:
        r = _row(c)
        lines.append(
            f"| {r['pilot_rank']} | {r['candidate_id']} | `{r['sequence']}` | {r['length']} "
            f"| {r['seed']} | {r['ensemble']} | {r['activity']} | {r['boman_activity']} "
            f"| {r['disagreement']} | {r['safety']} | {r['synthesis']} | {r['serum_stability']} "
            f"| {r['selectivity_proxy']} | {r['rich_selectivity']} |"
        )

    lines += [
        "",
        "## Next steps",
        "",
        "1. Human expert reviews this table and removes any sequences with known issues",
        "2. Institutional biosafety committee sign-off before ordering synthesis",
        "3. Synthesise selected peptides (SPPS, >95% purity, TFA-free if possible)",
        "4. MIC assay against target organism(s) in triplicate",
        "5. Hemolysis assay at 2× MIC against human erythrocytes",
        "6. Serum stability at 37°C, 0/2/4/8h timepoints",
        "7. Feed results back into pipeline for second-wave nomination",
        "",
        "## Reproducibility",
        "",
        "```bash",
        "make phase3   # regenerates the 89 nominees",
        "make pilot    # selects this panel from the nominees",
        "```",
        "",
        "Full methodology: `docs/NOMINATION_REPORT.md`",
    ]

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

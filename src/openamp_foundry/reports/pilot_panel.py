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
    "pilot_priority",
]

_DISCLAIMER = (
    "All scores are transparent physicochemical heuristics. "
    "No antimicrobial activity has been demonstrated in vitro or in vivo. "
    "These candidates are hypotheses for possible future expert review and assay only. "
    "Human expert review and institutional biosafety sign-off are required before synthesis."
)


def _row(c: dict) -> dict:
    scores = c.get("scores", {})
    return {
        "pilot_rank": c.get("pilot_rank", ""),
        "candidate_id": c.get("candidate_id", ""),
        "sequence": c.get("sequence", ""),
        "length": len(c.get("sequence", "")),
        "seed": c.get("seed", ""),
        "ensemble": round(scores.get("ensemble", 0.0), 4),
        "activity": round(scores.get("activity", 0.0), 4),
        "boman_activity": round(scores.get("boman_activity", 0.0), 4),
        "disagreement": round(scores.get("disagreement", 0.0), 4),
        "safety": round(scores.get("safety", 0.0), 4),
        "synthesis": round(scores.get("synthesis", 0.0), 4),
        "novelty": round(scores.get("novelty", 0.0), 4),
        "pilot_priority": round(c.get("pilot_priority", 0.0), 4),
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
        "Priority score = `ensemble − 0.3 × disagreement`  ",
        "Rules: one representative per seed (highest priority), then remaining slots filled by priority rank.",
        "",
        "## Candidates",
        "",
        "| # | ID | Sequence | Len | Seed | Ensemble | Activity | Boman | Disagree | Safety | Synth |",
        "|--:|---|---|--:|---|---:|---:|---:|---:|---:|---:|",
    ]

    for c in panel:
        r = _row(c)
        lines.append(
            f"| {r['pilot_rank']} | {r['candidate_id']} | `{r['sequence']}` | {r['length']} "
            f"| {r['seed']} | {r['ensemble']} | {r['activity']} | {r['boman_activity']} "
            f"| {r['disagreement']} | {r['safety']} | {r['synthesis']} |"
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
        f"Full methodology: `docs/NOMINATION_REPORT.md`",
    ]

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

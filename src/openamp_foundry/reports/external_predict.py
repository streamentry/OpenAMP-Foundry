"""Generate an external-predictor checklist for the pilot panel.

This module produces:
  1. A FASTA file of pilot sequences for batch submission to web-based AMP predictors
  2. A markdown checklist that walks through each tool and records results
  3. A confidence summary after results are recorded

We do NOT call external APIs automatically. All submissions are manual — external
tools may change, require registration, or have usage policies. This module only
generates the submission package and result-tracking template.

Recommended tools (free, no registration required as of 2024):
  - CAMPR4:       http://www.camp3.bicnirrh.res.in/predict.php
  - AMPScanner v2: https://www.dveltri.com/ascan/v2/ascan.html
  - dbAMP 2.0:    https://awi.cuhk.edu.cn/dbAMP/predict.php
"""
from __future__ import annotations

from pathlib import Path

_TOOLS = [
    {
        "name": "CAMPR4",
        "url": "http://www.camp3.bicnirrh.res.in/predict.php",
        "method": "SVM + Random Forest + Artificial Neural Network + Decision Tree (ensemble vote)",
        "input": "Paste FASTA in the text box, select all four models, submit",
        "positive_label": "AMP",
        "note": "Use 'Predict' tab. Export CSV results.",
    },
    {
        "name": "AMPScanner v2.0",
        "url": "https://www.dveltri.com/ascan/v2/ascan.html",
        "method": "LSTM deep learning model trained on APD + UniProt non-AMPs",
        "input": "Paste FASTA or upload file, click 'Predict'",
        "positive_label": "Antimicrobial",
        "note": "Records probability score. Use threshold 0.5 for binary call.",
    },
    {
        "name": "dbAMP 2.0",
        "url": "https://awi.cuhk.edu.cn/dbAMP/predict.php",
        "method": "Random Forest on physicochemical + amino acid composition features",
        "input": "Paste FASTA, click 'Predict'",
        "positive_label": "AMP",
        "note": "Also reports predicted activity spectrum (antibacterial/antifungal/etc.).",
    },
]


def write_pilot_fasta(panel: list[dict], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for c in panel:
        rank = c.get("pilot_rank", "?")
        seed = c.get("seed", "?")
        cid = c.get("candidate_id", "?")
        lines.append(f">{cid}|rank={rank}|seed={seed}")
        lines.append(c.get("sequence", ""))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_external_predict_checklist(
    panel: list[dict],
    fasta_path: str | Path,
    out_path: str | Path,
    generated_at: str = "",
) -> None:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    n = len(panel)
    lines = [
        "# External Predictor Checklist — Pilot Panel",
        "",
        "> **Purpose:** Obtain independent AMP predictions from published web tools before",
        "> committing to synthesis. Only synthesise candidates predicted as AMP by ≥2 tools.",
        "",
    ]
    if generated_at:
        lines += [f"Generated: {generated_at}", ""]

    lines += [
        f"Panel size: **{n} candidates** from `{fasta_path}`",
        "",
        "## Step 1 — Submit FASTA to each tool",
        "",
        f"FASTA file: `{fasta_path}`",
        "",
    ]

    for i, tool in enumerate(_TOOLS, start=1):
        lines += [
            f"### Tool {i}: {tool['name']}",
            f"- URL: {tool['url']}",
            f"- Method: {tool['method']}",
            f"- How to submit: {tool['input']}",
            f"- Positive label: `{tool['positive_label']}`",
            f"- Note: {tool['note']}",
            "",
        ]

    lines += [
        "## Step 2 — Record results",
        "",
        "Fill in the table below after running all three tools. Mark each cell Y/N.",
        "",
        "| Rank | ID | Sequence | CAMPR4 | AMPScanner v2 | dbAMP | Tools Agree (≥2/3) |",
        "|--:|---|---|:---:|:---:|:---:|:---:|",
    ]
    for c in panel:
        r = c.get("pilot_rank", "?")
        cid = c.get("candidate_id", "?")
        seq = c.get("sequence", "?")
        lines.append(f"| {r} | {cid} | `{seq}` | ? | ? | ? | ? |")

    lines += [
        "",
        "## Step 3 — Filter to confident candidates",
        "",
        "After filling in the table, run:",
        "```bash",
        "make pilot-confident KEEP=<comma-separated IDs of candidates where Tools Agree = Y>",
        "```",
        "Example:",
        "```bash",
        "make pilot-confident KEEP=SEED-003_VAR_051,SEED-005_VAR_068,SEED-002_VAR_084",
        "```",
        "",
        "## Step 4 — Decision gate",
        "",
        "| Outcome | Action |",
        "|---|---|",
        "| ≥12 candidates have Tools Agree = Y | Proceed to synthesis with confident panel |",
        "| 6–11 candidates have Tools Agree = Y | Synthesise only agreed candidates (wave 1) |",
        "| < 6 candidates have Tools Agree = Y | STOP — scoring model may not be reliable; revisit |",
        "",
        "## Why this matters",
        "",
        "Our internal scorer (physicochemical heuristics + Boman index) disagreed with itself",
        "(mean |activity − boman_activity| = 0.31). Three independent published tools provide",
        "external calibration. If 2/3 external tools agree with our nomination, confidence rises",
        "substantially. If they disagree, it is cheaper to find out now (free) than at synthesis ($500+).",
        "",
        "## Disclaimer",
        "",
        "External tool predictions are also computational — not wet-lab evidence. Even with 3/3",
        "tool agreement, the expected in-vitro hit rate is 20–60%. Human expert review and",
        "institutional biosafety sign-off remain mandatory before synthesis.",
    ]

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_confident_panel(
    panel: list[dict],
    keep_ids: list[str],
    out_path: str | Path,
    generated_at: str = "",
) -> list[dict]:
    """Filter panel to only those IDs confirmed by external predictors."""
    from openamp_foundry.reports.pilot_panel import write_pilot_csv, write_pilot_markdown

    keep_set = set(keep_ids)
    confident = [dict(c) for c in panel if c.get("candidate_id") in keep_set]

    for rank, c in enumerate(confident, start=1):
        c["pilot_rank"] = rank

    base = Path(out_path)
    csv_path = base.with_suffix(".csv")
    md_path = base.with_suffix(".md")

    write_pilot_csv(confident, csv_path)
    write_pilot_markdown(confident, md_path, generated_at=generated_at)

    return confident

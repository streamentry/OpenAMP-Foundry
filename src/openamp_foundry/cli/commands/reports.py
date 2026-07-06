"""Reporting commands."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone


def _run_lab_result_report(args: argparse.Namespace) -> int:
    from openamp_foundry.reports.lab_result_report import (
        build_lab_result_report,
        write_lab_result_json,
        write_lab_result_markdown,
    )

    report = build_lab_result_report(args.results_dir)
    write_lab_result_json(report, args.out_json)
    if args.out_md:
        write_lab_result_markdown(report, args.out_md)
    print(
        json.dumps(
            {
                "status": "ok",
                "n_results": report["summary"].get("n_results", 0),
                "n_candidates": report.get("n_candidates", 0),
                "n_control_failures": len(report.get("control_failures", [])),
                "out_json": args.out_json,
                "out_md": args.out_md,
            },
            indent=2,
        )
    )
    return 0

def _run_reviewer_questionnaire(args: argparse.Namespace) -> int:
    import csv as _csv
    import json as _json
    from pathlib import Path
    from openamp_foundry.qc.presynth_check import check_sequence

    panel = []
    with open(args.panel_csv, newline="", encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            panel.append(row)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    generated = []
    for c in panel:
        cid = c.get("candidate_id", "?")
        seq = c.get("sequence", "")
        try:
            qc = check_sequence(cid, seq)
        except Exception:
            qc = None
        flags = "\n".join(f"- {f}" for f in (qc.flags if qc else [])) if qc else "QC skipped"

        md = (
            f"# Reviewer Questionnaire — {cid}\n\n"
            f"**Generated:** {now}\n\n"
            f"## Candidate Metadata\n\n"
            f"| Field | Value |\n"
            f"|-------|-------|\n"
            f"| Candidate ID | {cid} |\n"
            f"| Sequence | `{seq}` |\n"
            f"| Length | {len(seq)} AA |\n\n"
            f"## QC Flags\n\n{flags if flags else '*No flags*'}\n\n"
            f"## Reviewer Assessment\n\n"
            f"### 1. Sequence Review\n"
            f"- [ ] Any obvious synthesis issues?\n"
            f"- [ ] Any motifs of concern?\n\n"
            f"### 2. Novelty Assessment\n"
            f"- [ ] Do you agree with the novelty classification?\n"
            f"- [ ] Is the best-match reference appropriate?\n\n"
            f"### 3. Safety Assessment\n"
            f"- [ ] Hemolysis risk acceptable?\n"
            f"- [ ] Cytotoxicity flags addressed?\n\n"
            f"### 4. Overall Recommendation\n\n"
            f"- [ ] **APPROVE** — proceed to synthesis\n"
            f"- [ ] **CONDITIONAL** — proceed with noted changes\n"
            f"- [ ] **REJECT** — do not synthesise\n\n"
            f"### Reviewer\n\n"
            f"| Field | Value |\n"
            f"|-------|-------|\n"
            f"| Name | |\n"
            f"| Institution | |\n"
            f"| Date | |\n"
            f"| Signature | |\n"
        )
        out_path = out_dir / f"{cid}_questionnaire.md"
        out_path.write_text(md, encoding="utf-8")
        generated.append(cid)

    print(_json.dumps({
        "status": "ok",
        "n_candidates": len(generated),
        "out_dir": str(out_dir),
    }, indent=2))
    return 0


def _run_ip_report(args: argparse.Namespace) -> int:
    import csv as _csv
    import json as _json
    from pathlib import Path

    # Load novelty data
    candidates = []
    with open(args.novelty_csv, newline="", encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            candidates.append(row)

    # Group by category
    by_cat = defaultdict(list)
    for c in candidates:
        by_cat[c.get("category", "NOVEL")].append(c)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    n_strong = len(by_cat.get("HIGH_CONFIDENCE_NOVEL", []))
    n_novel = len(by_cat.get("NOVEL", []))
    n_control = len(by_cat.get("KNOWN_VARIANT", [])) + len(by_cat.get("CLOSE_RELATIVE", []))

    lines = [
        "# IP Report — Novelty Claim Strength",
        "",
        f"> **Generated:** {now}",
        f"> **Panel:** {len(candidates)} candidates",
        "> **Novelty source:** `outputs/novelty_audit_full.csv`",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Claim tier | Count | Strategy |",
        "|------------|:-----:|----------|",
        f"| **Strong** (HIGH_CONFIDENCE_NOVEL) | {n_strong} | Primary patent claims; novelty unchallenged by 120-AMP library |",
        f"| **Moderate** (NOVEL) | {n_novel} | Conditional claims; verify mechanism distinction |",
        f"| **Control** (KNOWN_VARIANT + CLOSE_RELATIVE) | {n_control} | SAR controls; not individually patentable |",
        "",
        "## Claim Strength by Candidate",
        "",
        "| Candidate | Category | Best ref | Similarity | Claim strength |",
        "|-----------|----------|----------|:----------:|:--------------:|",
    ]
    for c in candidates:
        strength = {
            "HIGH_CONFIDENCE_NOVEL": "Strong",
            "NOVEL": "Moderate",
            "CLOSE_RELATIVE": "Weak (mechanism-dependent)",
            "KNOWN_VARIANT": "Not patentable (control/SAR)",
        }.get(c.get("category", ""), "Unknown")
        lines.append(
            f"| {c.get('candidate_id', '')} | {c.get('category', '')} "
            f"| {c.get('best_ref_family', '')} | {c.get('best_similarity', '')} "
            f"| {strength} |"
        )

    lines.extend([
        "",
        "## Candidate Categories per Seed Family",
        "",
        "| Seed | Strong claims | Moderate | Controls |",
        "|------|:-------------:|:---------:|:--------:|",
    ])
    seed_groups = defaultdict(lambda: {"strong": 0, "moderate": 0, "control": 0})
    for c in candidates:
        seed = c.get("seed", "?")
        cat = c.get("category", "")
        if cat == "HIGH_CONFIDENCE_NOVEL":
            seed_groups[seed]["strong"] += 1
        elif cat == "NOVEL":
            seed_groups[seed]["moderate"] += 1
        else:
            seed_groups[seed]["control"] += 1
    for seed, counts in sorted(seed_groups.items()):
        lines.append(f"| {seed} | {counts['strong']} | {counts['moderate']} | {counts['control']} |")

    lines.extend([
        "",
        "## Recommendations",
        "",
        "1. **File provisional patents** for HIGH_CONFIDENCE_NOVEL candidates before public disclosure.",
        "2. **Sequence deposit** in patent filing for all Strong and Moderate candidates.",
        "3. **Freedom-to-operate** search required for all candidates before publication.",
        "4. Keep control sequences (KNOWN_VARIANT, CLOSE_RELATIVE) in publication as SAR context.",
        "5. Do not disclose exact lead sequences publicly until IP path is decided.",
        "",
        "## Limitations",
        "",
        "- This report is a **computational novelty assessment**, not a legal patentability opinion.",
        "- Full prior-art search (APD3, DRAMP, patent databases) is required before filing.",
        "- Competitor sequence database (AMP-Designer, AMPGAN v3, LSSAMP, etc.) not yet checked.",
        "- See `docs/evidence/NOVELTY_CHECKLIST.md` for a step-by-step external verification guide.",
    ])

    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(_json.dumps({
        "status": "ok",
        "n_candidates": len(candidates),
        "n_strong": n_strong,
        "n_novel": n_novel,
        "n_control": n_control,
        "out": args.out,
    }, indent=2))
    return 0


def _run_batch_pack(args: argparse.Namespace) -> int:
    from openamp_foundry.reports.batch_pack import generate_batch_pack, write_batch_pack_markdown
    from openamp_foundry.utils.io import write_json

    pack = generate_batch_pack(
        ranked_jsonl_path=args.ranked,
        diversity_threshold=args.diversity_threshold,
    )
    write_json(args.out_json, pack)
    if args.out_md:
        write_batch_pack_markdown(pack, args.out_md)

    print(json.dumps({
        "status": "ok",
        "n_selected": pack["summary"]["n_candidates_selected"],
        "n_clusters": pack["summary"]["n_diversity_clusters"],
        "mean_novelty": pack["summary"]["mean_novelty"],
        "mean_safety": pack["summary"]["mean_safety"],
        "mean_synthesis": pack["summary"]["mean_synthesis"],
        "out_json": args.out_json,
        "out_md": args.out_md,
    }, indent=2))
    return 0


def _run_gold_standard(args: argparse.Namespace) -> int:
    import csv as _csv
    from openamp_foundry.features.physchem import compute_features
    from openamp_foundry.scoring.activity import activity_likeness_score
    from openamp_foundry.scoring.safety import safety_score
    from openamp_foundry.scoring.boman import boman_activity_score
    from openamp_foundry.scoring.ensemble import ensemble_score
    from openamp_foundry.config import load_config

    config = load_config(args.config)
    weights = config["weights"]

    GOLD_STANDARDS = [
        ("Melittin", "GIGAVLKVLTTGLPALISWIKRKRQQ", "Apis mellifera venom; hemolytic benchmark"),
        ("Magainin-2", "GIGKFLHSAKKFGKAFVGEIMNS", "Xenopus laevis frog skin; classical AMP"),
        ("LL-37", "LLGDFFRKSKEKIGKEFKRIVQRIKDFLRNLVPRTES", "Human cathelicidin; broad-spectrum"),
        ("Cecropin-A", "KWKLFKKIEKVGQNIRDGIIKAGPAVAVVGQATQIAK", "Silk moth immunity; pioneer AMP"),
        ("Defensin-HNP1", "ACYCRIPACIAGERRYGTCIYQGRLWAFCC", "Human neutrophil; β-sheet structure"),
        ("Polymyxin-B1", "XBDAXBBTBXBT", "Cyclic lipopeptide; last-resort MDR — placeholder"),
        ("Temporin-A", "FLPLIGRVLSGIL", "Frog skin; short helix; similar to SEED-004"),
    ]

    def _score(seq: str) -> dict:
        feats = compute_features(seq)
        act = activity_likeness_score(feats)
        safe = safety_score(feats)
        from openamp_foundry.scoring.synthesis import synthesis_feasibility_score
        from openamp_foundry.scoring.novelty import novelty_score
        synth = synthesis_feasibility_score(feats, valid_sequence=True)
        nov, _ = novelty_score(seq, [])
        boman = boman_activity_score(seq)
        raw = {"activity": act, "safety": safe, "synthesis": synth,
               "novelty": nov, "boman_activity": boman, "disagreement": abs(act - boman)}
        ens = ensemble_score(raw, weights)
        return {"activity": round(act, 3), "safety": round(safe, 3),
                "ensemble": round(ens, 3), "mu_h": round(feats.get("hydrophobic_moment", 0.0), 3)}

    panel = []
    with open(args.panel_csv, newline="", encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            panel.append(row)

    panel_scores = [
        {
            "id": r["candidate_id"],
            "seq": r["sequence"],
            "ensemble": float(r["ensemble"]),
            "activity": float(r["activity"]),
            "safety": float(r["safety"]),
        }
        for r in panel
    ]
    panel_ens = [p["ensemble"] for p in panel_scores]
    panel_min, panel_max = min(panel_ens), max(panel_ens)
    panel_mean = sum(panel_ens) / len(panel_ens)

    generated_at = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Gold-Standard Calibration",
        "",
        "> How do known literature AMPs score in the same pipeline as our candidates?",
        "> This confirms that our scoring is calibrated against validated actives.",
        "",
        f"Generated: {generated_at}",
        "",
        "## Confident panel score range (reference)",
        "",
        f"- Min ensemble: {panel_min:.3f}",
        f"- Max ensemble: {panel_max:.3f}",
        f"- Mean ensemble: {panel_mean:.3f}",
        "",
        "## Known AMP gold standards",
        "",
        "| Name | Sequence | Activity | Safety | Ensemble | μH | Note |",
        "|---|---|:---:|:---:|:---:|:---:|---|",
    ]

    gold_rows = []
    for name, seq, note in GOLD_STANDARDS:
        # Skip sequences with invalid AA (polymyxin placeholder)
        if any(c not in "ACDEFGHIKLMNPQRSTVWY" for c in seq.upper()):
            lines.append(f"| {name} | `{seq}` | — | — | — | — | {note} (non-standard AA; skipped) |")
            continue
        sc = _score(seq)
        vs_panel = (
            "ABOVE panel" if sc["ensemble"] > panel_max else
            "WITHIN panel range" if sc["ensemble"] >= panel_min else
            "BELOW panel"
        )
        lines.append(
            f"| {name} | `{seq[:20]}{'...' if len(seq)>20 else ''}` "
            f"| {sc['activity']} | {sc['safety']} | {sc['ensemble']} "
            f"| {sc['mu_h']} | {note} ({vs_panel}) |"
        )
        gold_rows.append((name, sc))

    lines += [
        "",
        "## Interpretation",
        "",
        "If known active AMPs score **within or below** the panel's ensemble range, the",
        "scoring is calibrated correctly — it values properties that literature validates.",
        "If known AMPs score *far above* the panel, the panel may be under-optimised.",
        "If known AMPs score *far below*, the panel may be over-scoring on non-AMP features.",
        "",
        "## Panel candidates for reference",
        "",
        "| ID | Ensemble | Activity | Safety |",
        "|---|:---:|:---:|:---:|",
    ]
    for p in sorted(panel_scores, key=lambda x: x["ensemble"], reverse=True):
        lines.append(f"| {p['id']} | {p['ensemble']:.3f} | {p['activity']:.3f} | {p['safety']:.3f} |")

    lines += [
        "",
        "## Blind spots (documented)",
        "",
        "- **Melittin** — hemolytic benchmark; high safety penalty (μH > 0.8) is expected and correct.",
        "- **Defensin-HNP1** — β-sheet disulfide peptide; our scorer targets α-helical AMPs; lower score expected.",
        "- **Polymyxin B** — cyclic lipopeptide with non-standard AA; not scorable by this pipeline.",
        "- **Temporin-A** (`FLPLIGRVLSGIL`) — similar scaffold to SEED-004; should score comparably.",
        "",
        "## Disclaimer",
        "",
        "This calibration uses the same scoring model as candidate nomination. It is not",
        "independent validation — it confirms internal consistency, not external predictive power.",
        "The AUROC benchmark (AUROC=0.7832 on 95 literature AMPs vs 96 background peptides; expanded PR #110) is",
        "the appropriate independent validation.",
    ]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "panel_range": [panel_min, panel_max],
        "panel_mean": panel_mean,
        "n_gold_scored": len(gold_rows),
        "out": args.out,
    }, indent=2))
    return 0


def _run_novelty_check_broad(args: argparse.Namespace) -> int:
    """Compare pilot panel candidates against a curated AMP reference database.

    The standard novelty score compares against ~45 seed sequences only.  This command
    uses a broader curated reference set (default: 72 published AMPs) to detect whether
    any candidates are near-copies of known AMPs that the seed-based score missed.

    Classification thresholds (Levenshtein similarity):
      KNOWN_VARIANT  >= threshold_known (default 0.70): effectively a known AMP
      CLOSE_RELATIVE >= threshold_close (default 0.50): close relative of known AMP
      NOVEL          < threshold_close: no close match in reference database
    """
    import csv as _csv
    from openamp_foundry.scoring.novelty import normalized_similarity

    # Load panel
    panel_path = Path(args.panel_csv)
    if not panel_path.exists():
        print(json.dumps({"status": "error", "message": f"panel CSV not found: {args.panel_csv}"}))
        return 1

    with open(panel_path, newline="", encoding="utf-8") as f:
        panel = list(_csv.DictReader(f))

    if not panel:
        print(json.dumps({"status": "error", "message": "panel CSV is empty"}))
        return 1

    # Load references
    refs_path = Path(args.references_csv)
    if not refs_path.exists():
        print(json.dumps({"status": "error", "message": f"references CSV not found: {args.references_csv}"}))
        return 1

    refs: list[dict] = []
    seen_seqs: set[str] = set()
    with open(refs_path, newline="", encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            seq = row.get("sequence", "").strip().upper()
            if seq and seq not in seen_seqs:
                seen_seqs.add(seq)
                refs.append({
                    "id": row.get("id", row.get("candidate_id", "?")),
                    "sequence": seq,
                    "family": row.get("family", "unknown"),
                    "reference": row.get("reference", ""),
                })

    if not refs:
        print(json.dumps({"status": "error", "message": "references CSV has no valid sequences"}))
        return 1

    thr_known = args.threshold_known
    thr_close = args.threshold_close

    if thr_close >= thr_known:
        print(json.dumps({
            "status": "error",
            "message": (
                f"threshold-close ({thr_close}) must be less than threshold-known ({thr_known}); "
                "the classification cascade would make CLOSE_RELATIVE unreachable"
            ),
        }))
        return 1

    import sys as _sys

    # Score each candidate
    results = []
    n_known = 0
    n_close = 0
    n_novel = 0

    for row in panel:
        cid = row.get("candidate_id", "?")
        seq = row.get("sequence", "").strip().upper()
        if not seq:
            print(f"WARNING: candidate {cid!r} has an empty sequence — skipping", file=_sys.stderr)
            continue
        seed = row.get("seed", "?")
        seed_novelty = float(row.get("novelty") or 0.0)
        ensemble = float(row.get("ensemble") or 0.0)

        best_sim = -1.0
        best_ref: dict = {}
        for ref in refs:
            s = normalized_similarity(seq, ref["sequence"])
            if s > best_sim:
                best_sim = s
                best_ref = ref

        best_sim = max(best_sim, 0.0)

        broad_novelty = round(1.0 - best_sim, 4)

        if best_sim >= thr_known:
            category = "KNOWN_VARIANT"
            n_known += 1
        elif best_sim >= thr_close:
            category = "CLOSE_RELATIVE"
            n_close += 1
        else:
            category = "NOVEL"
            n_novel += 1

        results.append({
            "candidate_id": cid,
            "sequence": seq,
            "seed": seed,
            "ensemble": ensemble,
            "seed_novelty": seed_novelty,
            "broad_similarity": round(best_sim, 4),
            "broad_novelty": broad_novelty,
            "best_match_id": best_ref.get("id", ""),
            "best_match_seq": best_ref.get("sequence", ""),
            "best_match_family": best_ref.get("family", ""),
            "best_match_reference": best_ref.get("reference", ""),
            "category": category,
        })

    # Build markdown report
    ts = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Broad Novelty Check — Pilot Panel vs Curated AMP Database",
        "",
        f"> Generated: {ts}  ",
        f"> Panel: {args.panel_csv}  ",
        f"> Reference database: {args.references_csv} ({len(refs)} unique sequences)  ",
        f"> Thresholds: KNOWN_VARIANT ≥ {thr_known:.0%}, CLOSE_RELATIVE ≥ {thr_close:.0%}",
        "",
        "## Purpose",
        "",
        "The standard pipeline novelty score compares candidates against ~45 seed sequences.",
        "This report extends the comparison to the curated AMP reference database to detect",
        "near-copies of published AMPs that the seed-based novelty score may miss.",
        "",
        "## Summary",
        "",
        "| Category | Count | Description |",
        "|---|:---:|---|",
        f"| KNOWN_VARIANT | {n_known} | ≥{thr_known:.0%} similar to a known published AMP |",
        f"| CLOSE_RELATIVE | {n_close} | {thr_close:.0%}–{thr_known:.0%} similar to a known AMP |",
        f"| NOVEL | {n_novel} | <{thr_close:.0%} similar — no close match in reference database |",
        f"| **Total** | **{len(results)}** | |",
        "",
        "## Per-Candidate Results",
        "",
        "| Rank | Candidate | Sequence | Seed | Ensemble | Seed-Novelty | Broad-Sim | Best-Match | Category |",
        "|--:|---|---|---|:---:|:---:|:---:|---|---|",
    ]

    for i, r in enumerate(results, 1):
        cat_icon = {"KNOWN_VARIANT": "⚠ KNOWN", "CLOSE_RELATIVE": "≈ CLOSE", "NOVEL": "✓ NOVEL"}[r["category"]]
        match_str = f"{r['best_match_id']} ({r['best_match_family']})" if r["best_match_id"] else "—"
        lines.append(
            f"| {i} | {r['candidate_id']} | `{r['sequence']}` | {r['seed']} "
            f"| {r['ensemble']:.3f} | {r['seed_novelty']:.3f} | {r['broad_similarity']:.3f} "
            f"| {match_str} | {cat_icon} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "### KNOWN_VARIANT candidates",
        "",
    ]

    known_rows = [r for r in results if r["category"] == "KNOWN_VARIANT"]
    if known_rows:
        for r in known_rows:
            lines += [
                f"**{r['candidate_id']}** (`{r['sequence']}`) — {r['broad_similarity']:.1%} similar "
                f"to {r['best_match_id']} ({r['best_match_family']}; {r['best_match_reference']}).  ",
                "The published AMP provides strong activity precedent for this candidate.",
                "Wet-lab value: confirms assay platform works; novelty claim limited.",
                "",
            ]
    else:
        lines += ["No KNOWN_VARIANT candidates found.", ""]

    lines += [
        "### CLOSE_RELATIVE candidates",
        "",
    ]
    close_rows = [r for r in results if r["category"] == "CLOSE_RELATIVE"]
    if close_rows:
        for r in close_rows:
            lines += [
                f"**{r['candidate_id']}** (`{r['sequence']}`) — {r['broad_similarity']:.1%} similar "
                f"to {r['best_match_id']} ({r['best_match_family']}).  ",
                "Related to a known AMP but with meaningful sequence differences. "
                "Activity probability elevated; novelty moderate.",
                "",
            ]
    else:
        lines += ["No CLOSE_RELATIVE candidates found.", ""]

    lines += [
        "### NOVEL candidates",
        "",
        f"{n_novel} candidates have <{thr_close:.0%} similarity to any sequence in the "
        f"{len(refs)}-sequence reference database.  ",
        "These represent the most scientifically novel fraction of the panel.",
        "Discovery of activity in this subset would be publishable as a novel AMP class.",
        "",
        "## Recommendations",
        "",
        "1. **KNOWN_VARIANT candidates** should be de-emphasised in novelty claims but retained "
        "as positive controls that validate the assay platform.",
    ]

    novel_seeds = sorted({r["seed"] for r in results if r["category"] == "NOVEL"})
    novel_seed_str = ", ".join(novel_seeds) if novel_seeds else "none"
    lines += [
        f"2. **NOVEL candidates** (from seeds: {novel_seed_str}) are the primary discovery "
        "targets. Any confirmed activity in this subset is publishable as a novel AMP.",
        "3. This report should be submitted with the ASSAY_PREREGISTRATION.md to document "
        "the novelty status of all candidates before wet-lab results are seen.",
        "",
        "## Caveat",
        "",
        "This comparison uses a curated 72-sequence reference database. A full BLASTp search "
        "against APD3 (>3,800 sequences), DRAMP v3.0 (>22,000 sequences), or dbAMP would be "
        "more comprehensive. Perform APD3 BLASTp of NOVEL candidates before publication to "
        "confirm novelty claims. See ROADMAP.md §'Beyond v1.0'.",
    ]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = {
        "status": "ok",
        "n_candidates": len(results),
        "n_references": len(refs),
        "n_known_variant": n_known,
        "n_close_relative": n_close,
        "n_novel": n_novel,
        "out": args.out,
    }
    print(json.dumps(summary, indent=2))
    return 0


def _run_calibration_intake(args: argparse.Namespace) -> int:
    """Build a calibration intake report from a pilot panel CSV + lab results."""
    from openamp_foundry.calibration.intake import (
        build_calibration_intake_report,
        write_calibration_intake_json,
        write_calibration_intake_markdown,
    )

    report = build_calibration_intake_report(args.panel, args.results_dir)
    write_calibration_intake_json(report, args.out_json)
    if args.out_md:
        write_calibration_intake_markdown(report, args.out_md)

    cohort_summary = {}
    for key, metric in report["cohort_metrics"].items():
        cohort_summary[key] = {
            "n": metric["n"],
            "insufficient_data": metric["insufficient_data"],
        }

    print(
        json.dumps(
            {
                "status": "ok",
                "n_panel_candidates": report["n_panel_candidates"],
                "n_lab_results": report["n_lab_results"],
                "n_matched_candidates": report["n_matched_candidates"],
                "n_orphan_lab_results": report["n_orphan_lab_results"],
                "cohort_metrics": cohort_summary,
                "out_json": args.out_json,
                "out_md": args.out_md,
                "disclaimer_excerpt": report["report_disclaimer"][:80] + "...",
            },
            indent=2,
        )
    )
    return 0


def _run_recalibration_gate(args: argparse.Namespace) -> int:
    """Evaluate the recalibration gate against an intake report + policy."""
    import json
    from pathlib import Path

    from openamp_foundry.calibration.policy import load_recalibration_policy
    from openamp_foundry.calibration.recalibration_gate import (
        evaluate_recalibration_gate,
        write_gate_verdict_json,
        write_gate_verdict_markdown,
    )

    intake_path = Path(args.intake_report)
    if not intake_path.exists():
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": f"intake report not found: {intake_path}",
                },
                indent=2,
            )
        )
        return 2

    with intake_path.open() as f:
        intake_report = json.load(f)

    try:
        policy = load_recalibration_policy(args.policy)
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": f"failed to load policy {args.policy!r}: {exc}",
                },
                indent=2,
            )
        )
        return 2

    previous_recalibration_at = args.previous_recalibration_at
    candidate_weight_l1_distance = args.weight_l1_distance
    if candidate_weight_l1_distance is not None:
        try:
            candidate_weight_l1_distance = float(candidate_weight_l1_distance)
        except (TypeError, ValueError):
            print(
                json.dumps(
                    {
                        "status": "error",
                        "error": (
                            "weight-l1-distance must be a float, got "
                            f"{args.weight_l1_distance!r}"
                        ),
                    },
                    indent=2,
                )
            )
            return 2

    project_root = Path(args.project_root) if args.project_root else Path.cwd()

    verdict = evaluate_recalibration_gate(
        intake_report,
        policy,
        intake_report_date=args.intake_report_date,
        previous_recalibration_at=previous_recalibration_at,
        candidate_weight_l1_distance=candidate_weight_l1_distance,
        project_root=project_root,
    )

    if args.out_json:
        write_gate_verdict_json(verdict, args.out_json)
    if args.out_md:
        write_gate_verdict_markdown(
            verdict,
            args.out_md,
            intake_report_path=str(intake_path),
            policy_path=str(args.policy),
        )

    # Avoid dumping nested arrays into the CLI stdout twice. Keep stdout concise.
    cli_summary = {
        "status": "ok",
        "may_recalibrate": verdict.may_recalibrate,
        "policy_version": verdict.policy_version,
        "policy_locked_at": verdict.policy_locked_at,
        "intake_report": str(intake_path),
        "policy": str(args.policy),
        "n_panel_candidates": verdict.n_panel_candidates,
        "n_lab_results": verdict.n_lab_results,
        "n_matched_candidates": verdict.n_matched_candidates,
        "rule_results": [
            {"rule_id": r.rule_id, "passed": r.passed, "observed": r.observed,
             "threshold": r.threshold, "reason": r.reason}
            for r in verdict.rule_results
        ],
        "rate_limit_status": [
            {"rule_id": s.rule_id, "status": s.status, "observed": s.observed,
             "threshold": s.threshold, "note": s.note}
            for s in verdict.rate_limit_status
        ],
        "reviewer_artefact_status": [
            {"artefact_id": s.artefact_id, "present": s.present,
             "expected_path": s.expected_path, "note": s.note}
            for s in verdict.reviewer_artefact_status
        ],
        "prohibited_action_count": len(verdict.prohibited_action_audit),
        "reasons": list(verdict.reasons),
        "summary": verdict.summary,
        "out_json": args.out_json,
        "out_md": args.out_md,
    }
    print(json.dumps(cli_summary, indent=2))
    # Exit code: 0 if may_recalibrate, 3 otherwise.
    return 0 if verdict.may_recalibrate else 3


def _run_recalibration_engine(args: argparse.Namespace) -> int:
    """Compute proposed weight deltas from intake + gate verdict.

    With ``--dry-run``, prints a human-readable diff table and skips all
    file writes. Without it, writes ``--out-json`` and/or ``--out-md``
    if specified. Neither mode applies changes.
    """
    intake_path = Path(args.intake_report)
    if not intake_path.exists():
        payload = {
            "status": "error",
            "error": f"Intake report not found: {intake_path}",
        }
        print(json.dumps(payload))
        return 2

    gate_path = Path(args.gate_verdict)
    if not gate_path.exists():
        payload = {
            "status": "error",
            "error": f"Gate verdict not found: {gate_path}",
        }
        print(json.dumps(payload))
        return 2

    from openamp_foundry.calibration.engine import (
        BudgetExceededError,
        PolicyViolationError,
        compute_weight_update,
    )
    from openamp_foundry.calibration.recalibration_gate import GateVerdict

    intake = json.loads(intake_path.read_text())
    gate_data = json.loads(gate_path.read_text())
    current_weights = json.loads(args.current_weights)
    l1_budget = args.l1_budget

    # Reconstruct GateVerdict from JSON
    gate_verdict = GateVerdict(
        may_recalibrate=gate_data["may_recalibrate"],
        policy_version=gate_data.get("policy_version", 0),
        policy_locked_at=gate_data.get("policy_locked_at", ""),
        intake_report_path=gate_data.get("intake_report_path", ""),
        n_panel_candidates=gate_data.get("n_panel_candidates", 0),
        n_matched_candidates=gate_data.get("n_matched_candidates", 0),
        n_lab_results=gate_data.get("n_lab_results", 0),
        rule_results=(),
        prohibited_action_audit=(),
        rate_limit_status=(),
        reviewer_artefact_status=(),
        reasons=tuple(gate_data.get("reasons", [])),
        summary=gate_data.get("summary", ""),
    )

    from openamp_foundry.reports.recalibration_report import (
        build_recalibration_report,
        write_recalibration_report_json,
        write_recalibration_report_markdown,
    )

    try:
        proposal = compute_weight_update(
            intake_report=intake,
            gate_verdict=gate_verdict,
            current_weights=current_weights,
            policy_l1_budget=l1_budget,
        )
    except PolicyViolationError as e:
        payload = {
            "status": "error",
            "error": str(e),
            "may_recalibrate": False,
        }
        print(json.dumps(payload))
        return 3
    except BudgetExceededError as e:
        payload = {
            "status": "budget_exceeded",
            "error": str(e),
        }
        print(json.dumps(payload))
        return 3

    # Build the combined recalibration report (proposal + gate verdict)
    report = build_recalibration_report(proposal, gate_verdict)
    prop_section = report.get("proposal", {})

    is_dry_run = getattr(args, "dry_run", False)
    dry_run_label = " [DRY RUN — no changes applied]" if is_dry_run else ""

    if is_dry_run:
        # Print diff table instead of writing files
        print(f"Recalibration Engine Proposal{dry_run_label}")
        print(f"{'=' * 60}")
        print(f"  Timestamp:      {report['timestamp']}")
        print(f"  Report type:    {report['report_type']}")
        print(f"  Schema version: {report['schema_version']}")
        print(f"  Policy version: {report['policy_version']}")
        print(f"  Gate passed:    {prop_section.get('gate_passed')}")
        print(f"  L1 total:       {prop_section.get('l1_total', 0):.4f} / budget {prop_section.get('l1_budget', 0):.4f}")
        print(f"  L1 within budget: {prop_section.get('l1_within_budget')}")
        gv = report.get("gate_verdict", {})
        n_rules = len(gv.get("rule_results", []))
        n_actions = len(gv.get("prohibited_action_audit", []))
        print(f"  Gate rules:     {n_rules} minimum conditions, {n_actions} prohibited actions")
        print()
        print(f"  {'Scorer':<20} {'Current':>8} {'Proposed':>8} {'Delta':>8}  {'Rationale'}")
        print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8}  {'-'*40}")
        for d in prop_section.get("deltas", []):
            sign = "+" if d["delta"] >= 0 else ""
            print(f"  {d['scorer']:<20} {d['current_weight']:>8.4f} {d['proposed_weight']:>8.4f} {sign}{d['delta']:>7.4f}  {d['rationale'][:60]}")
        print()
        print(f"  N deltas: {len(prop_section.get('deltas', []))}")
        notes = prop_section.get("notes", [])
        print(f"  Notes: {', '.join(notes) if notes else '(none)'}")
        print(f"{'=' * 60}")
        print("DRY RUN — no files written, no weight changes applied.")
    else:
        if args.out_json:
            write_recalibration_report_json(report, args.out_json)
        if args.out_md:
            write_recalibration_report_markdown(report, args.out_md)

    summary = {
        "status": "ok",
        "report_type": "recalibration_report",
        "schema_version": "1.0",
        "gate_passed": prop_section.get("gate_passed"),
        "n_deltas": len(prop_section.get("deltas", [])),
        "l1_total": round(prop_section.get("l1_total", 0), 4),
        "l1_within_budget": prop_section.get("l1_within_budget"),
        "timestamp": report["timestamp"],
        "human_review_required": True,
        "dry_run": is_dry_run,
    }
    print(json.dumps(summary, indent=2))
    return 0


def _run_validate_policy_version(args: argparse.Namespace) -> int:
    """Validate a proposed policy version against its predecessor."""
    from openamp_foundry.calibration.policy import load_recalibration_policy
    from openamp_foundry.calibration.policy_version import validate_policy_version

    current_path = Path(args.current_policy)
    previous_path = Path(args.previous_policy)

    if not current_path.exists():
        payload = {
            "status": "error",
            "error": f"Current policy not found: {current_path}",
        }
        print(json.dumps(payload))
        return 2

    if not previous_path.exists():
        payload = {
            "status": "error",
            "error": f"Previous policy not found: {previous_path}",
        }
        print(json.dumps(payload))
        return 2

    current_policy = load_recalibration_policy(current_path)
    previous_policy = load_recalibration_policy(previous_path)

    result = validate_policy_version(
        current_policy=current_policy,
        previous_policy=previous_policy,
        decision_log_dir=args.decision_log_dir,
        today=args.today,
    )

    payload = {
        "status": "valid" if result.passed else "invalid",
        "passed": result.passed,
        "version_valid": result.version_valid,
        "locked_changes_preserved": result.locked_changes_preserved,
        "decision_log_valid": result.decision_log_valid,
        "reasons": list(result.reasons),
    }
    print(json.dumps(payload, indent=2))
    return 0 if result.passed else 3

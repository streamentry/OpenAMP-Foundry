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

    try:
        report = build_lab_result_report(args.results_dir)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 2

    write_lab_result_json(report, args.out_json)
    if args.out_md:
        write_lab_result_markdown(report, args.out_md)
    print(
        json.dumps(
            {
                "status": (
                    "blocked"
                    if report.get("n_invalid_lab_result_files", 0)
                    or report.get("n_duplicate_lab_result_ids", 0)
                    else "ok"
                ),
                "n_results": report["summary"].get("n_results", 0),
                "n_candidates": report.get("n_candidates", 0),
                "n_invalid_lab_result_files": report.get(
                    "n_invalid_lab_result_files", 0
                ),
                "n_duplicate_lab_result_ids": report.get(
                    "n_duplicate_lab_result_ids", 0
                ),
                "n_control_failures": len(report.get("control_failures", [])),
                "out_json": args.out_json,
                "out_md": args.out_md,
            },
            indent=2,
        )
    )
    return (
        3
        if report.get("n_invalid_lab_result_files", 0)
        or report.get("n_duplicate_lab_result_ids", 0)
        else 0
    )

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
        "The standard pipeline novelty score compares against ~45 seed sequences.",
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

    try:
        report = build_calibration_intake_report(args.panel, args.results_dir)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 2

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
                "status": (
                    "blocked"
                    if report.get("n_invalid_lab_result_files", 0)
                    or report.get("input_integrity_issues", [])
                    else "ok"
                ),
                "n_panel_candidates": report["n_panel_candidates"],
                "n_lab_results": report["n_lab_results"],
                "n_matched_candidates": report["n_matched_candidates"],
                "n_orphan_lab_results": report["n_orphan_lab_results"],
                "n_invalid_lab_result_files": report.get(
                    "n_invalid_lab_result_files", 0
                ),
                "input_integrity_issues": report.get("input_integrity_issues", []),
                "input_validation_status": report.get(
                    "input_validation_status", "input_validated"
                ),
                "cohort_metrics": cohort_summary,
                "out_json": args.out_json,
                "out_md": args.out_md,
                "disclaimer_excerpt": report["report_disclaimer"][:80] + "...",
            },
            indent=2,
        )
    )
    return (
        3
        if report.get("n_invalid_lab_result_files", 0)
        or report.get("input_integrity_issues", [])
        else 0
    )


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
        "n_invalid_lab_result_files": verdict.n_invalid_lab_result_files,
        "n_input_integrity_issues": verdict.n_input_integrity_issues,
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


def _run_calibration_audit(args: argparse.Namespace) -> int:
    """Run a consistency audit across the calibration pipeline artifacts."""
    from openamp_foundry.calibration.audit import (
        run_calibration_audit,
        write_calibration_audit_json,
        write_calibration_audit_markdown,
    )

    audit = run_calibration_audit(
        intake_path=args.intake_report,
        gate_path=args.gate_verdict,
        engine_path=args.engine_proposal,
        report_path=args.recalibration_report,
    )

    if args.out_json:
        write_calibration_audit_json(audit, args.out_json)
    if args.out_md:
        write_calibration_audit_markdown(audit, args.out_md)

    cli_summary = {
        "status": "ok" if audit["overall_pass"] else "issues_found",
        "overall_pass": audit["overall_pass"],
        "n_checks": audit["n_checks"],
        "n_passed": audit["n_passed"],
        "n_failed": audit["n_failed"],
        "n_warnings": audit["n_warnings"],
        "artifacts_checked": audit["artifacts_checked"],
        "summary": audit["summary"],
        "out_json": args.out_json,
        "out_md": args.out_md,
    }
    print(json.dumps(cli_summary, indent=2))
    return 0 if audit["overall_pass"] else 3


def _run_calibration_overfit_check(args: argparse.Namespace) -> int:
    from openamp_foundry.calibration.overfit_warning import (
        run_overfit_check,
        write_overfit_check_json,
        write_overfit_check_markdown,
    )

    report = run_overfit_check(
        cohort_sizes=args.cohort_sizes,
        model_params=args.model_params,
        n_features=args.n_features,
        min_recommended=args.min_recommended,
    )
    if args.out_json:
        write_overfit_check_json(report, args.out_json)
    if args.out_md:
        write_overfit_check_markdown(report, args.out_md)

    print(json.dumps({
        "status": "ok",
        "worst_level": report["worst_level"],
        "any_critical": report["any_critical"],
        "any_warning": report["any_warning"],
        "n_cohorts": len(report["per_cohort"]),
        "out_json": args.out_json,
        "out_md": args.out_md,
    }, indent=2))
    return 0


def _run_synthetic_result_policy_check(args: argparse.Namespace) -> int:
    """Check whether synthetic/simulation results raise proof-ladder level."""
    from pathlib import Path
    from openamp_foundry.evidence.synthetic_result_policy import (
        check_synthetic_result_policy,
        run_policy_batch,
        write_policy_check_json,
        write_policy_check_markdown,
    )

    proposals_path = Path(args.proposals_json)
    if not proposals_path.exists():
        print(json.dumps({
            "status": "error",
            "error": f"proposals JSON not found: {proposals_path}",
        }))
        return 2

    with proposals_path.open() as f:
        proposals = json.load(f)

    if not isinstance(proposals, list):
        print(json.dumps({
            "status": "error",
            "error": "proposals JSON must be a list of {candidate_id, current_level, proposed_level, evidence_source} objects",
        }))
        return 2

    result = run_policy_batch(proposals)

    if args.out_json:
        write_policy_check_json(result, args.out_json)
    if args.out_md:
        write_policy_check_markdown(result, args.out_md)

    print(json.dumps({
        "status": "ok",
        "total": result["summary"]["total"],
        "passed": result["summary"]["passed"],
        "failed": result["summary"]["failed"],
        "any_violation": result["any_violation"],
        "dry_lab_only": result["dry_lab_only"],
        "out_json": args.out_json,
        "out_md": args.out_md,
    }, indent=2))
    return 3 if result["any_violation"] else 0


def _run_result_quality_filter(args: argparse.Namespace) -> int:
    """Filter lab results by quality flags for calibration eligibility."""
    import json
    from pathlib import Path

    from openamp_foundry.calibration.result_quality import (
        filter_results_for_calibration,
        write_result_quality_json,
        write_result_quality_markdown,
    )

    results_path = Path(args.results_json)
    if not results_path.exists():
        print(json.dumps({
            "status": "error",
            "error": f"results JSON not found: {results_path}",
        }))
        return 2

    with results_path.open() as f:
        results = json.load(f)

    if not isinstance(results, list):
        print(json.dumps({
            "status": "error",
            "error": "results JSON must be a list of {candidate_id, flags} objects",
        }))
        return 2

    filtered = filter_results_for_calibration(results)

    if args.out_json:
        write_result_quality_json(filtered, args.out_json)
    if args.out_md:
        write_result_quality_markdown(filtered, args.out_md)

    print(json.dumps({
        "status": "ok",
        "total": filtered["summary"]["total"],
        "included": filtered["summary"]["included"],
        "included_with_caution": filtered["summary"]["included_with_caution"],
        "excluded": filtered["summary"]["excluded"],
        "can_drive_update_count": filtered["can_drive_update_count"],
        "dry_lab_only": filtered["dry_lab_only"],
        "out_json": args.out_json,
        "out_md": args.out_md,
    }, indent=2))
    return 0


def _run_calibration_decision_checklist(args: argparse.Namespace) -> int:
    """Build a structured calibration decision review checklist."""
    import json
    from pathlib import Path

    from openamp_foundry.calibration.decision_checklist import (
        build_checklist,
        write_checklist_json,
        write_checklist_markdown,
    )

    responses_path = Path(args.responses_json)
    if not responses_path.exists():
        print(json.dumps({
            "status": "error",
            "error": f"responses JSON not found: {responses_path}",
        }))
        return 2

    with responses_path.open() as f:
        responses = json.load(f)

    if not isinstance(responses, dict):
        print(json.dumps({
            "status": "error",
            "error": "responses JSON must be a dict mapping item IDs to booleans",
        }))
        return 2

    try:
        checklist = build_checklist(
            checklist_id=args.checklist_id,
            date=args.date,
            reviewer=args.reviewer,
            responses=responses,
        )
    except ValueError as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        return 3

    if args.out_json:
        write_checklist_json(checklist, args.out_json)
    if args.out_md:
        write_checklist_markdown(checklist, args.out_md)

    print(json.dumps({
        "status": "ok",
        "checklist_id": checklist.checklist_id,
        "date": checklist.date,
        "reviewer": checklist.reviewer,
        "overall_pass": checklist.overall_pass,
        "missing_required": checklist.missing_required,
        "n_responses": len(checklist.responses),
        "dry_lab_only": checklist.dry_lab_only,
        "out_json": args.out_json,
        "out_md": args.out_md,
    }, indent=2))
    return 0 if checklist.overall_pass else 3


def _run_calibration_rollback_plan(args: argparse.Namespace) -> int:
    """Build and optionally write a recalibration rollback plan."""
    import json
    from pathlib import Path

    from openamp_foundry.calibration.rollback_plan import (
        build_rollback_plan,
        write_rollback_plan_json,
        write_rollback_plan_markdown,
    )

    triggered_by = [t.strip() for t in args.triggered_by.split(",") if t.strip()]

    try:
        plan = build_rollback_plan(
            plan_id=args.plan_id,
            version=args.version,
            triggered_by=triggered_by,
            notes=args.notes,
        )
    except ValueError as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        return 3

    if args.out_json:
        write_rollback_plan_json(plan, args.out_json)
    if args.out_md:
        write_rollback_plan_markdown(plan, args.out_md)

    print(json.dumps({
        "status": "ok",
        "plan_id": plan.plan_id,
        "version": plan.version,
        "triggered_by": plan.triggered_by,
        "n_steps": len(plan.steps),
        "dry_lab_only": plan.dry_lab_only,
        "out_json": args.out_json,
        "out_md": args.out_md,
    }, indent=2))
    return 0


def _run_validate_simulation_result(args: argparse.Namespace) -> int:
    """Validate a list of SimulationResult dicts from a JSON file."""
    import json
    from pathlib import Path

    from openamp_foundry.simulation.interfaces import SimulationResult
    from openamp_foundry.simulation.result_validator import (
        validate_simulation_result,
        validate_simulation_result_batch,
    )

    results_path = Path(args.results_json)
    if not results_path.exists():
        print(json.dumps({
            "status": "error",
            "error": f"results JSON not found: {results_path}",
        }))
        return 2

    with results_path.open() as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        print(json.dumps({
            "status": "error",
            "error": "results JSON must be a list of SimulationResult dicts",
        }))
        return 2

    results = []
    for item in raw:
        results.append(SimulationResult(
            module=item.get("module", ""),
            version=item.get("version", ""),
            scope=item.get("scope", []),
            scores=item.get("scores", {}),
            uncertainty=item.get("uncertainty", 0.0),
            calibration_set=item.get("calibration_set"),
            validated_against=item.get("validated_against", []),
            notes=item.get("notes", []),
        ))

    batch_result = validate_simulation_result_batch(results, strict=args.strict)

    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(batch_result, indent=2))

    print(json.dumps(batch_result, indent=2))
    return 3 if batch_result["any_invalid"] else 0


def _run_recalibration_decision_log_check(args):
    """CLI handler for recalibration-decision-log-check."""
    import json, sys
    from openamp_foundry.evidence.recalibration_decision_log import validate_dict
    data = json.load(open(args.input))
    issues = validate_dict(data)
    errors = [i for i in issues if not i.startswith("WARNING:")]
    warnings = [i for i in issues if i.startswith("WARNING:")]
    for w in warnings:
        print(w)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print("OK: RecalibrationDecisionLog is valid.")


def _run_recalibration_rejection_summary_check(args):
    """CLI handler for recalibration-rejection-summary-check."""
    import json, sys
    from openamp_foundry.evidence.recalibration_rejection_summary import validate_dict
    data = json.load(open(args.input))
    issues = validate_dict(data)
    errors = [i for i in issues if not i.startswith("WARNING:")]
    warnings = [i for i in issues if i.startswith("WARNING:")]
    for w in warnings:
        print(w)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print("OK: RecalibrationRejectionSummary is valid.")


def _run_proof_ladder_level_certificate_check(args):
    """CLI handler for proof-ladder-level-certificate-check."""
    import json, sys
    from openamp_foundry.evidence.proof_ladder_level_certificate import validate_dict
    data = json.load(open(args.input))
    issues = validate_dict(data)
    errors = [i for i in issues if not i.startswith("WARNING:")]
    warnings = [i for i in issues if i.startswith("WARNING:")]
    for w in warnings:
        print(w)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print("OK: ProofLadderLevelCertificate is valid.")


def _run_domain_review_outcome_check(args):
    from openamp_foundry.evidence.domain_review_outcome import (
        validate_domain_review_outcome_dict,
    )
    import json
    import sys

    data = json.loads(args.entry_json)
    result = validate_domain_review_outcome_dict(data)

    if args.format == "json":
        out = {
            "dro_id": result.dro_id,
            "pep_id": result.pep_id,
            "rvq_id": result.rvq_id,
            "review_domain": result.review_domain,
            "outcome_verdict": result.outcome_verdict,
            "outcome_confidence": result.outcome_confidence,
            "passed": result.passed,
            "errors": result.errors,
            "warnings": result.warnings,
            "dry_lab_only": result.dry_lab_only,
        }
        print(json.dumps(out, indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Domain Review Outcome: {status}")
        print(f"  DRO ID: {result.dro_id}")
        print(f"  PEP ID: {result.pep_id}")
        print(f"  RVQ ID: {result.rvq_id}")
        print(f"  Domain: {result.review_domain}")
        print(f"  Verdict: {result.outcome_verdict}")
        print(f"  Confidence: {result.outcome_confidence}")
        if result.errors:
            print("  Errors:")
            for e in result.errors:
                print(f"    - {e}")
        if result.warnings:
            print("  Warnings:")
            for w in result.warnings:
                print(f"    - {w}")

    sys.exit(0 if result.passed else 1)


def _run_pilot_package_completeness_check(args):
    import json, sys
    from openamp_foundry.evidence.pilot_package_completeness_report import validate_dict
    try:
        data = json.loads(args.json_input)
    except json.JSONDecodeError as exc:
        print(f"INVALID: JSON parse error: {exc}", file=sys.stderr)
        sys.exit(1)
    result = validate_dict(data)
    if result.valid:
        print("VALID")
        for w in result.warnings:
            print(f"WARNING: {w}")
    else:
        print("INVALID")
        for e in result.errors:
            print(f"ERROR: {e}")
        for w in result.warnings:
            print(f"WARNING: {w}")
        sys.exit(1)


def _run_simulation_registry(args: argparse.Namespace) -> int:
    """Display simulation module registry information."""
    from openamp_foundry.simulation.module_registry import (
        SIMULATION_MODULE_REGISTRY,
        get_module_entry,
        list_module_entries,
        registry_summary,
        VALID_STATUSES,
    )

    PROOF_LADDER_LABELS = {
        1: "computational nomination",
        2: "virtual-assay support",
        3: "in-silico ensemble agreement",
        4: "ex-vivo preliminary",
        5: "in-vivo preliminary",
        6: "clinical evidence",
    }

    show = getattr(args, "show", None)
    status_filter = getattr(args, "status", None)
    min_evidence = getattr(args, "min_evidence", None)
    output_format = getattr(args, "format", "text")

    if show:
        entry = get_module_entry(show)
        if entry is None:
            print(json.dumps({"status": "error", "error": f"Unknown module_id: '{show}'"}))
            return 3
        if output_format == "json":
            print(json.dumps({
                "module_id": entry.module_id,
                "name": entry.name,
                "description": entry.description,
                "status": entry.status,
                "evidence_level": entry.evidence_level,
                "evidence_label": PROOF_LADDER_LABELS.get(entry.evidence_level, "unknown"),
                "baseline_comparison": entry.baseline_comparison,
                "scope": entry.scope,
                "maintainer": entry.maintainer,
                "notes": entry.notes,
            }, indent=2))
        else:
            label = PROOF_LADDER_LABELS.get(entry.evidence_level, "unknown")
            print(f"Module: {entry.module_id}")
            print(f"  Name:               {entry.name}")
            print(f"  Description:        {entry.description}")
            print(f"  Status:             {entry.status}")
            print(f"  Evidence Level:     {entry.evidence_level} ({label})")
            print(f"  Baseline:           {entry.baseline_comparison}")
            print(f"  Scope:              {', '.join(entry.scope)}")
            print(f"  Maintainer:         {entry.maintainer}")
            if entry.notes:
                print(f"  Notes:              {entry.notes}")
    return 0


def _run_simulation_baseline_check(args: argparse.Namespace) -> int:
    """Check whether a simulation module beats its cheapest declared baseline."""
    from openamp_foundry.simulation.baseline_registry import (
        check_baseline_requirement,
        get_baseline_declaration,
    )

    module_id = args.module_id
    claimed_level = args.claimed_level
    baseline_beaten = args.baseline_beaten.lower() == "true"
    output_format = getattr(args, "format", "text")

    entry = get_baseline_declaration(module_id)
    if entry is None:
        print(json.dumps({
            "status": "error",
            "error": f"Unknown module_id '{module_id}'. Use --list to see available modules.",
        }))
        return 3

    result = check_baseline_requirement(module_id, claimed_level, baseline_beaten)

    if output_format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Baseline Check: {module_id}")
        print(f"  Module:                 {entry.module_name}")
        print(f"  Baseline:               {entry.baseline_description}")
        print(f"  Baseline type:          {entry.baseline_type}")
        print(f"  Evidence level ceiling: {entry.evidence_level_ceiling}")
        print(f"  Baseline beaten:        {baseline_beaten}")
        print(f"  Claimed evidence level: {claimed_level}")
        print(f"  Effective evidence:     {result['effective_evidence_level']}")
        print(f"  Capped:                 {result['capped']}")
        print(f"  Message:                {result['message']}")
        print()
        print("Dry-lab only. Baseline comparisons are computational benchmarks,")
        print("not biological proof.")

    return 3 if result["capped"] else 0


def _run_adapter_gate_check(args: argparse.Namespace) -> int:
    """Fail-closed adapter gate check for simulation adapters."""
    from openamp_foundry.simulation.adapter_gate import evaluate_adapter_gate

    module_id = args.module_id
    timeout_occurred = args.timeout.lower() == "true"
    connection_refused = args.connection_refused.lower() == "true"
    module_unavailable = args.module_unavailable.lower() == "true"
    output_format = getattr(args, "format", "text")

    schema_errors_raw = args.schema_errors
    try:
        schema_errors = json.loads(schema_errors_raw) if schema_errors_raw else []
    except (json.JSONDecodeError, TypeError):
        print(json.dumps({
            "status": "error",
            "error": f"Invalid JSON for --schema-errors: {schema_errors_raw!r}",
        }))
        return 2

    if not isinstance(schema_errors, list):
        print(json.dumps({
            "status": "error",
            "error": "--schema-errors must be a JSON array of strings",
        }))
        return 2

    baseline_beaten_raw = args.baseline_beaten
    baseline_beaten = None
    if baseline_beaten_raw is not None:
        baseline_beaten = baseline_beaten_raw.lower() == "true"

    gate_result = evaluate_adapter_gate(
        module_id=module_id,
        result=None,
        timeout_occurred=timeout_occurred,
        connection_refused=connection_refused,
        schema_errors=schema_errors,
        module_unavailable=module_unavailable,
        baseline_beaten=baseline_beaten,
    )

    if output_format == "json":
        print(json.dumps(gate_result.to_dict(), indent=2))
    else:
        status = "PASS" if gate_result.passed else "FAIL"
        print(f"Adapter Gate Check: {module_id}")
        print(f"  Status:  {status}")
        if gate_result.failure_reason:
            print(
                f"  Reason: {gate_result.failure_reason} — "
                f"{gate_result.failure_detail}"
            )
        print()
        print("Dry-lab only. Adapter gate checks are computational safeguards,")
        print("not biological proof.")

    return 0 if gate_result.passed else 3


def _run_simulation_ensemble_check(args: argparse.Namespace) -> int:
    """Check agreement across multiple simulation results for a sequence."""
    import json

    from openamp_foundry.simulation.ensemble_checker import (
        check_ensemble_agreement,
    )
    from openamp_foundry.simulation.interfaces import SimulationResult

    sequence = args.sequence
    output_format = getattr(args, "format", "text")
    score_key = args.score_key
    threshold = args.threshold

    try:
        raw_results = json.loads(args.results_json)
    except (json.JSONDecodeError, TypeError) as e:
        print(json.dumps({
            "status": "error",
            "error": f"Invalid JSON for --results-json: {e}",
        }))
        return 2

    if not isinstance(raw_results, list):
        print(json.dumps({
            "status": "error",
            "error": "--results-json must be a JSON array of SimulationResult dicts",
        }))
        return 2

    results = []
    for item in raw_results:
        results.append(SimulationResult(
            module=item.get("module", ""),
            version=item.get("version", ""),
            scope=item.get("scope", []),
            scores=item.get("scores", {}),
            uncertainty=item.get("uncertainty", 0.0),
            calibration_set=item.get("calibration_set"),
            validated_against=item.get("validated_against", []),
            notes=item.get("notes", []),
        ))

    agreement = check_ensemble_agreement(
        sequence=sequence,
        results=results,
        score_key=score_key,
        agreement_threshold=threshold,
    )

    if output_format == "json":
        print(json.dumps(agreement, indent=2))
    else:
        verdict = "AGREEMENT" if agreement["within_agreement"] else "DISAGREEMENT"
        print(f"Simulation Ensemble Check — {verdict}")
        print(f"  Sequence:       {sequence}")
        print(f"  Score key:      {score_key}")
        print(f"  N results:      {agreement['n_results']}")
        print(f"  Score range:    {agreement['score_range']}")
        print(f"  Threshold:      {agreement['agreement_threshold']}")
        print(f"  Within limit:   {agreement['within_agreement']}")
        if agreement.get("disagreement_message"):
            print(f"  Message: {agreement['disagreement_message']}")
        print(f"  Dry-lab only:   {agreement['dry_lab_only']}")
        print()
        if agreement["within_agreement"]:
            print("Results agree within the threshold. This strengthens confidence.")
        else:
            print("Results disagree. Investigate module discrepancies before use.")

    return 0 if agreement["within_agreement"] else 3


def _run_reviewer_briefing_check(args: argparse.Namespace) -> int:
    """Validate a reviewer briefing package passed as JSON."""
    try:
        entry_dict = json.loads(args.entry_json)
    except json.JSONDecodeError as exc:
        print(json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(entry_dict, dict):
        print(json.dumps({
            "status": "error",
            "error": "--entry-json must be a JSON object",
        }))
        return 2

    from openamp_foundry.evidence.reviewer_briefing_package import (
        validate_reviewer_briefing_dict,
    )

    result = validate_reviewer_briefing_dict(entry_dict)
    if args.format == "json":
        import dataclasses

        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(
            f"[{status}] Reviewer Briefing Check: {result.briefing_id} "
            f"(reviewer: {result.reviewer_name})"
        )
        for error in result.errors:
            print(f"  ERROR: {error}")
        for warning in result.warnings:
            print(f"  WARN:  {warning}")
        if result.passed:
            print("  Reviewer briefing package validated.")

    return 0 if result.passed else 3


def _run_audit_chain_check(args: argparse.Namespace) -> int:
    """Validate the nine-link evidence audit chain."""
    entry_dict = json.loads(args.entry_json)
    from openamp_foundry.evidence.audit_chain_completeness import (
        validate_audit_chain_dict,
    )

    result = validate_audit_chain_dict(entry_dict)
    if args.format == "json":
        import dataclasses

        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(
            f"[{status}] Audit Chain Check: {result.chain_id} "
            f"({result.missing_link_count} gaps)"
        )
        for error in result.errors:
            print(f"  ERROR: {error}")
        for warning in result.warnings:
            print(f"  WARN:  {warning}")

    return 0 if result.passed else 3


def _run_phase_ac_disconfirming_gate_check(args: argparse.Namespace) -> int:
    """Build and report the Phase AC aggregate disconfirming-evidence gate."""
    import dataclasses

    from openamp_foundry.evidence.disconfirming_test_record import (
        build_disconfirming_test_record,
    )
    from openamp_foundry.evidence.phase_ac_disconfirming_gate import (
        build_phase_ac_disconfirming_gate,
        format_phase_ac_disconfirming_gate,
    )

    payload = json.loads(args.entry_json)
    records = [
        build_disconfirming_test_record(
            dtr_id=record["dtr_id"],
            pipeline_version=record["pipeline_version"],
            claim_tested=record["claim_tested"],
            test_type=record["test_type"],
            test_description=record["test_description"],
            test_outcome=record["test_outcome"],
            evidence_summary=record["evidence_summary"],
            limitations=record["limitations"],
            created_at=record["created_at"],
        )
        for record in payload["records"]
    ]
    gate = build_phase_ac_disconfirming_gate(
        acdg_id=payload["acdg_id"],
        pipeline_version=payload["pipeline_version"],
        records=records,
        resolved_dtr_ids=payload.get("resolved_dtr_ids", []),
        limitations=payload["limitations"],
        created_at=payload["created_at"],
    )

    if args.format == "json":
        print(json.dumps(dataclasses.asdict(gate), indent=2))
    else:
        status = "PASS" if gate.verdict == "disconfirming_evidence_verified" else "FAIL"
        print(f"[{status}] {format_phase_ac_disconfirming_gate(gate)}")

    return 0 if gate.verdict == "disconfirming_evidence_verified" else 3


def _run_phase_aa_reproducibility_gate_check(args: argparse.Namespace) -> int:
    """Build and report the Phase AA reproducibility gate."""
    import dataclasses

    from openamp_foundry.evidence.phase_aa_reproducibility_gate import (
        build_phase_aa_reproducibility_gate,
        format_phase_aa_reproducibility_gate,
    )

    payload = json.loads(args.entry_json)
    gate = build_phase_aa_reproducibility_gate(
        aarg_id=payload["aarg_id"],
        pipeline_version=payload["pipeline_version"],
        rmc_id=payload.get("rmc_id", ""),
        dcr_id=payload.get("dcr_id", ""),
        cfp_id=payload.get("cfp_id", ""),
        sbw_id=payload.get("sbw_id", ""),
        created_at=payload["created_at"],
    )

    if args.format == "json":
        print(json.dumps(dataclasses.asdict(gate), indent=2))
    else:
        status = "PASS" if gate.verdict == "reproducibility_verified" else "FAIL"
        print(f"[{status}] {format_phase_aa_reproducibility_gate(gate)}")

    return 0 if gate.verdict == "reproducibility_verified" else 3


def _run_scientific_review_readiness_check(args: argparse.Namespace) -> int:
    """Build and report the Phase R scientific-review readiness gate."""
    import dataclasses

    from openamp_foundry.evidence.scientific_review_readiness_gate import (
        build_scientific_review_readiness_gate,
        format_scientific_review_readiness_gate,
    )

    try:
        payload = json.loads(args.entry_json)
    except json.JSONDecodeError as exc:
        error = {"passed": False, "violations": [f"invalid JSON input: {exc}"]}
        if args.format == "json":
            print(json.dumps(error, indent=2))
        else:
            print("[FAIL] Scientific Review Readiness Check")
            print(f"  ERROR: {error['violations'][0]}")
        return 3

    try:
        gate = build_scientific_review_readiness_gate(
            srg_id=payload["srg_id"],
            candidate_family_id=payload["candidate_family_id"],
            cfc_id=payload["cfc_id"],
            fnr_id=payload["fnr_id"],
            atr_id=payload["atr_id"],
            pqg_id=payload["pqg_id"],
            readiness_verdict=payload["readiness_verdict"],
            safety_flags=payload.get("safety_flags", []),
            failed_gates=payload.get("failed_gates", []),
            review_scope=payload["review_scope"],
            n_confirmed_hits=payload["n_confirmed_hits"],
            n_total_candidates=payload["n_total_candidates"],
            limitations=payload["limitations"],
            notes=payload.get("notes", ""),
        )
    except (KeyError, TypeError, ValueError) as exc:
        error = {"passed": False, "violations": [f"invalid SRG input: {exc}"]}
        if args.format == "json":
            print(json.dumps(error, indent=2))
        else:
            print("[FAIL] Scientific Review Readiness Check")
            print(f"  ERROR: {error['violations'][0]}")
        return 3

    is_ready = gate.readiness_verdict == "ready_for_external_review"
    if args.format == "json":
        print(json.dumps({**dataclasses.asdict(gate), "passed": is_ready}, indent=2))
    else:
        status = "PASS" if is_ready else "FAIL"
        print(f"[{status}] {format_scientific_review_readiness_gate(gate)}")

    return 0 if is_ready else 3


def _run_phase_z_accountability_gate_check(args: argparse.Namespace) -> int:
    """Build and report the Phase Z per-family accountability gate."""
    import dataclasses

    from openamp_foundry.evidence.phase_z_accountability_gate import (
        build_phase_z_accountability_gate,
        format_phase_z_accountability_gate,
    )

    payload = json.loads(args.entry_json)
    gate = build_phase_z_accountability_gate(
        zag_id=payload["zag_id"],
        pipeline_version=payload["pipeline_version"],
        fbh_id=payload.get("fbh_id", ""),
        bxr_id=payload.get("bxr_id", ""),
        arg_id=payload.get("arg_id", ""),
        cbf_id=payload.get("cbf_id", ""),
        created_at=payload["created_at"],
    )

    if args.format == "json":
        print(json.dumps(dataclasses.asdict(gate), indent=2))
    else:
        status = "PASS" if gate.verdict == "accountability_verified" else "FAIL"
        print(f"[{status}] {format_phase_z_accountability_gate(gate)}")

    return 0 if gate.verdict == "accountability_verified" else 3


def _run_pre_registration_check(args: argparse.Namespace) -> int:
    """Validate a pre-registration form passed as JSON."""
    entry_dict = json.loads(args.entry_json)
    from openamp_foundry.evidence.pre_registration_form import (
        validate_pre_registration_dict,
    )

    result = validate_pre_registration_dict(entry_dict)
    if args.format == "json":
        import dataclasses

        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(
            f"[{status}] Pre-Registration Check: {result.registration_id} "
            f"({result.candidate_count} candidates, "
            f"metric: {result.primary_outcome_metric})"
        )
        for error in result.errors:
            print(f"  ERROR: {error}")
        for warning in result.warnings:
            print(f"  WARN:  {warning}")

    return 0 if result.passed else 3


def _run_simulation_ci_report(args: argparse.Namespace) -> int:
    """Compute confidence intervals and overlap report for simulation results."""
    import json

    from openamp_foundry.simulation.ci_reporter import ci_report
    from openamp_foundry.simulation.interfaces import SimulationResult

    output_format = getattr(args, "format", "text")
    score_key = args.score_key

    try:
        raw_results = json.loads(args.results_json)
    except (json.JSONDecodeError, TypeError) as e:
        print(json.dumps({
            "status": "error",
            "error": f"Invalid JSON for --results-json: {e}",
        }))
        return 2

    if not isinstance(raw_results, list):
        print(json.dumps({
            "status": "error",
            "error": "--results-json must be a JSON array of SimulationResult dicts",
        }))
        return 2

    results = []
    for item in raw_results:
        results.append(SimulationResult(
            module=item.get("module", ""),
            version=item.get("version", ""),
            scope=item.get("scope", []),
            scores=item.get("scores", {}),
            uncertainty=item.get("uncertainty", 0.0),
            calibration_set=item.get("calibration_set"),
            validated_against=item.get("validated_against", []),
            notes=item.get("notes", []),
        ))

    report = ci_report(results, score_key=score_key)

    if output_format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(f"Simulation Confidence Interval Report")
        print(f"  Score key:      {report['score_key']}")
        print(f"  N results:      {report['n_results']}")
        print(f"  Any overlap:    {report['any_overlap']}")
        print()
        for ci_dict in report["cis"]:
            ov = ", ".join(ci_dict["overlaps_with"]) if ci_dict["overlaps_with"] else "(none)"
            print(f"  [{ci_dict['module_id']}]")
            print(f"    Point estimate: {ci_dict['point_estimate']:.4f}")
            print(f"    Uncertainty:    {ci_dict['uncertainty']:.4f}")
            print(f"    CI:             [{ci_dict['ci_lower']:.4f}, {ci_dict['ci_upper']:.4f}]")
            print(f"    Width:          {ci_dict['ci_width']:.4f}")
            print(f"    Overlaps with:  {ov}")
            print()
        print("Dry-lab only. Confidence intervals are computational estimates,")
        print("not biological proof.")

    return 0


def _run_simulation_provenance(args: argparse.Namespace) -> int:
    """Generate and display a simulation-result provenance record."""
    import json

    from openamp_foundry.simulation.provenance import (
        make_provenance_record,
        validate_provenance_record,
    )

    run_id = args.run_id
    module_id = args.module_id
    module_version = args.module_version
    timestamp_utc = args.timestamp_utc
    input_sequence = args.input_sequence
    output_format = getattr(args, "format", "text")

    try:
        scores = json.loads(args.scores_json)
    except (json.JSONDecodeError, TypeError) as e:
        print(json.dumps({
            "status": "error",
            "error": f"Invalid JSON for --scores-json: {e}",
        }))
        return 2

    if not isinstance(scores, dict):
        print(json.dumps({
            "status": "error",
            "error": "--scores-json must be a JSON object (dict)",
        }))
        return 2

    calibration_set = getattr(args, "calibration_set", None)

    record = make_provenance_record(
        run_id=run_id,
        module_id=module_id,
        module_version=module_version,
        timestamp_utc=timestamp_utc,
        input_sequence=input_sequence,
        result_scores=scores,
        calibration_set=calibration_set,
    )

    validation_errors = validate_provenance_record(record)
    if validation_errors:
        print(json.dumps({
            "status": "validation_error",
            "errors": validation_errors,
        }))
        return 3

    if output_format == "json":
        print(json.dumps(record.to_dict(), indent=2))
    else:
        print(f"Simulation Provenance Record")
        print(f"  Run ID:          {record.run_id}")
        print(f"  Module:          {record.module_id} v{record.module_version}")
        print(f"  Timestamp (UTC): {record.timestamp_utc}")
        print(f"  Input hash:      {record.input_hash}")
        print(f"  Result hash:     {record.result_hash}")
        if record.calibration_set:
            print(f"  Calibration set: {record.calibration_set}")
        if record.notes:
            for note in record.notes:
                print(f"  Note:            {note}")
        print(f"  Dry-lab only:    {record.dry_lab_only}")
        print()
        print("Dry-lab only. Provenance records are computational audit trails,")
        print("not biological proof.")

    return 0


def _run_simulation_deprecation_check(args: argparse.Namespace) -> int:
    """Check whether simulation modules are deprecated or unavailable."""
    import json

    from openamp_foundry.simulation.deprecation_enforcer import (
        run_deprecation_check_batch,
    )

    module_ids = [m.strip() for m in args.module_ids.split(",") if m.strip()]
    if not module_ids:
        print(json.dumps({"status": "error", "error": "No module IDs provided."}))
        return 2

    result = run_deprecation_check_batch(module_ids)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Simulation Deprecation Check")
        print(f"  Total modules:  {result['total']}")
        print(f"  Blocked:        {result['blocked']}")
        print(f"  Allowed:        {result['allowed']}")
        print(f"  Any blocked:    {result['any_blocked']}")
        print()
        for check in result["results"]:
            status = "BLOCKED" if check["is_blocked"] else "ALLOWED"
            print(f"  [{status:7}] {check['module_id']:35s} "
                  f"status={check['status']:15s} "
                  f"{check['block_reason']}")
        print()
        print("Dry-lab only. Deprecation checks are computational safeguards,")
        print("not biological proof.")

    return 3 if result["any_blocked"] else 0


def _run_simulation_scope_check(args: argparse.Namespace) -> int:
    """Check whether a simulation module covers all requested scopes."""
    from openamp_foundry.simulation.scope_checker import (
        check_scope_coverage,
    )

    module_id = args.module_id
    requested_scopes = [s.strip() for s in args.requested_scopes.split(",") if s.strip()]
    output_format = getattr(args, "format", "text")

    if not requested_scopes:
        print({"status": "error", "error": "No scopes provided."})
        return 2

    result = check_scope_coverage(module_id, requested_scopes)

    if output_format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Simulation Scope Coverage Check: {module_id}")
        print(f"  Requested scopes: {', '.join(result.requested_scopes)}")
        print(f"  Module scopes:    {', '.join(result.module_scopes) if result.module_scopes else '(none)'}")
        print(f"  Covered:          {', '.join(result.covered) if result.covered else '(none)'}")
        print(f"  Uncovered:        {', '.join(result.uncovered) if result.uncovered else '(none)'}")
        print(f"  Coverage:         {result.coverage_fraction:.1%}")
        print(f"  Fully covered:    {result.is_fully_covered}")
        print()
        print("Dry-lab only. Scope coverage checks are computational safeguards,")
        print("not biological proof.")

    return 0 if result.is_fully_covered else 3


def _run_simulation_evidence_packet(args: argparse.Namespace) -> int:
    """Assemble all simulation discipline checks into a single evidence packet."""
    import json

    from openamp_foundry.simulation.evidence_packet import (
        assemble_evidence_packet,
        evidence_packet_summary,
    )
    from openamp_foundry.simulation.interfaces import SimulationResult

    module_id = args.module_id
    output_format = getattr(args, "format", "text")

    try:
        raw = json.loads(args.result_json)
    except (json.JSONDecodeError, TypeError) as e:
        print(json.dumps({
            "status": "error",
            "error": f"Invalid JSON for --result-json: {e}",
        }))
        return 2

    if not isinstance(raw, dict):
        print(json.dumps({
            "status": "error",
            "error": "--result-json must be a JSON object (SimulationResult dict)",
        }))
        return 2

    if raw.get("module") != module_id:
        print(json.dumps({
            "status": "error",
            "error": f"--module-id '{module_id}' does not match result.module '{raw.get('module')}'",
        }))
        return 2

    result = SimulationResult(
        module=raw.get("module", ""),
        version=raw.get("version", ""),
        scope=raw.get("scope", []),
        scores=raw.get("scores", {}),
        uncertainty=raw.get("uncertainty", 0.0),
        calibration_set=raw.get("calibration_set"),
        validated_against=raw.get("validated_against", []),
        notes=raw.get("notes", []),
    )

    requested_scopes = [s.strip() for s in args.requested_scopes.split(",") if s.strip()]
    claimed_level = args.claimed_level
    baseline_beaten = args.baseline_beaten.lower() == "true"

    packet = assemble_evidence_packet(
        result=result,
        requested_scopes=requested_scopes,
        claimed_evidence_level=claimed_level,
        baseline_beaten=baseline_beaten,
    )

    summary = evidence_packet_summary(packet)

    if output_format == "json":
        print(json.dumps(summary, indent=2))
    else:
        status = "PASS" if packet.all_checks_passed else "FAIL"
        print(f"Simulation Evidence Packet: {packet.module_id}")
        print(f"  Status:                 {status}")
        print(f"  Claimed evidence level: {packet.claimed_evidence_level}")
        print(f"  Effective evidence:     {packet.effective_evidence_level}")
        print(f"  All checks passed:      {packet.all_checks_passed}")
        if packet.failure_reasons:
            print("  Failure reasons:")
            for reason in packet.failure_reasons:
                print(f"    - {reason}")
        print(f"  Dry-lab only:           {packet.dry_lab_only}")
        print()
        print("Dry-lab only. Evidence packets are computational audit artifacts,")
        print("not biological proof.")

    return 0 if packet.all_checks_passed else 3


def _run_artifact_version(args: argparse.Namespace) -> int:
    """Display artifact versioning information."""
    from openamp_foundry.versioning.artifact_version import (
        STABILITY_TIERS,
        VERSIONED_ARTIFACTS,
        get_artifact_version,
        list_versioned_artifacts,
        artifact_version_summary,
    )

    show_name = getattr(args, "show", None)
    tier_filter = getattr(args, "tier", None)
    output_format = getattr(args, "format", "text")

    if show_name:
        entry = get_artifact_version(show_name)
        if entry is None:
            print(json.dumps({
                "status": "error",
                "error": f"Unknown artifact '{show_name}'. "
                         f"Use --list to see available artifacts.",
            }))
            return 3
        if output_format == "json":
            print(json.dumps({
                "artifact_name": entry.artifact_name,
                "version": entry.version,
                "stability_tier": entry.stability_tier,
                "schema_id": entry.schema_id,
                "description": entry.description,
                "is_breaking_change": entry.is_breaking_change,
                "notes": entry.notes,
            }, indent=2))
        else:
            tier_desc = STABILITY_TIERS.get(entry.stability_tier, entry.stability_tier)
            print(f"Artifact: {entry.artifact_name}")
            print(f"  Version:           {entry.version}")
            print(f"  Stability tier:    {tier_desc}")
            if entry.schema_id:
                print(f"  Schema $id:        {entry.schema_id}")
            print(f"  Description:       {entry.description}")
            print(f"  Breaking change:   {entry.is_breaking_change}")
            if entry.notes:
                print(f"  Notes:             {entry.notes}")
        return 0

    entries = list_versioned_artifacts(tier=tier_filter)
    summary = artifact_version_summary()

    if output_format == "json":
        print(json.dumps({
            "artifacts": [
                {
                    "artifact_name": e.artifact_name,
                    "version": e.version,
                    "stability_tier": e.stability_tier,
                    "schema_id": e.schema_id,
                    "description": e.description,
                }
                for e in entries
            ],
            "summary": summary,
        }, indent=2))
    else:
        print("Artifact Version Registry")
        print("=" * 60)
        print(f"Total artifacts: {summary['total']}")
        print(f"By tier:         {dict(sorted(summary['by_tier'].items()))}")
        print(f"Dry-lab only:    {summary['dry_lab_only']}")
        print()
        for entry in entries:
            sid = f"  $id: {entry.schema_id}" if entry.schema_id else ""
            print(f"  [{entry.stability_tier:12}] {entry.artifact_name:30s} v{entry.version}{sid}")
        print()
        print("Dry-lab only. Artifact versioning describes schema compatibility,")
        print("not biological validity, safety, or efficacy.")
        print("See docs/engineering/ARTIFACT_VERSIONING_POLICY.md for policy details.")

    return 0


def _run_candidate_manifest(args: argparse.Namespace) -> int:
    """Build and optionally validate a candidate manifest from CLI arguments."""
    from openamp_foundry.manifests.candidate_manifest import (
        make_candidate_manifest,
        manifest_to_dict,
        validate_candidate_manifest,
    )

    try:
        scores = json.loads(args.scores_json)
    except (json.JSONDecodeError, TypeError) as e:
        print(json.dumps({"status": "error", "error": f"Invalid --scores-json: {e}"}))
        return 2

    if not isinstance(scores, dict):
        print(json.dumps({"status": "error", "error": "--scores-json must be a JSON object"}))
        return 2

    scopes = [s.strip() for s in args.scopes.split(",") if s.strip()]
    source_modules = [s.strip() for s in args.source_modules.split(",") if s.strip()]

    try:
        evidence_level = int(args.evidence_level)
    except (TypeError, ValueError):
        print(json.dumps({"status": "error", "error": "--evidence-level must be an integer"}))
        return 2

    manifest = make_candidate_manifest(
        candidate_id=args.candidate_id,
        sequence=args.sequence,
        evidence_level=evidence_level,
        scopes=scopes,
        scores=scores,
        uncertainty=args.uncertainty,
        source_modules=source_modules,
    )

    validation_errors: list[str] = []
    if getattr(args, "validate", False):
        validation_errors = validate_candidate_manifest(manifest)

    output_format = getattr(args, "format", "text")
    if output_format == "json":
        result = manifest_to_dict(manifest)
        if validation_errors:
            result["validation_errors"] = validation_errors
            result["valid"] = len(validation_errors) == 0
        print(json.dumps(result, indent=2))
    else:
        print(f"Candidate Manifest: {manifest.candidate_id}")
        print(f"  Sequence:        {manifest.sequence}")
        print(f"  Evidence level:  {manifest.evidence_level}")
        print(f"  Scopes:          {', '.join(manifest.scopes)}")
        print(f"  Scores:          {manifest.scores}")
        print(f"  Uncertainty:     {manifest.uncertainty}")
        print(f"  Source modules:  {', '.join(manifest.source_modules)}")
        print(f"  Calibration set: {manifest.calibration_set}")
        print(f"  Safety flags:    {', '.join(manifest.safety_flags) if manifest.safety_flags else '(none)'}")
        print(f"  Provenance run:  {manifest.provenance_run_id}")
        print(f"  Dry-lab only:    {manifest.dry_lab_only}")
        print(f"  Version:         {manifest.version}")
        print(f"  Created at:      {manifest.created_at}")
        print(f"  Notes:           {len(manifest.notes)}")
        if validation_errors:
            print(f"  Validation:      {len(validation_errors)} error(s)")
            for err in validation_errors:
                print(f"    - {err}")
        else:
            print(f"  Validation:      passed")
        print()
        print("Dry-lab only. Candidate manifests are computational artifacts,")
        print("not biological proof.")

    if validation_errors:
        return 3
    return 0


def _run_benchmark_card(args: argparse.Namespace) -> int:
    """Build and optionally validate a benchmark card from CLI arguments."""
    from openamp_foundry.benchmarks.benchmark_card import (
        make_benchmark_card,
        validate_benchmark_card,
    )

    card = make_benchmark_card(
        benchmark_id=args.benchmark_id,
        benchmark_name=args.benchmark_name,
        metric=args.metric,
        metric_value=args.metric_value,
        baseline_name=args.baseline_name,
        baseline_value=args.baseline_value,
        dataset=args.dataset,
        dataset_size=args.dataset_size,
    )

    validation_errors: list[str] = []
    if getattr(args, "validate", False):
        validation_errors = validate_benchmark_card(card)

    output_format = getattr(args, "format", "text")
    if output_format == "json":
        result = {
            "benchmark_id": card.benchmark_id,
            "benchmark_name": card.benchmark_name,
            "version": card.version,
            "date": card.date,
            "metric": card.metric,
            "metric_value": card.metric_value,
            "baseline_name": card.baseline_name,
            "baseline_value": card.baseline_value,
            "delta": card.delta,
            "beats_baseline": card.beats_baseline,
            "dataset": card.dataset,
            "dataset_size": card.dataset_size,
            "scope": list(card.scope),
            "caveats": list(card.caveats),
            "dry_lab_only": card.dry_lab_only,
        }
        if validation_errors:
            result["validation_errors"] = validation_errors
            result["valid"] = len(validation_errors) == 0
        print(json.dumps(result, indent=2))
    else:
        print(f"Benchmark Card: {card.benchmark_id}")
        print(f"  Name:            {card.benchmark_name}")
        print(f"  Version:         {card.version}")
        print(f"  Date:            {card.date}")
        print(f"  Metric:          {card.metric} = {card.metric_value}")
        print(f"  Baseline:        {card.baseline_name} = {card.baseline_value}")
        print(f"  Delta:           {card.delta:+.6f}")
        print(f"  Beats baseline:  {card.beats_baseline}")
        print(f"  Dataset:         {card.dataset} ({card.dataset_size} samples)")
        print(f"  Scope:           {', '.join(card.scope)}")
        print(f"  Caveats:         {len(card.caveats)}")
        print(f"  Dry-lab only:    {card.dry_lab_only}")
        if validation_errors:
            print(f"  Validation:      {len(validation_errors)} error(s)")
            for err in validation_errors:
                print(f"    - {err}")
        else:
            print(f"  Validation:      passed")
        print()
        print("Dry-lab only. Benchmark cards are computational artifacts,")
        print("not biological proof.")

    if validation_errors:
        return 3
    return 0


def _run_artifact_changelog(args: argparse.Namespace) -> int:
    """Display evidence-certificate changelog entries."""
    from openamp_foundry.versioning.artifact_changelog import (
        ARTIFACT_CHANGELOG,
        get_changelog_entries,
        validate_changelog,
        changelog_summary,
    )

    artifact = getattr(args, "artifact", None)
    version = getattr(args, "version", None)
    change_type = getattr(args, "change_type", None)
    breaking_only = getattr(args, "breaking_only", False)
    output_format = getattr(args, "format", "text")

    entries = get_changelog_entries(
        artifact_name=artifact,
        version=version,
        change_type=change_type,
        breaking_only=breaking_only,
    )

    summary = changelog_summary()
    validation_errors = validate_changelog()

    if output_format == "json":
        result = {
            "entries": [
                {
                    "version": e.version,
                    "date": e.date,
                    "artifact_name": e.artifact_name,
                    "change_type": e.change_type,
                    "description": e.description,
                    "breaking": e.breaking,
                    "notes": e.notes,
                }
                for e in entries
            ],
            "summary": summary,
            "valid": len(validation_errors) == 0,
        }
        if validation_errors:
            result["validation_errors"] = validation_errors
        print(json.dumps(result, indent=2))
    else:
        print("Artifact Changelog")
        print("=" * 60)
        print(f"Total entries:  {summary['total']}")
        print(f"By change type: {dict(sorted(summary['by_change_type'].items()))}")
        print(f"Breaking:       {summary['breaking_changes']}")
        print(f"Artifacts:      {', '.join(summary['artifacts_covered'])}")
        print(f"Dry-lab only:   {summary['dry_lab_only']}")
        if validation_errors:
            print(f"Validation:     {len(validation_errors)} error(s)")
        else:
            print(f"Validation:     passed")
        print()
        for entry in entries:
            breaking_label = " [BREAKING]" if entry.breaking else ""
            print(f"  v{entry.version:8s} {entry.date}  "
                  f"[{entry.change_type:10s}]{breaking_label}")
            print(f"  {'':18s} {entry.artifact_name}")
            print(f"  {'':18s} {entry.description[:80]}")
            if entry.notes:
                print(f"  {'':18s} Notes: {entry.notes[:80]}")
            print()

        print("Dry-lab only. Changelog entries describe schema and format")
        print("changes, not biological validity, safety, or efficacy.")

    if validation_errors:
        return 3
    return 0


def _run_integration_check(args: argparse.Namespace) -> int:
    """Run integration checks against a candidate manifest dict."""
    from openamp_foundry.adoption.integration_checker import (
        run_integration_checks,
    )

    try:
        manifest_dict = json.loads(args.manifest_json)
    except (json.JSONDecodeError, TypeError) as e:
        print(json.dumps({"status": "error", "error": f"Invalid --manifest-json: {e}"}))
        return 2

    if not isinstance(manifest_dict, dict):
        print(json.dumps({"status": "error", "error": "--manifest-json must be a JSON object"}))
        return 2

    result = run_integration_checks(manifest_dict)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        print(json.dumps(result, indent=2))
    else:
        print("Integration Check Results")
        print("=" * 60)
        print(f"All checks passed: {result['all_passed']}")
        print(f"  Passed: {result['passed_count']} / Failed: {result['failed_count']}")
        print()
        for check in result["checks"]:
            status = "PASS" if check["passed"] else "FAIL"
            print(f"  [{status}] {check['check_name']}")
            print(f"          {check['detail']}")
        print()
        print("Dry-lab only. Integration checks are computational safeguards,")
        print("not biological proof.")

    return 0 if result["all_passed"] else 3


def _run_adapter_check(args: argparse.Namespace) -> int:
    """Validate an adapter declaration dict via the adapter author guide contract."""
    from openamp_foundry.adapters.adapter_validator import validate_adapter_dict

    try:
        adapter_dict = json.loads(args.adapter_json)
    except (json.JSONDecodeError, TypeError) as e:
        print(json.dumps({"status": "error", "error": f"Invalid --adapter-json: {e}"}))
        return 2

    if not isinstance(adapter_dict, dict):
        print(json.dumps({"status": "error", "error": "--adapter-json must be a JSON object"}))
        return 2

    result = validate_adapter_dict(adapter_dict)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        print(json.dumps({
            "adapter_id": result.adapter_id,
            "passed": result.passed,
            "errors": result.errors,
            "warnings": result.warnings_list,
            "dry_lab_only": result.dry_lab_only,
        }, indent=2))
    else:
        print("Adapter Declaration Check")
        print("=" * 60)
        print(f"Adapter ID:     {result.adapter_id}")
        print(f"Status:         {'PASS' if result.passed else 'FAIL'}")
        print()
        if result.errors:
            print("Errors:")
            for err in result.errors:
                print(f"  - {err}")
        if result.warnings_list:
            print("Warnings:")
            for w in result.warnings_list:
                print(f"  - {w}")
        print()
        print("Dry-lab only. Adapter validation is a computational safeguard,")
        print("not biological proof.")

    return 0 if result.passed else 3


def _run_license_check(args: argparse.Namespace) -> int:
    """Validate a data license declaration."""
    from openamp_foundry.licensing.license_checker import (
        DataLicenseDeclaration,
        check_data_license,
    )

    try:
        source_dict = json.loads(args.source_json)
    except (json.JSONDecodeError, TypeError) as e:
        print(json.dumps({"status": "error", "error": f"Invalid --source-json: {e}"}))
        return 2

    if not isinstance(source_dict, dict):
        print(json.dumps({"status": "error", "error": "--source-json must be a JSON object"}))
        return 2

    decl = DataLicenseDeclaration(**source_dict)
    result = check_data_license(decl)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        print(json.dumps({
            "source_id": result.source_id,
            "license_id": result.license_id,
            "use_context": result.use_context,
            "passed": result.passed,
            "status": result.status,
            "errors": result.errors,
            "warnings": result.warnings,
            "dry_lab_only": result.dry_lab_only,
        }, indent=2))
    else:
        print("License Check")
        print("=" * 60)
        print(f"Source ID:      {result.source_id}")
        print(f"License ID:     {result.license_id}")
        print(f"Use Context:    {result.use_context}")
        print(f"Status:         {result.status.upper()}")
        print(f"Result:         {'PASS' if result.passed else 'FAIL'}")
        print()
        if result.errors:
            print("Errors:")
            for err in result.errors:
                print(f"  - {err}")
        if result.warnings:
            print("Warnings:")
            for w in result.warnings:
                print(f"  - {w}")
        print()
        print("Dry-lab only. License checks are computational safeguards,")
        print("not legal advice.")

    return 0 if result.passed else 3


def _run_artifact_compat_check(args: argparse.Namespace) -> int:
    """Run cross-artifact schema compatibility checks."""
    from openamp_foundry.compatibility.artifact_compatibility import (
        run_compatibility_check,
    )

    schemas_dir = Path(args.schemas_dir) if args.schemas_dir else None
    report = run_compatibility_check(schemas_dir)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        print(json.dumps(report, indent=2))
    else:
        print("Artifact Compatibility Check")
        print("=" * 60)
        print(f"Total schemas:  {report['total']}")
        print(f"Passed:         {report['passed']}")
        print(f"Failed:         {report['failed']}")
        print(f"All passed:     {report['all_passed']}")
        print()
        if not report["all_passed"]:
            print("Failures:")
            for r in report["results"]:
                if not r["passed"]:
                    print(f"  Schema: {r['schema_name']}")
                    for err in r["errors"]:
                        print(f"    - {err}")
        print()
        print("Dry-lab only. Schema compatibility checks prevent drift")
        print("between artifact versions.")

    return 0 if report["all_passed"] else 3


def _run_contribution_check(args: argparse.Namespace) -> int:
    """Validate a contribution intake dict."""
    from openamp_foundry.community.contribution_intake import validate_intake_dict

    try:
        intake_dict = json.loads(args.intake_json)
    except (json.JSONDecodeError, TypeError) as e:
        print(json.dumps({"status": "error", "error": f"Invalid --intake-json: {e}"}))
        return 2

    if not isinstance(intake_dict, dict):
        print(json.dumps({"status": "error", "error": "--intake-json must be a JSON object"}))
        return 2

    result = validate_intake_dict(intake_dict)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        print(json.dumps({
            "institution_name": result.institution_name,
            "contribution_type": result.contribution_type,
            "passed": result.passed,
            "errors": result.errors,
            "warnings": result.warnings,
            "required_review_class": result.required_review_class,
            "dry_lab_only": result.dry_lab_only,
        }, indent=2))
    else:
        print("Contribution Intake Check")
        print("=" * 60)
        print(f"Institution:       {result.institution_name}")
        print(f"Contribution type: {result.contribution_type}")
        print(f"Review class:      {result.required_review_class}")
        print(f"Status:            {'PASS' if result.passed else 'FAIL'}")
        print()
        if result.errors:
            print("Errors:")
            for err in result.errors:
                print(f"  - {err}")
        if result.warnings:
            print("Warnings:")
            for w in result.warnings:
                print(f"  - {w}")
        print()
        print("Dry-lab only. Contribution intake checks are computational")
        print("safeguards, not biological proof.")

    return 0 if result.passed else 3


def _run_decision_log(args: argparse.Namespace) -> int:
    """Query and validate the governance decision log."""
    from openamp_foundry.governance.decision_log import (
        validate_all_decisions,
        get_decisions_by_scope,
        GOVERNANCE_DECISIONS,
    )
    import json as _json

    if args.validate:
        result = validate_all_decisions()
        if args.format == "json":
            print(_json.dumps(result, indent=2))
        else:
            print(f"Decision log validation: {result['total']} decisions")
            print(f"  Passed: {result['passed']}")
            print(f"  Failed: {result['failed']}")
            print(f"  All passed: {result['all_passed']}")
            if result["failed"] > 0:
                for r in result["results"]:
                    if not r["passed"]:
                        print(f"  FAIL: {r['decision_id']}")
                        for e in r["errors"]:
                            print(f"    - {e}")
            print(f"  dry_lab_only: {result['dry_lab_only']}")
        return 0 if result["all_passed"] else 3

    if args.scope:
        decisions = get_decisions_by_scope(args.scope)
        if args.format == "json":
            print(_json.dumps([vars(d) for d in decisions], indent=2))
        else:
            print(f"Decisions in scope '{args.scope}': {len(decisions)}")
            for d in decisions:
                print(f"  {d.decision_id} ({d.date}) — {d.decision}")
                print(f"    Status: {d.status}  Review: {d.review_class}")
        return 0

    # Default: list all
    if args.format == "json":
        print(_json.dumps([vars(d) for d in GOVERNANCE_DECISIONS], indent=2))
    else:
        print("Governance Decision Log")
        print("=" * 60)
        for d in GOVERNANCE_DECISIONS:
            print(f"  {d.decision_id} | {d.date} | {d.scope:15s} | {d.status:12s} | {d.review_class}")
            print(f"    {d.decision}")
        print(f"\nTotal: {len(GOVERNANCE_DECISIONS)} decisions  (dry_lab_only: True)")

    return 0


def _run_release_request_check(args: argparse.Namespace) -> int:
    """Validate a release request before human review."""
    from openamp_foundry.governance.release_request import validate_request_dict

    try:
        request_dict = json.loads(args.request_json)
    except (json.JSONDecodeError, TypeError) as e:
        print(json.dumps({"status": "error", "error": f"Invalid --request-json: {e}"}))
        return 2

    if not isinstance(request_dict, dict):
        print(json.dumps({"status": "error", "error": "--request-json must be a JSON object"}))
        return 2

    result = validate_request_dict(request_dict)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        print(json.dumps({
            "release_id": result.release_id,
            "release_type": result.release_type,
            "passed": result.passed,
            "errors": result.errors,
            "warnings": result.warnings,
            "dry_lab_only": result.dry_lab_only,
        }, indent=2))
    else:
        print("Release Request Check")
        print("=" * 60)
        print(f"Release ID:     {result.release_id}")
        print(f"Release type:   {result.release_type}")
        print(f"Status:         {'PASS' if result.passed else 'FAIL'}")
        print()
        if result.errors:
            print("Errors:")
            for err in result.errors:
                print(f"  - {err}")
        if result.warnings:
            print("Warnings:")
            for w in result.warnings:
                print(f"  - {w}")
        print()
        print("Dry-lab only. Release request validation is a computational")
        print("safeguard, not biological proof.")

    return 0 if result.passed else 3


def _run_coi_check(args: argparse.Namespace) -> int:
    """Validate a COI disclosure before the formal review queue."""
    from openamp_foundry.governance.coi_disclosure import validate_coi_dict

    try:
        disclosure_dict = json.loads(args.disclosure_json)
    except (json.JSONDecodeError, TypeError) as e:
        print(json.dumps({"status": "error", "error": f"Invalid --disclosure-json: {e}"}))
        return 2

    if not isinstance(disclosure_dict, dict):
        print(json.dumps({"status": "error", "error": "--disclosure-json must be a JSON object"}))
        return 2

    result = validate_coi_dict(disclosure_dict)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        print(json.dumps({
            "disclosure_id": result.disclosure_id,
            "disclosure_type": result.disclosure_type,
            "passed": result.passed,
            "errors": result.errors,
            "warnings": result.warnings,
            "dry_lab_only": result.dry_lab_only,
        }, indent=2))
    else:
        print("COI Disclosure Check")
        print("=" * 60)
        print(f"Disclosure ID:   {result.disclosure_id}")
        print(f"Disclosure type: {result.disclosure_type}")
        print(f"Status:          {'PASS' if result.passed else 'FAIL'}")
        print()
        if result.errors:
            print("Errors:")
            for err in result.errors:
                print(f"  - {err}")
        if result.warnings:
            print("Warnings:")
            for w in result.warnings:
                print(f"  - {w}")
        print()
        print("Dry-lab only. COI disclosure validation is a computational")
        print("safeguard, not a legal determination.")

    return 0 if result.passed else 3


def _run_adoption_scorecard(args: argparse.Namespace) -> int:
    """Build an adoption scorecard from dimension inputs."""
    from openamp_foundry.adoption.scorecard import build_scorecard

    try:
        dimension_inputs = json.loads(args.scores_json)
    except (json.JSONDecodeError, TypeError) as e:
        print(json.dumps({"status": "error", "error": f"Invalid --scores-json: {e}"}))
        return 2

    if not isinstance(dimension_inputs, dict):
        print(json.dumps({"status": "error", "error": "--scores-json must be a JSON object"}))
        return 2

    card = build_scorecard(dimension_inputs)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        print(json.dumps({
            "total_score": card.total_score,
            "adoption_tier": card.adoption_tier,
            "dimensions": [
                {
                    "dimension": d.dimension,
                    "weight": d.weight,
                    "raw_score": d.raw_score,
                    "weighted_score": d.weighted_score,
                    "passed_checks": d.passed_checks,
                    "total_checks": d.total_checks,
                    "notes": d.notes,
                    "dry_lab_only": d.dry_lab_only,
                }
                for d in card.dimensions
            ],
            "summary": card.summary,
            "recommendations": card.recommendations,
            "dry_lab_only": card.dry_lab_only,
        }, indent=2))
    else:
        print("Adoption Scorecard")
        print("=" * 60)
        print(f"Total score:     {card.total_score:.4f}")
        print(f"Adoption tier:   {card.adoption_tier}")
        print()
        print("Dimensions:")
        for d in card.dimensions:
            status = "PASS" if d.raw_score >= 1.0 else f"FAIL ({d.passed_checks}/{d.total_checks})"
            print(f"  {d.dimension:30s} {d.weight:.2f}w  raw={d.raw_score:.2f}  wtd={d.weighted_score:.3f}  {status}")
        print()
        print(f"Summary: {card.summary}")
        if card.recommendations:
            print()
            print("Recommendations:")
            for r in card.recommendations:
                print(f"  - {r}")
        print()
        print("Dry-lab only. Scorecard measures adoption readiness,")
        print("not biological validity.")

    return 0


def _run_rotation_plan_check(args: argparse.Namespace) -> int:
    """Validate a maintainer rotation plan for bus-factor coverage."""
    from openamp_foundry.governance.maintainer_rotation import validate_rotation_plan_dict

    try:
        plan_dict = json.loads(args.plan_json)
    except (json.JSONDecodeError, TypeError) as e:
        print(json.dumps({"status": "error", "error": f"Invalid --plan-json: {e}"}))
        return 2

    if not isinstance(plan_dict, dict):
        print(json.dumps({"status": "error", "error": "--plan-json must be a JSON object"}))
        return 2

    result = validate_rotation_plan_dict(plan_dict)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        print(json.dumps({
            "passed": result.passed,
            "errors": result.errors,
            "warnings": result.warnings,
            "maintainer_count": result.maintainer_count,
            "critical_role_coverage": result.critical_role_coverage,
            "bus_factor_sufficient": result.bus_factor_sufficient,
            "dry_lab_only": result.dry_lab_only,
        }, indent=2))
    else:
        print("Rotation Plan Check")
        print("=" * 60)
        print(f"Status:                   {'PASS' if result.passed else 'FAIL'}")
        print(f"Maintainer count:         {result.maintainer_count}")
        print(f"Bus-factor sufficient:    {result.bus_factor_sufficient}")
        print(f"Critical role coverage:   {result.critical_role_coverage}")
        print()
        if result.errors:
            print("Errors:")
            for err in result.errors:
                print(f"  - {err}")
        if result.warnings:
            print("Warnings:")
            for w in result.warnings:
                print(f"  - {w}")
        print()
        print("Dry-lab only. Rotation plan validation is a computational")
        print("governance check, not a legal determination.")

    return 0 if result.passed else 3


def _run_certificate_claim_boundary_check(args):
    """CLI handler for certificate-claim-boundary-check."""
    import json, sys
    from openamp_foundry.evidence.certificate_claim_boundary import validate_dict
    data = json.load(open(args.input))
    issues = validate_dict(data)
    errors = [i for i in issues if not i.startswith("WARNING:")]
    warnings = [i for i in issues if i.startswith("WARNING:")]
    for w in warnings:
        print(w)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print("OK: CertificateClaimBoundary is valid.")


def _run_security_report_check(args: argparse.Namespace) -> int:
    """Validate a security vulnerability report."""
    import json as _json
    from openamp_foundry.governance.security_policy import validate_report_dict

    try:
        d = _json.loads(args.report_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--report-json must be a JSON object"}))
        return 2

    result = validate_report_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Security report {result.report_id} ({result.severity}): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Report validated. Ready for maintainer review.")

    return 0 if result.passed else 3


def _run_citation_check(args: argparse.Namespace) -> int:
    """Validate a citation entry."""
    import json as _json
    from openamp_foundry.governance.citation_policy import validate_citation_dict

    try:
        d = _json.loads(args.citation_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--citation-json must be a JSON object"}))
        return 2

    result = validate_citation_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Citation entry {result.artifact_id} ({result.citation_type}): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Citation entry validated. Ready for publication reference.")

    return 0 if result.passed else 3


def _run_rejection_reason_check(args):
    from openamp_foundry.evidence.rejection_reason_entry import (
        validate_rejection_reason_dict,
    )
    import json
    import sys

    data = json.loads(args.entry_json)
    result = validate_rejection_reason_dict(data)

    if args.format == "json":
        out = {
            "rjr_id": result.rjr_id,
            "candidate_id": result.candidate_id,
            "rejection_stage": result.rejection_stage,
            "rejection_reason": result.rejection_reason,
            "rejection_confidence": result.rejection_confidence,
            "passed": result.passed,
            "errors": result.errors,
            "warnings": result.warnings,
            "dry_lab_only": result.dry_lab_only,
        }
        print(json.dumps(out, indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Rejection Reason: {status}")
        print(f"  RJR ID: {result.rjr_id}")
        print(f"  Candidate: {result.candidate_id}")
        print(f"  Stage: {result.rejection_stage}")
        print(f"  Reason: {result.rejection_reason}")
        print(f"  Confidence: {result.rejection_confidence}")
        if result.errors:
            print("  Errors:")
            for e in result.errors:
                print(f"    - {e}")
        if result.warnings:
            print("  Warnings:")
            for w in result.warnings:
                print(f"    - {w}")

    sys.exit(0 if result.passed else 1)


def _run_negative_result_archive_check(args):
    from openamp_foundry.evidence.negative_result_archive_summary import (
        validate_negative_result_archive_dict,
    )
    import json
    import sys

    data = json.loads(args.entry_json)
    result = validate_negative_result_archive_dict(data)

    if args.format == "json":
        out = {
            "nas_id": result.nas_id,
            "batch_id": result.batch_id,
            "total_entries": result.total_entries,
            "completeness_confirmed": result.completeness_confirmed,
            "all_results_have_reason": result.all_results_have_reason,
            "passed": result.passed,
            "errors": result.errors,
            "warnings": result.warnings,
            "dry_lab_only": result.dry_lab_only,
        }
        print(json.dumps(out, indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Negative Result Archive: {status}")
        print(f"  NAS ID: {result.nas_id}")
        print(f"  Batch: {result.batch_id}")
        print(f"  Total entries: {result.total_entries}")
        print(f"  Completeness confirmed: {result.completeness_confirmed}")
        print(f"  All results have reason: {result.all_results_have_reason}")
        if result.errors:
            print("  Errors:")
            for e in result.errors:
                print(f"    - {e}")
        if result.warnings:
            print("  Warnings:")
            for w in result.warnings:
                print(f"    - {w}")

    sys.exit(0 if result.passed else 1)


def _run_failed_candidate_batch_report_check(args):
    from openamp_foundry.evidence.failed_candidate_batch_report import (
        validate_failed_candidate_batch_report_dict,
    )
    import json
    import sys

    data = json.loads(args.entry_json)
    result = validate_failed_candidate_batch_report_dict(data)

    if args.format == "json":
        out = {
            "fcr_id": result.fcr_id,
            "batch_id": result.batch_id,
            "total_candidates_screened": result.total_candidates_screened,
            "failed_candidate_count": result.failed_candidate_count,
            "failure_rate": result.failure_rate,
            "passed": result.passed,
            "errors": result.errors,
            "warnings": result.warnings,
            "dry_lab_only": result.dry_lab_only,
        }
        print(json.dumps(out, indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Failed Candidate Batch Report: {status}")
        print(f"  FCR ID: {result.fcr_id}")
        print(f"  Batch: {result.batch_id}")
        print(f"  Screened: {result.total_candidates_screened}")
        print(f"  Failed: {result.failed_candidate_count}")
        print(f"  Failure Rate: {result.failure_rate:.2%}")
        if result.errors:
            print("  Errors:")
            for e in result.errors:
                print(f"    - {e}")
        if result.warnings:
            print("  Warnings:")
            for w in result.warnings:
                print(f"    - {w}")

    sys.exit(0 if result.passed else 1)


def _run_advisory_review_check(args: argparse.Namespace) -> int:
    """Validate an advisory review entry."""
    import json as _json
    from openamp_foundry.governance.advisory_review import validate_advisory_review_dict

    try:
        d = _json.loads(args.review_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--review-json must be a JSON object"}))
        return 2

    result = validate_advisory_review_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Advisory review {result.review_id} ({result.review_type}): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Advisory review entry validated. Ready for logging.")

    return 0 if result.passed else 3


def _run_roadmap_sync_check(args: argparse.Namespace) -> int:
    """Validate a roadmap sync entry."""


def _run_reviewer_questionnaire_check(args):
    from openamp_foundry.evidence.reviewer_questionnaire import (
        validate_reviewer_questionnaire_dict,
    )
    import json
    import sys

    data = json.loads(args.entry_json)
    result = validate_reviewer_questionnaire_dict(data)

    if args.format == "json":
        out = {
            "rvq_id": result.rvq_id,
            "pep_id": result.pep_id,
            "overall_package_quality": result.overall_package_quality,
            "would_recommend_for_synthesis": result.would_recommend_for_synthesis,
            "passed": result.passed,
            "errors": result.errors,
            "warnings": result.warnings,
            "dry_lab_only": result.dry_lab_only,
        }
        print(json.dumps(out, indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Reviewer Questionnaire: {status}")
        print(f"  RVQ ID: {result.rvq_id}")
        print(f"  PEP ID: {result.pep_id}")
        print(f"  Overall Quality: {result.overall_package_quality}/5")
        print(f"  Recommendation: {result.would_recommend_for_synthesis}")
        if result.errors:
            print("  Errors:")
            for e in result.errors:
                print(f"    - {e}")
        if result.warnings:
            print("  Warnings:")
            for w in result.warnings:
                print(f"    - {w}")

    sys.exit(0 if result.passed else 1)


def _run_domain_review_outcome_check(args):
    from openamp_foundry.evidence.domain_review_outcome import (
        validate_domain_review_outcome_against_package_dict,
        validate_domain_review_outcome_dict,
    )
    import json
    import sys

    try:
        data = json.loads(args.entry_json)
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid --entry-json: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.package_json:
        try:
            with Path(args.package_json).open("r", encoding="utf-8") as handle:
                package = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: invalid --package-json: {exc}", file=sys.stderr)
            sys.exit(1)
        result = validate_domain_review_outcome_against_package_dict(data, package)
    else:
        result = validate_domain_review_outcome_dict(data)

    if args.format == "json":
        out = {
            "dro_id": result.dro_id,
            "pep_id": result.pep_id,
            "rvq_id": result.rvq_id,
            "review_domain": result.review_domain,
            "outcome_verdict": result.outcome_verdict,
            "outcome_confidence": result.outcome_confidence,
            "passed": result.passed,
            "errors": result.errors,
            "warnings": result.warnings,
            "dry_lab_only": result.dry_lab_only,
            "package_hash_status": result.package_hash_status,
        }
        print(json.dumps(out, indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Domain Review Outcome: {status}")
        print(f"  DRO ID: {result.dro_id}")
        print(f"  PEP ID: {result.pep_id}")
        print(f"  RVQ ID: {result.rvq_id}")
        print(f"  Domain: {result.review_domain}")
        print(f"  Verdict: {result.outcome_verdict}")
        print(f"  Confidence: {result.outcome_confidence}")
        print(f"  Package hash: {result.package_hash_status}")
        if result.errors:
            print("  Errors:")
            for e in result.errors:
                print(f"    - {e}")
        if result.warnings:
            print("  Warnings:")
            for w in result.warnings:
                print(f"    - {w}")

    sys.exit(0 if result.passed else 1)


def _run_negative_result_entry_check(args):
    import json, sys
    from openamp_foundry.evidence.negative_result_entry import validate_dict
    try:
        data = json.loads(args.json_input)
    except json.JSONDecodeError as exc:
        print(f"INVALID: JSON parse error: {exc}", file=sys.stderr)
        sys.exit(1)
    result = validate_dict(data)
    if result.valid:
        print("VALID")
        for w in result.warnings:
            print(f"WARNING: {w}")
    else:
        print("INVALID")
        for e in result.errors:
            print(f"ERROR: {e}")
        for w in result.warnings:
            print(f"WARNING: {w}")
        sys.exit(1)


def _run_candidate_selection_rationale_check(args):
    import json, sys
    from openamp_foundry.evidence.candidate_selection_rationale import validate_dict
    try:
        data = json.loads(args.json_input)
    except json.JSONDecodeError as exc:
        print(f"INVALID: JSON parse error: {exc}", file=sys.stderr)
        sys.exit(1)
    result = validate_dict(data)
    if result.valid:
        print("VALID")
        for w in result.warnings:
            print(f"WARNING: {w}")
    else:
        print("INVALID")
        for e in result.errors:
            print(f"ERROR: {e}")
        for w in result.warnings:
            print(f"WARNING: {w}")
        sys.exit(1)


def _run_batch_experiment_priority_ranker_check(args):
    import json, sys
    from openamp_foundry.evidence.batch_experiment_priority_ranker import validate_dict
    try:
        data = json.loads(args.json_input)
    except json.JSONDecodeError as exc:
        print(f"INVALID: JSON parse error: {exc}", file=sys.stderr)
        sys.exit(1)
    result = validate_dict(data)
    if result.valid:
        print("VALID")
        for w in result.warnings:
            print(f"WARNING: {w}")
    else:
        print("INVALID")
        for e in result.errors:
            print(f"ERROR: {e}")
        for w in result.warnings:
            print(f"WARNING: {w}")
        sys.exit(1)


def _run_calibration_improvement_record_check(args):
    import json, sys
    from openamp_foundry.evidence.calibration_improvement_record import validate_dict
    try:
        data = json.loads(args.json_input)
    except json.JSONDecodeError as exc:
        print(f"INVALID: JSON parse error: {exc}", file=sys.stderr)
        sys.exit(1)
    result = validate_dict(data)
    if result.valid:
        print("VALID")
        for w in result.warnings:
            print(f"WARNING: {w}")
    else:
        print("INVALID")
        for e in result.errors:
            print(f"ERROR: {e}")
        for w in result.warnings:
            print(f"WARNING: {w}")
        sys.exit(1)


def _run_post_experiment_calibration_intake_check(args):
    import json, sys
    from openamp_foundry.evidence.post_experiment_calibration_intake import validate_dict
    try:
        data = json.loads(args.json_input)
    except json.JSONDecodeError as exc:
        print(f"INVALID: JSON parse error: {exc}", file=sys.stderr)
        sys.exit(1)
    result = validate_dict(data)
    if result.valid:
        print("VALID")
        for w in result.warnings:
            print(f"WARNING: {w}")
    else:
        print("INVALID")
        for e in result.errors:
            print(f"ERROR: {e}")
        for w in result.warnings:
            print(f"WARNING: {w}")
        sys.exit(1)


def _run_negative_result_dashboard_check(args):
    import json, sys
    from openamp_foundry.evidence.negative_result_dashboard import validate_dict
    try:
        data = json.loads(args.json_input)
    except json.JSONDecodeError as exc:
        print(f"INVALID: JSON parse error: {exc}", file=sys.stderr)
        sys.exit(1)
    result = validate_dict(data)
    if result.valid:
        print("VALID")
        for w in result.warnings:
            print(f"WARNING: {w}")
    else:
        print("INVALID")
        for e in result.errors:
            print(f"ERROR: {e}")
        for w in result.warnings:
            print(f"WARNING: {w}")
        sys.exit(1)


def _run_synthetic_boundary_audit_record_check(args):
    """CLI handler for synthetic-boundary-audit-record-check."""
    import json, sys
    from openamp_foundry.evidence.synthetic_boundary_audit_record import validate_dict
    data = json.load(open(args.input))
    issues = validate_dict(data)
    errors = [i for i in issues if not i.startswith("WARNING:")]
    warnings = [i for i in issues if i.startswith("WARNING:")]
    for w in warnings:
        print(w)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print("OK: SyntheticBoundaryAuditRecord is valid.")


def _run_expert_review_example_package_check(args):
    """CLI handler for expert-review-example-package-check."""
    import json, sys
    from openamp_foundry.evidence.expert_review_example_package import validate_dict
    data = json.load(open(args.input))
    issues = validate_dict(data)
    errors = [i for i in issues if not i.startswith("WARNING:")]
    warnings = [i for i in issues if i.startswith("WARNING:")]
    for w in warnings:
        print(w)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print("OK: ExpertReviewExamplePackage is valid.")

def _run_annual_review_check(args: argparse.Namespace) -> int:
    """Validate an annual review checklist entry."""
    import json as _json
    from openamp_foundry.governance.annual_review import validate_annual_review_dict

    try:
        d = _json.loads(args.entry_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--entry-json must be a JSON object"}))
        return 2

    result = validate_annual_review_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Annual review {result.review_id} ({result.section} / {result.year}): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Annual review entry validated. Long-term trust maintained.")

    return 0 if result.passed else 3

def _run_baseline_comparison_check(args: argparse.Namespace) -> None:
    import json
    from openamp_foundry.evidence.baseline_comparison_manifest import validate_baseline_comparison_dict

    entry_dict = json.loads(args.entry_json)
    result = validate_baseline_comparison_dict(entry_dict)

    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        beats = "beats all" if result.pipeline_beats_all_baselines else "loses to some"
        print(f"[{status}] Baseline Comparison: {result.manifest_id} ({result.metric_name}, pipeline {beats} {result.baseline_count} baseline(s))")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")

def _run_batch_outcome_summary_check(args) -> int:
    import json
    from openamp_foundry.evidence.batch_outcome_summary import (
        validate_batch_outcome_summary_dict,
    )
    if args.entry_json:
        try:
            data = json.loads(args.entry_json)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON: {exc}", file=__import__("sys").stderr)
            return 1
    else:
        data = json.load(__import__("sys").stdin)
    result = validate_batch_outcome_summary_dict(data)
    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        synth = "SYNTHETIC" if result.is_synthetic else "REAL"
        print(f"[{status}] Batch Outcome Summary: {result.bos_id} ({synth})")
        print(f"  BSP: {result.bsp_id}")
        print(f"  Tested: {result.candidates_tested}/{result.candidates_proposed} "
              f"(active={result.candidates_active}, inactive={result.candidates_inactive}, "
              f"untested={result.candidates_untested})")
        for err in result.errors:
            print(f"  ERROR: {err}")
        for warn in result.warnings:
            print(f"  WARN:  {warn}")
    return 0 if result.passed else 1

def _run_batch_priority_check(args: argparse.Namespace) -> int:
    """Validate a batch experiment priority entry."""
    import json as _json
    from openamp_foundry.evidence.batch_priority import validate_batch_priority_dict

    try:
        d = _json.loads(args.entry_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--entry-json must be a JSON object"}))
        return 2

    result = validate_batch_priority_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Batch priority {result.priority_id} (candidate {result.candidate_id}, rank {result.priority_rank}): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Batch priority validated. Synthesis wave ranking is auditable.")

    return 0 if result.passed else 3

def _run_batch_selection_proposal_check(args: argparse.Namespace) -> int:
    from openamp_foundry.evidence.batch_selection_proposal import (
        validate_batch_selection_proposal_dict,
    )

    if args.entry_json:
        import json

        try:
            d = json.loads(args.entry_json)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON: {exc}", file=__import__("sys").stderr)
            return 2
        result = validate_batch_selection_proposal_dict(d)
    else:
        result = validate_batch_selection_proposal_dict(
            {
                "bsp_id": "BSP-DEMO",
                "pipeline_version": "v1.0.0",
                "gate_id": "CRG-DEMO",
                "gate_passed": True,
                "candidate_ids": ["CAND-001", "CAND-002"],
                "selection_strategy": "hybrid",
                "exploitation_fraction": 0.6,
                "exploration_fraction": 0.4,
                "max_brier_score_allowed": 0.20,
                "proposal_notes": "Demo proposal.",
                "reviewer": "demo@example.com",
                "dry_lab_only": True,
            }
        )

    if args.format == "json":
        import json

        print(
            json.dumps(
                {
                    "bsp_id": result.bsp_id,
                    "gate_id": result.gate_id,
                    "gate_passed": result.gate_passed,
                    "candidate_count": result.candidate_count,
                    "selection_strategy": result.selection_strategy,
                    "passed": result.passed,
                    "errors": result.errors,
                    "warnings": result.warnings,
                },
                indent=2,
            )
        )
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] Batch Selection Proposal: {result.bsp_id}")
        print(f"  Gate: {result.gate_id} (passed={result.gate_passed})")
        print(f"  Strategy: {result.selection_strategy}")
        print(f"  Candidates: {result.candidate_count}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN: {w}")

    return 0 if result.passed else 1

def _run_calibration_cycle_summary_check(args) -> int:
    import json
    from openamp_foundry.evidence.calibration_cycle_summary import (
        validate_calibration_cycle_summary_dict,
    )
    if args.entry_json:
        try:
            data = json.loads(args.entry_json)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON: {exc}", file=__import__("sys").stderr)
            return 1
    else:
        data = json.load(__import__("sys").stdin)
    result = validate_calibration_cycle_summary_dict(data)
    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        complete = "COMPLETE" if result.is_complete else f"INCOMPLETE ({result.missing_artifact_count} missing)"
        print(f"[{status}] Calibration Cycle Summary: {result.ccs_id} [{complete}]")
        print(f"  BSP: {result.bsp_id}, candidates: {result.candidate_count}")
        print(f"  Cycle outcome: {result.cycle_outcome}")
        for err in result.errors:
            print(f"  ERROR: {err}")
        for warn in result.warnings:
            print(f"  WARN:  {warn}")
    return 0 if result.passed else 1

def _run_calibration_improvement_check(args) -> int:
    import json
    from openamp_foundry.evidence.calibration_improvement_record import (
        validate_calibration_improvement_dict,
    )

    if args.entry_json:
        try:
            data = json.loads(args.entry_json)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON: {exc}", file=__import__("sys").stderr)
            return 1
    else:
        data = json.load(__import__("sys").stdin)

    result = validate_calibration_improvement_dict(data)

    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] Calibration Improvement: {result.improvement_id}")
        for err in result.errors:
            print(f"  ERROR: {err}")
        for warn in result.warnings:
            print(f"  WARN:  {warn}")

    return 0 if result.passed else 1

def _run_calibration_intake_check(args: argparse.Namespace) -> int:
    """Validate a post-experiment calibration intake entry."""
    import json as _json
    from openamp_foundry.evidence.calibration_intake import validate_calibration_intake_dict

    try:
        d = _json.loads(args.entry_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--entry-json must be a JSON object"}))
        return 2

    result = validate_calibration_intake_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        correct = "correct" if result.prediction_correct else "incorrect"
        print(f"Calibration intake {result.intake_id} (candidate {result.candidate_id}, prediction {correct}): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Calibration intake validated. Prediction-vs-outcome comparison is recorded.")

    return 0 if result.passed else 3

def _run_calibration_performance_check(args: argparse.Namespace) -> None:
    import json
    from openamp_foundry.evidence.calibration_performance_summary import validate_calibration_performance_dict

    entry_dict = json.loads(args.entry_json)
    result = validate_calibration_performance_dict(entry_dict)

    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] Calibration Performance: {result.summary_id} (v{result.pipeline_version}, n={result.total_candidates_evaluated}, Brier={result.brier_score:.3f})")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")

def _run_calibration_readiness_check(args) -> int:
    import json
    from openamp_foundry.evidence.calibration_readiness_gate import (
        validate_calibration_readiness_dict,
    )
    if args.entry_json:
        try:
            data = json.loads(args.entry_json)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON: {exc}", file=__import__("sys").stderr)
            return 1
    else:
        data = json.load(__import__("sys").stdin)
    result = validate_calibration_readiness_dict(data)
    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        gate = "GATE-PASS" if result.gate_passed else "GATE-FAIL"
        print(f"[{status}] Calibration Readiness Gate: {result.gate_id} [{gate}]")
        for err in result.errors:
            print(f"  ERROR: {err}")
        for warn in result.warnings:
            print(f"  WARN:  {warn}")
    return 0 if result.passed else 1

def _run_candidate_summary_card_check(args: argparse.Namespace) -> int:
    """Validate a candidate summary card entry."""
    import json as _json
    from openamp_foundry.evidence.candidate_summary_card import validate_candidate_summary_card_dict

    try:
        d = _json.loads(args.entry_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--entry-json must be a JSON object"}))
        return 2

    result = validate_candidate_summary_card_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Candidate summary card {result.card_id} (candidate {result.candidate_id}, length {result.sequence_length}): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Candidate summary card validated. Ready for reviewer packet.")

    return 0 if result.passed else 3

def _run_claim_to_evidence_check(args: argparse.Namespace) -> int:
    import json as _json
    from openamp_foundry.evidence.claim_to_evidence_mapper import validate_claim_to_evidence_dict

    try:
        d = _json.loads(args.entry_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--entry-json must be a JSON object"}))
        return 2

    result = validate_claim_to_evidence_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] Claim-to-Evidence Check: {result.mapping_id}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Claim-to-evidence mapping validated. Claim is traceable to supporting artifacts.")

    return 0 if result.passed else 3

def _run_cross_batch_aggregator_check(args) -> int:
    import json
    from openamp_foundry.evidence.cross_batch_aggregator import (
        validate_cross_batch_aggregator_dict,
    )
    if args.entry_json:
        try:
            data = json.loads(args.entry_json)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON: {exc}", file=__import__("sys").stderr)
            return 1
    else:
        data = json.load(__import__("sys").stdin)
    result = validate_cross_batch_aggregator_dict(data)
    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] Cross-Batch Aggregator: {result.aggregator_id}")
        for err in result.errors:
            print(f"  ERROR: {err}")
        for warn in result.warnings:
            print(f"  WARN:  {warn}")
    return 0 if result.passed else 1

def _run_dataset_release_check(args: argparse.Namespace) -> int:
    """Validate a dataset release package entry."""
    import json as _json
    from openamp_foundry.evidence.dataset_release import validate_dataset_release_dict

    try:
        d = _json.loads(args.entry_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--entry-json must be a JSON object"}))
        return 2

    result = validate_dataset_release_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Dataset release {result.release_id} ({result.dataset_name}): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Dataset release validated. Package meets data governance requirements.")

    return 0 if result.passed else 3

def _run_experiment_priority_check(args: argparse.Namespace) -> None:
    import json
    from openamp_foundry.evidence.experiment_priority_justification import validate_experiment_priority_dict

    entry_dict = json.loads(args.entry_json)
    result = validate_experiment_priority_dict(entry_dict)

    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] Experiment Priority: {result.justification_id} ({result.criteria_count} criteria, {result.rejected_alternative_count} alternatives rejected)")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")

def _run_external_sharing_clearance_check(args):
    from openamp_foundry.evidence.external_sharing_clearance import (
        validate_external_sharing_clearance_dict,
    )
    import json
    import sys

    data = json.loads(args.entry_json)
    result = validate_external_sharing_clearance_dict(data)

    if args.format == "json":
        out = {
            "esc_id": result.esc_id,
            "pep_id": result.pep_id,
            "pre_id": result.pre_id,
            "sharing_purpose": result.sharing_purpose,
            "passed": result.passed,
            "errors": result.errors,
            "warnings": result.warnings,
            "dry_lab_only": result.dry_lab_only,
        }
        print(json.dumps(out, indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"External Sharing Clearance: {status}")
        print(f"  ESC ID: {result.esc_id}")
        print(f"  PEP ID: {result.pep_id}")
        print(f"  PRE ID: {result.pre_id}")
        print(f"  Purpose: {result.sharing_purpose}")
        if result.errors:
            print("  Errors:")
            for e in result.errors:
                print(f"    - {e}")
        if result.warnings:
            print("  Warnings:")
            for w in result.warnings:
                print(f"    - {w}")

    sys.exit(0 if result.passed else 1)

def _run_hypothesis_outcome_check(args: argparse.Namespace) -> None:
    import json
    from openamp_foundry.evidence.hypothesis_outcome_record import validate_hypothesis_outcome_dict

    entry_dict = json.loads(args.entry_json)
    result = validate_hypothesis_outcome_dict(entry_dict)

    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        threshold_status = "MET" if result.success_threshold_met else "NOT MET"
        print(f"[{status}] Hypothesis Outcome: {result.outcome_id} -> {result.outcome_verdict} (threshold {threshold_status})")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")

def _run_multi_candidate_comparison_check(args: argparse.Namespace) -> int:
    """Validate a multi-candidate comparison entry."""
    import json as _json
    from openamp_foundry.evidence.multi_candidate_comparison import validate_multi_candidate_comparison_dict

    try:
        d = _json.loads(args.entry_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--entry-json must be a JSON object"}))
        return 2

    result = validate_multi_candidate_comparison_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Multi-candidate comparison {result.comparison_id} (batch {result.batch_id}, {result.candidate_count} candidates): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Multi-candidate comparison validated. Ready for supplementary table.")

    return 0 if result.passed else 3

def _run_negative_result_check(args: argparse.Namespace) -> None:
    import json
    from openamp_foundry.evidence.negative_result_record import validate_negative_result_dict

    entry_dict = json.loads(args.entry_json)
    result = validate_negative_result_dict(entry_dict)

    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        reported = "will be reported" if result.will_be_reported else "NOT REPORTED"
        print(f"[{status}] Negative Result: {result.record_id} ({result.failure_category}, {result.candidate_count} candidates, {reported})")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")

def _run_pilot_batch_safety_clearance_check(args) -> int:
    import json
    from openamp_foundry.evidence.pilot_batch_safety_clearance import (
        validate_pilot_batch_safety_clearance_dict,
    )
    if args.entry_json:
        try:
            data = json.loads(args.entry_json)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON: {exc}", file=__import__("sys").stderr)
            return 1
    else:
        data = json.load(__import__("sys").stdin)
    result = validate_pilot_batch_safety_clearance_dict(data)
    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        cleared = "CLEARED" if result.cleared_for_synthesis else "NOT-CLEARED"
        print(f"[{status}] Pilot Batch Safety Clearance: {result.psc_id} [{cleared}]")
        print(f"  BSP: {result.bsp_id}, risk tier: {result.max_safety_risk_tier}")
        print(f"  Rejections: {result.rejection_count}")
        for err in result.errors:
            print(f"  ERROR: {err}")
        for warn in result.warnings:
            print(f"  WARN:  {warn}")
    return 0 if result.passed else 1

def _run_pilot_evidence_package_check(args) -> int:
    import json
    from openamp_foundry.evidence.pilot_evidence_package import (
        validate_pilot_evidence_package_dict,
    )
    if args.entry_json:
        try:
            data = json.loads(args.entry_json)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON: {exc}", file=__import__("sys").stderr)
            return 1
    else:
        data = json.load(__import__("sys").stdin)
    result = validate_pilot_evidence_package_dict(data)
    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        complete = "COMPLETE" if result.is_complete else f"INCOMPLETE ({result.missing_artifact_count} missing)"
        print(f"[{status}] Pilot Evidence Package: {result.pep_id} [{complete}]")
        print(f"  CCS: {result.ccs_id}, candidates: {result.candidate_count}")
        print(f"  Cleared: {result.cleared_for_synthesis}")
        for err in result.errors:
            print(f"  ERROR: {err}")
        for warn in result.warnings:
            print(f"  WARN:  {warn}")
    return 0 if result.passed else 1

def _run_pilot_package_check(args: argparse.Namespace) -> int:
    """Validate a pilot package completeness entry."""
    import json as _json
    from openamp_foundry.evidence.pilot_package import validate_pilot_package_dict

    try:
        d = _json.loads(args.entry_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--entry-json must be a JSON object"}))
        return 2

    result = validate_pilot_package_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Pilot package {result.package_id} (batch {result.batch_id}): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Pilot package validated. All required artifacts present.")

    return 0 if result.passed else 3

def _run_pipeline_decision_audit_check(args: argparse.Namespace) -> int:
    """Validate a pipeline decision audit entry."""
    import json as _json
    from openamp_foundry.evidence.pipeline_decision_audit import validate_pipeline_decision_audit_dict

    try:
        d = _json.loads(args.entry_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--entry-json must be a JSON object"}))
        return 2

    result = validate_pipeline_decision_audit_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Pipeline decision audit {result.audit_id} (batch {result.batch_id}, type {result.decision_type}): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Pipeline decision audit validated. Decision is traceable and reviewable.")

    return 0 if result.passed else 3

def _run_pre_registration_entry_check(args) -> int:
    import json
    from openamp_foundry.evidence.pre_registration_entry import (
        validate_pre_registration_entry_dict,
    )
    if args.entry_json:
        try:
            data = json.loads(args.entry_json)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON: {exc}", file=__import__("sys").stderr)
            return 1
    else:
        data = json.load(__import__("sys").stdin)
    result = validate_pre_registration_entry_dict(data)
    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] Pre-Registration: {result.pre_id} [{result.registration_status}]")
        print(f"  Title: {result.experiment_title}")
        print(f"  Candidates: {result.candidate_count}, Controls: +{result.has_positive_control}/-{result.has_negative_control}")
        for err in result.errors:
            print(f"  ERROR: {err}")
        for warn in result.warnings:
            print(f"  WARN:  {warn}")
    return 0 if result.passed else 1

def _run_prediction_drift_check(args) -> int:
    import json
    from openamp_foundry.evidence.prediction_drift_monitor import (
        validate_prediction_drift_dict,
    )

    if args.entry_json:
        try:
            data = json.loads(args.entry_json)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON: {exc}", file=__import__("sys").stderr)
            return 1
    else:
        data = json.load(__import__("sys").stdin)

    result = validate_prediction_drift_dict(data)

    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] Prediction Drift Monitor: {result.monitor_id}")
        for err in result.errors:
            print(f"  ERROR: {err}")
        for warn in result.warnings:
            print(f"  WARN:  {warn}")

    return 0 if result.passed else 1

def _run_preprint_bundle_check(args: argparse.Namespace) -> int:
    """Validate a preprint evidence bundle entry."""
    import json as _json
    from openamp_foundry.evidence.preprint_bundle import validate_preprint_bundle_dict

    try:
        d = _json.loads(args.entry_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--entry-json must be a JSON object"}))
        return 2

    result = validate_preprint_bundle_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Preprint bundle {result.bundle_id} (batch {result.batch_id}, {result.artifact_count} artifacts): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Preprint bundle validated. Evidence package is ready for submission review.")

    return 0 if result.passed else 3

def _run_recalibration_refusal_check(args) -> int:
    import json
    from openamp_foundry.evidence.recalibration_refusal_record import (
        validate_recalibration_refusal_dict,
    )
    if args.entry_json:
        try:
            data = json.loads(args.entry_json)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON: {exc}", file=__import__("sys").stderr)
            return 1
    else:
        data = json.load(__import__("sys").stdin)
    result = validate_recalibration_refusal_dict(data)
    if args.format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] Recalibration Refusal: {result.rrf_id}")
        for err in result.errors:
            print(f"  ERROR: {err}")
        for warn in result.warnings:
            print(f"  WARN:  {warn}")
    return 0 if result.passed else 1

def _run_reproducibility_manifest_check(args: argparse.Namespace) -> int:
    """Validate a reproducibility manifest entry."""
    import json as _json
    from openamp_foundry.evidence.reproducibility_manifest import validate_reproducibility_manifest_dict

    try:
        d = _json.loads(args.entry_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--entry-json must be a JSON object"}))
        return 2

    result = validate_reproducibility_manifest_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Reproducibility manifest {result.manifest_id} (batch {result.batch_id}, {result.package_count} packages, {result.data_file_count} data files): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Reproducibility manifest validated. Run is fully documented for third-party reproduction.")

    return 0 if result.passed else 3

def _run_score_decomposition_check(args: argparse.Namespace) -> int:
    import json
    from openamp_foundry.evidence.score_decomposition_report import validate_score_decomposition_dict

    try:
        entry_dict = json.loads(args.entry_json)
    except json.JSONDecodeError as exc:
        print(json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(entry_dict, dict):
        print(json.dumps({"status": "error", "error": "--entry-json must be a JSON object"}))
        return 2

    result = validate_score_decomposition_dict(entry_dict)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] Score Decomposition Check: {result.report_id} ({result.candidate_id})")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Score decomposition validated. Composite score is auditable.")

    return 0 if result.passed else 3

def _run_selection_rationale_check(args: argparse.Namespace) -> int:
    """Validate a candidate selection rationale entry."""
    import json as _json
    from openamp_foundry.evidence.selection_rationale import validate_selection_rationale_dict

    try:
        d = _json.loads(args.entry_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--entry-json must be a JSON object"}))
        return 2

    result = validate_selection_rationale_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Selection rationale {result.selection_id} (candidate {result.candidate_id}): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Selection rationale validated. Decision is auditable.")

    return 0 if result.passed else 3

def _run_uncertainty_report_check(args: argparse.Namespace) -> int:
    """Validate an uncertainty quantification report entry."""
    import json as _json
    from openamp_foundry.evidence.uncertainty_report import validate_uncertainty_report_dict

    try:
        d = _json.loads(args.entry_json)
    except _json.JSONDecodeError as exc:
        print(_json.dumps({"status": "error", "error": f"Invalid JSON: {exc}"}))
        return 2

    if not isinstance(d, dict):
        print(_json.dumps({"status": "error", "error": "--entry-json must be a JSON object"}))
        return 2

    result = validate_uncertainty_report_dict(d)
    output_format = getattr(args, "format", "text")

    if output_format == "json":
        import dataclasses
        print(_json.dumps(dataclasses.asdict(result), indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"Uncertainty report {result.report_id} (candidate {result.candidate_id}, width {result.interval_width:.2f}): {status}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        if result.passed:
            print("  Uncertainty report validated. Prediction intervals are documented.")

    return 0 if result.passed else 3

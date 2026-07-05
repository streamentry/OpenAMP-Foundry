"""Selection commands."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

def _run_pilot_panel(args: argparse.Namespace) -> int:
    import json as _json

    from openamp_foundry.reports.pilot_panel import write_pilot_csv, write_pilot_markdown
    from openamp_foundry.selection.pilot import select_pilot_panel

    ranked_path = Path(args.ranked)
    if not ranked_path.exists():
        print(_json.dumps({"status": "error", "message": f"File not found: {args.ranked}"}))
        return 1

    candidates = []
    with open(ranked_path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = _json.loads(line)
            except _json.JSONDecodeError as exc:
                print(_json.dumps({
                    "status": "error",
                    "message": f"Malformed JSON on line {line_num} of {args.ranked}: {exc}",
                    "line_preview": line[:120],
                }))
                return 1
            if row.get("selected"):
                candidates.append(row)

    panel = select_pilot_panel(
        candidates,
        n=args.n,
        max_per_seed=args.max_per_seed,
        similarity_threshold=getattr(args, "similarity_threshold", None),
        min_per_structural_class=getattr(args, "min_per_structural_class", 0),
    )
    generated_at = datetime.now(timezone.utc).isoformat()

    write_pilot_csv(panel, args.out_csv)
    if args.out_md:
        write_pilot_markdown(panel, args.out_md, generated_at=generated_at)

    seeds = sorted({c.get("seed", "") for c in panel})
    n_consensus = sum(
        1 for c in panel if c.get("scores", {}).get("disagreement", 1.0) < 0.20
    )
    print(_json.dumps({
        "status": "ok",
        "n_nominees": len(candidates),
        "n_panel": len(panel),
        "seeds_represented": seeds,
        "n_dual_scorer_consensus": n_consensus,
        "structural_classes_represented": sorted(
            {c.get("structural_class", "") for c in panel if c.get("structural_class")}
        ),
        "out_csv": args.out_csv,
        "out_md": args.out_md,
        "disclaimer": (
            "No antimicrobial activity has been demonstrated. "
            "Human expert review required before synthesis."
        ),
    }, indent=2))
    return 0


def _run_pilot_confident(args: argparse.Namespace) -> int:
    import csv as _csv
    import json as _json
    from openamp_foundry.reports.external_predict import write_confident_panel

    panel = []
    with open(args.pilot_csv, newline="", encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            panel.append(row)

    keep_ids = [cid.strip() for cid in args.keep.split(",") if cid.strip()]
    generated_at = datetime.now(timezone.utc).isoformat()
    confident = write_confident_panel(panel, keep_ids, out_path=args.out, generated_at=generated_at)

    print(_json.dumps({
        "status": "ok",
        "n_input": len(panel),
        "n_confident": len(confident),
        "out_csv": args.out + ".csv",
        "out_md": args.out + ".md",
        "disclaimer": "Confident candidates still require human expert review and biosafety sign-off.",
    }, indent=2))
    return 0


def _run_diversity_check(args: argparse.Namespace) -> int:
    import csv as _csv
    from openamp_foundry.analysis.diversity import (
        cluster_panel,
        diversity_stats,
        family_structural_warnings,
        pairwise_similarity_matrix,
        recommend_minimal_diverse_panel,
    )
    from openamp_foundry.features.physchem import compute_features
    from openamp_foundry.qc.presynth_check import check_panel

    # Load panel
    with open(args.panel_csv, newline="", encoding="utf-8") as f:
        panel = list(_csv.DictReader(f))

    # Pre-synthesis QC to get μH and trypsin sites
    mu_h_map = {}
    for row in panel:
        seq = row["sequence"]
        feats = compute_features(seq)
        mu_h_map[row["candidate_id"]] = feats.get("hydrophobic_moment", 0.0)

    qc_results = check_panel(panel, mu_h_map=mu_h_map)
    qc_by_id = {q.candidate_id: q for q in qc_results}

    # Cluster
    threshold = args.similarity_threshold
    clustered = cluster_panel(panel, similarity_threshold=threshold)
    stats = diversity_stats(clustered)
    minimal = recommend_minimal_diverse_panel(clustered, n_per_cluster=args.n_per_cluster)

    # Family-level warnings (merge QC data)
    enriched = []
    for c in clustered:
        qc = qc_by_id.get(c["candidate_id"])
        if qc:
            enriched.append({
                **c,
                "mu_h": qc.mu_h,
                "trypsin_sites": qc.trypsin_sites,
                "methionine_count": qc.methionine_count,
            })
        else:
            enriched.append(c)
    fam_warnings = family_structural_warnings(enriched, min_family_size=3)

    # Pairwise matrix for report
    sequences = [c["sequence"] for c in panel]
    ids = [c["candidate_id"] for c in panel]
    mat = pairwise_similarity_matrix(sequences)

    # Build report
    ts = datetime.now(timezone.utc).isoformat()

    lines = [
        "# Sequence Diversity Analysis",
        "",
        f"> Generated: {ts}  ",
        f"> Panel: {args.panel_csv}  ",
        f"> Similarity threshold: {threshold}  ",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Candidates analysed | {stats['n_candidates']} |",
        f"| Structural clusters | {stats['n_clusters']} |",
        f"| Redundant candidates (same cluster as earlier) | {stats['n_redundant']} |",
        f"| Singleton clusters (fully unique) | {stats['n_singletons']} |",
        f"| Largest cluster size | {stats['largest_cluster_size']} |",
        f"| Mean pairwise similarity | {stats['mean_pairwise_similarity']:.3f} |",
        f"| Diversity score (1 − mean_sim) | {stats['diversity_score']:.3f} |",
        "",
    ]

    if stats["n_redundant"] > 0:
        lines += [
            "## ⚠ Redundancy Warning",
            "",
            f"{stats['n_redundant']} of {stats['n_candidates']} candidates share a cluster "
            f"with an earlier (higher-priority) candidate at similarity threshold {threshold}.",
            "Synthesising all of them adds cost with diminishing structural information gain.",
            "",
        ]

    # Cluster assignments table
    lines += [
        "## Cluster Assignments",
        "",
        "| Rank | ID | Sequence | Cluster | Ensemble | Safety | μH | Status |",
        "|--:|---|---|:---:|:---:|:---:|:---:|:---:|",
    ]

    minimal_ids = {c["candidate_id"] for c in minimal}
    seen_clusters: set[int] = set()
    for c in clustered:
        cid = c["cluster_id"]
        seen_clusters.add(cid)
        rank = c.get("pilot_rank", "")
        cand_id = c["candidate_id"]
        seq = c["sequence"]
        ens = float(c.get("ensemble", 0))
        safe = float(c.get("safety", 0))
        mu_h = mu_h_map.get(cand_id, 0.0)
        status = "✅ KEEP" if cand_id in minimal_ids else "⚠ REDUNDANT"
        lines.append(
            f"| {rank} | {cand_id} | `{seq}` | C{cid} | {ens:.3f} | {safe:.3f} | {mu_h:.2f} | {status} |"
        )

    # Minimal diverse panel
    lines += [
        "",
        f"## Recommended Minimal Diverse Panel ({len(minimal)} candidates)",
        "",
        f"Best 1 candidate per structural cluster. Covers {stats['n_clusters']} distinct "
        f"structural families in {len(minimal)} synthesis slots instead of {stats['n_candidates']}.",
        "",
        "| Priority | ID | Sequence | Cluster | Ensemble | Safety | μH |",
        "|:---:|---|---|:---:|:---:|:---:|:---:|",
    ]
    for i, c in enumerate(minimal, 1):
        cand_id = c["candidate_id"]
        seq = c["sequence"]
        ens = float(c.get("ensemble", 0))
        safe = float(c.get("safety", 0))
        mu_h = mu_h_map.get(cand_id, 0.0)
        cluster_id = c["cluster_id"]
        lines.append(
            f"| {i} | {cand_id} | `{seq}` | C{cluster_id} | {ens:.3f} | {safe:.3f} | {mu_h:.2f} |"
        )

    # Optimal cluster representatives (best ensemble per cluster, tie-break by low μH + no Met)
    from collections import defaultdict as _dd
    by_cluster: dict = _dd(list)
    for c in clustered:
        by_cluster[c["cluster_id"]].append(c)

    optimal = []
    for cid in sorted(by_cluster.keys()):
        members = by_cluster[cid]
        # Sort: highest ensemble first, tie-break: no Met then lowest μH
        members_sorted = sorted(
            members,
            key=lambda x: (
                -float(x.get("ensemble", 0)),
                1 if qc_by_id.get(x["candidate_id"]) and qc_by_id[x["candidate_id"]].methionine_count > 0 else 0,
                mu_h_map.get(x["candidate_id"], 0.0),
            )
        )
        for rep in members_sorted[:args.n_per_cluster]:
            optimal.append(rep)

    optimal_ids = {c["candidate_id"] for c in optimal}
    if optimal_ids != minimal_ids:
        lines += [
            "",
            f"## Optimal Cluster Representatives ({len(optimal)} candidates)",
            "",
            "Picked by **highest ensemble score per cluster** (tie-break: no Met, lower μH). "
            "This differs from 'Recommended Minimal' above, which picked by pilot rank.",
            "",
            "| Priority | ID | Sequence | Cluster | Ensemble | Safety | μH | Met |",
            "|:---:|---|---|:---:|:---:|:---:|:---:|:---:|",
        ]
        for i, c in enumerate(optimal, 1):
            cand_id = c["candidate_id"]
            seq = c["sequence"]
            ens = float(c.get("ensemble", 0))
            safe = float(c.get("safety", 0))
            mu_h = mu_h_map.get(cand_id, 0.0)
            cluster_id = c["cluster_id"]
            qc = qc_by_id.get(cand_id)
            met = qc.methionine_count if qc else 0
            met_flag = f"⚠ {met}×Met" if met > 0 else "✓"
            lines.append(
                f"| {i} | {cand_id} | `{seq}` | C{cluster_id} | {ens:.3f} | {safe:.3f} | {mu_h:.2f} | {met_flag} |"
            )
        lines += [
            "",
            "> Use these as the actual synthesis candidates if ordering ≤4 peptides.",
        ]

    # Family-level warnings
    if fam_warnings:
        lines += ["", "## Family-Level Structural Warnings", ""]
        for w in fam_warnings:
            lines += [f"**{w['family']} — {w['warning_type']}:** {w['message']}", ""]

    # Pairwise similarity heatmap (abbreviated)
    lines += [
        "",
        "## Pairwise Similarity (upper triangle, threshold shown)",
        "",
        "Values ≥ threshold are flagged as same-cluster.",
        "",
        "| | " + " | ".join(f"**{i}**" for i in range(1, len(ids) + 1)) + " |",
        "|---|" + "---|" * len(ids),
    ]
    for i, row_id in enumerate(ids):
        cells = []
        for j in range(len(ids)):
            if j < i:
                cells.append("")
            elif j == i:
                cells.append("1.00")
            else:
                v = mat[i][j]
                cells.append(f"**{v:.2f}**" if v >= threshold else f"{v:.2f}")
        lines.append(f"| **{i+1}** | " + " | ".join(cells) + " |")

    lines += [
        "",
        "## Synthesis Recommendation",
        "",
        f"**If budget allows ≤{len(minimal)} peptides:** Use the minimal diverse panel above.",
        f"**If budget allows all {stats['n_candidates']} peptides:** Order all — redundancy "
        "provides SAR (structure-activity relationship) data within each scaffold family.",
        "",
        "The minimal panel is strongly preferred for a first-pass experiment:",
        "- Covers all structural families",
        "- Maximises the chance of finding at least one hit in each scaffold class",
        "- Preserves budget for a second wave if any scaffold family shows promise",
        "",
        "## Disclaimer",
        "",
        "Sequence similarity (Levenshtein) is a proxy for structural similarity.",
        "Peptides with different sequences can still adopt similar 3D conformations,",
        "and vice versa. For short AMPs (<20 AA), sequence similarity is generally a",
        "reliable proxy for functional similarity.",
    ]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "n_candidates": stats["n_candidates"],
        "n_clusters": stats["n_clusters"],
        "n_redundant": stats["n_redundant"],
        "minimal_panel_size": len(minimal),
        "mean_pairwise_similarity": stats["mean_pairwise_similarity"],
        "diversity_score": stats["diversity_score"],
        "n_family_warnings": len(fam_warnings),
        "out": args.out,
    }, indent=2))
    return 0


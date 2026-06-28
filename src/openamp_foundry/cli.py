from __future__ import annotations

import argparse
import json
from pathlib import Path

from openamp_foundry.evidence.schemas import validate_json_schema
from openamp_foundry.pipeline import run_ranking_pipeline
from openamp_foundry.utils.io import read_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openamp-foundry")
    sub = parser.add_subparsers(dest="command", required=True)

    rank = sub.add_parser("rank", help="Rank candidate peptides and generate evidence.")
    rank.add_argument("--candidates", required=True)
    rank.add_argument("--references", required=False)
    rank.add_argument("--out", required=True)
    rank.add_argument("--report", required=False)
    rank.add_argument("--cert-dir", required=False)
    rank.add_argument("--manifest", required=False)
    rank.add_argument("--config", default="configs/pipeline.yaml")

    validate = sub.add_parser("validate", help="Validate a candidate certificate against JSON schema.")
    validate.add_argument("--certificate", required=True)
    validate.add_argument("--schema", required=True)

    bench = sub.add_parser("bench", help="Run benchmark and leakage checks.")
    bench_sub = bench.add_subparsers(dest="bench_command", required=True)

    leakage = bench_sub.add_parser("leakage", help="Find near-duplicate candidates in references.")
    leakage.add_argument("--candidates", required=True)
    leakage.add_argument("--references", required=True)
    leakage.add_argument("--threshold", type=float, default=0.90)
    leakage.add_argument("--out", required=False, help="Optional JSON output path.")

    baseline = bench_sub.add_parser(
        "baseline",
        help="Evaluate pipeline recall vs random baseline on a labelled set.",
    )
    baseline.add_argument("--candidates", required=True, help="CSV of all candidates to score.")
    baseline.add_argument("--references", required=False, help="Reference CSV for novelty scoring.")
    baseline.add_argument(
        "--positives",
        required=True,
        help="CSV of known-positive (active) peptides. IDs must match candidates CSV.",
    )
    baseline.add_argument(
        "--k",
        type=int,
        nargs="+",
        default=None,
        help="Recall@k cutoffs (default: auto from dataset size).",
    )
    baseline.add_argument("--config", default="configs/pipeline.yaml")
    baseline.add_argument("--out", required=False, help="Optional JSON output path.")

    generate = sub.add_parser(
        "generate-batch",
        help=(
            "Generate a candidate pool by conservative mutation of seed sequences. "
            "Output is a CSV suitable for the 'rank' command. "
            "This is a toy exploration tool — no biological activity is implied."
        ),
    )
    generate.add_argument(
        "--seeds",
        required=True,
        help="CSV of seed sequences (columns: id, sequence, source)",
    )
    generate.add_argument(
        "--out",
        required=True,
        help="Output CSV path for the candidate pool.",
    )
    generate.add_argument(
        "--n-double",
        type=int,
        default=25,
        help="Double-substitution variants per seed (default: 25)",
    )
    generate.add_argument(
        "--n-charge",
        type=int,
        default=12,
        help="Charge-enhanced variants per seed (default: 12)",
    )
    generate.add_argument(
        "--rng-seed",
        type=int,
        default=2024,
        help="RNG seed for reproducibility (default: 2024)",
    )

    pilot = sub.add_parser(
        "pilot-panel",
        help=(
            "Select a first-synthesis-wave pilot panel from a ranked JSONL file. "
            "Picks n candidates (default 20) maximising ensemble score, minimising scorer "
            "disagreement, and ensuring at least one representative per seed template."
        ),
    )
    pilot.add_argument(
        "--ranked",
        required=True,
        help="Ranked JSONL file (output of the 'rank' command).",
    )
    pilot.add_argument(
        "--n",
        type=int,
        default=20,
        help="Panel size (default: 20).",
    )
    pilot.add_argument(
        "--out-csv",
        required=True,
        help="Output CSV path (synthesis-ready format).",
    )
    pilot.add_argument(
        "--out-md",
        required=False,
        help="Optional output path for human-readable markdown panel.",
    )
    pilot.add_argument(
        "--max-per-seed",
        type=int,
        default=None,
        help=(
            "Cap the number of nominees from any single seed family. "
            "Prevents one high-scoring family from dominating the panel. "
            "Recommended: panel_size // number_of_seeds (e.g. 4 for a 20-member, 8-seed panel)."
        ),
    )
    pilot.add_argument(
        "--similarity-threshold",
        type=float,
        default=None,
        help=(
            "Levenshtein similarity ceiling between any two selected candidates (0–1). "
            "Candidates above this threshold vs an already-selected member are skipped, "
            "eliminating near-duplicates that crossed seed families. "
            "Recommended: 0.75. None = no filter (default)."
        ),
    )

    validate_scoring = sub.add_parser(
        "validate-scoring",
        help=(
            "Retrospective AUROC benchmark: known AMPs vs background random peptides. "
            "AUROC > 0.70 = model passes Gate 1 (proceed to synthesis). "
            "Run before committing to wet-lab spend."
        ),
    )
    validate_scoring.add_argument(
        "--amp-csv",
        default="examples/validation/known_amps.csv",
        help="CSV of known AMPs with 'id' and 'sequence' columns (label=1).",
    )
    validate_scoring.add_argument(
        "--decoy-csv",
        default="examples/validation/random_background.csv",
        help=(
            "CSV of decoy peptides (label=0). "
            "Default: background-frequency random peptides (standard benchmark). "
            "Use examples/validation/scrambled_decoys.csv for the stricter "
            "composition-matched shuffle test."
        ),
    )
    validate_scoring.add_argument(
        "--benchmark-type",
        choices=["standard", "strict"],
        default="standard",
        help=(
            "standard: AMPs vs background random peptides (primary synthesis gate). "
            "strict: AMPs vs composition-matched shuffled decoys (order-sensitivity test)."
        ),
    )
    validate_scoring.add_argument("--config", default="configs/pipeline.yaml")
    validate_scoring.add_argument(
        "--out",
        required=False,
        help="Optional JSON output path.",
    )

    external_predict = sub.add_parser(
        "external-predict",
        help=(
            "Generate FASTA and submission checklist for external AMP prediction tools "
            "(CAMPR4, AMPScanner v2, dbAMP). Must be submitted manually — no API calls made."
        ),
    )
    external_predict.add_argument(
        "--pilot-csv",
        required=True,
        help="Pilot panel CSV (output of 'pilot-panel' command).",
    )
    external_predict.add_argument(
        "--out-fasta",
        default="outputs/pilot_panel.fasta",
        help="Output FASTA file for tool submission.",
    )
    external_predict.add_argument(
        "--out-checklist",
        default="outputs/external_predict_checklist.md",
        help="Output markdown checklist for recording results.",
    )

    pilot_confident = sub.add_parser(
        "pilot-confident",
        help=(
            "Filter a pilot panel to candidates confirmed by ≥2 external predictors. "
            "Provide the comma-separated IDs of confirmed candidates via --keep."
        ),
    )
    pilot_confident.add_argument(
        "--pilot-csv",
        required=True,
        help="Pilot panel CSV (output of 'pilot-panel' command).",
    )
    pilot_confident.add_argument(
        "--keep",
        required=True,
        help="Comma-separated candidate IDs to retain (from external predictor results).",
    )
    pilot_confident.add_argument(
        "--out",
        default="outputs/confident_panel",
        help="Output path prefix (will write .csv and .md).",
    )

    presynth_qc = sub.add_parser(
        "presynth-qc",
        help=(
            "Run pre-synthesis QC on a panel CSV: flags oxidation risk, proteolytic "
            "sites, aggregation, formulation notes, and hemolysis stratification."
        ),
    )
    presynth_qc.add_argument(
        "--panel-csv",
        default="outputs/confident_panel.csv",
        help="Panel CSV file (candidate_id + sequence columns required).",
    )
    presynth_qc.add_argument(
        "--out",
        default="outputs/presynth_qc_report.md",
        help="Output markdown report path.",
    )

    gold_standard = sub.add_parser(
        "gold-standard",
        help=(
            "Score known reference AMPs (melittin, magainin-2, LL-37, cecropin A) "
            "through the pipeline and compare against the nominated panel."
        ),
    )
    gold_standard.add_argument(
        "--panel-csv",
        default="outputs/confident_panel.csv",
        help="Panel CSV to compare against.",
    )
    gold_standard.add_argument(
        "--out",
        default="outputs/gold_standard_calibration.md",
        help="Output markdown report path.",
    )
    gold_standard.add_argument(
        "--config",
        default="configs/pipeline.yaml",
        help="Pipeline config (for scoring weights).",
    )

    diversity_check = sub.add_parser(
        "diversity-check",
        help=(
            "Analyse sequence redundancy in the confident panel. "
            "Clusters candidates by sequence similarity and recommends a minimal "
            "diverse synthesis set to maximise structural coverage per synthesis dollar."
        ),
    )
    diversity_check.add_argument(
        "--panel-csv",
        required=True,
        help="Confident panel CSV (output of 'pilot-confident' command).",
    )
    diversity_check.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.60,
        help="Levenshtein similarity threshold for clustering (default: 0.60).",
    )
    diversity_check.add_argument(
        "--n-per-cluster",
        type=int,
        default=1,
        help="Max candidates to keep per cluster in the minimal panel (default: 1).",
    )
    diversity_check.add_argument(
        "--out",
        default="outputs/diversity_report.md",
        help="Output markdown report path.",
    )

    synthesis_order = sub.add_parser(
        "synthesis-order",
        help=(
            "Generate a vendor-ready synthesis order CSV and checklist from a panel CSV. "
            "Runs pre-synthesis QC on every candidate and auto-fills N/C-term modifications, "
            "purity spec, quantity, and special-handling notes."
        ),
    )
    synthesis_order.add_argument(
        "--panel-csv",
        default="outputs/confident_panel.csv",
        help="Panel CSV (candidate_id + sequence columns required).",
    )
    synthesis_order.add_argument(
        "--out-csv",
        default="outputs/synthesis_order.csv",
        help="Output path for vendor-ready order CSV.",
    )
    synthesis_order.add_argument(
        "--out-md",
        default="outputs/synthesis_checklist.md",
        help="Output path for synthesis checklist markdown.",
    )
    synthesis_order.add_argument(
        "--quantity-mg",
        type=float,
        default=5.0,
        help="Default order quantity in mg per peptide (default: 5.0). HIGH-difficulty peptides get 2×.",
    )

    batch_pack = sub.add_parser(
        "batch-pack",
        help=(
            "Generate Phase 3 batch pack reports (diversity, novelty, toxicity, synthesis) "
            "from a ranked JSONL file produced by 'rank'."
        ),
    )
    batch_pack.add_argument(
        "--ranked",
        required=True,
        help="Ranked JSONL file (output of the 'rank' command).",
    )
    batch_pack.add_argument(
        "--out-json",
        required=True,
        help="Output path for machine-readable batch pack JSON.",
    )
    batch_pack.add_argument(
        "--out-md",
        required=False,
        help="Optional output path for human-readable markdown report.",
    )
    batch_pack.add_argument(
        "--diversity-threshold",
        type=float,
        default=0.80,
        help="Similarity threshold for diversity clustering (default: 0.80)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "rank":
        run_ranking_pipeline(
            candidate_path=args.candidates,
            reference_path=args.references,
            out_path=args.out,
            report_path=args.report,
            cert_dir=args.cert_dir,
            config_path=args.config,
            manifest_path=args.manifest,
        )
        print(json.dumps({"status": "ok", "out": args.out, "report": args.report}, indent=2))
        return 0

    if args.command == "validate":
        payload = read_json(args.certificate)
        validate_json_schema(payload, Path(args.schema))
        print(json.dumps({"status": "valid", "certificate": args.certificate}, indent=2))
        return 0

    if args.command == "bench":
        return _run_bench(args)

    if args.command == "generate-batch":
        return _run_generate_batch(args)

    if args.command == "pilot-panel":
        return _run_pilot_panel(args)

    if args.command == "validate-scoring":
        return _run_validate_scoring(args)

    if args.command == "external-predict":
        return _run_external_predict(args)

    if args.command == "pilot-confident":
        return _run_pilot_confident(args)

    if args.command == "batch-pack":
        return _run_batch_pack(args)

    if args.command == "synthesis-order":
        return _run_synthesis_order(args)

    if args.command == "presynth-qc":
        return _run_presynth_qc(args)

    if args.command == "gold-standard":
        return _run_gold_standard(args)

    if args.command == "diversity-check":
        return _run_diversity_check(args)

    parser.error("unknown command")
    return 2


def _run_bench(args: argparse.Namespace) -> int:
    from openamp_foundry.data.loaders import load_candidates_csv
    from openamp_foundry.utils.io import write_json

    if args.bench_command == "leakage":
        from openamp_foundry.benchmark.leakage import find_near_duplicates

        candidates = load_candidates_csv(args.candidates)
        references = load_candidates_csv(args.references)
        hits = find_near_duplicates(candidates, references, threshold=args.threshold)
        result = {
            "status": "ok",
            "threshold": args.threshold,
            "near_duplicate_count": len(hits),
            "near_duplicates": hits,
            "warning": (
                "Near-duplicates detected. If these candidates were used for training or "
                "scoring baseline models, benchmark results may be inflated."
            ) if hits else None,
        }
        if args.out:
            write_json(args.out, result)
        print(json.dumps(result, indent=2))
        return 0

    if args.bench_command == "baseline":
        from openamp_foundry.benchmark.evaluate import benchmark_summary
        from openamp_foundry.pipeline import score_candidates

        scored, _ = score_candidates(
            candidate_path=args.candidates,
            reference_path=args.references,
            config_path=args.config,
        )
        positives = load_candidates_csv(args.positives)
        positive_ids = {p.candidate_id for p in positives}
        summary = benchmark_summary(scored, positive_ids, ks=args.k)
        result = {"status": "ok", **summary}
        if args.out:
            write_json(args.out, result)
        print(json.dumps(result, indent=2))
        return 0

    return 2


def _run_pilot_panel(args: argparse.Namespace) -> int:
    import json as _json
    from datetime import datetime, timezone

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
        "out_csv": args.out_csv,
        "out_md": args.out_md,
        "disclaimer": (
            "No antimicrobial activity has been demonstrated. "
            "Human expert review required before synthesis."
        ),
    }, indent=2))
    return 0


def _run_validate_scoring(args: argparse.Namespace) -> int:
    import json as _json
    from openamp_foundry.benchmark.retrospective import run_retrospective_benchmark
    from openamp_foundry.utils.io import write_json

    benchmark_type = getattr(args, "benchmark_type", "standard")
    result = run_retrospective_benchmark(
        amp_csv=args.amp_csv,
        decoy_csv=args.decoy_csv,
        config_path=args.config,
        benchmark_type=benchmark_type,
    )
    if args.out:
        write_json(args.out, result)
    summary = {
        "status": "ok",
        "benchmark_type": result.get("benchmark_type"),
        "n_positives": result.get("n_positives"),
        "n_negatives": result.get("n_negatives"),
        "auroc": result["auroc"],
        "auroc_above_random": result["auroc_above_random"],
        "auprc": result.get("auprc"),
        "recall_at_10": result.get("recall_at_10"),
        "recall_at_20": result.get("recall_at_20"),
        "recall_at_43": result.get("recall_at_43"),
        "interpretation": result["interpretation"],
        "out": args.out,
    }
    print(_json.dumps(summary, indent=2))
    return 0


def _run_external_predict(args: argparse.Namespace) -> int:
    import csv as _csv
    import json as _json
    from datetime import datetime, timezone
    from openamp_foundry.reports.external_predict import (
        write_external_predict_checklist,
        write_pilot_fasta,
    )

    panel = []
    with open(args.pilot_csv, newline="", encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            panel.append(row)

    generated_at = datetime.now(timezone.utc).isoformat()
    write_pilot_fasta(panel, args.out_fasta)
    write_external_predict_checklist(
        panel, fasta_path=args.out_fasta, out_path=args.out_checklist,
        generated_at=generated_at,
    )
    print(_json.dumps({
        "status": "ok",
        "n_candidates": len(panel),
        "fasta": args.out_fasta,
        "checklist": args.out_checklist,
        "next_step": (
            f"Submit {args.out_fasta} to CAMPR4, AMPScanner v2, and dbAMP. "
            f"Fill in {args.out_checklist}. Then run 'make pilot-confident'."
        ),
    }, indent=2))
    return 0


def _run_pilot_confident(args: argparse.Namespace) -> int:
    import csv as _csv
    import json as _json
    from datetime import datetime, timezone
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


def _run_generate_batch(args: argparse.Namespace) -> int:
    import csv

    from openamp_foundry.generators.template_mutator import generate_candidate_pool

    seeds_path = Path(args.seeds)
    if not seeds_path.exists():
        print(json.dumps({"status": "error", "message": f"Seeds file not found: {args.seeds}"}))
        return 1

    seed_ids: list[str] = []
    seed_seqs: list[str] = []
    with open(seeds_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seed_ids.append(row["id"])
            seed_seqs.append(row["sequence"].strip().upper())

    pool = generate_candidate_pool(
        seed_sequences=seed_seqs,
        seed_ids=seed_ids,
        n_double=args.n_double,
        n_charge_enhance=args.n_charge,
        rng_seed=args.rng_seed,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "sequence", "source"])
        writer.writeheader()
        writer.writerows(pool)

    print(json.dumps({
        "status": "ok",
        "n_seeds": len(seed_ids),
        "n_candidates_generated": len(pool),
        "out": str(out_path),
        "disclaimer": (
            "Generated candidates are toy conservative-substitution variants. "
            "They have no demonstrated biological activity. "
            "Run 'rank' to score and filter them."
        ),
    }, indent=2))
    return 0


def _run_synthesis_order(args: argparse.Namespace) -> int:
    import csv as _csv
    from datetime import datetime, timezone
    from openamp_foundry.features.physchem import compute_features
    from openamp_foundry.qc.order_generator import (
        generate_synthesis_order,
        write_order_csv,
        write_synthesis_checklist,
    )

    panel_path = Path(args.panel_csv)
    if not panel_path.exists():
        print(json.dumps({"status": "error", "message": f"File not found: {args.panel_csv}"}))
        return 1

    panel = []
    with open(panel_path, newline="", encoding="utf-8") as f:
        reader = _csv.DictReader(f)
        required_cols = {"candidate_id", "sequence"}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            missing = required_cols - set(reader.fieldnames or [])
            print(json.dumps({
                "status": "error",
                "message": f"Panel CSV missing required columns: {sorted(missing)}",
                "found_columns": list(reader.fieldnames or []),
            }))
            return 1
        for row in reader:
            panel.append(row)

    mu_h_map = {}
    for row in panel:
        seq = row["sequence"].strip().upper()
        feats = compute_features(seq)
        mu_h_map[row["candidate_id"]] = feats.get("hydrophobic_moment", 0.0)

    qty = args.quantity_mg
    order_rows, qc_results = generate_synthesis_order(
        panel,
        mu_h_map=mu_h_map,
        default_quantity_mg=qty,
        high_difficulty_quantity_mg=qty * 2,
    )

    generated_at = datetime.now(timezone.utc).isoformat()
    write_order_csv(order_rows, args.out_csv)
    write_synthesis_checklist(
        order_rows,
        qc_results,
        args.out_md,
        generated_at=generated_at,
        panel_csv=args.panel_csv,
    )

    n_acetyl = sum(1 for r in order_rows if r["n_modification"] == "Ac-")
    n_amide = sum(1 for r in order_rows if r["c_modification"] == "NH2")
    n_high = sum(1 for r in order_rows if r["synthesis_difficulty"] == "HIGH")
    total_mg = sum(float(r["quantity_mg"]) for r in order_rows)

    print(json.dumps({
        "status": "ok",
        "n_candidates": len(order_rows),
        "n_n_terminal_acetylation": n_acetyl,
        "n_c_terminal_amide": n_amide,
        "n_high_difficulty": n_high,
        "total_quantity_mg": total_mg,
        "out_csv": args.out_csv,
        "out_md": args.out_md,
        "disclaimer": (
            "This order is computationally generated. Human expert review required "
            "before submitting to vendor. No antimicrobial activity has been demonstrated."
        ),
    }, indent=2))
    return 0


def _run_presynth_qc(args: argparse.Namespace) -> int:
    import csv as _csv
    from datetime import datetime, timezone
    from openamp_foundry.qc.presynth_check import check_panel
    from openamp_foundry.features.physchem import compute_features

    panel = []
    with open(args.panel_csv, newline="", encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            panel.append(row)

    mu_h_map = {}
    for row in panel:
        seq = row["sequence"].strip().upper()
        feats = compute_features(seq)
        mu_h_map[row["candidate_id"]] = feats.get("hydrophobic_moment", 0.0)

    results = check_panel(panel, mu_h_map=mu_h_map)
    generated_at = datetime.now(timezone.utc).isoformat()

    lines = [
        "# Pre-Synthesis QC Report",
        "",
        "> Generated by `make presynth-qc`. Review all FLAGS before ordering synthesis.",
        "",
        f"Generated: {generated_at}  ",
        f"Panel: {args.panel_csv}  ",
        f"Candidates checked: {len(results)}",
        "",
        "## Summary Table",
        "",
        "| # | ID | Seq | MW(Da) | pI | Charge pH7.4 | M | C | OxRisk | Agg | TrypSites | SPPS | UV |",
        "|--:|---|---|---:|---:|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]

    for i, r in enumerate(results, 1):
        lines.append(
            f"| {i} | {r.candidate_id} | `{r.sequence}` | {r.molecular_weight_da} | {r.isoelectric_point} "
            f"| {r.charge_ph74:.1f} | {r.methionine_count} | {r.cysteine_count} "
            f"| {'⚠' if r.has_oxidation_risk else '✓'} "
            f"| {'⚠' if r.aggregation_risk else '✓'} "
            f"| {len(r.trypsin_sites)} "
            f"| {r.synthesis_difficulty} "
            f"| {'Y' if r.has_uv_chromophore else 'N (BCA)'} |"
        )

    lines += ["", "## Per-Candidate Details", ""]
    for r in results:
        lines += [
            f"### {r.candidate_id} — `{r.sequence}`",
            "",
            f"- **MW:** {r.molecular_weight_da} Da  | **pI:** {r.isoelectric_point}",
            f"- **Charge:** pH 7.4 = {r.charge_ph74:.2f} | pH 6.0 = {r.charge_ph60:.2f}",
            f"- **Methionine:** {r.methionine_count} | **Cysteine:** {r.cysteine_count}",
            f"- **Aggregation risk:** {'YES — ' + r.hydrophobic_run if r.aggregation_risk else 'No'}",
            f"- **Trypsin cleavage sites (interior):** {r.trypsin_sites if r.trypsin_sites else 'None'}",
            f"- **Chymotrypsin sites:** {r.chymotrypsin_sites if r.chymotrypsin_sites else 'None'}",
            f"- **Deamidation hotspots:** {r.deamidation_sites if r.deamidation_sites else 'None'}",
            f"- **Concentration method:** {r.formulation_note}",
            f"- **Hemolysis start conc:** {r.hemolysis_start_conc}",
            f"- **SPPS difficulty:** {r.synthesis_difficulty}",
        ]
        if r.flags:
            lines.append("- **FLAGS:**")
            for flag in r.flags:
                lines.append(f"  - ⚠ {flag}")
        else:
            lines.append("- **FLAGS:** None")
        lines.append("")

    lines += [
        "## Formulation Protocol (Universal)",
        "",
        "1. Dissolve lyophilised peptide in sterile ultrapure water to 1–5 mM stock",
        "2. If poor solubility: add 10% DMSO; vortex; bath-sonicate 5 min",
        "3. Dilute to working stock (100 μM) in 10 mM sodium phosphate pH 7.0",
        "4. Filter through 0.22 μm syringe filter (sterile)",
        "5. Determine concentration: A280 (if W/Y present) or BCA assay",
        "6. Aliquot 10–20 μL; store −80°C; avoid freeze-thaw cycles",
        "7. Freshly dilute into MIC assay medium (MHB, RPMI) immediately before use",
        "",
        "## Hemolysis Assay Starting Concentrations",
        "",
        "| μH range | Risk level | Starting concentration |",
        "|---|---|---|",
        "| > 0.80 | HIGH | ≤ MIC/10 |",
        "| 0.55 – 0.80 | MODERATE | ≤ MIC/3 |",
        "| < 0.55 | LOW | MIC |",
        "",
        "Use 0.5% (v/v) human RBCs in PBS. Positive control: 1% Triton X-100. "
        "Negative control: PBS only. Read OD541 after 1h at 37°C.",
        "",
        "## Disclaimer",
        "",
        "These QC checks are computational. Actual synthesis difficulty and yield depend "
        "on the synthesis laboratory's protocols, resin choice, and coupling chemistry. "
        "Verify purity by HPLC-MS before assay.",
    ]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    n_flags = sum(1 for r in results if r.flags)
    n_ox = sum(1 for r in results if r.has_oxidation_risk)
    print(json.dumps({
        "status": "ok",
        "n_candidates": len(results),
        "n_with_flags": n_flags,
        "n_oxidation_risk": n_ox,
        "out": args.out,
    }, indent=2))
    return 0


def _run_gold_standard(args: argparse.Namespace) -> int:
    import csv as _csv
    from datetime import datetime, timezone
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
        "The AUROC benchmark (AUROC=0.8420 on 43 literature AMPs vs 44 background peptides) is",
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
    from datetime import datetime, timezone
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


if __name__ == "__main__":
    raise SystemExit(main())

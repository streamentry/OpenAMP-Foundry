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

    if args.command == "batch-pack":
        return _run_batch_pack(args)

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


if __name__ == "__main__":
    raise SystemExit(main())

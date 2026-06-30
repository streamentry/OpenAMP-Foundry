"""Benchmark and scoring validation commands."""
from __future__ import annotations
import argparse
import json

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



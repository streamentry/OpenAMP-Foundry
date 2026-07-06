"""Benchmark and scoring validation commands."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

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




def _run_cluster_split_bench(args: argparse.Namespace) -> int:
    """Run cluster-split retrospective benchmark with honest CI."""
    import json as _json
    from openamp_foundry.benchmark.retrospective import run_cluster_split_benchmark
    from openamp_foundry.utils.io import write_json

    result = run_cluster_split_benchmark(
        amp_csv=args.amp_csv,
        decoy_csv=args.decoy_csv,
        config_path=args.config,
        similarity_threshold=args.threshold,
        n_bootstrap=args.n_bootstrap,
    )
    if args.out:
        write_json(args.out, result)
    summary = {
        "status": "ok",
        "benchmark": "cluster_split_retrospective",
        "n_positives": result["n_positives"],
        "n_negatives": result["n_negatives"],
        "n_clusters": result["n_clusters"],
        "n_multi_member_clusters": result["n_multi_member_clusters"],
        "n_amps_in_multi_member_clusters": result["n_amps_in_multi_member_clusters"],
        "full_auroc": result["full_auroc"],
        "standard_ci95": f"{result['standard_ci95_lo']}-{result['standard_ci95_hi']}",
        "cluster_aware_ci95": f"{result['cluster_aware_ci95_lo']}-{result['cluster_aware_ci95_hi']}",
        "representative_auroc": result["representative_auroc"],
        "representative_ci95": f"{result['representative_ci95_lo']}-{result['representative_ci95_hi']}",
        "held_out_auroc": result["held_out_auroc"],
        "interpretation": result["interpretation"],
        "out": args.out,
    }
    print(_json.dumps(summary, indent=2))
    return 0


def _run_expert_ablation_bench(args: argparse.Namespace) -> int:
    """Run expert-vs-ensemble ablation benchmark."""
    import json as _json
    from openamp_foundry.benchmark.retrospective import run_expert_ablation_benchmark
    from openamp_foundry.utils.io import write_json

    result = run_expert_ablation_benchmark(
        amp_csv=args.amp_csv,
        decoy_csv=args.decoy_csv,
        config_path=args.config,
        n_bootstrap=args.n_bootstrap,
    )
    if args.out:
        write_json(args.out, result)
    summary = {
        "status": "ok",
        "benchmark": "expert_ablation",
        "n_positives": result["n_positives"],
        "n_negatives": result["n_negatives"],
        "ensemble_auroc": result["ensemble_auroc"],
        "ensemble_ci95": f"{result['ensemble_ci95_lo']}-{result['ensemble_ci95_hi']}",
        "expert_auroc": result["expert_auroc"],
        "expert_ci95": f"{result['expert_ci95_lo']}-{result['expert_ci95_hi']}",
        "delta_auroc": result["delta_auroc"],
        "signal_bearing_components": result["signal_bearing_components"],
        "near_zero_components": result["near_zero_components"],
        "anti_signal_components": result["anti_signal_components"],
        "verdict": result["verdict"],
        "out": args.out,
    }
    print(_json.dumps(summary, indent=2))
    return 0


def _run_selectivity_bench(args: argparse.Namespace) -> int:
    """Run within-AMP selectivity benchmark (hemolytic vs selective AMPs)."""
    import json as _json
    from openamp_foundry.benchmark.retrospective import run_selectivity_benchmark
    from openamp_foundry.utils.io import write_json

    result = run_selectivity_benchmark(
        hemolysis_csv=args.hemolysis_csv,
        config_path=args.config,
        n_bootstrap=args.n_bootstrap,
    )
    if args.out:
        write_json(args.out, result)
    summary = {
        "status": "ok",
        "benchmark": "within_amp_selectivity",
        "n_hemolytic": result["n_hemolytic"],
        "n_selective": result["n_selective"],
        "n_border": result["n_border"],
        "risk_detectors": result["risk_detectors"],
        "risk_indicators": result["risk_indicators"],
        "safety_verdict": result["safety_verdict"],
        "selectivity_proxy_verdict": result["selectivity_proxy_verdict"],
        "rich_selectivity_verdict": result["rich_selectivity_verdict"],
        "expert_composite_verdict": result["expert_composite_verdict"],
        "n_blind_spots": len(result["blind_spots"]),
        "out": args.out,
    }
    print(_json.dumps(summary, indent=2))
    return 0


def _run_triage(args: argparse.Namespace) -> int:
    import json
    from openamp_foundry.benchmark.triage import run_triage_benchmark
    from openamp_foundry.utils.io import write_json

    result = run_triage_benchmark(
        hemolysis_csv=args.hemolysis_csv,
        decoy_csv=args.decoy_csv,
        config_path=args.config,
        n_bootstrap=args.n_bootstrap,
    )
    if args.out:
        write_json(args.out, result)
    summary = {
        "status": "ok",
        "benchmark": result["benchmark"],
        "n_selective": result["n_selective"],
        "n_hemolytic": result["n_hemolytic"],
        "n_decoy": result["n_decoy"],
        "best_scorer": result["best_scorer"],
        "per_scorer": {
            s: {
                "selective_vs_decoy": info["selective_vs_decoy"]["auroc"],
                "hemolytic_vs_decoy": info["hemolytic_vs_decoy"]["auroc"],
                "selective_vs_hemolytic": info["selective_vs_hemolytic"]["auroc"],
                "triages_correctly": info["triages_correctly"],
            }
            for s, info in result["per_scorer"].items()
        },
        "top_20_by_ensemble": result["top_20_by_ensemble"],
        "top_20_by_triage_score": result["top_20_by_triage_score"],
        "out": args.out,
    }
    print(json.dumps(summary, indent=2))
    return 0


def _run_metrics_snapshot(args: argparse.Namespace) -> int:
    import json

    from openamp_foundry.benchmark.metrics_snapshot import build_metrics_snapshot
    from openamp_foundry.utils.io import write_json

    result = build_metrics_snapshot(
        amp_csv=args.amp_csv,
        decoy_csv=args.decoy_csv,
        hemolysis_csv=args.hemolysis_csv,
        standard_config=args.config,
        phase3_config=args.phase3_config,
        cluster_threshold=args.threshold,
        n_bootstrap=args.n_bootstrap,
    )
    if args.out:
        write_json(args.out, result)
    print(json.dumps(result, indent=2))
    return 0


def _run_feature_decomp(args: argparse.Namespace) -> int:
    """Run per-feature selective_vs_hemolytic decomposition benchmark."""
    from openamp_foundry.benchmark.feature_decomp import (
        run_feature_decomposition_benchmark,
    )
    from openamp_foundry.utils.io import write_json

    result = run_feature_decomposition_benchmark(
        hemolysis_csv=args.hemolysis_csv,
        n_bootstrap=args.n_bootstrap,
    )
    if args.out:
        write_json(args.out, result)

    summary = {
        "benchmark": result["benchmark"],
        "n_hemolytic": result["n_hemolytic"],
        "n_selective": result["n_selective"],
        "n_features_tested": result["n_features_tested"],
        "n_significant": result["n_significant"],
        "best_feature": result["best_feature"],
        "best_detection_auroc": result["best_detection_auroc"],
        "significant_features": result["significant_features"],
        "unused_signal_features": result["unused_signal_features"],
        "verdict": result["verdict"],
        "out": args.out,
    }
    print(json.dumps(summary, indent=2))
    return 0


def _run_active_learning_bench(args: argparse.Namespace) -> int:
    """Run the active-learning recovery benchmark."""
    import tempfile
    from pathlib import Path
    from openamp_foundry.active_learning.benchmark import (
        run_active_learning_benchmark,
        write_benchmark_pool,
        generate_benchmark_pool,
    )

    # If no pool CSV provided, generate one
    pool_csv = getattr(args, "pool_csv", None)
    if pool_csv and Path(pool_csv).exists():
        result = run_active_learning_benchmark(
            pool_csv=args.pool_csv,
            n_hidden_actives=args.n_hidden,
            batch_size=args.batch_size,
            max_rounds=args.max_rounds,
            rng_seed=args.rng_seed,
        )
    else:
        # Generate synthetic pool and run benchmark inline
        pool = generate_benchmark_pool(
            n_total=50,
            n_active=10,
            rng_seed=args.rng_seed,
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline="",
        ) as f:
            tmp_csv = Path(f.name)
            write_benchmark_pool(pool, tmp_csv)
        try:
            result = run_active_learning_benchmark(
                pool_csv=tmp_csv,
                n_hidden_actives=args.n_hidden,
                batch_size=args.batch_size,
                max_rounds=args.max_rounds,
                rng_seed=args.rng_seed,
            )
        finally:
            tmp_csv.unlink(missing_ok=True)

    out_dict = result.to_dict()
    print(json.dumps(out_dict, indent=2))
    return 0


def _run_simulation_gate(args: argparse.Namespace) -> int:
    """Validate whether virtual-assay scores may affect ranking."""
    from openamp_foundry.simulation.gate import evaluate_simulation_gate

    verdict = evaluate_simulation_gate(
        amp_vs_decoy_path=args.amp_vs_decoy_json,
        within_amp_path=args.within_amp_json,
        required_mode=args.required_mode,
    ).to_dict()

    if args.out:
        Path(args.out).write_text(json.dumps(verdict, indent=2) + "\n")
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["may_use_weighted_mode"] else 3

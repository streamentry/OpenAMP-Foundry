"""Build a machine-readable snapshot of the repo's current benchmark truth."""

from __future__ import annotations

from pathlib import Path

from openamp_foundry.benchmark.retrospective import (
    run_cluster_split_benchmark,
    run_expert_ablation_benchmark,
    run_retrospective_benchmark,
    run_selectivity_benchmark,
)
from openamp_foundry.benchmark.feature_decomp import (
    run_feature_decomposition_benchmark,
)
from openamp_foundry.benchmark.triage import run_strict_triage_benchmark, run_triage_benchmark


def build_metrics_snapshot(
    *,
    amp_csv: str | Path = "examples/validation/known_amps.csv",
    decoy_csv: str | Path = "examples/validation/random_background.csv",
    hemolysis_csv: str | Path = "examples/validation/hemolysis_reference.csv",
    standard_config: str | Path = "configs/pipeline.yaml",
    phase3_config: str | Path = "configs/phase3.yaml",
    cluster_threshold: float = 0.70,
    n_bootstrap: int = 2000,
) -> dict[str, object]:
    """Return a compact, auditable snapshot of current benchmark metrics."""

    standard = run_retrospective_benchmark(
        amp_csv=amp_csv,
        decoy_csv=decoy_csv,
        config_path=standard_config,
        benchmark_type="standard",
    )
    phase3 = run_retrospective_benchmark(
        amp_csv=amp_csv,
        decoy_csv=decoy_csv,
        config_path=phase3_config,
        benchmark_type="standard",
    )
    cluster_split = run_cluster_split_benchmark(
        amp_csv=amp_csv,
        decoy_csv=decoy_csv,
        config_path=standard_config,
        similarity_threshold=cluster_threshold,
        n_bootstrap=n_bootstrap,
    )
    expert_ablation = run_expert_ablation_benchmark(
        amp_csv=amp_csv,
        decoy_csv=decoy_csv,
        config_path=standard_config,
        n_bootstrap=n_bootstrap,
    )
    selectivity = run_selectivity_benchmark(
        hemolysis_csv=hemolysis_csv,
        config_path=standard_config,
        n_bootstrap=n_bootstrap,
    )
    triage = run_triage_benchmark(
        hemolysis_csv=hemolysis_csv,
        decoy_csv=decoy_csv,
        config_path=standard_config,
        n_bootstrap=n_bootstrap,
    )
    strict_triage = run_strict_triage_benchmark(
        hemolysis_csv=hemolysis_csv,
        n_bootstrap=n_bootstrap,
    )
    feature_decomp = run_feature_decomposition_benchmark(
        hemolysis_csv=hemolysis_csv,
        n_bootstrap=n_bootstrap,
    )

    return {
        "schema_version": 1,
        "benchmark_inputs": {
            "amp_csv": str(amp_csv),
            "decoy_csv": str(decoy_csv),
            "hemolysis_csv": str(hemolysis_csv),
            "standard_config": str(standard_config),
            "phase3_config": str(phase3_config),
            "cluster_threshold": cluster_threshold,
            "n_bootstrap": n_bootstrap,
        },
        "standard": {
            "auroc": standard["auroc"],
            "auprc": standard.get("auprc"),
            "recall_at_10": standard.get("recall_at_10"),
            "recall_at_20": standard.get("recall_at_20"),
            "recall_at_43": standard.get("recall_at_43"),
            "n_positives": standard["n_positives"],
            "n_negatives": standard["n_negatives"],
            "n_total": standard["n_positives"] + standard["n_negatives"],
            "interpretation": standard["interpretation"],
        },
        "phase3": {
            "auroc": phase3["auroc"],
            "auprc": phase3.get("auprc"),
            "n_positives": phase3["n_positives"],
            "n_negatives": phase3["n_negatives"],
            "n_total": phase3["n_positives"] + phase3["n_negatives"],
            "interpretation": phase3["interpretation"],
        },
        "cluster_split": {
            "full_auroc": cluster_split["full_auroc"],
            "standard_ci95": [
                cluster_split["standard_ci95_lo"],
                cluster_split["standard_ci95_hi"],
            ],
            "cluster_aware_ci95": [
                cluster_split["cluster_aware_ci95_lo"],
                cluster_split["cluster_aware_ci95_hi"],
            ],
            "representative_auroc": cluster_split["representative_auroc"],
            "representative_ci95": [
                cluster_split["representative_ci95_lo"],
                cluster_split["representative_ci95_hi"],
            ],
            "held_out_auroc": cluster_split["held_out_auroc"],
            "n_clusters": cluster_split["n_clusters"],
            "n_multi_member_clusters": cluster_split["n_multi_member_clusters"],
            "n_amps_in_multi_member_clusters": cluster_split[
                "n_amps_in_multi_member_clusters"
            ],
            "interpretation": cluster_split["interpretation"],
        },
        "expert_ablation": {
            "ensemble_auroc": expert_ablation["ensemble_auroc"],
            "expert_auroc": expert_ablation["expert_auroc"],
            "delta_auroc": expert_ablation["delta_auroc"],
            "signal_bearing_components": expert_ablation[
                "signal_bearing_components"
            ],
            "near_zero_components": expert_ablation["near_zero_components"],
            "anti_signal_components": expert_ablation["anti_signal_components"],
            "verdict": expert_ablation["verdict"],
        },
        "selectivity": {
            "n_hemolytic": selectivity["n_hemolytic"],
            "n_selective": selectivity["n_selective"],
            "n_border": selectivity["n_border"],
            "safety_verdict": selectivity["safety_verdict"],
            "selectivity_proxy_verdict": selectivity["selectivity_proxy_verdict"],
            "rich_selectivity_verdict": selectivity["rich_selectivity_verdict"],
            "expert_composite_verdict": selectivity["expert_composite_verdict"],
            "risk_detectors": selectivity["risk_detectors"],
            "risk_indicators": selectivity["risk_indicators"],
            "per_score_auroc": selectivity["per_score_auroc"],
        },
        "triage": {
            "best_scorer": triage["best_scorer"],
            "top_20_by_ensemble": triage["top_20_by_ensemble"],
            "top_20_by_triage_score": triage["top_20_by_triage_score"],
            "top_20_by_expert_composite": triage["top_20_by_expert_composite"],
            "top_20_by_gate_triage": triage["top_20_by_gate_triage"],
            "per_scorer": {
                scorer: {
                    "selective_vs_decoy": info["selective_vs_decoy"]["auroc"],
                    "hemolytic_vs_decoy": info["hemolytic_vs_decoy"]["auroc"],
                    "selective_vs_hemolytic": info["selective_vs_hemolytic"]["auroc"],
                    "triages_correctly": info["triages_correctly"],
                }
                for scorer, info in triage["per_scorer"].items()
            },
        },
        "strict_triage": {
            "decoy_type": strict_triage["decoy_type"],
            "n_selective": strict_triage["n_selective"],
            "n_hemolytic": strict_triage["n_hemolytic"],
            "n_decoy": strict_triage["n_decoy"],
            "best_scorer": strict_triage["best_scorer"],
            "top_20_by_ensemble": strict_triage["top_20_by_ensemble"],
            "top_20_by_triage_score": strict_triage["top_20_by_triage_score"],
            "top_20_by_expert_composite": strict_triage["top_20_by_expert_composite"],
            "top_20_by_gate_triage": strict_triage["top_20_by_gate_triage"],
            "per_scorer": {
                scorer: {
                    "selective_vs_decoy": info["selective_vs_decoy"]["auroc"],
                    "hemolytic_vs_decoy": info["hemolytic_vs_decoy"]["auroc"],
                    "selective_vs_hemolytic": info["selective_vs_hemolytic"]["auroc"],
                    "triages_correctly": info["triages_correctly"],
                }
                for scorer, info in strict_triage["per_scorer"].items()
            },
        },
        "feature_decomposition": {
            "n_hemolytic": feature_decomp["n_hemolytic"],
            "n_selective": feature_decomp["n_selective"],
            "n_features_tested": feature_decomp["n_features_tested"],
            "n_significant": feature_decomp["n_significant"],
            "best_feature": feature_decomp["best_feature"],
            "best_detection_auroc": feature_decomp["best_detection_auroc"],
            "significant_features": feature_decomp["significant_features"],
            "unused_signal_features": feature_decomp["unused_signal_features"],
            "per_feature": feature_decomp["per_feature"],
            "verdict": feature_decomp["verdict"],
        },
    }

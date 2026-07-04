"""Benchmark layer for OpenAMP Foundry.

Provides leakage checks, retrospective AUROC, cluster-aware splits,
expert ablation, and triage benchmarks used to validate the scoring
pipeline against held-out positives and matched decoys.
"""

from openamp_foundry.benchmark.evaluate import (
    benchmark_summary,
    enrichment_factor,
    find_contaminated_references,
    random_recall_at_k,
    recall_at_k,
    top_k_ids,
)
from openamp_foundry.benchmark.feature_decomp import (
    run_feature_decomposition_benchmark,
)
from openamp_foundry.benchmark.leakage import find_near_duplicates
from openamp_foundry.benchmark.metrics_snapshot import build_metrics_snapshot
from openamp_foundry.benchmark.retrospective import (
    run_cluster_split_benchmark,
    run_expert_ablation_benchmark,
    run_retrospective_benchmark,
    run_selectivity_benchmark,
)
from openamp_foundry.benchmark.splits import (
    cluster_by_similarity,
    cluster_split,
    deterministic_split,
)
from openamp_foundry.benchmark.triage import (
    run_strict_triage_benchmark,
    run_triage_benchmark,
)

__all__ = [
    # evaluate
    "benchmark_summary",
    "enrichment_factor",
    "find_contaminated_references",
    "random_recall_at_k",
    "recall_at_k",
    "top_k_ids",
    # feature_decomp
    "run_feature_decomposition_benchmark",
    # leakage
    "find_near_duplicates",
    # metrics_snapshot
    "build_metrics_snapshot",
    # retrospective
    "run_cluster_split_benchmark",
    "run_expert_ablation_benchmark",
    "run_retrospective_benchmark",
    "run_selectivity_benchmark",
    # splits
    "cluster_by_similarity",
    "cluster_split",
    "deterministic_split",
    # triage
    "run_strict_triage_benchmark",
    "run_triage_benchmark",
]

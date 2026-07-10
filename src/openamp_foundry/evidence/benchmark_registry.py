"""Benchmark registry — Phase C C1.

Pre-defined BenchmarkCard instances for all major benchmarks in the pipeline.
Makes governance enforceable: any benchmark that runs must have a card here,
or CI governance will flag it.

Add a new BenchmarkCard to BENCHMARK_REGISTRY for every new benchmark script.
"""

from __future__ import annotations

from openamp_foundry.evidence.benchmark_card import BenchmarkCard

BENCHMARK_REGISTRY: list[BenchmarkCard] = [
    BenchmarkCard(
        bmc_id="BMC-0001",
        pipeline_version="0.10.33",
        benchmark_name="AMP Activity Precision@k Benchmark",
        measurement_target="antimicrobial_activity_prediction",
        split_strategy="leakage_aware_split",
        cheap_enemy_baselines=[
            "charge_threshold_gte4",
            "length_10_to_40_heuristic",
        ],
        evaluation_metrics=["precision_at_k", "auc_roc", "enrichment_factor"],
        known_limitations=[
            "Trained on APD3 data; may overfit to alpha-helical scaffolds.",
            "Binary activity labels do not distinguish MIC ranges.",
            "Benchmark does not account for peptide modifications.",
        ],
        deprecated=False,
        created_date="2024-06-01",
        last_updated_date="2024-06-01",
        notes="Primary operational benchmark for candidate ranking.",
    ),
    BenchmarkCard(
        bmc_id="BMC-0002",
        pipeline_version="0.10.33",
        benchmark_name="Charge-Matched AMP Activity Benchmark",
        measurement_target="antimicrobial_activity_prediction",
        split_strategy="charge_stratified",
        cheap_enemy_baselines=[
            "charge_threshold_gte4",
            "hydrophobicity_threshold_gte30pct",
        ],
        evaluation_metrics=["precision_at_k", "auc_roc"],
        known_limitations=[
            "Charge-matched control tests only one shortcut dimension.",
            "Does not control for length and hydrophobicity simultaneously.",
        ],
        deprecated=False,
        created_date="2024-06-01",
        last_updated_date="2024-06-01",
        notes="Charge-controlled test; see BMC-0003 for combined charge+length control.",
    ),
    BenchmarkCard(
        bmc_id="BMC-0003",
        pipeline_version="0.10.33",
        benchmark_name="Calibration Accuracy Benchmark",
        measurement_target="calibration_accuracy",
        split_strategy="random_70_30",
        cheap_enemy_baselines=[
            "isotonic_regression_recalibration",
            "temperature_scaling",
        ],
        evaluation_metrics=["calibration_error", "brier_score", "auc_roc"],
        known_limitations=[
            "Calibration on training-domain data; may not transfer to novel scaffolds.",
            "Uses held-out 30% split which may have residual class imbalance.",
        ],
        deprecated=False,
        created_date="2024-06-01",
        last_updated_date="2024-06-01",
        notes="Calibration benchmark for confidence estimation; required before candidate release.",
    ),
    BenchmarkCard(
        bmc_id="BMC-0004",
        pipeline_version="0.10.33",
        benchmark_name="Family-Stratified AMP Precision Benchmark",
        measurement_target="antimicrobial_activity_prediction",
        split_strategy="family_stratified",
        cheap_enemy_baselines=[
            "charge_threshold_gte4",
            "length_10_to_40_heuristic",
            "hydrophobicity_threshold_gte30pct",
        ],
        evaluation_metrics=["precision_at_k", "recall_at_k", "auc_roc"],
        known_limitations=[
            "Family labels from APD3 may be inconsistent across AMP subfamilies.",
            "Small family sizes may give noisy stratified estimates.",
            "Does not test cross-family generalization.",
        ],
        deprecated=False,
        created_date="2024-06-01",
        last_updated_date="2024-06-01",
        notes="Stratified by AMP family to reduce within-family shortcut inflation.",
    ),
    BenchmarkCard(
        bmc_id="BMC-0005",
        pipeline_version="0.10.33",
        benchmark_name="Cheap Enemy Comparison Benchmark",
        measurement_target="ensemble_ranking",
        split_strategy="leakage_aware_split",
        cheap_enemy_baselines=[
            "charge_threshold_gte4",
            "length_10_to_40_heuristic",
            "hydrophobicity_threshold_gte30pct",
            "charge_plus_length_conjunction",
        ],
        evaluation_metrics=["precision_at_k", "enrichment_factor"],
        known_limitations=[
            "Cheap enemies are fixed heuristics; dynamic threshold tuning not tested.",
            "Does not test leakage from structural similarity to training positives.",
        ],
        deprecated=False,
        created_date="2024-06-01",
        last_updated_date="2024-06-01",
        notes="Anti-hype benchmark; advanced scorers must beat all declared enemies to get ranking authority.",
    ),
]

# Quick lookup by BMC ID
BENCHMARK_REGISTRY_BY_ID: dict[str, BenchmarkCard] = {
    card.bmc_id: card for card in BENCHMARK_REGISTRY
}


def get_card(bmc_id: str) -> BenchmarkCard | None:
    """Return the BenchmarkCard for the given BMC ID, or None if not found."""
    return BENCHMARK_REGISTRY_BY_ID.get(bmc_id)


def validate_registry() -> list[str]:
    """Validate all cards in the registry. Returns list of errors."""
    all_errors: list[str] = []
    for card in BENCHMARK_REGISTRY:
        errors = card.validate()
        hard_errors = [e for e in errors if not e.startswith("WARNING")]
        for err in hard_errors:
            all_errors.append(f"{card.bmc_id}: {err}")
    return all_errors

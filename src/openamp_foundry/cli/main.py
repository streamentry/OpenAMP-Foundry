from __future__ import annotations

from openamp_foundry.cli.commands.core import _run_generate_batch
from openamp_foundry.cli.commands.benchmark import _run_bench, _run_validate_scoring, _run_cluster_split_bench, _run_expert_ablation_bench, _run_selectivity_bench, _run_triage, _run_metrics_snapshot, _run_feature_decomp, _run_active_learning_bench, _run_active_learning_strategy_compare, _run_simulation_gate
from openamp_foundry.cli.commands.selection import _run_pilot_panel, _run_pilot_confident, _run_diversity_check, _run_select_batch, _run_batch_rationale
from openamp_foundry.cli.commands.external import _run_external_predict, _run_external_consensus
from openamp_foundry.cli.commands.qc import _run_synthesis_order, _run_presynth_qc
from openamp_foundry.cli.commands.reports import (
    _run_reviewer_questionnaire, _run_ip_report, _run_batch_pack, _run_gold_standard,
    _run_novelty_check_broad, _run_lab_result_report, _run_calibration_intake,
    _run_recalibration_gate, _run_recalibration_engine, _run_validate_policy_version,
    _run_calibration_audit, _run_calibration_overfit_check, _run_result_quality_filter,
    _run_synthetic_result_policy_check, _run_calibration_decision_checklist,
    _run_calibration_rollback_plan, _run_simulation_registry, _run_validate_simulation_result,
    _run_simulation_baseline_check, _run_adapter_gate_check, _run_simulation_provenance,
    _run_simulation_ensemble_check, _run_simulation_ci_report, _run_simulation_deprecation_check,
    _run_simulation_scope_check, _run_simulation_evidence_packet, _run_artifact_version,
    _run_candidate_manifest, _run_benchmark_card, _run_artifact_changelog, _run_integration_check,
    _run_adapter_check, _run_license_check, _run_artifact_compat_check, _run_adoption_scorecard,
    _run_reviewer_briefing_check, _run_audit_chain_check,     _run_pre_registration_check,
    _run_external_sharing_clearance_check,
    _run_rejection_reason_check,
    _run_negative_result_archive_check,
    _run_failed_candidate_batch_report_check,
    _run_reviewer_questionnaire_check,
    _run_domain_review_outcome_check,
    _run_hypothesis_outcome_check, _run_baseline_comparison_check, _run_negative_result_check,
    _run_experiment_priority_check, _run_calibration_performance_check, _run_prediction_drift_check,
    _run_calibration_improvement_check,
    _run_cross_batch_aggregator_check,
    _run_calibration_readiness_check,
    _run_batch_selection_proposal_check,
    _run_recalibration_refusal_check,
    _run_batch_outcome_summary_check,
    _run_pilot_batch_safety_clearance_check,
    _run_calibration_cycle_summary_check,
    _run_pilot_evidence_package_check,
    _run_pre_registration_entry_check,
    _run_recalibration_decision_log_check,
    _run_recalibration_rejection_summary_check,
    _run_synthetic_boundary_audit_record_check,
    _run_expert_review_example_package_check,
    _run_proof_ladder_level_certificate_check,
)
from openamp_foundry.cli.commands.gates import _run_gate_check, _run_release_gate_check
from openamp_foundry.cli.commands.reports import _run_contribution_check
from openamp_foundry.cli.commands.reports import _run_decision_log
from openamp_foundry.cli.commands.reports import _run_release_request_check
from openamp_foundry.cli.commands.reports import _run_coi_check
from openamp_foundry.cli.commands.reports import _run_rotation_plan_check
from openamp_foundry.cli.commands.reports import _run_security_report_check
from openamp_foundry.cli.commands.reports import _run_citation_check
from openamp_foundry.cli.commands.reports import _run_roadmap_sync_check
from openamp_foundry.cli.commands.reports import _run_advisory_review_check, _run_annual_review_check, _run_selection_rationale_check, _run_batch_priority_check, _run_pilot_package_check, _run_calibration_intake_check, _run_uncertainty_report_check, _run_preprint_bundle_check, _run_reproducibility_manifest_check, _run_candidate_summary_card_check, _run_multi_candidate_comparison_check, _run_dataset_release_check, _run_pipeline_decision_audit_check, _run_claim_to_evidence_check, _run_score_decomposition_check

import argparse
import json
from pathlib import Path

from openamp_foundry.evidence.batch_experiment_priority_ranker import validate_dict as validate_batch_experiment_priority_ranker_dict
from openamp_foundry.evidence.calibration_improvement_record import validate_dict as validate_calibration_improvement_record_dict
from openamp_foundry.evidence.candidate_selection_rationale import validate_dict as validate_candidate_selection_rationale_dict
from openamp_foundry.evidence.negative_result_dashboard import validate_dict as validate_negative_result_dashboard_dict
from openamp_foundry.evidence.negative_result_entry import validate_dict as validate_negative_result_entry_dict
from openamp_foundry.evidence.pilot_package_completeness_report import validate_dict as validate_pilot_package_completeness_dict
from openamp_foundry.evidence.post_experiment_calibration_intake import validate_dict as validate_post_experiment_calibration_intake_dict
from openamp_foundry.evidence.quality import assess_certificate_quality
from openamp_foundry.evidence.schemas import validate_json_schema
from openamp_foundry.pipeline import run_ranking_pipeline
from openamp_foundry.selection.ranking_policy import ranking_policy_payload
from openamp_foundry.utils.io import read_json


def build_parser() -> argparse.ArgumentParser:
    from openamp_foundry import __version__
    parser = argparse.ArgumentParser(prog="openamp-foundry")
    parser.add_argument("--version", action="version", version=f"openamp-foundry {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    rank = sub.add_parser("rank", help="Rank candidate peptides and generate evidence.")
    rank.add_argument("--candidates", required=True)
    rank.add_argument("--references", required=False)
    rank.add_argument("--out", required=True)
    rank.add_argument("--report", required=False)
    rank.add_argument("--cert-dir", required=False)
    rank.add_argument("--manifest", required=False)
    rank.add_argument("--config", default="configs/pipeline.yaml")
    rank.add_argument(
        "--ranking-mode",
        choices=["ensemble", "expert"],
        default="ensemble",
        help=(
            "Ranking mode: 'ensemble' (default, activity-weighted) or "
            "'expert' (safety-aware expert composite with selectivity, "
            "hemolysis risk, and helix-hinge analysis). Expert mode "
            "partially corrects the ensemble's anti-selective bias."
        ),
    )
    rank.add_argument(
        "--track-failures",
        action="store_true",
        default=False,
        help=(
            "Write failed_candidates.jsonl alongside the main output, "
            "documenting which candidates were rejected by each gate."
        ),
    )
    rank.add_argument(
        "--simulation-mode",
        choices=["off", "info"],
        default="off",
        help=(
            "Simulation mode: 'off' (default, no simulation scores), "
            "'info' (run MembraneProxy and StructureProxy, include "
            "scores in report — no ranking impact). 'weighted' mode "
            "is not yet available (see 'make simulation-gate')."
        ),
    )

    validate = sub.add_parser("validate", help="Validate a candidate certificate against JSON schema.")
    validate.add_argument("--certificate", required=True)
    validate.add_argument("--schema", required=True)

    validate_quality = sub.add_parser(
        "validate-cert-quality",
        help="Assess certificate quality tier: pass / warn / fail.",
    )
    validate_quality.add_argument("--certificate", required=True)
    validate_quality.add_argument(
        "--schema",
        default="schemas/candidate.schema.json",
        help="JSON Schema path (default: schemas/candidate.schema.json).",
    )

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

    cluster_split = bench_sub.add_parser(
        "cluster-split",
        help=(
            "Cluster-split retrospective AUROC benchmark with honest CI. "
            "Clusters near-duplicate AMPs, reports cluster-aware bootstrap CI "
            "(wider than standard CI when near-duplicates exist), and held-out "
            "recovery AUROC for near-duplicate cluster members."
        ),
    )
    cluster_split.add_argument(
        "--amp-csv",
        default="examples/validation/known_amps.csv",
        help="CSV of known AMPs (id, sequence, family, reference, label).",
    )
    cluster_split.add_argument(
        "--decoy-csv",
        default="examples/validation/random_background.csv",
        help="CSV of decoy peptides.",
    )
    cluster_split.add_argument(
        "--config",
        default="configs/pipeline.yaml",
    )
    cluster_split.add_argument(
        "--threshold",
        type=float,
        default=0.70,
        help="Similarity threshold for clustering (default: 0.70).",
    )
    cluster_split.add_argument(
        "--n-bootstrap",
        type=int,
        default=2000,
        help="Bootstrap resample count (default: 2000).",
    )
    cluster_split.add_argument(
        "--out",
        required=False,
        help="Optional JSON output path.",
    )

    expert_ablation = bench_sub.add_parser(
        "expert-ablation",
        help=(
            "Expert-vs-ensemble ablation: does the 7-component expert composite "
            "(selectivity, serum stability, helix hinge, motif novelty) beat the "
            "simple ensemble on AMP-vs-decoy discrimination? Reports per-component "
            "AUROC to identify signal-bearing vs noise components."
        ),
    )
    expert_ablation.add_argument(
        "--amp-csv",
        default="examples/validation/known_amps.csv",
        help="CSV of known AMPs (id, sequence, ...).",
    )
    expert_ablation.add_argument(
        "--decoy-csv",
        default="examples/validation/random_background.csv",
        help="CSV of decoy peptides.",
    )
    expert_ablation.add_argument(
        "--config",
        default="configs/pipeline.yaml",
    )
    expert_ablation.add_argument(
        "--n-bootstrap",
        type=int,
        default=2000,
        help="Bootstrap resample count (default: 2000).",
    )
    expert_ablation.add_argument(
        "--out",
        required=False,
        help="Optional JSON output path.",
    )

    selectivity = bench_sub.add_parser(
        "selectivity",
        help=(
            "Within-AMP selectivity benchmark: can pipeline scorers distinguish "
            "hemolytic AMPs (HC50 < 25 ug/mL) from selective AMPs (HC50 >= 100 ug/mL)? "
            "Tests whether the safety, selectivity, and synthesis components earn "
            "their keep on within-AMP ranking -- the task they were designed for."
        ),
    )
    selectivity.add_argument(
        "--hemolysis-csv",
        default="examples/validation/hemolysis_reference.csv",
        help="CSV with columns: id, sequence, family, hc50_ugml, hemolysis_class, reference.",
    )
    selectivity.add_argument(
        "--config",
        default="configs/pipeline.yaml",
    )
    selectivity.add_argument(
        "--n-bootstrap",
        type=int,
        default=2000,
        help="Bootstrap resample count (default: 2000).",
    )
    selectivity.add_argument(
        "--out",
        required=False,
        help="Optional JSON output path.",
    )

    triage = bench_sub.add_parser(
        "triage",
        help=(
            "Multi-class triage benchmark: can the pipeline rank "
            "selective AMPs > hemolytic AMPs > random decoys in a combined panel? "
            "Tests the v1.1 ROADMAP triage benchmark requirement."
        ),
    )
    triage.add_argument(
        "--hemolysis-csv",
        default="examples/validation/hemolysis_reference.csv",
        help="Hemolysis reference CSV (id,sequence,family,hc50_ugml,hemolysis_class,reference).",
    )
    triage.add_argument(
        "--decoy-csv",
        default="examples/validation/random_background.csv",
        help="Random background decoy CSV (id,sequence,family,source,label).",
    )
    triage.add_argument("--config", default="configs/pipeline.yaml")
    triage.add_argument("--n-bootstrap", type=int, default=2000)
    triage.add_argument(
        "--out",
        required=False,
        help="Optional JSON output path.",
    )

    feature_decomp = bench_sub.add_parser(
        "feature-decomp",
        help=(
            "Per-feature selective_vs_hemolytic decomposition: tests every "
            "physicochemical feature individually for hemolysis discrimination. "
            "Identifies which features carry signal the composite scorers miss."
        ),
    )
    feature_decomp.add_argument(
        "--hemolysis-csv",
        default="examples/validation/hemolysis_reference.csv",
        help="Hemolysis reference CSV (id,sequence,family,hc50_ugml,hemolysis_class,reference).",
    )
    feature_decomp.add_argument("--n-bootstrap", type=int, default=2000)
    feature_decomp.add_argument(
        "--out",
        required=False,
        help="Optional JSON output path.",
    )

    metrics_snapshot = bench_sub.add_parser(
        "metrics-snapshot",
        help=(
            "Build a machine-readable snapshot of the repo's current benchmark truth. "
            "Use this to refresh docs/evidence/METRICS_CURRENT.md evidence and catch number drift."
        ),
    )
    metrics_snapshot.add_argument(
        "--amp-csv",
        default="examples/validation/known_amps.csv",
    )
    metrics_snapshot.add_argument(
        "--decoy-csv",
        default="examples/validation/random_background.csv",
    )
    metrics_snapshot.add_argument(
        "--hemolysis-csv",
        default="examples/validation/hemolysis_reference.csv",
    )
    metrics_snapshot.add_argument("--config", default="configs/pipeline.yaml")
    metrics_snapshot.add_argument("--phase3-config", default="configs/phase3.yaml")
    metrics_snapshot.add_argument("--threshold", type=float, default=0.70)
    metrics_snapshot.add_argument("--n-bootstrap", type=int, default=2000)
    metrics_snapshot.add_argument(
        "--out",
        required=False,
        help="Optional JSON output path.",
    )

    active_learning = bench_sub.add_parser(
        "active-learning",
        help=(
            "Active-learning recovery benchmark: hide known active AMPs from the "
            "selector and measure how many rounds it takes to recover them. "
            "Compares against random baseline. "
            "Generates synthetic data if no pool CSV is provided."
        ),
    )
    active_learning.add_argument(
        "--pool-csv",
        default=None,
        help="Optional labelled pool CSV (requires 'label' column: 1=active, 0=inactive).",
    )
    active_learning.add_argument(
        "--n-hidden",
        type=int,
        default=3,
        help="Number of active candidates to hide (default: 3).",
    )
    active_learning.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Batch size per selection round (default: 5).",
    )
    active_learning.add_argument(
        "--max-rounds",
        type=int,
        default=5,
        help="Maximum selection rounds (default: 5).",
    )
    active_learning.add_argument(
        "--rng-seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )

    strategy_compare = bench_sub.add_parser(
        "strategy-compare",
        help=(
            "Compare active-learning selection strategies (exploitation, exploration, "
            "diversity, combined, random) on the same synthetic pool. Prevents "
            "one-selector bias by making strategy comparison transparent."
        ),
    )
    strategy_compare.add_argument(
        "--n-total",
        type=int,
        default=50,
        help="Total candidate pool size (default: 50).",
    )
    strategy_compare.add_argument(
        "--n-active",
        type=int,
        default=10,
        help="Number of active candidates in pool (default: 10).",
    )
    strategy_compare.add_argument(
        "--n-hidden",
        type=int,
        default=3,
        help="Number of active candidates to hide (default: 3).",
    )
    strategy_compare.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Batch size per selection round (default: 5).",
    )
    strategy_compare.add_argument(
        "--max-rounds",
        type=int,
        default=5,
        help="Maximum selection rounds (default: 5).",
    )
    strategy_compare.add_argument(
        "--rng-seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    strategy_compare.add_argument(
        "--out-json",
        default=None,
        help="Optional JSON output path.",
    )
    strategy_compare.add_argument(
        "--out-md",
        default=None,
        help="Optional Markdown output path.",
    )

    simulation_gate = bench_sub.add_parser(
        "simulation-gate",
        help=(
            "Validate whether virtual-assay weighted mode is allowed. "
            "Reads ablation artifacts and fails closed unless simulations "
            "improve on both benchmark views."
        ),
    )
    simulation_gate.add_argument(
        "--amp-vs-decoy-json",
        required=True,
        help="Ablation JSON from scripts/benchmark_simulation_ablation.py --mode amp-vs-decoy.",
    )
    simulation_gate.add_argument(
        "--within-amp-json",
        required=True,
        help="Ablation JSON from scripts/benchmark_simulation_ablation.py --mode within-amp.",
    )
    simulation_gate.add_argument(
        "--required-mode",
        choices=["off", "info", "weighted"],
        default="weighted",
        help="Requested simulation integration mode (default: weighted).",
    )
    simulation_gate.add_argument(
        "--out",
        required=False,
        help="Optional JSON output path.",
    )

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
    pilot.add_argument(
        "--min-per-structural-class",
        type=int,
        default=0,
        help=(
            "Optional floor per coarse structural class before seed/remainder fill. "
            "Use to compensate for the documented v0.5.37 helic/charge bias. "
            "Default 0 preserves priority-only behavior."
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
            "Automates Playwright execution of external AMP predictors "
            "(CAMPR4, AMPScanner v2, AntiCP2, HemoFinder) and consolidates results."
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

    # Sprint 3 — External predictor consensus
    external_consensus = sub.add_parser(
        "external-consensus",
        help="Aggregate external predictor results into per-candidate consensus verdicts.",
    )
    external_consensus.add_argument(
        "--pilot-csv",
        default="outputs/pilot_panel.csv",
        help="Pilot panel CSV.",
    )
    external_consensus.add_argument(
        "--results-csv",
        required=True,
        help="CSV with per-candidate binary results (Y/N) for each external tool.",
    )
    external_consensus.add_argument(
        "--out",
        default="outputs/external_consensus_report.md",
        help="Output markdown report path.",
    )

    # Sprint 4 — Reviewer questionnaire
    reviewer_questionnaire = sub.add_parser(
        "reviewer-questionnaire",
        help="Generate pre-populated reviewer questionnaire for each pilot candidate.",
    )
    reviewer_questionnaire.add_argument(
        "--panel-csv",
        default="outputs/confident_panel.csv",
        help="Panel CSV.",
    )
    reviewer_questionnaire.add_argument(
        "--out",
        default="outputs/questionnaire",
        help="Output directory (one .md per candidate).",
    )

    # Sprint 5 — Gate check
    gate_check = sub.add_parser(
        "gate-check",
        help="Run pipeline decision gates and report pass/fail status.",
    )
    gate_check.add_argument(
        "--gate",
        type=int,
        default=0,
        help="Specific gate number to check (1-7), or 0 for all gates.",
    )
    gate_check.add_argument(
        "--validation-json",
        default="outputs/validate_scoring_report.json",
        help="Path to validate-scoring output JSON.",
    )

    # Sprint 6 — IP report
    ip_report = sub.add_parser(
        "ip-report",
        help="Generate intellectual property report with novelty claim strength analysis.",
    )
    ip_report.add_argument(
        "--panel-csv",
        default="outputs/confident_panel.csv",
        help="Panel CSV.",
    )
    ip_report.add_argument(
        "--novelty-csv",
        default="outputs/novelty_audit_full.csv",
        help="Novelty audit CSV (output of run_novelty_audit.py).",
    )
    ip_report.add_argument(
        "--out",
        default="outputs/ip_report.md",
        help="Output markdown report path.",
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

    lab_result_report = sub.add_parser(
        "lab-result-report",
        help=(
            "Build a reproducible summary report from validated wet-lab result JSON files. "
            "This is a review artifact only, not a biological claim engine."
        ),
    )
    lab_result_report.add_argument(
        "--results-dir",
        required=True,
        help="Directory containing lab result JSON files matching schemas/lab_result.schema.json.",
    )
    lab_result_report.add_argument(
        "--out-json",
        required=True,
        help="Output path for machine-readable report JSON.",
    )
    lab_result_report.add_argument(
        "--out-md",
        required=False,
        help="Optional output path for markdown review report.",
    )

    calibration_intake = sub.add_parser(
        "calibration-intake",
        help=(
            "Join a pilot panel CSV (computational predictions) with a directory of "
            "validated lab result JSON files (experimental outcomes) and produce a "
            "calibration intake report. Descriptive only. Does NOT trigger "
            "recalibration, weight updates, or selection-rule changes. Below the "
            "minimum cohort size no aggregate point estimate is reported."
        ),
    )
    calibration_intake.add_argument(
        "--panel",
        required=True,
        help="Pilot panel CSV (candidate_id + score columns).",
    )
    calibration_intake.add_argument(
        "--results-dir",
        required=True,
        help="Directory containing lab result JSON files matching schemas/lab_result.schema.json.",
    )
    calibration_intake.add_argument(
        "--out-json",
        required=True,
        help="Output path for machine-readable calibration intake JSON.",
    )
    calibration_intake.add_argument(
        "--out-md",
        required=False,
        help="Optional output path for markdown calibration intake summary.",
    )

    recalibration_gate = sub.add_parser(
        "recalibration-gate",
        help=(
            "Evaluate the recalibration gate against a calibration intake "
            "report and the pre-registered policy. Descriptive only -- does "
            "NOT trigger any weight update or scoring change. Returns "
            "may_recalibrate=true only when every minimum_condition rule "
            "passes. Exit code is 0 when may_recalibrate is true and 3 "
            "otherwise."
        ),
    )
    recalibration_gate.add_argument(
        "--intake-report",
        required=True,
        help="Path to calibration-intake JSON (output of `calibration-intake`).",
    )
    recalibration_gate.add_argument(
        "--policy",
        default="configs/recalibration_policy.yaml",
        help="Path to the pre-registered recalibration policy YAML.",
    )
    recalibration_gate.add_argument(
        "--intake-report-date",
        default=None,
        help=(
            "ISO date (YYYY-MM-DD) for the intake report; used to evaluate "
            "the COOLDOWN_DAYS rate limit."
        ),
    )
    recalibration_gate.add_argument(
        "--previous-recalibration-at",
        default=None,
        help=(
            "ISO date (YYYY-MM-DD) of the previous successful recalibration "
            "for the same scoring config. Omit if no prior recalibration."
        ),
    )
    recalibration_gate.add_argument(
        "--weight-l1-distance",
        default=None,
        help=(
            "Optional float for the L1 distance between current and proposed "
            "scoring weights. When set, the WEIGHT_CHANGE_L1_BUDGET rate "
            "limit becomes evaluable."
        ),
    )
    recalibration_gate.add_argument(
        "--project-root",
        default=None,
        help=(
            "Optional path used to resolve relative reviewer-artefact paths. "
            "Defaults to the current working directory."
        ),
    )
    recalibration_gate.add_argument(
        "--out-json",
        default=None,
        help="Optional output path for the gate verdict JSON.",
    )
    recalibration_gate.add_argument(
        "--out-md",
        default=None,
        help="Optional output path for the gate verdict Markdown report.",
    )

    recalibration_engine = sub.add_parser(
        "recalibration-engine",
        help=(
            "Compute proposed weight deltas from a calibration intake report + "
            "gate verdict. Does NOT apply changes -- returns a proposal for "
            "human review. Raises PolicyViolationError if may_recalibrate=False."
        ),
    )
    recalibration_engine.add_argument(
        "--intake-report",
        required=True,
        help="Path to calibration-intake JSON.",
    )
    recalibration_engine.add_argument(
        "--gate-verdict",
        required=True,
        help="Path to gate verdict JSON.",
    )
    recalibration_engine.add_argument(
        "--current-weights",
        required=True,
        help=(
            "JSON dict mapping scorer names to current weights "
            '(e.g. \'{"activity": 0.40, "safety": 0.25}\').'
        ),
    )
    recalibration_engine.add_argument(
        "--l1-budget",
        type=float,
        default=0.10,
        help="Maximum allowed L1 weight delta (default: 0.10).",
    )
    recalibration_engine.add_argument(
        "--out-json",
        default=None,
        help="Optional output path for the proposal JSON.",
    )
    recalibration_engine.add_argument(
        "--out-md",
        default=None,
        help="Optional output path for the proposal Markdown report.",
    )
    recalibration_engine.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help=(
            "Preview proposed weight changes without writing output files. "
            "Prints a diff table and exits. No side effects."
        ),
    )

    calibration_audit = sub.add_parser(
        "calibration-audit",
        help=(
            "Run a consistency audit across the calibration pipeline — "
            "intake report, gate verdict, engine proposal, and combined "
            "recalibration report. Checks that counts, verdicts, "
            "proposals, and timestamps are internally consistent."
        ),
    )
    calibration_audit.add_argument(
        "--intake-report",
        default=None,
        help="Path to the calibration intake JSON report.",
    )
    calibration_audit.add_argument(
        "--gate-verdict",
        default=None,
        help="Path to the recalibration gate verdict JSON.",
    )
    calibration_audit.add_argument(
        "--engine-proposal",
        default=None,
        help="Path to the recalibration engine proposal JSON.",
    )
    calibration_audit.add_argument(
        "--recalibration-report",
        default=None,
        help="Path to the combined recalibration report JSON.",
    )
    calibration_audit.add_argument(
        "--out-json",
        default=None,
        help="Optional output path for the audit report JSON.",
    )
    calibration_audit.add_argument(
        "--out-md",
        default=None,
        help="Optional output path for the audit report Markdown.",
    )

    novelty_broad = sub.add_parser(
        "novelty-check-broad",
        help=(
            "Check candidate novelty against a curated AMP reference database (72+ sequences). "
            "The standard novelty score compares against 45 seed sequences only; this command "
            "compares against the full amp_curated_references.csv to detect near-copies of "
            "published AMPs that the seed-based score may miss."
        ),
    )
    novelty_broad.add_argument(
        "--panel-csv",
        required=True,
        help="Pilot panel CSV (candidate_id + sequence columns required).",
    )
    novelty_broad.add_argument(
        "--references-csv",
        default="examples/known_reference/amp_curated_references.csv",
        help="Curated AMP reference CSV (default: amp_curated_references.csv).",
    )
    novelty_broad.add_argument(
        "--out",
        default="outputs/novelty_broad_report.md",
        help="Output markdown report path.",
    )
    novelty_broad.add_argument(
        "--threshold-known",
        type=float,
        default=0.70,
        help="Similarity >= this value → KNOWN_VARIANT (default: 0.70).",
    )
    novelty_broad.add_argument(
        "--threshold-close",
        type=float,
        default=0.50,
        help="Similarity >= this value → CLOSE_RELATIVE (default: 0.50).",
    )

    validate_policy_version = sub.add_parser(
        "validate-policy-version",
        help=(
            "Validate a proposed recalibration policy version against its "
            "predecessor. Checks version increment, locked-changes "
            "preservation, and decision-log recency. Exit code 0 if valid, "
            "3 if invalid."
        ),
    )
    validate_policy_version.add_argument(
        "--current-policy",
        required=True,
        help="Path to the proposed new policy YAML.",
    )
    validate_policy_version.add_argument(
        "--previous-policy",
        required=True,
        help="Path to the previously committed policy YAML.",
    )
    validate_policy_version.add_argument(
        "--decision-log-dir",
        default=None,
        help="Optional directory containing DECISION_LOG_<date>.md files.",
    )
    validate_policy_version.add_argument(
        "--today",
        default=None,
        help="ISO date (YYYY-MM-DD) for 'today'. Defaults to actual today.",
    )

    # ── Calibration overfit check ────────────────────────────────────
    calibration_overfit = sub.add_parser(
        "calibration-overfit-check",
        help=(
            "Check whether calibration cohort sizes are adequate relative "
            "to model parameters. Prevents false learning from under-powered "
            "cohorts. Dry-lab only — does not measure biological activity."
        ),
    )
    calibration_overfit.add_argument(
        "--cohort-sizes",
        required=True,
        type=lambda s: [int(x) for x in s.split(",")],
        help="Comma-separated cohort sizes (e.g. '12,45,30').",
    )
    calibration_overfit.add_argument(
        "--model-params",
        required=True,
        type=int,
        help="Number of trainable model parameters.",
    )
    calibration_overfit.add_argument(
        "--n-features",
        required=True,
        type=int,
        help="Number of input features.",
    )
    calibration_overfit.add_argument(
        "--min-recommended",
        type=int,
        default=30,
        help="Minimum recommended cohort size (default: 30).",
    )
    calibration_overfit.add_argument(
        "--out-json",
        default=None,
        help="Optional JSON output path.",
    )
    calibration_overfit.add_argument(
        "--out-md",
        default=None,
        help="Optional Markdown output path.",
    )

    # ── Batch-2 rationale report ─────────────────────────────────────
    batch_rationale = sub.add_parser(
        "batch-rationale",
        help=(
            "Generate a batch-2 selection rationale report. Creates a "
            "synthetic candidate pool, runs the batch-2 selector, and "
            "explains each selected candidate in terms of exploit / "
            "explore / diversity roles."
        ),
    )
    batch_rationale.add_argument(
        "--n-total", type=int, default=50,
        help="Total synthetic pool size (default: 50).",
    )
    batch_rationale.add_argument(
        "--n-active", type=int, default=10,
        help="Number of active (label=1) candidates (default: 10).",
    )
    batch_rationale.add_argument(
        "--batch-size", type=int, default=10,
        help="Desired batch-2 size (default: 10).",
    )
    batch_rationale.add_argument(
        "--safety-threshold", type=float, default=0.5,
        help="Minimum safety score (default: 0.5).",
    )
    batch_rationale.add_argument(
        "--selectivity-threshold", type=float, default=0.5,
        help="Minimum selectivity score (default: 0.5).",
    )
    batch_rationale.add_argument(
        "--ensemble-weight", type=float, default=0.40,
        help="Ensemble weight (default: 0.40).",
    )
    batch_rationale.add_argument(
        "--uncertainty-weight", type=float, default=0.30,
        help="Uncertainty weight (default: 0.30).",
    )
    batch_rationale.add_argument(
        "--diversity-weight", type=float, default=0.30,
        help="Diversity weight (default: 0.30).",
    )
    batch_rationale.add_argument(
        "--min-uncertainty-probes", type=int, default=1,
        help="Minimum uncertainty probes in selection (default: 1).",
    )
    batch_rationale.add_argument(
        "--rng-seed", type=int, default=42,
        help="RNG seed for reproducibility (default: 42).",
    )
    batch_rationale.add_argument(
        "--out-json",
        default=None,
        help="Optional JSON output path.",
    )
    batch_rationale.add_argument(
        "--out-md",
        default=None,
        help="Optional Markdown output path.",
    )

    # ── Batch-2 selector ──────────────────────────────────────────────
    select_batch = sub.add_parser(
        "select-batch",
        help=(
            "Select the next batch of candidates for lab testing after "
            "an initial batch has been assayed and the recalibration "
            "pipeline has run. Uses uncertainty sampling + diversity + "
            "safety gating to pick informative candidates."
        ),
    )
    select_batch.add_argument(
        "--candidates",
        required=True,
        help="Path to the full candidate pool CSV (same format as pilot panel).",
    )
    select_batch.add_argument(
        "--batch-1-ids",
        required=True,
        help="Comma-separated candidate IDs already tested in batch 1.",
    )
    select_batch.add_argument(
        "--n",
        type=int,
        default=10,
        help="Desired batch-2 size (default: 10).",
    )
    select_batch.add_argument(
        "--safety-threshold",
        type=float,
        default=0.5,
        help="Minimum safety score (0-1) for eligibility (default: 0.5).",
    )
    select_batch.add_argument(
        "--selectivity-threshold",
        type=float,
        default=0.5,
        help="Minimum rich_selectivity score for eligibility (default: 0.5).",
    )
    select_batch.add_argument(
        "--ensemble-weight",
        type=float,
        default=0.40,
        help="Weight for ensemble score in combined rank (default: 0.40).",
    )
    select_batch.add_argument(
        "--uncertainty-weight",
        type=float,
        default=0.30,
        help="Weight for uncertainty score (default: 0.30).",
    )
    select_batch.add_argument(
        "--diversity-weight",
        type=float,
        default=0.30,
        help="Weight for diversity vs batch-1 (default: 0.30).",
    )
    select_batch.add_argument(
        "--min-uncertainty-probes",
        type=int,
        default=1,
        help="At least this many high-uncertainty candidates in the selection (default: 1).",
    )
    select_batch.add_argument(
        "--out",
        required=True,
        help="Output path for the batch-2 manifest JSON.",
    )

    # ── Result quality filter ─────────────────────────────────────
    result_quality = sub.add_parser(
        "result-quality-filter",
        help=(
            "Filter lab results by quality flags. Low-quality outcomes "
            "cannot drive calibration updates — garbage results must not "
            "update the scoring model. Dry-lab only."
        ),
    )
    result_quality.add_argument(
        "--results-json",
        required=True,
        help="Path to JSON file with list of {candidate_id, flags} objects.",
    )
    result_quality.add_argument(
        "--out-json",
        default=None,
        help="Optional output path for filtered results JSON.",
    )
    result_quality.add_argument(
        "--out-md",
        default=None,
        help="Optional output path for markdown report.",
    )

    # ── Synthetic result policy check ──────────────────────────────
    srp = sub.add_parser(
        "synthetic-result-policy-check",
        help=(
            "Check whether synthetic/simulation results are used to raise "
            "a candidate's proof-ladder level. Anti-overclaim safeguard. "
            "Dry-lab only."
        ),
    )
    srp.add_argument(
        "--proposals-json",
        required=True,
        help=(
            "Path to JSON file with list of {candidate_id, current_level, "
            "proposed_level, evidence_source} objects."
        ),
    )
    srp.add_argument(
        "--out-json",
        default=None,
        help="Optional output path for policy check JSON.",
    )
    srp.add_argument(
        "--out-md",
        default=None,
        help="Optional output path for policy check markdown report.",
    )

    # ── Calibration rollback plan ────────────────────────────────────
    rbp = sub.add_parser(
        "calibration-rollback-plan",
        help=(
            "Generate a recalibration rollback plan. Documents the triggers, "
            "steps, and responsible parties for reverting a recalibration "
            "that degrades performance. Dry-lab only."
        ),
    )
    rbp.add_argument("--plan-id", required=True, help="Unique plan identifier (e.g. RBK-2026-001).")
    rbp.add_argument("--version", required=True, help="Calibration version to roll back (e.g. v0.5.87).")
    rbp.add_argument(
        "--triggered-by",
        required=True,
        help="Comma-separated trigger IDs (e.g. 'RT-01,RT-02').",
    )
    rbp.add_argument("--notes", default="", help="Optional notes about the rollback event.")
    rbp.add_argument("--out-json", default=None, help="Optional JSON output path.")
    rbp.add_argument("--out-md", default=None, help="Optional Markdown output path.")

    # ── Calibration decision review checklist ────────────────────────
    cdc = sub.add_parser(
        "calibration-decision-checklist",
        help=(
            "Build a structured calibration decision review checklist. "
            "Evaluates which required items are missing and sets overall_pass. "
            "Dry-lab only."
        ),
    )
    cdc.add_argument("--checklist-id", required=True, help="Unique checklist identifier (e.g. CHK-2026-001).")
    cdc.add_argument("--date", required=True, help="Review date in YYYY-MM-DD format.")
    cdc.add_argument("--reviewer", required=True, help="Name or role of the human reviewer.")
    cdc.add_argument(
        "--responses-json",
        required=True,
        help="Path to a JSON file mapping item IDs to boolean responses "
        '(e.g. {"G9-01": true, "G9-02": false, ...}).',
    )
    cdc.add_argument("--out-json", default=None, help="Optional output path for the checklist JSON.")
    cdc.add_argument("--out-md", default=None, help="Optional output path for the checklist Markdown.")

    # ── Simulation module registry ───────────────────────────────────
    simreg = sub.add_parser(
        "simulation-registry",
        help="Display the simulation module registry (status and evidence level of virtual assay modules). Dry-lab only.",
    )
    simreg.add_argument(
        "--list", action="store_true", default=True,
        dest="list_modules",
        help="List all registered modules (default).",
    )
    simreg.add_argument(
        "--show", type=str, default=None,
        metavar="MODULE_ID",
        help="Show details for a specific module ID.",
    )
    simreg.add_argument(
        "--status", type=str, default=None,
        choices=["active", "experimental", "deprecated", "unavailable"],
        help="Filter by status: active, experimental, deprecated, unavailable.",
    )
    simreg.add_argument(
        "--min-evidence", type=int, default=None,
        dest="min_evidence",
        help="Minimum evidence level (1-6) to filter by.",
    )
    simreg.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Simulation result validation ──────────────────────────────────
    vsr = sub.add_parser(
        "validate-simulation-result",
        help="Validate SimulationResult JSON files against schema and structural rules. Dry-lab only.",
    )
    vsr.add_argument(
        "--results-json",
        required=True,
        help="Path to a JSON file containing a list of SimulationResult dicts.",
    )
    vsr.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Enable strict validation (rejects dummy/stub modules, uncertainty=1.0, empty validated_against).",
    )
    vsr.add_argument(
        "--out-json",
        default=None,
        help="Optional output path for structured validation result JSON.",
    )

    # ── Simulation baseline check (H3) ────────────────────────────────
    sbc = sub.add_parser(
        "simulation-baseline-check",
        help=(
            "Check whether a simulation module beats its cheapest declared baseline. "
            "Caps evidence level if baseline not beaten. Dry-lab only."
        ),
    )
    sbc.add_argument(
        "--module-id", type=str, required=True,
        help="Module ID to check (e.g. membrane_proxy).",
    )
    sbc.add_argument(
        "--claimed-level", type=int, required=True,
        choices=range(1, 7),
        help="Claimed evidence level (1-6).",
    )
    sbc.add_argument(
        "--baseline-beaten", type=str, required=True,
        choices=["true", "false"],
        help="Whether the baseline has been beaten (true or false).",
    )
    sbc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Adapter gate check (H4) ──────────────────────────────────────
    agc = sub.add_parser(
        "adapter-gate-check",
        help=(
            "Check whether a simulation adapter passes the fail-closed gate. "
            "Dry-lab only."
        ),
    )
    agc.add_argument("--module-id", type=str, required=True, help="Module ID to check.")
    agc.add_argument(
        "--timeout", type=str, default="false",
        choices=["true", "false"],
        help="Whether a timeout occurred (default: false).",
    )
    agc.add_argument(
        "--connection-refused", type=str, default="false",
        choices=["true", "false"],
        help="Whether connection was refused (default: false).",
    )
    agc.add_argument(
        "--schema-errors", type=str, default="[]",
        help="JSON array of schema error strings (default: []).",
    )
    agc.add_argument(
        "--module-unavailable", type=str, default="false",
        choices=["true", "false"],
        help="Whether the module is unavailable (default: false).",
    )
    agc.add_argument(
        "--baseline-beaten", type=str, default=None,
        choices=["true", "false"],
        help="Whether the baseline was beaten (optional).",
    )
    agc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Simulation-result provenance (H5) ────────────────────────────────
    sp = sub.add_parser(
        "simulation-provenance",
        help=(
            "Generate a simulation-result provenance record with SHA-256 "
            "input and result hashes. Dry-lab only."
        ),
    )
    sp.add_argument("--run-id", type=str, required=True, help="Unique run ID (e.g. UUID).")
    sp.add_argument("--module-id", type=str, required=True, help="Module ID (e.g. membrane_proxy).")
    sp.add_argument("--module-version", type=str, required=True, help="Module version (e.g. 0.1.0).")
    sp.add_argument("--timestamp-utc", type=str, required=True, help="ISO 8601 UTC timestamp.")
    sp.add_argument("--input-sequence", type=str, required=True, help="Input peptide sequence.")
    sp.add_argument("--scores-json", type=str, required=True, help="JSON object of str→float scores.")
    sp.add_argument("--calibration-set", type=str, default=None, help="Optional calibration set identifier.")
    sp.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Simulation-ensemble agreement check (H6) ─────────────────────────
    sec = sub.add_parser(
        "simulation-ensemble-check",
        help=(
            "Check agreement across multiple simulation results for a sequence. "
            "When multiple simulation modules independently agree on a candidate, "
            "that agreement is stronger evidence than a single module alone. "
            "Dry-lab only."
        ),
    )
    sec.add_argument("--sequence", type=str, required=True, help="Peptide sequence to check.")
    sec.add_argument(
        "--results-json", type=str, required=True,
        help="JSON array of SimulationResult dicts.",
    )
    sec.add_argument(
        "--score-key", type=str, default="binding_energy",
        help="Score key to extract from each result's scores dict (default: binding_energy).",
    )
    sec.add_argument(
        "--threshold", type=float, default=0.2,
        help="Agreement threshold (max score range for agreement, default: 0.2).",
    )
    sec.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Simulation deprecation check (H8) ────────────────────────────
    sdc = sub.add_parser(
        "simulation-deprecation-check",
        help=(
            "Check whether simulation modules are deprecated or unavailable. "
            "Blocks deprecated modules from contributing to evidence packets. "
            "Dry-lab only."
        ),
    )
    sdc.add_argument(
        "--module-ids", type=str, required=True,
        help="Comma-separated module IDs (e.g. membrane_proxy,dummy_membrane_proxy).",
    )
    sdc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Simulation-scope coverage check (H9) ─────────────────────────
    ssc = sub.add_parser(
        "simulation-scope-check",
        help=(
            "Check whether a simulation module covers all requested biological scopes. "
            "Flags out-of-scope results so they are not silently trusted. "
            "Dry-lab only."
        ),
    )
    ssc.add_argument(
        "--module-id", type=str, required=True,
        help="Module ID to check (e.g. membrane_proxy).",
    )
    ssc.add_argument(
        "--requested-scopes", type=str, required=True,
        help="Comma-separated scopes (e.g. bacterial_binding,fungal_binding).",
    )
    ssc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Simulation-evidence packet assembler (H10 — Phase H capstone) ─
    sep = sub.add_parser(
        "simulation-evidence-packet",
        help=(
            "Assemble all simulation discipline checks into a single auditable "
            "evidence packet showing why a simulation result is trustworthy "
            "enough to support a given evidence level. Dry-lab only."
        ),
    )
    sep.add_argument(
        "--module-id", type=str, required=True,
        help="Module ID (validated against result.module).",
    )
    sep.add_argument(
        "--result-json", type=str, required=True,
        help="JSON string of a SimulationResult dict.",
    )
    sep.add_argument(
        "--requested-scopes", type=str, required=True,
        help="Comma-separated scopes (e.g. bacterial_membrane_binding,fungal_binding).",
    )
    sep.add_argument(
        "--claimed-level", type=int, required=True,
        choices=range(1, 7),
        help="Claimed evidence level (1-6).",
    )
    sep.add_argument(
        "--baseline-beaten", type=str, required=True,
        choices=["true", "false"],
        help="Whether the baseline has been beaten (true or false).",
    )
    sep.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Artifact versioning (Phase I I1) ─────────────────────────────
    av = sub.add_parser(
        "artifact-version",
        help=(
            "Display artifact versioning information for schemas and "
            "machine-readable artifacts. Dry-lab only."
        ),
    )
    av.add_argument(
        "--list", action="store_true", default=False, dest="list_artifacts",
        help="List all versioned artifacts (default action).",
    )
    av.add_argument(
        "--show", type=str, default=None, metavar="ARTIFACT_NAME",
        help="Show details for a specific artifact by name.",
    )
    av.add_argument(
        "--tier", type=str, default=None,
        choices=["stable", "experimental", "internal"],
        help="Filter artifacts by stability tier.",
    )
    av.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Artifact changelog (Phase I I4) ──────────────────────────────
    acl = sub.add_parser(
        "artifact-changelog",
        help=(
            "Display the evidence-certificate changelog — a structured "
            "record of artifact additions, changes, deprecations, and "
            "removals for backward compatibility. Dry-lab only."
        ),
    )
    acl.add_argument(
        "--artifact", type=str, default=None,
        help="Filter by artifact name.",
    )
    acl.add_argument(
        "--version", type=str, default=None,
        help="Filter by version (MAJOR.MINOR.PATCH).",
    )
    acl.add_argument(
        "--change-type", type=str, default=None,
        choices=["added", "changed", "deprecated", "removed", "fixed", "security"],
        help="Filter by change type.",
    )
    acl.add_argument(
        "--breaking-only", action="store_true", default=False,
        help="Show only breaking changes.",
    )
    acl.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Candidate manifest (Phase I I2) ──────────────────────────────
    cm = sub.add_parser(
        "candidate-manifest",
        help=(
            "Build and optionally validate a candidate manifest — the core "
            "interoperable artifact describing a dry-lab candidate. Dry-lab only."
        ),
    )
    cm.add_argument("--candidate-id", type=str, required=True, help="Candidate identifier (required).")
    cm.add_argument("--sequence", type=str, required=True, help="Amino acid sequence (required).")
    cm.add_argument("--evidence-level", type=str, required=True, help="Proof-ladder level 1-6 (required).")
    cm.add_argument("--scopes", type=str, required=True, help="Comma-separated scopes (required).")
    cm.add_argument("--scores-json", type=str, required=True, help="JSON object of score name→value (required).")
    cm.add_argument("--uncertainty", type=float, required=True, help="Uncertainty 0.0-1.0 (required).")
    cm.add_argument("--source-modules", type=str, required=True, help="Comma-separated source modules (required).")
    cm.add_argument("--validate", action="store_true", default=False, help="Run validate_candidate_manifest.")
    cm.add_argument("--format", type=str, default="text", choices=["text", "json"], help="Output format (default: text).")

    # ── Benchmark card (Phase I I3) ──────────────────────────────────
    bc = sub.add_parser(
        "benchmark-card",
        help=(
            "Create a benchmark card — a machine-readable artifact describing "
            "what was benchmarked, what the baseline was, what the result was, "
            "and what claims are supported. Dry-lab only."
        ),
    )
    bc.add_argument("--benchmark-id", type=str, required=True, help="Benchmark identifier (required).")
    bc.add_argument("--benchmark-name", type=str, required=True, help="Human-readable benchmark name (required).")
    bc.add_argument("--metric", type=str, required=True, help="Metric name (e.g. AUROC, AUPRC) (required).")
    bc.add_argument("--metric-value", type=float, required=True, help="Observed metric value (required).")
    bc.add_argument("--baseline-name", type=str, required=True, help="Baseline name (required).")
    bc.add_argument("--baseline-value", type=float, required=True, help="Baseline metric value (required).")
    bc.add_argument("--dataset", type=str, required=True, help="Dataset name or identifier (required).")
    bc.add_argument("--dataset-size", type=int, required=True, help="Number of samples in dataset (required).")
    bc.add_argument("--validate", action="store_true", default=False, help="Run validate_benchmark_card.")
    bc.add_argument("--format", type=str, default="text", choices=["text", "json"], help="Output format (default: text).")

    # ── Integration check (Phase I I5) ──────────────────────────────
    ic = sub.add_parser(
        "integration-check",
        help=(
            "Validate a downstream integration attempt against a candidate "
            "manifest. Runs 5 required checks: manifest_schema_valid, "
            "evidence_level_in_range, dry_lab_only_acknowledged, "
            "safety_flags_reviewed, baseline_comparison_present. Dry-lab only."
        ),
    )
    ic.add_argument(
        "--manifest-json", type=str, required=True,
        help="JSON string of a candidate manifest dict (required).",
    )
    ic.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Adapter declaration check (Phase I I6) ─────────────────────────
    ac = sub.add_parser(
        "adapter-check",
        help=(
            "Validate an adapter declaration against the Adapter Author Guide "
            "contract. Checks mode, output_status, ranking_effect, "
            "release_status, dry_lab_only, baseline comparison, network call "
            "documentation, and uncertainty. Dry-lab only."
        ),
    )
    ac.add_argument(
        "--adapter-json", type=str, required=True,
        help="JSON string of an adapter declaration dict (required).",
    )
    ac.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Data license check (Phase I I7) ──────────────────────────────
    lc = sub.add_parser(
        "license-check",
        help=(
            "Validate a data license declaration for an external data source. "
            "Prevents hidden legal risk by requiring explicit license declarations. "
            "Dry-lab only."
        ),
    )
    lc.add_argument(
        "--source-json", type=str, required=True,
        help="JSON string of a DataLicenseDeclaration dict (required).",
    )
    lc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Contribution intake check (Phase I I9) ──────────────────────
    cic = sub.add_parser(
        "contribution-check",
        help=(
            "Validate a proposed institutional contribution intake before "
            "submission. Checks minimum required fields for each contribution "
            "type. Dry-lab only."
        ),
    )
    cic.add_argument(
        "--intake-json", type=str, required=True,
        help="JSON string of a ContributionIntake dict (required).",
    )
    cic.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Artifact compatibility check (Phase I I8) ────────────────────
    acc = sub.add_parser(
        "artifact-compat-check",
        help=(
            "Run cross-artifact schema compatibility checks. Validates that "
            "published artifact schemas share consistent conventions and "
            "remain mutually compatible as they evolve. Dry-lab only."
        ),
    )
    acc.add_argument(
        "--schemas-dir", type=str, default=None,
        help="Path to schemas directory (default: schemas/).",
    )
    acc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Adoption scorecard (Phase I I10) ─────────────────────────────
    asc = sub.add_parser(
        "adoption-scorecard",
        help=(
            "Build an adoption scorecard aggregating Phase I adoption signals "
            "(integration_check, license_compliance, adapter_validation, "
            "schema_compatibility, contribution_readiness) into a dashboard. "
            "Dry-lab only."
        ),
    )
    asc.add_argument(
        "--scores-json", type=str, required=True,
        help="JSON dict of dimension inputs (required).",
    )
    asc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Decision log (Phase J J2) ──────────────────────────────────
    dl = sub.add_parser(
        "decision-log",
        help=(
            "Query and validate the governance decision log. "
            "Lists all governance decisions (GOV-001 through GOV-008) with "
            "scope, status, and review class. "
            "Dry-lab only."
        ),
    )
    dl.add_argument(
        "--validate", action="store_true", default=False,
        help="Validate all governance decisions.",
    )
    dl.add_argument(
        "--scope", type=str, default=None,
        help="Filter decisions by scope (e.g. safety, benchmark, release).",
    )
    dl.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Release request check (Phase J J3) ─────────────────────────
    rrc = sub.add_parser(
        "release-request-check",
        help=(
            "Validate a release request before human review. "
            "Checks all required fields are present and valid. "
            "Dry-lab only."
        ),
    )
    rrc.add_argument(
        "--request-json", type=str, required=True,
        help="JSON string of a ReleaseRequest dict (required).",
    )
    rrc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── COI disclosure check (Phase J J4) ───────────────────────────
    coi = sub.add_parser(
        "coi-check",
        help=(
            "Validate a conflict-of-interest disclosure before the "
            "formal review queue. Dry-lab only."
        ),
    )
    coi.add_argument(
        "--disclosure-json", type=str, required=True,
        help="JSON string of a COIDisclosure dict (required).",
    )
    coi.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Maintainer rotation plan check (Phase J J5) ──────────────────
    rpc = sub.add_parser(
        "rotation-plan-check",
        help=(
            "Validate a maintainer rotation plan for bus-factor "
            "coverage. Dry-lab only."
        ),
    )
    rpc.add_argument(
        "--plan-json", type=str, required=True,
        help="JSON string of a rotation plan dict (required).",
    )
    rpc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Release gate check (Phase J J1) ─────────────────────────────
    rgc = sub.add_parser(
        "release-gate-check",
        help=(
            "Check all required release gates before external release. "
            "Prevents unsafe or incomplete releases from escaping the dry-lab boundary. "
            "Dry-lab only."
        ),
    )
    rgc.add_argument(
        "--release-type", type=str, required=True,
        choices=sorted(["candidate", "model", "dataset", "evidence_packet", "schema"]),
        help="Type of release to validate.",
    )
    rgc.add_argument(
        "--artifact-id", type=str, required=True,
        help="Identifier for the artifact being released.",
    )
    rgc.add_argument(
        "--gates-json", type=str, required=True,
        help="JSON dict mapping gate names to boolean statuses.",
    )
    rgc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Security report check (Phase J J6) ──────────────────────────
    src = sub.add_parser(
        "security-report-check",
        help=(
            "Validate a security vulnerability report before the "
            "formal review queue. Dry-lab only."
        ),
    )
    src.add_argument(
        "--report-json", type=str, required=True,
        help="JSON string of a VulnerabilityReport dict (required).",
    )
    src.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Citation check (Phase J J7) ─────────────────────────────────
    cit = sub.add_parser(
        "citation-check",
        help=(
            "Validate a citation entry against the OpenAMP Foundry citation "
            "and reuse policy. Dry-lab only."
        ),
    )
    cit.add_argument(
        "--citation-json", type=str, required=True,
        help="JSON string of a CitationEntry dict (required).",
    )
    cit.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Roadmap sync check (Phase J J8) ─────────────────────────────
    rsc = sub.add_parser(
        "roadmap-sync-check",
        help=(
            "Validate a roadmap-to-issue sync entry. Ensures roadmap items "
            "are tracked and actionable. Dry-lab only."
        ),
    )
    rsc.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of a RoadmapSyncEntry dict (required).",
    )
    rsc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Advisory review check (Phase J J9) ──────────────────────────
    arc = sub.add_parser(
        "advisory-review-check",
        help=(
            "Validate an external advisory review entry. Dry-lab only."
        ),
    )
    arc.add_argument(
        "--review-json", type=str, required=True,
        help="JSON string of an AdvisoryReview dict (required).",
    )
    arc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Batch priority check (Phase K K2) ────────────────────────────
    bpc = sub.add_parser(
        "batch-priority-check",
        help=(
            "Validate a batch experiment priority entry. Ranks candidates for "
            "the next synthesis wave with evidence level and complexity. Dry-lab only."
        ),
    )
    bpc.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of a BatchPriorityEntry dict (required).",
    )
    bpc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Pilot package check (Phase K K3) ─────────────────────────────
    ppc = sub.add_parser(
        "pilot-package-check",
        help=(
            "Validate a pilot package completeness entry. Confirms all required "
            "artifacts are present before external lab submission. Dry-lab only."
        ),
    )
    ppc.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of a PilotPackageEntry dict (required).",
    )
    ppc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Calibration intake check (Phase K K4) ────────────────────────
    cic = sub.add_parser(
        "calibration-intake-check",
        help=(
            "Validate a post-experiment calibration intake entry. Compares pipeline "
            "prediction against actual lab outcome and records the calibration signal."
        ),
    )
    cic.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of a CalibrationIntakeEntry dict (required).",
    )
    cic.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Uncertainty report check (Phase K K5) ────────────────────────
    urc = sub.add_parser(
        "uncertainty-report-check",
        help=(
            "Validate an uncertainty quantification report. Checks prediction "
            "intervals, confidence levels, and calibration source. Dry-lab only."
        ),
    )
    urc.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of an UncertaintyReportEntry dict (required).",
    )
    urc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Preprint bundle check (Phase L L1) ───────────────────────────
    pbc = sub.add_parser(
        "preprint-bundle-check",
        help=(
            "Validate a preprint evidence bundle. Confirms all K-phase artifacts "
            "are referenced and release is approved. Dry-lab only."
        ),
    )
    pbc.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of a PreprintBundleEntry dict (required).",
    )
    pbc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Reproducibility manifest check (Phase L L2) ───────────────────
    rmc = sub.add_parser(
        "reproducibility-manifest-check",
        help=(
            "Validate a reproducibility manifest. Confirms software versions, "
            "data checksums, and random seeds are documented. Dry-lab only."
        ),
    )
    rmc.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of a ReproducibilityManifestEntry dict (required).",
    )
    rmc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Candidate summary card check (Phase L L3) ─────────────────────
    cscc = sub.add_parser(
        "candidate-summary-card-check",
        help=(
            "Validate a candidate summary card. Confirms sequence, evidence level, "
            "activity label, and safety flags. Dry-lab only."
        ),
    )
    cscc.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of a CandidateSummaryCardEntry dict (required).",
    )
    cscc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Multi-candidate comparison check (Phase L L4) ─────────────────
    mccc = sub.add_parser(
        "multi-candidate-comparison-check",
        help=(
            "Validate a multi-candidate comparison. Confirms candidate list, "
            "criteria, top-candidate rationale, and evidence level. Dry-lab only."
        ),
    )
    mccc.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of a MultiCandidateComparisonEntry dict (required).",
    )
    mccc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Dataset release check (Phase L L5) ───────────────────────────
    drc = sub.add_parser(
        "dataset-release-check",
        help=(
            "Validate a dataset release package. Confirms license, provenance, "
            "dual-use assessment, and release approval. Dry-lab only."
        ),
    )
    drc.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of a DatasetReleaseEntry dict (required).",
    )
    drc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Pipeline decision audit check (Phase M M1) ────────────────────
    pdac = sub.add_parser(
        "pipeline-decision-audit-check",
        help=(
            "Validate a pipeline decision audit entry. Records filter/threshold/rank "
            "decisions with rationale for external audit. Dry-lab only."
        ),
    )
    pdac.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of a PipelineDecisionAuditEntry dict (required).",
    )
    pdac.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Claim-to-evidence check (Phase M M2) ───────────────────────────
    ctec = sub.add_parser(
        "claim-to-evidence-check",
        help=(
            "Validate a claim-to-evidence mapping entry. Maps each scientific "
            "claim to the artifact that supports it for external audit. Dry-lab only."
        ),
    )
    ctec.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of a ClaimToEvidenceEntry dict (required).",
    )
    ctec.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Score decomposition check (Phase M M3) ─────────────────────────
    sdc = sub.add_parser(
        "score-decomposition-check",
        help=(
            "Validate a score decomposition report entry. Documents how "
            "composite scores are computed from named components. Dry-lab only."
        ),
    )
    sdc.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of a ScoreDecompositionEntry dict (required).",
    )
    sdc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Reviewer briefing check (Phase M M4) ────────────────────────────
    rbc = sub.add_parser(
        "reviewer-briefing-check",
        help="Validate a reviewer briefing package entry. "
        "One-stop summary for external auditors before they begin review. "
        "Dry-lab only.",
    )
    rbc.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of a ReviewerBriefingEntry dict (required).",
    )
    rbc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Audit chain completeness check (Phase M M5) ──────────────────
    audit_chain_parser = sub.add_parser(
        "audit-chain-check",
        help="Validate audit chain completeness for a batch",
    )
    audit_chain_parser.add_argument("--entry-json", required=True)
    audit_chain_parser.add_argument(
        "--format", choices=["text", "json"], default="text"
    )

    # ── Pre-registration form check (Phase N N1) ─────────────────────
    pre_registration_parser = sub.add_parser(
        "pre-registration-check",
        help="Validate a pre-registration form entry",
    )
    pre_registration_parser.add_argument("--entry-json", required=True)
    pre_registration_parser.add_argument(
        "--format", choices=["text", "json"], default="text"
    )
    pre_registration_parser.set_defaults(func=_run_pre_registration_check)

    external_sharing_clearance_parser = sub.add_parser(
        "external-sharing-clearance-check",
        help="Validate an ExternalSharingClearance entry (ESC-).",
    )
    external_sharing_clearance_parser.add_argument("--entry-json", required=True)
    external_sharing_clearance_parser.add_argument(
        "--format", choices=["text", "json"], default="text"
    )

    rejection_reason_parser = sub.add_parser(
        "rejection-reason-check",
        help="Validate a RejectionReasonEntry (RJR-).",
    )
    rejection_reason_parser.add_argument("--entry-json", required=True)
    rejection_reason_parser.add_argument(
        "--format", choices=["text", "json"], default="text"
    )

    negative_result_archive_parser = sub.add_parser(
        "negative-result-archive-check",
        help="Validate a NegativeResultArchiveSummary (NAS-).",
    )
    negative_result_archive_parser.add_argument("--entry-json", required=True)
    negative_result_archive_parser.add_argument(
        "--format", choices=["text", "json"], default="text"
    )

    failed_candidate_report_parser = sub.add_parser(
        "failed-candidate-batch-report-check",
        help="Validate a FailedCandidateBatchReport (FCR-).",
    )
    failed_candidate_report_parser.add_argument("--entry-json", required=True)
    failed_candidate_report_parser.add_argument(
        "--format", choices=["text", "json"], default="text"
    )

    reviewer_questionnaire_parser = sub.add_parser(
        "reviewer-questionnaire-check",
        help="Validate a ReviewerQuestionnaire (RVQ-).",
    )
    reviewer_questionnaire_parser.add_argument("--entry-json", required=True)
    reviewer_questionnaire_parser.add_argument(
        "--format", choices=["text", "json"], default="text"
    )

    domain_review_outcome_parser = sub.add_parser(
        "domain-review-outcome-check",
        help="Validate a DomainReviewOutcome (DRO-).",
    )
    domain_review_outcome_parser.add_argument("--entry-json", required=True)
    domain_review_outcome_parser.add_argument(
        "--format", choices=["text", "json"], default="text"
    )

    # ── Hypothesis outcome check (Phase N N2) ────────────────────────
    hypothesis_outcome_parser = sub.add_parser(
        "hypothesis-outcome-check",
        help="Validate a hypothesis outcome record entry",
    )
    hypothesis_outcome_parser.add_argument("--entry-json", required=True)
    hypothesis_outcome_parser.add_argument(
        "--format", choices=["text", "json"], default="text"
    )
    hypothesis_outcome_parser.set_defaults(func=_run_hypothesis_outcome_check)

    # ── Baseline comparison check (Phase N N3) ───────────────────────
    baseline_comparison_parser = sub.add_parser(
        "baseline-comparison-check",
        help="Validate a baseline comparison manifest entry",
    )
    baseline_comparison_parser.add_argument("--entry-json", required=True)
    baseline_comparison_parser.add_argument(
        "--format", choices=["text", "json"], default="text"
    )
    baseline_comparison_parser.set_defaults(func=_run_baseline_comparison_check)

    # ── Negative result record check (Phase N N4) ──────────────────────
    negative_result_parser = sub.add_parser(
        "negative-result-check",
        help="Validate a negative result record entry",
    )
    negative_result_parser.add_argument("--entry-json", required=True)
    negative_result_parser.add_argument(
        "--format", choices=["text", "json"], default="text"
    )
    negative_result_parser.set_defaults(func=_run_negative_result_check)

    experiment_priority_parser = sub.add_parser(
        "experiment-priority-check",
        help="Validate an experiment priority justification entry",
    )
    experiment_priority_parser.add_argument("--entry-json", required=True)
    experiment_priority_parser.add_argument(
        "--format", choices=["text", "json"], default="text"
    )
    experiment_priority_parser.set_defaults(func=_run_experiment_priority_check)

    calibration_performance_parser = sub.add_parser(
        "calibration-performance-check",
        help="Validate a calibration performance summary entry",
    )
    calibration_performance_parser.add_argument("--entry-json", required=True)
    calibration_performance_parser.add_argument(
        "--format", choices=["text", "json"], default="text"
    )
    calibration_performance_parser.set_defaults(func=_run_calibration_performance_check)

    p_drift = sub.add_parser(
        "prediction-drift-check",
        help="Validate prediction drift monitor entry",
    )
    p_drift.add_argument("--entry-json", default=None)
    p_drift.add_argument("--format", choices=["text", "json"], default="text")
    p_drift.set_defaults(func=_run_prediction_drift_check)

    p_cir = sub.add_parser(
        "calibration-improvement-check",
        help="Validate calibration improvement record entry",
    )
    p_cir.add_argument("--entry-json", default=None)
    p_cir.add_argument("--format", choices=["text", "json"], default="text")
    p_cir.set_defaults(func=_run_calibration_improvement_check)

    p_cba = sub.add_parser(
        "cross-batch-aggregator-check",
        help="Validate cross-batch performance aggregator entry",
    )
    p_cba.add_argument("--entry-json", default=None)
    p_cba.add_argument("--format", choices=["text", "json"], default="text")
    p_cba.set_defaults(func=_run_cross_batch_aggregator_check)

    p_crg = sub.add_parser(
        "calibration-readiness-check",
        help="Validate calibration readiness gate entry",
    )
    p_crg.add_argument("--entry-json", default=None)
    p_crg.add_argument("--format", choices=["text", "json"], default="text")
    p_crg.set_defaults(func=_run_calibration_readiness_check)

    p_bsp = sub.add_parser(
        "batch-selection-proposal-check",
        help="Validate batch selection proposal entry",
    )
    p_bsp.add_argument("--entry-json", default=None)
    p_bsp.add_argument("--format", choices=["text", "json"], default="text")
    p_bsp.set_defaults(func=_run_batch_selection_proposal_check)

    p_rrf = sub.add_parser(
        "recalibration-refusal-check",
        help="Validate recalibration refusal record entry",
    )
    p_rrf.add_argument("--entry-json", default=None)
    p_rrf.add_argument("--format", choices=["text", "json"], default="text")
    p_rrf.set_defaults(func=_run_recalibration_refusal_check)

    p_bos = sub.add_parser(
        "batch-outcome-summary-check",
        help="Validate batch outcome summary entry",
    )
    p_bos.add_argument("--entry-json", default=None)
    p_bos.add_argument("--format", choices=["text", "json"], default="text")
    p_bos.set_defaults(func=_run_batch_outcome_summary_check)

    p_psc = sub.add_parser(
        "pilot-batch-safety-clearance-check",
        help="Validate pilot batch safety clearance entry",
    )
    p_psc.add_argument("--entry-json", default=None)
    p_psc.add_argument("--format", choices=["text", "json"], default="text")
    p_psc.set_defaults(func=_run_pilot_batch_safety_clearance_check)

    p_ccs = sub.add_parser(
        "calibration-cycle-summary-check",
        help="Validate calibration cycle summary entry",
    )
    p_ccs.add_argument("--entry-json", default=None)
    p_ccs.add_argument("--format", choices=["text", "json"], default="text")
    p_ccs.set_defaults(func=_run_calibration_cycle_summary_check)

    p_pep = sub.add_parser(
        "pilot-evidence-package-check",
        help="Validate pilot evidence package entry",
    )
    p_pep.add_argument("--entry-json", default=None)
    p_pep.add_argument("--format", choices=["text", "json"], default="text")
    p_pep.set_defaults(func=_run_pilot_evidence_package_check)

    p_pre = sub.add_parser(
        "pre-registration-check",
        help="Validate pre-registration entry",
    )
    p_pre.add_argument("--entry-json", default=None)
    p_pre.add_argument("--format", choices=["text", "json"], default="text")
    p_pre.set_defaults(func=_run_pre_registration_entry_check)

    negative_result_entry_parser = sub.add_parser(
        "negative-result-entry-check",
        help="Validate a NegativeResultEntry (NRR-) record",
    )
    negative_result_entry_parser.add_argument("json_input", help="JSON string of the NRR- record")

    ppc_parser = sub.add_parser(
        "pilot-package-completeness-check",
        help="Validate a PilotPackageCompletenessReport (PPC-) record",
    )
    ppc_parser.add_argument("json_input", help="JSON string of the PPC- record")

    csr_parser = sub.add_parser(
        "candidate-selection-rationale-check",
        help="Validate a CandidateSelectionRationale (CSR-) record",
    )
    csr_parser.add_argument("json_input", help="JSON string of the CSR- record")

    bpr_parser = sub.add_parser(
        "batch-experiment-priority-ranker-check",
        help="Validate a BatchExperimentPriorityRanker (BPR-) record",
    )
    bpr_parser.add_argument("json_input", help="JSON string of the BPR- record")

    cir_parser = subparsers.add_parser(
        "calibration-improvement-record-check",
        help="Validate a CalibrationImprovementRecord (CIR-) record",
    )
    cir_parser.add_argument("json_input", help="JSON string of the CIR- record")

    pci_parser = subparsers.add_parser(
        "post-experiment-calibration-intake-check",
        help="Validate a PostExperimentCalibrationIntake (PCI-) record",
    )
    pci_parser.add_argument("json_input", help="JSON string of the PCI- record")

    nrd_parser = subparsers.add_parser(
        "negative-result-dashboard-check",
        help="Validate a NegativeResultDashboard (NRD-) record",
    )
    nrd_parser.add_argument("json_input", help="JSON string of the NRD- record")

    p_rdl = subparsers.add_parser("recalibration-decision-log-check", help="Validate a RecalibrationDecisionLog JSON")
    p_rdl.add_argument("input", help="Path to JSON file")
    p_rdl.set_defaults(func=_run_recalibration_decision_log_check)

    p_rrs = subparsers.add_parser("recalibration-rejection-summary-check", help="Validate a RecalibrationRejectionSummary JSON")
    p_rrs.add_argument("input", help="Path to JSON file")
    p_rrs.set_defaults(func=_run_recalibration_rejection_summary_check)

    p_sbr = subparsers.add_parser("synthetic-boundary-audit-record-check", help="Validate a SyntheticBoundaryAuditRecord JSON")
    p_sbr.add_argument("input", help="Path to JSON file")
    p_sbr.set_defaults(func=_run_synthetic_boundary_audit_record_check)

    p_erp = subparsers.add_parser("expert-review-example-package-check", help="Validate an ExpertReviewExamplePackage JSON")
    p_erp.add_argument("input", help="Path to JSON file")
    p_erp.set_defaults(func=_run_expert_review_example_package_check)

    p_plc = subparsers.add_parser("proof-ladder-level-certificate-check", help="Validate a ProofLadderLevelCertificate JSON")
    p_plc.add_argument("input", help="Path to JSON file")
    p_plc.set_defaults(func=_run_proof_ladder_level_certificate_check)

    # ── Selection rationale check (Phase K K1) ───────────────────────
    src2 = sub.add_parser(
        "selection-rationale-check",
        help=(
            "Validate a candidate selection rationale. Ensures every selected "
            "candidate has a documented evidence level and baseline comparison. "
            "Dry-lab only."
        ),
    )
    src2.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of a SelectionRationaleEntry dict (required).",
    )
    src2.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Annual review check (Phase J J10) ───────────────────────────
    anrc = sub.add_parser(
        "annual-review-check",
        help=(
            "Validate an annual safety and benchmark review checklist entry. "
            "Dry-lab only."
        ),
    )
    anrc.add_argument(
        "--entry-json", type=str, required=True,
        help="JSON string of an AnnualReviewEntry dict (required).",
    )
    anrc.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    # ── Simulation-result confidence interval report (H7) ────────────
    sicr = sub.add_parser(
        "simulation-ci-report",
        help=(
            "Compute confidence intervals from SimulationResult uncertainty fields "
            "and compare them for overlap. Makes uncertainty explicit and auditable. "
            "Dry-lab only."
        ),
    )
    sicr.add_argument(
        "--results-json", type=str, required=True,
        help="JSON array of SimulationResult dicts.",
    )
    sicr.add_argument(
        "--score-key", type=str, default="binding_energy",
        help="Score key to extract from each result's scores dict (default: binding_energy).",
    )
    sicr.add_argument(
        "--format", type=str, default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "rank":
        sim_mode = getattr(args, "simulation_mode", "off")
        run_ranking_pipeline(
            candidate_path=args.candidates,
            reference_path=args.references,
            out_path=args.out,
            report_path=args.report,
            cert_dir=args.cert_dir,
            config_path=args.config,
            manifest_path=args.manifest,
            ranking_mode=getattr(args, "ranking_mode", "ensemble"),
            simulation_mode=sim_mode,
            track_failures=getattr(args, "track_failures", False),
        )
        print(
            json.dumps(
                {
                    "status": "ok",
                    "out": args.out,
                    "report": args.report,
                    "ranking_mode": getattr(args, "ranking_mode", "ensemble"),
                    "simulation_mode": sim_mode,
                    "ranking_policy": ranking_policy_payload(
                        getattr(args, "ranking_mode", "ensemble")
                    ),
                },
                indent=2,
            )
        )
        return 0

    if args.command == "validate":
        payload = read_json(args.certificate)
        validate_json_schema(payload, Path(args.schema))
        print(json.dumps({"status": "valid", "certificate": args.certificate}, indent=2))
        return 0

    if args.command == "validate-cert-quality":
        payload = read_json(args.certificate)
        result = assess_certificate_quality(payload, schema_path=args.schema)
        print(json.dumps(result, indent=2))
        return 0 if result["tier"] in ("pass", "warn") else 3

    if args.command == "bench":
        if args.bench_command == "cluster-split":
            return _run_cluster_split_bench(args)
        if args.bench_command == "expert-ablation":
            return _run_expert_ablation_bench(args)
        if args.bench_command == "selectivity":
            return _run_selectivity_bench(args)
        if args.bench_command == "triage":
            return _run_triage(args)
        if args.bench_command == "feature-decomp":
            return _run_feature_decomp(args)
        if args.bench_command == "metrics-snapshot":
            return _run_metrics_snapshot(args)
        if args.bench_command == "active-learning":
            return _run_active_learning_bench(args)
        if args.bench_command == "strategy-compare":
            return _run_active_learning_strategy_compare(args)
        if args.bench_command == "simulation-gate":
            return _run_simulation_gate(args)
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

    if args.command == "external-consensus":
        return _run_external_consensus(args)

    if args.command == "reviewer-questionnaire":
        return _run_reviewer_questionnaire(args)

    if args.command == "gate-check":
        return _run_gate_check(args)

    if args.command == "release-gate-check":
        return _run_release_gate_check(args)

    if args.command == "ip-report":
        return _run_ip_report(args)

    if args.command == "batch-pack":
        return _run_batch_pack(args)

    if args.command == "lab-result-report":
        return _run_lab_result_report(args)

    if args.command == "calibration-intake":
        return _run_calibration_intake(args)

    if args.command == "recalibration-gate":
        return _run_recalibration_gate(args)

    if args.command == "recalibration-engine":
        return _run_recalibration_engine(args)

    if args.command == "synthesis-order":
        return _run_synthesis_order(args)

    if args.command == "presynth-qc":
        return _run_presynth_qc(args)

    if args.command == "gold-standard":
        return _run_gold_standard(args)

    if args.command == "diversity-check":
        return _run_diversity_check(args)

    if args.command == "novelty-check-broad":
        return _run_novelty_check_broad(args)

    if args.command == "validate-policy-version":
        return _run_validate_policy_version(args)

    if args.command == "calibration-audit":
        return _run_calibration_audit(args)

    if args.command == "batch-rationale":
        return _run_batch_rationale(args)

    if args.command == "select-batch":
        return _run_select_batch(args)

    if args.command == "calibration-overfit-check":
        return _run_calibration_overfit_check(args)

    if args.command == "result-quality-filter":
        return _run_result_quality_filter(args)

    if args.command == "synthetic-result-policy-check":
        return _run_synthetic_result_policy_check(args)

    if args.command == "calibration-decision-checklist":
        return _run_calibration_decision_checklist(args)

    if args.command == "calibration-rollback-plan":
        return _run_calibration_rollback_plan(args)

    if args.command == "simulation-registry":
        return _run_simulation_registry(args)

    if args.command == "validate-simulation-result":
        return _run_validate_simulation_result(args)

    if args.command == "simulation-baseline-check":
        return _run_simulation_baseline_check(args)

    if args.command == "adapter-gate-check":
        return _run_adapter_gate_check(args)

    if args.command == "simulation-provenance":
        return _run_simulation_provenance(args)

    if args.command == "simulation-ensemble-check":
        return _run_simulation_ensemble_check(args)

    if args.command == "simulation-ci-report":
        return _run_simulation_ci_report(args)

    if args.command == "simulation-deprecation-check":
        return _run_simulation_deprecation_check(args)

    if args.command == "simulation-scope-check":
        return _run_simulation_scope_check(args)

    if args.command == "simulation-evidence-packet":
        return _run_simulation_evidence_packet(args)

    if args.command == "artifact-version":
        return _run_artifact_version(args)

    if args.command == "artifact-changelog":
        return _run_artifact_changelog(args)

    if args.command == "candidate-manifest":
        return _run_candidate_manifest(args)

    if args.command == "benchmark-card":
        return _run_benchmark_card(args)

    if args.command == "integration-check":
        return _run_integration_check(args)

    if args.command == "adapter-check":
        return _run_adapter_check(args)

    if args.command == "license-check":
        return _run_license_check(args)

    if args.command == "contribution-check":
        return _run_contribution_check(args)

    if args.command == "artifact-compat-check":
        return _run_artifact_compat_check(args)

    if args.command == "adoption-scorecard":
        return _run_adoption_scorecard(args)

    if args.command == "decision-log":
        return _run_decision_log(args)

    if args.command == "release-request-check":
        return _run_release_request_check(args)

    if args.command == "coi-check":
        return _run_coi_check(args)

    if args.command == "rotation-plan-check":
        return _run_rotation_plan_check(args)

    if args.command == "security-report-check":
        return _run_security_report_check(args)

    if args.command == "citation-check":
        return _run_citation_check(args)

    if args.command == "roadmap-sync-check":
        return _run_roadmap_sync_check(args)

    if args.command == "advisory-review-check":
        return _run_advisory_review_check(args)

    if args.command == "annual-review-check":
        return _run_annual_review_check(args)

    if args.command == "selection-rationale-check":
        return _run_selection_rationale_check(args)

    if args.command == "batch-priority-check":
        return _run_batch_priority_check(args)

    if args.command == "pilot-package-check":
        return _run_pilot_package_check(args)

    if args.command == "calibration-intake-check":
        return _run_calibration_intake_check(args)

    if args.command == "uncertainty-report-check":
        return _run_uncertainty_report_check(args)

    if args.command == "preprint-bundle-check":
        return _run_preprint_bundle_check(args)

    if args.command == "reproducibility-manifest-check":
        return _run_reproducibility_manifest_check(args)

    if args.command == "candidate-summary-card-check":
        return _run_candidate_summary_card_check(args)

    if args.command == "multi-candidate-comparison-check":
        return _run_multi_candidate_comparison_check(args)

    if args.command == "dataset-release-check":
        return _run_dataset_release_check(args)

    if args.command == "pipeline-decision-audit-check":
        return _run_pipeline_decision_audit_check(args)

    if args.command == "claim-to-evidence-check":
        return _run_claim_to_evidence_check(args)

    if args.command == "score-decomposition-check":
        return _run_score_decomposition_check(args)

    if args.command == "reviewer-briefing-check":
        return _run_reviewer_briefing_check(args)

    if args.command == "audit-chain-check":
        return _run_audit_chain_check(args)

    if args.command == "pre-registration-check":
        return _run_pre_registration_check(args)

    if args.command == "external-sharing-clearance-check":
        return _run_external_sharing_clearance_check(args)

    if args.command == "rejection-reason-check":
        return _run_rejection_reason_check(args)

    if args.command == "negative-result-archive-check":
        return _run_negative_result_archive_check(args)

    if args.command == "failed-candidate-batch-report-check":
        return _run_failed_candidate_batch_report_check(args)

    if args.command == "reviewer-questionnaire-check":
        _run_reviewer_questionnaire_check(args)

    if args.command == "domain-review-outcome-check":
        _run_domain_review_outcome_check(args)

    if args.command == "hypothesis-outcome-check":
        return _run_hypothesis_outcome_check(args)

    if args.command == "baseline-comparison-check":
        return _run_baseline_comparison_check(args)

    if args.command == "negative-result-check":
        return _run_negative_result_check(args)
    if args.command == "experiment-priority-check":
        return _run_experiment_priority_check(args)
    if args.command == "calibration-performance-check":
        return _run_calibration_performance_check(args)

    if args.command == "prediction-drift-check":
        return _run_prediction_drift_check(args)

    if args.command == "cross-batch-aggregator-check":
        return _run_cross_batch_aggregator_check(args)

    if args.command == "calibration-readiness-check":
        return _run_calibration_readiness_check(args)

    if args.command == "batch-selection-proposal-check":
        return _run_batch_selection_proposal_check(args)

    if args.command == "recalibration-refusal-check":
        return _run_recalibration_refusal_check(args)

    if args.command == "batch-outcome-summary-check":
        return _run_batch_outcome_summary_check(args)

    if args.command == "pilot-batch-safety-clearance-check":
        return _run_pilot_batch_safety_clearance_check(args)

    if args.command == "calibration-cycle-summary-check":
        return _run_calibration_cycle_summary_check(args)

    if args.command == "pilot-evidence-package-check":
        return _run_pilot_evidence_package_check(args)

    if args.command == "pre-registration-check":
        return _run_pre_registration_entry_check(args)

    if args.command == "negative-result-entry-check":
        from openamp_foundry.cli.commands.reports import _run_negative_result_entry_check
        _run_negative_result_entry_check(args)

    elif args.command == "pilot-package-completeness-check":
        from openamp_foundry.cli.commands.reports import _run_pilot_package_completeness_check
        _run_pilot_package_completeness_check(args)

    elif args.command == "candidate-selection-rationale-check":
        from openamp_foundry.cli.commands.reports import _run_candidate_selection_rationale_check
        _run_candidate_selection_rationale_check(args)

    elif args.command == "batch-experiment-priority-ranker-check":
        from openamp_foundry.cli.commands.reports import _run_batch_experiment_priority_ranker_check
        _run_batch_experiment_priority_ranker_check(args)

    elif args.command == "calibration-improvement-record-check":
        from openamp_foundry.cli.commands.reports import _run_calibration_improvement_record_check
        _run_calibration_improvement_record_check(args)

    elif args.command == "post-experiment-calibration-intake-check":
        from openamp_foundry.cli.commands.reports import _run_post_experiment_calibration_intake_check
        _run_post_experiment_calibration_intake_check(args)

    elif args.command == "negative-result-dashboard-check":
        from openamp_foundry.cli.commands.reports import _run_negative_result_dashboard_check
        _run_negative_result_dashboard_check(args)

    elif args.command == "recalibration-decision-log-check":
        _run_recalibration_decision_log_check(args)

    elif args.command == "expert-review-example-package-check":
        _run_expert_review_example_package_check(args)

    elif args.command == "recalibration-rejection-summary-check":
        _run_recalibration_rejection_summary_check(args)

    elif args.command == "proof-ladder-level-certificate-check":
        _run_proof_ladder_level_certificate_check(args)

    else:
        parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

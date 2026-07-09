from __future__ import annotations

from openamp_foundry.cli.commands.core import _run_generate_batch
from openamp_foundry.cli.commands.benchmark import _run_bench, _run_validate_scoring, _run_cluster_split_bench, _run_expert_ablation_bench, _run_selectivity_bench, _run_triage, _run_metrics_snapshot, _run_feature_decomp, _run_active_learning_bench, _run_active_learning_strategy_compare, _run_simulation_gate
from openamp_foundry.cli.commands.selection import _run_pilot_panel, _run_pilot_confident, _run_diversity_check, _run_select_batch, _run_batch_rationale
from openamp_foundry.cli.commands.external import _run_external_predict, _run_external_consensus
from openamp_foundry.cli.commands.qc import _run_synthesis_order, _run_presynth_qc
from openamp_foundry.cli.commands.reports import _run_reviewer_questionnaire, _run_ip_report, _run_batch_pack, _run_gold_standard, _run_novelty_check_broad, _run_lab_result_report, _run_calibration_intake, _run_recalibration_gate, _run_recalibration_engine, _run_validate_policy_version, _run_calibration_audit, _run_calibration_overfit_check, _run_result_quality_filter, _run_synthetic_result_policy_check, _run_calibration_decision_checklist, _run_calibration_rollback_plan, _run_simulation_registry, _run_validate_simulation_result, _run_simulation_baseline_check, _run_adapter_gate_check, _run_simulation_provenance, _run_simulation_ensemble_check, _run_simulation_ci_report, _run_simulation_deprecation_check, _run_simulation_scope_check, _run_simulation_evidence_packet, _run_artifact_version, _run_candidate_manifest, _run_benchmark_card, _run_artifact_changelog, _run_integration_check, _run_adapter_check, _run_license_check, _run_artifact_compat_check, _run_adoption_scorecard
from openamp_foundry.cli.commands.gates import _run_gate_check, _run_release_gate_check
from openamp_foundry.cli.commands.reports import _run_contribution_check
from openamp_foundry.cli.commands.reports import _run_decision_log
from openamp_foundry.cli.commands.reports import _run_release_request_check
from openamp_foundry.cli.commands.reports import _run_coi_check

import argparse
import json
from pathlib import Path

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

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

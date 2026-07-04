from __future__ import annotations

from openamp_foundry.cli.commands.core import _run_generate_batch
from openamp_foundry.cli.commands.benchmark import _run_bench, _run_validate_scoring, _run_cluster_split_bench, _run_expert_ablation_bench, _run_selectivity_bench, _run_triage, _run_metrics_snapshot, _run_feature_decomp
from openamp_foundry.cli.commands.selection import _run_pilot_panel, _run_pilot_confident, _run_diversity_check
from openamp_foundry.cli.commands.external import _run_external_predict, _run_external_consensus
from openamp_foundry.cli.commands.qc import _run_synthesis_order, _run_presynth_qc
from openamp_foundry.cli.commands.reports import _run_reviewer_questionnaire, _run_ip_report, _run_batch_pack, _run_gold_standard, _run_novelty_check_broad, _run_lab_result_report, _run_calibration_intake, _run_recalibration_gate
from openamp_foundry.cli.commands.gates import _run_gate_check

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
            "Use this to refresh docs/METRICS_CURRENT.md evidence and catch number drift."
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
            ranking_mode=getattr(args, "ranking_mode", "ensemble"),
        )
        print(json.dumps({"status": "ok", "out": args.out, "report": args.report}, indent=2))
        return 0

    if args.command == "validate":
        payload = read_json(args.certificate)
        validate_json_schema(payload, Path(args.schema))
        print(json.dumps({"status": "valid", "certificate": args.certificate}, indent=2))
        return 0

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

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

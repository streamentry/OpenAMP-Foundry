from __future__ import annotations

from openamp_foundry.cli.commands.core import _run_generate_batch
from openamp_foundry.cli.commands.benchmark import _run_bench, _run_validate_scoring
from openamp_foundry.cli.commands.selection import _run_pilot_panel, _run_pilot_confident, _run_diversity_check
from openamp_foundry.cli.commands.external import _run_external_predict, _run_external_consensus
from openamp_foundry.cli.commands.qc import _run_synthesis_order, _run_presynth_qc
from openamp_foundry.cli.commands.reports import _run_reviewer_questionnaire, _run_ip_report, _run_batch_pack, _run_gold_standard, _run_novelty_check_broad
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



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

    parser.error("unknown command")
    return 2


def _run_bench(args: argparse.Namespace) -> int:
    from openamp_foundry.benchmark.leakage import find_near_duplicates
    from openamp_foundry.data.loaders import load_candidates_csv
    from openamp_foundry.utils.io import write_json

    if args.bench_command == "leakage":
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

    return 2


if __name__ == "__main__":
    raise SystemExit(main())

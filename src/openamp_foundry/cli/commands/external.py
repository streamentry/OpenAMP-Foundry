"""External predictor commands."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone

def _run_external_predict(args: argparse.Namespace) -> int:
    import csv as _csv
    import json as _json
    from openamp_foundry.reports.external_predict import (
        write_external_predict_checklist,
        write_pilot_fasta,
    )

    panel = []
    with open(args.pilot_csv, newline="", encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            panel.append(row)

    generated_at = datetime.now(timezone.utc).isoformat()
    write_pilot_fasta(panel, args.out_fasta)
    write_external_predict_checklist(
        panel, fasta_path=args.out_fasta, out_path=args.out_checklist,
        generated_at=generated_at,
    )
    print(_json.dumps({
        "status": "ok",
        "n_candidates": len(panel),
        "fasta": args.out_fasta,
        "checklist": args.out_checklist,
        "next_step": (
            f"Submit {args.out_fasta} to CAMPR4, AMPScanner v2, and dbAMP. "
            f"Fill in {args.out_checklist}. Then run 'make pilot-confident'."
        ),
    }, indent=2))
    return 0


def _run_external_consensus(args: argparse.Namespace) -> int:
    import json as _json
    from openamp_foundry.reports.external_consensus import (
        compute_consensus,
        write_consensus_report,
        consensus_report_to_dict,
    )
    results = compute_consensus(args.pilot_csv, args.results_csv)
    write_consensus_report(results, args.out)
    summary = consensus_report_to_dict(results)
    summary["out"] = args.out
    print(_json.dumps(summary, indent=2))
    return 0



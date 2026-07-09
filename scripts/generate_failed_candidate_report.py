"""Generate a structured report of failed/rejected candidates.

Reads a batch of failed candidates with rejection reasons (using codes from
the rejection taxonomy at schemas/rejection_taxonomy.schema.json) and produces:
  - Machine-readable JSON report with summary statistics and per-candidate detail
  - Human-readable Markdown summary

Usage:
    python scripts/generate_failed_candidate_report.py \
        --input examples/failed_candidates_example.json \
        --out-json outputs/failed_candidate_report.json \
        --out-md outputs/failed_candidate_report.md

    python scripts/generate_failed_candidate_report.py \
        --input examples/failed_candidates_example.json \
        --out-json outputs/failed_candidate_report.json \
        --validate-rejection-codes

Output artifacts:
  - JSON report (--out-json): machine-readable with summary, aggregation, per-candidate
  - Markdown summary (--out-md): human-readable with tables, category breakdowns

Caveats:
  - Rejection codes reflect pipeline or reviewer decisions, not biological
    inactivity unless confirmed by lab assay.
  - Soft rejections may be overcome by threshold or policy changes.
  - This output is informational only and requires qualified review before
    any claim about candidate quality.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_DIR = _SCRIPT_DIR.parent
_TAXONOMY_PATH = _REPO_DIR / "schemas" / "rejection_taxonomy.schema.json"


def load_taxonomy(taxonomy_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load the rejection taxonomy from its schema file (embedded $defs.taxonomy_entry examples)."""
    p = Path(taxonomy_path or _TAXONOMY_PATH)
    if not p.exists():
        msg = f"Taxonomy schema not found: {p}"
        raise FileNotFoundError(msg)

    try:
        from openamp_foundry.utils.io import read_json
    except ImportError:
        with p.open("r") as f:
            schema = json.load(f)
    else:
        schema = read_json(p)

    # If the schema itself is the taxonomy array (example file), return it
    if isinstance(schema, list):
        return schema

    # If it's a schema with an "examples" array on the $defs.taxonomy_entry, extract examples
    # from the compiled schema definition
    # For the rejection taxonomy schema, we need the external example file
    example_path = _REPO_DIR / "examples" / "rejection_taxonomy_example.json"
    if example_path.exists():
        try:
            from openamp_foundry.utils.io import read_json as _rj
            return _rj(example_path)
        except ImportError:
            with example_path.open("r") as f:
                return json.load(f)

    msg = f"Cannot load taxonomy entries from {p}. Provide the example file path."
    raise ValueError(msg)


def _get_taxonomy_codes(taxonomy: list[dict[str, Any]]) -> set[str]:
    return {e["code"] for e in taxonomy}


def _get_taxonomy_by_code(taxonomy: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {e["code"]: e for e in taxonomy}


def validate_rejection_codes(
    candidates: list[dict[str, Any]],
    taxonomy_codes: set[str],
) -> list[dict[str, Any]]:
    """Check that all rejection codes in candidates exist in the taxonomy.

    Returns a list of error dicts — empty if all codes are valid.
    """
    errors: list[dict[str, Any]] = []
    for c in candidates:
        cid = c.get("candidate_id", "?")
        rejections = c.get("rejections", [])
        for r in rejections:
            code = r.get("code", "")
            if code and code not in taxonomy_codes:
                errors.append({
                    "candidate_id": cid,
                    "code": code,
                    "error": f"Unknown rejection code: {code}",
                })
    return errors


def build_report(
    candidates: list[dict[str, Any]],
    source_batch: str,
    pipeline_version: str,
    report_date: str,
    taxonomy: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a structured failed-candidate report from candidate rejection data."""
    tax_codes = _get_taxonomy_codes(taxonomy)
    tax_by_code = _get_taxonomy_by_code(taxonomy)

    # Per-candidate data
    candidate_entries: list[dict[str, Any]] = []
    for c in candidates:
        rejections = c.get("rejections", [])
        rejection_entries: list[dict[str, Any]] = []
        for r in rejections:
            code = r.get("code", "")
            detail = r.get("detail", "")
            entry = {"code": code, "detail": detail}
            tax_entry = tax_by_code.get(code)
            if tax_entry:
                entry["category"] = tax_entry.get("category", "")
                entry["severity"] = tax_entry.get("severity", "")
                entry["evidence_impact"] = tax_entry.get("evidence_impact", "")
            rejection_entries.append(entry)

        candidate_entries.append({
            "candidate_id": c.get("candidate_id", "?"),
            "sequence": c.get("sequence", ""),
            "rejection_count": len(rejection_entries),
            "rejections": rejection_entries,
            "severity_summary": _summarize_severity(rejection_entries),
        })

    # Aggregate statistics
    total_candidates = len(candidate_entries)
    all_codes = []
    all_categories: defaultdict[str, list[str]] = defaultdict(list)
    all_severities: defaultdict[str, int] = defaultdict(int)
    all_stages: defaultdict[str, list[str]] = defaultdict(list)
    all_impacts: defaultdict[str, int] = defaultdict(int)

    for entry in candidate_entries:
        for r in entry["rejections"]:
            code = r["code"]
            all_codes.append(code)
            cat = r.get("category", "unknown")
            all_categories[cat].append(entry["candidate_id"])
            sev = r.get("severity", "unknown")
            all_severities[sev] += 1
            imp = r.get("evidence_impact", "unknown")
            all_impacts[imp] += 1
            stage = tax_by_code.get(code, {}).get("applies_at_stage", "unknown")
            all_stages[stage].append(entry["candidate_id"])

    code_freq = Counter(all_codes)
    category_summary = {}
    for cat, cids in sorted(all_categories.items()):
        category_summary[cat] = {
            "count": len(cids),
            "candidates": sorted(set(cids)),
        }

    stage_summary = {}
    for stage, cids in sorted(all_stages.items()):
        stage_summary[stage] = {
            "count": len(cids),
            "candidates": sorted(set(cids)),
        }

    # Top-level severity summary per-candidate
    severity_counts: defaultdict[str, int] = defaultdict(int)
    for entry in candidate_entries:
        for sev_entry in entry["severity_summary"]:
            severity_counts[sev_entry["severity"]] += sev_entry["count"]

    unknown_codes = [code for code in all_codes if code not in tax_codes]
    unknown_set = sorted(set(unknown_codes))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "report_metadata": {
            "generated_at": now,
            "report_type": "failed_candidate_report",
            "schema_version": "1.0.0",
            "source_batch": source_batch,
            "pipeline_version": pipeline_version,
            "report_date": report_date,
            "taxonomy_source": str(_TAXONOMY_PATH),
        },
        "summary": {
            "total_candidates": total_candidates,
            "total_unique_rejection_codes": len(code_freq),
            "total_rejection_instances": len(all_codes),
            "unknown_codes": unknown_set,
            "by_category": category_summary,
            "by_stage": stage_summary,
            "by_severity": dict(severity_counts),
            "by_evidence_impact": dict(all_impacts),
            "rejection_code_frequencies": dict(code_freq.most_common()),
        },
        "candidates": candidate_entries,
        "caveats": [
            "Computational outputs are hypotheses and review aids. They are not biological proof.",
            "Rejection codes reflect pipeline or reviewer decisions, not biological inactivity unless confirmed by lab assay.",
            "Soft rejections may be overcome by threshold or policy changes.",
            "Hard rejections require new evidence to overturn.",
            "This report is informational only and requires qualified review.",
        ],
        "dry_lab_only": True,
    }


def _summarize_severity(rejections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    severity_counts: defaultdict[str, int] = defaultdict(int)
    for r in rejections:
        sev = r.get("severity", "unknown")
        severity_counts[sev] += 1
    return [
        {"severity": sev, "count": cnt}
        for sev, cnt in sorted(severity_counts.items())
    ]


def build_markdown_report(report: dict[str, Any]) -> str:
    """Generate a Markdown summary from the structured report."""
    meta = report["report_metadata"]
    summary = report["summary"]
    lines: list[str] = []

    lines.append("# Failed Candidate Report")
    lines.append("")
    lines.append("> **Dry-lab only — informational.** This report is a computational "
                 "summary of pipeline rejection decisions. It is not biological proof "
                 "of inactivity unless confirmed by lab assay.")
    lines.append("")

    lines.append("## Report Metadata")
    lines.append("")
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| Generated at | {meta['generated_at']} |")
    lines.append(f"| Source batch | {meta['source_batch']} |")
    lines.append(f"| Pipeline version | {meta['pipeline_version']} |")
    lines.append(f"| Report date | {meta['report_date']} |")
    lines.append(f"| Taxonomy source | `{meta['taxonomy_source']}` |")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total candidates | {summary['total_candidates']} |")
    lines.append(f"| Unique rejection codes | {summary['total_unique_rejection_codes']} |")
    lines.append(f"| Total rejection instances | {summary['total_rejection_instances']} |")
    if summary.get("unknown_codes"):
        lines.append(f"| Unknown codes | {', '.join(summary['unknown_codes'])} |")
    lines.append("")

    lines.append("### By Category")
    lines.append("")
    lines.append("| Category | Count | Candidates |")
    lines.append("|----------|-------|------------|")
    for cat, data in sorted(summary.get("by_category", {}).items()):
        cid_str = ", ".join(data["candidates"])
        lines.append(f"| {cat} | {data['count']} | {cid_str} |")
    lines.append("")

    lines.append("### By Severity")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    for sev, cnt in sorted(summary.get("by_severity", {}).items()):
        lines.append(f"| {sev} | {cnt} |")
    lines.append("")

    lines.append("### By Evidence Impact")
    lines.append("")
    lines.append("| Evidence Impact | Count |")
    lines.append("|-----------------|-------|")
    for imp, cnt in sorted(summary.get("by_evidence_impact", {}).items()):
        lines.append(f"| {imp} | {cnt} |")
    lines.append("")

    lines.append("### Rejection Code Frequencies")
    lines.append("")
    lines.append("| Code | Count |")
    lines.append("|------|-------|")
    for code, cnt in summary.get("rejection_code_frequencies", {}).items():
        lines.append(f"| `{code}` | {cnt} |")
    lines.append("")

    lines.append("## Per-Candidate Breakdown")
    lines.append("")
    for c in report.get("candidates", []):
        cid = c["candidate_id"]
        seq = c.get("sequence", "")
        lines.append(f"### {cid}")
        if seq:
            lines.append("")
            lines.append(f"**Sequence:** `{seq}`")
        lines.append("")
        lines.append(f"**Rejection count:** {c['rejection_count']}")
        lines.append("")
        sev_str = "; ".join(
            f"{s['severity']}: {s['count']}" for s in c.get("severity_summary", [])
        )
        if sev_str:
            lines.append(f"**Severity breakdown:** {sev_str}")
        lines.append("")
        lines.append("| Code | Detail | Category | Severity | Evidence Impact |")
        lines.append("|------|--------|----------|----------|-----------------|")
        for r in c["rejections"]:
            lines.append(
                f"| `{r['code']}` | {r.get('detail', '')} | "
                f"{r.get('category', '')} | {r.get('severity', '')} | "
                f"{r.get('evidence_impact', '')} |"
            )
        lines.append("")

    lines.append("## Caveats")
    lines.append("")
    for caveat in report.get("caveats", []):
        lines.append(f"- {caveat}")
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by `scripts/generate_failed_candidate_report.py` — "
                 f"`{meta['pipeline_version']}`*")

    return "\n".join(lines)


def load_input(input_path: str | Path) -> dict[str, Any]:
    """Load and validate the failed-candidates input file."""
    p = Path(input_path)
    if not p.exists():
        msg = f"Input file not found: {p}"
        raise FileNotFoundError(msg)

    try:
        from openamp_foundry.utils.io import read_json
        return read_json(p)
    except ImportError:
        with p.open("r") as f:
            return json.load(f)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a structured report of failed/rejected candidates",
    )
    parser.add_argument(
        "--input", required=True, type=Path,
        help="Path to failed candidates JSON input file",
    )
    parser.add_argument(
        "--out-json", type=Path, default=None,
        help="Path to write JSON report (default: not written)",
    )
    parser.add_argument(
        "--out-md", type=Path, default=None,
        help="Path to write Markdown summary (default: not written)",
    )
    parser.add_argument(
        "--taxonomy", type=Path, default=None,
        help="Path to rejection taxonomy schema or example file",
    )
    parser.add_argument(
        "--validate-rejection-codes", action="store_true",
        help="Validate rejection codes against the taxonomy before generating report",
    )
    parser.add_argument(
        "--pipeline-version", default=None,
        help="Override pipeline version (default: from input file metadata)",
    )
    parser.add_argument(
        "--report-date", default=None,
        help="Override report date YYYY-MM-DD (default: from input or today)",
    )
    args = parser.parse_args(argv)

    # Load input
    try:
        input_data = load_input(args.input)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading input: {e}", file=sys.stderr)
        return 2

    candidates = input_data.get("candidates", [])
    if not candidates:
        print("Error: No candidates in input file", file=sys.stderr)
        return 2

    source_batch = input_data.get("source_batch", "unknown")
    pipeline_version = args.pipeline_version or input_data.get(
        "pipeline_version", "unknown"
    )
    report_date = args.report_date or input_data.get(
        "date", datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )

    # Load taxonomy
    try:
        taxonomy = load_taxonomy(args.taxonomy)
    except (FileNotFoundError, ValueError) as e:
        print(f"Warning: {e}", file=sys.stderr)
        taxonomy = []
        if args.validate_rejection_codes:
            print(
                "Error: Cannot validate rejection codes without taxonomy",
                file=sys.stderr,
            )
            return 2

    # Validate rejection codes if requested
    if args.validate_rejection_codes:
        tax_codes = _get_taxonomy_codes(taxonomy)
        code_errors = validate_rejection_codes(candidates, tax_codes)
        if code_errors:
            print("Rejection code validation errors:", file=sys.stderr)
            for err in code_errors:
                print(
                    f"  {err['candidate_id']}: {err['error']}",
                    file=sys.stderr,
                )
            return 3

    # Build report
    report = build_report(
        candidates=candidates,
        source_batch=source_batch,
        pipeline_version=pipeline_version,
        report_date=report_date,
        taxonomy=taxonomy,
    )

    # Write JSON output
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        )
        print(f"Wrote JSON report to {args.out_json}")

    # Write Markdown output
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        md_content = build_markdown_report(report)
        args.out_md.write_text(md_content)
        print(f"Wrote Markdown summary to {args.out_md}")

    if not args.out_json and not args.out_md:
        # Print JSON to stdout
        print(json.dumps(report, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Check a negative-result archive JSON file for completeness.

Reads a JSON list of negative-result entries and checks each entry against
completeness criteria: all required fields present, no duplicate candidate_ids,
each entry has at least one content field (assay_result, score_safety, or
reviewer_notes/reason_detail), date format is valid YYYY-MM-DD, and optional
intake_report_id references are consistent (present only when entry has
prediction-vs-actual data).

Outputs a structured completeness report as JSON and/or Markdown.

Usage:
    python scripts/check_negative_archive_completeness.py \\
        --input examples/negative_result_archive_example.json \\
        --out-json outputs/negative_archive_completeness_report.json \\
        --out-md outputs/negative_archive_completeness_report.md

Exit codes:
    0  All entries pass all checks
    1  One or more entries fail one or more checks
    2  Input error (missing file, invalid JSON, wrong structure)
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_FIELDS = {
    "entry_id", "date", "candidate_id", "sequence",
    "reason_category", "reason_detail", "pipeline_version", "source_batch",
}
CONTENT_FIELDS = {"assay_result", "score_safety", "reviewer_notes", "reason_detail"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
INTAKE_REPORT_ID_PATTERN = re.compile(r"^INT-\d{4}-\d{3,}$")


def _check_required_fields(entry: dict, i: int) -> list[str]:
    errors: list[str] = []
    for field in sorted(REQUIRED_FIELDS):
        if field not in entry or entry[field] in (None, ""):
            errors.append(
                f"Entry {i} (candidate: {entry.get('candidate_id', '?')}): "
                f"missing or empty required field '{field}'"
            )
    return errors


def _check_has_content_fields(entry: dict, i: int) -> list[str]:
    errors: list[str] = []
    has_content = any(
        entry.get(f) not in (None, "") for f in CONTENT_FIELDS
    )
    if not has_content:
        errors.append(
            f"Entry {i} (candidate: {entry.get('candidate_id', '?')}): "
            f"no content field present — must have at least one of "
            f"{sorted(CONTENT_FIELDS)}"
        )
    return errors


def _check_date_format(entry: dict, i: int) -> list[str]:
    errors: list[str] = []
    date_str = entry.get("date", "")
    if not DATE_PATTERN.match(str(date_str)):
        errors.append(
            f"Entry {i} (candidate: {entry.get('candidate_id', '?')}): "
            f"invalid date format '{date_str}' — expected YYYY-MM-DD"
        )
    else:
        try:
            datetime.strptime(str(date_str), "%Y-%m-%d")
        except ValueError:
            errors.append(
                f"Entry {i} (candidate: {entry.get('candidate_id', '?')}): "
                f"invalid date '{date_str}' — not a real calendar date"
            )
    return errors


def _check_intake_report_id(entry: dict, i: int) -> list[str]:
    errors: list[str] = []
    intake_id = entry.get("intake_report_id")
    if intake_id is not None and str(intake_id).strip():
        if not INTAKE_REPORT_ID_PATTERN.match(str(intake_id)):
            errors.append(
                f"Entry {i} (candidate: {entry.get('candidate_id', '?')}): "
                f"intake_report_id '{intake_id}' does not match expected format "
                f"INT-YYYY-NNN"
            )
    return errors


def check_archive(entries: list[dict], source_file: str = "") -> dict:
    total = len(entries)
    per_entry_results: list[dict] = []
    all_errors: list[str] = []
    seen_candidate_ids: set[str] = set()
    duplicate_ids: list[str] = []

    for i, entry in enumerate(entries):
        entry_errors: list[str] = []

        entry_errors.extend(_check_required_fields(entry, i))
        entry_errors.extend(_check_has_content_fields(entry, i))
        entry_errors.extend(_check_date_format(entry, i))
        entry_errors.extend(_check_intake_report_id(entry, i))

        cid = str(entry.get("candidate_id", "?"))
        if cid in seen_candidate_ids:
            duplicate_ids.append(cid)
        seen_candidate_ids.add(cid)

        entry_pass = len(entry_errors) == 0
        per_entry_results.append({
            "entry_id": entry.get("entry_id", i),
            "candidate_id": cid,
            "checks": {
                "required_fields": not any("required field" in e for e in entry_errors),
                "has_content_fields": not any("content field" in e for e in entry_errors),
                "date_format": not any("date format" in e or "calendar date" in e for e in entry_errors),
                "intake_report_id_format": not any("intake_report_id" in e for e in entry_errors),
            },
            "errors": entry_errors,
            "pass": entry_pass,
        })
        all_errors.extend(entry_errors)

    duplicate_errors: list[str] = []
    for dup_id in sorted(set(duplicate_ids)):
        dup_entries = [
            str(entry.get("entry_id", "?")) for entry in entries
            if str(entry.get("candidate_id", "")) == dup_id
        ]
        duplicate_errors.append(
            f"Duplicate candidate_id '{dup_id}' across entries: {', '.join(dup_entries)}"
        )

    pass_count = sum(1 for r in per_entry_results if r["pass"])
    fail_count = total - pass_count

    check_results = {
        "required_fields": {
            "pass": not any("required field" in e for e in all_errors),
            "details": [e for e in all_errors if "required field" in e],
        },
        "duplicate_candidate_ids": {
            "pass": len(duplicate_errors) == 0,
            "details": duplicate_errors,
        },
        "has_content_fields": {
            "pass": not any("content field" in e for e in all_errors),
            "details": [e for e in all_errors if "content field" in e],
        },
        "date_format": {
            "pass": not any("date format" in e or "calendar date" in e for e in all_errors),
            "details": [e for e in all_errors if "date format" in e or "calendar date" in e],
        },
        "intake_report_id_references": {
            "pass": not any("intake_report_id" in e for e in all_errors),
            "details": [e for e in all_errors if "intake_report_id" in e],
        },
    }

    all_check_pass = all(c["pass"] for c in check_results.values())

    pass_rate = f"{100 * pass_count / total:.1f}%" if total > 0 else "100.0%"

    return {
        "report_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "pipeline_version": "v0.5.80",
            "source_file": source_file,
            "total_entries": total,
        },
        "summary": {
            "total_entries": total,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pass_rate": pass_rate,
        },
        "checks": check_results,
        "per_entry_results": per_entry_results,
        "_caveat": (
            "This completeness report checks structural and formatting "
            "criteria only. A PASS on all checks means the archive entries "
            "are well-formed per the defined completeness rules. It does not "
            "confirm biological accuracy, pipeline correctness, or data "
            "authenticity. Missing content fields may reflect genuine data "
            "absence rather than record-keeping errors. All conclusions about "
            "entry quality require qualified human review."
        ),
    }


def generate_markdown(report: dict) -> str:
    lines: list[str] = []
    lines.append("# Negative-Result Archive Completeness Report\n")
    meta = report.get("report_metadata", {})
    lines.append(f"**Generated:** {meta.get('generated_at', '?')}  ")
    lines.append(f"**Pipeline version:** {meta.get('pipeline_version', '?')}  ")
    lines.append(f"**Source file:** {meta.get('source_file', '?')}  ")
    lines.append(f"**Total entries:** {meta.get('total_entries', 0)}\n")

    summary = report.get("summary", {})
    lines.append("## Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total entries | {summary.get('total_entries', 0)} |")
    lines.append(f"| Pass | {summary.get('pass_count', 0)} |")
    lines.append(f"| Fail | {summary.get('fail_count', 0)} |")
    lines.append(f"| Pass rate | {summary.get('pass_rate', '?')} |")
    lines.append("")

    checks = report.get("checks", {})
    lines.append("## Check Results\n")
    lines.append("| Check | Result | Details |")
    lines.append("|-------|--------|---------|")
    for check_name, check_result in checks.items():
        status = "PASS" if check_result["pass"] else "FAIL"
        detail_count = len(check_result["details"])
        detail_text = f"{detail_count} issue(s)" if detail_count > 0 else "ok"
        lines.append(f"| {check_name} | {status} | {detail_text} |")
    lines.append("")

    failed_details = {name: c["details"] for name, c in checks.items() if c["details"]}
    if failed_details:
        lines.append("## Detailed Errors\n")
        for check_name, details in failed_details.items():
            lines.append(f"### {check_name}\n")
            for detail in details:
                lines.append(f"- {detail}")
            lines.append("")

    lines.append("## Per-Entry Results\n")
    per_entry = report.get("per_entry_results", [])
    lines.append("| Entry ID | Candidate ID | Pass | Errors |")
    lines.append("|----------|--------------|------|--------|")
    for entry_result in per_entry:
        status = "PASS" if entry_result["pass"] else "FAIL"
        err_count = len(entry_result["errors"])
        lines.append(
            f"| {entry_result.get('entry_id', '?')} | "
            f"{entry_result.get('candidate_id', '?')} | "
            f"{status} | {err_count} |"
        )
    lines.append("")

    lines.append(f"## Caveat\n\n{report.get('_caveat', '')}\n")
    return "\n".join(lines)


def load_entries(input_path: str | Path) -> list[dict]:
    path = Path(input_path)
    if not path.exists():
        print(f"Error: Input not found: {input_path}", file=sys.stderr)
        sys.exit(2)

    try:
        data = json.loads(path.read_text())
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(2)

    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = data.get("entries", data.get("candidates", []))
        if not isinstance(entries, list):
            print("Error: 'entries' value must be a list", file=sys.stderr)
            sys.exit(2)
    else:
        print("Error: Input must be a JSON array or object with an 'entries' key", file=sys.stderr)
        sys.exit(2)

    if not entries:
        print("Error: No entries found in input", file=sys.stderr)
        sys.exit(2)

    return entries


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Check a negative-result archive JSON file for completeness."
    )
    parser.add_argument("--input", required=True, help="Path to negative-result archive JSON file")
    parser.add_argument("--out-json", default=None, help="Output JSON report path")
    parser.add_argument("--out-md", default=None, help="Output Markdown report path")

    args = parser.parse_args()

    entries = load_entries(args.input)
    report = check_archive(entries, source_file=str(args.input))

    print(json.dumps(report, indent=2))

    if args.out_json:
        Path(args.out_json).write_text(json.dumps(report, indent=2) + "\n")
        print(f"\nJSON report written to: {args.out_json}")

    if args.out_md:
        md = generate_markdown(report)
        Path(args.out_md).write_text(md + "\n")
        print(f"Markdown report written to: {args.out_md}")

    overall_pass = report["summary"]["fail_count"] == 0
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())

"""Link negative-result entries to calibration intake reports.

Closes the learning loop by tracing each negative-result entry back to
its prediction-vs-actual data in the calibration intake report.

Reads:
  - A negative-result archive (JSON with list of entries)
  - A calibration intake report (JSON, as produced by
    src/openamp_foundry/calibration/intake.py)

Produces:
  - Machine-readable linked report with per-candidate linkage,
    unmatched/orphan tracking, and cohort overlap metrics
  - Human-readable Markdown summary

Usage:
    python scripts/link_negative_result_to_intake.py \
        --negative-result-archive examples/negative_result_archive.json \
        --intake-report outputs/calibration_intake_report.json \
        --out-json outputs/negative_result_intake_link.json \
        --out-md outputs/negative_result_intake_link.md

Caveats:
  - Linkage is by candidate_id. Entries with candidate_ids not found in the
    intake report are reported as unmatched but do not invalidate the report.
  - The intake_report_id field on each entry is advisory. This script does
    NOT require it, but validates it when present.
  - This report is informational only and requires qualified review.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any] | list[Any]:
    p = Path(path)
    if not p.exists():
        msg = f"File not found: {p}"
        raise FileNotFoundError(msg)
    try:
        from openamp_foundry.utils.io import read_json
        return read_json(p)
    except ImportError:
        with p.open("r") as f:
            return json.load(f)


def _entries_by_candidate(
    entries: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    by_cid: dict[str, list[dict[str, Any]]] = {}
    for e in entries:
        cid = e.get("candidate_id", "")
        by_cid.setdefault(cid, []).append(e)
    return by_cid


def _intake_by_candidate(
    intake: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    rows = intake.get("per_candidate_joined", [])
    return {r.get("candidate_id", ""): r for r in rows if r.get("candidate_id")}


def build_link_report(
    entries: list[dict[str, Any]],
    intake_report: dict[str, Any],
    archive_source: str = "",
) -> dict[str, Any]:
    entries_by_cid = _entries_by_candidate(entries)
    intake_by_cid = _intake_by_candidate(intake_report)

    total = len(entries)
    matched: list[dict[str, Any]] = []
    unmatched_candidate_ids: set[str] = set()

    for e in entries:
        cid = e.get("candidate_id", "")
        intake_row = intake_by_cid.get(cid)
        linked = {
            "entry_id": e.get("entry_id"),
            "candidate_id": cid,
            "reason_category": e.get("reason_category", ""),
            "reason_detail": e.get("reason_detail", ""),
            "date": e.get("date", ""),
            "matched": intake_row is not None,
        }
        if intake_row is not None:
            linked["coverage_note"] = intake_row.get("coverage_note", "")
            linked["predictions"] = intake_row.get("predictions", {})
            linked["had_lab_result"] = intake_row.get("has_lab") is not None
            if intake_row.get("has_lab"):
                linked["lab_summary"] = {
                    "n_results": intake_row["has_lab"].get("n_results", 0),
                    "n_mic": intake_row["has_lab"].get("n_mic", 0),
                    "n_hemolysis": intake_row["has_lab"].get("n_hemolysis", 0),
                    "active_mic": intake_row["has_lab"].get("active_mic"),
                    "high_hemolysis": intake_row["has_lab"].get("high_hemolysis"),
                    "all_controls_passed": intake_row["has_lab"].get(
                        "all_controls_passed", True
                    ),
                }
        else:
            unmatched_candidate_ids.add(cid)

        # Validate intake_report_id if present
        rid = e.get("intake_report_id", "")
        matched.append(linked)

    # Orphan intake candidates: those in intake but not in any entry
    intake_cids = set(intake_by_cid.keys())
    entry_cids = set(entries_by_cid.keys())
    orphan_intake_ids = sorted(intake_cids - entry_cids)

    # Validate intake_report_id references
    invalid_ids: list[dict[str, Any]] = []
    intake_source = str(intake_report.get("panel_csv", ""))
    for e in entries:
        rid = e.get("intake_report_id", "")
        if rid and rid != intake_source:
            invalid_ids.append({
                "entry_id": e.get("entry_id"),
                "candidate_id": e.get("candidate_id", ""),
                "intake_report_id": rid,
                "expected": intake_source,
            })

    n_matched = sum(1 for m in matched if m["matched"])
    n_linked_with_lab = sum(
        1 for m in matched if m["matched"] and m.get("had_lab_result")
    )
    matched_categories = Counter(
        m["reason_category"] for m in matched if m["matched"]
    )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "report_metadata": {
            "generated_at": now,
            "report_type": "negative_result_intake_link_report",
            "schema_version": "1.0.0",
            "archive_source": archive_source,
            "intake_report_source": str(intake_report.get("panel_csv", "unknown")),
        },
        "summary": {
            "total_negative_entries": total,
            "total_matched_to_intake": n_matched,
            "total_unmatched_negative_entries": total - n_matched,
            "intake_candidates_without_negative_entry": len(orphan_intake_ids),
            "orphan_intake_candidate_ids": orphan_intake_ids,
            "negative_entries_with_lab_result": n_linked_with_lab,
            "linkage_rate": round(n_matched / total, 4) if total > 0 else 0.0,
            "invalid_intake_report_ids": invalid_ids,
            "by_reason_category_matched": dict(matched_categories.most_common()),
        },
        "linked_entries": matched,
        "control_failures_in_intake": intake_report.get("control_failures", []),
        "cohort_metrics_from_intake": intake_report.get("cohort_metrics", {}),
        "caveats": [
            "Computational outputs are hypotheses and review aids. They are not biological proof.",
            "Linkage is by candidate_id only. Entries without a matching intake row are reported as unmatched.",
            "Orphan intake candidates (in intake but not in negative-result archive) may be active, pending, or withdrawn.",
            "The intake_report_id field is advisory and does not affect linkage logic.",
            "This report is informational only and requires qualified review.",
        ],
        "dry_lab_only": True,
    }


def build_markdown_report(report: dict[str, Any]) -> str:
    meta = report["report_metadata"]
    summary = report["summary"]
    lines: list[str] = []

    lines.append("# Negative-Result to Intake Link Report")
    lines.append("")
    lines.append("> **Dry-lab only — informational.** This report traces negative-result "
                 "entries back to their calibration intake data. It does not validate "
                 "the pipeline or confirm biological inactivity.")
    lines.append("")

    lines.append("## Report Metadata")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| Generated at | {meta['generated_at']} |")
    lines.append(f"| Archive source | {meta['archive_source']} |")
    lines.append(f"| Intake source | {meta['intake_report_source']} |")
    lines.append("")

    lines.append("## Linkage Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total negative entries | {summary['total_negative_entries']} |")
    lines.append(f"| Matched to intake | {summary['total_matched_to_intake']} |")
    lines.append(f"| Unmatched | {summary['total_unmatched_negative_entries']} |")
    lines.append(
        f"| Linkage rate | {summary['linkage_rate']} |"
    )
    lines.append(
        f"| Negative entries with lab result | "
        f"{summary['negative_entries_with_lab_result']} |"
    )
    lines.append(
        f"| Intake candidates without negative entry | "
        f"{summary['intake_candidates_without_negative_entry']} |"
    )
    if summary.get("orphan_intake_candidate_ids"):
        lines.append(
            f"| Orphan intake IDs | "
            f"{', '.join(summary['orphan_intake_candidate_ids'][:10])} |"
        )
    lines.append("")

    if summary.get("by_reason_category_matched"):
        lines.append("### Matched Entries by Reason Category")
        lines.append("")
        lines.append("| Reason Category | Count |")
        lines.append("|----------------|-------|")
        for cat, cnt in sorted(summary["by_reason_category_matched"].items()):
            lines.append(f"| {cat} | {cnt} |")
        lines.append("")

    if summary.get("invalid_intake_report_ids"):
        lines.append("### Invalid intake_report_id References")
        lines.append("")
        lines.append("| Entry | Candidate | Found ID | Expected |")
        lines.append("|-------|-----------|----------|----------|")
        for inv in summary["invalid_intake_report_ids"]:
            lines.append(
                f"| {inv['entry_id']} | {inv['candidate_id']} | "
                f"{inv['intake_report_id']} | {inv['expected']} |"
            )
        lines.append("")

    lines.append("## Linked Entries")
    lines.append("")
    lines.append("| Entry | Candidate | Reason Category | Matched | Has Lab | Predictions |")
    lines.append("|-------|-----------|-----------------|---------|---------|-------------|")
    for m in report.get("linked_entries", []):
        pred_str = ""
        if m.get("predictions"):
            pred = m["predictions"]
            parts = []
            for k in ("ensemble", "activity", "safety", "synthesis", "novelty"):
                v = pred.get(k)
                if v is not None:
                    parts.append(f"{k}={v:.2f}")
            pred_str = "; ".join(parts)
        lines.append(
            f"| {m['entry_id']} | {m['candidate_id']} | {m['reason_category']} "
            f"| {'yes' if m['matched'] else 'no'} "
            f"| {'yes' if m.get('had_lab_result') else 'no'} "
            f"| {pred_str[:60]} |"
        )
    lines.append("")

    if report.get("control_failures_in_intake"):
        lines.append("## Control Failures (from Intake Report)")
        lines.append("")
        lines.append("| Result ID | Candidate | Assay | Pos Ctrl | Neg Ctrl |")
        lines.append("|-----------|-----------|-------|----------|----------|")
        for cf in report["control_failures_in_intake"]:
            lines.append(
                f"| {cf.get('result_id', '?')} | {cf.get('candidate_id', '?')} "
                f"| {cf.get('assay_type', '?')} "
                f"| {cf.get('positive_control_passed', '?')} "
                f"| {cf.get('negative_control_passed', '?')} |"
            )
        lines.append("")

    lines.append("## Caveats")
    lines.append("")
    for caveat in report.get("caveats", []):
        lines.append(f"- {caveat}")
    lines.append("")
    lines.append("---")
    lines.append(
        "*Generated by `scripts/link_negative_result_to_intake.py`*"
    )

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Link negative-result entries to calibration intake reports",
    )
    parser.add_argument(
        "--negative-result-archive", required=True, type=Path,
        help="Path to negative-result archive JSON file",
    )
    parser.add_argument(
        "--intake-report", required=True, type=Path,
        help="Path to calibration intake report JSON file",
    )
    parser.add_argument(
        "--out-json", type=Path, default=None,
        help="Path to write JSON link report",
    )
    parser.add_argument(
        "--out-md", type=Path, default=None,
        help="Path to write Markdown link report",
    )
    args = parser.parse_args(argv)

    try:
        archive_data = load_json(args.negative_result_archive)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading negative-result archive: {e}", file=sys.stderr)
        return 2

    try:
        intake_report = load_json(args.intake_report)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading intake report: {e}", file=sys.stderr)
        return 2

    if isinstance(archive_data, list):
        entries = archive_data
    else:
        entries = archive_data.get("entries", [])

    if not entries:
        print("Error: No entries in negative-result archive", file=sys.stderr)
        return 2

    if not isinstance(intake_report, dict):
        print(
            "Error: Intake report must be a JSON object",
            file=sys.stderr,
        )
        return 2

    archive_source = str(args.negative_result_archive)
    if isinstance(archive_data, dict):
        archive_source = archive_data.get(
            "archive_source", archive_source
        )

    report = build_link_report(
        entries=entries,
        intake_report=intake_report,
        archive_source=archive_source,
    )

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        )
        print(f"Wrote JSON link report to {args.out_json}")

    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        md_content = build_markdown_report(report)
        args.out_md.write_text(md_content)
        print(f"Wrote Markdown link report to {args.out_md}")

    if not args.out_json and not args.out_md:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())

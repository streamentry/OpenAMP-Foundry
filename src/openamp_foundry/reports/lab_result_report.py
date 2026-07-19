"""Wet-lab result reporting.

Converts validated lab result JSON files into a reproducible summary artifact for
human review, calibration intake, and future active-learning loops.

This module is descriptive only. It does not upgrade assay outcomes into drug,
efficacy, or safety claims.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openamp_foundry.data.lab_results import (
    candidate_result_map,
    duplicate_result_ids,
    load_lab_results_dir_with_errors,
    summarise_candidate_outcomes,
    summarise_lab_results,
)


def build_lab_result_report(results_dir: str | Path) -> dict[str, Any]:
    """Build a machine-readable wet-lab result report from a directory of JSON files."""
    results, invalid_lab_result_files = load_lab_results_dir_with_errors(results_dir)
    summary = summarise_lab_results(results)
    by_candidate = summarise_candidate_outcomes(results)
    duplicate_ids = duplicate_result_ids(results)
    controls_failed = [
        {
            "result_id": r["result_id"],
            "candidate_id": r["candidate_id"],
            "assay_type": r["assay_type"],
            "positive_control_passed": r["positive_control_passed"],
            "negative_control_passed": r["negative_control_passed"],
        }
        for r in results
        if not (r.get("positive_control_passed") and r.get("negative_control_passed"))
    ]
    by_lab: dict[str, int] = {}
    for r in results:
        lab = r.get("performed_by_lab", "unknown")
        by_lab[lab] = by_lab.get(lab, 0) + 1

    return {
        "summary": summary,
        "n_invalid_lab_result_files": len(invalid_lab_result_files),
        "invalid_lab_result_files": invalid_lab_result_files,
        "input_validation_status": (
            "blocked_on_invalid_results"
            if invalid_lab_result_files
            else "blocked_on_duplicate_ids"
            if duplicate_ids
            else "input_validated"
        ),
        "duplicate_lab_result_ids": duplicate_ids,
        "n_duplicate_lab_result_ids": len(duplicate_ids),
        "by_candidate": by_candidate,
        "control_failures": controls_failed,
        "by_lab": dict(sorted(by_lab.items())),
        "n_candidates": len(candidate_result_map(results)),
        "report_disclaimer": (
            "Wet-lab result report. Experimental observations on computationally nominated "
            "candidates only. Not proof of efficacy, safety, clinical utility, or novelty. "
            "Qualified expert review and independent replication remain mandatory."
        ),
    }


def write_lab_result_markdown(report: dict[str, Any], out_path: str | Path) -> None:
    """Write a human-readable markdown report."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    s = report["summary"]

    lines = [
        "# Wet-Lab Result Report",
        "",
        report["report_disclaimer"],
        "",
        "## Batch Summary",
        "",
        f"- Results loaded: {s.get('n_results', 0)}",
        f"- Candidates covered: {report.get('n_candidates', 0)}",
        f"- Results with both controls passing: {s.get('n_valid_controls', 0)}",
        f"- Invalid result files: {report.get('n_invalid_lab_result_files', 0)}",
        f"- Duplicate result IDs: {report.get('n_duplicate_lab_result_ids', 0)}",
        "",
        "## Assay Type Counts",
        "",
        "| Assay type | Count |",
        "|---|---:|",
    ]
    for assay_type, count in sorted(s.get("by_assay_type", {}).items()):
        lines.append(f"| {assay_type} | {count} |")

    lines += [
        "",
        "## Qualitative Outcome Counts",
        "",
        "| Outcome | Count |",
        "|---|---:|",
    ]
    for outcome, count in sorted(s.get("by_qualitative_result", {}).items()):
        lines.append(f"| {outcome} | {count} |")

    lines += [
        "",
        "## Per-Candidate Rollup",
        "",
        "| Candidate | Results | Usable | Assays | Usable active | Usable toxic | Controls ok | Window |",
        "|---|---:|---:|---|---|---|---|---|",
    ]
    for row in report.get("by_candidate", []):
        lines.append(
            f"| {row['candidate_id']} | {row['n_results']} | {row['n_usable_results']} | {', '.join(row['assay_types'])} | "
            f"{_yes_no(row['has_any_active'])} | {_yes_no(row['has_any_toxic'])} | "
            f"{_yes_no(row['all_controls_passed'])} | {row['first_assay_date']} to {row['last_assay_date']} |"
        )

    lines += ["", "## Control Failures", ""]
    failures = report.get("control_failures", [])
    if failures:
        lines += [
            "| Result ID | Candidate | Assay | Positive control | Negative control |",
            "|---|---|---|---|---|",
        ]
        for item in failures:
            lines.append(
                f"| {item['result_id']} | {item['candidate_id']} | {item['assay_type']} | "
                f"{_yes_no(item['positive_control_passed'])} | {_yes_no(item['negative_control_passed'])} |"
            )
    else:
        lines.append("No control failures recorded.")

    invalid_files = report.get("invalid_lab_result_files", [])
    if invalid_files:
        lines += [
            "",
            "## Input Validation Blockers",
            "",
            "> Invalid result files were excluded from this report.",
            "",
            "| File | Error |",
            "|---|---|",
        ]
        lines.extend(f"| {item['file']} | {item['error']} |" for item in invalid_files)

    duplicate_ids = report.get("duplicate_lab_result_ids", [])
    if duplicate_ids:
        lines += [
            "",
            "## Input Integrity Blockers",
            "",
            "> Duplicate result IDs were retained but this report is not a clean cohort.",
            "",
            "- Duplicate result IDs: " + ", ".join(duplicate_ids),
        ]

    lines += [
        "",
        "## Next Review Questions",
        "",
        "- Which candidates remain interesting after removing any result with failed controls?",
        "- Which assay readouts need repeat runs before they can affect selection policy?",
        "- Do the observed outcomes support recalibration, or is the batch still too small or noisy?",
        "",
    ]

    p.write_text("\n".join(lines), encoding="utf-8")


def write_lab_result_json(report: dict[str, Any], out_path: str | Path) -> None:
    """Write the machine-readable wet-lab result report."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report, indent=2), encoding="utf-8")


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"

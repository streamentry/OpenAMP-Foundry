"""Result-quality flag propagation into the calibration engine.

Low-quality outcomes cannot drive updates — garbage results must not
update the scoring model. This module provides quality assessment of
lab results before they enter the calibration pipeline.

Dry-lab only. Does not measure biological activity.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

QUALITY_FLAGS: dict[str, str] = {
    "low_sample_quality": "Sample quality below acceptable threshold",
    "assay_interference": "Assay interference detected (e.g., compound precipitation, quenching)",
    "ambiguous_activity": "Activity borderline or unclear from dose-response",
    "contamination": "Sample contamination detected",
    "protocol_deviation": "Protocol deviation recorded for this result",
    "borderline_threshold": "Result at borderline of assay threshold",
    "replicate_disagreement": "Replicates show high variability",
    "missing_negative_control": "Negative control missing or failed",
}

EXCLUDED_FLAGS: set[str] = {"contamination", "assay_interference"}


@dataclass
class ResultQualityReport:
    candidate_id: str
    flags: list[str] = field(default_factory=list)
    quality_level: str = "high"
    can_drive_update: bool = True
    propagation_action: str = "include"
    explanation: str = ""
    dry_lab_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def assess_result_quality(
    candidate_id: str,
    flags: list[str],
) -> ResultQualityReport:
    """Assess the quality of a single result and determine whether it
    can drive a calibration update.

    Parameters
    ----------
    candidate_id : str
        Identifier for the candidate.
    flags : list of str
        Quality flags from QUALITY_FLAGS keys.

    Returns
    -------
    ResultQualityReport with quality_level, can_drive_update,
    propagation_action, and explanation.
    """
    unknown = [f for f in flags if f not in QUALITY_FLAGS]
    if unknown:
        raise ValueError(
            f"Unknown quality flags for {candidate_id}: {unknown}. "
            f"Valid flags: {list(QUALITY_FLAGS.keys())}"
        )

    has_excluded = any(f in EXCLUDED_FLAGS for f in flags)

    if has_excluded:
        return ResultQualityReport(
            candidate_id=candidate_id,
            flags=flags,
            quality_level="excluded",
            can_drive_update=False,
            propagation_action="exclude",
            explanation=(
                f"Candidate {candidate_id} excluded due to "
                f"irrecoverable quality flags: {flags}. "
                f"Contamination or assay interference present."
            ),
            dry_lab_only=True,
        )

    if len(flags) >= 2:
        return ResultQualityReport(
            candidate_id=candidate_id,
            flags=flags,
            quality_level="low",
            can_drive_update=False,
            propagation_action="exclude",
            explanation=(
                f"Candidate {candidate_id} has {len(flags)} quality flags "
                f"({flags}). Multiple quality issues prevent reliable "
                f"calibration update."
            ),
            dry_lab_only=True,
        )

    if len(flags) == 1:
        return ResultQualityReport(
            candidate_id=candidate_id,
            flags=flags,
            quality_level="acceptable",
            can_drive_update=True,
            propagation_action="include_with_caution",
            explanation=(
                f"Candidate {candidate_id} has 1 quality flag "
                f"({flags[0]}). Result is acceptable but should be "
                f"used with caution in calibration."
            ),
            dry_lab_only=True,
        )

    return ResultQualityReport(
        candidate_id=candidate_id,
        flags=flags,
        quality_level="high",
        can_drive_update=True,
        propagation_action="include",
        explanation=(
            f"Candidate {candidate_id} has no quality flags. "
            f"Result is suitable for driving calibration updates."
        ),
        dry_lab_only=True,
    )


def filter_results_for_calibration(
    results: list[dict],
) -> dict:
    """Filter a list of result dicts into quality-based categories.

    Each result dict must have:
        candidate_id (str)
        flags (list[str])

    Returns a dict with 'included', 'included_with_caution', 'excluded'
    lists (each containing dict representations of ResultQualityReport),
    a 'summary' with counts, 'can_drive_update_count', and
    'dry_lab_only' flag.
    """
    included: list[dict] = []
    included_with_caution: list[dict] = []
    excluded: list[dict] = []

    for r in results:
        raw_flags = r.get("flags") or []
        report = assess_result_quality(
            candidate_id=r["candidate_id"],
            flags=raw_flags,
        )
        d = report.to_dict()
        if report.propagation_action == "include":
            included.append(d)
        elif report.propagation_action == "include_with_caution":
            included_with_caution.append(d)
        else:
            excluded.append(d)

    total = len(results)
    n_included = len(included)
    n_included_with_caution = len(included_with_caution)
    n_excluded = len(excluded)
    can_drive_update_count = n_included + n_included_with_caution

    return {
        "included": included,
        "included_with_caution": included_with_caution,
        "excluded": excluded,
        "summary": {
            "total": total,
            "included": n_included,
            "included_with_caution": n_included_with_caution,
            "excluded": n_excluded,
        },
        "can_drive_update_count": can_drive_update_count,
        "dry_lab_only": True,
    }


def write_result_quality_json(
    report: ResultQualityReport | dict,
    path: str | Path,
) -> None:
    if isinstance(report, ResultQualityReport):
        data = report.to_dict()
    else:
        data = report
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def write_result_quality_markdown(
    report: ResultQualityReport | dict,
    path: str | Path,
) -> None:
    if isinstance(report, ResultQualityReport):
        data = report.to_dict()
    else:
        data = report

    if "included" in data:
        _write_filter_markdown(data, path)
    else:
        _write_single_report_markdown(data, path)


def _write_single_report_markdown(data: dict, path: str | Path) -> None:
    lines = [
        "# Result Quality Report",
        "",
        "> **Dry-lab only.** This report is a computational assessment.",
        "",
        "## Summary",
        "",
        f"| Key | Value |",
        f"|-----|-------|",
        f"| Candidate ID | {data.get('candidate_id', '?')} |",
        f"| Quality level | {data.get('quality_level', '?')} |",
        f"| Can drive update | {data.get('can_drive_update', '?')} |",
        f"| Propagation action | {data.get('propagation_action', '?')} |",
        f"| Dry-lab only | {data.get('dry_lab_only', '?')} |",
        "",
        "## Flags",
        "",
    ]
    flags = data.get("flags", [])
    if flags:
        for f in flags:
            desc = QUALITY_FLAGS.get(f, "Unknown flag")
            lines.append(f"- **{f}**: {desc}")
    else:
        lines.append("No quality flags.")

    lines.extend([
        "",
        "## Explanation",
        "",
        data.get("explanation", ""),
        "",
        "## Caveats",
        "",
        "- This report is a computational assessment of result quality.",
        "- A high-quality assessment does not confirm biological activity.",
        "- All calibration decisions require qualified human review.",
    ])
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def _write_filter_markdown(data: dict, path: str | Path) -> None:
    summary = data.get("summary", {})
    lines = [
        "# Calibration Result Quality Filter",
        "",
        "> **Dry-lab only.** This report is a computational filter of",
        "> lab result quality for calibration eligibility.",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total results | {summary.get('total', 0)} |",
        f"| Included | {summary.get('included', 0)} |",
        f"| Included with caution | {summary.get('included_with_caution', 0)} |",
        f"| Excluded | {summary.get('excluded', 0)} |",
        f"| Can drive update count | {data.get('can_drive_update_count', 0)} |",
        f"| Dry-lab only | {data.get('dry_lab_only', True)} |",
        "",
        "## Included Results",
        "",
    ]
    for r in data.get("included", []):
        lines.append(
            f"- **{r['candidate_id']}**: {r['quality_level']} "
            f"({r['explanation']})"
        )
    lines.extend([
        "",
        "## Included with Caution",
        "",
    ])
    for r in data.get("included_with_caution", []):
        flags_str = ", ".join(r.get("flags", []))
        lines.append(
            f"- **{r['candidate_id']}**: flags=[{flags_str}] "
            f"({r['explanation']})"
        )
    lines.extend([
        "",
        "## Excluded Results",
        "",
    ])
    for r in data.get("excluded", []):
        flags_str = ", ".join(r.get("flags", []))
        lines.append(
            f"- **{r['candidate_id']}**: flags=[{flags_str}] "
            f"({r['explanation']})"
        )
    lines.extend([
        "",
        "## Caveats",
        "",
        "- Quality filtering is a computational assessment only.",
        "- Excluded results may still contain useful information for review.",
        "- Inclusion does not confirm biological activity or safety.",
        "- All calibration decisions require qualified human review.",
    ])
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")

from __future__ import annotations
from dataclasses import dataclass
from typing import List


VALID_BATCH_GRADES = frozenset({"full", "majority", "minority", "none"})

LOW_COMPLETENESS_GRADES = frozenset({"minority", "none"})

VALID_AUDIT_VERDICTS = frozenset({
    "all_complete",
    "majority_complete",
    "minority_complete",
    "none_complete",
    "no_batches",
})

COMPLETENESS_AUDIT_THRESHOLD = 0.5


@dataclass
class BatchSummaryEntry:
    batch_id: str
    bti_id: str
    n_families_total: int
    n_families_complete: int
    n_families_partial: int
    n_families_empty: int
    batch_completeness_grade: str
    flagged_low_completeness: bool


@dataclass
class CrossBatchAuditSummary:
    cba2_id: str
    pipeline_version: str
    n_batches_total: int
    n_batches_flagged: int
    total_families_across_batches: int
    total_families_complete: int
    total_families_partial: int
    total_families_empty: int
    batch_entries: list[BatchSummaryEntry]
    overall_audit_verdict: str
    flagged_batch_ids: list[str]
    audit_coverage_rate: float
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def _compute_overall_audit_verdict(
    n_batches_total: int,
    n_full: int,
) -> str:
    if n_batches_total == 0:
        return "no_batches"
    if n_full == n_batches_total:
        return "all_complete"
    if n_full >= n_batches_total / 2:
        return "majority_complete"
    if n_full > 0:
        return "minority_complete"
    return "none_complete"


def validate_cross_batch_audit_summary(
    summary: CrossBatchAuditSummary,
) -> list[str]:
    violations = []

    if not summary.cba2_id.startswith("CBA2-"):
        violations.append("cba2_id must start with 'CBA2-'")

    if not summary.dry_lab_only:
        violations.append("dry_lab_only must be True")

    if summary.n_batches_total != len(summary.batch_entries):
        violations.append(
            f"n_batches_total ({summary.n_batches_total}) must equal len(batch_entries) ({len(summary.batch_entries)})"
        )

    expected_flagged = sum(
        1 for e in summary.batch_entries if e.flagged_low_completeness
    )
    if summary.n_batches_flagged != expected_flagged:
        violations.append(
            f"n_batches_flagged ({summary.n_batches_flagged}) must equal count of flagged entries ({expected_flagged})"
        )

    expected_total = sum(e.n_families_total for e in summary.batch_entries)
    if summary.total_families_across_batches != expected_total:
        violations.append(
            f"total_families_across_batches ({summary.total_families_across_batches}) must equal sum of n_families_total ({expected_total})"
        )

    expected_complete = sum(e.n_families_complete for e in summary.batch_entries)
    if summary.total_families_complete != expected_complete:
        violations.append(
            f"total_families_complete ({summary.total_families_complete}) must equal sum of n_families_complete ({expected_complete})"
        )

    expected_partial = sum(e.n_families_partial for e in summary.batch_entries)
    if summary.total_families_partial != expected_partial:
        violations.append(
            f"total_families_partial ({summary.total_families_partial}) must equal sum of n_families_partial ({expected_partial})"
        )

    expected_empty = sum(e.n_families_empty for e in summary.batch_entries)
    if summary.total_families_empty != expected_empty:
        violations.append(
            f"total_families_empty ({summary.total_families_empty}) must equal sum of n_families_empty ({expected_empty})"
        )

    for entry in summary.batch_entries:
        expected_flag = entry.batch_completeness_grade in LOW_COMPLETENESS_GRADES
        if entry.flagged_low_completeness != expected_flag:
            violations.append(
                f"flagged_low_completeness ({entry.flagged_low_completeness}) for batch {entry.batch_id} must equal {expected_flag} for grade '{entry.batch_completeness_grade}'"
            )

    expected_flagged_ids = sorted(
        e.batch_id for e in summary.batch_entries if e.flagged_low_completeness
    )
    if summary.flagged_batch_ids != expected_flagged_ids:
        violations.append(
            f"flagged_batch_ids ({summary.flagged_batch_ids}) must equal {expected_flagged_ids}"
        )

    total_families = summary.total_families_across_batches
    expected_coverage = (
        summary.total_families_complete / total_families if total_families > 0 else 0.0
    )
    if abs(summary.audit_coverage_rate - expected_coverage) > 0.001:
        violations.append(
            f"audit_coverage_rate ({summary.audit_coverage_rate}) must approximately equal {expected_coverage}"
        )

    n_full = sum(
        1 for e in summary.batch_entries if e.batch_completeness_grade == "full"
    )
    expected_verdict = _compute_overall_audit_verdict(
        summary.n_batches_total, n_full
    )
    if summary.overall_audit_verdict != expected_verdict:
        violations.append(
            f"overall_audit_verdict '{summary.overall_audit_verdict}' must be '{expected_verdict}' "
            f"given n_batches_total={summary.n_batches_total} and n_full={n_full}"
        )

    if not summary.limitations:
        violations.append("limitations must be non-empty")

    return violations


def build_cross_batch_audit_summary(
    cba2_id: str,
    pipeline_version: str,
    batch_entry_dicts: list[dict],
    limitations: list[str],
    created_at: str,
) -> CrossBatchAuditSummary:
    batch_entries: list[BatchSummaryEntry] = []
    for d in batch_entry_dicts:
        grade = d["batch_completeness_grade"]
        flagged = grade in LOW_COMPLETENESS_GRADES
        batch_entries.append(
            BatchSummaryEntry(
                batch_id=d["batch_id"],
                bti_id=d["bti_id"],
                n_families_total=d["n_families_total"],
                n_families_complete=d["n_families_complete"],
                n_families_partial=d["n_families_partial"],
                n_families_empty=d["n_families_empty"],
                batch_completeness_grade=grade,
                flagged_low_completeness=flagged,
            )
        )

    n_batches_total = len(batch_entries)
    n_batches_flagged = sum(1 for e in batch_entries if e.flagged_low_completeness)
    total_families_across_batches = sum(e.n_families_total for e in batch_entries)
    total_families_complete = sum(e.n_families_complete for e in batch_entries)
    total_families_partial = sum(e.n_families_partial for e in batch_entries)
    total_families_empty = sum(e.n_families_empty for e in batch_entries)
    audit_coverage_rate = (
        total_families_complete / total_families_across_batches
        if total_families_across_batches > 0
        else 0.0
    )
    flagged_batch_ids = sorted(
        e.batch_id for e in batch_entries if e.flagged_low_completeness
    )
    n_full = sum(
        1 for e in batch_entries if e.batch_completeness_grade == "full"
    )
    overall_audit_verdict = _compute_overall_audit_verdict(
        n_batches_total, n_full
    )

    summary = CrossBatchAuditSummary(
        cba2_id=cba2_id,
        pipeline_version=pipeline_version,
        n_batches_total=n_batches_total,
        n_batches_flagged=n_batches_flagged,
        total_families_across_batches=total_families_across_batches,
        total_families_complete=total_families_complete,
        total_families_partial=total_families_partial,
        total_families_empty=total_families_empty,
        batch_entries=batch_entries,
        overall_audit_verdict=overall_audit_verdict,
        flagged_batch_ids=flagged_batch_ids,
        audit_coverage_rate=audit_coverage_rate,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )

    violations = validate_cross_batch_audit_summary(summary)
    if violations:
        raise ValueError(f"Invalid CrossBatchAuditSummary: {violations}")
    return summary


def format_cross_batch_audit_summary(summary: CrossBatchAuditSummary) -> str:
    flagged_str = ", ".join(summary.flagged_batch_ids) if summary.flagged_batch_ids else "(none)"
    limitations_str = "; ".join(summary.limitations)
    lines = [
        f"Cross-Batch Audit Summary — {summary.cba2_id}",
        f"Pipeline: {summary.pipeline_version}  |  Created: {summary.created_at}",
        f"Batches: {summary.n_batches_total} total, {summary.n_batches_flagged} flagged",
        f"Audit Verdict: {summary.overall_audit_verdict}  |  "
        f"Coverage Rate: {summary.audit_coverage_rate:.3f}",
        f"Families — Complete: {summary.total_families_complete}  |  "
        f"Partial: {summary.total_families_partial}  |  "
        f"Empty: {summary.total_families_empty}  |  "
        f"Total: {summary.total_families_across_batches}",
        f"Flagged Batches: [{flagged_str}]",
        f"Limitations: {limitations_str}",
        "dry_lab_only: True",
        "",
        "Batch Entries:",
    ]
    for entry in summary.batch_entries:
        flag_marker = " [FLAGGED]" if entry.flagged_low_completeness else ""
        lines.append(
            f"  {entry.batch_id} ({entry.bti_id}): "
            f"grade={entry.batch_completeness_grade}, "
            f"complete={entry.n_families_complete}, "
            f"partial={entry.n_families_partial}, "
            f"empty={entry.n_families_empty}, "
            f"total={entry.n_families_total}{flag_marker}"
        )
    return "\n".join(lines)

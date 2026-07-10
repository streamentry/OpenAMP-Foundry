from __future__ import annotations
from dataclasses import dataclass, field


REQUIRED_ARTIFACT_TYPES = frozenset({"BSP", "SEG", "ECC", "STL"})

VALID_GAP_VERDICTS = frozenset({"no_gaps", "partial_gaps", "critical_gaps", "no_families"})


@dataclass
class FamilyGapEntry:
    candidate_family_id: str
    present_artifact_types: list[str]
    missing_artifact_types: list[str]
    gap_count: int
    has_gap: bool


@dataclass
class BatchEvidenceGapReport:
    beg_id: str
    batch_id: str
    pipeline_version: str
    n_families_total: int
    n_families_with_gaps: int
    n_families_complete: int
    family_gap_entries: list[FamilyGapEntry]
    required_artifact_types: list[str]
    overall_gap_verdict: str
    total_missing_count: int
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


@dataclass
class BEGValidationResult:
    valid: bool
    violations: list[str] = field(default_factory=list)


def _compute_gap_verdict(n_families_total: int, n_families_with_gaps: int) -> str:
    if n_families_total == 0:
        return "no_families"
    if n_families_with_gaps == 0:
        return "no_gaps"
    if n_families_with_gaps == n_families_total:
        return "critical_gaps"
    return "partial_gaps"


def validate_batch_evidence_gap_report(
    report: BatchEvidenceGapReport,
) -> BEGValidationResult:
    violations = []

    if not report.beg_id.startswith("BEG-"):
        violations.append("beg_id must start with 'BEG-'")

    if not report.dry_lab_only:
        violations.append("dry_lab_only must be True")

    if report.n_families_total != len(report.family_gap_entries):
        violations.append(
            f"n_families_total ({report.n_families_total}) must equal len(family_gap_entries) "
            f"({len(report.family_gap_entries)})"
        )

    expected_with_gaps = sum(1 for e in report.family_gap_entries if e.has_gap)
    if report.n_families_with_gaps != expected_with_gaps:
        violations.append(
            f"n_families_with_gaps ({report.n_families_with_gaps}) must equal count of entries "
            f"with has_gap=True ({expected_with_gaps})"
        )

    expected_complete = sum(1 for e in report.family_gap_entries if not e.has_gap)
    if report.n_families_complete != expected_complete:
        violations.append(
            f"n_families_complete ({report.n_families_complete}) must equal count of entries "
            f"with has_gap=False ({expected_complete})"
        )

    expected_total_missing = sum(e.gap_count for e in report.family_gap_entries)
    if report.total_missing_count != expected_total_missing:
        violations.append(
            f"total_missing_count ({report.total_missing_count}) must equal sum of gap_counts "
            f"({expected_total_missing})"
        )

    expected_verdict = _compute_gap_verdict(report.n_families_total, report.n_families_with_gaps)
    if report.overall_gap_verdict != expected_verdict:
        violations.append(
            f"overall_gap_verdict '{report.overall_gap_verdict}' must be '{expected_verdict}'"
        )

    if report.required_artifact_types != sorted(REQUIRED_ARTIFACT_TYPES):
        violations.append(
            f"required_artifact_types must equal {sorted(REQUIRED_ARTIFACT_TYPES)}"
        )

    for entry in report.family_gap_entries:
        if entry.candidate_family_id.startswith("TOY-"):
            violations.append(
                f"TOY- candidate_family_id ('{entry.candidate_family_id}') is not allowed"
            )

        if entry.present_artifact_types != sorted(entry.present_artifact_types):
            violations.append(
                f"present_artifact_types must be sorted for {entry.candidate_family_id}"
            )

        if entry.missing_artifact_types != sorted(entry.missing_artifact_types):
            violations.append(
                f"missing_artifact_types must be sorted for {entry.candidate_family_id}"
            )

        if entry.gap_count != len(entry.missing_artifact_types):
            violations.append(
                f"gap_count ({entry.gap_count}) must equal len(missing_artifact_types) "
                f"({len(entry.missing_artifact_types)}) for {entry.candidate_family_id}"
            )

        if entry.has_gap != (entry.gap_count > 0):
            violations.append(
                f"has_gap ({entry.has_gap}) must equal gap_count > 0 for {entry.candidate_family_id}"
            )

    if not report.limitations:
        violations.append("limitations must be non-empty")

    return BEGValidationResult(valid=len(violations) == 0, violations=violations)


def build_batch_evidence_gap_report(
    beg_id: str,
    batch_id: str,
    pipeline_version: str,
    family_artifact_dicts: list[dict],
    limitations: list[str],
    created_at: str,
) -> BatchEvidenceGapReport:
    family_gap_entries: list[FamilyGapEntry] = []
    for d in family_artifact_dicts:
        artifact_ids = d["artifact_ids"]
        present = sorted(set(artifact_ids.keys()) & REQUIRED_ARTIFACT_TYPES)
        missing = sorted(REQUIRED_ARTIFACT_TYPES - set(artifact_ids.keys()))
        gap_count = len(missing)
        family_gap_entries.append(
            FamilyGapEntry(
                candidate_family_id=d["candidate_family_id"],
                present_artifact_types=present,
                missing_artifact_types=missing,
                gap_count=gap_count,
                has_gap=gap_count > 0,
            )
        )

    n_families_total = len(family_gap_entries)
    n_families_with_gaps = sum(1 for e in family_gap_entries if e.has_gap)
    n_families_complete = sum(1 for e in family_gap_entries if not e.has_gap)
    total_missing_count = sum(e.gap_count for e in family_gap_entries)
    overall_gap_verdict = _compute_gap_verdict(n_families_total, n_families_with_gaps)

    return BatchEvidenceGapReport(
        beg_id=beg_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        n_families_total=n_families_total,
        n_families_with_gaps=n_families_with_gaps,
        n_families_complete=n_families_complete,
        family_gap_entries=family_gap_entries,
        required_artifact_types=sorted(REQUIRED_ARTIFACT_TYPES),
        overall_gap_verdict=overall_gap_verdict,
        total_missing_count=total_missing_count,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )


def format_batch_evidence_gap_report(report: BatchEvidenceGapReport) -> str:
    lines = [
        f"Batch Evidence Gap Report — {report.beg_id}",
        f"Batch: {report.batch_id}  |  Pipeline: {report.pipeline_version}",
        f"Verdict: {report.overall_gap_verdict}  |  Families: {report.n_families_total}",
        f"Complete: {report.n_families_complete}  |  With Gaps: {report.n_families_with_gaps}"
        f"  |  Total Missing: {report.total_missing_count}",
        f"Required Artifacts: {', '.join(report.required_artifact_types)}",
        f"Created: {report.created_at}",
        f"Limitations: {'; '.join(report.limitations)}",
        f"dry_lab_only: {report.dry_lab_only}",
    ]
    return "\n".join(lines)

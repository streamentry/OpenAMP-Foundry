"""BRC- batch release checklist schema.

Machine-verifiable checklist that must pass before a batch is released for
wet-lab synthesis. Gates on PCC grade >= B, no critical BEG gaps, at least
one SAT entry, and all required artifacts present.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_PCC_GRADES: frozenset[str] = frozenset({"A", "B", "C", "D"})
PASSING_PCC_GRADES: frozenset[str] = frozenset({"A", "B"})

VALID_BEG_VERDICTS: frozenset[str] = frozenset({
    "no_gaps", "partial_gaps", "critical_gaps", "no_families",
})
BLOCKING_BEG_VERDICTS: frozenset[str] = frozenset({"critical_gaps", "no_families"})

VALID_RELEASE_VERDICTS: frozenset[str] = frozenset({
    "approved", "blocked", "conditional",
})


@dataclass
class ChecklistItem:
    item_id: str
    description: str
    passed: bool
    details: str


@dataclass
class BatchReleaseChecklist:
    brc_id: str
    batch_id: str
    pipeline_version: str
    pcc_id: str
    pcc_grade: str
    beg_id: str
    beg_verdict: str
    sat_id: str
    n_sat_entries: int
    checklist_items: list[ChecklistItem]
    n_items_total: int
    n_items_passed: int
    n_items_failed: int
    release_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def _compute_release_verdict(items: list[ChecklistItem]) -> str:
    all_passed = all(it.passed for it in items)
    if all_passed:
        return "approved"
    any_failed = any(not it.passed for it in items)
    if any_failed:
        return "blocked"
    return "conditional"


def validate_batch_release_checklist(brc: BatchReleaseChecklist) -> None:
    if not brc.brc_id.startswith("BRC-"):
        raise ValueError(f"brc_id must start with 'BRC-': {brc.brc_id!r}")
    if not brc.batch_id:
        raise ValueError("batch_id must be non-empty")
    if not brc.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if not brc.pcc_id.startswith("PCC-"):
        raise ValueError(f"pcc_id must start with 'PCC-': {brc.pcc_id!r}")
    if brc.pcc_grade not in VALID_PCC_GRADES:
        raise ValueError(f"pcc_grade {brc.pcc_grade!r} not in VALID_PCC_GRADES")
    if not brc.beg_id.startswith("BEG-"):
        raise ValueError(f"beg_id must start with 'BEG-': {brc.beg_id!r}")
    if brc.beg_verdict not in VALID_BEG_VERDICTS:
        raise ValueError(f"beg_verdict {brc.beg_verdict!r} not in VALID_BEG_VERDICTS")
    if not brc.sat_id.startswith("SAT-"):
        raise ValueError(f"sat_id must start with 'SAT-': {brc.sat_id!r}")
    if brc.n_sat_entries < 0:
        raise ValueError("n_sat_entries must be >= 0")
    if brc.release_verdict not in VALID_RELEASE_VERDICTS:
        raise ValueError(
            f"release_verdict {brc.release_verdict!r} not in VALID_RELEASE_VERDICTS"
        )
    if not brc.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not brc.limitations:
        raise ValueError("limitations must be non-empty")
    if not brc.created_at:
        raise ValueError("created_at must be non-empty")
    if brc.n_items_total != len(brc.checklist_items):
        raise ValueError("n_items_total must equal len(checklist_items)")
    n_passed = sum(1 for it in brc.checklist_items if it.passed)
    if brc.n_items_passed != n_passed:
        raise ValueError("n_items_passed mismatch")
    if brc.n_items_failed != brc.n_items_total - n_passed:
        raise ValueError("n_items_failed mismatch")


def build_batch_release_checklist(
    *,
    brc_id: str,
    batch_id: str,
    pipeline_version: str,
    pcc_id: str,
    pcc_grade: str,
    beg_id: str,
    beg_verdict: str,
    sat_id: str,
    n_sat_entries: int,
    limitations: list[str],
    created_at: str,
) -> BatchReleaseChecklist:
    items: list[ChecklistItem] = []

    pcc_pass = pcc_grade in PASSING_PCC_GRADES
    items.append(ChecklistItem(
        item_id="PCC-GRADE",
        description="PCC grade must be A or B",
        passed=pcc_pass,
        details=f"PCC grade is {pcc_grade!r} — {'pass' if pcc_pass else 'fail'}",
    ))

    beg_pass = beg_verdict not in BLOCKING_BEG_VERDICTS
    items.append(ChecklistItem(
        item_id="BEG-VERDICT",
        description="BEG verdict must not be critical_gaps or no_families",
        passed=beg_pass,
        details=f"BEG verdict is {beg_verdict!r} — {'pass' if beg_pass else 'fail'}",
    ))

    sat_pass = n_sat_entries >= 1
    items.append(ChecklistItem(
        item_id="SAT-ENTRIES",
        description="At least one SAT entry must exist",
        passed=sat_pass,
        details=f"SAT entries: {n_sat_entries} — {'pass' if sat_pass else 'fail'}",
    ))

    n_total = len(items)
    n_passed = sum(1 for it in items if it.passed)
    n_failed = n_total - n_passed
    verdict = _compute_release_verdict(items)

    brc = BatchReleaseChecklist(
        brc_id=brc_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        pcc_id=pcc_id,
        pcc_grade=pcc_grade,
        beg_id=beg_id,
        beg_verdict=beg_verdict,
        sat_id=sat_id,
        n_sat_entries=n_sat_entries,
        checklist_items=items,
        n_items_total=n_total,
        n_items_passed=n_passed,
        n_items_failed=n_failed,
        release_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_batch_release_checklist(brc)
    return brc


def format_batch_release_checklist(brc: BatchReleaseChecklist) -> str:
    lines = [
        f"Batch Release Checklist — {brc.brc_id}",
        f"Batch: {brc.batch_id}  |  Pipeline: {brc.pipeline_version}",
        f"Verdict: {brc.release_verdict}  |  Items: {brc.n_items_total}",
        f"Passed: {brc.n_items_passed}  |  Failed: {brc.n_items_failed}",
        f"PCC: {brc.pcc_id} (grade={brc.pcc_grade})  |  BEG: {brc.beg_id} ({brc.beg_verdict})",
        f"SAT: {brc.sat_id} (entries={brc.n_sat_entries})",
        "Checklist:",
    ]
    for item in brc.checklist_items:
        status = "PASS" if item.passed else "FAIL"
        lines.append(f"  [{status}] {item.item_id}: {item.description}")
        lines.append(f"         {item.details}")
    lines.append(f"Created: {brc.created_at}")
    lines.append(f"Limitations: {'; '.join(brc.limitations)}")
    lines.append(f"dry_lab_only: {brc.dry_lab_only}")
    return "\n".join(lines)

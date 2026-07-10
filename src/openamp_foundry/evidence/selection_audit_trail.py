from __future__ import annotations
from dataclasses import dataclass, field


VALID_DECISIONS = frozenset({"selected", "rejected", "deferred"})

VALID_STAGES = frozenset({"nomination", "screening", "ranking", "shortlisting"})


@dataclass
class DecisionEntry:
    candidate_family_id: str
    decision: str
    decision_stage: str
    rationale: str
    evidence_artifact_ids: list[str]
    decided_at: str


@dataclass
class SelectionAuditTrail:
    sat_id: str
    batch_id: str
    pipeline_version: str
    n_entries: int
    entries: list[DecisionEntry]
    n_selected: int
    n_rejected: int
    n_deferred: int
    final_shortlist_ids: list[str]
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


@dataclass
class SATValidationResult:
    valid: bool
    violations: list[str] = field(default_factory=list)


def validate_selection_audit_trail(trail: SelectionAuditTrail) -> SATValidationResult:
    violations = []

    if not trail.sat_id.startswith("SAT-"):
        violations.append("sat_id must start with 'SAT-'")

    if not trail.dry_lab_only:
        violations.append("dry_lab_only must be True")

    if trail.n_entries != len(trail.entries):
        violations.append(
            f"n_entries ({trail.n_entries}) must equal len(entries) ({len(trail.entries)})"
        )

    expected_selected = sum(1 for e in trail.entries if e.decision == "selected")
    if trail.n_selected != expected_selected:
        violations.append(
            f"n_selected ({trail.n_selected}) must equal count of selected entries ({expected_selected})"
        )

    expected_rejected = sum(1 for e in trail.entries if e.decision == "rejected")
    if trail.n_rejected != expected_rejected:
        violations.append(
            f"n_rejected ({trail.n_rejected}) must equal count of rejected entries ({expected_rejected})"
        )

    expected_deferred = sum(1 for e in trail.entries if e.decision == "deferred")
    if trail.n_deferred != expected_deferred:
        violations.append(
            f"n_deferred ({trail.n_deferred}) must equal count of deferred entries ({expected_deferred})"
        )

    expected_shortlist = sorted({e.candidate_family_id for e in trail.entries if e.decision == "selected"})
    if trail.final_shortlist_ids != expected_shortlist:
        violations.append(
            f"final_shortlist_ids {trail.final_shortlist_ids} must equal sorted selected family IDs {expected_shortlist}"
        )

    for entry in trail.entries:
        if entry.candidate_family_id.startswith("TOY-"):
            violations.append(f"TOY- candidate_family_id ('{entry.candidate_family_id}') is not allowed")

        if entry.decision not in VALID_DECISIONS:
            violations.append(
                f"decision '{entry.decision}' must be one of {sorted(VALID_DECISIONS)} for {entry.candidate_family_id}"
            )

        if entry.decision_stage not in VALID_STAGES:
            violations.append(
                f"decision_stage '{entry.decision_stage}' must be one of {sorted(VALID_STAGES)} for {entry.candidate_family_id}"
            )

        if not entry.rationale:
            violations.append(f"rationale must be non-empty for {entry.candidate_family_id}")

        if entry.evidence_artifact_ids != sorted(entry.evidence_artifact_ids):
            violations.append(
                f"evidence_artifact_ids must be sorted for {entry.candidate_family_id}"
            )

    if not trail.limitations:
        violations.append("limitations must be non-empty")

    return SATValidationResult(valid=len(violations) == 0, violations=violations)


def build_selection_audit_trail(
    sat_id: str,
    batch_id: str,
    pipeline_version: str,
    decision_dicts: list[dict],
    limitations: list[str],
    created_at: str,
) -> SelectionAuditTrail:
    entries: list[DecisionEntry] = []
    for d in decision_dicts:
        entries.append(
            DecisionEntry(
                candidate_family_id=d["candidate_family_id"],
                decision=d["decision"],
                decision_stage=d["decision_stage"],
                rationale=d["rationale"],
                evidence_artifact_ids=sorted(d.get("evidence_artifact_ids", [])),
                decided_at=d.get("decided_at", ""),
            )
        )

    n_entries = len(entries)
    n_selected = sum(1 for e in entries if e.decision == "selected")
    n_rejected = sum(1 for e in entries if e.decision == "rejected")
    n_deferred = sum(1 for e in entries if e.decision == "deferred")
    final_shortlist_ids = sorted({e.candidate_family_id for e in entries if e.decision == "selected"})

    return SelectionAuditTrail(
        sat_id=sat_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        n_entries=n_entries,
        entries=entries,
        n_selected=n_selected,
        n_rejected=n_rejected,
        n_deferred=n_deferred,
        final_shortlist_ids=final_shortlist_ids,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )


def format_selection_audit_trail(trail: SelectionAuditTrail) -> str:
    lines = [
        f"Selection Audit Trail — {trail.sat_id}",
        f"Batch: {trail.batch_id}  |  Pipeline: {trail.pipeline_version}",
        f"Entries: {trail.n_entries}  |  Selected: {trail.n_selected}  |  "
        f"Rejected: {trail.n_rejected}  |  Deferred: {trail.n_deferred}",
        f"Final Shortlist ({len(trail.final_shortlist_ids)}): {', '.join(trail.final_shortlist_ids) or '(none)'}",
        f"Created: {trail.created_at}",
        f"Limitations: {'; '.join(trail.limitations)}",
        f"dry_lab_only: {trail.dry_lab_only}",
    ]
    return "\n".join(lines)

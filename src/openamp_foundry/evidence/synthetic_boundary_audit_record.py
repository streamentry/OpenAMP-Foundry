"""Synthetic boundary audit record schema — Phase G G8.

Documents each enforcement of the policy that synthetic/simulation results
cannot raise a candidate's proof-ladder level.

Proof-ladder levels:
  1 = computational nomination
  2 = virtual-assay support
  3 = in-silico ensemble agreement
  4 = ex-vivo preliminary         ← requires wet-lab evidence
  5 = in-vivo preliminary         ← requires wet-lab evidence
  6 = clinical evidence           ← requires wet-lab evidence

Synthetic results may maintain or, when combined with prior wet-lab evidence,
annotate a level — but they CANNOT raise it. Level 4+ is unreachable by
simulation alone.

This schema makes each enforcement event an auditable artifact.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

SBR_PREFIX = "SBR-"

PROOF_LADDER_MIN = 1
PROOF_LADDER_MAX = 3  # max level reachable via synthetic-only evidence
WET_LAB_REQUIRED_LEVEL = 4  # level ≥ 4 requires wet-lab evidence

VALID_EVIDENCE_SOURCES = frozenset({
    "synthetic",
    "simulation",
    "computational",
    "mixed_synthetic_lab",
})

VALID_ENFORCEMENT_OUTCOMES = frozenset({
    "all_passed",
    "violations_blocked",
    "violations_flagged",
})

VIOLATION_RATE_TOLERANCE = 0.01
HIGH_VIOLATION_RATE_WARNING = 0.3
SUMMARY_MAX_LENGTH = 400
NOTES_MAX_LENGTH = 300
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class SyntheticBoundaryAuditRecord:
    sbr_id: str
    pipeline_version: str
    batch_id: str
    audit_date: str
    evidence_source: str
    total_candidates_checked: int
    total_violations: int
    violation_rate: float
    blocked_upgrades: int
    max_proposed_ladder_level: int
    policy_enforced: bool
    enforcement_outcome: str
    summary: str
    notes: str = ""


def validate(record: SyntheticBoundaryAuditRecord) -> List[str]:
    """Return list of error strings; empty list means valid."""
    errors: List[str] = []

    # Rule 1: ID prefix
    if not record.sbr_id.startswith(SBR_PREFIX):
        errors.append(
            f"sbr_id must start with '{SBR_PREFIX}', got: {record.sbr_id!r}"
        )

    # Rule 2: pipeline_version non-empty
    if not record.pipeline_version.strip():
        errors.append("pipeline_version must not be empty")

    # Rule 3: batch_id non-empty
    if not record.batch_id.strip():
        errors.append("batch_id must not be empty")

    # Rule 4: audit_date ISO format
    if not _ISO_DATE_RE.match(record.audit_date):
        errors.append(
            f"audit_date must be YYYY-MM-DD, got: {record.audit_date!r}"
        )

    # Rule 5: evidence_source vocabulary
    if record.evidence_source not in VALID_EVIDENCE_SOURCES:
        errors.append(
            f"evidence_source must be one of {sorted(VALID_EVIDENCE_SOURCES)}, "
            f"got: {record.evidence_source!r}"
        )

    # Rule 6: total_candidates_checked >= 1
    if record.total_candidates_checked < 1:
        errors.append(
            f"total_candidates_checked must be >= 1, "
            f"got: {record.total_candidates_checked}"
        )

    # Rule 7: total_violations in [0, total_candidates_checked]
    if not (0 <= record.total_violations <= record.total_candidates_checked):
        errors.append(
            f"total_violations must be in [0, {record.total_candidates_checked}], "
            f"got: {record.total_violations}"
        )

    # Rule 8: violation_rate in [0.0, 1.0]
    if not (0.0 <= record.violation_rate <= 1.0):
        errors.append(
            f"violation_rate must be in [0.0, 1.0], got: {record.violation_rate}"
        )

    # Rule 9: violation_rate consistency (tolerance 0.01)
    if record.total_candidates_checked >= 1:
        computed = record.total_violations / record.total_candidates_checked
        if abs(computed - record.violation_rate) > VIOLATION_RATE_TOLERANCE:
            errors.append(
                f"violation_rate ({record.violation_rate:.4f}) inconsistent with "
                f"total_violations/total_candidates_checked "
                f"({record.total_violations}/{record.total_candidates_checked} "
                f"= {computed:.4f}); tolerance is {VIOLATION_RATE_TOLERANCE}"
            )

    # Rule 10: blocked_upgrades in [0, total_violations]
    if not (0 <= record.blocked_upgrades <= record.total_violations):
        errors.append(
            f"blocked_upgrades must be in [0, {record.total_violations}], "
            f"got: {record.blocked_upgrades}"
        )

    # Rule 11: max_proposed_ladder_level in [1, 6]
    if not (1 <= record.max_proposed_ladder_level <= 6):
        errors.append(
            f"max_proposed_ladder_level must be in [1, 6], "
            f"got: {record.max_proposed_ladder_level}"
        )

    # Rule 12: synthetic-only evidence cannot propose level >= 4
    if (
        record.evidence_source in ("synthetic", "simulation", "computational")
        and record.max_proposed_ladder_level >= WET_LAB_REQUIRED_LEVEL
        and record.total_violations == 0
    ):
        errors.append(
            f"evidence_source '{record.evidence_source}' cannot support "
            f"max_proposed_ladder_level {record.max_proposed_ladder_level} "
            f"(level {WET_LAB_REQUIRED_LEVEL}+ requires wet-lab evidence) "
            f"without any violations recorded"
        )

    # Rule 13: policy_enforced must be True
    if not record.policy_enforced:
        errors.append(
            "policy_enforced must be True — the synthetic boundary policy "
            "must be actively enforced; disable this check requires human review"
        )

    # Rule 14: enforcement_outcome vocabulary
    if record.enforcement_outcome not in VALID_ENFORCEMENT_OUTCOMES:
        errors.append(
            f"enforcement_outcome must be one of "
            f"{sorted(VALID_ENFORCEMENT_OUTCOMES)}, "
            f"got: {record.enforcement_outcome!r}"
        )

    # Rule 15: summary non-empty and length
    if not record.summary.strip():
        errors.append("summary must not be empty")
    elif len(record.summary) > SUMMARY_MAX_LENGTH:
        errors.append(
            f"summary exceeds {SUMMARY_MAX_LENGTH} chars "
            f"(got {len(record.summary)})"
        )

    # Rule 16: notes length
    if len(record.notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"notes exceeds {NOTES_MAX_LENGTH} chars (got {len(record.notes)})"
        )

    # Warnings
    if record.violation_rate > HIGH_VIOLATION_RATE_WARNING:
        errors.append(
            f"WARNING: violation_rate ({record.violation_rate:.2f}) > "
            f"{HIGH_VIOLATION_RATE_WARNING} — high overclaim attempt rate; "
            "review batch selection and scoring methodology"
        )
    if record.total_violations > 0 and record.blocked_upgrades < record.total_violations:
        errors.append(
            f"WARNING: {record.total_violations - record.blocked_upgrades} violations "
            "were flagged but not blocked — verify enforcement_outcome is correct"
        )
    if not record.notes.strip():
        errors.append(
            "WARNING: notes is empty — consider documenting enforcement context"
        )

    return errors


def validate_dict(data: dict) -> List[str]:
    """Validate a plain dict by constructing SyntheticBoundaryAuditRecord first."""
    try:
        record = SyntheticBoundaryAuditRecord(**data)
    except TypeError as exc:
        return [f"Schema construction error: {exc}"]
    return validate(record)

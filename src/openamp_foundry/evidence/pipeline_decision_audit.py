"""Pipeline decision audit entry schema (Phase M M1).

Records each significant decision made during candidate ranking,
filtering, or selection to support external audit of the pipeline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

VALID_DECISION_TYPES: set[str] = {
    "benchmark_updated",
    "calibration_adjusted",
    "candidate_ranked",
    "candidate_rejected",
    "filter_applied",
    "safety_flag_applied",
    "threshold_chosen",
}

VALID_EVIDENCE_LEVELS: set[int] = {1, 2, 3, 4, 5, 6}
MAX_DESCRIPTION_LENGTH: int = 500
MAX_RATIONALE_LENGTH: int = 1000

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class PipelineDecisionAuditEntry:
    """One pipeline decision audit record."""

    audit_id: str
    batch_id: str
    pipeline_version: str
    decision_date: str
    decision_type: str
    decision_description: str
    rationale: str
    alternatives_considered: List[str]
    affected_candidate_count: int
    evidence_level: int
    pre_specified: bool
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class PipelineDecisionAuditResult:
    """Validation result for a PipelineDecisionAuditEntry."""

    audit_id: str
    batch_id: str
    decision_type: str
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_pipeline_decision_audit(
    entry: PipelineDecisionAuditEntry,
) -> PipelineDecisionAuditResult:
    """Validate a PipelineDecisionAuditEntry.  Returns a PipelineDecisionAuditResult."""
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.audit_id.startswith("AUD-"):
        errors.append("audit_id must start with 'AUD-'")

    if not entry.batch_id:
        errors.append("batch_id must not be empty")

    if not entry.pipeline_version:
        errors.append("pipeline_version must not be empty")

    if not _DATE_RE.match(entry.decision_date):
        errors.append("decision_date must be YYYY-MM-DD")

    if entry.decision_type not in VALID_DECISION_TYPES:
        errors.append(
            f"decision_type '{entry.decision_type}' is not valid; "
            f"must be one of {sorted(VALID_DECISION_TYPES)}"
        )

    if not entry.decision_description:
        errors.append("decision_description must not be empty")
    elif len(entry.decision_description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            f"decision_description exceeds {MAX_DESCRIPTION_LENGTH} characters "
            f"({len(entry.decision_description)} chars)"
        )

    if not entry.rationale:
        errors.append("rationale must not be empty")
    elif len(entry.rationale) > MAX_RATIONALE_LENGTH:
        errors.append(
            f"rationale exceeds {MAX_RATIONALE_LENGTH} characters "
            f"({len(entry.rationale)} chars)"
        )

    if entry.affected_candidate_count < 0:
        errors.append("affected_candidate_count must be >= 0")

    if entry.evidence_level not in VALID_EVIDENCE_LEVELS:
        errors.append(
            f"evidence_level {entry.evidence_level} is not valid; "
            f"must be one of {sorted(VALID_EVIDENCE_LEVELS)}"
        )

    if not entry.reviewer:
        errors.append("reviewer must not be empty")

    if entry.dry_lab_only is not True:
        errors.append("dry_lab_only must be True")

    if not errors:
        if not entry.pre_specified:
            warnings.append(
                "pre_specified is False; this is a post-hoc decision. "
                "Document the justification carefully to avoid selection bias."
            )

        if not entry.alternatives_considered:
            warnings.append(
                "alternatives_considered is empty; consider recording what "
                "alternative thresholds or approaches were evaluated."
            )

        if entry.evidence_level <= 2:
            warnings.append(
                f"evidence_level {entry.evidence_level} is low (≤2); "
                "this decision rests on limited computational evidence."
            )

        if entry.affected_candidate_count == 0:
            warnings.append(
                "affected_candidate_count is 0; verify this decision "
                "actually affected no candidates."
            )

    return PipelineDecisionAuditResult(
        audit_id=entry.audit_id,
        batch_id=entry.batch_id,
        decision_type=entry.decision_type,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_pipeline_decision_audit_dict(d: dict) -> PipelineDecisionAuditResult:
    """Validate a dict representation of a PipelineDecisionAuditEntry."""
    required = [
        "audit_id",
        "batch_id",
        "pipeline_version",
        "decision_date",
        "decision_type",
        "decision_description",
        "rationale",
        "alternatives_considered",
        "affected_candidate_count",
        "evidence_level",
        "pre_specified",
        "reviewer",
    ]
    for key in required:
        if key not in d:
            return PipelineDecisionAuditResult(
                audit_id=d.get("audit_id", ""),
                batch_id=d.get("batch_id", ""),
                decision_type=d.get("decision_type", ""),
                passed=False,
                errors=[f"missing required field: {key}"],
                warnings=[],
            )

    entry = PipelineDecisionAuditEntry(
        audit_id=d["audit_id"],
        batch_id=d["batch_id"],
        pipeline_version=d["pipeline_version"],
        decision_date=d["decision_date"],
        decision_type=d["decision_type"],
        decision_description=d["decision_description"],
        rationale=d["rationale"],
        alternatives_considered=d["alternatives_considered"],
        affected_candidate_count=d["affected_candidate_count"],
        evidence_level=d["evidence_level"],
        pre_specified=d["pre_specified"],
        reviewer=d["reviewer"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_pipeline_decision_audit(entry)

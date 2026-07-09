from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

MINIMUM_SELECTION_CRITERIA: int = 2
MAXIMUM_SELECTION_CRITERIA_WARNING: int = 6
MAX_REJECTION_RATIONALE_LENGTH: int = 500
MAX_RESOURCE_CONSTRAINT_LENGTH: int = 200


@dataclass
class ExperimentPriorityEntry:
    justification_id: str
    batch_id: str
    pipeline_version: str
    decision_date: str
    selection_criteria: List[str]
    rejected_alternatives: List[str]
    rejection_rationale: str
    resource_constraint: str
    safety_reviewed: bool
    pre_specified: bool
    decided_by: str
    dry_lab_only: bool = True


@dataclass
class ExperimentPriorityResult:
    justification_id: str
    batch_id: str
    criteria_count: int
    rejected_alternative_count: int
    safety_reviewed: bool
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_experiment_priority(
    entry: ExperimentPriorityEntry,
) -> ExperimentPriorityResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.justification_id.startswith("EPJ-"):
        errors.append(
            f"justification_id must start with 'EPJ-', got '{entry.justification_id}'"
        )

    if len(entry.selection_criteria) < MINIMUM_SELECTION_CRITERIA:
        errors.append(
            f"selection_criteria must contain at least {MINIMUM_SELECTION_CRITERIA} criteria, "
            f"got {len(entry.selection_criteria)}"
        )

    if not entry.rejected_alternatives:
        errors.append(
            "rejected_alternatives must contain at least 1 alternative; "
            "selection without alternatives is not a decision"
        )

    if not entry.rejection_rationale:
        errors.append("rejection_rationale must not be empty")
    elif len(entry.rejection_rationale) > MAX_REJECTION_RATIONALE_LENGTH:
        errors.append(
            f"rejection_rationale exceeds {MAX_REJECTION_RATIONALE_LENGTH} characters "
            f"(got {len(entry.rejection_rationale)})"
        )

    if len(entry.resource_constraint) > MAX_RESOURCE_CONSTRAINT_LENGTH:
        errors.append(
            f"resource_constraint exceeds {MAX_RESOURCE_CONSTRAINT_LENGTH} characters "
            f"(got {len(entry.resource_constraint)})"
        )

    if not entry.safety_reviewed:
        errors.append(
            "safety_reviewed must be True; safety criteria must be checked "
            "before selecting candidates for experimental validation"
        )

    if not entry.decided_by:
        errors.append("decided_by must not be empty")

    if not entry.dry_lab_only:
        errors.append(
            "dry_lab_only must be True for experiment priority justifications "
            "(computational prioritization only)"
        )

    if not errors:
        if not entry.pre_specified:
            warnings.append(
                "pre_specified=False; selection criteria were not pre-specified before "
                "seeing candidates — post-hoc criteria selection introduces bias"
            )

        if len(entry.selection_criteria) == MINIMUM_SELECTION_CRITERIA:
            warnings.append(
                f"only {MINIMUM_SELECTION_CRITERIA} selection criteria used (minimum); "
                "more criteria strengthen selection defensibility"
            )

        if not entry.resource_constraint:
            warnings.append(
                "resource_constraint is empty; documenting capacity or resource "
                "constraints improves transparency of the prioritization decision"
            )

        if len(entry.selection_criteria) > MAXIMUM_SELECTION_CRITERIA_WARNING:
            warnings.append(
                f"{len(entry.selection_criteria)} selection criteria exceed "
                f"{MAXIMUM_SELECTION_CRITERIA_WARNING}; many criteria may over-fit "
                "to batch-specific characteristics"
            )

    passed = len(errors) == 0
    return ExperimentPriorityResult(
        justification_id=entry.justification_id,
        batch_id=entry.batch_id,
        criteria_count=len(entry.selection_criteria),
        rejected_alternative_count=len(entry.rejected_alternatives),
        safety_reviewed=entry.safety_reviewed,
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_experiment_priority_dict(d: dict) -> ExperimentPriorityResult:
    required_fields = [
        "justification_id",
        "batch_id",
        "pipeline_version",
        "decision_date",
        "selection_criteria",
        "rejected_alternatives",
        "rejection_rationale",
        "resource_constraint",
        "safety_reviewed",
        "pre_specified",
        "decided_by",
    ]
    missing = [f for f in required_fields if f not in d]
    if missing:
        return ExperimentPriorityResult(
            justification_id=d.get("justification_id", "UNKNOWN"),
            batch_id=d.get("batch_id", "UNKNOWN"),
            criteria_count=0,
            rejected_alternative_count=0,
            safety_reviewed=False,
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=True,
        )

    entry = ExperimentPriorityEntry(
        justification_id=d["justification_id"],
        batch_id=d["batch_id"],
        pipeline_version=d["pipeline_version"],
        decision_date=d["decision_date"],
        selection_criteria=list(d["selection_criteria"]),
        rejected_alternatives=list(d["rejected_alternatives"]),
        rejection_rationale=d["rejection_rationale"],
        resource_constraint=d["resource_constraint"],
        safety_reviewed=bool(d["safety_reviewed"]),
        pre_specified=bool(d["pre_specified"]),
        decided_by=d["decided_by"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_experiment_priority(entry)

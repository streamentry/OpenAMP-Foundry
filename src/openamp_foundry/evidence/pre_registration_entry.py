"""Pre-registration entry schema — Phase Q Q2.

Documents the experimental plan locked BEFORE wet-lab work begins.
A pre-registration enforces that hypothesis, primary endpoint, and
candidate list are committed before any results are observed — the
foundation of auditable, non-cherry-picked evidence.

An approved PRE entry is a prerequisite for a complete Pilot Evidence
Package (PEP). Rejected entries are preserved for audit trail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

PRE_PREFIX = "PRE-"
VALID_REGISTRATION_STATUSES = frozenset({"submitted", "approved", "rejected"})
NOTES_MAX_LENGTH = 400
MIN_CANDIDATES = 1


@dataclass
class PreRegistrationEntry:
    """Pre-committed experimental plan for a pilot batch."""

    pre_id: str
    pipeline_version: str
    experiment_title: str
    hypothesis: str
    primary_endpoint: str
    candidate_ids: List[str]
    positive_control_id: Optional[str]
    negative_control_id: Optional[str]
    registered_date: str
    registration_status: str
    registrar: str
    notes: str
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class PreRegistrationResult:
    pre_id: str
    pipeline_version: str
    experiment_title: str
    registration_status: str
    candidate_count: int
    has_positive_control: bool
    has_negative_control: bool
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_pre_registration_entry(
    entry: PreRegistrationEntry,
) -> PreRegistrationResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.pre_id.startswith(PRE_PREFIX):
        errors.append(
            f"pre_id must start with '{PRE_PREFIX}', got '{entry.pre_id}'"
        )

    if not entry.pipeline_version:
        errors.append("pipeline_version must not be empty")

    if not entry.experiment_title:
        errors.append("experiment_title must not be empty")

    if not entry.hypothesis:
        errors.append("hypothesis must not be empty")

    if not entry.primary_endpoint:
        errors.append("primary_endpoint must not be empty")

    if len(entry.candidate_ids) < MIN_CANDIDATES:
        errors.append(
            f"candidate_ids must contain at least {MIN_CANDIDATES} entry, "
            f"got {len(entry.candidate_ids)}"
        )

    # registered_date must be ISO format YYYY-MM-DD
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", entry.registered_date):
        errors.append(
            f"registered_date must be ISO format YYYY-MM-DD, "
            f"got '{entry.registered_date}'"
        )

    if entry.registration_status not in VALID_REGISTRATION_STATUSES:
        errors.append(
            f"registration_status must be one of "
            f"{sorted(VALID_REGISTRATION_STATUSES)}, "
            f"got '{entry.registration_status}'"
        )

    if not entry.registrar:
        errors.append("registrar must not be empty")

    if len(entry.notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"notes exceeds {NOTES_MAX_LENGTH} characters "
            f"(got {len(entry.notes)})"
        )

    # Warnings
    if entry.registration_status == "approved" and entry.dry_lab_only:
        warnings.append(
            "registration_status=approved with dry_lab_only=True — "
            "an approved pre-registration implies wet-lab work is planned; "
            "confirm dry_lab_only reflects the actual experiment type"
        )

    if not entry.positive_control_id and not errors:
        warnings.append(
            "no positive_control_id — experiments without a positive control "
            "reduce interpretability of results"
        )

    if not entry.negative_control_id and not errors:
        warnings.append(
            "no negative_control_id — experiments without a negative control "
            "reduce interpretability of results"
        )

    if len(entry.candidate_ids) == 1 and not errors:
        warnings.append(
            "candidate_ids contains only 1 entry — a single-candidate "
            "experiment provides limited statistical power"
        )

    has_positive_control = entry.positive_control_id is not None and entry.positive_control_id != ""
    has_negative_control = entry.negative_control_id is not None and entry.negative_control_id != ""

    return PreRegistrationResult(
        pre_id=entry.pre_id,
        pipeline_version=entry.pipeline_version,
        experiment_title=entry.experiment_title,
        registration_status=entry.registration_status,
        candidate_count=len(entry.candidate_ids),
        has_positive_control=has_positive_control,
        has_negative_control=has_negative_control,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_pre_registration_entry_dict(d: dict) -> PreRegistrationResult:
    missing = []
    for k in (
        "pre_id",
        "pipeline_version",
        "experiment_title",
        "hypothesis",
        "primary_endpoint",
        "candidate_ids",
        "registered_date",
        "registration_status",
        "registrar",
        "notes",
        "reviewer",
    ):
        if k not in d:
            missing.append(k)
    if missing:
        return PreRegistrationResult(
            pre_id=d.get("pre_id", ""),
            pipeline_version=d.get("pipeline_version", ""),
            experiment_title=d.get("experiment_title", ""),
            registration_status=d.get("registration_status", ""),
            candidate_count=0,
            has_positive_control=False,
            has_negative_control=False,
            passed=False,
            errors=[f"missing required fields: {missing}"],
            warnings=[],
            dry_lab_only=d.get("dry_lab_only", True),
        )
    entry = PreRegistrationEntry(
        pre_id=d["pre_id"],
        pipeline_version=d["pipeline_version"],
        experiment_title=d["experiment_title"],
        hypothesis=d["hypothesis"],
        primary_endpoint=d["primary_endpoint"],
        candidate_ids=list(d["candidate_ids"]),
        positive_control_id=d.get("positive_control_id"),
        negative_control_id=d.get("negative_control_id"),
        registered_date=d["registered_date"],
        registration_status=d["registration_status"],
        registrar=d["registrar"],
        notes=d["notes"],
        reviewer=d["reviewer"],
        dry_lab_only=bool(d.get("dry_lab_only", True)),
    )
    return validate_pre_registration_entry(entry)

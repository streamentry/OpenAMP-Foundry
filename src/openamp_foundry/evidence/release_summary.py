"""RSM- release-summary schema and generator.

Produces a public-safe summary of what was released by stripping restricted
fields before any external distribution.  Every external share of pipeline
outputs must go through this generator — no ad-hoc field omission.

Restricted fields list what must NOT appear in public summaries:
individual candidate IDs, internal batch references, rejection reasons,
raw sequence data, reviewer identities, and internal restriction text.

Makes the stripping step machine-checkable rather than relying on human
memory of what is sensitive.
"""

from __future__ import annotations

from dataclasses import dataclass

RESTRICTED_FIELDS: tuple[str, ...] = (
    "erp_id",
    "rejection_reason",
    "restrictions",
    "candidate_ids",
    "reviewer_ids",
    "raw_sequences",
    "batch_ids",
    "internal_notes",
    "collaborator_names",
)

VALID_RSM_RELEASE_SCOPES: frozenset[str] = frozenset({
    "academic_collaboration",
    "public_preprint",
    "internal_only",
    "restricted_partner",
})

VALID_RSM_DECISIONS: frozenset[str] = frozenset({
    "authorized",
    "rejected",
    "pending_review",
})


@dataclass
class ReleaseSummary:
    rsm_id: str
    srd_id: str
    pipeline_version: str
    release_scope: str
    release_decision: str
    candidate_count: int
    safety_checks_summary: list[str]
    public_notes: str
    limitations_summary: str
    restricted_fields_stripped: bool
    dry_lab_only: bool
    created_at: str


def validate_release_summary(rsm: ReleaseSummary) -> None:
    if not rsm.rsm_id.startswith("RSM-"):
        raise ValueError(f"rsm_id must start with 'RSM-': {rsm.rsm_id!r}")
    if not rsm.srd_id.startswith("SRD-"):
        raise ValueError(f"srd_id must start with 'SRD-': {rsm.srd_id!r}")
    if not rsm.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if rsm.release_scope not in VALID_RSM_RELEASE_SCOPES:
        raise ValueError(
            f"release_scope {rsm.release_scope!r} not in VALID_RSM_RELEASE_SCOPES"
        )
    if rsm.release_decision not in VALID_RSM_DECISIONS:
        raise ValueError(
            f"release_decision {rsm.release_decision!r} not in VALID_RSM_DECISIONS"
        )
    if rsm.candidate_count < 0:
        raise ValueError("candidate_count must be non-negative")
    if not rsm.restricted_fields_stripped:
        raise ValueError("restricted_fields_stripped must be True")
    if not rsm.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not rsm.limitations_summary:
        raise ValueError("limitations_summary must be non-empty")
    if not rsm.created_at:
        raise ValueError("created_at must be non-empty")


def build_release_summary(
    *,
    rsm_id: str,
    srd_id: str,
    pipeline_version: str,
    release_scope: str,
    release_decision: str,
    candidate_count: int,
    safety_checks_summary: list[str],
    public_notes: str = "",
    limitations_summary: str,
    created_at: str,
) -> ReleaseSummary:
    """Build a ReleaseSummary with restricted_fields_stripped and dry_lab_only always True."""
    rsm = ReleaseSummary(
        rsm_id=rsm_id,
        srd_id=srd_id,
        pipeline_version=pipeline_version,
        release_scope=release_scope,
        release_decision=release_decision,
        candidate_count=candidate_count,
        safety_checks_summary=list(safety_checks_summary),
        public_notes=public_notes,
        limitations_summary=limitations_summary,
        restricted_fields_stripped=True,
        dry_lab_only=True,
        created_at=created_at,
    )
    validate_release_summary(rsm)
    return rsm


def strip_restricted_fields(source: dict) -> dict:
    """Return a copy of *source* with all RESTRICTED_FIELDS removed."""
    return {k: v for k, v in source.items() if k not in RESTRICTED_FIELDS}


def generate_release_summary(
    *,
    rsm_id: str,
    srd_id: str,
    pipeline_version: str,
    release_scope: str,
    release_decision: str,
    candidate_count: int,
    safety_checks_summary: list[str],
    limitations_summary: str,
    public_notes: str = "",
    created_at: str,
    source_fields: dict | None = None,
) -> ReleaseSummary:
    """Generate a public-safe ReleaseSummary, stripping any restricted fields
    found in *source_fields* before building.

    *source_fields* is optional raw data that will be validated for absence of
    restricted fields — raising ValueError if any restricted key is present.
    This makes accidental leakage detectable at generation time.
    """
    if source_fields is not None:
        leaked = [k for k in RESTRICTED_FIELDS if k in source_fields]
        if leaked:
            raise ValueError(
                f"Restricted fields present in source_fields, must be stripped first: {leaked}"
            )
    return build_release_summary(
        rsm_id=rsm_id,
        srd_id=srd_id,
        pipeline_version=pipeline_version,
        release_scope=release_scope,
        release_decision=release_decision,
        candidate_count=candidate_count,
        safety_checks_summary=safety_checks_summary,
        public_notes=public_notes,
        limitations_summary=limitations_summary,
        created_at=created_at,
    )


def format_release_summary(rsm: ReleaseSummary) -> str:
    lines = [
        f"Release Summary — {rsm.rsm_id}",
        f"Authorization: {rsm.srd_id}  |  Pipeline: {rsm.pipeline_version}",
        f"Decision: {rsm.release_decision}  |  Scope: {rsm.release_scope}",
        f"Candidates in summary: {rsm.candidate_count}",
        f"Restricted fields stripped: {rsm.restricted_fields_stripped}",
    ]
    if rsm.safety_checks_summary:
        lines.append(f"Safety checks: {'; '.join(rsm.safety_checks_summary)}")
    if rsm.public_notes:
        lines.append(f"Notes: {rsm.public_notes}")
    lines.append(f"Limitations: {rsm.limitations_summary}")
    lines.append(f"Created: {rsm.created_at}")
    lines.append(f"dry_lab_only: {rsm.dry_lab_only}")
    return "\n".join(lines)

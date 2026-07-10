"""Cross-repo evidence traceability schema for multi-lab reproducibility."""

from __future__ import annotations

from dataclasses import dataclass, field

CROSS_REPO_TRACEABILITY_ID_PREFIX = "CRT-"

VALID_REPO_TYPES: frozenset = frozenset(
    {
        "primary",
        "fork",
        "mirror",
        "partner_lab",
        "independent_replication",
        "downstream_consumer",
    }
)

VALID_ARTIFACT_TYPES: frozenset = frozenset(
    {
        "evidence_certificate",
        "release_manifest",
        "benchmark_card",
        "negative_result_record",
        "batch_outcome_summary",
        "fasta_export",
        "calibration_cycle_summary",
        "external_review_packet",
    }
)

VALID_TRACEABILITY_STATUSES: frozenset = frozenset(
    {"pending", "linked", "verified", "broken", "superseded"}
)

VALID_LINK_CONFIDENCE_LEVELS: frozenset = frozenset(
    {"high", "medium", "low", "unverified"}
)

CANONICAL_REPO_URL = "https://github.com/Open-Problem-Lab/OpenAMP-Foundry"


@dataclass
class CrossRepoArtifactRef:
    artifact_id: str
    artifact_type: str
    source_repo_url: str
    source_repo_type: str
    commit_sha: str
    confidence_level: str
    is_verified: bool = False
    verification_note: str = ""


@dataclass
class CrossRepoTraceabilityRecord:
    record_id: str
    primary_artifact_id: str
    primary_artifact_type: str
    external_refs: list = field(default_factory=list)
    total_external_repos: int = 0
    traceability_status: str = "pending"
    dry_lab_only: bool = True
    is_example_data: bool = True
    traceability_note: str = ""


@dataclass
class TraceabilityValidationResult:
    is_valid: bool
    violations: list = field(default_factory=list)


def build_cross_repo_artifact_ref(
    artifact_id: str,
    artifact_type: str,
    source_repo_url: str,
    source_repo_type: str,
    commit_sha: str,
    confidence_level: str,
    is_verified: bool = False,
    verification_note: str = "",
) -> CrossRepoArtifactRef:
    return CrossRepoArtifactRef(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        source_repo_url=source_repo_url,
        source_repo_type=source_repo_type,
        commit_sha=commit_sha,
        confidence_level=confidence_level,
        is_verified=is_verified,
        verification_note=verification_note,
    )


def build_cross_repo_traceability_record(
    record_id: str,
    primary_artifact_id: str,
    primary_artifact_type: str,
    external_refs: list,
    traceability_status: str,
    dry_lab_only: bool = True,
    is_example_data: bool = True,
    traceability_note: str = "",
) -> CrossRepoTraceabilityRecord:
    return CrossRepoTraceabilityRecord(
        record_id=record_id,
        primary_artifact_id=primary_artifact_id,
        primary_artifact_type=primary_artifact_type,
        external_refs=list(external_refs),
        total_external_repos=len(external_refs),
        traceability_status=traceability_status,
        dry_lab_only=dry_lab_only,
        is_example_data=is_example_data,
        traceability_note=traceability_note or f"CRT record for {primary_artifact_id}",
    )


def validate_cross_repo_traceability_record(
    record: CrossRepoTraceabilityRecord,
) -> TraceabilityValidationResult:
    violations: list[str] = []

    if not record.record_id.startswith(CROSS_REPO_TRACEABILITY_ID_PREFIX):
        violations.append(
            f"record_id must start with '{CROSS_REPO_TRACEABILITY_ID_PREFIX}', "
            f"got '{record.record_id}'"
        )

    if not record.primary_artifact_id:
        violations.append("primary_artifact_id must not be empty")

    if record.primary_artifact_type not in VALID_ARTIFACT_TYPES:
        violations.append(
            f"primary_artifact_type '{record.primary_artifact_type}' "
            f"not in VALID_ARTIFACT_TYPES"
        )

    if record.traceability_status not in VALID_TRACEABILITY_STATUSES:
        violations.append(
            f"traceability_status '{record.traceability_status}' "
            f"not in VALID_TRACEABILITY_STATUSES"
        )

    if record.total_external_repos != len(record.external_refs):
        violations.append(
            f"total_external_repos={record.total_external_repos} does not match "
            f"len(external_refs)={len(record.external_refs)}"
        )

    if not record.dry_lab_only:
        violations.append(
            "dry_lab_only must be True; wet-lab traceability records require human review"
        )

    if not record.traceability_note:
        violations.append("traceability_note must not be empty")

    for i, ref in enumerate(record.external_refs):
        pfx = f"external_refs[{i}]"

        if not ref.artifact_id:
            violations.append(f"{pfx}: artifact_id must not be empty")

        if ref.artifact_type not in VALID_ARTIFACT_TYPES:
            violations.append(
                f"{pfx}: artifact_type '{ref.artifact_type}' not in VALID_ARTIFACT_TYPES"
            )

        if not ref.source_repo_url.startswith("https://"):
            violations.append(
                f"{pfx}: source_repo_url must start with 'https://', "
                f"got '{ref.source_repo_url}'"
            )

        if ref.source_repo_type not in VALID_REPO_TYPES:
            violations.append(
                f"{pfx}: source_repo_type '{ref.source_repo_type}' not in VALID_REPO_TYPES"
            )

        if not ref.commit_sha:
            violations.append(f"{pfx}: commit_sha must not be empty")

        if ref.confidence_level not in VALID_LINK_CONFIDENCE_LEVELS:
            violations.append(
                f"{pfx}: confidence_level '{ref.confidence_level}' "
                f"not in VALID_LINK_CONFIDENCE_LEVELS"
            )

    return TraceabilityValidationResult(
        is_valid=len(violations) == 0,
        violations=violations,
    )


def format_cross_repo_traceability_record(record: CrossRepoTraceabilityRecord) -> str:
    lines: list[str] = []
    lines.append(f"Cross-Repo Traceability Record ({record.record_id})")
    lines.append(f"  Primary artifact: {record.primary_artifact_id} [{record.primary_artifact_type}]")
    lines.append(f"  Status: {record.traceability_status}")
    lines.append(f"  Dry-lab only: {record.dry_lab_only}")
    lines.append(f"  Total external repos: {record.total_external_repos}")
    lines.append(f"  Note: {record.traceability_note}")
    if record.external_refs:
        lines.append("  External references:")
        for ref in record.external_refs:
            verified = "✓" if ref.is_verified else "?"
            lines.append(
                f"    [{verified}] {ref.artifact_id} ({ref.artifact_type}) "
                f"@ {ref.source_repo_url} "
                f"[{ref.source_repo_type}] confidence={ref.confidence_level}"
            )
    return "\n".join(lines) + "\n"

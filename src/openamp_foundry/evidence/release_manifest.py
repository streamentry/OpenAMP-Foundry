"""
Machine-readable release manifest schema.

I8: Downstream tools can parse what was released.
Records what candidate IDs, evidence certificates, benchmark cards,
and schema versions were included in a named release to external reviewers.
Release manifests use the RMF- prefix and are dry-lab-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

RELEASE_MANIFEST_ID_PREFIX: str = "RMF-"
DRY_LAB_ONLY_REQUIRED: bool = True
MIN_CANDIDATE_IDS: int = 1
MIN_SCHEMA_VERSION_LENGTH: int = 3

VALID_RELEASE_STATUSES: frozenset[str] = frozenset({
    "draft",
    "under_review",
    "approved",
    "released",
    "retracted",
})


@dataclass
class ReleaseManifest:
    """
    Machine-readable record of what was included in a named candidate release.

    Every field is present so downstream tools can verify receipt and
    reconstruct exactly what was shared with an external reviewer.
    """

    manifest_id: str
    release_name: str
    generated_at: str
    pipeline_version: str
    git_sha: str
    schema_version: str
    candidate_ids: list[str]
    evidence_certificate_ids: list[str]
    benchmark_card_ids: list[str]
    is_dry_lab_only: bool
    total_candidates: int
    contact: str
    release_status: str
    notes: str


@dataclass
class ManifestValidationResult:
    """Result of validating a ReleaseManifest."""

    is_valid: bool
    violations: list[str]
    warnings: list[str]
    manifest_id: str
    validation_summary: str


def validate_release_manifest(manifest: ReleaseManifest) -> ManifestValidationResult:
    """
    Validate a ReleaseManifest against all integrity rules.

    Rules:
      1. manifest_id must start with 'RMF-'
      2. manifest_id must not be empty beyond the prefix
      3. release_name must not be empty
      4. generated_at must not be empty
      5. pipeline_version must not be empty
      6. git_sha must not be empty
      7. schema_version must be at least MIN_SCHEMA_VERSION_LENGTH characters
      8. candidate_ids must have at least MIN_CANDIDATE_IDS entries
      9. total_candidates must equal len(candidate_ids)
      10. is_dry_lab_only must be True
      11. contact must not be empty
      12. release_status must be in VALID_RELEASE_STATUSES
      13. candidate_ids must contain no duplicates
      14. evidence_certificate_ids must contain no duplicates
    """
    violations: list[str] = []
    warnings: list[str] = []

    if not manifest.manifest_id.startswith(RELEASE_MANIFEST_ID_PREFIX):
        violations.append(
            f"manifest_id must start with '{RELEASE_MANIFEST_ID_PREFIX}', "
            f"got: {manifest.manifest_id!r}"
        )

    if len(manifest.manifest_id) <= len(RELEASE_MANIFEST_ID_PREFIX):
        violations.append(
            "manifest_id must have content after the prefix."
        )

    if not manifest.release_name.strip():
        violations.append("release_name must not be empty.")

    if not manifest.generated_at.strip():
        violations.append("generated_at must not be empty.")

    if not manifest.pipeline_version.strip():
        violations.append("pipeline_version must not be empty.")

    if not manifest.git_sha.strip():
        violations.append("git_sha must not be empty.")

    if len(manifest.schema_version.strip()) < MIN_SCHEMA_VERSION_LENGTH:
        violations.append(
            f"schema_version must be at least {MIN_SCHEMA_VERSION_LENGTH} characters, "
            f"got: {manifest.schema_version!r}"
        )

    if len(manifest.candidate_ids) < MIN_CANDIDATE_IDS:
        violations.append(
            f"candidate_ids must have at least {MIN_CANDIDATE_IDS} entry, "
            f"got {len(manifest.candidate_ids)}."
        )

    if manifest.total_candidates != len(manifest.candidate_ids):
        violations.append(
            f"total_candidates ({manifest.total_candidates}) must equal "
            f"len(candidate_ids) ({len(manifest.candidate_ids)})."
        )

    if not manifest.is_dry_lab_only:
        violations.append(
            "is_dry_lab_only must be True. Release manifests are dry-lab artifacts only."
        )

    if not manifest.contact.strip():
        violations.append("contact must not be empty.")

    if manifest.release_status not in VALID_RELEASE_STATUSES:
        violations.append(
            f"release_status must be one of {sorted(VALID_RELEASE_STATUSES)}, "
            f"got: {manifest.release_status!r}"
        )

    if len(manifest.candidate_ids) != len(set(manifest.candidate_ids)):
        violations.append("candidate_ids must not contain duplicates.")

    if len(manifest.evidence_certificate_ids) != len(set(manifest.evidence_certificate_ids)):
        violations.append("evidence_certificate_ids must not contain duplicates.")

    if not manifest.evidence_certificate_ids:
        warnings.append(
            "evidence_certificate_ids is empty. Consider linking certificates for auditability."
        )

    if not manifest.benchmark_card_ids:
        warnings.append(
            "benchmark_card_ids is empty. Consider linking BMC- cards for transparency."
        )

    is_valid = len(violations) == 0
    if is_valid:
        summary = (
            f"ReleaseManifest {manifest.manifest_id} is valid: "
            f"{manifest.total_candidates} candidate(s), "
            f"status={manifest.release_status}."
        )
    else:
        summary = (
            f"ReleaseManifest {manifest.manifest_id} has {len(violations)} violation(s): "
            + "; ".join(violations[:2])
            + ("..." if len(violations) > 2 else "")
        )

    return ManifestValidationResult(
        is_valid=is_valid,
        violations=violations,
        warnings=warnings,
        manifest_id=manifest.manifest_id,
        validation_summary=summary,
    )


def format_release_manifest(manifest: ReleaseManifest) -> str:
    """Return a human-readable summary of a ReleaseManifest."""
    lines: list[str] = [
        f"Release Manifest: {manifest.manifest_id}",
        f"  Release name:     {manifest.release_name}",
        f"  Status:           {manifest.release_status}",
        f"  Generated at:     {manifest.generated_at}",
        f"  Pipeline version: {manifest.pipeline_version}",
        f"  Git SHA:          {manifest.git_sha}",
        f"  Schema version:   {manifest.schema_version}",
        f"  Dry-lab only:     {manifest.is_dry_lab_only}",
        f"  Candidates ({manifest.total_candidates}):",
    ]
    for cid in manifest.candidate_ids:
        lines.append(f"    - {cid}")
    if manifest.evidence_certificate_ids:
        lines.append(f"  Evidence certificates ({len(manifest.evidence_certificate_ids)}):")
        for eid in manifest.evidence_certificate_ids:
            lines.append(f"    - {eid}")
    if manifest.benchmark_card_ids:
        lines.append(f"  Benchmark cards ({len(manifest.benchmark_card_ids)}):")
        for bid in manifest.benchmark_card_ids:
            lines.append(f"    - {bid}")
    lines.append(f"  Contact:          {manifest.contact}")
    if manifest.notes:
        lines.append(f"  Notes:            {manifest.notes}")
    return "\n".join(lines)

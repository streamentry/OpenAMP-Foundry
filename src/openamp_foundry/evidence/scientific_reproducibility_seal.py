"""SRS- scientific reproducibility seal schema.

Immutable record asserting that a batch's evidence trail is complete and
auditable. Includes pipeline version, schema hash placeholder, and
human-reviewed flag. Enables preprint data availability statements.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_SEAL_STATUSES: frozenset[str] = frozenset({
    "sealed", "provisional", "invalidated",
})

VALID_REVIEW_LEVELS: frozenset[str] = frozenset({
    "human_reviewed", "automated_only", "not_reviewed",
})

MIN_PIPELINE_VERSION_LENGTH: int = 2
SCHEMA_HASH_PLACEHOLDER: str = "PENDING"


@dataclass
class ScientificReproducibilitySeal:
    srs_id: str
    batch_id: str
    pipeline_version: str
    ebm_id: str
    prg_id: str
    schema_hash: str
    seal_status: str
    review_level: str
    human_reviewed: bool
    sealed_at: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_scientific_reproducibility_seal(srs: ScientificReproducibilitySeal) -> None:
    if not srs.srs_id.startswith("SRS-"):
        raise ValueError(f"srs_id must start with 'SRS-': {srs.srs_id!r}")
    if not srs.batch_id:
        raise ValueError("batch_id must be non-empty")
    if len(srs.pipeline_version) < MIN_PIPELINE_VERSION_LENGTH:
        raise ValueError(
            f"pipeline_version must be at least {MIN_PIPELINE_VERSION_LENGTH} chars"
        )
    if not srs.ebm_id.startswith("EBM-"):
        raise ValueError(f"ebm_id must start with 'EBM-': {srs.ebm_id!r}")
    if not srs.prg_id.startswith("PRG-"):
        raise ValueError(f"prg_id must start with 'PRG-': {srs.prg_id!r}")
    if not srs.schema_hash:
        raise ValueError("schema_hash must be non-empty")
    if srs.seal_status not in VALID_SEAL_STATUSES:
        raise ValueError(
            f"seal_status {srs.seal_status!r} not in VALID_SEAL_STATUSES"
        )
    if srs.review_level not in VALID_REVIEW_LEVELS:
        raise ValueError(
            f"review_level {srs.review_level!r} not in VALID_REVIEW_LEVELS"
        )
    if srs.review_level == "human_reviewed" and not srs.human_reviewed:
        raise ValueError(
            "human_reviewed must be True when review_level='human_reviewed'"
        )
    if srs.seal_status == "sealed" and srs.review_level == "not_reviewed":
        raise ValueError(
            "seal_status='sealed' requires review_level != 'not_reviewed'"
        )
    if not srs.sealed_at:
        raise ValueError("sealed_at must be non-empty")
    if not srs.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not srs.limitations:
        raise ValueError("limitations must be non-empty")
    if not srs.created_at:
        raise ValueError("created_at must be non-empty")


def build_scientific_reproducibility_seal(
    *,
    srs_id: str,
    batch_id: str,
    pipeline_version: str,
    ebm_id: str,
    prg_id: str,
    schema_hash: str = SCHEMA_HASH_PLACEHOLDER,
    seal_status: str,
    review_level: str,
    human_reviewed: bool,
    sealed_at: str,
    limitations: list[str],
    created_at: str,
) -> ScientificReproducibilitySeal:
    srs = ScientificReproducibilitySeal(
        srs_id=srs_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        ebm_id=ebm_id,
        prg_id=prg_id,
        schema_hash=schema_hash,
        seal_status=seal_status,
        review_level=review_level,
        human_reviewed=human_reviewed,
        sealed_at=sealed_at,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_scientific_reproducibility_seal(srs)
    return srs


def format_scientific_reproducibility_seal(srs: ScientificReproducibilitySeal) -> str:
    lines = [
        f"Scientific Reproducibility Seal — {srs.srs_id}",
        f"Batch: {srs.batch_id}  |  Pipeline: {srs.pipeline_version}",
        f"Status: {srs.seal_status}  |  Review: {srs.review_level}",
        f"Human reviewed: {srs.human_reviewed}",
        f"EBM: {srs.ebm_id}  |  PRG: {srs.prg_id}",
        f"Schema hash: {srs.schema_hash}",
        f"Sealed at: {srs.sealed_at}",
        f"Created: {srs.created_at}",
        f"Limitations: {'; '.join(srs.limitations)}",
        f"dry_lab_only: {srs.dry_lab_only}",
    ]
    return "\n".join(lines)

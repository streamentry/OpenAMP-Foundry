"""EBM- evidence bundle manifest schema.

Portable listing of all evidence artifact IDs and schema types for a batch.
Enables reproducibility checks and external handoff; machine-readable index
a scientist can use to request any artifact.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_MANIFEST_SCHEMA_TYPES: frozenset[str] = frozenset({
    "BSP", "PSC", "BOS", "CPS", "CBA", "CRG",
    "RSR", "PQT", "BTI", "CBA2", "BEG", "SAT", "PCC",
    "FET", "BRC", "CSV", "PTR", "ECI", "PRG",
})

VALID_MANIFEST_STATUSES: frozenset[str] = frozenset({
    "complete", "partial", "empty",
})


@dataclass
class ManifestEntry:
    schema_type: str
    artifact_id: str
    description: str


@dataclass
class EvidenceBundleManifest:
    ebm_id: str
    batch_id: str
    pipeline_version: str
    entries: list[ManifestEntry]
    n_entries: int
    schema_types_included: list[str]
    manifest_status: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def _compute_status(n_entries: int) -> str:
    if n_entries == 0:
        return "empty"
    n_required = len(VALID_MANIFEST_SCHEMA_TYPES)
    if n_entries >= n_required:
        return "complete"
    return "partial"


def validate_evidence_bundle_manifest(ebm: EvidenceBundleManifest) -> None:
    if not ebm.ebm_id.startswith("EBM-"):
        raise ValueError(f"ebm_id must start with 'EBM-': {ebm.ebm_id!r}")
    if not ebm.batch_id:
        raise ValueError("batch_id must be non-empty")
    if not ebm.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    for entry in ebm.entries:
        if entry.schema_type not in VALID_MANIFEST_SCHEMA_TYPES:
            raise ValueError(
                f"schema_type {entry.schema_type!r} not in VALID_MANIFEST_SCHEMA_TYPES"
            )
        if not entry.artifact_id:
            raise ValueError(
                f"artifact_id must be non-empty for schema_type {entry.schema_type!r}"
            )
    if ebm.manifest_status not in VALID_MANIFEST_STATUSES:
        raise ValueError(
            f"manifest_status {ebm.manifest_status!r} not in VALID_MANIFEST_STATUSES"
        )
    if not ebm.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not ebm.limitations:
        raise ValueError("limitations must be non-empty")
    if not ebm.created_at:
        raise ValueError("created_at must be non-empty")
    if ebm.n_entries != len(ebm.entries):
        raise ValueError("n_entries must equal len(entries)")
    expected_types = sorted({e.schema_type for e in ebm.entries})
    if ebm.schema_types_included != expected_types:
        raise ValueError("schema_types_included mismatch")


def build_evidence_bundle_manifest(
    *,
    ebm_id: str,
    batch_id: str,
    pipeline_version: str,
    entry_dicts: list[dict],
    limitations: list[str],
    created_at: str,
) -> EvidenceBundleManifest:
    """Build an evidence bundle manifest.

    entry_dicts: list of dicts with keys: schema_type, artifact_id, description.
    """
    entries = [
        ManifestEntry(
            schema_type=d["schema_type"],
            artifact_id=d["artifact_id"],
            description=d.get("description", ""),
        )
        for d in entry_dicts
    ]
    schema_types = sorted({e.schema_type for e in entries})
    status = _compute_status(len(schema_types))

    ebm = EvidenceBundleManifest(
        ebm_id=ebm_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        entries=entries,
        n_entries=len(entries),
        schema_types_included=schema_types,
        manifest_status=status,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_evidence_bundle_manifest(ebm)
    return ebm


def format_evidence_bundle_manifest(ebm: EvidenceBundleManifest) -> str:
    lines = [
        f"Evidence Bundle Manifest — {ebm.ebm_id}",
        f"Batch: {ebm.batch_id}  |  Pipeline: {ebm.pipeline_version}",
        f"Status: {ebm.manifest_status}  |  Entries: {ebm.n_entries}",
        f"Schema types: {', '.join(ebm.schema_types_included)}",
    ]
    if ebm.entries:
        lines.append("Artifacts:")
        for entry in ebm.entries:
            desc = f" — {entry.description}" if entry.description else ""
            lines.append(f"  {entry.schema_type}: {entry.artifact_id}{desc}")
    lines.append(f"Created: {ebm.created_at}")
    lines.append(f"Limitations: {'; '.join(ebm.limitations)}")
    lines.append(f"dry_lab_only: {ebm.dry_lab_only}")
    return "\n".join(lines)

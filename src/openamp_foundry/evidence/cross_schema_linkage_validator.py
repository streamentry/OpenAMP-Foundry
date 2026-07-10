"""CSV- cross-schema linkage validator schema.

Validates that artifact IDs referenced in SAT evidence_artifact_ids, BEG
missing lists, and BTI entries are internally consistent. Catches orphaned
references before external sharing.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_LINKAGE_VERDICTS: frozenset[str] = frozenset({
    "all_valid", "orphans_found", "no_references",
})

VALID_REFERENCE_SOURCES: frozenset[str] = frozenset({
    "SAT", "BEG", "BTI",
})


@dataclass
class OrphanEntry:
    artifact_id: str
    reference_source: str
    details: str


@dataclass
class CrossSchemaLinkageValidator:
    csv_id: str
    batch_id: str
    pipeline_version: str
    sat_id: str
    beg_id: str
    bti_id: str
    all_known_artifact_ids: list[str]
    referenced_artifact_ids: list[str]
    orphan_entries: list[OrphanEntry]
    n_references_checked: int
    n_orphans_found: int
    linkage_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def _compute_verdict(n_refs: int, n_orphans: int) -> str:
    if n_refs == 0:
        return "no_references"
    if n_orphans > 0:
        return "orphans_found"
    return "all_valid"


def validate_cross_schema_linkage_validator(csv: CrossSchemaLinkageValidator) -> None:
    if not csv.csv_id.startswith("CSV-"):
        raise ValueError(f"csv_id must start with 'CSV-': {csv.csv_id!r}")
    if not csv.batch_id:
        raise ValueError("batch_id must be non-empty")
    if not csv.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if not csv.sat_id.startswith("SAT-"):
        raise ValueError(f"sat_id must start with 'SAT-': {csv.sat_id!r}")
    if not csv.beg_id.startswith("BEG-"):
        raise ValueError(f"beg_id must start with 'BEG-': {csv.beg_id!r}")
    if not csv.bti_id.startswith("BTI-"):
        raise ValueError(f"bti_id must start with 'BTI-': {csv.bti_id!r}")
    if csv.linkage_verdict not in VALID_LINKAGE_VERDICTS:
        raise ValueError(
            f"linkage_verdict {csv.linkage_verdict!r} not in VALID_LINKAGE_VERDICTS"
        )
    for entry in csv.orphan_entries:
        if entry.reference_source not in VALID_REFERENCE_SOURCES:
            raise ValueError(
                f"reference_source {entry.reference_source!r} not in VALID_REFERENCE_SOURCES"
            )
    if not csv.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not csv.limitations:
        raise ValueError("limitations must be non-empty")
    if not csv.created_at:
        raise ValueError("created_at must be non-empty")
    if csv.n_references_checked != len(csv.referenced_artifact_ids):
        raise ValueError("n_references_checked must equal len(referenced_artifact_ids)")
    if csv.n_orphans_found != len(csv.orphan_entries):
        raise ValueError("n_orphans_found must equal len(orphan_entries)")


def build_cross_schema_linkage_validator(
    *,
    csv_id: str,
    batch_id: str,
    pipeline_version: str,
    sat_id: str,
    beg_id: str,
    bti_id: str,
    known_artifact_ids: list[str],
    reference_dicts: list[dict],
    limitations: list[str],
    created_at: str,
) -> CrossSchemaLinkageValidator:
    """Build a cross-schema linkage validator record.

    Args:
        known_artifact_ids: All artifact IDs that actually exist in this batch.
        reference_dicts: List of dicts with keys: artifact_id, reference_source.
            reference_source must be one of VALID_REFERENCE_SOURCES.
    """
    for d in reference_dicts:
        if d["reference_source"] not in VALID_REFERENCE_SOURCES:
            raise ValueError(
                f"reference_source {d['reference_source']!r} not in VALID_REFERENCE_SOURCES"
            )

    known_set = set(known_artifact_ids)
    all_known_sorted = sorted(known_artifact_ids)

    referenced = sorted({d["artifact_id"] for d in reference_dicts})
    orphans: list[OrphanEntry] = []
    for d in reference_dicts:
        aid = d["artifact_id"]
        src = d["reference_source"]
        if aid not in known_set:
            orphans.append(OrphanEntry(
                artifact_id=aid,
                reference_source=src,
                details=f"{aid!r} referenced in {src} but not found in known artifacts",
            ))

    orphans_sorted = sorted(orphans, key=lambda o: (o.artifact_id, o.reference_source))
    verdict = _compute_verdict(len(referenced), len(orphans_sorted))

    record = CrossSchemaLinkageValidator(
        csv_id=csv_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        sat_id=sat_id,
        beg_id=beg_id,
        bti_id=bti_id,
        all_known_artifact_ids=all_known_sorted,
        referenced_artifact_ids=referenced,
        orphan_entries=orphans_sorted,
        n_references_checked=len(referenced),
        n_orphans_found=len(orphans_sorted),
        linkage_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_cross_schema_linkage_validator(record)
    return record


def format_cross_schema_linkage_validator(csv: CrossSchemaLinkageValidator) -> str:
    lines = [
        f"Cross-Schema Linkage Validator — {csv.csv_id}",
        f"Batch: {csv.batch_id}  |  Pipeline: {csv.pipeline_version}",
        f"Verdict: {csv.linkage_verdict}",
        f"References checked: {csv.n_references_checked}  |  Orphans: {csv.n_orphans_found}",
        f"SAT: {csv.sat_id}  |  BEG: {csv.beg_id}  |  BTI: {csv.bti_id}",
    ]
    if csv.orphan_entries:
        lines.append("Orphaned references:")
        for entry in csv.orphan_entries:
            lines.append(f"  [{entry.reference_source}] {entry.artifact_id}: {entry.details}")
    else:
        lines.append("No orphaned references found.")
    lines.append(f"Created: {csv.created_at}")
    lines.append(f"Limitations: {'; '.join(csv.limitations)}")
    lines.append(f"dry_lab_only: {csv.dry_lab_only}")
    return "\n".join(lines)

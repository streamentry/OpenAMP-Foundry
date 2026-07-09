from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class CandidateManifest:
    candidate_id: str
    sequence: str
    evidence_level: int
    scopes: list[str]
    scores: dict[str, float]
    uncertainty: float
    source_modules: list[str]
    calibration_set: str | None
    safety_flags: list[str]
    provenance_run_id: str | None
    dry_lab_only: bool = True
    version: str = "1.0.0"
    created_at: str = ""
    notes: list[str] = field(default_factory=list)


def make_candidate_manifest(
    candidate_id: str,
    sequence: str,
    evidence_level: int,
    scopes: list[str],
    scores: dict[str, float],
    uncertainty: float,
    source_modules: list[str],
    *,
    calibration_set: str | None = None,
    safety_flags: list[str] | None = None,
    provenance_run_id: str | None = None,
    created_at: str = "",
    notes: list[str] | None = None,
) -> CandidateManifest:
    return CandidateManifest(
        candidate_id=candidate_id,
        sequence=sequence,
        evidence_level=evidence_level,
        scopes=scopes,
        scores=scores,
        uncertainty=uncertainty,
        source_modules=source_modules,
        calibration_set=calibration_set,
        safety_flags=safety_flags or [],
        provenance_run_id=provenance_run_id,
        created_at=created_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        notes=notes or [],
    )


def validate_candidate_manifest(manifest: CandidateManifest) -> list[str]:
    errors: list[str] = []
    if not manifest.candidate_id:
        errors.append("candidate_id must be non-empty")
    if not manifest.sequence:
        errors.append("sequence must be non-empty")
    if manifest.evidence_level < 1 or manifest.evidence_level > 6:
        errors.append(f"evidence_level must be 1-6, got {manifest.evidence_level}")
    if not manifest.scopes:
        errors.append("scopes must be a non-empty list")
    if manifest.uncertainty < 0.0 or manifest.uncertainty > 1.0:
        errors.append(f"uncertainty must be in [0.0, 1.0], got {manifest.uncertainty}")
    if not manifest.source_modules:
        errors.append("source_modules must be a non-empty list")
    if not manifest.dry_lab_only:
        errors.append("dry_lab_only must be True")
    if not re.match(r"^\d+\.\d+\.\d+$", manifest.version):
        errors.append(f"version must match MAJOR.MINOR.PATCH, got {manifest.version!r}")
    return errors


def manifest_to_dict(manifest: CandidateManifest) -> dict:
    return {
        "candidate_id": manifest.candidate_id,
        "sequence": manifest.sequence,
        "evidence_level": manifest.evidence_level,
        "scopes": list(manifest.scopes),
        "scores": dict(manifest.scores),
        "uncertainty": manifest.uncertainty,
        "source_modules": list(manifest.source_modules),
        "calibration_set": manifest.calibration_set,
        "safety_flags": list(manifest.safety_flags),
        "provenance_run_id": manifest.provenance_run_id,
        "dry_lab_only": manifest.dry_lab_only,
        "version": manifest.version,
        "created_at": manifest.created_at,
        "notes": list(manifest.notes),
    }


def manifest_summary(manifests: list[CandidateManifest]) -> dict:
    by_evidence: dict[str, int] = {}
    with_safety_flags = 0
    for m in manifests:
        level_key = str(m.evidence_level)
        by_evidence[level_key] = by_evidence.get(level_key, 0) + 1
        if m.safety_flags:
            with_safety_flags += 1
    return {
        "total": len(manifests),
        "by_evidence_level": by_evidence,
        "with_safety_flags": with_safety_flags,
        "dry_lab_only": True,
    }

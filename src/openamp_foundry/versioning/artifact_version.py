from __future__ import annotations

import re
from dataclasses import dataclass, field

STABILITY_TIERS: dict[str, str] = {
    "stable": "Tier 1 — requires MAJOR bump for breaking changes",
    "experimental": "Tier 2 — may change without notice, must be labeled",
    "internal": "Tier 3 — no stability promise, not for external use",
}


@dataclass
class ArtifactVersionInfo:
    artifact_name: str
    version: str
    stability_tier: str
    schema_id: str | None
    description: str
    is_breaking_change: bool = False
    notes: str = ""


VERSIONED_ARTIFACTS: list[ArtifactVersionInfo] = [
    ArtifactVersionInfo(
        artifact_name="candidate",
        version="1.0.0",
        stability_tier="stable",
        schema_id=None,
        description="Candidate evidence certificate — per-candidate scoring and evidence output",
        is_breaking_change=False,
        notes="Core schema used in all pipeline runs. No $id set, but in active production use.",
    ),
    ArtifactVersionInfo(
        artifact_name="lab_result",
        version="1.0.0",
        stability_tier="stable",
        schema_id=None,
        description="Lab assay result — machine-readable outcome for active-learning ingestion",
        is_breaking_change=False,
        notes="Required for calibration intake loop. No $id set, but in active production use.",
    ),
    ArtifactVersionInfo(
        artifact_name="run_manifest",
        version="1.0.0",
        stability_tier="stable",
        schema_id=None,
        description="Run manifest — pipeline run provenance with input hashes and output paths",
        is_breaking_change=False,
        notes="Provenance record for reproducibility. No $id set, but in active production use.",
    ),
    ArtifactVersionInfo(
        artifact_name="external_review_packet",
        version="1.0.0",
        stability_tier="stable",
        schema_id="https://openamp-foundry.org/schemas/external_review_packet.schema.json",
        description="External review packet — complete machine-checkable review artifact for lab partners",
        is_breaking_change=False,
        notes="Has $id URI. Used for external-facing review packets.",
    ),
    ArtifactVersionInfo(
        artifact_name="safety_release_decision",
        version="1.0.0",
        stability_tier="stable",
        schema_id="https://openamp-foundry.org/schemas/safety_release_decision.schema.json",
        description="Safety release decision — human-gated release decision with safety checks",
        is_breaking_change=False,
        notes="Has $id URI. Human review required for release decisions.",
    ),
    ArtifactVersionInfo(
        artifact_name="simulation_result",
        version="1.0.0",
        stability_tier="experimental",
        schema_id="https://openamp.ai/schemas/simulation_result.schema.json",
        description="Simulation result — virtual assay module output with uncertainty",
        is_breaking_change=False,
        notes="Has $id URI. Experimental due to ongoing simulation module development.",
    ),
]


def get_artifact_version(artifact_name: str) -> ArtifactVersionInfo | None:
    for entry in VERSIONED_ARTIFACTS:
        if entry.artifact_name == artifact_name:
            return entry
    return None


def list_versioned_artifacts(tier: str | None = None) -> list[ArtifactVersionInfo]:
    if tier is None:
        return list(VERSIONED_ARTIFACTS)
    return [entry for entry in VERSIONED_ARTIFACTS if entry.stability_tier == tier]


def validate_version_format(version: str) -> bool:
    pattern = r"^\d+\.\d+\.\d+$"
    return bool(re.match(pattern, version))


def artifact_version_summary() -> dict:
    by_tier: dict[str, int] = {}
    for entry in VERSIONED_ARTIFACTS:
        by_tier[entry.stability_tier] = by_tier.get(entry.stability_tier, 0) + 1
    return {
        "total": len(VERSIONED_ARTIFACTS),
        "by_tier": by_tier,
        "stable_count": len(list_versioned_artifacts("stable")),
        "experimental_count": len(list_versioned_artifacts("experimental")),
        "dry_lab_only": True,
    }

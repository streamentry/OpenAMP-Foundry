from __future__ import annotations

import re
from dataclasses import dataclass

CHANGE_TYPES: set[str] = {"added", "changed", "deprecated", "removed", "fixed", "security"}


@dataclass
class ChangelogEntry:
    version: str
    date: str
    artifact_name: str
    change_type: str
    description: str
    breaking: bool = False
    notes: str = ""


ARTIFACT_CHANGELOG: list[ChangelogEntry] = [
    ChangelogEntry(
        version="1.0.0",
        date="2026-07-09",
        artifact_name="candidate_manifest",
        change_type="added",
        description=(
            "Initial schema with 14 required fields: candidate_id, sequence, "
            "evidence_level, scopes, scores, uncertainty, source_modules, "
            "calibration_set, safety_flags, provenance_run_id, dry_lab_only, "
            "version, created_at, notes. Phase I I2."
        ),
        breaking=False,
        notes="Core interoperable artifact for dry-lab candidates.",
    ),
    ChangelogEntry(
        version="1.0.0",
        date="2026-07-09",
        artifact_name="benchmark_card",
        change_type="added",
        description=(
            "Initial schema with 15 required fields: benchmark_id, "
            "benchmark_name, version, date, metric, metric_value, "
            "baseline_name, baseline_value, delta, beats_baseline, dataset, "
            "dataset_size, scope, caveats, dry_lab_only. Phase I I3."
        ),
        breaking=False,
        notes="Standard format for external benchmark results.",
    ),
    ChangelogEntry(
        version="1.0.0",
        date="2026-07-09",
        artifact_name="simulation_result",
        change_type="added",
        description=(
            "Initial schema with 8 required fields: module, version, scope, "
            "scores, uncertainty, calibration_set, validated_against, notes. "
            "Phase H H2."
        ),
        breaking=False,
        notes="Virtual assay module output with uncertainty.",
    ),
    ChangelogEntry(
        version="1.0.0",
        date="2026-07-09",
        artifact_name="simulation_module_registry",
        change_type="added",
        description=(
            "Initial schema with module metadata fields: module_id, name, "
            "description, status, evidence_level, baseline_comparison, scope, "
            "maintainer, notes. Phase H H1."
        ),
        breaking=False,
        notes="Registry of virtual assay modules with status and evidence level.",
    ),
    ChangelogEntry(
        version="1.0.0",
        date="2026-07-09",
        artifact_name="artifact_versioning_policy",
        change_type="added",
        description=(
            "Initial versioning policy document with stability tiers, "
            "SemVer format, breaking change rules, and deprecation "
            "timeline. Phase I I1."
        ),
        breaking=False,
        notes="External users now have stability guarantees.",
    ),
    ChangelogEntry(
        version="1.0.0",
        date="2026-07-09",
        artifact_name="artifact_changelog",
        change_type="added",
        description=(
            "Initial evidence-certificate changelog with structured "
            "entries for all versioned artifacts. Phase I I4."
        ),
        breaking=False,
        notes="Backward compatibility for external artifact consumers.",
    ),
]


def get_changelog_entries(
    artifact_name: str | None = None,
    version: str | None = None,
    change_type: str | None = None,
    breaking_only: bool = False,
) -> list[ChangelogEntry]:
    result = list(ARTIFACT_CHANGELOG)
    if artifact_name is not None:
        result = [e for e in result if e.artifact_name == artifact_name]
    if version is not None:
        result = [e for e in result if e.version == version]
    if change_type is not None:
        result = [e for e in result if e.change_type == change_type]
    if breaking_only:
        result = [e for e in result if e.breaking]
    return result


def validate_changelog() -> list[str]:
    errors: list[str] = []
    version_pattern = re.compile(r"^\d+\.\d+\.\d+$")
    for i, entry in enumerate(ARTIFACT_CHANGELOG):
        if not version_pattern.match(entry.version):
            errors.append(f"Entry {i}: invalid version format '{entry.version}'")
        if not entry.date or "-" not in entry.date:
            errors.append(f"Entry {i}: invalid date format '{entry.date}'")
        if not entry.artifact_name:
            errors.append(f"Entry {i}: empty artifact_name")
        if entry.change_type not in CHANGE_TYPES:
            errors.append(f"Entry {i}: invalid change_type '{entry.change_type}'")
        if not entry.description:
            errors.append(f"Entry {i}: empty description")
    return errors


def changelog_summary() -> dict:
    by_change_type: dict[str, int] = {}
    breaking_count = 0
    artifacts: set[str] = set()
    for entry in ARTIFACT_CHANGELOG:
        by_change_type[entry.change_type] = by_change_type.get(entry.change_type, 0) + 1
        if entry.breaking:
            breaking_count += 1
        artifacts.add(entry.artifact_name)
    return {
        "total": len(ARTIFACT_CHANGELOG),
        "by_change_type": by_change_type,
        "breaking_changes": breaking_count,
        "artifacts_covered": sorted(artifacts),
        "dry_lab_only": True,
    }

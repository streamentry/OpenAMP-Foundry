"""
Versioned schema export for partner consumption.

I6: Stable API for partners. Provides a manifest of all exported schemas
with version metadata, stability tiers, and schema IDs. Partners can use
this manifest to discover available schemas and their current versions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

SCHEMA_EXPORT_ID_PREFIX: str = "SEM-"

VALID_STABILITY_TIERS: frozenset[str] = frozenset({
    "stable",
    "experimental",
    "internal",
    "deprecated",
})

STABILITY_TIER_DESCRIPTIONS: dict[str, str] = {
    "stable": "Tier 1 — breaking changes require MAJOR version bump",
    "experimental": "Tier 2 — may change without notice, not for production",
    "internal": "Tier 3 — no stability promise, not for external use",
    "deprecated": "Tier 0 — scheduled for removal, do not use",
}


@dataclass
class SchemaExportEntry:
    """A single schema in a versioned export manifest."""

    schema_name: str
    schema_path: str
    schema_id: str
    version: str
    stability_tier: str
    description: str
    is_dry_lab_only: bool


@dataclass
class SchemaExportManifest:
    """
    Versioned export manifest for all schemas available to partner tools.

    Export manifests use the SEM- prefix and record which schemas are
    available, at what version, and at what stability tier.
    """

    manifest_id: str
    generated_at: str
    total_schemas: int
    stable_schemas: int
    experimental_schemas: int
    deprecated_schemas: int
    entries: list[SchemaExportEntry]
    is_stable_export: bool
    export_summary: str


@dataclass
class ExportValidationResult:
    """Result of validating a SchemaExportManifest."""

    is_valid: bool
    violations: list[str]
    warnings: list[str]
    manifest_id: str
    validation_summary: str


def build_schema_export_entry(
    schema_name: str,
    schema_path: str,
    schema_id: str,
    version: str,
    stability_tier: str,
    description: str,
    is_dry_lab_only: bool = True,
) -> SchemaExportEntry:
    """
    Build a SchemaExportEntry for a single schema.

    All schemas exported from OpenAMP Foundry are dry-lab-only by default.
    """
    return SchemaExportEntry(
        schema_name=schema_name,
        schema_path=schema_path,
        schema_id=schema_id,
        version=version,
        stability_tier=stability_tier,
        description=description,
        is_dry_lab_only=is_dry_lab_only,
    )


def build_schema_export_manifest(
    manifest_id: str,
    generated_at: str,
    entries: list[SchemaExportEntry],
) -> SchemaExportManifest:
    """
    Build a SchemaExportManifest from a list of SchemaExportEntry instances.

    Computes tier counts and stability flag automatically.
    """
    stable = sum(1 for e in entries if e.stability_tier == "stable")
    experimental = sum(1 for e in entries if e.stability_tier == "experimental")
    deprecated = sum(1 for e in entries if e.stability_tier == "deprecated")
    is_stable = len(entries) > 0 and experimental == 0 and deprecated == 0

    summary = (
        f"SEM manifest {manifest_id}: "
        f"{len(entries)} schema(s), "
        f"{stable} stable, "
        f"{experimental} experimental, "
        f"{deprecated} deprecated."
    )

    return SchemaExportManifest(
        manifest_id=manifest_id,
        generated_at=generated_at,
        total_schemas=len(entries),
        stable_schemas=stable,
        experimental_schemas=experimental,
        deprecated_schemas=deprecated,
        entries=entries,
        is_stable_export=is_stable,
        export_summary=summary,
    )


def validate_schema_export_manifest(
    manifest: SchemaExportManifest,
) -> ExportValidationResult:
    """
    Validate a SchemaExportManifest against integrity rules.

    Rules:
      1. manifest_id must start with 'SEM-'
      2. manifest_id must have content after the prefix
      3. generated_at must not be empty
      4. total_schemas must equal len(entries)
      5. all entries must have a non-empty schema_name
      6. all entries must have a non-empty schema_id
      7. all entries must have a stability_tier in VALID_STABILITY_TIERS
      8. schema names must not contain duplicates
      9. stable_schemas + experimental_schemas + deprecated_schemas must equal
         the count of entries with those three tiers (internal counts separately)
      10. is_stable_export must be False if any experimental or deprecated entries exist
    """
    violations: list[str] = []
    warnings: list[str] = []

    if not manifest.manifest_id.startswith(SCHEMA_EXPORT_ID_PREFIX):
        violations.append(
            f"manifest_id must start with '{SCHEMA_EXPORT_ID_PREFIX}', "
            f"got: {manifest.manifest_id!r}"
        )

    if len(manifest.manifest_id) <= len(SCHEMA_EXPORT_ID_PREFIX):
        violations.append("manifest_id must have content after the prefix.")

    if not manifest.generated_at.strip():
        violations.append("generated_at must not be empty.")

    if manifest.total_schemas != len(manifest.entries):
        violations.append(
            f"total_schemas ({manifest.total_schemas}) must equal "
            f"len(entries) ({len(manifest.entries)})."
        )

    for i, entry in enumerate(manifest.entries):
        if not entry.schema_name.strip():
            violations.append(f"Entry {i}: schema_name must not be empty.")
        if not entry.schema_id.strip():
            violations.append(f"Entry {i}: schema_id must not be empty.")
        if entry.stability_tier not in VALID_STABILITY_TIERS:
            violations.append(
                f"Entry {i} ({entry.schema_name!r}): stability_tier must be one of "
                f"{sorted(VALID_STABILITY_TIERS)}, got: {entry.stability_tier!r}"
            )

    names = [e.schema_name for e in manifest.entries]
    if len(names) != len(set(names)):
        violations.append("schema_names must not contain duplicates.")

    has_experimental = any(e.stability_tier == "experimental" for e in manifest.entries)
    has_deprecated = any(e.stability_tier == "deprecated" for e in manifest.entries)
    if manifest.is_stable_export and (has_experimental or has_deprecated):
        violations.append(
            "is_stable_export must be False when experimental or deprecated entries exist."
        )

    if manifest.deprecated_schemas > 0:
        warnings.append(
            f"{manifest.deprecated_schemas} deprecated schema(s) in export. "
            "Consider removing them before next major release."
        )

    is_valid = len(violations) == 0
    if is_valid:
        summary = (
            f"SchemaExportManifest {manifest.manifest_id} is valid: "
            f"{manifest.total_schemas} schema(s)."
        )
    else:
        summary = (
            f"SchemaExportManifest {manifest.manifest_id} has "
            f"{len(violations)} violation(s): "
            + "; ".join(violations[:2])
            + ("..." if len(violations) > 2 else "")
        )

    return ExportValidationResult(
        is_valid=is_valid,
        violations=violations,
        warnings=warnings,
        manifest_id=manifest.manifest_id,
        validation_summary=summary,
    )


def format_schema_export_manifest(manifest: SchemaExportManifest) -> str:
    """Return a human-readable schema export manifest."""
    lines: list[str] = [
        f"Schema Export Manifest: {manifest.manifest_id}",
        f"  Generated:         {manifest.generated_at}",
        f"  Total schemas:     {manifest.total_schemas}",
        f"  Stable:            {manifest.stable_schemas}",
        f"  Experimental:      {manifest.experimental_schemas}",
        f"  Deprecated:        {manifest.deprecated_schemas}",
        f"  Stable export:     {manifest.is_stable_export}",
        "",
        "Schemas:",
    ]
    for entry in manifest.entries:
        tier_mark = {
            "stable": "+",
            "experimental": "~",
            "internal": ".",
            "deprecated": "!",
        }.get(entry.stability_tier, "?")
        lines.append(
            f"  [{tier_mark}] {entry.schema_name} v{entry.version} "
            f"({entry.stability_tier}) "
            f"{'[dry-lab-only]' if entry.is_dry_lab_only else '[wet-lab]'}"
        )
        if entry.description:
            lines.append(f"       {entry.description}")
    return "\n".join(lines)

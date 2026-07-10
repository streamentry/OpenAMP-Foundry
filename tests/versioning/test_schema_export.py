"""Tests for I6 versioned schema export."""

from __future__ import annotations

import pytest

from openamp_foundry.versioning.schema_export import (
    SCHEMA_EXPORT_ID_PREFIX,
    STABILITY_TIER_DESCRIPTIONS,
    VALID_STABILITY_TIERS,
    ExportValidationResult,
    SchemaExportEntry,
    SchemaExportManifest,
    build_schema_export_entry,
    build_schema_export_manifest,
    format_schema_export_manifest,
    validate_schema_export_manifest,
)


def _make_entry(**kwargs) -> SchemaExportEntry:
    defaults = dict(
        schema_name="external_review_packet",
        schema_path="src/openamp_foundry/evidence/external_review_packet.py",
        schema_id="https://openamp-foundry.org/schemas/erp/1.0.0",
        version="1.0.0",
        stability_tier="stable",
        description="ERP- schema for external review packets.",
        is_dry_lab_only=True,
    )
    defaults.update(kwargs)
    return SchemaExportEntry(**defaults)


def _make_manifest(**kwargs) -> SchemaExportManifest:
    entries = kwargs.pop("entries", [_make_entry()])
    manifest_id = kwargs.pop("manifest_id", "SEM-2026-001")
    generated_at = kwargs.pop("generated_at", "2026-01-01T00:00:00Z")
    return build_schema_export_manifest(manifest_id, generated_at, entries)


class TestConstants:
    def test_prefix(self):
        assert SCHEMA_EXPORT_ID_PREFIX == "SEM-"

    def test_valid_tiers_frozenset(self):
        assert isinstance(VALID_STABILITY_TIERS, frozenset)

    def test_stable_in_tiers(self):
        assert "stable" in VALID_STABILITY_TIERS

    def test_experimental_in_tiers(self):
        assert "experimental" in VALID_STABILITY_TIERS

    def test_internal_in_tiers(self):
        assert "internal" in VALID_STABILITY_TIERS

    def test_deprecated_in_tiers(self):
        assert "deprecated" in VALID_STABILITY_TIERS

    def test_tier_descriptions_dict(self):
        assert isinstance(STABILITY_TIER_DESCRIPTIONS, dict)

    def test_tier_descriptions_has_stable(self):
        assert "stable" in STABILITY_TIER_DESCRIPTIONS

    def test_tier_descriptions_has_deprecated(self):
        assert "deprecated" in STABILITY_TIER_DESCRIPTIONS


class TestBuildSchemaExportEntry:
    def test_builds_entry(self):
        entry = build_schema_export_entry(
            schema_name="foo",
            schema_path="src/foo.py",
            schema_id="https://example.org/foo",
            version="1.0.0",
            stability_tier="stable",
            description="Foo schema.",
        )
        assert isinstance(entry, SchemaExportEntry)

    def test_default_dry_lab_only(self):
        entry = build_schema_export_entry("x", "path", "id", "1.0", "stable", "desc")
        assert entry.is_dry_lab_only is True

    def test_explicit_dry_lab_false(self):
        entry = build_schema_export_entry("x", "p", "i", "1.0", "stable", "d", False)
        assert entry.is_dry_lab_only is False

    def test_all_fields_stored(self):
        entry = build_schema_export_entry(
            "foo", "src/foo.py", "id://foo", "2.0.0", "experimental", "desc"
        )
        assert entry.schema_name == "foo"
        assert entry.schema_path == "src/foo.py"
        assert entry.schema_id == "id://foo"
        assert entry.version == "2.0.0"
        assert entry.stability_tier == "experimental"
        assert entry.description == "desc"


class TestBuildSchemaExportManifest:
    def test_builds_manifest(self):
        manifest = _make_manifest()
        assert isinstance(manifest, SchemaExportManifest)

    def test_total_schemas_count(self):
        entries = [_make_entry(schema_name=f"s{i}") for i in range(3)]
        manifest = _make_manifest(entries=entries)
        assert manifest.total_schemas == 3

    def test_stable_count(self):
        entries = [
            _make_entry(schema_name="a", stability_tier="stable"),
            _make_entry(schema_name="b", stability_tier="experimental"),
        ]
        manifest = _make_manifest(entries=entries)
        assert manifest.stable_schemas == 1

    def test_experimental_count(self):
        entries = [
            _make_entry(schema_name="a", stability_tier="experimental"),
            _make_entry(schema_name="b", stability_tier="experimental"),
        ]
        manifest = _make_manifest(entries=entries)
        assert manifest.experimental_schemas == 2

    def test_deprecated_count(self):
        entries = [
            _make_entry(schema_name="a", stability_tier="deprecated"),
        ]
        manifest = _make_manifest(entries=entries)
        assert manifest.deprecated_schemas == 1

    def test_is_stable_when_all_stable(self):
        entries = [_make_entry(schema_name="a", stability_tier="stable")]
        manifest = _make_manifest(entries=entries)
        assert manifest.is_stable_export is True

    def test_not_stable_with_experimental(self):
        entries = [_make_entry(schema_name="a", stability_tier="experimental")]
        manifest = _make_manifest(entries=entries)
        assert manifest.is_stable_export is False

    def test_not_stable_with_deprecated(self):
        entries = [_make_entry(schema_name="a", stability_tier="deprecated")]
        manifest = _make_manifest(entries=entries)
        assert manifest.is_stable_export is False

    def test_empty_entries_not_stable(self):
        manifest = _make_manifest(entries=[])
        assert manifest.is_stable_export is False

    def test_summary_nonempty(self):
        manifest = _make_manifest()
        assert len(manifest.export_summary) > 0

    def test_manifest_id_stored(self):
        manifest = _make_manifest()
        assert manifest.manifest_id == "SEM-2026-001"

    def test_generated_at_stored(self):
        manifest = _make_manifest()
        assert manifest.generated_at == "2026-01-01T00:00:00Z"


class TestValidateSchemaExportManifest:
    def test_valid_manifest_passes(self):
        manifest = _make_manifest()
        result = validate_schema_export_manifest(manifest)
        assert result.is_valid is True

    def test_valid_no_violations(self):
        manifest = _make_manifest()
        result = validate_schema_export_manifest(manifest)
        assert result.violations == []

    def test_result_type(self):
        manifest = _make_manifest()
        result = validate_schema_export_manifest(manifest)
        assert isinstance(result, ExportValidationResult)

    def test_bad_prefix_fails(self):
        manifest = _make_manifest()
        manifest.manifest_id = "BAD-001"
        result = validate_schema_export_manifest(manifest)
        assert not result.is_valid

    def test_prefix_only_fails(self):
        manifest = _make_manifest()
        manifest.manifest_id = "SEM-"
        result = validate_schema_export_manifest(manifest)
        assert not result.is_valid

    def test_empty_generated_at_fails(self):
        manifest = _make_manifest()
        manifest.generated_at = ""
        result = validate_schema_export_manifest(manifest)
        assert not result.is_valid

    def test_wrong_total_fails(self):
        manifest = _make_manifest()
        manifest.total_schemas = 999
        result = validate_schema_export_manifest(manifest)
        assert not result.is_valid

    def test_empty_schema_name_fails(self):
        entries = [_make_entry(schema_name="")]
        manifest = _make_manifest(entries=entries)
        result = validate_schema_export_manifest(manifest)
        assert not result.is_valid

    def test_empty_schema_id_fails(self):
        entries = [_make_entry(schema_id="")]
        manifest = _make_manifest(entries=entries)
        result = validate_schema_export_manifest(manifest)
        assert not result.is_valid

    def test_invalid_tier_fails(self):
        entries = [_make_entry(stability_tier="beta")]
        manifest = _make_manifest(entries=entries)
        result = validate_schema_export_manifest(manifest)
        assert not result.is_valid

    def test_duplicate_names_fail(self):
        entries = [
            _make_entry(schema_name="same"),
            _make_entry(schema_name="same"),
        ]
        manifest = _make_manifest(entries=entries)
        result = validate_schema_export_manifest(manifest)
        assert not result.is_valid

    def test_stable_export_with_experimental_fails(self):
        entries = [_make_entry(schema_name="a", stability_tier="experimental")]
        manifest = _make_manifest(entries=entries)
        manifest.is_stable_export = True
        result = validate_schema_export_manifest(manifest)
        assert not result.is_valid

    def test_deprecated_warns(self):
        entries = [_make_entry(schema_name="a", stability_tier="deprecated")]
        manifest = _make_manifest(entries=entries)
        result = validate_schema_export_manifest(manifest)
        assert result.is_valid
        assert len(result.warnings) > 0

    def test_all_tiers_valid(self):
        for tier in VALID_STABILITY_TIERS:
            entries = [_make_entry(schema_name="a", stability_tier=tier)]
            manifest = _make_manifest(entries=entries)
            result = validate_schema_export_manifest(manifest)
            if tier in ("deprecated",):
                assert result.is_valid
            else:
                assert result.is_valid, f"tier {tier!r} should be valid"

    def test_summary_nonempty(self):
        manifest = _make_manifest()
        result = validate_schema_export_manifest(manifest)
        assert len(result.validation_summary) > 0


class TestFormatSchemaExportManifest:
    def setup_method(self):
        self.entries = [
            _make_entry(
                schema_name="external_review_packet",
                version="1.0.0",
                stability_tier="stable",
            ),
            _make_entry(
                schema_name="pilot_preregistration",
                version="0.9.0",
                stability_tier="experimental",
            ),
        ]
        self.manifest = _make_manifest(entries=self.entries)
        self.text = format_schema_export_manifest(self.manifest)

    def test_returns_string(self):
        assert isinstance(self.text, str)

    def test_contains_manifest_id(self):
        assert "SEM-2026-001" in self.text

    def test_contains_schema_names(self):
        assert "external_review_packet" in self.text
        assert "pilot_preregistration" in self.text

    def test_contains_versions(self):
        assert "1.0.0" in self.text
        assert "0.9.0" in self.text

    def test_contains_tier_labels(self):
        assert "stable" in self.text
        assert "experimental" in self.text

    def test_stable_marker(self):
        assert "[+]" in self.text

    def test_experimental_marker(self):
        assert "[~]" in self.text

    def test_dry_lab_label(self):
        assert "dry-lab-only" in self.text

    def test_contains_counts(self):
        assert "2" in self.text

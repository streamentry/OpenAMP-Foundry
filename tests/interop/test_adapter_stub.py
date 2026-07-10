"""Tests for src/openamp_foundry/interop/adapter_stub.py (63 tests)."""

import pytest
from openamp_foundry.interop.adapter_stub import (
    ADAPTER_STUB_ID_PREFIX,
    VALID_TARGET_TOOLS,
    VALID_OUTPUT_FORMATS,
    VALID_ADAPTER_STATUSES,
    TOY_ID_PREFIXES,
    STUB_DISCLAIMER,
    AdapterField,
    AdapterStubRecord,
    AdapterValidationResult,
    build_adapter_field,
    build_adapter_stub_record,
    validate_adapter_stub_record,
    format_adapter_stub_record,
)


def _valid_record():
    return build_adapter_stub_record(
        adapter_id="ADS-001",
        target_tool="ampscanner",
        output_format="fasta",
        adapter_status="stub",
        dry_lab_only=True,
        disclaimer=STUB_DISCLAIMER,
        version="0.1.0",
        implementation_notes="Stub for AMPScanner v2 integration",
    )


class TestConstants:
    def test_prefix(self):
        assert ADAPTER_STUB_ID_PREFIX == "ADS-"

    def test_valid_target_tools_is_frozenset(self):
        assert isinstance(VALID_TARGET_TOOLS, frozenset)

    def test_ampscanner_in_tools(self):
        assert "ampscanner" in VALID_TARGET_TOOLS

    def test_modlamp_in_tools(self):
        assert "modlamp" in VALID_TARGET_TOOLS

    def test_hmmer_in_tools(self):
        assert "hmmer" in VALID_TARGET_TOOLS

    def test_valid_output_formats_is_frozenset(self):
        assert isinstance(VALID_OUTPUT_FORMATS, frozenset)

    def test_fasta_in_formats(self):
        assert "fasta" in VALID_OUTPUT_FORMATS

    def test_csv_in_formats(self):
        assert "csv" in VALID_OUTPUT_FORMATS

    def test_json_in_formats(self):
        assert "json" in VALID_OUTPUT_FORMATS

    def test_valid_adapter_statuses_is_frozenset(self):
        assert isinstance(VALID_ADAPTER_STATUSES, frozenset)

    def test_stub_in_statuses(self):
        assert "stub" in VALID_ADAPTER_STATUSES

    def test_complete_in_statuses(self):
        assert "complete" in VALID_ADAPTER_STATUSES

    def test_deprecated_in_statuses(self):
        assert "deprecated" in VALID_ADAPTER_STATUSES

    def test_toy_id_prefixes_is_frozenset(self):
        assert isinstance(TOY_ID_PREFIXES, frozenset)

    def test_toy_prefix_in_prefixes(self):
        assert "TOY-" in TOY_ID_PREFIXES

    def test_stub_disclaimer_not_empty(self):
        assert STUB_DISCLAIMER != ""

    def test_stub_disclaimer_mentions_biological(self):
        assert "biological" in STUB_DISCLAIMER.lower()

    def test_stub_disclaimer_mentions_human_review(self):
        assert "human review" in STUB_DISCLAIMER.lower()


class TestBuildAdapterField:
    def test_returns_adapter_field(self):
        f = build_adapter_field("candidate_id", "sequence_id")
        assert isinstance(f, AdapterField)

    def test_source_field_stored(self):
        f = build_adapter_field("candidate_id", "sequence_id")
        assert f.source_field == "candidate_id"

    def test_target_field_stored(self):
        f = build_adapter_field("candidate_id", "sequence_id")
        assert f.target_field == "sequence_id"

    def test_transform_default_identity(self):
        f = build_adapter_field("candidate_id", "sequence_id")
        assert f.transform == "identity"

    def test_transform_custom(self):
        f = build_adapter_field("sequence", "aa_sequence", transform="uppercase")
        assert f.transform == "uppercase"

    def test_is_required_default_true(self):
        f = build_adapter_field("candidate_id", "sequence_id")
        assert f.is_required is True

    def test_is_required_false(self):
        f = build_adapter_field("description", "notes", is_required=False)
        assert f.is_required is False

    def test_notes_stored(self):
        f = build_adapter_field("candidate_id", "id", notes="rename only")
        assert f.notes == "rename only"


class TestBuildAdapterStubRecord:
    def test_returns_adapter_stub_record(self):
        record = _valid_record()
        assert isinstance(record, AdapterStubRecord)

    def test_adapter_id_stored(self):
        record = _valid_record()
        assert record.adapter_id == "ADS-001"

    def test_target_tool_stored(self):
        record = _valid_record()
        assert record.target_tool == "ampscanner"

    def test_output_format_stored(self):
        record = _valid_record()
        assert record.output_format == "fasta"

    def test_adapter_status_stored(self):
        record = _valid_record()
        assert record.adapter_status == "stub"

    def test_dry_lab_only_stored(self):
        record = _valid_record()
        assert record.dry_lab_only is True

    def test_disclaimer_stored(self):
        record = _valid_record()
        assert record.disclaimer == STUB_DISCLAIMER

    def test_version_stored(self):
        record = _valid_record()
        assert record.version == "0.1.0"

    def test_implementation_notes_auto_when_empty(self):
        record = build_adapter_stub_record(
            adapter_id="ADS-001",
            target_tool="ampscanner",
            output_format="fasta",
        )
        assert record.implementation_notes != ""

    def test_field_mappings_empty_by_default(self):
        record = _valid_record()
        assert record.field_mappings == []

    def test_field_mappings_stored(self):
        fm = build_adapter_field("candidate_id", "seq_id")
        record = build_adapter_stub_record(
            adapter_id="ADS-001",
            target_tool="ampscanner",
            output_format="fasta",
            field_mappings=[fm],
        )
        assert len(record.field_mappings) == 1


class TestValidateAdapterStubRecord:
    def test_valid_record_passes(self):
        result = validate_adapter_stub_record(_valid_record())
        assert result.is_valid

    def test_returns_validation_result(self):
        result = validate_adapter_stub_record(_valid_record())
        assert isinstance(result, AdapterValidationResult)

    def test_no_violations_on_valid(self):
        result = validate_adapter_stub_record(_valid_record())
        assert result.violations == []

    def test_wrong_id_prefix_fails(self):
        record = _valid_record()
        record.adapter_id = "BAD-001"
        result = validate_adapter_stub_record(record)
        assert not result.is_valid
        assert any("ADS-" in v for v in result.violations)

    def test_invalid_target_tool_fails(self):
        record = _valid_record()
        record.target_tool = "unknown_tool"
        result = validate_adapter_stub_record(record)
        assert not result.is_valid
        assert any("target_tool" in v for v in result.violations)

    def test_invalid_output_format_fails(self):
        record = _valid_record()
        record.output_format = "docx"
        result = validate_adapter_stub_record(record)
        assert not result.is_valid
        assert any("output_format" in v for v in result.violations)

    def test_invalid_adapter_status_fails(self):
        record = _valid_record()
        record.adapter_status = "unknown"
        result = validate_adapter_stub_record(record)
        assert not result.is_valid
        assert any("adapter_status" in v for v in result.violations)

    def test_dry_lab_false_fails(self):
        record = _valid_record()
        record.dry_lab_only = False
        result = validate_adapter_stub_record(record)
        assert not result.is_valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_empty_disclaimer_fails(self):
        record = _valid_record()
        record.disclaimer = ""
        result = validate_adapter_stub_record(record)
        assert not result.is_valid
        assert any("disclaimer" in v for v in result.violations)

    def test_disclaimer_missing_biological_fails(self):
        record = _valid_record()
        record.disclaimer = "Stub adapter. Human review required."
        result = validate_adapter_stub_record(record)
        assert not result.is_valid
        assert any("biological" in v for v in result.violations)

    def test_empty_version_fails(self):
        record = _valid_record()
        record.version = ""
        result = validate_adapter_stub_record(record)
        assert not result.is_valid
        assert any("version" in v for v in result.violations)

    def test_empty_implementation_notes_fails(self):
        record = _valid_record()
        record.implementation_notes = ""
        result = validate_adapter_stub_record(record)
        assert not result.is_valid
        assert any("implementation_notes" in v for v in result.violations)

    def test_field_mapping_empty_source_fails(self):
        fm = build_adapter_field("", "target")
        record = build_adapter_stub_record(
            adapter_id="ADS-001",
            target_tool="ampscanner",
            output_format="fasta",
            field_mappings=[fm],
            implementation_notes="test",
        )
        result = validate_adapter_stub_record(record)
        assert not result.is_valid
        assert any("source_field" in v for v in result.violations)

    def test_field_mapping_empty_target_fails(self):
        fm = build_adapter_field("source", "")
        record = build_adapter_stub_record(
            adapter_id="ADS-001",
            target_tool="ampscanner",
            output_format="fasta",
            field_mappings=[fm],
            implementation_notes="test",
        )
        result = validate_adapter_stub_record(record)
        assert not result.is_valid
        assert any("target_field" in v for v in result.violations)

    def test_multiple_violations_accumulated(self):
        record = _valid_record()
        record.adapter_id = "BAD-001"
        record.target_tool = "unknown"
        result = validate_adapter_stub_record(record)
        assert len(result.violations) >= 2

    def test_all_valid_target_tools_accepted(self):
        for tool in VALID_TARGET_TOOLS:
            record = build_adapter_stub_record(
                adapter_id="ADS-001",
                target_tool=tool,
                output_format="fasta",
                implementation_notes=f"stub for {tool}",
            )
            result = validate_adapter_stub_record(record)
            assert result.is_valid, f"Tool {tool} failed: {result.violations}"

    def test_all_valid_formats_accepted(self):
        for fmt in VALID_OUTPUT_FORMATS:
            record = build_adapter_stub_record(
                adapter_id="ADS-001",
                target_tool="ampscanner",
                output_format=fmt,
                implementation_notes="stub",
            )
            result = validate_adapter_stub_record(record)
            assert result.is_valid, f"Format {fmt} failed: {result.violations}"


class TestFormatAdapterStubRecord:
    def test_returns_string(self):
        record = _valid_record()
        result = format_adapter_stub_record(record)
        assert isinstance(result, str)

    def test_contains_adapter_id(self):
        record = _valid_record()
        result = format_adapter_stub_record(record)
        assert "ADS-001" in result

    def test_contains_target_tool(self):
        record = _valid_record()
        result = format_adapter_stub_record(record)
        assert "ampscanner" in result

    def test_contains_output_format(self):
        record = _valid_record()
        result = format_adapter_stub_record(record)
        assert "fasta" in result

    def test_contains_status(self):
        record = _valid_record()
        result = format_adapter_stub_record(record)
        assert "stub" in result

    def test_contains_disclaimer(self):
        record = _valid_record()
        result = format_adapter_stub_record(record)
        assert "biological" in result.lower()

    def test_ends_with_newline(self):
        record = _valid_record()
        result = format_adapter_stub_record(record)
        assert result.endswith("\n")

    def test_field_mappings_shown(self):
        fm = build_adapter_field("candidate_id", "seq_id", transform="identity")
        record = build_adapter_stub_record(
            adapter_id="ADS-001",
            target_tool="ampscanner",
            output_format="fasta",
            field_mappings=[fm],
            implementation_notes="test",
        )
        result = format_adapter_stub_record(record)
        assert "candidate_id" in result
        assert "seq_id" in result

    def test_no_mappings_shows_stub_message(self):
        record = _valid_record()
        result = format_adapter_stub_record(record)
        assert "none defined" in result or "stub" in result

"""Tests for src/openamp_foundry/interop/jsonld_context.py (63 tests)."""

import json
import pytest
from openamp_foundry.interop.jsonld_context import (
    JSONLD_CONTEXT_ID_PREFIX,
    JSONLD_CONTEXT_VERSION,
    OPENAMP_NAMESPACE,
    SCHEMA_ORG_NAMESPACE,
    VALID_EVIDENCE_TYPES,
    VALID_PROOF_LADDER_LEVELS,
    REQUIRED_CERTIFICATE_FIELDS,
    JSONLD_BASE_CONTEXT,
    JsonLdContextRecord,
    JsonLdContextValidationResult,
    build_jsonld_context_record,
    validate_jsonld_context_record,
    format_jsonld_context_record,
    annotate_certificate_with_context,
)


def _valid_record(evidence_type="EvidenceCertificate"):
    return build_jsonld_context_record(
        context_id="JLC-001",
        evidence_type=evidence_type,
        generation_note="Test context",
    )


class TestConstants:
    def test_prefix(self):
        assert JSONLD_CONTEXT_ID_PREFIX == "JLC-"

    def test_context_version(self):
        assert JSONLD_CONTEXT_VERSION == "1.0"

    def test_openamp_namespace_starts_with_https(self):
        assert OPENAMP_NAMESPACE.startswith("https://")

    def test_schema_org_namespace(self):
        assert "schema.org" in SCHEMA_ORG_NAMESPACE

    def test_valid_evidence_types_is_frozenset(self):
        assert isinstance(VALID_EVIDENCE_TYPES, frozenset)

    def test_evidence_certificate_in_types(self):
        assert "EvidenceCertificate" in VALID_EVIDENCE_TYPES

    def test_batch_outcome_in_types(self):
        assert "BatchOutcomeSummary" in VALID_EVIDENCE_TYPES

    def test_negative_result_in_types(self):
        assert "NegativeResultRecord" in VALID_EVIDENCE_TYPES

    def test_benchmark_card_in_types(self):
        assert "BenchmarkCard" in VALID_EVIDENCE_TYPES

    def test_release_manifest_in_types(self):
        assert "ReleaseManifest" in VALID_EVIDENCE_TYPES

    def test_valid_proof_ladder_levels_is_frozenset(self):
        assert isinstance(VALID_PROOF_LADDER_LEVELS, frozenset)

    def test_dry_lab_candidate_in_proof_levels(self):
        assert "dry_lab_candidate" in VALID_PROOF_LADDER_LEVELS

    def test_required_certificate_fields_is_frozenset(self):
        assert isinstance(REQUIRED_CERTIFICATE_FIELDS, frozenset)

    def test_certificate_id_required(self):
        assert "certificate_id" in REQUIRED_CERTIFICATE_FIELDS

    def test_proof_ladder_level_required(self):
        assert "proof_ladder_level" in REQUIRED_CERTIFICATE_FIELDS

    def test_dry_lab_only_required(self):
        assert "dry_lab_only" in REQUIRED_CERTIFICATE_FIELDS

    def test_base_context_is_dict(self):
        assert isinstance(JSONLD_BASE_CONTEXT, dict)

    def test_base_context_has_vocab(self):
        assert "@vocab" in JSONLD_BASE_CONTEXT

    def test_base_context_has_schema(self):
        assert "schema" in JSONLD_BASE_CONTEXT

    def test_base_context_has_certificate_id(self):
        assert "certificate_id" in JSONLD_BASE_CONTEXT


class TestBuildJsonLdContextRecord:
    def test_returns_jsonld_context_record(self):
        record = _valid_record()
        assert isinstance(record, JsonLdContextRecord)

    def test_context_id_stored(self):
        record = _valid_record()
        assert record.context_id == "JLC-001"

    def test_evidence_type_stored(self):
        record = _valid_record()
        assert record.evidence_type == "EvidenceCertificate"

    def test_context_version_default(self):
        record = _valid_record()
        assert record.context_version == JSONLD_CONTEXT_VERSION

    def test_context_version_custom(self):
        record = build_jsonld_context_record(
            context_id="JLC-001",
            evidence_type="BenchmarkCard",
            context_version="2.0",
        )
        assert record.context_version == "2.0"

    def test_namespace_set(self):
        record = _valid_record()
        assert record.namespace == OPENAMP_NAMESPACE

    def test_is_dry_lab_constrained_true(self):
        record = _valid_record()
        assert record.is_dry_lab_constrained is True

    def test_generation_note_stored(self):
        record = build_jsonld_context_record(
            context_id="JLC-001",
            evidence_type="EvidenceCertificate",
            generation_note="Custom note",
        )
        assert record.generation_note == "Custom note"

    def test_generation_note_auto_generated_when_empty(self):
        record = build_jsonld_context_record(
            context_id="JLC-001",
            evidence_type="EvidenceCertificate",
        )
        assert record.generation_note != ""

    def test_context_document_contains_vocab(self):
        record = _valid_record()
        assert "@vocab" in record.context_document

    def test_extra_terms_merged(self):
        record = build_jsonld_context_record(
            context_id="JLC-001",
            evidence_type="EvidenceCertificate",
            extra_terms={"custom_field": "openamp:customField"},
        )
        assert "custom_field" in record.context_document


class TestValidateJsonLdContextRecord:
    def test_valid_record_passes(self):
        result = validate_jsonld_context_record(_valid_record())
        assert result.is_valid

    def test_returns_validation_result(self):
        result = validate_jsonld_context_record(_valid_record())
        assert isinstance(result, JsonLdContextValidationResult)

    def test_no_violations_on_valid(self):
        result = validate_jsonld_context_record(_valid_record())
        assert result.violations == []

    def test_wrong_id_prefix_fails(self):
        record = _valid_record()
        record.context_id = "CTX-001"
        result = validate_jsonld_context_record(record)
        assert not result.is_valid
        assert any("JLC-" in v for v in result.violations)

    def test_invalid_evidence_type_fails(self):
        record = _valid_record()
        record.evidence_type = "UnknownType"
        result = validate_jsonld_context_record(record)
        assert not result.is_valid
        assert any("evidence_type" in v for v in result.violations)

    def test_empty_context_version_fails(self):
        record = _valid_record()
        record.context_version = ""
        result = validate_jsonld_context_record(record)
        assert not result.is_valid
        assert any("context_version" in v for v in result.violations)

    def test_missing_vocab_fails(self):
        record = _valid_record()
        del record.context_document["@vocab"]
        result = validate_jsonld_context_record(record)
        assert not result.is_valid
        assert any("@vocab" in v for v in result.violations)

    def test_wrong_namespace_fails(self):
        record = _valid_record()
        record.namespace = "https://wrong.org/ns#"
        result = validate_jsonld_context_record(record)
        assert not result.is_valid
        assert any("namespace" in v for v in result.violations)

    def test_missing_required_fields_fails(self):
        record = _valid_record()
        del record.context_document["certificate_id"]
        result = validate_jsonld_context_record(record)
        assert not result.is_valid
        assert any("missing required" in v for v in result.violations)

    def test_dry_lab_constrained_false_fails(self):
        record = _valid_record()
        record.is_dry_lab_constrained = False
        result = validate_jsonld_context_record(record)
        assert not result.is_valid
        assert any("dry_lab_constrained" in v for v in result.violations)

    def test_empty_generation_note_fails(self):
        record = _valid_record()
        record.generation_note = ""
        result = validate_jsonld_context_record(record)
        assert not result.is_valid
        assert any("generation_note" in v for v in result.violations)

    def test_multiple_violations_accumulated(self):
        record = _valid_record()
        record.context_id = "BAD-001"
        record.evidence_type = "Unknown"
        result = validate_jsonld_context_record(record)
        assert len(result.violations) >= 2

    def test_all_valid_evidence_types_accepted(self):
        for et in VALID_EVIDENCE_TYPES:
            record = build_jsonld_context_record(
                context_id="JLC-001",
                evidence_type=et,
                generation_note="test",
            )
            result = validate_jsonld_context_record(record)
            assert result.is_valid, f"Type {et} failed: {result.violations}"


class TestFormatJsonLdContextRecord:
    def test_returns_string(self):
        record = _valid_record()
        result = format_jsonld_context_record(record)
        assert isinstance(result, str)

    def test_valid_json(self):
        record = _valid_record()
        result = format_jsonld_context_record(record)
        parsed = json.loads(result)
        assert parsed is not None

    def test_contains_context_key(self):
        record = _valid_record()
        parsed = json.loads(format_jsonld_context_record(record))
        assert "@context" in parsed

    def test_contains_meta_key(self):
        record = _valid_record()
        parsed = json.loads(format_jsonld_context_record(record))
        assert "_meta" in parsed

    def test_meta_contains_context_id(self):
        record = _valid_record()
        parsed = json.loads(format_jsonld_context_record(record))
        assert parsed["_meta"]["context_id"] == "JLC-001"

    def test_meta_contains_evidence_type(self):
        record = _valid_record()
        parsed = json.loads(format_jsonld_context_record(record))
        assert parsed["_meta"]["evidence_type"] == "EvidenceCertificate"

    def test_meta_contains_namespace(self):
        record = _valid_record()
        parsed = json.loads(format_jsonld_context_record(record))
        assert "namespace" in parsed["_meta"]

    def test_context_has_vocab(self):
        record = _valid_record()
        parsed = json.loads(format_jsonld_context_record(record))
        assert "@vocab" in parsed["@context"]


class TestAnnotateCertificateWithContext:
    def test_returns_dict(self):
        record = _valid_record()
        cert = {"certificate_id": "CERT-001"}
        result = annotate_certificate_with_context(cert, record)
        assert isinstance(result, dict)

    def test_adds_context_key(self):
        record = _valid_record()
        cert = {"certificate_id": "CERT-001"}
        result = annotate_certificate_with_context(cert, record)
        assert "@context" in result

    def test_adds_type_key(self):
        record = _valid_record()
        cert = {"certificate_id": "CERT-001"}
        result = annotate_certificate_with_context(cert, record)
        assert "@type" in result

    def test_type_matches_evidence_type(self):
        record = _valid_record("BenchmarkCard")
        cert = {}
        result = annotate_certificate_with_context(cert, record)
        assert result["@type"] == "BenchmarkCard"

    def test_original_fields_preserved(self):
        record = _valid_record()
        cert = {"certificate_id": "CERT-001", "candidate_id": "TOY-X"}
        result = annotate_certificate_with_context(cert, record)
        assert result["certificate_id"] == "CERT-001"
        assert result["candidate_id"] == "TOY-X"

    def test_does_not_mutate_original(self):
        record = _valid_record()
        cert = {"certificate_id": "CERT-001"}
        original_copy = dict(cert)
        annotate_certificate_with_context(cert, record)
        assert cert == original_copy

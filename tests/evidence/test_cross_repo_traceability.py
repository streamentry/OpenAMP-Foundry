"""Tests for src/openamp_foundry/evidence/cross_repo_traceability.py (63 tests)."""

import pytest
from openamp_foundry.evidence.cross_repo_traceability import (
    CROSS_REPO_TRACEABILITY_ID_PREFIX,
    VALID_REPO_TYPES,
    VALID_ARTIFACT_TYPES,
    VALID_TRACEABILITY_STATUSES,
    VALID_LINK_CONFIDENCE_LEVELS,
    CANONICAL_REPO_URL,
    CrossRepoArtifactRef,
    CrossRepoTraceabilityRecord,
    TraceabilityValidationResult,
    build_cross_repo_artifact_ref,
    build_cross_repo_traceability_record,
    validate_cross_repo_traceability_record,
    format_cross_repo_traceability_record,
)


def _valid_ref():
    return build_cross_repo_artifact_ref(
        artifact_id="CERT-TOY-001",
        artifact_type="evidence_certificate",
        source_repo_url="https://github.com/partner-lab/openamp-fork",
        source_repo_type="partner_lab",
        commit_sha="abc1234",
        confidence_level="medium",
        is_verified=False,
    )


def _valid_record(refs=None):
    if refs is None:
        refs = [_valid_ref()]
    return build_cross_repo_traceability_record(
        record_id="CRT-001",
        primary_artifact_id="CERT-TOY-001",
        primary_artifact_type="evidence_certificate",
        external_refs=refs,
        traceability_status="linked",
        dry_lab_only=True,
        is_example_data=True,
        traceability_note="CRT record for toy example",
    )


class TestConstants:
    def test_prefix(self):
        assert CROSS_REPO_TRACEABILITY_ID_PREFIX == "CRT-"

    def test_valid_repo_types_is_frozenset(self):
        assert isinstance(VALID_REPO_TYPES, frozenset)

    def test_primary_in_repo_types(self):
        assert "primary" in VALID_REPO_TYPES

    def test_partner_lab_in_repo_types(self):
        assert "partner_lab" in VALID_REPO_TYPES

    def test_independent_replication_in_repo_types(self):
        assert "independent_replication" in VALID_REPO_TYPES

    def test_valid_artifact_types_is_frozenset(self):
        assert isinstance(VALID_ARTIFACT_TYPES, frozenset)

    def test_evidence_certificate_in_artifact_types(self):
        assert "evidence_certificate" in VALID_ARTIFACT_TYPES

    def test_release_manifest_in_artifact_types(self):
        assert "release_manifest" in VALID_ARTIFACT_TYPES

    def test_fasta_export_in_artifact_types(self):
        assert "fasta_export" in VALID_ARTIFACT_TYPES

    def test_valid_traceability_statuses_is_frozenset(self):
        assert isinstance(VALID_TRACEABILITY_STATUSES, frozenset)

    def test_pending_in_statuses(self):
        assert "pending" in VALID_TRACEABILITY_STATUSES

    def test_verified_in_statuses(self):
        assert "verified" in VALID_TRACEABILITY_STATUSES

    def test_broken_in_statuses(self):
        assert "broken" in VALID_TRACEABILITY_STATUSES

    def test_valid_confidence_levels_is_frozenset(self):
        assert isinstance(VALID_LINK_CONFIDENCE_LEVELS, frozenset)

    def test_high_in_confidence_levels(self):
        assert "high" in VALID_LINK_CONFIDENCE_LEVELS

    def test_unverified_in_confidence_levels(self):
        assert "unverified" in VALID_LINK_CONFIDENCE_LEVELS

    def test_canonical_repo_url_is_github(self):
        assert "github.com" in CANONICAL_REPO_URL


class TestBuildCrossRepoArtifactRef:
    def test_returns_artifact_ref(self):
        ref = _valid_ref()
        assert isinstance(ref, CrossRepoArtifactRef)

    def test_artifact_id_stored(self):
        ref = _valid_ref()
        assert ref.artifact_id == "CERT-TOY-001"

    def test_artifact_type_stored(self):
        ref = _valid_ref()
        assert ref.artifact_type == "evidence_certificate"

    def test_source_repo_url_stored(self):
        ref = _valid_ref()
        assert ref.source_repo_url == "https://github.com/partner-lab/openamp-fork"

    def test_source_repo_type_stored(self):
        ref = _valid_ref()
        assert ref.source_repo_type == "partner_lab"

    def test_commit_sha_stored(self):
        ref = _valid_ref()
        assert ref.commit_sha == "abc1234"

    def test_confidence_level_stored(self):
        ref = _valid_ref()
        assert ref.confidence_level == "medium"

    def test_is_verified_default_false(self):
        ref = _valid_ref()
        assert ref.is_verified is False

    def test_verification_note_default_empty(self):
        ref = _valid_ref()
        assert ref.verification_note == ""


class TestBuildCrossRepoTraceabilityRecord:
    def test_returns_traceability_record(self):
        record = _valid_record()
        assert isinstance(record, CrossRepoTraceabilityRecord)

    def test_record_id_stored(self):
        record = _valid_record()
        assert record.record_id == "CRT-001"

    def test_primary_artifact_id_stored(self):
        record = _valid_record()
        assert record.primary_artifact_id == "CERT-TOY-001"

    def test_primary_artifact_type_stored(self):
        record = _valid_record()
        assert record.primary_artifact_type == "evidence_certificate"

    def test_total_external_repos_computed(self):
        record = _valid_record([_valid_ref(), _valid_ref()])
        assert record.total_external_repos == 2

    def test_traceability_status_stored(self):
        record = _valid_record()
        assert record.traceability_status == "linked"

    def test_dry_lab_only_stored(self):
        record = _valid_record()
        assert record.dry_lab_only is True

    def test_is_example_data_stored(self):
        record = _valid_record()
        assert record.is_example_data is True

    def test_traceability_note_auto_when_empty(self):
        record = build_cross_repo_traceability_record(
            record_id="CRT-001",
            primary_artifact_id="CERT-001",
            primary_artifact_type="evidence_certificate",
            external_refs=[_valid_ref()],
            traceability_status="pending",
        )
        assert record.traceability_note != ""


class TestValidateCrossRepoTraceabilityRecord:
    def test_valid_record_passes(self):
        result = validate_cross_repo_traceability_record(_valid_record())
        assert result.is_valid

    def test_returns_validation_result(self):
        result = validate_cross_repo_traceability_record(_valid_record())
        assert isinstance(result, TraceabilityValidationResult)

    def test_no_violations_on_valid(self):
        result = validate_cross_repo_traceability_record(_valid_record())
        assert result.violations == []

    def test_wrong_prefix_fails(self):
        record = _valid_record()
        record.record_id = "XYZ-001"
        result = validate_cross_repo_traceability_record(record)
        assert not result.is_valid
        assert any("CRT-" in v for v in result.violations)

    def test_empty_primary_artifact_id_fails(self):
        record = _valid_record()
        record.primary_artifact_id = ""
        result = validate_cross_repo_traceability_record(record)
        assert not result.is_valid

    def test_invalid_primary_artifact_type_fails(self):
        record = _valid_record()
        record.primary_artifact_type = "unknown_type"
        result = validate_cross_repo_traceability_record(record)
        assert not result.is_valid
        assert any("primary_artifact_type" in v for v in result.violations)

    def test_invalid_traceability_status_fails(self):
        record = _valid_record()
        record.traceability_status = "bogus"
        result = validate_cross_repo_traceability_record(record)
        assert not result.is_valid

    def test_total_repos_mismatch_fails(self):
        record = _valid_record()
        record.total_external_repos = 99
        result = validate_cross_repo_traceability_record(record)
        assert not result.is_valid
        assert any("total_external_repos" in v for v in result.violations)

    def test_dry_lab_false_fails(self):
        record = _valid_record()
        record.dry_lab_only = False
        result = validate_cross_repo_traceability_record(record)
        assert not result.is_valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_empty_traceability_note_fails(self):
        record = _valid_record()
        record.traceability_note = ""
        result = validate_cross_repo_traceability_record(record)
        assert not result.is_valid
        assert any("traceability_note" in v for v in result.violations)

    def test_ref_empty_artifact_id_fails(self):
        ref = _valid_ref()
        ref.artifact_id = ""
        result = validate_cross_repo_traceability_record(_valid_record([ref]))
        assert not result.is_valid

    def test_ref_invalid_artifact_type_fails(self):
        ref = _valid_ref()
        ref.artifact_type = "unknown"
        result = validate_cross_repo_traceability_record(_valid_record([ref]))
        assert not result.is_valid

    def test_ref_non_https_url_fails(self):
        ref = _valid_ref()
        ref.source_repo_url = "http://insecure.example.com/repo"
        result = validate_cross_repo_traceability_record(_valid_record([ref]))
        assert not result.is_valid
        assert any("https://" in v for v in result.violations)

    def test_ref_invalid_repo_type_fails(self):
        ref = _valid_ref()
        ref.source_repo_type = "unknown_type"
        result = validate_cross_repo_traceability_record(_valid_record([ref]))
        assert not result.is_valid

    def test_ref_empty_commit_sha_fails(self):
        ref = _valid_ref()
        ref.commit_sha = ""
        result = validate_cross_repo_traceability_record(_valid_record([ref]))
        assert not result.is_valid
        assert any("commit_sha" in v for v in result.violations)

    def test_ref_invalid_confidence_level_fails(self):
        ref = _valid_ref()
        ref.confidence_level = "very_high"
        result = validate_cross_repo_traceability_record(_valid_record([ref]))
        assert not result.is_valid

    def test_multiple_violations_accumulated(self):
        record = _valid_record()
        record.record_id = "BAD-001"
        record.primary_artifact_type = "unknown"
        result = validate_cross_repo_traceability_record(record)
        assert len(result.violations) >= 2

    def test_all_valid_artifact_types_accepted(self):
        for atype in VALID_ARTIFACT_TYPES:
            record = build_cross_repo_traceability_record(
                record_id="CRT-001",
                primary_artifact_id="CERT-001",
                primary_artifact_type=atype,
                external_refs=[_valid_ref()],
                traceability_status="pending",
                traceability_note="test",
            )
            result = validate_cross_repo_traceability_record(record)
            assert result.is_valid, f"Type {atype} failed: {result.violations}"

    def test_all_valid_confidence_levels_accepted(self):
        for level in VALID_LINK_CONFIDENCE_LEVELS:
            ref = build_cross_repo_artifact_ref(
                artifact_id="CERT-001",
                artifact_type="evidence_certificate",
                source_repo_url="https://github.com/partner/repo",
                source_repo_type="partner_lab",
                commit_sha="abc123",
                confidence_level=level,
            )
            record = _valid_record([ref])
            result = validate_cross_repo_traceability_record(record)
            assert result.is_valid, f"Level {level} failed: {result.violations}"


class TestFormatCrossRepoTraceabilityRecord:
    def test_returns_string(self):
        record = _valid_record()
        result = format_cross_repo_traceability_record(record)
        assert isinstance(result, str)

    def test_contains_record_id(self):
        record = _valid_record()
        result = format_cross_repo_traceability_record(record)
        assert "CRT-001" in result

    def test_contains_primary_artifact_id(self):
        record = _valid_record()
        result = format_cross_repo_traceability_record(record)
        assert "CERT-TOY-001" in result

    def test_contains_status(self):
        record = _valid_record()
        result = format_cross_repo_traceability_record(record)
        assert "linked" in result

    def test_contains_ref_artifact_id(self):
        record = _valid_record()
        result = format_cross_repo_traceability_record(record)
        assert "CERT-TOY-001" in result

    def test_contains_repo_url(self):
        record = _valid_record()
        result = format_cross_repo_traceability_record(record)
        assert "github.com" in result

    def test_ends_with_newline(self):
        record = _valid_record()
        result = format_cross_repo_traceability_record(record)
        assert result.endswith("\n")

    def test_verified_ref_shows_checkmark(self):
        ref = _valid_ref()
        ref.is_verified = True
        record = _valid_record([ref])
        result = format_cross_repo_traceability_record(record)
        assert "✓" in result

    def test_unverified_ref_shows_question_mark(self):
        record = _valid_record()
        result = format_cross_repo_traceability_record(record)
        assert "?" in result

"""Tests for src/openamp_foundry/export/fasta_export.py (63 tests)."""

import pytest
from openamp_foundry.export.fasta_export import (
    FASTA_EXPORT_ID_PREFIX,
    VALID_EXPORT_CONTEXTS,
    VALID_CANDIDATE_STATUSES,
    VALID_AMINO_ACIDS,
    DRY_LAB_SAFE_CONTEXTS,
    TOY_ID_PREFIXES,
    MIN_SEQUENCE_LENGTH,
    MAX_SEQUENCE_LENGTH,
    DRY_LAB_CLAIM_TERMS,
    FastaExportEntry,
    FastaExportRecord,
    FastaExportValidationResult,
    build_fasta_entry,
    build_fasta_export_record,
    validate_fasta_export_record,
    format_fasta_export,
)


def _valid_entry(candidate_id="TOY-001", sequence="ACDEFGHIKLM"):
    return build_fasta_entry(
        candidate_id=candidate_id,
        sequence=sequence,
        description="Toy AMP candidate",
        export_context="dry_lab_only",
        status="nominated",
        is_toy_data=True,
    )


def _valid_record(entries=None):
    if entries is None:
        entries = [_valid_entry()]
    return build_fasta_export_record(
        export_id="FAE-001",
        entries=entries,
        dry_lab_only=True,
        export_context="dry_lab_only",
        export_note="Computational dry-lab candidates only.",
        export_timestamp_utc="2026-01-01T00:00:00Z",
    )


class TestConstants:
    def test_prefix(self):
        assert FASTA_EXPORT_ID_PREFIX == "FAE-"

    def test_valid_export_contexts_is_frozenset(self):
        assert isinstance(VALID_EXPORT_CONTEXTS, frozenset)

    def test_valid_export_contexts_contains_dry_lab_only(self):
        assert "dry_lab_only" in VALID_EXPORT_CONTEXTS

    def test_valid_export_contexts_contains_partner_review(self):
        assert "partner_review" in VALID_EXPORT_CONTEXTS

    def test_valid_export_contexts_contains_internal_use(self):
        assert "internal_use" in VALID_EXPORT_CONTEXTS

    def test_valid_export_contexts_contains_public_release(self):
        assert "public_release" in VALID_EXPORT_CONTEXTS

    def test_valid_candidate_statuses_is_frozenset(self):
        assert isinstance(VALID_CANDIDATE_STATUSES, frozenset)

    def test_valid_candidate_statuses_contains_nominated(self):
        assert "nominated" in VALID_CANDIDATE_STATUSES

    def test_valid_candidate_statuses_contains_selected(self):
        assert "selected" in VALID_CANDIDATE_STATUSES

    def test_valid_candidate_statuses_contains_retracted(self):
        assert "retracted" in VALID_CANDIDATE_STATUSES

    def test_valid_amino_acids_is_frozenset(self):
        assert isinstance(VALID_AMINO_ACIDS, frozenset)

    def test_valid_amino_acids_has_20_standard(self):
        assert len(VALID_AMINO_ACIDS) == 20

    def test_dry_lab_safe_contexts_subset_of_valid(self):
        assert DRY_LAB_SAFE_CONTEXTS.issubset(VALID_EXPORT_CONTEXTS)

    def test_public_release_not_in_dry_lab_safe_contexts(self):
        assert "public_release" not in DRY_LAB_SAFE_CONTEXTS

    def test_toy_id_prefixes_is_frozenset(self):
        assert isinstance(TOY_ID_PREFIXES, frozenset)

    def test_toy_id_prefixes_contains_toy(self):
        assert "TOY-" in TOY_ID_PREFIXES

    def test_toy_id_prefixes_contains_mock(self):
        assert "MOCK-" in TOY_ID_PREFIXES

    def test_min_sequence_length(self):
        assert MIN_SEQUENCE_LENGTH == 5

    def test_max_sequence_length(self):
        assert MAX_SEQUENCE_LENGTH == 100

    def test_dry_lab_claim_terms_is_frozenset(self):
        assert isinstance(DRY_LAB_CLAIM_TERMS, frozenset)

    def test_dry_lab_claim_terms_contains_computational(self):
        assert "computational" in DRY_LAB_CLAIM_TERMS


class TestBuildFastaEntry:
    def test_returns_fasta_export_entry(self):
        entry = _valid_entry()
        assert isinstance(entry, FastaExportEntry)

    def test_candidate_id_stored(self):
        entry = _valid_entry(candidate_id="TOY-XYZ")
        assert entry.candidate_id == "TOY-XYZ"

    def test_sequence_uppercased(self):
        entry = build_fasta_entry(
            candidate_id="TOY-001",
            sequence="acdefg",
            description="test",
            export_context="dry_lab_only",
            status="nominated",
            is_toy_data=True,
        )
        assert entry.sequence == "ACDEFG"

    def test_description_stored(self):
        entry = build_fasta_entry(
            candidate_id="TOY-001",
            sequence="ACDEFG",
            description="My desc",
            export_context="dry_lab_only",
            status="nominated",
            is_toy_data=True,
        )
        assert entry.description == "My desc"

    def test_export_context_stored(self):
        entry = _valid_entry()
        assert entry.export_context == "dry_lab_only"

    def test_status_stored(self):
        entry = _valid_entry()
        assert entry.status == "nominated"

    def test_is_toy_data_stored(self):
        entry = _valid_entry()
        assert entry.is_toy_data is True


class TestBuildFastaExportRecord:
    def test_returns_fasta_export_record(self):
        record = _valid_record()
        assert isinstance(record, FastaExportRecord)

    def test_export_id_stored(self):
        record = _valid_record()
        assert record.export_id == "FAE-001"

    def test_total_candidates_matches_entries(self):
        entries = [_valid_entry("TOY-001"), _valid_entry("TOY-002")]
        record = _valid_record(entries=entries)
        assert record.total_candidates == 2

    def test_dry_lab_only_stored(self):
        record = _valid_record()
        assert record.dry_lab_only is True

    def test_export_context_stored(self):
        record = _valid_record()
        assert record.export_context == "dry_lab_only"

    def test_export_note_stored(self):
        record = _valid_record()
        assert "computational" in record.export_note.lower() or "dry" in record.export_note.lower()

    def test_timestamp_defaults_when_empty(self):
        record = build_fasta_export_record(
            export_id="FAE-001",
            entries=[_valid_entry()],
            dry_lab_only=True,
            export_context="dry_lab_only",
            export_note="computational",
            export_timestamp_utc="",
        )
        assert record.export_timestamp_utc != ""

    def test_entries_stored(self):
        entry = _valid_entry()
        record = _valid_record(entries=[entry])
        assert len(record.entries) == 1


class TestValidateFastaExportRecord:
    def test_valid_record_passes(self):
        result = validate_fasta_export_record(_valid_record())
        assert result.is_valid

    def test_returns_validation_result(self):
        result = validate_fasta_export_record(_valid_record())
        assert isinstance(result, FastaExportValidationResult)

    def test_no_violations_on_valid(self):
        result = validate_fasta_export_record(_valid_record())
        assert result.violations == []

    def test_wrong_id_prefix_fails(self):
        record = _valid_record()
        record.export_id = "XXX-001"
        result = validate_fasta_export_record(record)
        assert not result.is_valid
        assert any("FAE-" in v for v in result.violations)

    def test_invalid_export_context_fails(self):
        record = _valid_record()
        record.export_context = "invalid_context"
        result = validate_fasta_export_record(record)
        assert not result.is_valid

    def test_dry_lab_with_public_release_context_fails(self):
        record = _valid_record()
        record.dry_lab_only = True
        record.export_context = "public_release"
        result = validate_fasta_export_record(record)
        assert not result.is_valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_total_candidates_mismatch_fails(self):
        record = _valid_record()
        record.total_candidates = 99
        result = validate_fasta_export_record(record)
        assert not result.is_valid
        assert any("total_candidates" in v for v in result.violations)

    def test_export_note_missing_claim_term_fails(self):
        record = _valid_record()
        record.export_note = "Some note without required terms."
        result = validate_fasta_export_record(record)
        assert not result.is_valid
        assert any("export_note" in v for v in result.violations)

    def test_invalid_amino_acid_in_sequence_fails(self):
        entry = build_fasta_entry(
            candidate_id="TOY-001",
            sequence="ACDEFX",
            description="test",
            export_context="dry_lab_only",
            status="nominated",
            is_toy_data=True,
        )
        record = _valid_record(entries=[entry])
        result = validate_fasta_export_record(record)
        assert not result.is_valid
        assert any("invalid amino acid" in v for v in result.violations)

    def test_sequence_too_short_fails(self):
        entry = build_fasta_entry(
            candidate_id="TOY-001",
            sequence="ACD",
            description="test",
            export_context="dry_lab_only",
            status="nominated",
            is_toy_data=True,
        )
        record = _valid_record(entries=[entry])
        result = validate_fasta_export_record(record)
        assert not result.is_valid
        assert any("length" in v for v in result.violations)

    def test_sequence_too_long_fails(self):
        entry = build_fasta_entry(
            candidate_id="TOY-001",
            sequence="A" * 101,
            description="test",
            export_context="dry_lab_only",
            status="nominated",
            is_toy_data=True,
        )
        record = _valid_record(entries=[entry])
        result = validate_fasta_export_record(record)
        assert not result.is_valid
        assert any("length" in v for v in result.violations)

    def test_invalid_entry_export_context_fails(self):
        entry = _valid_entry()
        entry.export_context = "bogus"
        record = _valid_record(entries=[entry])
        result = validate_fasta_export_record(record)
        assert not result.is_valid

    def test_invalid_entry_status_fails(self):
        entry = _valid_entry()
        entry.status = "unknown_status"
        record = _valid_record(entries=[entry])
        result = validate_fasta_export_record(record)
        assert not result.is_valid
        assert any("status" in v for v in result.violations)

    def test_dry_lab_requires_toy_id_or_flag(self):
        entry = build_fasta_entry(
            candidate_id="REAL-001",
            sequence="ACDEFGHIKLM",
            description="test",
            export_context="dry_lab_only",
            status="nominated",
            is_toy_data=False,
        )
        record = _valid_record(entries=[entry])
        result = validate_fasta_export_record(record)
        assert not result.is_valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_dry_lab_allows_toy_id_without_flag(self):
        entry = build_fasta_entry(
            candidate_id="TOY-001",
            sequence="ACDEFGHIKLM",
            description="test",
            export_context="dry_lab_only",
            status="nominated",
            is_toy_data=False,
        )
        record = _valid_record(entries=[entry])
        result = validate_fasta_export_record(record)
        assert result.is_valid

    def test_dry_lab_allows_mock_prefix(self):
        entry = build_fasta_entry(
            candidate_id="MOCK-001",
            sequence="ACDEFGHIKLM",
            description="test",
            export_context="dry_lab_only",
            status="nominated",
            is_toy_data=False,
        )
        record = _valid_record(entries=[entry])
        result = validate_fasta_export_record(record)
        assert result.is_valid

    def test_multiple_violations_accumulated(self):
        record = _valid_record()
        record.export_id = "BAD-001"
        record.export_context = "invalid"
        result = validate_fasta_export_record(record)
        assert len(result.violations) >= 2

    def test_dry_lab_note_with_dry_lab_term(self):
        record = _valid_record()
        record.export_note = "dry-lab candidates only"
        result = validate_fasta_export_record(record)
        assert result.is_valid

    def test_in_silico_term_accepted(self):
        record = _valid_record()
        record.export_note = "in silico screening results"
        result = validate_fasta_export_record(record)
        assert result.is_valid


class TestFormatFastaExport:
    def test_returns_string(self):
        record = _valid_record()
        result = format_fasta_export(record)
        assert isinstance(result, str)

    def test_contains_export_id(self):
        record = _valid_record()
        result = format_fasta_export(record)
        assert "FAE-001" in result

    def test_contains_candidate_id(self):
        record = _valid_record()
        result = format_fasta_export(record)
        assert "TOY-001" in result

    def test_fasta_header_starts_with_gt(self):
        record = _valid_record()
        result = format_fasta_export(record)
        lines = result.splitlines()
        header_lines = [l for l in lines if l.startswith(">")]
        assert len(header_lines) >= 1

    def test_sequence_in_output(self):
        entry = _valid_entry(sequence="ACDEFGHIKLM")
        record = _valid_record(entries=[entry])
        result = format_fasta_export(record)
        assert "ACDEFGHIKLM" in result

    def test_long_sequence_wrapped_at_60(self):
        long_seq = "A" * 80
        entry = _valid_entry(sequence=long_seq)
        record = _valid_record(entries=[entry])
        result = format_fasta_export(record)
        lines = [l for l in result.splitlines() if l and not l.startswith(";") and not l.startswith(">")]
        for l in lines:
            assert len(l) <= 60

    def test_comment_lines_start_with_semicolon(self):
        record = _valid_record()
        result = format_fasta_export(record)
        comment_lines = [l for l in result.splitlines() if l.startswith(";")]
        assert len(comment_lines) >= 1

    def test_dry_lab_only_in_output(self):
        record = _valid_record()
        result = format_fasta_export(record)
        assert "dry_lab_only" in result or "True" in result

    def test_ends_with_newline(self):
        record = _valid_record()
        result = format_fasta_export(record)
        assert result.endswith("\n")

    def test_multiple_entries_produce_multiple_headers(self):
        entries = [_valid_entry("TOY-001"), _valid_entry("TOY-002")]
        record = _valid_record(entries=entries)
        result = format_fasta_export(record)
        headers = [l for l in result.splitlines() if l.startswith(">")]
        assert len(headers) == 2

    def test_header_contains_status(self):
        record = _valid_record()
        result = format_fasta_export(record)
        assert "nominated" in result

    def test_header_contains_context(self):
        record = _valid_record()
        result = format_fasta_export(record)
        assert "dry_lab_only" in result

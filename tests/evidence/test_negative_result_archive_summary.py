"""Tests for NegativeResultArchiveSummary schema — Phase F F2."""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.negative_result_archive_summary import (
    NegativeResultArchiveSummary,
    NegativeResultArchiveSummaryResult,
    validate_negative_result_archive_summary,
    validate_negative_result_archive_summary_dict,
)


def _valid_entry(**overrides) -> NegativeResultArchiveSummary:
    defaults = dict(
        nas_id="NAS-001",
        pipeline_version="v0.10.10",
        batch_id="BATCH-001",
        archive_date="2026-07-10",
        negative_result_count=3,
        negative_result_ids=["NRR-001", "NRR-002", "NRR-003"],
        completeness_confirmed=True,
        all_results_have_reason=True,
        archive_notes="Archive of batch 1 negative results.",
        reviewer="Dr. Smith",
        dry_lab_only=True,
    )
    defaults.update(overrides)
    return NegativeResultArchiveSummary(**defaults)


# ── 1. NAS ID validation ──────────────────────────────────────────────────────

class TestNasIdValidation:
    def test_valid_nas_prefix(self):
        result = validate_negative_result_archive_summary(_valid_entry())
        assert result.passed

    def test_wrong_prefix_fails(self):
        result = validate_negative_result_archive_summary(_valid_entry(nas_id="NRR-001"))
        assert not result.passed
        assert any("nas_id must start with 'NAS-'" in e for e in result.errors)

    def test_empty_nas_id_fails(self):
        result = validate_negative_result_archive_summary(_valid_entry(nas_id=""))
        assert not result.passed

    def test_lowercase_prefix_fails(self):
        result = validate_negative_result_archive_summary(_valid_entry(nas_id="nas-001"))
        assert not result.passed

    def test_nas_long_id_passes(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(nas_id="NAS-20260710-BATCH001")
        )
        assert result.passed

    def test_nas_id_in_result(self):
        result = validate_negative_result_archive_summary(_valid_entry(nas_id="NAS-XYZ"))
        assert result.nas_id == "NAS-XYZ"

    def test_no_prefix_just_number_fails(self):
        result = validate_negative_result_archive_summary(_valid_entry(nas_id="001"))
        assert not result.passed


# ── 2. Required fields validation ─────────────────────────────────────────────

class TestRequiredFields:
    def test_all_valid_passes(self):
        result = validate_negative_result_archive_summary(_valid_entry())
        assert result.passed

    def test_empty_pipeline_version_fails(self):
        result = validate_negative_result_archive_summary(_valid_entry(pipeline_version=""))
        assert not result.passed
        assert any("pipeline_version must not be empty" in e for e in result.errors)

    def test_whitespace_pipeline_version_fails(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(pipeline_version="   ")
        )
        assert not result.passed

    def test_empty_batch_id_fails(self):
        result = validate_negative_result_archive_summary(_valid_entry(batch_id=""))
        assert not result.passed
        assert any("batch_id must not be empty" in e for e in result.errors)

    def test_whitespace_batch_id_fails(self):
        result = validate_negative_result_archive_summary(_valid_entry(batch_id="  "))
        assert not result.passed

    def test_empty_reviewer_fails(self):
        result = validate_negative_result_archive_summary(_valid_entry(reviewer=""))
        assert not result.passed
        assert any("reviewer must not be empty" in e for e in result.errors)

    def test_whitespace_reviewer_fails(self):
        result = validate_negative_result_archive_summary(_valid_entry(reviewer="   "))
        assert not result.passed

    def test_multiple_empty_fields_all_reported(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(pipeline_version="", batch_id="", reviewer="")
        )
        assert not result.passed
        assert len([e for e in result.errors if "must not be empty" in e]) == 3

    def test_batch_id_in_result(self):
        result = validate_negative_result_archive_summary(_valid_entry(batch_id="BATCH-999"))
        assert result.batch_id == "BATCH-999"


# ── 3. Archive date format ────────────────────────────────────────────────────

class TestArchiveDateFormat:
    def test_valid_iso_date(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(archive_date="2026-07-10")
        )
        assert result.passed

    def test_date_without_dashes_fails(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(archive_date="20260710")
        )
        assert not result.passed
        assert any("archive_date must be ISO format" in e for e in result.errors)

    def test_slash_separator_fails(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(archive_date="2026/07/10")
        )
        assert not result.passed

    def test_empty_date_fails(self):
        result = validate_negative_result_archive_summary(_valid_entry(archive_date=""))
        assert not result.passed

    def test_partial_date_fails(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(archive_date="2026-07")
        )
        assert not result.passed

    def test_another_valid_date(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(archive_date="2025-01-15")
        )
        assert result.passed


# ── 4. Negative result count validation ───────────────────────────────────────

class TestNegativeResultCount:
    def test_count_matches_ids_passes(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(
                negative_result_count=2,
                negative_result_ids=["NRR-001", "NRR-002"],
            )
        )
        assert result.passed

    def test_count_mismatch_fails(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(
                negative_result_count=5,
                negative_result_ids=["NRR-001", "NRR-002"],
            )
        )
        assert not result.passed
        assert any("negative_result_count" in e and "does not match" in e
                   for e in result.errors)

    def test_zero_count_with_empty_ids_warns(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(negative_result_count=0, negative_result_ids=[])
        )
        assert result.passed
        assert any("0" in w for w in result.warnings)

    def test_negative_count_fails(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(
                negative_result_count=-1,
                negative_result_ids=[],
            )
        )
        assert not result.passed
        assert any("negative_result_count must be >= 0" in e for e in result.errors)

    def test_count_in_result(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(
                negative_result_count=1,
                negative_result_ids=["NRR-001"],
            )
        )
        assert result.negative_result_count == 1

    def test_large_count_warns(self):
        ids = [f"NRR-{i:03d}" for i in range(51)]
        result = validate_negative_result_archive_summary(
            _valid_entry(negative_result_count=51, negative_result_ids=ids)
        )
        assert result.passed
        assert any("exceeds" in w for w in result.warnings)


# ── 5. NRR ID prefix validation ───────────────────────────────────────────────

class TestNrrIdValidation:
    def test_all_valid_nrr_ids_pass(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(
                negative_result_count=2,
                negative_result_ids=["NRR-001", "NRR-002"],
            )
        )
        assert result.passed

    def test_wrong_prefix_in_ids_fails(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(
                negative_result_count=2,
                negative_result_ids=["NRR-001", "BAD-002"],
            )
        )
        assert not result.passed
        assert any("all negative_result_ids must start with 'NRR-'" in e
                   for e in result.errors)

    def test_empty_string_in_ids_fails(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(
                negative_result_count=2,
                negative_result_ids=["NRR-001", ""],
            )
        )
        assert not result.passed

    def test_lowercase_nrr_prefix_fails(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(
                negative_result_count=1,
                negative_result_ids=["nrr-001"],
            )
        )
        assert not result.passed

    def test_all_ids_reported_in_error(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(
                negative_result_count=2,
                negative_result_ids=["BAD-001", "ALSO-BAD"],
            )
        )
        assert not result.passed


# ── 6. Completeness confirmed ─────────────────────────────────────────────────

class TestCompletenessConfirmed:
    def test_completeness_true_passes(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(completeness_confirmed=True)
        )
        assert result.passed

    def test_completeness_false_fails(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(completeness_confirmed=False)
        )
        assert not result.passed
        assert any("completeness_confirmed must be True" in e for e in result.errors)

    def test_completeness_false_is_blocking(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(completeness_confirmed=False)
        )
        assert not result.passed

    def test_both_flags_false_both_reported(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(completeness_confirmed=False, all_results_have_reason=False)
        )
        assert not result.passed
        assert any("completeness_confirmed" in e for e in result.errors)
        assert any("all_results_have_reason" in e for e in result.errors)


# ── 7. All results have reason ────────────────────────────────────────────────

class TestAllResultsHaveReason:
    def test_all_have_reason_true_passes(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(all_results_have_reason=True)
        )
        assert result.passed

    def test_all_have_reason_false_fails(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(all_results_have_reason=False)
        )
        assert not result.passed
        assert any("all_results_have_reason must be True" in e for e in result.errors)

    def test_flag_reflected_in_pass_status(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(all_results_have_reason=False)
        )
        assert not result.passed

    def test_dry_lab_only_in_result(self):
        result = validate_negative_result_archive_summary(_valid_entry(dry_lab_only=True))
        assert result.dry_lab_only is True


# ── 8. Archive notes validation ───────────────────────────────────────────────

class TestArchiveNotes:
    def test_valid_notes_passes(self):
        result = validate_negative_result_archive_summary(
            _valid_entry(archive_notes="Batch 1 archive complete.")
        )
        assert result.passed

    def test_empty_notes_triggers_warning(self):
        result = validate_negative_result_archive_summary(_valid_entry(archive_notes=""))
        assert result.passed
        assert any("archive_notes is empty" in w for w in result.warnings)

    def test_notes_at_limit_passes(self):
        notes = "x" * 400
        result = validate_negative_result_archive_summary(_valid_entry(archive_notes=notes))
        assert result.passed

    def test_notes_over_limit_fails(self):
        notes = "x" * 401
        result = validate_negative_result_archive_summary(_valid_entry(archive_notes=notes))
        assert not result.passed
        assert any("archive_notes must be at most 400" in e for e in result.errors)

    def test_notes_just_over_limit_fails(self):
        notes = "y" * 402
        result = validate_negative_result_archive_summary(_valid_entry(archive_notes=notes))
        assert not result.passed


# ── 9. Dict-based validator ───────────────────────────────────────────────────

class TestDictValidator:
    def test_valid_dict_passes(self):
        data = {
            "nas_id": "NAS-001",
            "pipeline_version": "v0.10.10",
            "batch_id": "BATCH-001",
            "archive_date": "2026-07-10",
            "negative_result_count": 2,
            "negative_result_ids": ["NRR-001", "NRR-002"],
            "completeness_confirmed": True,
            "all_results_have_reason": True,
            "archive_notes": "Batch archive.",
            "reviewer": "Dr. Smith",
            "dry_lab_only": True,
        }
        result = validate_negative_result_archive_summary_dict(data)
        assert result.passed

    def test_dict_wrong_prefix_fails(self):
        data = {
            "nas_id": "BAD-001",
            "pipeline_version": "v0.10.10",
            "batch_id": "BATCH-001",
            "archive_date": "2026-07-10",
            "negative_result_count": 1,
            "negative_result_ids": ["NRR-001"],
            "completeness_confirmed": True,
            "all_results_have_reason": True,
            "archive_notes": "ok",
            "reviewer": "Dr. Smith",
        }
        result = validate_negative_result_archive_summary_dict(data)
        assert not result.passed

    def test_dict_completeness_false_fails(self):
        data = {
            "nas_id": "NAS-001",
            "pipeline_version": "v0.10.10",
            "batch_id": "BATCH-001",
            "archive_date": "2026-07-10",
            "negative_result_count": 1,
            "negative_result_ids": ["NRR-001"],
            "completeness_confirmed": False,
            "all_results_have_reason": True,
            "archive_notes": "ok",
            "reviewer": "Dr. Smith",
        }
        result = validate_negative_result_archive_summary_dict(data)
        assert not result.passed

    def test_dict_count_mismatch_fails(self):
        data = {
            "nas_id": "NAS-001",
            "pipeline_version": "v0.10.10",
            "batch_id": "BATCH-001",
            "archive_date": "2026-07-10",
            "negative_result_count": 5,
            "negative_result_ids": ["NRR-001"],
            "completeness_confirmed": True,
            "all_results_have_reason": True,
            "archive_notes": "ok",
            "reviewer": "Dr. Smith",
        }
        result = validate_negative_result_archive_summary_dict(data)
        assert not result.passed

    def test_dict_defaults_dry_lab_true(self):
        data = {
            "nas_id": "NAS-001",
            "pipeline_version": "v0.10.10",
            "batch_id": "BATCH-001",
            "archive_date": "2026-07-10",
            "negative_result_count": 1,
            "negative_result_ids": ["NRR-001"],
            "completeness_confirmed": True,
            "all_results_have_reason": True,
            "archive_notes": "ok",
            "reviewer": "Dr. Jones",
        }
        result = validate_negative_result_archive_summary_dict(data)
        assert result.dry_lab_only is True

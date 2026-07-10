"""Tests for FailedCandidateBatchReport schema — Phase F F4."""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.failed_candidate_batch_report import (
    FailedCandidateBatchReport,
    FailedCandidateBatchReportResult,
    validate_failed_candidate_batch_report,
    validate_failed_candidate_batch_report_dict,
)


def _valid_entry(**overrides) -> FailedCandidateBatchReport:
    defaults = dict(
        fcr_id="FCR-001",
        pipeline_version="v0.10.11",
        batch_id="BATCH-001",
        report_date="2026-07-10",
        total_candidates_screened=10,
        failed_candidate_count=4,
        failure_rate=0.4,
        top_rejection_reasons=["toxicity_risk", "low_activity_score"],
        rejection_reason_ids=["RJR-001", "RJR-002"],
        negative_result_archive_id="NAS-001",
        report_notes="Batch 1 screening summary.",
        reviewer="Dr. Smith",
        dry_lab_only=True,
    )
    defaults.update(overrides)
    return FailedCandidateBatchReport(**defaults)


# ── 1. FCR ID validation ──────────────────────────────────────────────────────

class TestFcrIdValidation:
    def test_valid_fcr_prefix(self):
        result = validate_failed_candidate_batch_report(_valid_entry())
        assert result.passed

    def test_wrong_prefix_fails(self):
        result = validate_failed_candidate_batch_report(_valid_entry(fcr_id="NAS-001"))
        assert not result.passed
        assert any("fcr_id must start with 'FCR-'" in e for e in result.errors)

    def test_empty_fcr_id_fails(self):
        result = validate_failed_candidate_batch_report(_valid_entry(fcr_id=""))
        assert not result.passed

    def test_lowercase_prefix_fails(self):
        result = validate_failed_candidate_batch_report(_valid_entry(fcr_id="fcr-001"))
        assert not result.passed

    def test_fcr_long_id_passes(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(fcr_id="FCR-20260710-BATCH001")
        )
        assert result.passed

    def test_fcr_id_in_result(self):
        result = validate_failed_candidate_batch_report(_valid_entry(fcr_id="FCR-XYZ"))
        assert result.fcr_id == "FCR-XYZ"

    def test_no_prefix_fails(self):
        result = validate_failed_candidate_batch_report(_valid_entry(fcr_id="001"))
        assert not result.passed


# ── 2. Required fields ────────────────────────────────────────────────────────

class TestRequiredFields:
    def test_all_valid_passes(self):
        result = validate_failed_candidate_batch_report(_valid_entry())
        assert result.passed

    def test_empty_pipeline_version_fails(self):
        result = validate_failed_candidate_batch_report(_valid_entry(pipeline_version=""))
        assert not result.passed
        assert any("pipeline_version must not be empty" in e for e in result.errors)

    def test_whitespace_pipeline_fails(self):
        result = validate_failed_candidate_batch_report(_valid_entry(pipeline_version="  "))
        assert not result.passed

    def test_empty_batch_id_fails(self):
        result = validate_failed_candidate_batch_report(_valid_entry(batch_id=""))
        assert not result.passed
        assert any("batch_id must not be empty" in e for e in result.errors)

    def test_empty_reviewer_fails(self):
        result = validate_failed_candidate_batch_report(_valid_entry(reviewer=""))
        assert not result.passed
        assert any("reviewer must not be empty" in e for e in result.errors)

    def test_multiple_empty_fields_all_reported(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(pipeline_version="", batch_id="", reviewer="")
        )
        assert not result.passed
        assert len([e for e in result.errors if "must not be empty" in e]) == 3

    def test_batch_id_in_result(self):
        result = validate_failed_candidate_batch_report(_valid_entry(batch_id="BATCH-999"))
        assert result.batch_id == "BATCH-999"


# ── 3. Report date format ─────────────────────────────────────────────────────

class TestReportDateFormat:
    def test_valid_iso_date(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(report_date="2026-07-10")
        )
        assert result.passed

    def test_date_without_dashes_fails(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(report_date="20260710")
        )
        assert not result.passed
        assert any("report_date must be ISO format" in e for e in result.errors)

    def test_slash_date_fails(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(report_date="2026/07/10")
        )
        assert not result.passed

    def test_empty_date_fails(self):
        result = validate_failed_candidate_batch_report(_valid_entry(report_date=""))
        assert not result.passed

    def test_another_valid_date(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(report_date="2025-12-01")
        )
        assert result.passed


# ── 4. Candidate count validation ─────────────────────────────────────────────

class TestCandidateCountValidation:
    def test_valid_counts_pass(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(total_candidates_screened=10, failed_candidate_count=5,
                         failure_rate=0.5)
        )
        assert result.passed

    def test_total_screened_zero_fails(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(total_candidates_screened=0, failed_candidate_count=0,
                         failure_rate=0.0)
        )
        assert not result.passed
        assert any("total_candidates_screened must be >= 1" in e for e in result.errors)

    def test_total_screened_negative_fails(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(total_candidates_screened=-1, failed_candidate_count=0,
                         failure_rate=0.0)
        )
        assert not result.passed

    def test_failed_exceeds_total_fails(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(total_candidates_screened=5, failed_candidate_count=10,
                         failure_rate=1.0)
        )
        assert not result.passed
        assert any("cannot exceed" in e for e in result.errors)

    def test_failed_negative_fails(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(total_candidates_screened=5, failed_candidate_count=-1,
                         failure_rate=0.0)
        )
        assert not result.passed

    def test_zero_failures_passes(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(total_candidates_screened=10, failed_candidate_count=0,
                         failure_rate=0.0)
        )
        assert result.passed

    def test_count_in_result(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(total_candidates_screened=20, failed_candidate_count=8,
                         failure_rate=0.4)
        )
        assert result.total_candidates_screened == 20
        assert result.failed_candidate_count == 8


# ── 5. Failure rate validation ────────────────────────────────────────────────

class TestFailureRateValidation:
    def test_valid_rate_passes(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(total_candidates_screened=10, failed_candidate_count=4,
                         failure_rate=0.4)
        )
        assert result.passed

    def test_rate_below_zero_fails(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(failure_rate=-0.1)
        )
        assert not result.passed
        assert any("failure_rate must be in [0.0, 1.0]" in e for e in result.errors)

    def test_rate_above_one_fails(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(failure_rate=1.1)
        )
        assert not result.passed

    def test_rate_inconsistent_with_counts_fails(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(total_candidates_screened=10, failed_candidate_count=4,
                         failure_rate=0.7)
        )
        assert not result.passed
        assert any("inconsistent" in e for e in result.errors)

    def test_rate_exact_match_passes(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(total_candidates_screened=4, failed_candidate_count=1,
                         failure_rate=0.25)
        )
        assert result.passed

    def test_rate_within_tolerance_passes(self):
        # 1/3 = 0.3333..., 0.333 is within 0.01 tolerance
        result = validate_failed_candidate_batch_report(
            _valid_entry(total_candidates_screened=3, failed_candidate_count=1,
                         failure_rate=0.333)
        )
        assert result.passed

    def test_all_fail_warns(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(total_candidates_screened=5, failed_candidate_count=5,
                         failure_rate=1.0)
        )
        assert result.passed
        assert any("1.0" in w for w in result.warnings)

    def test_rate_in_result(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(total_candidates_screened=10, failed_candidate_count=3,
                         failure_rate=0.3)
        )
        assert result.failure_rate == 0.3


# ── 6. Top rejection reasons validation ───────────────────────────────────────

class TestTopRejectionReasonsValidation:
    def test_valid_reasons_pass(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(top_rejection_reasons=["toxicity_risk", "hemolysis_risk"])
        )
        assert result.passed

    def test_invalid_reason_fails(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(top_rejection_reasons=["bad_reason"])
        )
        assert not result.passed
        assert any("top_rejection_reasons contains invalid" in e for e in result.errors)

    def test_empty_reasons_list_passes(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(top_rejection_reasons=[])
        )
        assert result.passed

    def test_all_valid_reasons_accepted(self):
        all_reasons = [
            "low_activity_score", "hemolysis_risk", "toxicity_risk",
            "insufficient_novelty", "data_quality_failure", "safety_policy_block",
            "duplicate", "out_of_scope", "manual_exclusion",
        ]
        result = validate_failed_candidate_batch_report(
            _valid_entry(top_rejection_reasons=all_reasons)
        )
        assert result.passed

    def test_mixed_valid_invalid_fails(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(top_rejection_reasons=["toxicity_risk", "unknown_reason"])
        )
        assert not result.passed


# ── 7. RJR ID and NAS ID linking ──────────────────────────────────────────────

class TestArtifactLinking:
    def test_valid_rjr_ids_pass(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(rejection_reason_ids=["RJR-001", "RJR-002"])
        )
        assert result.passed

    def test_wrong_rjr_prefix_fails(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(rejection_reason_ids=["BAD-001"])
        )
        assert not result.passed
        assert any("all rejection_reason_ids must start with 'RJR-'" in e
                   for e in result.errors)

    def test_empty_rjr_ids_warns(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(rejection_reason_ids=[])
        )
        assert result.passed
        assert any("rejection_reason_ids is empty" in w for w in result.warnings)

    def test_valid_nas_id_passes(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(negative_result_archive_id="NAS-001")
        )
        assert result.passed

    def test_wrong_nas_prefix_fails(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(negative_result_archive_id="WRONG-001")
        )
        assert not result.passed
        assert any("negative_result_archive_id must start with 'NAS-'" in e
                   for e in result.errors)

    def test_empty_nas_id_warns(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(negative_result_archive_id="")
        )
        assert result.passed
        assert any("negative_result_archive_id is empty" in w for w in result.warnings)

    def test_empty_report_notes_warns(self):
        result = validate_failed_candidate_batch_report(_valid_entry(report_notes=""))
        assert result.passed
        assert any("report_notes is empty" in w for w in result.warnings)


# ── 8. Report notes length ────────────────────────────────────────────────────

class TestReportNotesLength:
    def test_valid_notes_passes(self):
        result = validate_failed_candidate_batch_report(
            _valid_entry(report_notes="Batch had 40% failure rate.")
        )
        assert result.passed

    def test_notes_at_limit_passes(self):
        notes = "x" * 400
        result = validate_failed_candidate_batch_report(_valid_entry(report_notes=notes))
        assert result.passed

    def test_notes_over_limit_fails(self):
        notes = "x" * 401
        result = validate_failed_candidate_batch_report(_valid_entry(report_notes=notes))
        assert not result.passed
        assert any("report_notes must be at most 400" in e for e in result.errors)

    def test_notes_just_over_limit_fails(self):
        notes = "y" * 402
        result = validate_failed_candidate_batch_report(_valid_entry(report_notes=notes))
        assert not result.passed


# ── 9. Dict-based validator ───────────────────────────────────────────────────

class TestDictValidator:
    def test_valid_dict_passes(self):
        data = {
            "fcr_id": "FCR-001",
            "pipeline_version": "v0.10.11",
            "batch_id": "BATCH-001",
            "report_date": "2026-07-10",
            "total_candidates_screened": 10,
            "failed_candidate_count": 4,
            "failure_rate": 0.4,
            "top_rejection_reasons": ["toxicity_risk"],
            "rejection_reason_ids": ["RJR-001"],
            "negative_result_archive_id": "NAS-001",
            "report_notes": "Batch summary.",
            "reviewer": "Dr. Smith",
            "dry_lab_only": True,
        }
        result = validate_failed_candidate_batch_report_dict(data)
        assert result.passed

    def test_dict_wrong_prefix_fails(self):
        data = {
            "fcr_id": "BAD-001",
            "pipeline_version": "v0.10.11",
            "batch_id": "BATCH-001",
            "report_date": "2026-07-10",
            "total_candidates_screened": 5,
            "failed_candidate_count": 2,
            "failure_rate": 0.4,
            "top_rejection_reasons": [],
            "rejection_reason_ids": [],
            "negative_result_archive_id": "NAS-001",
            "report_notes": "ok",
            "reviewer": "Dr. Smith",
        }
        result = validate_failed_candidate_batch_report_dict(data)
        assert not result.passed

    def test_dict_inconsistent_rate_fails(self):
        data = {
            "fcr_id": "FCR-001",
            "pipeline_version": "v0.10.11",
            "batch_id": "BATCH-001",
            "report_date": "2026-07-10",
            "total_candidates_screened": 10,
            "failed_candidate_count": 4,
            "failure_rate": 0.9,
            "top_rejection_reasons": [],
            "rejection_reason_ids": [],
            "negative_result_archive_id": "NAS-001",
            "report_notes": "ok",
            "reviewer": "Dr. Smith",
        }
        result = validate_failed_candidate_batch_report_dict(data)
        assert not result.passed

    def test_dict_defaults_dry_lab_true(self):
        data = {
            "fcr_id": "FCR-001",
            "pipeline_version": "v0.10.11",
            "batch_id": "BATCH-001",
            "report_date": "2026-07-10",
            "total_candidates_screened": 5,
            "failed_candidate_count": 2,
            "failure_rate": 0.4,
            "top_rejection_reasons": [],
            "rejection_reason_ids": [],
            "negative_result_archive_id": "NAS-001",
            "report_notes": "ok",
            "reviewer": "Dr. Jones",
        }
        result = validate_failed_candidate_batch_report_dict(data)
        assert result.dry_lab_only is True

    def test_dict_multiple_errors(self):
        data = {
            "fcr_id": "BAD",
            "pipeline_version": "",
            "batch_id": "",
            "report_date": "not-a-date",
            "total_candidates_screened": 0,
            "failed_candidate_count": -1,
            "failure_rate": 2.0,
            "top_rejection_reasons": ["invalid_reason"],
            "rejection_reason_ids": ["BAD-001"],
            "negative_result_archive_id": "WRONG-001",
            "report_notes": "",
            "reviewer": "",
        }
        result = validate_failed_candidate_batch_report_dict(data)
        assert not result.passed
        assert len(result.errors) >= 5

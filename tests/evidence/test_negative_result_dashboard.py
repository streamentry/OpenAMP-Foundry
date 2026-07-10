"""Tests for NegativeResultDashboard (NRD-) schema — Phase F F9."""

import pytest
from openamp_foundry.evidence.negative_result_dashboard import (
    HIGH_REJECTION_RATE_WARNING,
    NRD_PREFIX,
    NOTES_MAX_LENGTH,
    REJECTION_RATE_TOLERANCE,
    SUMMARY_MAX_LENGTH,
    VALID_REJECTION_REASONS,
    VALID_REJECTION_STAGES,
    NegativeResultDashboard,
    NegativeResultDashboardResult,
    validate,
    validate_dict,
)


def _make(**kwargs) -> NegativeResultDashboard:
    defaults = dict(
        nrd_id="NRD-001",
        pipeline_version="v0.10.20",
        batch_id="BATCH-007",
        report_date="2026-07-10",
        total_candidates_evaluated=20,
        total_rejections=14,
        rejection_rate=0.7,
        top_rejection_stage="toxicity_screen",
        top_rejection_reason="failed_toxicity",
        high_confidence_rejections=10,
        all_rejections_have_nrr=True,
        summary="14/20 candidates rejected; toxicity screen most common failure stage.",
        notes="",
    )
    defaults.update(kwargs)
    return NegativeResultDashboard(**defaults)


# --- Baseline valid ---

class TestValidBaseline:
    def test_valid_dashboard_passes(self):
        r = validate(_make())
        assert r.valid
        assert r.errors == []

    def test_valid_returns_result_type(self):
        r = validate(_make())
        assert isinstance(r, NegativeResultDashboardResult)

    def test_valid_with_notes(self):
        r = validate(_make(notes="Pipeline reviewed by calibration team."))
        assert r.valid

    def test_valid_zero_rejections(self):
        r = validate(_make(
            total_rejections=0,
            rejection_rate=0.0,
            high_confidence_rejections=0,
            summary="No rejections in this batch; all candidates passed.",
        ))
        assert r.valid

    def test_valid_all_stages(self):
        for stage in VALID_REJECTION_STAGES:
            r = validate(_make(top_rejection_stage=stage))
            assert r.valid or all("top_rejection_stage" not in e for e in r.errors)

    def test_valid_all_reasons(self):
        for reason in VALID_REJECTION_REASONS:
            r = validate(_make(top_rejection_reason=reason))
            assert r.valid or all("top_rejection_reason" not in e for e in r.errors)


# --- nrd_id validation ---

class TestNrdIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(nrd_id="NRR-001"))
        assert not r.valid
        assert any("nrd_id" in e for e in r.errors)

    def test_empty_id(self):
        r = validate(_make(nrd_id=""))
        assert not r.valid

    def test_lowercase_prefix(self):
        r = validate(_make(nrd_id="nrd-001"))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(nrd_id="NRD-999"))
        assert r.valid


# --- pipeline_version validation ---

class TestPipelineVersionValidation:
    def test_empty_fails(self):
        r = validate(_make(pipeline_version=""))
        assert not r.valid
        assert any("pipeline_version" in e for e in r.errors)

    def test_whitespace_fails(self):
        r = validate(_make(pipeline_version="   "))
        assert not r.valid

    def test_valid(self):
        r = validate(_make(pipeline_version="v2.0.0"))
        assert r.valid


# --- batch_id validation ---

class TestBatchIdValidation:
    def test_empty_fails(self):
        r = validate(_make(batch_id=""))
        assert not r.valid
        assert any("batch_id" in e for e in r.errors)

    def test_whitespace_fails(self):
        r = validate(_make(batch_id="  "))
        assert not r.valid

    def test_valid(self):
        r = validate(_make(batch_id="BATCH-999"))
        assert r.valid


# --- report_date validation ---

class TestReportDateValidation:
    def test_valid_date(self):
        r = validate(_make(report_date="2026-01-15"))
        assert r.valid

    def test_invalid_format(self):
        r = validate(_make(report_date="10/07/2026"))
        assert not r.valid
        assert any("report_date" in e for e in r.errors)

    def test_empty_fails(self):
        r = validate(_make(report_date=""))
        assert not r.valid

    def test_partial_date_fails(self):
        r = validate(_make(report_date="2026-07"))
        assert not r.valid

    def test_text_date_fails(self):
        r = validate(_make(report_date="July 2026"))
        assert not r.valid


# --- total_candidates_evaluated validation ---

class TestCandidatesEvaluatedValidation:
    def test_zero_fails(self):
        r = validate(_make(total_candidates_evaluated=0))
        assert not r.valid
        assert any("total_candidates_evaluated" in e for e in r.errors)

    def test_negative_fails(self):
        r = validate(_make(total_candidates_evaluated=-1))
        assert not r.valid

    def test_one_passes(self):
        r = validate(_make(
            total_candidates_evaluated=1,
            total_rejections=1,
            rejection_rate=1.0,
            high_confidence_rejections=1,
        ))
        assert r.valid


# --- total_rejections validation ---

class TestTotalRejectionsValidation:
    def test_negative_fails(self):
        r = validate(_make(total_rejections=-1, rejection_rate=0.0))
        assert not r.valid
        assert any("total_rejections" in e for e in r.errors)

    def test_exceeds_evaluated_fails(self):
        r = validate(_make(total_rejections=21, rejection_rate=1.0))
        assert not r.valid
        assert any("exceed" in e or "total_rejections" in e for e in r.errors)

    def test_zero_rejections_passes(self):
        r = validate(_make(
            total_rejections=0,
            rejection_rate=0.0,
            high_confidence_rejections=0,
            summary="No rejections.",
        ))
        assert r.valid


# --- rejection_rate validation ---

class TestRejectionRateValidation:
    def test_negative_fails(self):
        r = validate(_make(rejection_rate=-0.1))
        assert not r.valid

    def test_above_one_fails(self):
        r = validate(_make(rejection_rate=1.1))
        assert not r.valid

    def test_inconsistent_fails(self):
        r = validate(_make(
            total_candidates_evaluated=20,
            total_rejections=14,
            rejection_rate=0.5,
        ))
        assert not r.valid
        assert any("inconsistent" in e for e in r.errors)

    def test_consistent_passes(self):
        r = validate(_make(
            total_candidates_evaluated=20,
            total_rejections=10,
            rejection_rate=0.5,
        ))
        assert r.valid

    def test_within_tolerance_passes(self):
        r = validate(_make(
            total_candidates_evaluated=20,
            total_rejections=14,
            rejection_rate=0.701,
        ))
        assert r.valid


# --- stage and reason validation ---

class TestStageReasonValidation:
    def test_invalid_stage(self):
        r = validate(_make(top_rejection_stage="unknown_stage"))
        assert not r.valid
        assert any("top_rejection_stage" in e for e in r.errors)

    def test_empty_stage(self):
        r = validate(_make(top_rejection_stage=""))
        assert not r.valid

    def test_invalid_reason(self):
        r = validate(_make(top_rejection_reason="unknown_reason"))
        assert not r.valid
        assert any("top_rejection_reason" in e for e in r.errors)

    def test_empty_reason(self):
        r = validate(_make(top_rejection_reason=""))
        assert not r.valid

    def test_all_valid_stages(self):
        for stage in VALID_REJECTION_STAGES:
            r = validate(_make(top_rejection_stage=stage))
            assert not any("top_rejection_stage" in e for e in r.errors)

    def test_all_valid_reasons(self):
        for reason in VALID_REJECTION_REASONS:
            r = validate(_make(top_rejection_reason=reason))
            assert not any("top_rejection_reason" in e for e in r.errors)


# --- high_confidence_rejections validation ---

class TestHighConfidenceRejectionsValidation:
    def test_negative_fails(self):
        r = validate(_make(high_confidence_rejections=-1))
        assert not r.valid
        assert any("high_confidence" in e for e in r.errors)

    def test_exceeds_total_fails(self):
        r = validate(_make(high_confidence_rejections=15))
        assert not r.valid
        assert any("exceed" in e or "high_confidence" in e for e in r.errors)

    def test_zero_passes(self):
        r = validate(_make(high_confidence_rejections=0))
        assert r.valid

    def test_equal_to_total_passes(self):
        r = validate(_make(high_confidence_rejections=14))
        assert r.valid


# --- all_rejections_have_nrr validation ---

class TestAllRejectionsHaveNrrValidation:
    def test_false_fails(self):
        r = validate(_make(all_rejections_have_nrr=False))
        assert not r.valid
        assert any("all_rejections_have_nrr" in e for e in r.errors)

    def test_true_passes(self):
        r = validate(_make(all_rejections_have_nrr=True))
        assert r.valid or all("nrr" not in e for e in r.errors)


# --- summary validation ---

class TestSummaryValidation:
    def test_empty_fails(self):
        r = validate(_make(summary=""))
        assert not r.valid
        assert any("summary" in e for e in r.errors)

    def test_whitespace_fails(self):
        r = validate(_make(summary="   "))
        assert not r.valid

    def test_too_long_fails(self):
        r = validate(_make(summary="x" * (SUMMARY_MAX_LENGTH + 1)))
        assert not r.valid
        assert any("summary" in e for e in r.errors)

    def test_at_max_passes(self):
        r = validate(_make(summary="x" * SUMMARY_MAX_LENGTH))
        assert r.valid

    def test_short_passes(self):
        r = validate(_make(summary="14/20 rejected at toxicity screen."))
        assert r.valid


# --- notes validation ---

class TestNotesValidation:
    def test_empty_valid(self):
        r = validate(_make(notes=""))
        assert r.valid

    def test_too_long_fails(self):
        r = validate(_make(notes="x" * (NOTES_MAX_LENGTH + 1)))
        assert not r.valid
        assert any("notes" in e for e in r.errors)

    def test_at_max_passes(self):
        r = validate(_make(notes="x" * NOTES_MAX_LENGTH))
        assert r.valid


# --- Warnings ---

class TestWarnings:
    def test_high_rejection_rate_warns(self):
        r = validate(_make(
            total_rejections=18,
            rejection_rate=0.9,
            high_confidence_rejections=10,
        ))
        assert any("unusually high" in w or "rejection_rate" in w for w in r.warnings)

    def test_all_rejected_warns(self):
        r = validate(_make(
            total_rejections=20,
            rejection_rate=1.0,
            high_confidence_rejections=14,
            summary="All candidates rejected.",
        ))
        assert any("all candidates" in w or "total_rejections" in w or "systematic" in w for w in r.warnings)

    def test_empty_notes_warns(self):
        r = validate(_make(notes=""))
        assert any("notes" in w or "context" in w for w in r.warnings)

    def test_no_warnings_in_clean_entry(self):
        r = validate(_make(notes="clean", rejection_rate=0.7))
        assert r.warnings == []

    def test_reasonable_rate_no_warn(self):
        r = validate(_make(notes="ok", rejection_rate=0.7))
        assert not any("unusually high" in w for w in r.warnings)


# --- validate_dict ---

class TestValidateDict:
    def _valid_dict(self, **kwargs):
        d = dict(
            nrd_id="NRD-001",
            pipeline_version="v0.10.20",
            batch_id="BATCH-007",
            report_date="2026-07-10",
            total_candidates_evaluated=20,
            total_rejections=14,
            rejection_rate=0.7,
            top_rejection_stage="toxicity_screen",
            top_rejection_reason="failed_toxicity",
            high_confidence_rejections=10,
            all_rejections_have_nrr=True,
            summary="14/20 candidates rejected at toxicity screen.",
            notes="",
        )
        d.update(kwargs)
        return d

    def test_valid_dict_passes(self):
        r = validate_dict(self._valid_dict())
        assert r.valid

    def test_invalid_prefix_fails(self):
        r = validate_dict(self._valid_dict(nrd_id="NRR-001"))
        assert not r.valid

    def test_empty_dict_fails(self):
        r = validate_dict({})
        assert not r.valid

    def test_false_nrr_fails(self):
        r = validate_dict(self._valid_dict(all_rejections_have_nrr=False))
        assert not r.valid

    def test_inconsistent_rate_fails(self):
        r = validate_dict(self._valid_dict(total_rejections=14, rejection_rate=0.5))
        assert not r.valid


# --- Constants ---

class TestConstants:
    def test_nrd_prefix(self):
        assert NRD_PREFIX == "NRD-"

    def test_valid_stages_count(self):
        assert len(VALID_REJECTION_STAGES) == 7

    def test_valid_reasons_count(self):
        assert len(VALID_REJECTION_REASONS) == 9

    def test_rejection_rate_tolerance(self):
        assert REJECTION_RATE_TOLERANCE == 0.01

    def test_high_rejection_rate_warning(self):
        assert HIGH_REJECTION_RATE_WARNING == 0.8

    def test_summary_max_length(self):
        assert SUMMARY_MAX_LENGTH == 400

    def test_notes_max_length(self):
        assert NOTES_MAX_LENGTH == 300

"""Tests for RejectionReasonEntry schema — Phase F F3."""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.rejection_reason_entry import (
    RejectionReasonEntry,
    RejectionReasonResult,
    validate_rejection_reason,
    validate_rejection_reason_dict,
)


def _valid_entry(**overrides) -> RejectionReasonEntry:
    defaults = dict(
        rjr_id="RJR-001",
        pipeline_version="v0.10.9",
        candidate_id="CAND-001",
        rejection_stage="toxicity_screen",
        rejection_reason="toxicity_risk",
        rejection_confidence="high",
        rejection_date="2026-07-10",
        borderline=False,
        reviewer="Dr. Smith",
        rejection_notes="Predicted cytotoxicity above threshold.",
        dry_lab_only=True,
    )
    defaults.update(overrides)
    return RejectionReasonEntry(**defaults)


# ── 1. RJR ID validation ──────────────────────────────────────────────────────

class TestRjrIdValidation:
    def test_valid_rjr_prefix(self):
        result = validate_rejection_reason(_valid_entry())
        assert result.passed

    def test_wrong_prefix_fails(self):
        result = validate_rejection_reason(_valid_entry(rjr_id="RRF-001"))
        assert not result.passed
        assert any("rjr_id must start with 'RJR-'" in e for e in result.errors)

    def test_empty_rjr_id_fails(self):
        result = validate_rejection_reason(_valid_entry(rjr_id=""))
        assert not result.passed

    def test_lowercase_prefix_fails(self):
        result = validate_rejection_reason(_valid_entry(rjr_id="rjr-001"))
        assert not result.passed

    def test_rjr_prefix_long_id_passes(self):
        result = validate_rejection_reason(_valid_entry(rjr_id="RJR-20260710-CAND001"))
        assert result.passed

    def test_rjr_id_in_result(self):
        result = validate_rejection_reason(_valid_entry(rjr_id="RJR-XYZ"))
        assert result.rjr_id == "RJR-XYZ"

    def test_no_prefix_fails(self):
        result = validate_rejection_reason(_valid_entry(rjr_id="001"))
        assert not result.passed


# ── 2. Required fields validation ─────────────────────────────────────────────

class TestRequiredFields:
    def test_all_valid_passes(self):
        result = validate_rejection_reason(_valid_entry())
        assert result.passed

    def test_empty_pipeline_version_fails(self):
        result = validate_rejection_reason(_valid_entry(pipeline_version=""))
        assert not result.passed
        assert any("pipeline_version must not be empty" in e for e in result.errors)

    def test_whitespace_pipeline_version_fails(self):
        result = validate_rejection_reason(_valid_entry(pipeline_version="   "))
        assert not result.passed

    def test_empty_candidate_id_fails(self):
        result = validate_rejection_reason(_valid_entry(candidate_id=""))
        assert not result.passed
        assert any("candidate_id must not be empty" in e for e in result.errors)

    def test_whitespace_candidate_id_fails(self):
        result = validate_rejection_reason(_valid_entry(candidate_id="  "))
        assert not result.passed

    def test_empty_reviewer_fails(self):
        result = validate_rejection_reason(_valid_entry(reviewer=""))
        assert not result.passed
        assert any("reviewer must not be empty" in e for e in result.errors)

    def test_whitespace_reviewer_fails(self):
        result = validate_rejection_reason(_valid_entry(reviewer="  "))
        assert not result.passed

    def test_multiple_empty_fields_all_reported(self):
        result = validate_rejection_reason(
            _valid_entry(pipeline_version="", candidate_id="", reviewer="")
        )
        assert not result.passed
        assert len([e for e in result.errors if "must not be empty" in e]) == 3

    def test_candidate_id_in_result(self):
        result = validate_rejection_reason(_valid_entry(candidate_id="CAND-999"))
        assert result.candidate_id == "CAND-999"


# ── 3. Rejection stage validation ─────────────────────────────────────────────

class TestRejectionStageValidation:
    def test_initial_screen_passes(self):
        result = validate_rejection_reason(
            _valid_entry(rejection_stage="initial_screen", rejection_reason="low_activity_score")
        )
        assert result.passed

    def test_toxicity_screen_passes(self):
        result = validate_rejection_reason(_valid_entry(rejection_stage="toxicity_screen"))
        assert result.passed

    def test_hemolysis_screen_passes(self):
        result = validate_rejection_reason(
            _valid_entry(rejection_stage="hemolysis_screen", rejection_reason="hemolysis_risk")
        )
        assert result.passed

    def test_novelty_filter_passes(self):
        result = validate_rejection_reason(
            _valid_entry(rejection_stage="novelty_filter", rejection_reason="insufficient_novelty")
        )
        assert result.passed

    def test_selection_gate_passes(self):
        result = validate_rejection_reason(
            _valid_entry(rejection_stage="selection_gate", rejection_reason="data_quality_failure")
        )
        assert result.passed

    def test_safety_policy_block_passes(self):
        result = validate_rejection_reason(
            _valid_entry(
                rejection_stage="safety_policy_block",
                rejection_reason="safety_policy_block",
                rejection_notes="Triggered dual-use screen.",
            )
        )
        assert result.passed

    def test_manual_exclusion_stage_passes(self):
        result = validate_rejection_reason(
            _valid_entry(
                rejection_stage="manual_exclusion",
                rejection_reason="manual_exclusion",
                rejection_notes="Excluded by PI.",
            )
        )
        assert result.passed

    def test_invalid_stage_fails(self):
        result = validate_rejection_reason(_valid_entry(rejection_stage="unknown_phase"))
        assert not result.passed
        assert any("rejection_stage must be one of" in e for e in result.errors)

    def test_empty_stage_fails(self):
        result = validate_rejection_reason(_valid_entry(rejection_stage=""))
        assert not result.passed

    def test_stage_in_result(self):
        result = validate_rejection_reason(_valid_entry(rejection_stage="hemolysis_screen",
                                                        rejection_reason="hemolysis_risk"))
        assert result.rejection_stage == "hemolysis_screen"


# ── 4. Rejection reason validation ────────────────────────────────────────────

class TestRejectionReasonValidation:
    def test_low_activity_score_passes(self):
        result = validate_rejection_reason(
            _valid_entry(rejection_reason="low_activity_score", rejection_stage="initial_screen")
        )
        assert result.passed

    def test_hemolysis_risk_passes(self):
        result = validate_rejection_reason(
            _valid_entry(rejection_reason="hemolysis_risk", rejection_stage="hemolysis_screen")
        )
        assert result.passed

    def test_toxicity_risk_passes(self):
        result = validate_rejection_reason(_valid_entry(rejection_reason="toxicity_risk"))
        assert result.passed

    def test_insufficient_novelty_passes(self):
        result = validate_rejection_reason(
            _valid_entry(rejection_reason="insufficient_novelty", rejection_stage="novelty_filter")
        )
        assert result.passed

    def test_data_quality_failure_passes(self):
        result = validate_rejection_reason(
            _valid_entry(rejection_reason="data_quality_failure", rejection_stage="selection_gate")
        )
        assert result.passed

    def test_duplicate_passes(self):
        result = validate_rejection_reason(
            _valid_entry(rejection_reason="duplicate", rejection_stage="novelty_filter")
        )
        assert result.passed

    def test_out_of_scope_passes(self):
        result = validate_rejection_reason(
            _valid_entry(rejection_reason="out_of_scope", rejection_stage="manual_exclusion",
                         rejection_notes="Outside scope of current pilot.")
        )
        assert result.passed

    def test_invalid_reason_fails(self):
        result = validate_rejection_reason(_valid_entry(rejection_reason="too_boring"))
        assert not result.passed
        assert any("rejection_reason must be one of" in e for e in result.errors)

    def test_empty_reason_fails(self):
        result = validate_rejection_reason(_valid_entry(rejection_reason=""))
        assert not result.passed

    def test_reason_in_result(self):
        result = validate_rejection_reason(
            _valid_entry(rejection_reason="duplicate", rejection_stage="novelty_filter")
        )
        assert result.rejection_reason == "duplicate"


# ── 5. Rejection confidence validation ────────────────────────────────────────

class TestRejectionConfidenceValidation:
    def test_high_confidence_passes(self):
        result = validate_rejection_reason(_valid_entry(rejection_confidence="high"))
        assert result.passed

    def test_medium_confidence_passes(self):
        result = validate_rejection_reason(_valid_entry(rejection_confidence="medium"))
        assert result.passed

    def test_low_confidence_passes(self):
        result = validate_rejection_reason(_valid_entry(rejection_confidence="low"))
        assert result.passed

    def test_uncertain_confidence_passes_with_warning(self):
        result = validate_rejection_reason(_valid_entry(rejection_confidence="uncertain"))
        assert result.passed
        assert any("uncertain" in w for w in result.warnings)

    def test_invalid_confidence_fails(self):
        result = validate_rejection_reason(_valid_entry(rejection_confidence="very_high"))
        assert not result.passed
        assert any("rejection_confidence must be one of" in e for e in result.errors)

    def test_empty_confidence_fails(self):
        result = validate_rejection_reason(_valid_entry(rejection_confidence=""))
        assert not result.passed

    def test_confidence_in_result(self):
        result = validate_rejection_reason(_valid_entry(rejection_confidence="low"))
        assert result.rejection_confidence == "low"


# ── 6. Rejection date validation ──────────────────────────────────────────────

class TestRejectionDateValidation:
    def test_valid_iso_date(self):
        result = validate_rejection_reason(_valid_entry(rejection_date="2026-07-10"))
        assert result.passed

    def test_date_without_dashes_fails(self):
        result = validate_rejection_reason(_valid_entry(rejection_date="20260710"))
        assert not result.passed
        assert any("rejection_date must be ISO format" in e for e in result.errors)

    def test_slash_date_fails(self):
        result = validate_rejection_reason(_valid_entry(rejection_date="2026/07/10"))
        assert not result.passed

    def test_empty_date_fails(self):
        result = validate_rejection_reason(_valid_entry(rejection_date=""))
        assert not result.passed

    def test_partial_date_fails(self):
        result = validate_rejection_reason(_valid_entry(rejection_date="2026-07"))
        assert not result.passed

    def test_another_valid_date(self):
        result = validate_rejection_reason(_valid_entry(rejection_date="2025-01-01"))
        assert result.passed


# ── 7. Rejection notes validation ─────────────────────────────────────────────

class TestRejectionNotesValidation:
    def test_valid_notes_passes(self):
        result = validate_rejection_reason(_valid_entry(rejection_notes="Toxicity too high."))
        assert result.passed

    def test_empty_notes_allowed_for_non_manual(self):
        result = validate_rejection_reason(
            _valid_entry(rejection_reason="toxicity_risk", rejection_notes="")
        )
        assert result.passed

    def test_notes_at_limit_passes(self):
        notes = "x" * 400
        result = validate_rejection_reason(_valid_entry(rejection_notes=notes))
        assert result.passed

    def test_notes_over_limit_fails(self):
        notes = "x" * 401
        result = validate_rejection_reason(_valid_entry(rejection_notes=notes))
        assert not result.passed
        assert any("rejection_notes must be at most 400" in e for e in result.errors)

    def test_notes_just_over_limit_fails(self):
        notes = "y" * 402
        result = validate_rejection_reason(_valid_entry(rejection_notes=notes))
        assert not result.passed


# ── 8. Manual exclusion requires notes ────────────────────────────────────────

class TestManualExclusionRequiresNotes:
    def test_manual_exclusion_with_notes_passes(self):
        result = validate_rejection_reason(
            _valid_entry(
                rejection_reason="manual_exclusion",
                rejection_stage="manual_exclusion",
                rejection_notes="Excluded by PI — out of scope.",
            )
        )
        assert result.passed

    def test_manual_exclusion_without_notes_fails(self):
        result = validate_rejection_reason(
            _valid_entry(
                rejection_reason="manual_exclusion",
                rejection_stage="manual_exclusion",
                rejection_notes="",
            )
        )
        assert not result.passed
        assert any("manual_exclusion" in e for e in result.errors)

    def test_manual_exclusion_whitespace_notes_fails(self):
        result = validate_rejection_reason(
            _valid_entry(
                rejection_reason="manual_exclusion",
                rejection_stage="manual_exclusion",
                rejection_notes="   ",
            )
        )
        assert not result.passed

    def test_other_reason_empty_notes_passes(self):
        result = validate_rejection_reason(
            _valid_entry(rejection_reason="toxicity_risk", rejection_notes="")
        )
        assert result.passed


# ── 9. Borderline + confidence consistency ────────────────────────────────────

class TestBorderlineConsistency:
    def test_borderline_true_high_confidence_fails(self):
        result = validate_rejection_reason(
            _valid_entry(borderline=True, rejection_confidence="high")
        )
        assert not result.passed
        assert any("borderline=True is inconsistent with rejection_confidence='high'" in e
                   for e in result.errors)

    def test_borderline_true_medium_passes(self):
        result = validate_rejection_reason(
            _valid_entry(borderline=True, rejection_confidence="medium",
                         rejection_notes="Very close call.")
        )
        assert result.passed

    def test_borderline_true_low_passes(self):
        result = validate_rejection_reason(
            _valid_entry(borderline=True, rejection_confidence="low",
                         rejection_notes="Could have gone either way.")
        )
        assert result.passed

    def test_borderline_false_high_confidence_passes(self):
        result = validate_rejection_reason(
            _valid_entry(borderline=False, rejection_confidence="high")
        )
        assert result.passed

    def test_borderline_true_no_notes_warns(self):
        result = validate_rejection_reason(
            _valid_entry(borderline=True, rejection_confidence="medium", rejection_notes="")
        )
        assert result.passed
        assert any("borderline" in w for w in result.warnings)

    def test_safety_block_no_notes_warns(self):
        result = validate_rejection_reason(
            _valid_entry(
                rejection_reason="safety_policy_block",
                rejection_stage="safety_policy_block",
                rejection_notes="",
            )
        )
        assert result.passed
        assert any("safety_policy_block" in w for w in result.warnings)


# ── 10. Dict-based validator ──────────────────────────────────────────────────

class TestDictValidator:
    def test_valid_dict_passes(self):
        data = {
            "rjr_id": "RJR-001",
            "pipeline_version": "v0.10.9",
            "candidate_id": "CAND-001",
            "rejection_stage": "toxicity_screen",
            "rejection_reason": "toxicity_risk",
            "rejection_confidence": "high",
            "rejection_date": "2026-07-10",
            "borderline": False,
            "reviewer": "Dr. Smith",
            "rejection_notes": "Too cytotoxic.",
            "dry_lab_only": True,
        }
        result = validate_rejection_reason_dict(data)
        assert result.passed

    def test_dict_wrong_prefix_fails(self):
        data = {
            "rjr_id": "BAD-001",
            "pipeline_version": "v0.10.9",
            "candidate_id": "CAND-001",
            "rejection_stage": "toxicity_screen",
            "rejection_reason": "toxicity_risk",
            "rejection_confidence": "high",
            "rejection_date": "2026-07-10",
            "borderline": False,
            "reviewer": "Dr. Smith",
            "rejection_notes": "ok",
        }
        result = validate_rejection_reason_dict(data)
        assert not result.passed

    def test_dict_defaults_dry_lab_true(self):
        data = {
            "rjr_id": "RJR-001",
            "pipeline_version": "v0.10.9",
            "candidate_id": "CAND-001",
            "rejection_stage": "toxicity_screen",
            "rejection_reason": "toxicity_risk",
            "rejection_confidence": "high",
            "rejection_date": "2026-07-10",
            "borderline": False,
            "reviewer": "Dr. Smith",
            "rejection_notes": "ok",
        }
        result = validate_rejection_reason_dict(data)
        assert result.dry_lab_only is True

    def test_dict_multiple_errors_reported(self):
        data = {
            "rjr_id": "BAD-001",
            "pipeline_version": "",
            "candidate_id": "",
            "rejection_stage": "fake_stage",
            "rejection_reason": "fake_reason",
            "rejection_confidence": "fake_confidence",
            "rejection_date": "not-a-date",
            "borderline": True,
            "reviewer": "",
            "rejection_notes": "",
        }
        result = validate_rejection_reason_dict(data)
        assert not result.passed
        assert len(result.errors) >= 5

    def test_dict_borderline_conflict_detected(self):
        data = {
            "rjr_id": "RJR-001",
            "pipeline_version": "v0.10.9",
            "candidate_id": "CAND-001",
            "rejection_stage": "toxicity_screen",
            "rejection_reason": "toxicity_risk",
            "rejection_confidence": "high",
            "rejection_date": "2026-07-10",
            "borderline": True,
            "reviewer": "Dr. Smith",
            "rejection_notes": "ok",
        }
        result = validate_rejection_reason_dict(data)
        assert not result.passed
        assert any("borderline" in e for e in result.errors)

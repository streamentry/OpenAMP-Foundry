"""Tests for pilot_preregistration module (E5)."""
from __future__ import annotations

import pytest

from openamp_foundry.evidence.pilot_preregistration import (
    PilotPreregistration,
    PreregistrationValidationResult,
    ScoreThreshold,
    VALID_AMENDMENT_REASONS,
    VALID_OUTCOME_METRICS,
    format_pilot_preregistration,
    validate_pilot_preregistration,
)


# --- Helpers ---

def _make_threshold(**kwargs) -> ScoreThreshold:
    defaults = dict(score_name="ensemble_score", threshold_value=0.75, direction="above")
    defaults.update(kwargs)
    return ScoreThreshold(**defaults)


def _make_record(**kwargs) -> PilotPreregistration:
    defaults = dict(
        record_id="PRR-2026-001",
        version="1.0.0",
        frozen_at="2026-07-10T00:00:00Z",
        pipeline_version="0.9.0",
        git_sha="abc1234",
        primary_hypothesis="High-scoring candidates will show MIC reduction vs. control.",
        selection_criteria=["ensemble_score >= 0.75", "toxicity_score < 0.3"],
        score_thresholds=[_make_threshold()],
        n_candidates_planned=5,
        positive_control="colistin_1ug_ml",
        negative_control="pbs_vehicle",
        outcome_metric="minimum_inhibitory_concentration",
        dry_lab_only_declaration=True,
        is_locked=False,
    )
    defaults.update(kwargs)
    return PilotPreregistration(**defaults)


# --- ScoreThreshold ---

class TestScoreThreshold:
    def test_is_dataclass(self):
        t = _make_threshold()
        assert isinstance(t, ScoreThreshold)

    def test_fields_accessible(self):
        t = ScoreThreshold("activity_score", 0.80, "above")
        assert t.score_name == "activity_score"
        assert t.threshold_value == pytest.approx(0.80)
        assert t.direction == "above"

    def test_threshold_stored(self):
        t = _make_threshold(threshold_value=0.5)
        assert t.threshold_value == pytest.approx(0.5)


# --- PilotPreregistration ---

class TestPilotPreregistration:
    def test_is_dataclass(self):
        r = _make_record()
        assert isinstance(r, PilotPreregistration)

    def test_fields_accessible(self):
        r = _make_record()
        assert r.record_id == "PRR-2026-001"
        assert r.dry_lab_only_declaration is True

    def test_default_notes_empty(self):
        r = _make_record()
        assert r.notes == ""

    def test_default_amendment_count(self):
        r = _make_record()
        assert r.amendment_count == 0

    def test_is_locked_default_false(self):
        r = _make_record()
        assert r.is_locked is False


# --- PreregistrationValidationResult ---

class TestPreregistrationValidationResult:
    def test_is_dataclass(self):
        r = PreregistrationValidationResult(True, [], [], "PRR-001", "ok")
        assert isinstance(r, PreregistrationValidationResult)

    def test_fields_accessible(self):
        r = PreregistrationValidationResult(False, ["v1"], ["w1"], "PRR-001", "bad")
        assert r.is_valid is False
        assert len(r.violations) == 1
        assert r.record_id == "PRR-001"

    def test_summary_stored(self):
        r = PreregistrationValidationResult(True, [], [], "PRR-001", "all good")
        assert r.validation_summary == "all good"


# --- validate_pilot_preregistration ---

class TestValidatePilotPreregistration:
    def test_valid_record_passes(self):
        result = validate_pilot_preregistration(_make_record())
        assert result.is_valid is True
        assert result.violations == []

    def test_returns_validation_result(self):
        result = validate_pilot_preregistration(_make_record())
        assert isinstance(result, PreregistrationValidationResult)

    def test_invalid_record_id_prefix(self):
        r = _make_record(record_id="REC-001")
        result = validate_pilot_preregistration(r)
        assert not result.is_valid
        assert any("PRR-" in v for v in result.violations)

    def test_invalid_version_format(self):
        r = _make_record(version="v1.0")
        result = validate_pilot_preregistration(r)
        assert not result.is_valid
        assert any("version" in v for v in result.violations)

    def test_invalid_git_sha_too_short(self):
        r = _make_record(git_sha="abc")
        result = validate_pilot_preregistration(r)
        assert not result.is_valid

    def test_invalid_git_sha_uppercase(self):
        r = _make_record(git_sha="ABC1234")
        result = validate_pilot_preregistration(r)
        assert not result.is_valid

    def test_dry_lab_false_blocked(self):
        r = _make_record(dry_lab_only_declaration=False)
        result = validate_pilot_preregistration(r)
        assert not result.is_valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_empty_selection_criteria_blocked(self):
        r = _make_record(selection_criteria=[])
        result = validate_pilot_preregistration(r)
        assert not result.is_valid
        assert any("selection_criteria" in v for v in result.violations)

    def test_empty_score_thresholds_blocked(self):
        r = _make_record(score_thresholds=[])
        result = validate_pilot_preregistration(r)
        assert not result.is_valid
        assert any("score_thresholds" in v for v in result.violations)

    def test_zero_candidates_blocked(self):
        r = _make_record(n_candidates_planned=0)
        result = validate_pilot_preregistration(r)
        assert not result.is_valid
        assert any("n_candidates_planned" in v for v in result.violations)

    def test_negative_candidates_blocked(self):
        r = _make_record(n_candidates_planned=-1)
        result = validate_pilot_preregistration(r)
        assert not result.is_valid

    def test_invalid_outcome_metric_blocked(self):
        r = _make_record(outcome_metric="made_up_metric")
        result = validate_pilot_preregistration(r)
        assert not result.is_valid
        assert any("outcome_metric" in v for v in result.violations)

    def test_valid_outcome_metrics_accepted(self):
        for metric in VALID_OUTCOME_METRICS:
            r = _make_record(outcome_metric=metric)
            result = validate_pilot_preregistration(r)
            metric_violations = [v for v in result.violations if "outcome_metric" in v]
            assert metric_violations == [], f"{metric} should be valid"

    def test_empty_hypothesis_blocked(self):
        r = _make_record(primary_hypothesis="")
        result = validate_pilot_preregistration(r)
        assert not result.is_valid
        assert any("primary_hypothesis" in v for v in result.violations)

    def test_whitespace_only_hypothesis_blocked(self):
        r = _make_record(primary_hypothesis="   ")
        result = validate_pilot_preregistration(r)
        assert not result.is_valid

    def test_empty_positive_control_blocked(self):
        r = _make_record(positive_control="")
        result = validate_pilot_preregistration(r)
        assert not result.is_valid
        assert any("positive_control" in v for v in result.violations)

    def test_empty_negative_control_blocked(self):
        r = _make_record(negative_control="")
        result = validate_pilot_preregistration(r)
        assert not result.is_valid
        assert any("negative_control" in v for v in result.violations)

    def test_empty_frozen_at_blocked(self):
        r = _make_record(frozen_at="")
        result = validate_pilot_preregistration(r)
        assert not result.is_valid
        assert any("frozen_at" in v for v in result.violations)

    def test_threshold_above_one_blocked(self):
        t = _make_threshold(threshold_value=1.5)
        r = _make_record(score_thresholds=[t])
        result = validate_pilot_preregistration(r)
        assert not result.is_valid
        assert any("threshold_value" in v for v in result.violations)

    def test_threshold_below_zero_blocked(self):
        t = _make_threshold(threshold_value=-0.1)
        r = _make_record(score_thresholds=[t])
        result = validate_pilot_preregistration(r)
        assert not result.is_valid

    def test_threshold_at_zero_valid(self):
        t = _make_threshold(threshold_value=0.0)
        r = _make_record(score_thresholds=[t])
        result = validate_pilot_preregistration(r)
        threshold_violations = [v for v in result.violations if "threshold_value" in v]
        assert threshold_violations == []

    def test_threshold_at_one_valid(self):
        t = _make_threshold(threshold_value=1.0)
        r = _make_record(score_thresholds=[t])
        result = validate_pilot_preregistration(r)
        threshold_violations = [v for v in result.violations if "threshold_value" in v]
        assert threshold_violations == []

    def test_invalid_amendment_reason_blocked(self):
        r = _make_record(amendment_reasons=["add_new_outcome"])
        result = validate_pilot_preregistration(r)
        assert not result.is_valid
        assert any("amendment_reasons" in v for v in result.violations)

    def test_valid_amendment_reason_accepted(self):
        for reason in VALID_AMENDMENT_REASONS:
            r = _make_record(amendment_reasons=[reason])
            result = validate_pilot_preregistration(r)
            reason_violations = [v for v in result.violations if "amendment_reasons" in v]
            assert reason_violations == [], f"{reason} should be valid"

    def test_locked_with_amendments_produces_warning(self):
        r = _make_record(is_locked=True, amendment_count=2)
        result = validate_pilot_preregistration(r)
        assert len(result.warnings) >= 1
        assert any("amendment" in w for w in result.warnings)

    def test_valid_summary_contains_record_id(self):
        result = validate_pilot_preregistration(_make_record())
        assert "PRR-2026-001" in result.validation_summary

    def test_violation_summary_mentions_violations(self):
        r = _make_record(record_id="BAD", dry_lab_only_declaration=False)
        result = validate_pilot_preregistration(r)
        assert "violation" in result.validation_summary

    def test_valid_outcome_metrics_set_size(self):
        assert len(VALID_OUTCOME_METRICS) == 8

    def test_valid_amendment_reasons_set_size(self):
        assert len(VALID_AMENDMENT_REASONS) == 5

    def test_multiple_violations_all_reported(self):
        r = _make_record(
            record_id="BAD",
            dry_lab_only_declaration=False,
            selection_criteria=[],
            score_thresholds=[],
        )
        result = validate_pilot_preregistration(r)
        assert len(result.violations) >= 4

    def test_locked_record_no_violations(self):
        r = _make_record(is_locked=True)
        result = validate_pilot_preregistration(r)
        assert result.is_valid

    def test_multiple_thresholds_accepted(self):
        thresholds = [
            _make_threshold(score_name="ensemble", threshold_value=0.75),
            _make_threshold(score_name="activity", threshold_value=0.70),
            _make_threshold(score_name="safety", threshold_value=0.80),
        ]
        r = _make_record(score_thresholds=thresholds)
        result = validate_pilot_preregistration(r)
        assert result.is_valid


# --- format_pilot_preregistration ---

class TestFormatPilotPreregistration:
    def test_returns_string(self):
        assert isinstance(format_pilot_preregistration(_make_record()), str)

    def test_contains_header(self):
        assert "PILOT PRE-REGISTRATION" in format_pilot_preregistration(_make_record())

    def test_contains_record_id(self):
        assert "PRR-2026-001" in format_pilot_preregistration(_make_record())

    def test_valid_record_shows_valid(self):
        assert "VALID" in format_pilot_preregistration(_make_record())

    def test_invalid_record_shows_invalid(self):
        r = _make_record(dry_lab_only_declaration=False)
        assert "INVALID" in format_pilot_preregistration(r)

    def test_contains_hypothesis(self):
        text = format_pilot_preregistration(_make_record())
        assert "HYPOTHESIS" in text

    def test_contains_thresholds_section(self):
        text = format_pilot_preregistration(_make_record())
        assert "THRESHOLD" in text

    def test_contains_outcome_metric(self):
        text = format_pilot_preregistration(_make_record())
        assert "minimum_inhibitory_concentration" in text

    def test_notice_in_invalid_output(self):
        r = _make_record(dry_lab_only_declaration=False)
        text = format_pilot_preregistration(r)
        assert "NOTICE" in text

    def test_positive_control_shown(self):
        text = format_pilot_preregistration(_make_record())
        assert "colistin_1ug_ml" in text

    def test_summary_in_output(self):
        r = _make_record()
        result = validate_pilot_preregistration(r)
        text = format_pilot_preregistration(r)
        assert result.validation_summary in text

    def test_locked_status_shown(self):
        r = _make_record(is_locked=True)
        text = format_pilot_preregistration(r)
        assert "YES" in text

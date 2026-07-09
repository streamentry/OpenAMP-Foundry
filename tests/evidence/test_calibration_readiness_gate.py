"""Tests for calibration readiness gate schema (Phase O O5)."""
import pytest
from openamp_foundry.evidence.calibration_readiness_gate import (
    GATE_NOTES_MAX_LENGTH,
    MIN_BATCHES,
    PASS_BRIER_THRESHOLD,
    VALID_TRENDS,
    WARN_BRIER_THRESHOLD,
    CalibrationReadinessEntry,
    CalibrationReadinessResult,
    validate_calibration_readiness,
    validate_calibration_readiness_dict,
)


def make_entry(**kwargs) -> CalibrationReadinessEntry:
    defaults = dict(
        gate_id="CRG-001",
        pipeline_version="v1.0.0",
        aggregator_id="CBA-001",
        mean_brier_score=0.15,
        trend="stable",
        total_batches_evaluated=3,
        gate_passed=True,
        failure_reasons=[],
        gate_notes="All checks passed.",
        reviewer="alice",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return CalibrationReadinessEntry(**defaults)


class TestConstants:
    def test_gate_notes_max_length(self):
        assert GATE_NOTES_MAX_LENGTH == 400

    def test_pass_brier_threshold(self):
        assert PASS_BRIER_THRESHOLD == 0.25

    def test_warn_brier_threshold(self):
        assert WARN_BRIER_THRESHOLD == 0.2

    def test_valid_trends(self):
        assert "improving" in VALID_TRENDS
        assert "stable" in VALID_TRENDS
        assert "degrading" in VALID_TRENDS
        assert len(VALID_TRENDS) == 3

    def test_min_batches(self):
        assert MIN_BATCHES == 2


class TestHappyPath:
    def test_valid_passed_entry(self):
        entry = make_entry()
        result = validate_calibration_readiness(entry)
        assert result.passed
        assert result.errors == []

    def test_valid_failed_entry(self):
        entry = make_entry(
            gate_passed=False,
            failure_reasons=["Brier score too high: 0.30"],
        )
        result = validate_calibration_readiness(entry)
        assert result.passed
        assert result.errors == []

    def test_result_fields(self):
        entry = make_entry()
        result = validate_calibration_readiness(entry)
        assert result.gate_id == "CRG-001"
        assert result.pipeline_version == "v1.0.0"
        assert result.mean_brier_score == 0.15
        assert result.trend == "stable"
        assert result.gate_passed is True
        assert result.dry_lab_only is True

    def test_dry_lab_only_default_true(self):
        entry = CalibrationReadinessEntry(
            gate_id="CRG-001",
            pipeline_version="v1.0",
            aggregator_id="CBA-001",
            mean_brier_score=0.15,
            trend="stable",
            total_batches_evaluated=3,
            gate_passed=True,
            failure_reasons=[],
            gate_notes="",
            reviewer="bob",
        )
        assert entry.dry_lab_only is True

    def test_improving_trend_passes(self):
        entry = make_entry(trend="improving")
        result = validate_calibration_readiness(entry)
        assert result.passed

    def test_degrading_trend_with_failures_passes_validation(self):
        entry = make_entry(
            trend="degrading",
            gate_passed=False,
            failure_reasons=["degrading trend detected"],
        )
        result = validate_calibration_readiness(entry)
        assert result.passed

    def test_multiple_failure_reasons(self):
        entry = make_entry(
            gate_passed=False,
            failure_reasons=["high Brier score", "degrading trend"],
        )
        result = validate_calibration_readiness(entry)
        assert result.passed


class TestGateIdValidation:
    def test_wrong_prefix_fails(self):
        entry = make_entry(gate_id="WRONG-001")
        result = validate_calibration_readiness(entry)
        assert not result.passed
        assert any("CRG-" in e for e in result.errors)

    def test_correct_prefix_passes(self):
        entry = make_entry(gate_id="CRG-2026-001")
        result = validate_calibration_readiness(entry)
        assert result.passed


class TestAggregatorIdValidation:
    def test_wrong_aggregator_prefix_fails(self):
        entry = make_entry(aggregator_id="WRONG-001")
        result = validate_calibration_readiness(entry)
        assert not result.passed
        assert any("CBA-" in e for e in result.errors)

    def test_correct_aggregator_prefix_passes(self):
        entry = make_entry(aggregator_id="CBA-2026-001")
        result = validate_calibration_readiness(entry)
        assert result.passed


class TestBrierScoreValidation:
    def test_brier_below_zero_fails(self):
        entry = make_entry(mean_brier_score=-0.1)
        result = validate_calibration_readiness(entry)
        assert not result.passed
        assert any("mean_brier_score" in e for e in result.errors)

    def test_brier_above_one_fails(self):
        entry = make_entry(mean_brier_score=1.1)
        result = validate_calibration_readiness(entry)
        assert not result.passed

    def test_brier_zero_passes(self):
        entry = make_entry(mean_brier_score=0.0)
        result = validate_calibration_readiness(entry)
        assert result.passed

    def test_brier_one_passes_schema(self):
        entry = make_entry(
            mean_brier_score=1.0,
            gate_passed=False,
            failure_reasons=["extreme Brier score"],
        )
        result = validate_calibration_readiness(entry)
        assert result.passed


class TestTrendValidation:
    def test_invalid_trend_fails(self):
        entry = make_entry(trend="unknown")
        result = validate_calibration_readiness(entry)
        assert not result.passed
        assert any("trend" in e for e in result.errors)

    def test_empty_trend_fails(self):
        entry = make_entry(trend="")
        result = validate_calibration_readiness(entry)
        assert not result.passed

    def test_all_valid_trends_pass(self):
        for trend in VALID_TRENDS:
            entry = make_entry(trend=trend)
            result = validate_calibration_readiness(entry)
            assert result.passed, f"trend={trend} should pass"


class TestBatchCountValidation:
    def test_one_batch_fails(self):
        entry = make_entry(total_batches_evaluated=1)
        result = validate_calibration_readiness(entry)
        assert not result.passed
        assert any("total_batches_evaluated" in e for e in result.errors)

    def test_zero_batches_fails(self):
        entry = make_entry(total_batches_evaluated=0)
        result = validate_calibration_readiness(entry)
        assert not result.passed

    def test_two_batches_passes(self):
        entry = make_entry(total_batches_evaluated=2)
        result = validate_calibration_readiness(entry)
        assert result.passed


class TestGateNotesValidation:
    def test_notes_too_long_fails(self):
        entry = make_entry(gate_notes="x" * 401)
        result = validate_calibration_readiness(entry)
        assert not result.passed
        assert any("gate_notes" in e for e in result.errors)

    def test_notes_exact_max_passes(self):
        entry = make_entry(gate_notes="x" * 400)
        result = validate_calibration_readiness(entry)
        assert result.passed

    def test_empty_notes_passes(self):
        entry = make_entry(gate_notes="")
        result = validate_calibration_readiness(entry)
        assert result.passed


class TestGatePassedConsistency:
    def test_passed_true_with_failures_fails(self):
        entry = make_entry(
            gate_passed=True,
            failure_reasons=["some failure"],
        )
        result = validate_calibration_readiness(entry)
        assert not result.passed
        assert any("gate_passed" in e for e in result.errors)

    def test_passed_false_empty_reasons_fails(self):
        entry = make_entry(
            gate_passed=False,
            failure_reasons=[],
        )
        result = validate_calibration_readiness(entry)
        assert not result.passed
        assert any("failure_reasons" in e or "gate_passed" in e for e in result.errors)

    def test_passed_true_no_failures_passes(self):
        entry = make_entry(gate_passed=True, failure_reasons=[])
        result = validate_calibration_readiness(entry)
        assert result.passed

    def test_passed_false_with_reasons_passes(self):
        entry = make_entry(
            gate_passed=False,
            failure_reasons=["Brier > threshold"],
        )
        result = validate_calibration_readiness(entry)
        assert result.passed


class TestWarnings:
    def test_degrading_and_passed_warns(self):
        entry = make_entry(trend="degrading", gate_passed=True)
        result = validate_calibration_readiness(entry)
        assert result.passed
        assert any("degrading" in w for w in result.warnings)

    def test_degrading_and_failed_no_degrading_warn(self):
        entry = make_entry(
            trend="degrading",
            gate_passed=False,
            failure_reasons=["trend degrading"],
        )
        result = validate_calibration_readiness(entry)
        assert result.passed
        assert not any("degrading" in w for w in result.warnings)

    def test_stable_no_degrading_warn(self):
        entry = make_entry(trend="stable")
        result = validate_calibration_readiness(entry)
        assert result.passed
        assert not any("degrading" in w for w in result.warnings)

    def test_marginal_brier_and_passed_warns(self):
        entry = make_entry(mean_brier_score=0.22, gate_passed=True, failure_reasons=[])
        result = validate_calibration_readiness(entry)
        assert result.passed
        assert any("marginal pass" in w for w in result.warnings)

    def test_good_brier_no_marginal_warn(self):
        entry = make_entry(mean_brier_score=0.15)
        result = validate_calibration_readiness(entry)
        assert result.passed
        assert not any("marginal pass" in w for w in result.warnings)

    def test_brier_at_warn_threshold_warns(self):
        entry = make_entry(mean_brier_score=0.2, gate_passed=True, failure_reasons=[])
        result = validate_calibration_readiness(entry)
        assert result.passed
        assert any("marginal pass" in w for w in result.warnings)

    def test_brier_at_pass_threshold_fails_gate(self):
        entry = make_entry(
            mean_brier_score=0.25,
            gate_passed=False,
            failure_reasons=["Brier score at threshold"],
        )
        result = validate_calibration_readiness(entry)
        assert result.passed
        assert not any("marginal pass" in w for w in result.warnings)


class TestDictInterface:
    def test_valid_dict_passes(self):
        data = {
            "gate_id": "CRG-001",
            "pipeline_version": "v1.0",
            "aggregator_id": "CBA-001",
            "mean_brier_score": 0.15,
            "trend": "stable",
            "total_batches_evaluated": 3,
            "gate_passed": True,
            "failure_reasons": [],
            "gate_notes": "ok",
            "reviewer": "alice",
        }
        result = validate_calibration_readiness_dict(data)
        assert result.passed

    def test_missing_field_fails(self):
        data = {"gate_id": "CRG-001"}
        result = validate_calibration_readiness_dict(data)
        assert not result.passed
        assert any("Missing required field" in e for e in result.errors)

    def test_dict_dry_lab_only_default_true(self):
        data = {
            "gate_id": "CRG-001",
            "pipeline_version": "v1.0",
            "aggregator_id": "CBA-001",
            "mean_brier_score": 0.15,
            "trend": "stable",
            "total_batches_evaluated": 3,
            "gate_passed": True,
            "failure_reasons": [],
            "gate_notes": "ok",
            "reviewer": "alice",
        }
        result = validate_calibration_readiness_dict(data)
        assert result.dry_lab_only is True

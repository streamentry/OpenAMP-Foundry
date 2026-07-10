"""Tests for prediction quality trend report (Phase S S5)."""
import pytest
from openamp_foundry.evidence.prediction_quality_trend_report import (
    WHROutcomeRecord,
    PredictionQualityTrendReport,
    VALID_TREND_VERDICTS,
    DEFAULT_ROLLING_WINDOW,
    DEFAULT_ALERT_THRESHOLD,
    MIN_OUTCOMES_FOR_TREND,
    validate_prediction_quality_trend_report,
    build_prediction_quality_trend_report,
    format_prediction_quality_trend_report,
)


def _make_outcome(whr_id="WHR-001", batch_id="B001", score=0.9, hit=True, date="2026-01-01"):
    return WHROutcomeRecord(whr_id=whr_id, batch_id=batch_id, predicted_score=score, confirmed_hit=hit, confirmation_date=date)


def _make_outcomes(n_hit, n_miss, batch_id="B001"):
    records = []
    for i in range(n_hit):
        records.append(_make_outcome(whr_id=f"WHR-H{i}", batch_id=batch_id, score=0.9, hit=True))
    for i in range(n_miss):
        records.append(_make_outcome(whr_id=f"WHR-M{i}", batch_id=batch_id, score=0.3, hit=False))
    return records


class TestWHROutcomeRecord:
    def test_valid_construction(self):
        r = _make_outcome()
        assert r.whr_id == "WHR-001"
        assert r.batch_id == "B001"
        assert r.predicted_score == 0.9
        assert r.confirmed_hit is True
        assert r.confirmation_date == "2026-01-01"

    def test_confirmed_hit_true(self):
        r = _make_outcome(hit=True)
        assert r.confirmed_hit is True

    def test_confirmed_hit_false(self):
        r = _make_outcome(hit=False)
        assert r.confirmed_hit is False

    def test_predicted_score_negative(self):
        r = _make_outcome(score=-0.5)
        assert r.predicted_score == -0.5

    def test_predicted_score_zero(self):
        r = _make_outcome(score=0.0)
        assert r.predicted_score == 0.0

    def test_predicted_score_positive(self):
        r = _make_outcome(score=0.75)
        assert r.predicted_score == 0.75

    def test_whr_id_non_empty(self):
        r = _make_outcome(whr_id="WHR-999")
        assert len(r.whr_id) > 0


class TestValidatePredictionQualityTrendReport:
    def _valid_report(self, **overrides):
        records = _make_outcomes(3, 2)
        params = dict(
            pqt_id="PQT-001",
            pipeline_version="v1",
            n_outcomes_total=5,
            n_confirmed_hits=3,
            n_batches_covered=1,
            outcome_records=records,
            rolling_window_size=2,
            rolling_precision_values=[0.6, 0.6, 0.6, 0.6],
            overall_precision=0.6,
            trend_verdict="stable",
            degradation_alert=False,
            score_hit_correlation=0.5,
            dry_lab_only=True,
            limitations=["test only"],
            created_at="2026-01-01",
            alert_threshold=0.1,
        )
        params.update(overrides)
        return PredictionQualityTrendReport(**params)

    def test_valid_sufficient_data_passes(self):
        report = self._valid_report()
        result = validate_prediction_quality_trend_report(report)
        assert result.valid
        assert len(result.violations) == 0

    def test_valid_insufficient_data_passes(self):
        records = _make_outcomes(2, 2)
        report = PredictionQualityTrendReport(
            pqt_id="PQT-002",
            pipeline_version="v1",
            n_outcomes_total=4,
            n_confirmed_hits=2,
            n_batches_covered=1,
            outcome_records=records,
            rolling_window_size=5,
            rolling_precision_values=[],
            overall_precision=0.5,
            trend_verdict="insufficient_data",
            degradation_alert=False,
            score_hit_correlation=0.3,
            dry_lab_only=True,
            limitations=["test only"],
            created_at="2026-01-01",
            alert_threshold=0.1,
        )
        result = validate_prediction_quality_trend_report(report)
        assert result.valid
        assert len(result.violations) == 0

    def test_pqt_id_not_starting_with_PQT_fails(self):
        report = self._valid_report(pqt_id="INVALID-001")
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("pqt_id must start with 'PQT-'" in v for v in result.violations)

    def test_dry_lab_only_false_fails(self):
        report = self._valid_report(dry_lab_only=False)
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_n_outcomes_total_mismatch_fails(self):
        report = self._valid_report(n_outcomes_total=10)
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("n_outcomes_total" in v for v in result.violations)

    def test_n_confirmed_hits_mismatch_fails(self):
        report = self._valid_report(n_confirmed_hits=5)
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("n_confirmed_hits" in v for v in result.violations)

    def test_n_batches_covered_mismatch_fails(self):
        report = self._valid_report(n_batches_covered=5)
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("n_batches_covered" in v for v in result.violations)

    def test_overall_precision_mismatch_fails(self):
        report = self._valid_report(overall_precision=0.1)
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("overall_precision" in v for v in result.violations)

    def test_rolling_window_size_below_2_fails(self):
        report = self._valid_report(rolling_window_size=1, rolling_precision_values=[0.6, 0.6, 0.6, 0.6, 0.6])
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("rolling_window_size" in v for v in result.violations)

    def test_rolling_precision_values_wrong_length_fails(self):
        report = self._valid_report(rolling_precision_values=[0.6])
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("rolling_precision_values" in v for v in result.violations)

    def test_insufficient_data_with_non_empty_rpv_fails(self):
        records = _make_outcomes(5, 5)
        report = PredictionQualityTrendReport(
            pqt_id="PQT-003",
            pipeline_version="v1",
            n_outcomes_total=10,
            n_confirmed_hits=5,
            n_batches_covered=1,
            outcome_records=records,
            rolling_window_size=2,
            rolling_precision_values=[0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
            overall_precision=0.5,
            trend_verdict="insufficient_data",
            degradation_alert=False,
            score_hit_correlation=0.0,
            dry_lab_only=True,
            limitations=["test"],
            created_at="2026-01-01",
            alert_threshold=0.1,
        )
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("insufficient_data" in v and "rolling_precision_values" in v for v in result.violations)

    def test_improving_with_non_improving_values_fails(self):
        records = _make_outcomes(5, 5)
        report = PredictionQualityTrendReport(
            pqt_id="PQT-004",
            pipeline_version="v1",
            n_outcomes_total=10,
            n_confirmed_hits=5,
            n_batches_covered=1,
            outcome_records=records,
            rolling_window_size=2,
            rolling_precision_values=[0.8, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
            overall_precision=0.5,
            trend_verdict="improving",
            degradation_alert=False,
            score_hit_correlation=0.0,
            dry_lab_only=True,
            limitations=["test"],
            created_at="2026-01-01",
            alert_threshold=0.1,
        )
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("improving" in v and "trend_verdict" in v for v in result.violations)

    def test_degrading_with_non_degrading_values_fails(self):
        records = _make_outcomes(5, 5)
        report = PredictionQualityTrendReport(
            pqt_id="PQT-005",
            pipeline_version="v1",
            n_outcomes_total=10,
            n_confirmed_hits=5,
            n_batches_covered=1,
            outcome_records=records,
            rolling_window_size=2,
            rolling_precision_values=[0.5, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
            overall_precision=0.5,
            trend_verdict="degrading",
            degradation_alert=True,
            score_hit_correlation=0.0,
            dry_lab_only=True,
            limitations=["test"],
            created_at="2026-01-01",
            alert_threshold=0.1,
        )
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("degrading" in v and "trend_verdict" in v for v in result.violations)

    def test_degradation_alert_true_when_not_degrading_fails(self):
        report = self._valid_report(degradation_alert=True)
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("degradation_alert" in v for v in result.violations)

    def test_degradation_alert_false_when_degrading_fails(self):
        records = _make_outcomes(5, 5)
        report = PredictionQualityTrendReport(
            pqt_id="PQT-006",
            pipeline_version="v1",
            n_outcomes_total=10,
            n_confirmed_hits=5,
            n_batches_covered=1,
            outcome_records=records,
            rolling_window_size=2,
            rolling_precision_values=[0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1],
            overall_precision=0.5,
            trend_verdict="degrading",
            degradation_alert=False,
            score_hit_correlation=0.0,
            dry_lab_only=True,
            limitations=["test"],
            created_at="2026-01-01",
            alert_threshold=0.1,
        )
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("degradation_alert" in v for v in result.violations)

    def test_score_hit_correlation_above_1_fails(self):
        report = self._valid_report(score_hit_correlation=1.5)
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("score_hit_correlation" in v for v in result.violations)

    def test_score_hit_correlation_below_minus_1_fails(self):
        report = self._valid_report(score_hit_correlation=-1.5)
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("score_hit_correlation" in v for v in result.violations)

    def test_empty_limitations_fails(self):
        report = self._valid_report(limitations=[])
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("limitations" in v for v in result.violations)

    def test_alert_threshold_zero_fails(self):
        report = self._valid_report(alert_threshold=0.0)
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("alert_threshold" in v for v in result.violations)

    def test_alert_threshold_above_1_fails(self):
        report = self._valid_report(alert_threshold=1.5)
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("alert_threshold" in v for v in result.violations)

    def test_invalid_trend_verdict_fails(self):
        report = self._valid_report(trend_verdict="invalid_verdict", degradation_alert=False, rolling_precision_values=[0.6])
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("trend_verdict" in v for v in result.violations)

    def test_improving_with_empty_rpv_fails(self):
        report = self._valid_report(trend_verdict="improving", rolling_precision_values=[], degradation_alert=False)
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("improving" in v for v in result.violations)

    def test_degrading_with_empty_rpv_fails(self):
        report = self._valid_report(trend_verdict="degrading", rolling_precision_values=[], degradation_alert=True)
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("degrading" in v for v in result.violations)

    def test_stable_with_empty_rpv_fails(self):
        report = self._valid_report(trend_verdict="stable", rolling_precision_values=[], degradation_alert=False)
        result = validate_prediction_quality_trend_report(report)
        assert not result.valid
        assert any("stable" in v for v in result.violations)

    def test_score_hit_correlation_exactly_negative_one_passes(self):
        report = self._valid_report(score_hit_correlation=-1.0)
        result = validate_prediction_quality_trend_report(report)
        assert result.valid

    def test_score_hit_correlation_exactly_one_passes(self):
        report = self._valid_report(score_hit_correlation=1.0)
        result = validate_prediction_quality_trend_report(report)
        assert result.valid


class TestBuildPredictionQualityTrendReport:
    def test_build_all_hits(self):
        outcomes = _make_outcomes(3, 0)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-010",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.n_confirmed_hits == 3
        assert report.overall_precision == 1.0

    def test_build_all_miss(self):
        outcomes = _make_outcomes(0, 3)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-011",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.n_confirmed_hits == 0
        assert report.overall_precision == 0.0

    def test_build_mixed_outcomes_correct_precision(self):
        outcomes = _make_outcomes(2, 3)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-012",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.n_confirmed_hits == 2
        assert report.overall_precision == 0.4

    def test_build_auto_sets_dry_lab_only_true(self):
        outcomes = _make_outcomes(3, 2)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-013",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.dry_lab_only is True

    def test_build_insufficient_data_verdict(self):
        outcomes = _make_outcomes(3, 0)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-014",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
            rolling_window_size=5,
        )
        assert report.trend_verdict == "insufficient_data"
        assert report.rolling_precision_values == []

    def test_build_sufficient_data_has_rolling_values(self):
        outcomes = _make_outcomes(5, 5)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-015",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
            rolling_window_size=2,
        )
        assert len(report.rolling_precision_values) > 0

    def test_build_improving_trend(self):
        outcomes = _make_outcomes(0, 5) + _make_outcomes(5, 0)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-016",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
            rolling_window_size=5,
            alert_threshold=0.1,
        )
        assert report.trend_verdict == "improving"
        assert report.degradation_alert is False

    def test_build_degrading_trend_sets_alert(self):
        outcomes = _make_outcomes(5, 0) + _make_outcomes(0, 5)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-017",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
            rolling_window_size=5,
            alert_threshold=0.1,
        )
        assert report.trend_verdict == "degrading"
        assert report.degradation_alert is True

    def test_build_stable_trend(self):
        outcomes = _make_outcomes(3, 2) + _make_outcomes(3, 2)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-018",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
            rolling_window_size=5,
            alert_threshold=0.1,
        )
        assert report.trend_verdict == "stable"
        assert report.degradation_alert is False

    def test_build_default_rolling_window_size(self):
        outcomes = _make_outcomes(5, 5)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-019",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.rolling_window_size == DEFAULT_ROLLING_WINDOW

    def test_build_custom_rolling_window_size(self):
        outcomes = _make_outcomes(5, 5)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-020",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
            rolling_window_size=3,
        )
        assert report.rolling_window_size == 3

    def test_build_default_alert_threshold(self):
        outcomes = _make_outcomes(3, 2)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-021",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.alert_threshold == DEFAULT_ALERT_THRESHOLD

    def test_build_n_outcomes_total_matches_len(self):
        outcomes = _make_outcomes(4, 3)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-022",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.n_outcomes_total == len(outcomes)

    def test_build_n_batches_covered_matches_unique(self):
        outcomes = _make_outcomes(2, 1, batch_id="B001") + _make_outcomes(2, 1, batch_id="B002")
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-023",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.n_batches_covered == 2

    def test_build_multiple_batches(self):
        outcomes = [
            _make_outcome(whr_id="WHR-1", batch_id="B001", score=0.9, hit=True),
            _make_outcome(whr_id="WHR-2", batch_id="B002", score=0.3, hit=False),
            _make_outcome(whr_id="WHR-3", batch_id="B003", score=0.7, hit=True),
        ]
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-024",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.n_batches_covered == 3

    def test_build_score_hit_correlation_in_range(self):
        outcomes = _make_outcomes(5, 5)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-025",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert isinstance(report.score_hit_correlation, float)
        assert -1.0 <= report.score_hit_correlation <= 1.0

    def test_build_all_same_scores_zero_correlation(self):
        records = [
            WHROutcomeRecord(whr_id=f"WHR-{i}", batch_id="B001", predicted_score=0.5, confirmed_hit=True, confirmation_date="2026-01-01")
            for i in range(5)
        ]
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-026",
            pipeline_version="v1",
            outcome_records=records,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.score_hit_correlation == 0.0

    def test_build_empty_outcomes(self):
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-027",
            pipeline_version="v1",
            outcome_records=[],
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.overall_precision == 0.0
        assert report.trend_verdict == "insufficient_data"
        assert report.n_outcomes_total == 0
        assert report.n_confirmed_hits == 0

    def test_build_rejects_rolling_window_size_below_2(self):
        outcomes = _make_outcomes(5, 5)
        with pytest.raises(ValueError):
            build_prediction_quality_trend_report(
                pqt_id="PQT-028",
                pipeline_version="v1",
                outcome_records=outcomes,
                limitations=["test"],
                created_at="2026-01-01",
                rolling_window_size=1,
            )

    def test_build_single_batch(self):
        outcomes = _make_outcomes(5, 0)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-029",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.n_batches_covered == 1

    def test_build_pqt_id_prefix_enforced(self):
        with pytest.raises(ValueError):
            build_prediction_quality_trend_report(
                pqt_id="BAD-001",
                pipeline_version="v1",
                outcome_records=_make_outcomes(3, 2),
                limitations=["test"],
                created_at="2026-01-01",
            )

    def test_build_rolling_precision_values_correct_length(self):
        outcomes = _make_outcomes(10, 0)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-030",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
            rolling_window_size=5,
        )
        expected_len = len(outcomes) - 5 + 1
        assert len(report.rolling_precision_values) == expected_len


class TestPredictionQualityTrendReportIntegration:
    def test_round_trip_build_then_validate_passes(self):
        outcomes = _make_outcomes(5, 5)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-100",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        result = validate_prediction_quality_trend_report(report)
        assert result.valid

    def test_toy_prefix_in_pqt_id_allowed(self):
        outcomes = _make_outcomes(3, 2)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-TOY-001",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.pqt_id == "PQT-TOY-001"
        result = validate_prediction_quality_trend_report(report)
        assert result.valid

    def test_degrading_verdict_sets_alert_end_to_end(self):
        outcomes = _make_outcomes(5, 0) + _make_outcomes(0, 5)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-101",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
            rolling_window_size=5,
            alert_threshold=0.1,
        )
        assert report.trend_verdict == "degrading"
        assert report.degradation_alert is True

    def test_insufficient_data_has_empty_rolling_values(self):
        outcomes = _make_outcomes(3, 2)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-102",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
            rolling_window_size=10,
        )
        assert report.trend_verdict == "insufficient_data"
        assert report.rolling_precision_values == []

    def test_overall_precision_in_zero_one(self):
        outcomes = _make_outcomes(7, 3)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-103",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert 0.0 <= report.overall_precision <= 1.0

    def test_rolling_precision_values_in_zero_one(self):
        outcomes = _make_outcomes(5, 5)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-104",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
            rolling_window_size=2,
        )
        for v in report.rolling_precision_values:
            assert 0.0 <= v <= 1.0

    def test_single_batch_n_batches_covered(self):
        outcomes = _make_outcomes(5, 5)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-105",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.n_batches_covered == 1

    def test_rejects_rolling_window_size_below_2(self):
        outcomes = _make_outcomes(5, 5)
        with pytest.raises(ValueError):
            build_prediction_quality_trend_report(
                pqt_id="PQT-106",
                pipeline_version="v1",
                outcome_records=outcomes,
                limitations=["test"],
                created_at="2026-01-01",
                rolling_window_size=1,
            )

    def test_empty_limitations_rejected(self):
        with pytest.raises(ValueError):
            build_prediction_quality_trend_report(
                pqt_id="PQT-107",
                pipeline_version="v1",
                outcome_records=_make_outcomes(3, 2),
                limitations=[],
                created_at="2026-01-01",
            )

    def test_dry_lab_only_always_true_in_build(self):
        outcomes = _make_outcomes(5, 5)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-108",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        assert report.dry_lab_only is True
        result = validate_prediction_quality_trend_report(report)
        assert result.valid


class TestFormatPredictionQualityTrendReport:
    def test_returns_string(self):
        outcomes = _make_outcomes(3, 2)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-200",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        output = format_prediction_quality_trend_report(report)
        assert isinstance(output, str)

    def test_contains_pqt_id(self):
        outcomes = _make_outcomes(3, 2)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-200",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        output = format_prediction_quality_trend_report(report)
        assert "PQT-200" in output

    def test_contains_trend_verdict(self):
        outcomes = _make_outcomes(3, 2)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-200",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        output = format_prediction_quality_trend_report(report)
        assert report.trend_verdict in output

    def test_contains_overall_precision(self):
        outcomes = _make_outcomes(3, 2)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-200",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        output = format_prediction_quality_trend_report(report)
        assert "0.6000" in output or "0.6" in output

    def test_contains_n_outcomes_total(self):
        outcomes = _make_outcomes(3, 2)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-200",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
        )
        output = format_prediction_quality_trend_report(report)
        assert "5" in output

    def test_contains_rolling_precision_values(self):
        outcomes = _make_outcomes(5, 5)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-201",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only"],
            created_at="2026-01-01",
            rolling_window_size=2,
        )
        output = format_prediction_quality_trend_report(report)
        assert "Rolling Precision" in output

    def test_contains_limitations(self):
        outcomes = _make_outcomes(3, 2)
        report = build_prediction_quality_trend_report(
            pqt_id="PQT-202",
            pipeline_version="v1",
            outcome_records=outcomes,
            limitations=["test only", "small sample"],
            created_at="2026-01-01",
        )
        output = format_prediction_quality_trend_report(report)
        assert "test only" in output
        assert "small sample" in output

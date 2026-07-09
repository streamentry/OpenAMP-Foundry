"""Tests for cross-batch performance aggregator schema (Phase O O4)."""
import pytest
from openamp_foundry.evidence.cross_batch_aggregator import (
    AGGREGATION_NOTES_MAX_LENGTH,
    CPS_PREFIX,
    HIGH_VARIANCE_THRESHOLD,
    MIN_BATCHES,
    POOR_BRIER_THRESHOLD,
    SUMMARY_ID_PREFIX,
    VALID_TRENDS,
    CrossBatchAggregatorEntry,
    CrossBatchAggregatorResult,
    validate_cross_batch_aggregator,
    validate_cross_batch_aggregator_dict,
)


def make_entry(**kwargs) -> CrossBatchAggregatorEntry:
    defaults = dict(
        aggregator_id="CBA-001",
        pipeline_version="v1.0.0",
        batch_ids_included=["BATCH-001", "BATCH-002"],
        summary_ids_included=["CPS-001", "CPS-002"],
        mean_brier_score=0.15,
        min_brier_score=0.10,
        max_brier_score=0.20,
        trend="stable",
        total_candidates_evaluated=100,
        aggregation_notes="Two batches aggregated.",
        reviewer="alice",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return CrossBatchAggregatorEntry(**defaults)


class TestConstants:
    def test_aggregation_notes_max_length(self):
        assert AGGREGATION_NOTES_MAX_LENGTH == 400

    def test_valid_trends(self):
        assert "improving" in VALID_TRENDS
        assert "stable" in VALID_TRENDS
        assert "degrading" in VALID_TRENDS
        assert len(VALID_TRENDS) == 3

    def test_poor_brier_threshold(self):
        assert POOR_BRIER_THRESHOLD == 0.25

    def test_high_variance_threshold(self):
        assert HIGH_VARIANCE_THRESHOLD == 0.2

    def test_min_batches(self):
        assert MIN_BATCHES == 2

    def test_summary_id_prefix(self):
        assert SUMMARY_ID_PREFIX == "CBA-"

    def test_cps_prefix(self):
        assert CPS_PREFIX == "CPS-"


class TestHappyPath:
    def test_valid_entry_passes(self):
        entry = make_entry()
        result = validate_cross_batch_aggregator(entry)
        assert result.passed
        assert result.errors == []

    def test_result_fields(self):
        entry = make_entry()
        result = validate_cross_batch_aggregator(entry)
        assert result.aggregator_id == "CBA-001"
        assert result.pipeline_version == "v1.0.0"
        assert result.mean_brier_score == 0.15
        assert result.trend == "stable"
        assert result.dry_lab_only is True

    def test_dry_lab_only_default_true(self):
        entry = CrossBatchAggregatorEntry(
            aggregator_id="CBA-001",
            pipeline_version="v1.0",
            batch_ids_included=["A", "B"],
            summary_ids_included=["CPS-A", "CPS-B"],
            mean_brier_score=0.15,
            min_brier_score=0.10,
            max_brier_score=0.20,
            trend="stable",
            total_candidates_evaluated=20,
            aggregation_notes="",
            reviewer="bob",
        )
        assert entry.dry_lab_only is True

    def test_three_batches_passes(self):
        entry = make_entry(
            batch_ids_included=["A", "B", "C"],
            summary_ids_included=["CPS-A", "CPS-B", "CPS-C"],
            total_candidates_evaluated=150,
        )
        result = validate_cross_batch_aggregator(entry)
        assert result.passed

    def test_improving_trend_passes(self):
        entry = make_entry(trend="improving")
        result = validate_cross_batch_aggregator(entry)
        assert result.passed

    def test_degrading_trend_passes_with_warning(self):
        entry = make_entry(trend="degrading")
        result = validate_cross_batch_aggregator(entry)
        assert result.passed

    def test_all_equal_brier_scores_pass(self):
        entry = make_entry(
            mean_brier_score=0.2,
            min_brier_score=0.2,
            max_brier_score=0.2,
        )
        result = validate_cross_batch_aggregator(entry)
        assert result.passed


class TestAggregatorIdValidation:
    def test_wrong_prefix_fails(self):
        entry = make_entry(aggregator_id="WRONG-001")
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed
        assert any("CBA-" in e for e in result.errors)

    def test_correct_prefix_passes(self):
        entry = make_entry(aggregator_id="CBA-2026-001")
        result = validate_cross_batch_aggregator(entry)
        assert result.passed


class TestBatchCountValidation:
    def test_one_batch_ids_fails(self):
        entry = make_entry(
            batch_ids_included=["BATCH-001"],
            summary_ids_included=["CPS-001"],
        )
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed
        assert any("batch_ids_included" in e for e in result.errors)

    def test_empty_batch_ids_fails(self):
        entry = make_entry(batch_ids_included=[], summary_ids_included=[])
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed

    def test_one_summary_ids_fails(self):
        entry = make_entry(
            batch_ids_included=["A", "B"],
            summary_ids_included=["CPS-A"],
        )
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed
        assert any("summary_ids_included" in e for e in result.errors)


class TestSummaryIdPrefixValidation:
    def test_invalid_summary_prefix_fails(self):
        entry = make_entry(summary_ids_included=["WRONG-001", "WRONG-002"])
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed
        assert any("CPS-" in e for e in result.errors)

    def test_mixed_valid_invalid_summary_fails(self):
        entry = make_entry(summary_ids_included=["CPS-001", "BAD-002"])
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed

    def test_valid_cps_prefixes_pass(self):
        entry = make_entry(summary_ids_included=["CPS-A", "CPS-B"])
        result = validate_cross_batch_aggregator(entry)
        assert result.passed


class TestBatchSummaryLengthMismatch:
    def test_mismatched_lengths_fail(self):
        entry = make_entry(
            batch_ids_included=["A", "B", "C"],
            summary_ids_included=["CPS-A", "CPS-B"],
        )
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed
        assert any("equal length" in e for e in result.errors)


class TestBrierScoreBoundsValidation:
    def test_mean_below_zero_fails(self):
        entry = make_entry(mean_brier_score=-0.1)
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed
        assert any("mean_brier_score" in e for e in result.errors)

    def test_mean_above_one_fails(self):
        entry = make_entry(mean_brier_score=1.1, max_brier_score=1.1)
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed

    def test_min_below_zero_fails(self):
        entry = make_entry(min_brier_score=-0.1)
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed
        assert any("min_brier_score" in e for e in result.errors)

    def test_max_above_one_fails(self):
        entry = make_entry(max_brier_score=1.1, mean_brier_score=1.05)
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed


class TestBrierScoreOrderValidation:
    def test_min_greater_than_mean_fails(self):
        entry = make_entry(
            min_brier_score=0.3,
            mean_brier_score=0.2,
            max_brier_score=0.4,
        )
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed
        assert any("must hold" in e for e in result.errors)

    def test_mean_greater_than_max_fails(self):
        entry = make_entry(
            min_brier_score=0.1,
            mean_brier_score=0.5,
            max_brier_score=0.3,
        )
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed

    def test_min_equal_max_equal_mean_passes(self):
        entry = make_entry(
            min_brier_score=0.15,
            mean_brier_score=0.15,
            max_brier_score=0.15,
        )
        result = validate_cross_batch_aggregator(entry)
        assert result.passed


class TestTrendValidation:
    def test_invalid_trend_fails(self):
        entry = make_entry(trend="unknown")
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed
        assert any("trend" in e for e in result.errors)

    def test_empty_trend_fails(self):
        entry = make_entry(trend="")
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed

    def test_all_valid_trends_pass(self):
        for trend in VALID_TRENDS:
            entry = make_entry(trend=trend)
            result = validate_cross_batch_aggregator(entry)
            assert result.passed, f"trend={trend} should pass"


class TestCandidateCountValidation:
    def test_zero_candidates_fails(self):
        entry = make_entry(total_candidates_evaluated=0)
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed

    def test_one_candidate_fails(self):
        entry = make_entry(total_candidates_evaluated=1)
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed

    def test_two_candidates_passes(self):
        entry = make_entry(total_candidates_evaluated=2)
        result = validate_cross_batch_aggregator(entry)
        assert result.passed


class TestNotesValidation:
    def test_notes_too_long_fails(self):
        entry = make_entry(aggregation_notes="x" * 401)
        result = validate_cross_batch_aggregator(entry)
        assert not result.passed
        assert any("aggregation_notes" in e for e in result.errors)

    def test_notes_exact_max_passes(self):
        entry = make_entry(aggregation_notes="x" * 400)
        result = validate_cross_batch_aggregator(entry)
        assert result.passed

    def test_empty_notes_passes(self):
        entry = make_entry(aggregation_notes="")
        result = validate_cross_batch_aggregator(entry)
        assert result.passed


class TestWarnings:
    def test_poor_mean_brier_warns(self):
        entry = make_entry(
            mean_brier_score=0.3,
            min_brier_score=0.25,
            max_brier_score=0.35,
        )
        result = validate_cross_batch_aggregator(entry)
        assert result.passed
        assert any("calibration below par" in w for w in result.warnings)

    def test_good_brier_no_warn(self):
        entry = make_entry(mean_brier_score=0.15)
        result = validate_cross_batch_aggregator(entry)
        assert result.passed
        assert not any("calibration below par" in w for w in result.warnings)

    def test_high_variance_warns(self):
        entry = make_entry(
            min_brier_score=0.05,
            mean_brier_score=0.15,
            max_brier_score=0.30,
        )
        result = validate_cross_batch_aggregator(entry)
        assert result.passed
        assert any("high variance" in w for w in result.warnings)

    def test_low_variance_no_warn(self):
        entry = make_entry(
            min_brier_score=0.10,
            mean_brier_score=0.15,
            max_brier_score=0.29,
        )
        result = validate_cross_batch_aggregator(entry)
        assert result.passed
        assert not any("high variance" in w for w in result.warnings)

    def test_degrading_trend_warns(self):
        entry = make_entry(trend="degrading")
        result = validate_cross_batch_aggregator(entry)
        assert result.passed
        assert any("degrading" in w for w in result.warnings)

    def test_stable_trend_no_warn(self):
        entry = make_entry(trend="stable")
        result = validate_cross_batch_aggregator(entry)
        assert result.passed
        assert not any("degrading" in w for w in result.warnings)

    def test_improving_trend_no_warn(self):
        entry = make_entry(trend="improving")
        result = validate_cross_batch_aggregator(entry)
        assert result.passed
        assert not any("degrading" in w for w in result.warnings)


class TestDictInterface:
    def test_valid_dict_passes(self):
        data = {
            "aggregator_id": "CBA-001",
            "pipeline_version": "v1.0",
            "batch_ids_included": ["A", "B"],
            "summary_ids_included": ["CPS-A", "CPS-B"],
            "mean_brier_score": 0.15,
            "min_brier_score": 0.10,
            "max_brier_score": 0.20,
            "trend": "stable",
            "total_candidates_evaluated": 100,
            "aggregation_notes": "ok",
            "reviewer": "alice",
        }
        result = validate_cross_batch_aggregator_dict(data)
        assert result.passed

    def test_missing_field_fails(self):
        data = {"aggregator_id": "CBA-001"}
        result = validate_cross_batch_aggregator_dict(data)
        assert not result.passed
        assert any("Missing required field" in e for e in result.errors)

    def test_dict_dry_lab_only_default_true(self):
        data = {
            "aggregator_id": "CBA-001",
            "pipeline_version": "v1.0",
            "batch_ids_included": ["A", "B"],
            "summary_ids_included": ["CPS-A", "CPS-B"],
            "mean_brier_score": 0.15,
            "min_brier_score": 0.10,
            "max_brier_score": 0.20,
            "trend": "stable",
            "total_candidates_evaluated": 100,
            "aggregation_notes": "ok",
            "reviewer": "alice",
        }
        result = validate_cross_batch_aggregator_dict(data)
        assert result.dry_lab_only is True

"""Tests for src/openamp_foundry/evidence/batch_comparative_summary.py (63 tests)."""

import pytest
from openamp_foundry.evidence.batch_comparative_summary import (
    BATCH_COMPARATIVE_SUMMARY_ID_PREFIX,
    VALID_TREND_DIRECTIONS,
    VALID_COMPARISON_STATUSES,
    VALID_QUALITY_TIERS,
    MIN_BATCHES_FOR_TREND,
    MAX_BATCHES_PER_SUMMARY,
    BatchSnapshotEntry,
    BatchComparativeSummary,
    ComparativeSummaryValidationResult,
    build_batch_snapshot_entry,
    build_batch_comparative_summary,
    validate_batch_comparative_summary,
    format_batch_comparative_summary,
)


def _valid_snapshot(batch_id="TOY-BATCH-001", batch_index=0):
    return build_batch_snapshot_entry(
        batch_id=batch_id,
        batch_index=batch_index,
        total_candidates=20,
        n_nominated=5,
        n_rejected=10,
        hit_rate=0.25,
        primary_rejection_reason="toxicity_flag",
        has_calibration_update=False,
        snapshot_note="Toy batch snapshot",
    )


def _valid_summary(batches=None, overall_trend="stable"):
    if batches is None:
        batches = [_valid_snapshot("TOY-BATCH-001", 0), _valid_snapshot("TOY-BATCH-002", 1)]
    return build_batch_comparative_summary(
        summary_id="BCS-001",
        batches=batches,
        overall_trend=overall_trend,
        comparison_status="draft",
        dry_lab_only=True,
        quality_tier="medium",
        trend_note="Stable performance over two toy batches.",
        improvement_observed=False,
        is_example_data=True,
    )


class TestConstants:
    def test_prefix(self):
        assert BATCH_COMPARATIVE_SUMMARY_ID_PREFIX == "BCS-"

    def test_valid_trend_directions_is_frozenset(self):
        assert isinstance(VALID_TREND_DIRECTIONS, frozenset)

    def test_improving_in_trends(self):
        assert "improving" in VALID_TREND_DIRECTIONS

    def test_stable_in_trends(self):
        assert "stable" in VALID_TREND_DIRECTIONS

    def test_declining_in_trends(self):
        assert "declining" in VALID_TREND_DIRECTIONS

    def test_insufficient_data_in_trends(self):
        assert "insufficient_data" in VALID_TREND_DIRECTIONS

    def test_valid_comparison_statuses_is_frozenset(self):
        assert isinstance(VALID_COMPARISON_STATUSES, frozenset)

    def test_draft_in_statuses(self):
        assert "draft" in VALID_COMPARISON_STATUSES

    def test_finalized_in_statuses(self):
        assert "finalized" in VALID_COMPARISON_STATUSES

    def test_valid_quality_tiers_is_frozenset(self):
        assert isinstance(VALID_QUALITY_TIERS, frozenset)

    def test_high_in_tiers(self):
        assert "high" in VALID_QUALITY_TIERS

    def test_insufficient_in_tiers(self):
        assert "insufficient" in VALID_QUALITY_TIERS

    def test_min_batches_for_trend(self):
        assert MIN_BATCHES_FOR_TREND == 2

    def test_max_batches_per_summary(self):
        assert MAX_BATCHES_PER_SUMMARY == 20


class TestBuildBatchSnapshotEntry:
    def test_returns_batch_snapshot_entry(self):
        entry = _valid_snapshot()
        assert isinstance(entry, BatchSnapshotEntry)

    def test_batch_id_stored(self):
        entry = _valid_snapshot("TOY-BATCH-X")
        assert entry.batch_id == "TOY-BATCH-X"

    def test_batch_index_stored(self):
        entry = _valid_snapshot(batch_index=3)
        assert entry.batch_index == 3

    def test_total_candidates_stored(self):
        entry = _valid_snapshot()
        assert entry.total_candidates == 20

    def test_hit_rate_stored(self):
        entry = _valid_snapshot()
        assert entry.hit_rate == 0.25

    def test_has_calibration_update_stored(self):
        entry = build_batch_snapshot_entry(
            batch_id="TOY-001",
            batch_index=0,
            total_candidates=10,
            n_nominated=2,
            n_rejected=5,
            hit_rate=0.2,
            primary_rejection_reason="novelty",
            has_calibration_update=True,
        )
        assert entry.has_calibration_update is True

    def test_snapshot_note_stored(self):
        entry = _valid_snapshot()
        assert entry.snapshot_note == "Toy batch snapshot"


class TestBuildBatchComparativeSummary:
    def test_returns_batch_comparative_summary(self):
        summary = _valid_summary()
        assert isinstance(summary, BatchComparativeSummary)

    def test_summary_id_stored(self):
        summary = _valid_summary()
        assert summary.summary_id == "BCS-001"

    def test_total_batches_computed(self):
        summary = _valid_summary()
        assert summary.total_batches == 2

    def test_overall_trend_stored(self):
        summary = _valid_summary(overall_trend="stable")
        assert summary.overall_trend == "stable"

    def test_comparison_status_stored(self):
        summary = _valid_summary()
        assert summary.comparison_status == "draft"

    def test_dry_lab_only_stored(self):
        summary = _valid_summary()
        assert summary.dry_lab_only is True

    def test_quality_tier_stored(self):
        summary = _valid_summary()
        assert summary.quality_tier == "medium"

    def test_is_example_data_stored(self):
        summary = _valid_summary()
        assert summary.is_example_data is True

    def test_improvement_observed_stored(self):
        summary = _valid_summary()
        assert summary.improvement_observed is False

    def test_single_batch_stored(self):
        summary = build_batch_comparative_summary(
            summary_id="BCS-001",
            batches=[_valid_snapshot()],
            overall_trend="insufficient_data",
            comparison_status="draft",
            dry_lab_only=True,
            quality_tier="insufficient",
        )
        assert summary.total_batches == 1


class TestValidateBatchComparativeSummary:
    def test_valid_summary_passes(self):
        result = validate_batch_comparative_summary(_valid_summary())
        assert result.is_valid

    def test_returns_validation_result(self):
        result = validate_batch_comparative_summary(_valid_summary())
        assert isinstance(result, ComparativeSummaryValidationResult)

    def test_no_violations_on_valid(self):
        result = validate_batch_comparative_summary(_valid_summary())
        assert result.violations == []

    def test_wrong_prefix_fails(self):
        summary = _valid_summary()
        summary.summary_id = "XYZ-001"
        result = validate_batch_comparative_summary(summary)
        assert not result.is_valid
        assert any("BCS-" in v for v in result.violations)

    def test_invalid_trend_fails(self):
        summary = _valid_summary()
        summary.overall_trend = "unknown"
        result = validate_batch_comparative_summary(summary)
        assert not result.is_valid
        assert any("overall_trend" in v for v in result.violations)

    def test_invalid_comparison_status_fails(self):
        summary = _valid_summary()
        summary.comparison_status = "bogus"
        result = validate_batch_comparative_summary(summary)
        assert not result.is_valid

    def test_invalid_quality_tier_fails(self):
        summary = _valid_summary()
        summary.quality_tier = "excellent"
        result = validate_batch_comparative_summary(summary)
        assert not result.is_valid

    def test_total_batches_mismatch_fails(self):
        summary = _valid_summary()
        summary.total_batches = 99
        result = validate_batch_comparative_summary(summary)
        assert not result.is_valid
        assert any("total_batches" in v for v in result.violations)

    def test_too_many_batches_fails(self):
        batches = [_valid_snapshot(f"TOY-{i:03d}", i) for i in range(MAX_BATCHES_PER_SUMMARY + 1)]
        summary = build_batch_comparative_summary(
            summary_id="BCS-001",
            batches=batches,
            overall_trend="stable",
            comparison_status="draft",
            dry_lab_only=True,
            quality_tier="medium",
        )
        result = validate_batch_comparative_summary(summary)
        assert not result.is_valid
        assert any("MAX_BATCHES_PER_SUMMARY" in v for v in result.violations)

    def test_improving_trend_with_single_batch_fails(self):
        summary = build_batch_comparative_summary(
            summary_id="BCS-001",
            batches=[_valid_snapshot()],
            overall_trend="improving",
            comparison_status="draft",
            dry_lab_only=True,
            quality_tier="medium",
        )
        result = validate_batch_comparative_summary(summary)
        assert not result.is_valid
        assert any("MIN_BATCHES_FOR_TREND" in v or "batches" in v for v in result.violations)

    def test_declining_trend_with_single_batch_fails(self):
        summary = build_batch_comparative_summary(
            summary_id="BCS-001",
            batches=[_valid_snapshot()],
            overall_trend="declining",
            comparison_status="draft",
            dry_lab_only=True,
            quality_tier="medium",
        )
        result = validate_batch_comparative_summary(summary)
        assert not result.is_valid

    def test_insufficient_data_with_single_batch_passes(self):
        summary = build_batch_comparative_summary(
            summary_id="BCS-001",
            batches=[_valid_snapshot()],
            overall_trend="insufficient_data",
            comparison_status="draft",
            dry_lab_only=True,
            quality_tier="insufficient",
        )
        result = validate_batch_comparative_summary(summary)
        assert result.is_valid

    def test_dry_lab_false_fails(self):
        summary = _valid_summary()
        summary.dry_lab_only = False
        result = validate_batch_comparative_summary(summary)
        assert not result.is_valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_improvement_observed_with_declining_fails(self):
        summary = _valid_summary(overall_trend="declining")
        summary.improvement_observed = True
        result = validate_batch_comparative_summary(summary)
        assert not result.is_valid
        assert any("improvement_observed" in v for v in result.violations)

    def test_improvement_observed_with_improving_passes(self):
        summary = _valid_summary(overall_trend="improving")
        summary.improvement_observed = True
        result = validate_batch_comparative_summary(summary)
        assert result.is_valid

    def test_batch_empty_id_fails(self):
        batch = _valid_snapshot()
        batch.batch_id = ""
        summary = _valid_summary(batches=[batch, _valid_snapshot("TOY-002", 1)])
        result = validate_batch_comparative_summary(summary)
        assert not result.is_valid
        assert any("batch_id" in v for v in result.violations)

    def test_batch_hit_rate_out_of_range_fails(self):
        batch = _valid_snapshot()
        batch.hit_rate = 1.5
        summary = _valid_summary(batches=[batch, _valid_snapshot("TOY-002", 1)])
        result = validate_batch_comparative_summary(summary)
        assert not result.is_valid
        assert any("hit_rate" in v for v in result.violations)

    def test_batch_nominations_plus_rejections_exceed_total_fails(self):
        batch = _valid_snapshot()
        batch.n_nominated = 15
        batch.n_rejected = 15
        batch.total_candidates = 20
        summary = _valid_summary(batches=[batch, _valid_snapshot("TOY-002", 1)])
        result = validate_batch_comparative_summary(summary)
        assert not result.is_valid
        assert any("total_candidates" in v for v in result.violations)

    def test_multiple_violations_accumulated(self):
        summary = _valid_summary()
        summary.summary_id = "BAD-001"
        summary.overall_trend = "unknown"
        result = validate_batch_comparative_summary(summary)
        assert len(result.violations) >= 2

    def test_all_valid_trends_accepted(self):
        for trend in VALID_TREND_DIRECTIONS:
            batches = [_valid_snapshot("TOY-001", 0), _valid_snapshot("TOY-002", 1)]
            summary = build_batch_comparative_summary(
                summary_id="BCS-001",
                batches=batches,
                overall_trend=trend,
                comparison_status="draft",
                dry_lab_only=True,
                quality_tier="medium",
            )
            result = validate_batch_comparative_summary(summary)
            assert result.is_valid, f"Trend {trend} failed: {result.violations}"


class TestFormatBatchComparativeSummary:
    def test_returns_string(self):
        summary = _valid_summary()
        result = format_batch_comparative_summary(summary)
        assert isinstance(result, str)

    def test_contains_summary_id(self):
        summary = _valid_summary()
        result = format_batch_comparative_summary(summary)
        assert "BCS-001" in result

    def test_contains_trend(self):
        summary = _valid_summary()
        result = format_batch_comparative_summary(summary)
        assert "stable" in result

    def test_contains_total_batches(self):
        summary = _valid_summary()
        result = format_batch_comparative_summary(summary)
        assert "2" in result

    def test_contains_batch_ids(self):
        summary = _valid_summary()
        result = format_batch_comparative_summary(summary)
        assert "TOY-BATCH-001" in result
        assert "TOY-BATCH-002" in result

    def test_contains_hit_rate(self):
        summary = _valid_summary()
        result = format_batch_comparative_summary(summary)
        assert "0.25" in result

    def test_shows_calibration_update(self):
        batch = _valid_snapshot()
        batch.has_calibration_update = True
        summary = build_batch_comparative_summary(
            summary_id="BCS-001",
            batches=[batch, _valid_snapshot("TOY-002", 1)],
            overall_trend="stable",
            comparison_status="draft",
            dry_lab_only=True,
            quality_tier="medium",
        )
        result = format_batch_comparative_summary(summary)
        assert "calibration" in result.lower()

    def test_ends_with_newline(self):
        summary = _valid_summary()
        result = format_batch_comparative_summary(summary)
        assert result.endswith("\n")

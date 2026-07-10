"""Tests for pipeline_run_stability_report — RSR- schema, build, validate, format."""

import statistics

from openamp_foundry.evidence.pipeline_run_stability_report import (
    RunRankRecord,
    PipelineRunStabilityReport,
    RSRValidationResult,
    validate_pipeline_run_stability_report,
    build_pipeline_run_stability_report,
    format_pipeline_run_stability_report,
    VALID_STABILITY_VERDICTS,
    VALID_COMPARISON_METHODS,
    DEFAULT_STABILITY_THRESHOLD,
)


def _make_record(
    run_id: str = "run_001",
    rank: int = 1,
    score: float = 0.95,
    included: bool = True,
) -> RunRankRecord:
    return RunRankRecord(run_id=run_id, rank=rank, score=score, included_in_selection=included)


def _record_list(ranks_and_included):
    return [
        _make_record(run_id=f"run_{i:03d}", rank=r, score=95.0 - r, included=inc)
        for i, (r, inc) in enumerate(ranks_and_included)
    ]


def _report(**overrides) -> PipelineRunStabilityReport:
    records = _record_list([(1, True), (3, True), (2, False)])
    params = dict(
        rsr_id="RSR-001",
        candidate_family_id="AMP-1234",
        pipeline_version="v2.1.0",
        n_runs_compared=3,
        run_records=records,
        rank_min=1,
        rank_max=3,
        rank_std=1.0,
        score_mean=93.0,
        score_std=1.0,
        stability_verdict="stable",
        stability_threshold=2.0,
        always_selected=False,
        never_selected=False,
        selection_consistency_rate=2 / 3,
        dry_lab_only=True,
        limitations=["Toy data only"],
        created_at="2026-07-10",
        comparison_method="identical_inputs",
        n_candidate_families_in_run=100,
    )
    params.update(overrides)
    return PipelineRunStabilityReport(**params)


# =============================================================================
# Class 1 — TestRunRankRecord
# =============================================================================


class TestRunRankRecord:
    def test_valid_construction(self):
        r = _make_record()
        assert r.run_id == "run_001"
        assert r.rank == 1
        assert r.score == 0.95
        assert r.included_in_selection is True

    def test_rank_is_int(self):
        r = _make_record(rank=42)
        assert isinstance(r.rank, int)

    def test_rank_ge_one(self):
        r = _make_record(rank=1)
        assert r.rank >= 1
        r2 = _make_record(rank=999)
        assert r2.rank >= 1

    def test_score_float_positive(self):
        r = _make_record(score=3.14)
        assert isinstance(r.score, float)
        assert r.score > 0

    def test_score_float_negative(self):
        r = _make_record(score=-0.5)
        assert isinstance(r.score, float)

    def test_score_float_zero(self):
        r = _make_record(score=0.0)
        assert r.score == 0.0

    def test_included_in_selection_true(self):
        r = _make_record(included=True)
        assert r.included_in_selection is True

    def test_included_in_selection_false(self):
        r = _make_record(included=False)
        assert r.included_in_selection is False


# =============================================================================
# Class 2 — TestValidatePipelineRunStabilityReport
# =============================================================================


class TestValidatePipelineRunStabilityReport:
    def test_valid_stable_report(self):
        result = validate_pipeline_run_stability_report(_report())
        assert result.valid, f"Expected valid stable report, got violations: {result.violations}"

    def test_valid_borderline_report(self):
        # ranks [1, 4] => stdev = sqrt(4.5) ≈ 2.121, threshold=2.0 => borderline
        records = _record_list([(1, True), (4, False)])
        r = _report(
            run_records=records,
            n_runs_compared=2,
            rank_min=1,
            rank_max=4,
            rank_std=statistics.stdev([1, 4]),
            score_mean=statistics.mean([94.0, 91.0]),
            score_std=statistics.stdev([94.0, 91.0]),
            stability_verdict="borderline",
            always_selected=False,
            never_selected=False,
            selection_consistency_rate=0.5,
        )
        result = validate_pipeline_run_stability_report(r)
        assert result.valid, f"Expected valid borderline, got: {result.violations}"

    def test_valid_unstable_report(self):
        # ranks [1, 10] => stdev = sqrt(40.5) ≈ 6.364, threshold=2.0 => unstable (>= 4.0)
        records = _record_list([(1, False), (10, True)])
        expected_std = statistics.stdev([1, 10])
        r = _report(
            run_records=records,
            n_runs_compared=2,
            rank_min=1,
            rank_max=10,
            rank_std=expected_std,
            score_mean=statistics.mean([94.0, 85.0]),
            score_std=statistics.stdev([94.0, 85.0]),
            stability_verdict="unstable",
            always_selected=False,
            never_selected=False,
            selection_consistency_rate=0.5,
        )
        result = validate_pipeline_run_stability_report(r)
        assert result.valid, f"Expected valid unstable, got: {result.violations}"

    def test_rsr_id_prefix_rejected(self):
        r = _report(rsr_id="BAD-001")
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("rsr_id must start with 'RSR-'" in v for v in result.violations)

    def test_toy_candidate_rejected(self):
        r = _report(candidate_family_id="TOY-abc")
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("TOY-" in v for v in result.violations)

    def test_dry_lab_only_false_rejected(self):
        r = _report(dry_lab_only=False)
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_n_runs_compared_too_low(self):
        r = _report(n_runs_compared=1)
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("n_runs_compared" in v for v in result.violations)

    def test_run_records_length_mismatch(self):
        r = _report(n_runs_compared=2)
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("len(run_records)" in v for v in result.violations)

    def test_rank_min_mismatch(self):
        r = _report(rank_min=999)
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("rank_min" in v for v in result.violations)

    def test_rank_max_mismatch(self):
        r = _report(rank_max=999)
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("rank_max" in v for v in result.violations)

    def test_rank_std_mismatch(self):
        r = _report(rank_std=999.0)
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("rank_std" in v for v in result.violations)

    def test_score_mean_mismatch(self):
        r = _report(score_mean=999.0)
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("score_mean" in v for v in result.violations)

    def test_score_std_mismatch(self):
        r = _report(score_std=999.0)
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("score_std" in v for v in result.violations)

    def test_stable_with_high_std_rejected(self):
        r = _report(rank_std=3.0, stability_verdict="stable")
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("stable" in v and "requires" in v for v in result.violations)

    def test_unstable_with_low_std_rejected(self):
        r = _report(rank_std=1.0, stability_verdict="unstable")
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("unstable" in v and "requires" in v for v in result.violations)

    def test_single_run_blocked(self):
        r = _report(stability_verdict="single_run")
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("single_run" in v for v in result.violations)

    def test_always_selected_mismatch(self):
        r = _report(always_selected=True)
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("always_selected" in v for v in result.violations)

    def test_never_selected_mismatch(self):
        records = _record_list([(1, True), (3, False)])
        r = _report(
            run_records=records,
            n_runs_compared=2,
            rank_min=1,
            rank_max=3,
            rank_std=statistics.stdev([1, 3]),
            score_mean=statistics.mean([94.0, 92.0]),
            score_std=statistics.stdev([94.0, 92.0]),
            never_selected=True,
            always_selected=False,
            selection_consistency_rate=0.5,
        )
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("never_selected" in v for v in result.violations)

    def test_selection_consistency_mismatch(self):
        r = _report(selection_consistency_rate=0.0)
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("selection_consistency_rate" in v for v in result.violations)

    def test_empty_limitations(self):
        r = _report(limitations=[])
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("limitations" in v for v in result.violations)

    def test_invalid_comparison_method(self):
        r = _report(comparison_method="invalid_method")
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("comparison_method" in v for v in result.violations)

    def test_threshold_zero_or_negative(self):
        r = _report(stability_threshold=0.0)
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("stability_threshold" in v for v in result.violations)

    def test_n_candidate_families_too_low(self):
        r = _report(n_candidate_families_in_run=0)
        result = validate_pipeline_run_stability_report(r)
        assert not result.valid
        assert any("n_candidate_families_in_run" in v for v in result.violations)


# =============================================================================
# Class 3 — TestBuildPipelineRunStabilityReport
# =============================================================================


class TestBuildPipelineRunStabilityReport:
    def test_build_stable_computes_correct_stats(self):
        records = _record_list([(1, True), (2, True), (3, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-010",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="different_seeds",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
        )
        assert report.rank_min == 1
        assert report.rank_max == 3
        assert abs(report.rank_std - statistics.stdev([1, 2, 3])) < 0.01

    def test_build_unstable_verdict(self):
        records = _record_list([(1, True), (10, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-011",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="different_seeds",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
        )
        assert report.stability_verdict == "unstable"

    def test_build_borderline_verdict(self):
        records = _record_list([(1, True), (4, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-012",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="different_seeds",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
        )
        assert report.stability_verdict == "borderline"

    def test_build_sets_dry_lab_only_true(self):
        records = _record_list([(1, True), (2, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-013",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="different_seeds",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
        )
        assert report.dry_lab_only is True

    def test_build_all_selected(self):
        records = _record_list([(1, True), (2, True), (3, True)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-014",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
        )
        assert report.always_selected is True
        assert report.never_selected is False
        assert abs(report.selection_consistency_rate - 1.0) < 0.001

    def test_build_none_selected(self):
        records = _record_list([(1, False), (2, False), (3, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-015",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
        )
        assert report.never_selected is True
        assert report.always_selected is False
        assert abs(report.selection_consistency_rate - 0.0) < 0.001

    def test_build_mixed_selection(self):
        records = _record_list([(1, True), (2, False), (3, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-016",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
        )
        assert report.always_selected is False
        assert report.never_selected is False
        assert abs(report.selection_consistency_rate - 1 / 3) < 0.001

    def test_build_less_than_two_raises(self):
        records = [_make_record()]
        import pytest

        with pytest.raises(ValueError, match="At least 2"):
            build_pipeline_run_stability_report(
                rsr_id="RSR-017",
                candidate_family_id="AMP-5678",
                pipeline_version="v3.0.0",
                run_records=records,
                comparison_method="identical_inputs",
                n_candidate_families_in_run=50,
                limitations=["Synthetic data"],
                created_at="2026-07-10",
            )

    def test_build_custom_threshold(self):
        records = _record_list([(1, True), (3, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-018",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
            stability_threshold=5.0,
        )
        assert report.stability_threshold == 5.0
        assert report.stability_verdict == "stable"

    def test_build_default_threshold(self):
        records = _record_list([(1, True), (2, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-019",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
        )
        assert report.stability_threshold == DEFAULT_STABILITY_THRESHOLD

    def test_build_n_runs_matches_len(self):
        records = _record_list([(1, True), (2, False), (3, True), (4, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-020",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
        )
        assert report.n_runs_compared == 4
        assert len(report.run_records) == 4

    def test_build_rank_std_via_stdev(self):
        records = _record_list([(1, True), (5, False), (9, True)])
        expected = statistics.stdev([1, 5, 9])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-021",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
        )
        assert abs(report.rank_std - expected) < 0.01

    def test_build_score_mean_std(self):
        records = [
            _make_record(run_id="r1", rank=1, score=0.95, included=True),
            _make_record(run_id="r2", rank=3, score=0.87, included=True),
            _make_record(run_id="r3", rank=2, score=0.91, included=False),
        ]
        expected_mean = statistics.mean([0.95, 0.87, 0.91])
        expected_std = statistics.stdev([0.95, 0.87, 0.91])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-022",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
        )
        assert abs(report.score_mean - expected_mean) < 0.01
        assert abs(report.score_std - expected_std) < 0.01

    def test_build_stable_below_threshold(self):
        records = _record_list([(1, True), (2, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-023",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
        )
        assert report.stability_verdict == "stable"
        assert report.rank_std < report.stability_threshold

    def test_build_borderline_at_threshold(self):
        records = _record_list([(1, True), (4, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-024",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
        )
        assert report.stability_verdict == "borderline"
        assert report.stability_threshold <= report.rank_std < report.stability_threshold * 2

    def test_build_unstable_at_double_threshold(self):
        records = _record_list([(1, True), (10, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-025",
            candidate_family_id="AMP-5678",
            pipeline_version="v3.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=50,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
        )
        assert report.stability_verdict == "unstable"
        assert report.rank_std >= report.stability_threshold * 2


# =============================================================================
# Class 4 — TestPipelineRunStabilityReportIntegration
# =============================================================================


class TestPipelineRunStabilityReportIntegration:
    def test_round_trip_build_validate(self):
        records = _record_list([(1, True), (2, True), (3, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-100",
            candidate_family_id="AMP-9999",
            pipeline_version="v4.0.0",
            run_records=records,
            comparison_method="bootstrap_resampling",
            n_candidate_families_in_run=200,
            limitations=["Synthetic benchmark data"],
            created_at="2026-07-10",
        )
        result = validate_pipeline_run_stability_report(report)
        assert result.valid, f"Round-trip failed: {result.violations}"

    def test_stable_verdict_stats_consistent(self):
        records = _record_list([(1, True), (2, True)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-101",
            candidate_family_id="AMP-9999",
            pipeline_version="v4.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=200,
            limitations=["Synthetic benchmark data"],
            created_at="2026-07-10",
        )
        assert report.stability_verdict == "stable"
        assert report.rank_min < report.rank_max or report.rank_min == report.rank_max
        assert report.rank_std >= 0

    def test_rank_min_leq_rank_max(self):
        records = _record_list([(5, True), (3, True), (8, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-102",
            candidate_family_id="AMP-9999",
            pipeline_version="v4.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=200,
            limitations=["Synthetic benchmark data"],
            created_at="2026-07-10",
        )
        assert report.rank_min <= report.rank_max

    def test_consistency_rate_in_range(self):
        records = _record_list([(1, True), (2, True), (3, False), (4, True)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-103",
            candidate_family_id="AMP-9999",
            pipeline_version="v4.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=200,
            limitations=["Synthetic benchmark data"],
            created_at="2026-07-10",
        )
        assert 0.0 <= report.selection_consistency_rate <= 1.0

    def test_always_never_mutually_exclusive_mixed(self):
        records = _record_list([(1, True), (2, False)])
        report = build_pipeline_run_stability_report(
            rsr_id="RSR-104",
            candidate_family_id="AMP-9999",
            pipeline_version="v4.0.0",
            run_records=records,
            comparison_method="identical_inputs",
            n_candidate_families_in_run=200,
            limitations=["Synthetic benchmark data"],
            created_at="2026-07-10",
        )
        assert not (report.always_selected and report.never_selected)

    def test_toy_candidate_blocked(self):
        records = _record_list([(1, True), (2, False)])
        report = PipelineRunStabilityReport(
            rsr_id="RSR-105",
            candidate_family_id="TOY-foo",
            pipeline_version="v4.0.0",
            n_runs_compared=2,
            run_records=records,
            rank_min=1,
            rank_max=2,
            rank_std=statistics.stdev([1, 2]),
            score_mean=statistics.mean([94.0, 93.0]),
            score_std=statistics.stdev([94.0, 93.0]),
            stability_verdict="stable",
            stability_threshold=2.0,
            always_selected=False,
            never_selected=False,
            selection_consistency_rate=0.5,
            dry_lab_only=True,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
            comparison_method="identical_inputs",
            n_candidate_families_in_run=100,
        )
        result = validate_pipeline_run_stability_report(report)
        assert not result.valid
        assert any("TOY-" in v for v in result.violations)

    def test_dry_lab_only_false_blocked(self):
        records = _record_list([(1, True), (2, False)])
        report = PipelineRunStabilityReport(
            rsr_id="RSR-106",
            candidate_family_id="AMP-9999",
            pipeline_version="v4.0.0",
            n_runs_compared=2,
            run_records=records,
            rank_min=1,
            rank_max=2,
            rank_std=statistics.stdev([1, 2]),
            score_mean=statistics.mean([94.0, 93.0]),
            score_std=statistics.stdev([94.0, 93.0]),
            stability_verdict="stable",
            stability_threshold=2.0,
            always_selected=False,
            never_selected=False,
            selection_consistency_rate=0.5,
            dry_lab_only=False,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
            comparison_method="identical_inputs",
            n_candidate_families_in_run=100,
        )
        result = validate_pipeline_run_stability_report(report)
        assert not result.valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_invalid_rsr_id_blocked(self):
        records = _record_list([(1, True), (2, False)])
        report = PipelineRunStabilityReport(
            rsr_id="INVALID",
            candidate_family_id="AMP-9999",
            pipeline_version="v4.0.0",
            n_runs_compared=2,
            run_records=records,
            rank_min=1,
            rank_max=2,
            rank_std=statistics.stdev([1, 2]),
            score_mean=statistics.mean([94.0, 93.0]),
            score_std=statistics.stdev([94.0, 93.0]),
            stability_verdict="stable",
            stability_threshold=2.0,
            always_selected=False,
            never_selected=False,
            selection_consistency_rate=0.5,
            dry_lab_only=True,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
            comparison_method="identical_inputs",
            n_candidate_families_in_run=100,
        )
        result = validate_pipeline_run_stability_report(report)
        assert not result.valid
        assert any("RSR-" in v for v in result.violations)

    def test_single_run_blocked_e2e(self):
        records = _record_list([(1, True), (2, False)])
        report = PipelineRunStabilityReport(
            rsr_id="RSR-107",
            candidate_family_id="AMP-9999",
            pipeline_version="v4.0.0",
            n_runs_compared=2,
            run_records=records,
            rank_min=1,
            rank_max=2,
            rank_std=statistics.stdev([1, 2]),
            score_mean=statistics.mean([94.0, 93.0]),
            score_std=statistics.stdev([94.0, 93.0]),
            stability_verdict="single_run",
            stability_threshold=2.0,
            always_selected=False,
            never_selected=False,
            selection_consistency_rate=0.5,
            dry_lab_only=True,
            limitations=["Synthetic data"],
            created_at="2026-07-10",
            comparison_method="identical_inputs",
            n_candidate_families_in_run=100,
        )
        result = validate_pipeline_run_stability_report(report)
        assert not result.valid
        assert any("single_run" in v for v in result.violations)

    def test_build_rejects_bad_params_via_validate(self):
        records = _record_list([(1, True), (2, False)])
        report = PipelineRunStabilityReport(
            rsr_id="RSR-108",
            candidate_family_id="AMP-9999",
            pipeline_version="v4.0.0",
            n_runs_compared=2,
            run_records=records,
            rank_min=1,
            rank_max=2,
            rank_std=statistics.stdev([1, 2]),
            score_mean=statistics.mean([94.0, 93.0]),
            score_std=statistics.stdev([94.0, 93.0]),
            stability_verdict="stable",
            stability_threshold=2.0,
            always_selected=False,
            never_selected=False,
            selection_consistency_rate=0.5,
            dry_lab_only=True,
            limitations=[],
            created_at="2026-07-10",
            comparison_method="identical_inputs",
            n_candidate_families_in_run=100,
        )
        result = validate_pipeline_run_stability_report(report)
        assert not result.valid
        assert any("limitations" in v for v in result.violations)


# =============================================================================
# Class 5 — TestFormatPipelineRunStabilityReport
# =============================================================================


class TestFormatPipelineRunStabilityReport:
    def test_returns_string(self):
        report = _report()
        text = format_pipeline_run_stability_report(report)
        assert isinstance(text, str)

    def test_contains_rsr_id(self):
        report = _report()
        text = format_pipeline_run_stability_report(report)
        assert "RSR-001" in text

    def test_contains_stability_verdict(self):
        report = _report()
        text = format_pipeline_run_stability_report(report)
        assert "stable" in text

    def test_contains_n_runs_compared(self):
        report = _report()
        text = format_pipeline_run_stability_report(report)
        assert "3" in text

    def test_contains_selection_rate(self):
        report = _report()
        text = format_pipeline_run_stability_report(report)
        assert "Selection Consistency" in text

    def test_contains_comparison_method(self):
        report = _report()
        text = format_pipeline_run_stability_report(report)
        assert "identical_inputs" in text

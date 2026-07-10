"""Tests for score_enemy_gap_report module — Phase S S1 (SEG-)."""
import pytest
from openamp_foundry.evidence.score_enemy_gap_report import (
    ScoreEnemyGapReport,
    CheapEnemyResult,
    VALID_GAP_VERDICTS,
    VALID_CHEAP_ENEMY_TYPES,
    VALID_GAP_ASSESSMENT_METHODS,
    MINIMUM_MEANINGFUL_GAP,
    validate_score_enemy_gap_report,
    build_score_enemy_gap_report,
    format_score_enemy_gap_report,
)


def _make_enemy(enemy_type="charge_score", enemy_score=0.60, pipeline_score=0.80) -> CheapEnemyResult:
    gap = round(pipeline_score - enemy_score, 6)
    return CheapEnemyResult(
        enemy_type=enemy_type,
        enemy_score=enemy_score,
        pipeline_score=pipeline_score,
        gap=gap,
        gap_exceeds_threshold=gap >= MINIMUM_MEANINGFUL_GAP,
    )


def _make_report(**kwargs) -> ScoreEnemyGapReport:
    enemy = _make_enemy()
    defaults = dict(
        seg_id="SEG-001",
        run_id="RUN-001",
        candidate_family_id="FAM-001",
        gap_verdict="gap_meaningful",
        gap_assessment_method="absolute_difference",
        pipeline_score=0.80,
        best_enemy_score=0.60,
        best_enemy_type="charge_score",
        gap=0.20,
        minimum_meaningful_gap=MINIMUM_MEANINGFUL_GAP,
        n_enemies_tested=1,
        enemy_results=[enemy],
        dry_lab_only=True,
        limitations="Dry-lab scores only. No wet-lab validation performed.",
        notes="",
        fnr_id=None,
    )
    defaults.update(kwargs)
    return ScoreEnemyGapReport(**defaults)


class TestSEGIDValidation:
    def test_valid_seg_id(self):
        r = _make_report(seg_id="SEG-001")
        result = validate_score_enemy_gap_report(r)
        assert result.valid

    def test_invalid_seg_id_missing_prefix(self):
        r = _make_report(seg_id="001")
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("seg_id" in v for v in result.violations)

    def test_invalid_seg_id_wrong_prefix(self):
        r = _make_report(seg_id="FNR-001")
        result = validate_score_enemy_gap_report(r)
        assert not result.valid

    def test_toy_family_id_blocked(self):
        r = _make_report(candidate_family_id="TOY-001")
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("TOY-" in v for v in result.violations)

    def test_run_id_required(self):
        r = _make_report(run_id="")
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("run_id" in v for v in result.violations)

    def test_candidate_family_id_required(self):
        r = _make_report(candidate_family_id="")
        result = validate_score_enemy_gap_report(r)
        assert not result.valid

    def test_fnr_id_prefix_required_when_provided(self):
        r = _make_report(fnr_id="001")
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("fnr_id" in v for v in result.violations)

    def test_fnr_id_valid_when_correct_prefix(self):
        r = _make_report(fnr_id="FNR-001")
        result = validate_score_enemy_gap_report(r)
        assert result.valid

    def test_fnr_id_none_is_valid(self):
        r = _make_report(fnr_id=None)
        result = validate_score_enemy_gap_report(r)
        assert result.valid


class TestGapVerdictValidation:
    def test_all_valid_verdicts_accepted(self):
        for verdict in VALID_GAP_VERDICTS - {"gap_absent", "comparison_not_run"}:
            gap = 0.20 if verdict == "gap_meaningful" else 0.02
            r = _make_report(gap_verdict=verdict, gap=gap)
            result = validate_score_enemy_gap_report(r)
            assert result.valid, f"Expected valid for verdict={verdict}: {result.violations}"

    def test_invalid_verdict_rejected(self):
        r = _make_report(gap_verdict="significant")
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("gap_verdict" in v for v in result.violations)

    def test_gap_meaningful_requires_sufficient_gap(self):
        r = _make_report(gap_verdict="gap_meaningful", gap=0.01)
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("gap_meaningful" in v for v in result.violations)

    def test_gap_meaningful_with_sufficient_gap_valid(self):
        r = _make_report(gap_verdict="gap_meaningful", gap=0.20)
        result = validate_score_enemy_gap_report(r)
        assert result.valid

    def test_gap_absent_requires_zero_or_negative_gap(self):
        enemy = _make_enemy(enemy_score=0.90, pipeline_score=0.80)
        r = _make_report(
            gap_verdict="gap_absent",
            pipeline_score=0.80,
            best_enemy_score=0.90,
            best_enemy_type="charge_score",
            gap=-0.10,
            n_enemies_tested=1,
            enemy_results=[enemy],
        )
        result = validate_score_enemy_gap_report(r)
        assert result.valid

    def test_gap_absent_with_positive_gap_rejected(self):
        r = _make_report(gap_verdict="gap_absent", gap=0.10)
        result = validate_score_enemy_gap_report(r)
        assert not result.valid

    def test_comparison_not_run_with_zero_enemies(self):
        r = _make_report(
            gap_verdict="comparison_not_run",
            n_enemies_tested=0,
            enemy_results=[],
            gap=0.80,
            best_enemy_score=0.0,
            best_enemy_type="random_baseline",
        )
        result = validate_score_enemy_gap_report(r)
        assert result.valid

    def test_comparison_not_run_with_enemies_rejected(self):
        r = _make_report(gap_verdict="comparison_not_run", n_enemies_tested=1)
        result = validate_score_enemy_gap_report(r)
        assert not result.valid

    def test_gap_marginal_valid(self):
        r = _make_report(gap_verdict="gap_marginal", gap=0.02)
        result = validate_score_enemy_gap_report(r)
        assert result.valid


class TestScoreValidation:
    def test_pipeline_score_out_of_range_rejected(self):
        r = _make_report(pipeline_score=1.5)
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("pipeline_score" in v for v in result.violations)

    def test_pipeline_score_negative_rejected(self):
        r = _make_report(pipeline_score=-0.1)
        result = validate_score_enemy_gap_report(r)
        assert not result.valid

    def test_best_enemy_score_out_of_range_rejected(self):
        r = _make_report(best_enemy_score=1.5)
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("best_enemy_score" in v for v in result.violations)

    def test_best_enemy_score_zero_valid(self):
        r = _make_report(
            pipeline_score=0.80,
            best_enemy_score=0.0,
            gap=0.80,
            best_enemy_type="random_baseline",
        )
        result = validate_score_enemy_gap_report(r)
        assert result.valid

    def test_gap_inconsistent_with_scores_rejected(self):
        r = _make_report(pipeline_score=0.80, best_enemy_score=0.60, gap=0.50)
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("inconsistent" in v for v in result.violations)

    def test_gap_consistent_with_scores_valid(self):
        r = _make_report(pipeline_score=0.80, best_enemy_score=0.60, gap=0.20)
        result = validate_score_enemy_gap_report(r)
        assert result.valid

    def test_minimum_meaningful_gap_must_be_positive(self):
        r = _make_report(minimum_meaningful_gap=0.0)
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("minimum_meaningful_gap" in v for v in result.violations)


class TestEnemyTypeValidation:
    def test_all_valid_enemy_types_accepted(self):
        for etype in VALID_CHEAP_ENEMY_TYPES:
            r = _make_report(
                best_enemy_type=etype,
                enemy_results=[_make_enemy(enemy_type=etype)],
            )
            result = validate_score_enemy_gap_report(r)
            assert result.valid, f"Expected valid for enemy_type={etype}: {result.violations}"

    def test_invalid_enemy_type_rejected(self):
        r = _make_report(best_enemy_type="neural_network_score")
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("best_enemy_type" in v for v in result.violations)

    def test_n_enemies_must_be_positive(self):
        r = _make_report(n_enemies_tested=0, enemy_results=[_make_enemy()])
        result = validate_score_enemy_gap_report(r)
        assert not result.valid

    def test_n_enemies_must_match_results_count(self):
        r = _make_report(n_enemies_tested=2, enemy_results=[_make_enemy()])
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("n_enemies_tested" in v for v in result.violations)

    def test_enemy_result_with_invalid_type_rejected(self):
        bad_enemy = CheapEnemyResult(
            enemy_type="bad_type",
            enemy_score=0.60,
            pipeline_score=0.80,
            gap=0.20,
            gap_exceeds_threshold=True,
        )
        r = _make_report(enemy_results=[bad_enemy])
        result = validate_score_enemy_gap_report(r)
        assert not result.valid

    def test_enemy_result_score_out_of_range_rejected(self):
        bad_enemy = CheapEnemyResult(
            enemy_type="charge_score",
            enemy_score=1.5,
            pipeline_score=0.80,
            gap=-0.70,
            gap_exceeds_threshold=False,
        )
        r = _make_report(enemy_results=[bad_enemy], best_enemy_score=1.5)
        result = validate_score_enemy_gap_report(r)
        assert not result.valid


class TestAssessmentMethodValidation:
    def test_all_valid_methods_accepted(self):
        for method in VALID_GAP_ASSESSMENT_METHODS:
            r = _make_report(gap_assessment_method=method)
            result = validate_score_enemy_gap_report(r)
            assert result.valid, f"Expected valid for method={method}: {result.violations}"

    def test_invalid_method_rejected(self):
        r = _make_report(gap_assessment_method="t_test")
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("gap_assessment_method" in v for v in result.violations)


class TestDryLabAndLimitations:
    def test_dry_lab_only_false_rejected(self):
        r = _make_report(dry_lab_only=False)
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_limitations_required(self):
        r = _make_report(limitations="")
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert any("limitations" in v for v in result.violations)

    def test_limitations_too_short_rejected(self):
        r = _make_report(limitations="Too short")
        result = validate_score_enemy_gap_report(r)
        assert not result.valid

    def test_limitations_sufficient_valid(self):
        r = _make_report(limitations="Dry-lab scores only. No wet-lab validation performed.")
        result = validate_score_enemy_gap_report(r)
        assert result.valid


class TestBuildAndFormat:
    def test_build_auto_computes_gap_meaningful(self):
        enemy = _make_enemy(enemy_score=0.60, pipeline_score=0.80)
        report = build_score_enemy_gap_report(
            seg_id="SEG-001",
            run_id="RUN-001",
            candidate_family_id="FAM-001",
            gap_assessment_method="absolute_difference",
            pipeline_score=0.80,
            enemy_results=[enemy],
            limitations="Dry-lab scores only. No wet-lab validation performed.",
        )
        assert report.gap_verdict == "gap_meaningful"
        assert report.dry_lab_only is True

    def test_build_auto_computes_gap_absent(self):
        enemy = _make_enemy(enemy_score=0.90, pipeline_score=0.80)
        report = build_score_enemy_gap_report(
            seg_id="SEG-001",
            run_id="RUN-001",
            candidate_family_id="FAM-001",
            gap_assessment_method="absolute_difference",
            pipeline_score=0.80,
            enemy_results=[enemy],
            limitations="Dry-lab scores only. No wet-lab validation performed.",
        )
        assert report.gap_verdict == "gap_absent"

    def test_build_auto_computes_gap_marginal(self):
        enemy = _make_enemy(enemy_score=0.77, pipeline_score=0.80)
        report = build_score_enemy_gap_report(
            seg_id="SEG-001",
            run_id="RUN-001",
            candidate_family_id="FAM-001",
            gap_assessment_method="absolute_difference",
            pipeline_score=0.80,
            enemy_results=[enemy],
            limitations="Dry-lab scores only. No wet-lab validation performed.",
        )
        assert report.gap_verdict == "gap_marginal"

    def test_build_comparison_not_run_when_no_enemies(self):
        report = build_score_enemy_gap_report(
            seg_id="SEG-001",
            run_id="RUN-001",
            candidate_family_id="FAM-001",
            gap_assessment_method="absolute_difference",
            pipeline_score=0.80,
            enemy_results=[],
            limitations="Dry-lab scores only. No wet-lab validation performed.",
        )
        assert report.gap_verdict == "comparison_not_run"
        assert report.n_enemies_tested == 0

    def test_build_picks_best_enemy(self):
        enemies = [
            _make_enemy("charge_score", 0.60, 0.80),
            _make_enemy("length_score", 0.70, 0.80),
            _make_enemy("hydrophobicity_score", 0.55, 0.80),
        ]
        report = build_score_enemy_gap_report(
            seg_id="SEG-001",
            run_id="RUN-001",
            candidate_family_id="FAM-001",
            gap_assessment_method="absolute_difference",
            pipeline_score=0.80,
            enemy_results=enemies,
            limitations="Dry-lab scores only. No wet-lab validation performed.",
        )
        assert report.best_enemy_type == "length_score"
        assert report.best_enemy_score == 0.70

    def test_build_raises_on_invalid(self):
        with pytest.raises(ValueError):
            build_score_enemy_gap_report(
                seg_id="INVALID",
                run_id="RUN-001",
                candidate_family_id="FAM-001",
                gap_assessment_method="absolute_difference",
                pipeline_score=0.80,
                enemy_results=[_make_enemy()],
                limitations="Dry-lab scores only.",
            )

    def test_format_includes_seg_id(self):
        r = _make_report()
        text = format_score_enemy_gap_report(r)
        assert "SEG-001" in text

    def test_format_includes_verdict(self):
        r = _make_report()
        text = format_score_enemy_gap_report(r)
        assert "gap_meaningful" in text

    def test_format_includes_scores(self):
        r = _make_report()
        text = format_score_enemy_gap_report(r)
        assert "0.8" in text

    def test_format_includes_limitations(self):
        r = _make_report()
        text = format_score_enemy_gap_report(r)
        assert "Dry-lab" in text

    def test_format_includes_fnr_link_when_present(self):
        r = _make_report(fnr_id="FNR-001")
        text = format_score_enemy_gap_report(r)
        assert "FNR-001" in text

    def test_format_excludes_fnr_when_absent(self):
        r = _make_report(fnr_id=None)
        text = format_score_enemy_gap_report(r)
        assert "FNR Link" not in text

    def test_format_is_multiline(self):
        r = _make_report()
        text = format_score_enemy_gap_report(r)
        assert "\n" in text

    def test_valid_report_passes_validation(self):
        r = _make_report()
        result = validate_score_enemy_gap_report(r)
        assert result.valid
        assert result.violations == []

    def test_multiple_violations_collected(self):
        r = _make_report(seg_id="INVALID", gap_verdict="bad_verdict")
        result = validate_score_enemy_gap_report(r)
        assert not result.valid
        assert len(result.violations) >= 2

    def test_minimum_meaningful_gap_constant_value(self):
        assert MINIMUM_MEANINGFUL_GAP == 0.05

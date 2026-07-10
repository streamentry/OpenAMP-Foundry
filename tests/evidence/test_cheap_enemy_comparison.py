"""Tests for cheap_enemy_comparison module (C9)."""
import pytest

from openamp_foundry.evidence.cheap_enemy_comparison import (
    CheapEnemyComparisonReport,
    EnemyResult,
    compute_cheap_enemy_comparison,
    format_cheap_enemy_comparison,
)


# --- EnemyResult ---

class TestEnemyResult:
    def test_is_dataclass(self):
        r = EnemyResult(
            enemy_name="charge_threshold",
            enemy_score=0.5,
            advanced_score=0.7,
            margin=0.2,
            beats_enemy=True,
        )
        assert isinstance(r, EnemyResult)

    def test_fields_accessible(self):
        r = EnemyResult("test", 0.3, 0.5, 0.2, True)
        assert r.enemy_name == "test"
        assert r.enemy_score == 0.3
        assert r.advanced_score == 0.5
        assert r.margin == pytest.approx(0.2)
        assert r.beats_enemy is True


# --- compute_cheap_enemy_comparison ---

class TestComputeCheapEnemyComparison:
    def test_beats_all_enemies(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="ensemble_v1",
            advanced_scorer_score=0.80,
            enemy_scores={"charge_threshold": 0.60, "length_filter": 0.55},
        )
        assert report.all_enemies_beaten is True
        assert report.ranking_authority_granted is True
        assert report.n_beaten == 2
        assert report.n_failed == 0

    def test_fails_one_enemy(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="ensemble_v1",
            advanced_scorer_score=0.60,
            enemy_scores={"charge_threshold": 0.65, "length_filter": 0.55},
        )
        assert report.all_enemies_beaten is False
        assert report.ranking_authority_granted is False
        assert report.n_beaten == 1
        assert report.n_failed == 1
        assert "charge_threshold" in report.failed_enemies

    def test_fails_all_enemies(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="weak_scorer",
            advanced_scorer_score=0.40,
            enemy_scores={"charge_threshold": 0.60, "length_filter": 0.55},
        )
        assert report.all_enemies_beaten is False
        assert report.n_failed == 2
        assert len(report.failed_enemies) == 2

    def test_invalid_bmc_id_raises(self):
        with pytest.raises(ValueError, match="BMC-"):
            compute_cheap_enemy_comparison(
                bmc_id="NOT-VALID",
                metric="precision_at_k",
                advanced_scorer_name="scorer",
                advanced_scorer_score=0.8,
                enemy_scores={"enemy": 0.5},
            )

    def test_empty_enemy_scores_raises(self):
        with pytest.raises(ValueError, match="empty"):
            compute_cheap_enemy_comparison(
                bmc_id="BMC-0001",
                metric="precision_at_k",
                advanced_scorer_name="scorer",
                advanced_scorer_score=0.8,
                enemy_scores={},
            )

    def test_lower_is_better_mode(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0003",
            metric="calibration_error",
            advanced_scorer_name="calibrated_v1",
            advanced_scorer_score=0.05,
            enemy_scores={"isotonic_regression": 0.10},
            higher_is_better=False,
        )
        assert report.all_enemies_beaten is True
        assert report.ranking_authority_granted is True

    def test_lower_is_better_fails(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0003",
            metric="calibration_error",
            advanced_scorer_name="bad_calibration",
            advanced_scorer_score=0.15,
            enemy_scores={"isotonic_regression": 0.10},
            higher_is_better=False,
        )
        assert report.all_enemies_beaten is False
        assert report.ranking_authority_granted is False

    def test_margin_correct_higher_better(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="scorer",
            advanced_scorer_score=0.80,
            enemy_scores={"charge_threshold": 0.60},
        )
        result = report.enemy_results[0]
        assert result.margin == pytest.approx(0.20)

    def test_margin_correct_lower_better(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0003",
            metric="calibration_error",
            advanced_scorer_name="scorer",
            advanced_scorer_score=0.05,
            enemy_scores={"baseline": 0.10},
            higher_is_better=False,
        )
        result = report.enemy_results[0]
        assert result.margin == pytest.approx(0.05)

    def test_bmc_id_stored(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0002",
            metric="auc_roc",
            advanced_scorer_name="scorer",
            advanced_scorer_score=0.75,
            enemy_scores={"baseline": 0.70},
        )
        assert report.bmc_id == "BMC-0002"

    def test_metric_stored(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="enrichment_factor",
            advanced_scorer_name="scorer",
            advanced_scorer_score=3.0,
            enemy_scores={"baseline": 2.0},
        )
        assert report.metric == "enrichment_factor"

    def test_scorer_name_stored(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="my_ensemble",
            advanced_scorer_score=0.8,
            enemy_scores={"baseline": 0.6},
        )
        assert report.advanced_scorer_name == "my_ensemble"

    def test_scorer_score_stored(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="scorer",
            advanced_scorer_score=0.777,
            enemy_scores={"baseline": 0.5},
        )
        assert report.advanced_scorer_score == pytest.approx(0.777)

    def test_n_enemies_correct(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="scorer",
            advanced_scorer_score=0.8,
            enemy_scores={"a": 0.5, "b": 0.6, "c": 0.7},
        )
        assert report.n_enemies == 3

    def test_enemy_results_list_length(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="scorer",
            advanced_scorer_score=0.8,
            enemy_scores={"a": 0.5, "b": 0.6},
        )
        assert len(report.enemy_results) == 2

    def test_returns_dataclass(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="scorer",
            advanced_scorer_score=0.8,
            enemy_scores={"baseline": 0.5},
        )
        assert isinstance(report, CheapEnemyComparisonReport)

    def test_summary_contains_granted_when_all_beaten(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="scorer",
            advanced_scorer_score=0.8,
            enemy_scores={"baseline": 0.5},
        )
        assert "GRANTED" in report.comparison_summary

    def test_summary_contains_denied_when_failed(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="scorer",
            advanced_scorer_score=0.4,
            enemy_scores={"baseline": 0.5},
        )
        assert "DENIED" in report.comparison_summary

    def test_summary_contains_scorer_name(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="my_special_scorer",
            advanced_scorer_score=0.8,
            enemy_scores={"baseline": 0.5},
        )
        assert "my_special_scorer" in report.comparison_summary

    def test_failed_enemies_list_correct(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="scorer",
            advanced_scorer_score=0.5,
            enemy_scores={"weak": 0.4, "strong": 0.6},
        )
        assert "strong" in report.failed_enemies
        assert "weak" not in report.failed_enemies

    def test_exact_tie_does_not_beat(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="scorer",
            advanced_scorer_score=0.5,
            enemy_scores={"baseline": 0.5},
        )
        assert report.all_enemies_beaten is False
        assert report.n_failed == 1

    def test_bmc_id_must_start_with_bmc(self):
        with pytest.raises(ValueError):
            compute_cheap_enemy_comparison("bmc-0001", "metric", "s", 0.5, {"e": 0.3})

    def test_single_enemy_passes(self):
        report = compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="scorer",
            advanced_scorer_score=0.9,
            enemy_scores={"only_enemy": 0.8},
        )
        assert report.all_enemies_beaten is True
        assert report.n_enemies == 1


# --- format_cheap_enemy_comparison ---

class TestFormatCheapEnemyComparison:
    def _passing_report(self) -> CheapEnemyComparisonReport:
        return compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="ensemble_v1",
            advanced_scorer_score=0.80,
            enemy_scores={"charge_threshold": 0.60, "length_filter": 0.55},
        )

    def _failing_report(self) -> CheapEnemyComparisonReport:
        return compute_cheap_enemy_comparison(
            bmc_id="BMC-0001",
            metric="precision_at_k",
            advanced_scorer_name="weak_scorer",
            advanced_scorer_score=0.50,
            enemy_scores={"charge_threshold": 0.60},
        )

    def test_returns_string(self):
        assert isinstance(format_cheap_enemy_comparison(self._passing_report()), str)

    def test_contains_header(self):
        assert "CHEAP ENEMY COMPARISON" in format_cheap_enemy_comparison(self._passing_report())

    def test_contains_bmc_id(self):
        assert "BMC-0001" in format_cheap_enemy_comparison(self._passing_report())

    def test_contains_metric(self):
        assert "precision_at_k" in format_cheap_enemy_comparison(self._passing_report())

    def test_contains_scorer_name(self):
        assert "ensemble_v1" in format_cheap_enemy_comparison(self._passing_report())

    def test_granted_in_passing(self):
        assert "GRANTED" in format_cheap_enemy_comparison(self._passing_report())

    def test_denied_in_failing(self):
        assert "DENIED" in format_cheap_enemy_comparison(self._failing_report())

    def test_pass_label_present(self):
        assert "PASS" in format_cheap_enemy_comparison(self._passing_report())

    def test_fail_label_present(self):
        assert "FAIL" in format_cheap_enemy_comparison(self._failing_report())

    def test_contains_notice(self):
        assert "NOTICE" in format_cheap_enemy_comparison(self._passing_report())

    def test_contains_summary(self):
        report = self._passing_report()
        text = format_cheap_enemy_comparison(report)
        assert report.comparison_summary in text

    def test_enemy_names_in_output(self):
        text = format_cheap_enemy_comparison(self._passing_report())
        assert "charge_threshold" in text
        assert "length_filter" in text

    def test_scores_in_output(self):
        text = format_cheap_enemy_comparison(self._passing_report())
        assert "0.80" in text or "0.8000" in text

    def test_all_enemies_beaten_yes(self):
        text = format_cheap_enemy_comparison(self._passing_report())
        assert "YES" in text

    def test_all_enemies_beaten_no(self):
        text = format_cheap_enemy_comparison(self._failing_report())
        assert "NO" in text

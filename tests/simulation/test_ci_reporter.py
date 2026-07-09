"""Tests for simulation confidence interval reporter."""
from __future__ import annotations

import pytest

from openamp_foundry.simulation.ci_reporter import (
    ScoreCI,
    ci_report,
    compare_cis,
    compute_score_ci,
)
from openamp_foundry.simulation.interfaces import SimulationResult


def _make_result(
    module: str,
    score: float,
    uncertainty: float = 0.1,
    score_key: str = "binding_energy",
) -> SimulationResult:
    return SimulationResult(
        module=module,
        version="0.1.0",
        scope=["bacterial_binding"],
        scores={score_key: score},
        uncertainty=uncertainty,
        calibration_set=None,
        validated_against=["APD3"],
        notes=[],
    )


class TestComputeScoreCI:
    def test_returns_score_ci_with_correct_bounds(self):
        result = _make_result("membrane_proxy", 0.75, uncertainty=0.1)
        ci = compute_score_ci(result)
        assert ci is not None
        assert ci.module_id == "membrane_proxy"
        assert ci.score_key == "binding_energy"
        assert ci.point_estimate == 0.75
        assert ci.uncertainty == 0.1
        assert ci.ci_lower == 0.65
        assert ci.ci_upper == 0.85

    def test_ci_width_equals_two_times_uncertainty(self):
        result = _make_result("membrane_proxy", 0.75, uncertainty=0.1)
        ci = compute_score_ci(result)
        assert ci is not None
        assert ci.ci_width == pytest.approx(0.20)
        assert ci.ci_width == pytest.approx(2 * ci.uncertainty)

    def test_missing_score_key_returns_none(self):
        result = _make_result("membrane_proxy", 0.75, score_key="binding_energy")
        ci = compute_score_ci(result, score_key="other_key")
        assert ci is None

    def test_dry_lab_only_always_true(self):
        result = _make_result("membrane_proxy", 0.75)
        ci = compute_score_ci(result)
        assert ci is not None
        assert ci.dry_lab_only is True


class TestCompareCIs:
    def test_non_overlapping_cis_have_empty_overlaps_with(self):
        cis = [
            ScoreCI(
                module_id="module_a",
                score_key="binding_energy",
                point_estimate=0.2,
                uncertainty=0.05,
                ci_lower=0.15,
                ci_upper=0.25,
                ci_width=0.10,
            ),
            ScoreCI(
                module_id="module_b",
                score_key="binding_energy",
                point_estimate=0.9,
                uncertainty=0.05,
                ci_lower=0.85,
                ci_upper=0.95,
                ci_width=0.10,
            ),
        ]
        result = compare_cis(cis)
        assert result[0].overlaps_with == []
        assert result[1].overlaps_with == []

    def test_overlapping_cis_have_populated_overlaps_with(self):
        cis = [
            ScoreCI(
                module_id="module_a",
                score_key="binding_energy",
                point_estimate=0.5,
                uncertainty=0.3,
                ci_lower=0.2,
                ci_upper=0.8,
                ci_width=0.60,
            ),
            ScoreCI(
                module_id="module_b",
                score_key="binding_energy",
                point_estimate=0.6,
                uncertainty=0.3,
                ci_lower=0.3,
                ci_upper=0.9,
                ci_width=0.60,
            ),
        ]
        result = compare_cis(cis)
        assert "module_b" in result[0].overlaps_with
        assert "module_a" in result[1].overlaps_with

    def test_does_not_mutate_input(self):
        cis = [
            ScoreCI(
                module_id="module_a",
                score_key="binding_energy",
                point_estimate=0.5,
                uncertainty=0.3,
                ci_lower=0.2,
                ci_upper=0.8,
                ci_width=0.60,
            ),
            ScoreCI(
                module_id="module_b",
                score_key="binding_energy",
                point_estimate=0.6,
                uncertainty=0.3,
                ci_lower=0.3,
                ci_upper=0.9,
                ci_width=0.60,
            ),
        ]
        original_ids = [c.module_id for c in cis]
        compare_cis(cis)
        assert [c.overlaps_with for c in cis] == [[], []]
        assert [c.module_id for c in cis] == original_ids

    def test_overlap_example_half_plus_minus_three(self):
        cis = [
            ScoreCI(
                module_id="module_a",
                score_key="binding_energy",
                point_estimate=0.5,
                uncertainty=0.3,
                ci_lower=0.2,
                ci_upper=0.8,
                ci_width=0.60,
            ),
            ScoreCI(
                module_id="module_b",
                score_key="binding_energy",
                point_estimate=0.6,
                uncertainty=0.3,
                ci_lower=0.3,
                ci_upper=0.9,
                ci_width=0.60,
            ),
        ]
        result = compare_cis(cis)
        assert len(result[0].overlaps_with) == 1
        assert len(result[1].overlaps_with) == 1

    def test_no_overlap_example_narrow_cis(self):
        cis = [
            ScoreCI(
                module_id="module_a",
                score_key="binding_energy",
                point_estimate=0.2,
                uncertainty=0.05,
                ci_lower=0.15,
                ci_upper=0.25,
                ci_width=0.10,
            ),
            ScoreCI(
                module_id="module_b",
                score_key="binding_energy",
                point_estimate=0.9,
                uncertainty=0.05,
                ci_lower=0.85,
                ci_upper=0.95,
                ci_width=0.10,
            ),
        ]
        result = compare_cis(cis)
        assert len(result[0].overlaps_with) == 0
        assert len(result[1].overlaps_with) == 0


class TestCIReport:
    def test_empty_results(self):
        report = ci_report([], score_key="binding_energy")
        assert report["n_results"] == 0
        assert report["cis"] == []
        assert report["any_overlap"] is False

    def test_n_results_correct(self):
        results = [
            _make_result("module_a", 0.75),
            _make_result("module_b", 0.80),
        ]
        report = ci_report(results)
        assert report["n_results"] == 2

    def test_dry_lab_only_true(self):
        results = [
            _make_result("module_a", 0.75),
        ]
        report = ci_report(results)
        assert report["dry_lab_only"] is True

    def test_any_overlap_false_when_no_overlaps(self):
        results = [
            _make_result("module_a", 0.2, uncertainty=0.05),
            _make_result("module_b", 0.9, uncertainty=0.05),
        ]
        report = ci_report(results)
        assert report["any_overlap"] is False

    def test_any_overlap_true_when_overlaps_exist(self):
        results = [
            _make_result("module_a", 0.5, uncertainty=0.3),
            _make_result("module_b", 0.6, uncertainty=0.3),
        ]
        report = ci_report(results)
        assert report["any_overlap"] is True

    def test_overlapping_example(self):
        results = [
            _make_result("module_a", 0.5, uncertainty=0.3),
            _make_result("module_b", 0.6, uncertainty=0.3),
        ]
        report = ci_report(results)
        assert report["any_overlap"] is True
        ci_a = [c for c in report["cis"] if c["module_id"] == "module_a"][0]
        ci_b = [c for c in report["cis"] if c["module_id"] == "module_b"][0]
        assert "module_b" in ci_a["overlaps_with"]
        assert "module_a" in ci_b["overlaps_with"]

    def test_non_overlapping_example(self):
        results = [
            _make_result("module_a", 0.2, uncertainty=0.05),
            _make_result("module_b", 0.9, uncertainty=0.05),
        ]
        report = ci_report(results)
        assert report["any_overlap"] is False
        ci_a = [c for c in report["cis"] if c["module_id"] == "module_a"][0]
        ci_b = [c for c in report["cis"] if c["module_id"] == "module_b"][0]
        assert ci_a["overlaps_with"] == []
        assert ci_b["overlaps_with"] == []

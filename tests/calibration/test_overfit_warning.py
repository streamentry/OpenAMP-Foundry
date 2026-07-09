"""Tests for calibration overfit warning module.

Verifies:
  - Critical threshold (cohort_size < 10)
  - Warning threshold (cohort_size < min_recommended and ratio < 3.0)
  - Caution threshold (cohort_size < min_recommended or ratio < 5.0)
  - None level (cohort_size >= min_recommended and ratio >= 5.0)
  - run_overfit_check with mixed severity
  - run_overfit_check all-none
  - run_overfit_check all-critical
  - ratio calculation correctness
  - message non-empty for each level
  - dry_lab_only=True everywhere
  - worst_level logic
  - any_critical / any_warning flags
  - Empty cohort list edge case
  - JSON and Markdown writers produce output
  - Single cohort matches check_cohort_overfit_risk

Honest limitation:
  These tests validate computational logic only. They do not measure
  biological activity, safety, or real-world performance.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

import pytest

from openamp_foundry.calibration.overfit_warning import (
    check_cohort_overfit_risk,
    run_overfit_check,
    write_overfit_check_json,
    write_overfit_check_markdown,
)


class TestCheckCohortOverfitRisk:
    """Single-cohort overfit risk assessment."""

    def test_critical_cohort_size_less_than_10(self):
        result = check_cohort_overfit_risk(
            cohort_size=5, model_params=10, n_features=5
        )
        assert result["warning_level"] == "critical"
        assert result["cohort_size"] == 5
        assert result["dry_lab_only"] is True

    def test_warning_threshold(self):
        result = check_cohort_overfit_risk(
            cohort_size=15, model_params=10, n_features=5, min_recommended=30
        )
        assert result["warning_level"] == "warning"
        assert result["ratio"] < 3.0

    def test_warning_cohort_below_min_recommended_with_low_ratio(self):
        result = check_cohort_overfit_risk(
            cohort_size=20, model_params=10, n_features=3, min_recommended=30
        )
        assert result["warning_level"] == "warning"
        assert result["cohort_size"] < result.get("min_recommended", 30)

    def test_caution_cohort_small_but_ratio_ok(self):
        result = check_cohort_overfit_risk(
            cohort_size=20, model_params=4, n_features=3, min_recommended=30
        )
        assert result["warning_level"] == "caution"
        assert result["ratio"] >= 3.0

    def test_caution_ratio_low_but_cohort_ok(self):
        result = check_cohort_overfit_risk(
            cohort_size=35, model_params=10, n_features=5, min_recommended=30
        )
        assert result["warning_level"] == "caution"
        assert result["cohort_size"] >= 30
        assert result["ratio"] < 5.0

    def test_none_level(self):
        result = check_cohort_overfit_risk(
            cohort_size=100, model_params=10, n_features=5, min_recommended=30
        )
        assert result["warning_level"] == "none"
        assert result["ratio"] >= 5.0

    def test_all_messages_non_empty(self):
        for cohort_size, mp, nf, mr in [
            (5, 10, 5, 30),
            (15, 10, 5, 30),
            (20, 4, 3, 30),
            (100, 10, 5, 30),
        ]:
            result = check_cohort_overfit_risk(
                cohort_size=cohort_size, model_params=mp,
                n_features=nf, min_recommended=mr,
            )
            assert len(result["message"]) > 0
            assert len(result["recommendation"]) > 0

    def test_dry_lab_only_always_true(self):
        for cohort_size in [5, 15, 25, 100]:
            result = check_cohort_overfit_risk(
                cohort_size=cohort_size, model_params=10,
                n_features=5, min_recommended=30,
            )
            assert result["dry_lab_only"] is True

    def test_ratio_calculation(self):
        result = check_cohort_overfit_risk(
            cohort_size=20, model_params=5, n_features=3
        )
        assert result["ratio"] == 4.0

    def test_custom_min_recommended(self):
        result = check_cohort_overfit_risk(
            cohort_size=10, model_params=5, n_features=3, min_recommended=10
        )
        assert result["warning_level"] == "caution"
        assert result["ratio"] == 2.0


class TestRunOverfitCheck:
    """Multi-cohort aggregated overfit check."""

    def test_mixed_severity(self):
        result = run_overfit_check(
            cohort_sizes=[5, 25, 100],
            model_params=10,
            n_features=5,
            min_recommended=30,
        )
        assert len(result["per_cohort"]) == 3
        assert result["worst_level"] == "critical"
        assert result["any_critical"] is True
        assert result["any_warning"] is True
        assert result["dry_lab_only"] is True

    def test_all_none(self):
        result = run_overfit_check(
            cohort_sizes=[100, 200, 300],
            model_params=10,
            n_features=5,
            min_recommended=30,
        )
        assert result["worst_level"] == "none"
        assert result["any_critical"] is False
        assert result["any_warning"] is False
        assert all(c["warning_level"] == "none" for c in result["per_cohort"])

    def test_all_critical(self):
        result = run_overfit_check(
            cohort_sizes=[3, 5, 8],
            model_params=10,
            n_features=5,
        )
        assert result["worst_level"] == "critical"
        assert result["any_critical"] is True
        assert result["any_warning"] is True
        assert all(c["warning_level"] == "critical" for c in result["per_cohort"])

    def test_worst_level_logic(self):
        result = run_overfit_check(
            cohort_sizes=[25, 50],
            model_params=10,
            n_features=5,
            min_recommended=30,
        )
        levels = [c["warning_level"] for c in result["per_cohort"]]
        assert "caution" in levels or "warning" in levels

    def test_any_critical_and_any_warning_flags(self):
        result = run_overfit_check(
            cohort_sizes=[8, 15, 100],
            model_params=10,
            n_features=5,
            min_recommended=30,
        )
        assert result["any_critical"] is True
        assert result["any_warning"] is True

    def test_dry_lab_only_in_summary(self):
        result = run_overfit_check(
            cohort_sizes=[10, 20], model_params=10, n_features=5
        )
        assert result["dry_lab_only"] is True
        for c in result["per_cohort"]:
            assert c["dry_lab_only"] is True

    def test_empty_cohort_list(self):
        result = run_overfit_check(
            cohort_sizes=[], model_params=10, n_features=5
        )
        assert result["per_cohort"] == []
        assert result["worst_level"] == "none"
        assert result["any_critical"] is False
        assert result["any_warning"] is False

    def test_single_cohort_matches_check_function(self):
        direct = check_cohort_overfit_risk(25, 10, 5, min_recommended=30)
        aggregated = run_overfit_check(
            [25], 10, 5, min_recommended=30
        )
        assert len(aggregated["per_cohort"]) == 1
        ac = aggregated["per_cohort"][0]
        for key in ("cohort_size", "model_params", "n_features",
                     "ratio", "warning_level"):
            assert ac[key] == direct[key]

    def test_ratio_zero_division_edge(self):
        result = check_cohort_overfit_risk(
            cohort_size=0, model_params=0, n_features=0
        )
        assert result["warning_level"] == "critical"
        assert result["ratio"] == 0.0


class TestWriters:
    """JSON and Markdown output writers."""

    def test_json_writer(self):
        report = run_overfit_check([8, 25, 50], 10, 5)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            path = f.name
        try:
            write_overfit_check_json(report, path)
            with open(path) as f:
                loaded = json.load(f)
            assert loaded["worst_level"] == report["worst_level"]
            assert loaded["any_critical"] == report["any_critical"]
            assert len(loaded["per_cohort"]) == 3
        finally:
            Path(path).unlink(missing_ok=True)

    def test_markdown_writer(self):
        report = run_overfit_check([8, 25, 50], 10, 5)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            path = f.name
        try:
            write_overfit_check_markdown(report, path)
            with open(path) as f:
                content = f.read()
            assert "# Calibration Overfit Risk Report" in content
            assert "Critical" in content or "critical" in content
            assert "Dry-lab" in content
        finally:
            Path(path).unlink(missing_ok=True)

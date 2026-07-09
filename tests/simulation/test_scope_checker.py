"""Tests for simulation-scope coverage checker."""
import json
import pytest

from openamp_foundry.simulation.interfaces import SimulationResult
from openamp_foundry.simulation.scope_checker import (
    ScopeCoverageResult,
    check_scope_coverage,
    check_result_scope,
    scope_coverage_report,
)


class TestScopeCoverageResult:
    def test_fully_covered(self):
        result = check_scope_coverage("membrane_proxy", ["bacterial_membrane_binding"])
        assert result.is_fully_covered is True
        assert result.covered == ["bacterial_membrane_binding"]
        assert result.uncovered == []

    def test_partially_covered(self):
        result = check_scope_coverage("membrane_proxy", ["bacterial_membrane_binding", "fungal_binding"])
        assert result.is_fully_covered is False
        assert result.uncovered == ["fungal_binding"]
        assert result.covered == ["bacterial_membrane_binding"]

    def test_no_scopes_requested(self):
        result = check_scope_coverage("membrane_proxy", [])
        assert result.coverage_fraction == 1.0
        assert result.is_fully_covered is True

    def test_unknown_module_id(self):
        result = check_scope_coverage("nonexistent_module", ["bacterial_membrane_binding"])
        assert result.module_scopes == []
        assert result.uncovered == ["bacterial_membrane_binding"]
        assert result.is_fully_covered is False

    @pytest.mark.parametrize("func", [
        check_scope_coverage,
        lambda m, s: check_result_scope(
            SimulationResult(
                module=m, version="0.1.0", scope=["bacterial_membrane_binding"],
                scores={"x": 0.5}, uncertainty=0.1, calibration_set=None,
                validated_against=[], notes=[],
            ), s,
        ),
    ])
    def test_dry_lab_only_always_true(self, func):
        if func == check_scope_coverage:
            result = func("membrane_proxy", ["bacterial_membrane_binding"])
        else:
            result = func("membrane_proxy", ["bacterial_membrane_binding"])
        assert result.dry_lab_only is True

    def test_covered_list_correct(self):
        result = check_scope_coverage("membrane_proxy", ["bacterial_membrane_binding", "fungal_binding"])
        assert result.covered == ["bacterial_membrane_binding"]

    def test_uncovered_list_correct(self):
        result = check_scope_coverage("membrane_proxy", ["bacterial_membrane_binding", "fungal_binding"])
        assert result.uncovered == ["fungal_binding"]

    def test_coverage_fraction_half(self):
        result = check_scope_coverage("membrane_proxy", ["bacterial_membrane_binding", "fungal_binding"])
        assert result.coverage_fraction == 0.5

    def test_coverage_fraction_full(self):
        result = check_scope_coverage("membrane_proxy", ["bacterial_membrane_binding"])
        assert result.coverage_fraction == 1.0

    def test_coverage_fraction_zero(self):
        result = check_scope_coverage("structure_proxy", ["bacterial_membrane_binding"])
        assert result.coverage_fraction == 0.0

    def test_check_result_scope_intersection(self):
        result = SimulationResult(
            module="membrane_proxy", version="0.1.0",
            scope=["bacterial_membrane_binding", "extra_scope"],
            scores={"x": 0.5}, uncertainty=0.1, calibration_set=None,
            validated_against=[], notes=[],
        )
        coverage = check_result_scope(result, ["bacterial_membrane_binding", "extra_scope"])
        assert coverage.module_scopes == ["bacterial_membrane_binding"]
        assert coverage.covered == ["bacterial_membrane_binding"]
        assert coverage.uncovered == ["extra_scope"]

    def test_scope_coverage_report_keys(self):
        report = scope_coverage_report("membrane_proxy", ["bacterial_membrane_binding"])
        expected_keys = {
            "module_id", "requested_scopes", "module_scopes",
            "covered", "uncovered", "coverage_fraction",
            "is_fully_covered", "dry_lab_only",
        }
        assert set(report.keys()) == expected_keys

    def test_scope_coverage_report_dry_lab_only(self):
        report = scope_coverage_report("membrane_proxy", ["bacterial_membrane_binding"])
        assert report["dry_lab_only"] is True

    def test_membrane_proxy_covers_bacterial(self):
        result = check_scope_coverage("membrane_proxy", ["bacterial_membrane_binding"])
        assert "bacterial_membrane_binding" in result.covered

    def test_membrane_proxy_does_not_cover_fungal(self):
        result = check_scope_coverage("membrane_proxy", ["fungal_binding"])
        assert "fungal_binding" in result.uncovered

    def test_empty_module_scopes_all_uncovered(self):
        result = check_scope_coverage("external_adapter_placeholder", ["fungal_binding"])
        assert result.uncovered == ["fungal_binding"]
        assert result.coverage_fraction == 0.0

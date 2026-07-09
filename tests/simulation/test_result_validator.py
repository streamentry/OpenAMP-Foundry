"""Tests for SimulationResult validation."""
from __future__ import annotations

import math

import pytest

from openamp_foundry.simulation.interfaces import SimulationResult
from openamp_foundry.simulation.result_validator import (
    validate_simulation_result,
    validate_simulation_result_batch,
)


def _make_valid(**overrides) -> SimulationResult:
    base = SimulationResult(
        module="membrane_proxy",
        version="0.1.0",
        scope=["bacterial_binding"],
        scores={"binding_energy": 0.75},
        uncertainty=0.15,
        calibration_set="demo_amps_2026",
        validated_against=["APD3"],
        notes=["Test result."],
    )
    for k, v in overrides.items():
        setattr(base, k, v)
    return base


class TestValidateSimulationResult:
    def test_valid_result_passes(self):
        result = _make_valid()
        assert validate_simulation_result(result) == []

    def test_empty_module_string(self):
        result = _make_valid(module="")
        errors = validate_simulation_result(result)
        assert any("module" in e for e in errors)

    def test_empty_version_string(self):
        result = _make_valid(version="")
        errors = validate_simulation_result(result)
        assert any("version" in e for e in errors)

    def test_uncertainty_below_zero(self):
        result = _make_valid(uncertainty=-0.1)
        errors = validate_simulation_result(result)
        assert any(">= 0.0" in e for e in errors)

    def test_uncertainty_above_one(self):
        result = _make_valid(uncertainty=1.5)
        errors = validate_simulation_result(result)
        assert any("<= 1.0" in e for e in errors)

    def test_uncertainty_exactly_zero(self):
        result = _make_valid(uncertainty=0.0)
        assert validate_simulation_result(result) == []

    def test_uncertainty_exactly_one_non_strict(self):
        result = _make_valid(uncertainty=1.0)
        assert validate_simulation_result(result) == []

    def test_strict_uncertainty_one_errors(self):
        result = _make_valid(uncertainty=1.0)
        errors = validate_simulation_result(result, strict=True)
        assert any("strict: uncertainty must be < 1.0" in e for e in errors)

    def test_strict_module_dummy_errors(self):
        result = _make_valid(module="dummy")
        errors = validate_simulation_result(result, strict=True)
        assert any("strict: module must not be 'dummy'" in e for e in errors)

    def test_strict_module_contains_stub_errors(self):
        result = _make_valid(module="my_stub_module")
        errors = validate_simulation_result(result, strict=True)
        assert any("strict: module must not contain 'stub'" in e for e in errors)

    def test_strict_module_stub_case_insensitive(self):
        result = _make_valid(module="MyStubProxy")
        errors = validate_simulation_result(result, strict=True)
        assert any("strict: module must not contain 'stub'" in e for e in errors)

    def test_strict_module_dummy_membrane_proxy_passes_dummy_and_stub_check(self):
        result = _make_valid(module="dummy_membrane_proxy")
        errors = validate_simulation_result(result, strict=True)
        assert not any("stub" in e for e in errors)
        assert not any("must not be" in e for e in errors)

    def test_strict_validated_against_empty_errors(self):
        result = _make_valid(validated_against=[])
        errors = validate_simulation_result(result, strict=True)
        assert any("strict: validated_against must be non-empty" in e for e in errors)

    def test_strict_valid_result_passes(self):
        result = _make_valid(uncertainty=0.5, validated_against=["APD3"])
        assert validate_simulation_result(result, strict=True) == []

    def test_scores_with_nan_errors(self):
        result = _make_valid(scores={"x": float("nan")})
        errors = validate_simulation_result(result)
        assert any("finite" in e for e in errors)

    def test_scores_with_inf_errors(self):
        result = _make_valid(scores={"x": float("inf")})
        errors = validate_simulation_result(result)
        assert any("finite" in e for e in errors)


class TestValidateSimulationResultBatch:
    def test_empty_list(self):
        result = validate_simulation_result_batch([])
        assert result["checked"] == 0
        assert result["valid"] == 0
        assert result["invalid"] == 0
        assert result["any_invalid"] is False

    def test_mix_valid_and_invalid(self):
        results = [
            _make_valid(),
            _make_valid(module=""),
            _make_valid(uncertainty=-0.5),
        ]
        result = validate_simulation_result_batch(results)
        assert result["checked"] == 3
        assert result["valid"] == 1
        assert result["invalid"] == 2
        assert result["any_invalid"] is True

    def test_dry_lab_only_true(self):
        result = validate_simulation_result_batch([])
        assert result["dry_lab_only"] is True

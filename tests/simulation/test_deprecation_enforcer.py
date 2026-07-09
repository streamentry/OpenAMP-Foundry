"""Tests for the simulation-module deprecation enforcer."""
from __future__ import annotations

from openamp_foundry.simulation.deprecation_enforcer import (
    BLOCKED_STATUSES,
    DeprecationCheckResult,
    check_module_deprecation,
    enforce_deprecation,
    run_deprecation_check_batch,
)
from openamp_foundry.simulation.interfaces import SimulationResult


class TestDeprecationCheckResult:
    def test_dry_lab_only_always_true(self):
        r = DeprecationCheckResult(
            module_id="test", status="active",
            is_blocked=False, block_reason="",
        )
        assert r.dry_lab_only is True

    def test_to_dict(self):
        r = DeprecationCheckResult(
            module_id="m", status="active",
            is_blocked=False, block_reason="",
        )
        d = r.to_dict()
        assert d["module_id"] == "m"
        assert d["dry_lab_only"] is True


class TestCheckModuleDeprecation:
    def test_active_module_not_blocked(self):
        r = check_module_deprecation("membrane_proxy")
        assert r.is_blocked is False
        assert r.status == "active"
        assert r.block_reason == ""

    def test_deprecated_module_blocked(self):
        r = check_module_deprecation("dummy_membrane_proxy")
        assert r.is_blocked is True
        assert r.status == "deprecated"
        assert "deprecated" in r.block_reason

    def test_unavailable_module_blocked(self):
        r = check_module_deprecation("external_adapter_placeholder")
        assert r.is_blocked is True
        assert r.status == "unavailable"
        assert "unavailable" in r.block_reason

    def test_unknown_module_blocked_with_unknown_status(self):
        r = check_module_deprecation("nonexistent_module")
        assert r.is_blocked is True
        assert r.status == "unknown"
        assert "not found" in r.block_reason

    def test_dry_lab_only_always_true(self):
        r = check_module_deprecation("membrane_proxy")
        assert r.dry_lab_only is True
        r2 = check_module_deprecation("dummy_membrane_proxy")
        assert r2.dry_lab_only is True
        r3 = check_module_deprecation("unknown")
        assert r3.dry_lab_only is True

    def test_membrane_proxy_active_not_blocked(self):
        r = check_module_deprecation("membrane_proxy")
        assert r.is_blocked is False
        assert r.status == "active"


class TestEnforceDeprecation:
    def _make_result(self, module_id: str) -> SimulationResult:
        return SimulationResult(
            module=module_id,
            version="0.1.0",
            scope=["test"],
            scores={"score": 0.5},
            uncertainty=0.1,
            calibration_set=None,
            validated_against=[],
        )

    def test_filters_out_deprecated_results(self):
        results = [
            self._make_result("membrane_proxy"),
            self._make_result("dummy_membrane_proxy"),
        ]
        out = enforce_deprecation(results)
        assert out["blocked"] == 1
        assert len(out["passed_results"]) == 1
        assert out["passed_results"][0].module == "membrane_proxy"

    def test_passed_count_correct(self):
        results = [
            self._make_result("membrane_proxy"),
            self._make_result("structure_proxy"),
            self._make_result("dummy_membrane_proxy"),
        ]
        out = enforce_deprecation(results)
        assert out["total_input"] == 3
        assert out["passed"] == 2
        assert out["blocked"] == 1

    def test_blocked_modules_sorted_and_deduplicated(self):
        results = [
            self._make_result("dummy_membrane_proxy"),
            self._make_result("dummy_membrane_proxy"),
            self._make_result("membrane_proxy"),
        ]
        out = enforce_deprecation(results)
        assert out["blocked_modules"] == ["dummy_membrane_proxy"]

    def test_dry_lab_only_true(self):
        results = [self._make_result("membrane_proxy")]
        out = enforce_deprecation(results)
        assert out["dry_lab_only"] is True

    def test_all_allowed_blocked_zero(self):
        results = [
            self._make_result("membrane_proxy"),
            self._make_result("structure_proxy"),
        ]
        out = enforce_deprecation(results)
        assert out["blocked"] == 0
        assert out["passed"] == 2


class TestRunDeprecationCheckBatch:
    def test_total_correct(self):
        out = run_deprecation_check_batch(
            ["membrane_proxy", "structure_proxy"]
        )
        assert out["total"] == 2

    def test_any_blocked_true_when_blocked(self):
        out = run_deprecation_check_batch(
            ["membrane_proxy", "dummy_membrane_proxy"]
        )
        assert out["any_blocked"] is True
        assert out["blocked"] == 1

    def test_any_blocked_false_when_all_allowed(self):
        out = run_deprecation_check_batch(
            ["membrane_proxy", "structure_proxy"]
        )
        assert out["any_blocked"] is False
        assert out["blocked"] == 0

    def test_dry_lab_only_true(self):
        out = run_deprecation_check_batch(["membrane_proxy"])
        assert out["dry_lab_only"] is True

    def test_membrane_proxy_not_blocked(self):
        out = run_deprecation_check_batch(["membrane_proxy"])
        assert out["any_blocked"] is False
        assert out["results"][0]["is_blocked"] is False

    def test_dummy_membrane_proxy_blocked(self):
        out = run_deprecation_check_batch(["dummy_membrane_proxy"])
        assert out["any_blocked"] is True
        assert out["results"][0]["is_blocked"] is True


class TestBlockedStatuses:
    def test_deprecated_in_blocked(self):
        assert "deprecated" in BLOCKED_STATUSES

    def test_unavailable_in_blocked(self):
        assert "unavailable" in BLOCKED_STATUSES

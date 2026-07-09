"""Tests for fail-closed adapter gate."""
from __future__ import annotations

import pytest

from openamp_foundry.simulation.adapter_gate import (
    FAIL_CLOSED_REASONS,
    AdapterGateResult,
    evaluate_adapter_gate,
    run_adapter_gate_batch,
)
from openamp_foundry.simulation.interfaces import SimulationResult


def _make_result(**overrides) -> SimulationResult:
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


class TestEvaluateAdapterGate:
    def test_timeout_fails_closed(self):
        r = evaluate_adapter_gate("m1", _make_result(), timeout_occurred=True)
        assert r.passed is False
        assert r.failure_reason == "timeout"
        assert r.dry_lab_only is True

    def test_connection_refused_fails_closed(self):
        r = evaluate_adapter_gate("m1", _make_result(), connection_refused=True)
        assert r.passed is False
        assert r.failure_reason == "connection_refused"

    def test_result_none_fails_invalid_response(self):
        r = evaluate_adapter_gate("m1", None)
        assert r.passed is False
        assert r.failure_reason == "invalid_response"

    def test_schema_errors_fails_schema_violation(self):
        r = evaluate_adapter_gate("m1", _make_result(), schema_errors=["field missing"])
        assert r.passed is False
        assert r.failure_reason == "schema_violation"

    def test_module_unavailable_fails(self):
        r = evaluate_adapter_gate("m1", _make_result(), module_unavailable=True)
        assert r.passed is False
        assert r.failure_reason == "module_unavailable"

    def test_baseline_not_beaten_fails(self):
        r = evaluate_adapter_gate("m1", _make_result(), baseline_beaten=False)
        assert r.passed is False
        assert r.failure_reason == "baseline_not_beaten"

    def test_all_clear_passes(self):
        r = evaluate_adapter_gate("m1", _make_result(), baseline_beaten=True)
        assert r.passed is True
        assert r.failure_reason is None

    def test_dry_lab_only_always_true(self):
        for passed in [True, False]:
            r = evaluate_adapter_gate(
                "m1",
                _make_result() if passed else None,
            )
            assert r.dry_lab_only is True

    def test_priority_timeout_beats_connection_refused(self):
        r = evaluate_adapter_gate(
            "m1", _make_result(),
            timeout_occurred=True,
            connection_refused=True,
        )
        assert r.failure_reason == "timeout"

    def test_priority_connection_refused_beats_result_none(self):
        r = evaluate_adapter_gate(
            "m1", None,
            connection_refused=True,
        )
        assert r.failure_reason == "connection_refused"

    def test_priority_schema_errors_beat_module_unavailable(self):
        r = evaluate_adapter_gate(
            "m1", _make_result(),
            schema_errors=["bad field"],
            module_unavailable=True,
        )
        assert r.failure_reason == "schema_violation"

    def test_baseline_beaten_true_does_not_fail(self):
        r = evaluate_adapter_gate("m1", _make_result(), baseline_beaten=True)
        assert r.passed is True

    def test_baseline_beaten_none_does_not_trigger_baseline_check(self):
        r = evaluate_adapter_gate("m1", _make_result(), baseline_beaten=None)
        assert r.passed is True
        assert r.failure_reason is None

    def test_empty_schema_errors_does_not_fail(self):
        r = evaluate_adapter_gate("m1", _make_result(), schema_errors=[])
        assert r.passed is True


class TestRunAdapterGateBatch:
    def test_batch_with_mix_correct_counts(self):
        calls = [
            {"module_id": "m1", "result": _make_result(), "baseline_beaten": True},
            {"module_id": "m2", "result": None},
            {"module_id": "m3", "result": _make_result(), "timeout_occurred": True},
        ]
        out = run_adapter_gate_batch(calls)
        assert out["total"] == 3
        assert out["passed"] == 1
        assert out["failed"] == 2

    def test_batch_any_failed_true_when_any_fail(self):
        calls = [
            {"module_id": "m1", "result": None},
        ]
        out = run_adapter_gate_batch(calls)
        assert out["any_failed"] is True

    def test_batch_any_failed_false_when_all_pass(self):
        calls = [
            {"module_id": "m1", "result": _make_result(), "baseline_beaten": True},
        ]
        out = run_adapter_gate_batch(calls)
        assert out["any_failed"] is False

    def test_batch_dry_lab_only_true(self):
        out = run_adapter_gate_batch([])
        assert out["dry_lab_only"] is True

    def test_batch_results_list_length(self):
        calls = [
            {"module_id": "m1", "result": _make_result()},
            {"module_id": "m2", "result": _make_result()},
        ]
        out = run_adapter_gate_batch(calls)
        assert len(out["results"]) == 2


class TestFailClosedReasons:
    def test_fail_closed_reasons_has_required_keys(self):
        required = {
            "timeout", "connection_refused", "invalid_response",
            "schema_violation", "module_unavailable", "baseline_not_beaten",
        }
        assert required.issubset(set(FAIL_CLOSED_REASONS.keys()))

    def test_all_reasons_have_non_empty_descriptions(self):
        for key, desc in FAIL_CLOSED_REASONS.items():
            assert desc, f"Empty description for reason: {key}"

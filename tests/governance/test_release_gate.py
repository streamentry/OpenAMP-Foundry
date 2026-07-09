"""Tests for release gate validator."""
from __future__ import annotations

from openamp_foundry.governance.release_gate import (
    RELEASE_TYPES,
    UNIVERSAL_GATES,
    EXTRA_GATES_BY_TYPE,
    ReleaseGateResult,
    validate_release_gate,
)


def test_all_universal_gates_pass():
    gates = {g: True for g in UNIVERSAL_GATES}
    gates.update({g: True for g in EXTRA_GATES_BY_TYPE["candidate"]})
    result = validate_release_gate("candidate", "test-artifact", gates)
    assert result.passed
    assert len(result.gates_failed) == 0


def test_candidate_release_all_gates_pass():
    gates = {g: True for g in UNIVERSAL_GATES}
    gates.update({g: True for g in EXTRA_GATES_BY_TYPE["candidate"]})
    result = validate_release_gate("candidate", "cand-v1", gates)
    assert result.passed
    assert result.release_type == "candidate"
    assert result.artifact_id == "cand-v1"


def test_model_release_all_gates_pass():
    gates = {g: True for g in UNIVERSAL_GATES}
    gates.update({g: True for g in EXTRA_GATES_BY_TYPE["model"]})
    result = validate_release_gate("model", "model-xgb-v2", gates)
    assert result.passed
    assert result.release_type == "model"


def test_dataset_release_all_gates_pass():
    gates = {g: True for g in UNIVERSAL_GATES}
    gates.update({g: True for g in EXTRA_GATES_BY_TYPE["dataset"]})
    result = validate_release_gate("dataset", "db-2026", gates)
    assert result.passed
    assert result.release_type == "dataset"


def test_evidence_packet_release_all_gates_pass():
    gates = {g: True for g in UNIVERSAL_GATES}
    gates.update({g: True for g in EXTRA_GATES_BY_TYPE["evidence_packet"]})
    result = validate_release_gate("evidence_packet", "evp-01", gates)
    assert result.passed
    assert result.release_type == "evidence_packet"


def test_schema_release_all_gates_pass():
    gates = {g: True for g in UNIVERSAL_GATES}
    gates.update({g: True for g in EXTRA_GATES_BY_TYPE["schema"]})
    result = validate_release_gate("schema", "schema-v2", gates)
    assert result.passed
    assert result.release_type == "schema"


def test_one_universal_gate_fails():
    gates = {g: True for g in UNIVERSAL_GATES}
    gates["ci_tests_pass"] = False
    result = validate_release_gate("candidate", "test-artifact", gates)
    assert not result.passed
    assert "ci_tests_pass" in result.gates_failed


def test_missing_gate_treated_as_failed():
    gates = {g: True for g in UNIVERSAL_GATES if g != "no_critical_issues"}
    result = validate_release_gate("candidate", "test-artifact", gates)
    assert not result.passed
    assert "no_critical_issues" in result.gates_failed


def test_invalid_release_type():
    gates = {g: True for g in UNIVERSAL_GATES}
    result = validate_release_gate("invalid_type", "test-artifact", gates)
    assert not result.passed
    assert "release_type='invalid_type' not in" in result.errors[0]


def test_empty_artifact_id():
    gates = {g: True for g in UNIVERSAL_GATES}
    result = validate_release_gate("candidate", "", gates)
    assert not result.passed
    assert any("artifact_id must not be empty" in e for e in result.errors)


def test_dry_lab_only_confirmed_false_critical():
    gates = {g: True for g in UNIVERSAL_GATES}
    gates["dry_lab_only_confirmed"] = False
    result = validate_release_gate("candidate", "test-artifact", gates)
    assert not result.passed
    assert any("CRITICAL: dry_lab_only_confirmed must be True" in e for e in result.errors)


def test_all_results_have_dry_lab_only_true():
    gates = {g: True for g in UNIVERSAL_GATES}
    result = validate_release_gate("candidate", "test-artifact", gates)
    assert result.dry_lab_only is True


def test_universal_gates_has_7_entries():
    assert len(UNIVERSAL_GATES) == 7, f"Expected 7, got {len(UNIVERSAL_GATES)}"


def test_release_types_has_5_entries():
    assert len(RELEASE_TYPES) == 5, f"Expected 5, got {len(RELEASE_TYPES)}"


def test_candidate_extra_gates_includes_human_review():
    assert "human_review_complete" in EXTRA_GATES_BY_TYPE["candidate"]


def test_model_extra_gates_includes_baseline_comparison():
    assert "baseline_comparison_present" in EXTRA_GATES_BY_TYPE["model"]


def test_release_gate_result_default_dry_lab_only():
    r = ReleaseGateResult(
        release_type="candidate",
        artifact_id="a",
        passed=True,
        gates_passed=[],
        gates_failed=[],
        errors=[],
        warnings=[],
    )
    assert r.dry_lab_only is True


def test_validate_release_gate_with_unknown_gate_in_status():
    gates = {g: True for g in UNIVERSAL_GATES}
    gates.update({g: True for g in EXTRA_GATES_BY_TYPE["candidate"]})
    gates["some_unknown_gate"] = True
    result = validate_release_gate("candidate", "test-artifact", gates)
    assert result.passed

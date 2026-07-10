"""Tests for PRG- pre-release audit gateway schema."""

import pytest
from openamp_foundry.evidence.pre_release_audit_gateway import (
    PreReleaseAuditGateway,
    GateResult,
    VALID_GATE_STATUSES,
    VALID_RELEASE_VERDICTS,
    REQUIRED_GATES,
    build_pre_release_audit_gateway,
    format_pre_release_audit_gateway,
    validate_pre_release_audit_gateway,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        prg_id="PRG-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        brc_artifact_id="BRC-001",
        brc_verdict="approved",
        pcc_artifact_id="PCC-001",
        pcc_grade="A",
        eci_artifact_id="ECI-001",
        eci_grade="B",
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_pre_release_audit_gateway(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_gate_statuses_is_frozenset():
    assert isinstance(VALID_GATE_STATUSES, frozenset)


def test_valid_gate_statuses_contains_pass():
    assert "pass" in VALID_GATE_STATUSES


def test_valid_gate_statuses_contains_fail():
    assert "fail" in VALID_GATE_STATUSES


def test_valid_gate_statuses_contains_not_evaluated():
    assert "not_evaluated" in VALID_GATE_STATUSES


def test_valid_release_verdicts_is_frozenset():
    assert isinstance(VALID_RELEASE_VERDICTS, frozenset)


def test_valid_release_verdicts_contains_approved():
    assert "approved" in VALID_RELEASE_VERDICTS


def test_valid_release_verdicts_contains_blocked():
    assert "blocked" in VALID_RELEASE_VERDICTS


def test_required_gates_is_tuple():
    assert isinstance(REQUIRED_GATES, tuple)


def test_required_gates_contains_brc():
    assert "BRC" in REQUIRED_GATES


def test_required_gates_contains_pcc():
    assert "PCC" in REQUIRED_GATES


def test_required_gates_contains_eci():
    assert "ECI" in REQUIRED_GATES


def test_required_gates_count():
    assert len(REQUIRED_GATES) == 3


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_pre_release_audit_gateway():
    assert isinstance(_build(), PreReleaseAuditGateway)


def test_build_prg_id_stored():
    assert _build().prg_id == "PRG-001"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_approved_when_all_pass():
    r = _build()
    assert r.release_verdict == "approved"


def test_build_blocked_when_brc_not_approved():
    r = _build(brc_verdict="blocked")
    assert r.release_verdict == "blocked"


def test_build_blocked_when_pcc_grade_c():
    r = _build(pcc_grade="C")
    assert r.release_verdict == "blocked"


def test_build_blocked_when_eci_grade_d():
    r = _build(eci_grade="D")
    assert r.release_verdict == "blocked"


def test_build_approved_with_pcc_grade_b():
    r = _build(pcc_grade="B")
    assert r.release_verdict == "approved"


def test_build_approved_with_eci_grade_a():
    r = _build(eci_grade="A")
    assert r.release_verdict == "approved"


def test_build_n_gates_total_is_3():
    assert _build().n_gates_total == 3


def test_build_n_gates_passed_3_when_all_pass():
    r = _build()
    assert r.n_gates_passed == 3


def test_build_n_gates_failed_0_when_all_pass():
    r = _build()
    assert r.n_gates_failed == 0


def test_build_n_gates_failed_1_on_bad_pcc():
    r = _build(pcc_grade="C")
    assert r.n_gates_failed == 1


def test_build_gate_results_are_gate_result():
    for gr in _build().gate_results:
        assert isinstance(gr, GateResult)


def test_build_gate_results_contain_brc():
    types = [gr.gate_type for gr in _build().gate_results]
    assert "BRC" in types


def test_build_gate_results_contain_pcc():
    types = [gr.gate_type for gr in _build().gate_results]
    assert "PCC" in types


def test_build_gate_results_contain_eci():
    types = [gr.gate_type for gr in _build().gate_results]
    assert "ECI" in types


def test_build_brc_artifact_id_stored():
    r = _build()
    brc_gate = next(gr for gr in r.gate_results if gr.gate_type == "BRC")
    assert brc_gate.artifact_id == "BRC-001"


def test_build_pcc_artifact_id_stored():
    r = _build()
    pcc_gate = next(gr for gr in r.gate_results if gr.gate_type == "PCC")
    assert pcc_gate.artifact_id == "PCC-001"


def test_build_eci_artifact_id_stored():
    r = _build()
    eci_gate = next(gr for gr in r.gate_results if gr.gate_type == "ECI")
    assert eci_gate.artifact_id == "ECI-001"


def test_build_brc_status_pass_when_approved():
    r = _build()
    brc_gate = next(gr for gr in r.gate_results if gr.gate_type == "BRC")
    assert brc_gate.status == "pass"


def test_build_brc_status_fail_when_blocked():
    r = _build(brc_verdict="blocked")
    brc_gate = next(gr for gr in r.gate_results if gr.gate_type == "BRC")
    assert brc_gate.status == "fail"


def test_build_pcc_status_fail_when_grade_d():
    r = _build(pcc_grade="D")
    pcc_gate = next(gr for gr in r.gate_results if gr.gate_type == "PCC")
    assert pcc_gate.status == "fail"


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_prg_id_prefix():
    with pytest.raises(ValueError, match="PRG-"):
        _build(prg_id="BAD-001")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_prg_id():
    assert "PRG-001" in format_pre_release_audit_gateway(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_pre_release_audit_gateway(_build())


def test_format_contains_verdict():
    assert "approved" in format_pre_release_audit_gateway(_build())


def test_format_contains_pass_markers():
    assert "[PASS]" in format_pre_release_audit_gateway(_build())


def test_format_contains_fail_markers_when_blocked():
    r = _build(pcc_grade="D")
    assert "[FAIL]" in format_pre_release_audit_gateway(r)


def test_format_contains_gate_types():
    formatted = format_pre_release_audit_gateway(_build())
    for gt in REQUIRED_GATES:
        assert gt in formatted


def test_format_contains_limitations():
    assert "dry-lab only" in format_pre_release_audit_gateway(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_pre_release_audit_gateway(_build())


def test_format_is_string():
    assert isinstance(format_pre_release_audit_gateway(_build()), str)

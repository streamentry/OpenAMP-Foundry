"""Tests for V5G- Phase V completeness gate schema."""

import pytest
from openamp_foundry.evidence.phase_v_completeness_gate import (
    PhaseVCompletenessGate,
    V5ComponentCheck,
    REQUIRED_V5_COMPONENTS,
    VALID_V5G_VERDICTS,
    build_phase_v_completeness_gate,
    format_phase_v_completeness_gate,
    validate_phase_v_completeness_gate,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        v5g_id="V5G-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        prg_artifact_id="PRG-001",
        ebm_artifact_id="EBM-001",
        srs_artifact_id="SRS-001",
        erp_artifact_id="ERP-001",
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_phase_v_completeness_gate(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_required_v5_components_is_tuple():
    assert isinstance(REQUIRED_V5_COMPONENTS, tuple)


def test_required_v5_components_contains_prg():
    assert "PRG" in REQUIRED_V5_COMPONENTS


def test_required_v5_components_contains_ebm():
    assert "EBM" in REQUIRED_V5_COMPONENTS


def test_required_v5_components_contains_srs():
    assert "SRS" in REQUIRED_V5_COMPONENTS


def test_required_v5_components_contains_erp():
    assert "ERP" in REQUIRED_V5_COMPONENTS


def test_required_v5_components_count():
    assert len(REQUIRED_V5_COMPONENTS) == 4


def test_valid_v5g_verdicts_is_frozenset():
    assert isinstance(VALID_V5G_VERDICTS, frozenset)


def test_valid_v5g_verdicts_contains_ready():
    assert "ready" in VALID_V5G_VERDICTS


def test_valid_v5g_verdicts_contains_blocked():
    assert "blocked" in VALID_V5G_VERDICTS


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_phase_v_completeness_gate():
    assert isinstance(_build(), PhaseVCompletenessGate)


def test_build_v5g_id_stored():
    assert _build().v5g_id == "V5G-001"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_n_components_required_is_4():
    assert _build().n_components_required == 4


def test_build_all_present_gives_ready():
    assert _build().gate_verdict == "ready"


def test_build_all_present_n_components_present_4():
    assert _build().n_components_present == 4


def test_build_all_present_missing_is_empty():
    assert _build().missing_component_types == []


def test_build_component_checks_length():
    assert len(_build().component_checks) == 4


def test_build_component_checks_are_v5_component_check():
    for c in _build().component_checks:
        assert isinstance(c, V5ComponentCheck)


def test_build_prg_check_present():
    checks = {c.component_type: c for c in _build().component_checks}
    assert checks["PRG"].present is True


def test_build_ebm_check_present():
    checks = {c.component_type: c for c in _build().component_checks}
    assert checks["EBM"].present is True


def test_build_srs_check_present():
    checks = {c.component_type: c for c in _build().component_checks}
    assert checks["SRS"].present is True


def test_build_erp_check_present():
    checks = {c.component_type: c for c in _build().component_checks}
    assert checks["ERP"].present is True


def test_build_prg_artifact_id_stored():
    checks = {c.component_type: c for c in _build().component_checks}
    assert checks["PRG"].artifact_id == "PRG-001"


def test_build_ebm_artifact_id_stored():
    checks = {c.component_type: c for c in _build().component_checks}
    assert checks["EBM"].artifact_id == "EBM-001"


def test_build_srs_artifact_id_stored():
    checks = {c.component_type: c for c in _build().component_checks}
    assert checks["SRS"].artifact_id == "SRS-001"


def test_build_erp_artifact_id_stored():
    checks = {c.component_type: c for c in _build().component_checks}
    assert checks["ERP"].artifact_id == "ERP-001"


def test_build_missing_prg_gives_blocked():
    r = _build(prg_artifact_id="")
    assert r.gate_verdict == "blocked"


def test_build_missing_prg_n_present_3():
    r = _build(prg_artifact_id="")
    assert r.n_components_present == 3


def test_build_missing_prg_in_missing_list():
    r = _build(prg_artifact_id="")
    assert "PRG" in r.missing_component_types


def test_build_missing_ebm_gives_blocked():
    r = _build(ebm_artifact_id="")
    assert r.gate_verdict == "blocked"


def test_build_missing_srs_gives_blocked():
    r = _build(srs_artifact_id="")
    assert r.gate_verdict == "blocked"


def test_build_missing_erp_gives_blocked():
    r = _build(erp_artifact_id="")
    assert r.gate_verdict == "blocked"


def test_build_all_missing_gives_blocked():
    r = _build(prg_artifact_id="", ebm_artifact_id="", srs_artifact_id="", erp_artifact_id="")
    assert r.gate_verdict == "blocked"


def test_build_all_missing_n_present_0():
    r = _build(prg_artifact_id="", ebm_artifact_id="", srs_artifact_id="", erp_artifact_id="")
    assert r.n_components_present == 0


def test_build_all_missing_missing_list_sorted():
    r = _build(prg_artifact_id="", ebm_artifact_id="", srs_artifact_id="", erp_artifact_id="")
    assert r.missing_component_types == sorted(r.missing_component_types)


def test_build_missing_list_sorted_when_two_missing():
    r = _build(ebm_artifact_id="", srs_artifact_id="")
    assert r.missing_component_types == sorted(r.missing_component_types)


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_v5g_id_prefix():
    with pytest.raises(ValueError, match="V5G-"):
        _build(v5g_id="BAD-001")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_prg_artifact_without_prefix():
    gate = _build()
    gate.component_checks[0].artifact_id = "BAD-001"
    with pytest.raises(ValueError):
        validate_phase_v_completeness_gate(gate)


def test_validate_rejects_invalid_gate_verdict():
    gate = _build()
    gate.gate_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="gate_verdict"):
        validate_phase_v_completeness_gate(gate)


def test_validate_rejects_dry_lab_only_false():
    gate = _build()
    gate.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_phase_v_completeness_gate(gate)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_wrong_n_components_required():
    gate = _build()
    gate.n_components_required = 3
    with pytest.raises(ValueError, match="n_components_required"):
        validate_phase_v_completeness_gate(gate)


def test_validate_rejects_n_present_mismatch():
    gate = _build()
    gate.n_components_present = 99
    with pytest.raises(ValueError, match="n_components_present"):
        validate_phase_v_completeness_gate(gate)


def test_validate_rejects_missing_list_mismatch():
    gate = _build()
    gate.missing_component_types = ["PRG"]
    with pytest.raises(ValueError, match="missing_component_types"):
        validate_phase_v_completeness_gate(gate)


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_v5g_id():
    assert "V5G-001" in format_phase_v_completeness_gate(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_phase_v_completeness_gate(_build())


def test_format_contains_verdict_ready():
    assert "ready" in format_phase_v_completeness_gate(_build())


def test_format_contains_prg():
    assert "PRG" in format_phase_v_completeness_gate(_build())


def test_format_contains_ebm():
    assert "EBM" in format_phase_v_completeness_gate(_build())


def test_format_contains_srs():
    assert "SRS" in format_phase_v_completeness_gate(_build())


def test_format_contains_erp():
    assert "ERP" in format_phase_v_completeness_gate(_build())


def test_format_contains_present_label():
    assert "PRESENT" in format_phase_v_completeness_gate(_build())


def test_format_contains_missing_label_when_blocked():
    r = _build(prg_artifact_id="")
    assert "MISSING" in format_phase_v_completeness_gate(r)


def test_format_contains_limitations():
    assert "dry-lab only" in format_phase_v_completeness_gate(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_phase_v_completeness_gate(_build())


def test_format_is_string():
    assert isinstance(format_phase_v_completeness_gate(_build()), str)

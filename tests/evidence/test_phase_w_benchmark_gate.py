"""Tests for WBG- Phase W benchmark gate schema."""

import pytest
from openamp_foundry.evidence.phase_w_benchmark_gate import (
    PhaseWBenchmarkGate,
    WComponentCheck,
    REQUIRED_W_COMPONENTS,
    VALID_WBG_VERDICTS,
    HARDENED_REQUIRED_PRESENT,
    PARTIALLY_HARDENED_MIN_PRESENT,
    build_phase_w_benchmark_gate,
    format_phase_w_benchmark_gate,
    validate_phase_w_benchmark_gate,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        wbg_id="WBG-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        nch_artifact_id="NCH-001",
        cmc_artifact_id="CMC-001",
        sch_artifact_id="SCH-001",
        bcr_artifact_id="BCR-001",
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_phase_w_benchmark_gate(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_required_w_components_is_tuple():
    assert isinstance(REQUIRED_W_COMPONENTS, tuple)


def test_required_w_components_contains_nch():
    assert "NCH" in REQUIRED_W_COMPONENTS


def test_required_w_components_contains_cmc():
    assert "CMC" in REQUIRED_W_COMPONENTS


def test_required_w_components_contains_sch():
    assert "SCH" in REQUIRED_W_COMPONENTS


def test_required_w_components_contains_bcr():
    assert "BCR" in REQUIRED_W_COMPONENTS


def test_required_w_components_count():
    assert len(REQUIRED_W_COMPONENTS) == 4


def test_valid_wbg_verdicts_is_frozenset():
    assert isinstance(VALID_WBG_VERDICTS, frozenset)


def test_valid_wbg_verdicts_contains_hardened():
    assert "hardened" in VALID_WBG_VERDICTS


def test_valid_wbg_verdicts_contains_partially_hardened():
    assert "partially_hardened" in VALID_WBG_VERDICTS


def test_valid_wbg_verdicts_contains_not_hardened():
    assert "not_hardened" in VALID_WBG_VERDICTS


def test_hardened_required_present():
    assert HARDENED_REQUIRED_PRESENT == 4


def test_partially_hardened_min_present():
    assert PARTIALLY_HARDENED_MIN_PRESENT == 2


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_phase_w_benchmark_gate():
    assert isinstance(_build(), PhaseWBenchmarkGate)


def test_build_wbg_id_stored():
    assert _build().wbg_id == "WBG-001"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_n_components_required_is_4():
    assert _build().n_components_required == 4


def test_build_all_present_gives_hardened():
    assert _build().gate_verdict == "hardened"


def test_build_all_present_n_components_4():
    assert _build().n_components_present == 4


def test_build_all_present_missing_is_empty():
    assert _build().missing_component_types == []


def test_build_component_checks_length():
    assert len(_build().component_checks) == 4


def test_build_component_checks_are_w_component_check():
    for c in _build().component_checks:
        assert isinstance(c, WComponentCheck)


def test_build_nch_check_present():
    checks = {c.component_type: c for c in _build().component_checks}
    assert checks["NCH"].present is True


def test_build_cmc_check_present():
    checks = {c.component_type: c for c in _build().component_checks}
    assert checks["CMC"].present is True


def test_build_sch_check_present():
    checks = {c.component_type: c for c in _build().component_checks}
    assert checks["SCH"].present is True


def test_build_bcr_check_present():
    checks = {c.component_type: c for c in _build().component_checks}
    assert checks["BCR"].present is True


def test_build_nch_artifact_id_stored():
    checks = {c.component_type: c for c in _build().component_checks}
    assert checks["NCH"].artifact_id == "NCH-001"


def test_build_bcr_artifact_id_stored():
    checks = {c.component_type: c for c in _build().component_checks}
    assert checks["BCR"].artifact_id == "BCR-001"


def test_build_missing_one_gives_partially_hardened():
    r = _build(nch_artifact_id="")
    assert r.gate_verdict == "partially_hardened"


def test_build_missing_two_gives_partially_hardened():
    r = _build(nch_artifact_id="", cmc_artifact_id="")
    assert r.gate_verdict == "partially_hardened"


def test_build_missing_three_gives_not_hardened():
    r = _build(nch_artifact_id="", cmc_artifact_id="", sch_artifact_id="")
    assert r.gate_verdict == "not_hardened"


def test_build_all_missing_gives_not_hardened():
    r = _build(nch_artifact_id="", cmc_artifact_id="", sch_artifact_id="", bcr_artifact_id="")
    assert r.gate_verdict == "not_hardened"


def test_build_all_missing_n_present_0():
    r = _build(nch_artifact_id="", cmc_artifact_id="", sch_artifact_id="", bcr_artifact_id="")
    assert r.n_components_present == 0


def test_build_missing_nch_in_missing_list():
    r = _build(nch_artifact_id="")
    assert "NCH" in r.missing_component_types


def test_build_missing_list_sorted():
    r = _build(nch_artifact_id="", bcr_artifact_id="")
    assert r.missing_component_types == sorted(r.missing_component_types)


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_wbg_id_prefix():
    with pytest.raises(ValueError, match="WBG-"):
        _build(wbg_id="BAD-001")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_nch_artifact_without_prefix():
    gate = _build()
    gate.component_checks[0].artifact_id = "BAD-001"
    with pytest.raises(ValueError):
        validate_phase_w_benchmark_gate(gate)


def test_validate_rejects_invalid_gate_verdict():
    gate = _build()
    gate.gate_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="gate_verdict"):
        validate_phase_w_benchmark_gate(gate)


def test_validate_rejects_dry_lab_only_false():
    gate = _build()
    gate.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_phase_w_benchmark_gate(gate)


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
        validate_phase_w_benchmark_gate(gate)


def test_validate_rejects_n_present_mismatch():
    gate = _build()
    gate.n_components_present = 99
    with pytest.raises(ValueError, match="n_components_present"):
        validate_phase_w_benchmark_gate(gate)


def test_validate_rejects_missing_list_mismatch():
    gate = _build()
    gate.missing_component_types = ["NCH"]
    with pytest.raises(ValueError, match="missing_component_types"):
        validate_phase_w_benchmark_gate(gate)


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_wbg_id():
    assert "WBG-001" in format_phase_w_benchmark_gate(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_phase_w_benchmark_gate(_build())


def test_format_contains_hardened_verdict():
    assert "hardened" in format_phase_w_benchmark_gate(_build())


def test_format_contains_nch():
    assert "NCH" in format_phase_w_benchmark_gate(_build())


def test_format_contains_cmc():
    assert "CMC" in format_phase_w_benchmark_gate(_build())


def test_format_contains_sch():
    assert "SCH" in format_phase_w_benchmark_gate(_build())


def test_format_contains_bcr():
    assert "BCR" in format_phase_w_benchmark_gate(_build())


def test_format_contains_present_label():
    assert "PRESENT" in format_phase_w_benchmark_gate(_build())


def test_format_contains_missing_label_when_absent():
    r = _build(nch_artifact_id="")
    assert "MISSING" in format_phase_w_benchmark_gate(r)


def test_format_contains_limitations():
    assert "dry-lab only" in format_phase_w_benchmark_gate(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_phase_w_benchmark_gate(_build())


def test_format_is_string():
    assert isinstance(format_phase_w_benchmark_gate(_build()), str)

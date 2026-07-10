"""Tests for ZAG- Phase Z accountability gate schema."""

import pytest
from openamp_foundry.evidence.phase_z_accountability_gate import (
    PhaseZAccountabilityGate,
    ZComponentCheck,
    REQUIRED_Z_COMPONENTS,
    VALID_ZAG_VERDICTS,
    build_phase_z_accountability_gate,
    format_phase_z_accountability_gate,
    validate_phase_z_accountability_gate,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        zag_id="ZAG-001",
        pipeline_version="v1.0",
        fbh_id="FBH-001",
        bxr_id="BXR-001",
        arg_id="ARG-001",
        cbf_id="CBF-001",
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_phase_z_accountability_gate(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_required_z_components_is_tuple():
    assert isinstance(REQUIRED_Z_COMPONENTS, tuple)


def test_required_z_components_has_four():
    assert len(REQUIRED_Z_COMPONENTS) == 4


def test_required_z_components_contains_fbh():
    assert "FBH" in REQUIRED_Z_COMPONENTS


def test_required_z_components_contains_bxr():
    assert "BXR" in REQUIRED_Z_COMPONENTS


def test_required_z_components_contains_arg():
    assert "ARG" in REQUIRED_Z_COMPONENTS


def test_required_z_components_contains_cbf():
    assert "CBF" in REQUIRED_Z_COMPONENTS


def test_valid_zag_verdicts_is_frozenset():
    assert isinstance(VALID_ZAG_VERDICTS, frozenset)


def test_valid_zag_verdicts_has_three():
    assert len(VALID_ZAG_VERDICTS) == 3


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_phase_z_accountability_gate():
    assert isinstance(_build(), PhaseZAccountabilityGate)


def test_build_zag_id_stored():
    assert _build().zag_id == "ZAG-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_all_present_gives_accountability_verified():
    assert _build().verdict == "accountability_verified"


def test_build_all_present_n_components_4():
    assert _build().n_components_present == 4


def test_build_three_present_gives_accountability_partial():
    r = _build(cbf_id="")
    assert r.verdict == "accountability_partial"


def test_build_two_present_gives_accountability_partial():
    r = _build(arg_id="", cbf_id="")
    assert r.verdict == "accountability_partial"


def test_build_one_present_gives_accountability_not_established():
    r = _build(bxr_id="", arg_id="", cbf_id="")
    assert r.verdict == "accountability_not_established"


def test_build_none_present_gives_accountability_not_established():
    r = _build(fbh_id="", bxr_id="", arg_id="", cbf_id="")
    assert r.verdict == "accountability_not_established"


def test_build_none_present_n_components_0():
    r = _build(fbh_id="", bxr_id="", arg_id="", cbf_id="")
    assert r.n_components_present == 0


def test_build_component_checks_are_z_component_check():
    for c in _build().component_checks:
        assert isinstance(c, ZComponentCheck)


def test_build_component_checks_count():
    assert len(_build().component_checks) == 4


def test_build_fbh_present_true():
    c = next(c for c in _build().component_checks if c.component_type == "FBH")
    assert c.is_present is True


def test_build_fbh_absent_false():
    c = next(
        c
        for c in _build(fbh_id="").component_checks
        if c.component_type == "FBH"
    )
    assert c.is_present is False


def test_build_fbh_artifact_id_stored():
    c = next(c for c in _build().component_checks if c.component_type == "FBH")
    assert c.artifact_id == "FBH-001"


def test_build_bxr_artifact_id_stored():
    c = next(c for c in _build().component_checks if c.component_type == "BXR")
    assert c.artifact_id == "BXR-001"


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_zag_id_prefix():
    with pytest.raises(ValueError, match="ZAG-"):
        _build(zag_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_wrong_fbh_prefix():
    with pytest.raises(ValueError, match="FBH-"):
        _build(fbh_id="BAD-001")


def test_validate_rejects_wrong_bxr_prefix():
    with pytest.raises(ValueError, match="BXR-"):
        _build(bxr_id="BAD-001")


def test_validate_rejects_wrong_arg_prefix():
    with pytest.raises(ValueError, match="ARG-"):
        _build(arg_id="BAD-001")


def test_validate_rejects_wrong_cbf_prefix():
    with pytest.raises(ValueError, match="CBF-"):
        _build(cbf_id="BAD-001")


def test_validate_rejects_n_components_mismatch():
    zag = _build()
    zag.n_components_present = 99
    with pytest.raises(ValueError, match="n_components_present"):
        validate_phase_z_accountability_gate(zag)


def test_validate_rejects_verdict_mismatch_4_present():
    zag = _build()
    zag.verdict = "accountability_partial"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_z_accountability_gate(zag)


def test_validate_rejects_verdict_mismatch_3_present():
    zag = _build(cbf_id="")
    zag.verdict = "accountability_not_established"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_z_accountability_gate(zag)


def test_validate_rejects_verdict_mismatch_2_present():
    zag = _build(arg_id="", cbf_id="")
    zag.verdict = "accountability_not_established"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_z_accountability_gate(zag)


def test_validate_rejects_verdict_mismatch_1_present():
    zag = _build(bxr_id="", arg_id="", cbf_id="")
    zag.verdict = "accountability_verified"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_z_accountability_gate(zag)


def test_validate_rejects_verdict_mismatch_0_present():
    zag = _build(fbh_id="", bxr_id="", arg_id="", cbf_id="")
    zag.verdict = "accountability_verified"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_z_accountability_gate(zag)


def test_validate_rejects_dry_lab_only_false():
    zag = _build()
    zag.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_phase_z_accountability_gate(zag)


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_invalid_verdict():
    zag = _build()
    zag.verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="verdict"):
        validate_phase_z_accountability_gate(zag)


def test_validate_rejects_wrong_component_count():
    zag = _build()
    zag.component_checks = zag.component_checks[:2]
    with pytest.raises(ValueError, match="component_checks"):
        validate_phase_z_accountability_gate(zag)


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_zag_id():
    assert "ZAG-001" in format_phase_z_accountability_gate(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_phase_z_accountability_gate(_build())


def test_format_contains_verdict():
    assert "accountability_verified" in format_phase_z_accountability_gate(_build())


def test_format_contains_component_name():
    assert "FBH" in format_phase_z_accountability_gate(_build())


def test_format_contains_present_status():
    assert "PRESENT" in format_phase_z_accountability_gate(_build())


def test_format_contains_absent_when_missing():
    assert "ABSENT" in format_phase_z_accountability_gate(_build(cbf_id=""))


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_phase_z_accountability_gate(_build())


def test_format_is_string():
    assert isinstance(format_phase_z_accountability_gate(_build()), str)

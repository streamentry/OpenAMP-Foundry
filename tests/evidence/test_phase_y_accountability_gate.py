"""Tests for YAG- Phase Y accountability gate schema."""

import pytest
from openamp_foundry.evidence.phase_y_accountability_gate import (
    PhaseYAccountabilityGate,
    YComponentCheck,
    REQUIRED_Y_COMPONENTS,
    VALID_YAG_VERDICTS,
    ACCOUNTABILITY_VERIFIED_REQUIRED_PRESENT,
    ACCOUNTABILITY_PARTIAL_MIN_PRESENT,
    build_phase_y_accountability_gate,
    format_phase_y_accountability_gate,
    validate_phase_y_accountability_gate,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        yag_id="YAG-001",
        pipeline_version="v1.0",
        cbr_artifact_id="CBR-001",
        fia_artifact_id="FIA-001",
        sda_artifact_id="SDA-001",
        pmc_artifact_id="PMC-001",
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_phase_y_accountability_gate(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_required_y_components_is_tuple():
    assert isinstance(REQUIRED_Y_COMPONENTS, tuple)


def test_required_y_components_contains_cbr():
    assert "CBR" in REQUIRED_Y_COMPONENTS


def test_required_y_components_contains_fia():
    assert "FIA" in REQUIRED_Y_COMPONENTS


def test_required_y_components_contains_sda():
    assert "SDA" in REQUIRED_Y_COMPONENTS


def test_required_y_components_contains_pmc():
    assert "PMC" in REQUIRED_Y_COMPONENTS


def test_required_y_components_has_four_entries():
    assert len(REQUIRED_Y_COMPONENTS) == 4


def test_valid_yag_verdicts_is_frozenset():
    assert isinstance(VALID_YAG_VERDICTS, frozenset)


def test_valid_yag_verdicts_contains_accountability_verified():
    assert "accountability_verified" in VALID_YAG_VERDICTS


def test_valid_yag_verdicts_contains_accountability_partial():
    assert "accountability_partial" in VALID_YAG_VERDICTS


def test_valid_yag_verdicts_contains_accountability_not_established():
    assert "accountability_not_established" in VALID_YAG_VERDICTS


def test_accountability_verified_required_present():
    assert ACCOUNTABILITY_VERIFIED_REQUIRED_PRESENT == 4


def test_accountability_partial_min_present():
    assert ACCOUNTABILITY_PARTIAL_MIN_PRESENT == 2


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_phase_y_accountability_gate():
    assert isinstance(_build(), PhaseYAccountabilityGate)


def test_build_yag_id_stored():
    assert _build().yag_id == "YAG-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_all_present_gives_accountability_verified():
    assert _build().yag_verdict == "accountability_verified"


def test_build_all_present_n_components_4():
    assert _build().n_components_present == 4


def test_build_three_present_gives_accountability_partial():
    r = _build(pmc_artifact_id="")
    assert r.yag_verdict == "accountability_partial"


def test_build_two_present_gives_accountability_partial():
    r = _build(sda_artifact_id="", pmc_artifact_id="")
    assert r.yag_verdict == "accountability_partial"


def test_build_one_present_gives_accountability_not_established():
    r = _build(fia_artifact_id="", sda_artifact_id="", pmc_artifact_id="")
    assert r.yag_verdict == "accountability_not_established"


def test_build_none_present_gives_accountability_not_established():
    r = _build(
        cbr_artifact_id="",
        fia_artifact_id="",
        sda_artifact_id="",
        pmc_artifact_id="",
    )
    assert r.yag_verdict == "accountability_not_established"


def test_build_none_present_n_components_0():
    r = _build(
        cbr_artifact_id="",
        fia_artifact_id="",
        sda_artifact_id="",
        pmc_artifact_id="",
    )
    assert r.n_components_present == 0


def test_build_component_checks_are_y_component_check():
    for c in _build().component_checks:
        assert isinstance(c, YComponentCheck)


def test_build_component_checks_count():
    assert len(_build().component_checks) == 4


def test_build_cbr_present_true():
    r = _build()
    cbr_check = next(c for c in r.component_checks if c.component_type == "CBR")
    assert cbr_check.present is True


def test_build_cbr_absent_false():
    r = _build(cbr_artifact_id="")
    cbr_check = next(c for c in r.component_checks if c.component_type == "CBR")
    assert cbr_check.present is False


def test_build_pmc_artifact_id_stored():
    r = _build()
    pmc_check = next(c for c in r.component_checks if c.component_type == "PMC")
    assert pmc_check.artifact_id == "PMC-001"


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_yag_id_prefix():
    with pytest.raises(ValueError, match="YAG-"):
        _build(yag_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_wrong_cbr_prefix():
    with pytest.raises(ValueError, match="CBR-"):
        _build(cbr_artifact_id="BAD-001")


def test_validate_rejects_wrong_fia_prefix():
    with pytest.raises(ValueError, match="FIA-"):
        _build(fia_artifact_id="BAD-001")


def test_validate_rejects_wrong_sda_prefix():
    with pytest.raises(ValueError, match="SDA-"):
        _build(sda_artifact_id="BAD-001")


def test_validate_rejects_wrong_pmc_prefix():
    with pytest.raises(ValueError, match="PMC-"):
        _build(pmc_artifact_id="BAD-001")


def test_validate_rejects_n_components_mismatch():
    yag = _build()
    yag.n_components_present = 99
    with pytest.raises(ValueError, match="n_components_present"):
        validate_phase_y_accountability_gate(yag)


def test_validate_rejects_invalid_yag_verdict():
    yag = _build()
    yag.yag_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="yag_verdict"):
        validate_phase_y_accountability_gate(yag)


def test_validate_rejects_dry_lab_only_false():
    yag = _build()
    yag.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_phase_y_accountability_gate(yag)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_wrong_component_count():
    yag = _build()
    yag.component_checks = yag.component_checks[:2]
    with pytest.raises(ValueError, match="component_checks"):
        validate_phase_y_accountability_gate(yag)


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_yag_id():
    assert "YAG-001" in format_phase_y_accountability_gate(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_phase_y_accountability_gate(_build())


def test_format_contains_verdict():
    assert "accountability_verified" in format_phase_y_accountability_gate(_build())


def test_format_contains_cbr():
    assert "CBR" in format_phase_y_accountability_gate(_build())


def test_format_contains_fia():
    assert "FIA" in format_phase_y_accountability_gate(_build())


def test_format_contains_sda():
    assert "SDA" in format_phase_y_accountability_gate(_build())


def test_format_contains_pmc():
    assert "PMC" in format_phase_y_accountability_gate(_build())


def test_format_contains_present_status():
    assert "PRESENT" in format_phase_y_accountability_gate(_build())


def test_format_contains_absent_when_missing():
    assert "ABSENT" in format_phase_y_accountability_gate(_build(pmc_artifact_id=""))


def test_format_contains_limitations():
    assert "dry-lab only" in format_phase_y_accountability_gate(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_phase_y_accountability_gate(_build())


def test_format_is_string():
    assert isinstance(format_phase_y_accountability_gate(_build()), str)

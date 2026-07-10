"""Tests for XLG- Phase X learning gate schema."""

import pytest
from openamp_foundry.evidence.phase_x_learning_gate import (
    PhaseXLearningGate,
    XComponentCheck,
    REQUIRED_X_COMPONENTS,
    VALID_XLG_VERDICTS,
    LEARNING_VERIFIED_REQUIRED_PRESENT,
    LEARNING_IN_PROGRESS_MIN_PRESENT,
    build_phase_x_learning_gate,
    format_phase_x_learning_gate,
    validate_phase_x_learning_gate,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        xlg_id="XLG-001",
        pipeline_version="v1.0",
        mbl_artifact_id="MBL-001",
        cit_artifact_id="CIT-001",
        lpr_artifact_id="LPR-001",
        rcc_artifact_id="RCC-001",
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_phase_x_learning_gate(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_required_x_components_is_tuple():
    assert isinstance(REQUIRED_X_COMPONENTS, tuple)


def test_required_x_components_contains_mbl():
    assert "MBL" in REQUIRED_X_COMPONENTS


def test_required_x_components_contains_cit():
    assert "CIT" in REQUIRED_X_COMPONENTS


def test_required_x_components_contains_lpr():
    assert "LPR" in REQUIRED_X_COMPONENTS


def test_required_x_components_contains_rcc():
    assert "RCC" in REQUIRED_X_COMPONENTS


def test_required_x_components_has_four_entries():
    assert len(REQUIRED_X_COMPONENTS) == 4


def test_valid_xlg_verdicts_is_frozenset():
    assert isinstance(VALID_XLG_VERDICTS, frozenset)


def test_valid_xlg_verdicts_contains_learning_verified():
    assert "learning_verified" in VALID_XLG_VERDICTS


def test_valid_xlg_verdicts_contains_learning_in_progress():
    assert "learning_in_progress" in VALID_XLG_VERDICTS


def test_valid_xlg_verdicts_contains_learning_not_started():
    assert "learning_not_started" in VALID_XLG_VERDICTS


def test_learning_verified_required_present():
    assert LEARNING_VERIFIED_REQUIRED_PRESENT == 4


def test_learning_in_progress_min_present():
    assert LEARNING_IN_PROGRESS_MIN_PRESENT == 2


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_phase_x_learning_gate():
    assert isinstance(_build(), PhaseXLearningGate)


def test_build_xlg_id_stored():
    assert _build().xlg_id == "XLG-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_all_present_gives_learning_verified():
    assert _build().xlg_verdict == "learning_verified"


def test_build_all_present_n_components_4():
    assert _build().n_components_present == 4


def test_build_three_present_gives_learning_in_progress():
    r = _build(rcc_artifact_id="")
    assert r.xlg_verdict == "learning_in_progress"


def test_build_two_present_gives_learning_in_progress():
    r = _build(lpr_artifact_id="", rcc_artifact_id="")
    assert r.xlg_verdict == "learning_in_progress"


def test_build_one_present_gives_learning_not_started():
    r = _build(cit_artifact_id="", lpr_artifact_id="", rcc_artifact_id="")
    assert r.xlg_verdict == "learning_not_started"


def test_build_none_present_gives_learning_not_started():
    r = _build(
        mbl_artifact_id="",
        cit_artifact_id="",
        lpr_artifact_id="",
        rcc_artifact_id="",
    )
    assert r.xlg_verdict == "learning_not_started"


def test_build_none_present_n_components_0():
    r = _build(
        mbl_artifact_id="",
        cit_artifact_id="",
        lpr_artifact_id="",
        rcc_artifact_id="",
    )
    assert r.n_components_present == 0


def test_build_component_checks_are_x_component_check():
    for c in _build().component_checks:
        assert isinstance(c, XComponentCheck)


def test_build_component_checks_count():
    assert len(_build().component_checks) == 4


def test_build_mbl_present_true():
    r = _build()
    mbl_check = next(c for c in r.component_checks if c.component_type == "MBL")
    assert mbl_check.present is True


def test_build_mbl_absent_false():
    r = _build(mbl_artifact_id="")
    mbl_check = next(c for c in r.component_checks if c.component_type == "MBL")
    assert mbl_check.present is False


def test_build_artifact_id_stored():
    r = _build()
    cit_check = next(c for c in r.component_checks if c.component_type == "CIT")
    assert cit_check.artifact_id == "CIT-001"


def test_build_empty_artifact_id_means_absent():
    r = _build(rcc_artifact_id="")
    rcc_check = next(c for c in r.component_checks if c.component_type == "RCC")
    assert rcc_check.artifact_id == ""
    assert rcc_check.present is False


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_xlg_id_prefix():
    with pytest.raises(ValueError, match="XLG-"):
        _build(xlg_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_n_components_mismatch():
    xlg = _build()
    xlg.n_components_present = 99
    with pytest.raises(ValueError, match="n_components_present"):
        validate_phase_x_learning_gate(xlg)


def test_validate_rejects_invalid_xlg_verdict():
    xlg = _build()
    xlg.xlg_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="xlg_verdict"):
        validate_phase_x_learning_gate(xlg)


def test_validate_rejects_wrong_artifact_prefix_mbl():
    with pytest.raises(ValueError, match="MBL-"):
        _build(mbl_artifact_id="BAD-001")


def test_validate_rejects_wrong_artifact_prefix_cit():
    with pytest.raises(ValueError, match="CIT-"):
        _build(cit_artifact_id="BAD-001")


def test_validate_rejects_wrong_artifact_prefix_lpr():
    with pytest.raises(ValueError, match="LPR-"):
        _build(lpr_artifact_id="BAD-001")


def test_validate_rejects_wrong_artifact_prefix_rcc():
    with pytest.raises(ValueError, match="RCC-"):
        _build(rcc_artifact_id="BAD-001")


def test_validate_rejects_dry_lab_only_false():
    xlg = _build()
    xlg.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_phase_x_learning_gate(xlg)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_wrong_component_count():
    xlg = _build()
    xlg.component_checks = xlg.component_checks[:2]
    with pytest.raises(ValueError, match="component_checks"):
        validate_phase_x_learning_gate(xlg)


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_xlg_id():
    assert "XLG-001" in format_phase_x_learning_gate(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_phase_x_learning_gate(_build())


def test_format_contains_verdict():
    assert "learning_verified" in format_phase_x_learning_gate(_build())


def test_format_contains_mbl_component():
    assert "MBL" in format_phase_x_learning_gate(_build())


def test_format_contains_cit_component():
    assert "CIT" in format_phase_x_learning_gate(_build())


def test_format_contains_lpr_component():
    assert "LPR" in format_phase_x_learning_gate(_build())


def test_format_contains_rcc_component():
    assert "RCC" in format_phase_x_learning_gate(_build())


def test_format_contains_present_status():
    assert "PRESENT" in format_phase_x_learning_gate(_build())


def test_format_contains_absent_status():
    assert "ABSENT" in format_phase_x_learning_gate(_build(rcc_artifact_id=""))


def test_format_contains_limitations():
    assert "dry-lab only" in format_phase_x_learning_gate(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_phase_x_learning_gate(_build())


def test_format_is_string():
    assert isinstance(format_phase_x_learning_gate(_build()), str)

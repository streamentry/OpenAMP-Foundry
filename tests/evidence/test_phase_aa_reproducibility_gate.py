"""Tests for AARG- Phase AA reproducibility gate schema."""

import pytest
from openamp_foundry.evidence.phase_aa_reproducibility_gate import (
    PhaseAaReproducibilityGate,
    AAComponentCheck,
    REQUIRED_AA_COMPONENTS,
    VALID_AARG_VERDICTS,
    build_phase_aa_reproducibility_gate,
    format_phase_aa_reproducibility_gate,
    validate_phase_aa_reproducibility_gate,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        aarg_id="AARG-001",
        pipeline_version="v1.0",
        rmc_id="RMC-001",
        dcr_id="DCR-001",
        cfp_id="CFP-001",
        sbw_id="SBW-001",
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_phase_aa_reproducibility_gate(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_required_aa_components_is_tuple():
    assert isinstance(REQUIRED_AA_COMPONENTS, tuple)


def test_required_aa_components_has_four():
    assert len(REQUIRED_AA_COMPONENTS) == 4


def test_required_aa_components_contains_rmc():
    assert "RMC" in REQUIRED_AA_COMPONENTS


def test_required_aa_components_contains_dcr():
    assert "DCR" in REQUIRED_AA_COMPONENTS


def test_required_aa_components_contains_cfp():
    assert "CFP" in REQUIRED_AA_COMPONENTS


def test_required_aa_components_contains_sbw():
    assert "SBW" in REQUIRED_AA_COMPONENTS


def test_valid_aarg_verdicts_is_frozenset():
    assert isinstance(VALID_AARG_VERDICTS, frozenset)


def test_valid_aarg_verdicts_has_three():
    assert len(VALID_AARG_VERDICTS) == 3


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_phase_aa_reproducibility_gate():
    assert isinstance(_build(), PhaseAaReproducibilityGate)


def test_build_aarg_id_stored():
    assert _build().aarg_id == "AARG-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_all_present_gives_reproducibility_verified():
    assert _build().verdict == "reproducibility_verified"


def test_build_all_present_n_components_4():
    assert _build().n_components_present == 4


def test_build_three_present_gives_reproducibility_partial():
    r = _build(sbw_id="")
    assert r.verdict == "reproducibility_partial"


def test_build_two_present_gives_reproducibility_partial():
    r = _build(cfp_id="", sbw_id="")
    assert r.verdict == "reproducibility_partial"


def test_build_one_present_gives_reproducibility_not_established():
    r = _build(dcr_id="", cfp_id="", sbw_id="")
    assert r.verdict == "reproducibility_not_established"


def test_build_none_present_gives_reproducibility_not_established():
    r = _build(rmc_id="", dcr_id="", cfp_id="", sbw_id="")
    assert r.verdict == "reproducibility_not_established"


def test_build_none_present_n_components_0():
    r = _build(rmc_id="", dcr_id="", cfp_id="", sbw_id="")
    assert r.n_components_present == 0


def test_build_component_checks_are_aa_component_check():
    for c in _build().component_checks:
        assert isinstance(c, AAComponentCheck)


def test_build_component_checks_count():
    assert len(_build().component_checks) == 4


def test_build_rmc_present_true():
    c = next(c for c in _build().component_checks if c.component_type == "RMC")
    assert c.is_present is True


def test_build_rmc_absent_false():
    c = next(
        c
        for c in _build(rmc_id="").component_checks
        if c.component_type == "RMC"
    )
    assert c.is_present is False


def test_build_rmc_artifact_id_stored():
    c = next(c for c in _build().component_checks if c.component_type == "RMC")
    assert c.artifact_id == "RMC-001"


def test_build_dcr_artifact_id_stored():
    c = next(c for c in _build().component_checks if c.component_type == "DCR")
    assert c.artifact_id == "DCR-001"


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_aarg_id_prefix():
    with pytest.raises(ValueError, match="AARG-"):
        _build(aarg_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_wrong_rmc_prefix():
    with pytest.raises(ValueError, match="RMC-"):
        _build(rmc_id="BAD-001")


def test_validate_rejects_wrong_dcr_prefix():
    with pytest.raises(ValueError, match="DCR-"):
        _build(dcr_id="BAD-001")


def test_validate_rejects_wrong_cfp_prefix():
    with pytest.raises(ValueError, match="CFP-"):
        _build(cfp_id="BAD-001")


def test_validate_rejects_wrong_sbw_prefix():
    with pytest.raises(ValueError, match="SBW-"):
        _build(sbw_id="BAD-001")


def test_validate_rejects_n_components_mismatch():
    aarg = _build()
    aarg.n_components_present = 99
    with pytest.raises(ValueError, match="n_components_present"):
        validate_phase_aa_reproducibility_gate(aarg)


def test_validate_rejects_verdict_mismatch_4_present():
    aarg = _build()
    aarg.verdict = "reproducibility_partial"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_aa_reproducibility_gate(aarg)


def test_validate_rejects_verdict_mismatch_3_present():
    aarg = _build(sbw_id="")
    aarg.verdict = "reproducibility_not_established"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_aa_reproducibility_gate(aarg)


def test_validate_rejects_verdict_mismatch_2_present():
    aarg = _build(cfp_id="", sbw_id="")
    aarg.verdict = "reproducibility_not_established"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_aa_reproducibility_gate(aarg)


def test_validate_rejects_verdict_mismatch_1_present():
    aarg = _build(dcr_id="", cfp_id="", sbw_id="")
    aarg.verdict = "reproducibility_verified"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_aa_reproducibility_gate(aarg)


def test_validate_rejects_verdict_mismatch_0_present():
    aarg = _build(rmc_id="", dcr_id="", cfp_id="", sbw_id="")
    aarg.verdict = "reproducibility_verified"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_aa_reproducibility_gate(aarg)


def test_validate_rejects_dry_lab_only_false():
    aarg = _build()
    aarg.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_phase_aa_reproducibility_gate(aarg)


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_invalid_verdict():
    aarg = _build()
    aarg.verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="verdict"):
        validate_phase_aa_reproducibility_gate(aarg)


def test_validate_rejects_wrong_component_count():
    aarg = _build()
    aarg.component_checks = aarg.component_checks[:2]
    with pytest.raises(ValueError, match="component_checks"):
        validate_phase_aa_reproducibility_gate(aarg)


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_aarg_id():
    assert "AARG-001" in format_phase_aa_reproducibility_gate(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_phase_aa_reproducibility_gate(_build())


def test_format_contains_verdict():
    assert "reproducibility_verified" in format_phase_aa_reproducibility_gate(_build())


def test_format_contains_component_name():
    assert "RMC" in format_phase_aa_reproducibility_gate(_build())


def test_format_contains_present_status():
    assert "PRESENT" in format_phase_aa_reproducibility_gate(_build())


def test_format_contains_absent_when_missing():
    assert "ABSENT" in format_phase_aa_reproducibility_gate(_build(sbw_id=""))


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_phase_aa_reproducibility_gate(_build())


def test_format_is_string():
    assert isinstance(format_phase_aa_reproducibility_gate(_build()), str)

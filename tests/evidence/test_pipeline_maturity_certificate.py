"""Tests for PMC- pipeline maturity certificate schema."""

import pytest
from openamp_foundry.evidence.pipeline_maturity_certificate import (
    PipelineMaturityCertificate,
    PMCComponentCheck,
    VALID_PMC_GRADES,
    VALID_PMC_VERDICTS,
    REQUIRED_PMC_COMPONENTS,
    GRADE_A_REQUIRED_SUPERIOR_VERDICTS,
    GRADE_B_REQUIRED_SUPERIOR_VERDICTS,
    GRADE_C_REQUIRED_SUPERIOR_VERDICTS,
    build_pipeline_maturity_certificate,
    format_pipeline_maturity_certificate,
    validate_pipeline_maturity_certificate,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        pmc_id="PMC-001",
        pipeline_version="v1.0",
        cbr_artifact_id="CBR-001",
        cbr_verdict="pipeline_superior",
        fia_artifact_id="FIA-001",
        fia_verdict="multi_feature_signal",
        sda_artifact_id="SDA-001",
        sda_verdict="diverse_panel",
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_pipeline_maturity_certificate(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_pmc_grades_is_frozenset():
    assert isinstance(VALID_PMC_GRADES, frozenset)


def test_valid_pmc_grades_contains_a():
    assert "A" in VALID_PMC_GRADES


def test_valid_pmc_grades_contains_d():
    assert "D" in VALID_PMC_GRADES


def test_valid_pmc_verdicts_is_frozenset():
    assert isinstance(VALID_PMC_VERDICTS, frozenset)


def test_valid_pmc_verdicts_contains_pipeline_validated():
    assert "pipeline_validated" in VALID_PMC_VERDICTS


def test_valid_pmc_verdicts_contains_insufficient_evidence():
    assert "insufficient_evidence" in VALID_PMC_VERDICTS


def test_required_pmc_components_contains_cbr():
    assert "CBR" in REQUIRED_PMC_COMPONENTS


def test_required_pmc_components_contains_fia():
    assert "FIA" in REQUIRED_PMC_COMPONENTS


def test_required_pmc_components_contains_sda():
    assert "SDA" in REQUIRED_PMC_COMPONENTS


def test_grade_a_required_superior_verdicts():
    assert GRADE_A_REQUIRED_SUPERIOR_VERDICTS == 3


def test_grade_b_required_superior_verdicts():
    assert GRADE_B_REQUIRED_SUPERIOR_VERDICTS == 2


def test_grade_c_required_superior_verdicts():
    assert GRADE_C_REQUIRED_SUPERIOR_VERDICTS == 1


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_pipeline_maturity_certificate():
    assert isinstance(_build(), PipelineMaturityCertificate)


def test_build_pmc_id_stored():
    assert _build().pmc_id == "PMC-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_all_superior_gives_grade_a():
    assert _build().pmc_grade == "A"


def test_build_all_superior_gives_pipeline_validated():
    assert _build().pmc_verdict == "pipeline_validated"


def test_build_two_superior_gives_grade_b():
    r = _build(sda_verdict="proximity_driven")
    assert r.pmc_grade == "B"


def test_build_two_superior_gives_pipeline_provisional():
    r = _build(sda_verdict="proximity_driven")
    assert r.pmc_verdict == "pipeline_provisional"


def test_build_one_superior_gives_grade_c():
    r = _build(fia_verdict="charge_dominated", sda_verdict="proximity_driven")
    assert r.pmc_grade == "C"


def test_build_no_superior_gives_grade_d():
    r = _build(
        cbr_verdict="tied",
        fia_verdict="charge_dominated",
        sda_verdict="proximity_driven",
    )
    assert r.pmc_grade == "D"


def test_build_empty_gives_grade_d_insufficient():
    r = _build(
        cbr_artifact_id="",
        cbr_verdict="",
        fia_artifact_id="",
        fia_verdict="",
        sda_artifact_id="",
        sda_verdict="",
    )
    assert r.pmc_grade == "D"
    assert r.pmc_verdict == "insufficient_evidence"


def test_build_n_components_assessed_all():
    assert _build().n_components_assessed == 3


def test_build_n_components_assessed_partial():
    r = _build(sda_artifact_id="", sda_verdict="")
    assert r.n_components_assessed == 2


def test_build_n_superior_verdicts_all():
    assert _build().n_superior_verdicts == 3


def test_build_n_superior_verdicts_none():
    r = _build(
        cbr_verdict="tied",
        fia_verdict="charge_dominated",
        sda_verdict="proximity_driven",
    )
    assert r.n_superior_verdicts == 0


def test_build_component_checks_are_pmc_component_check():
    for c in _build().component_checks:
        assert isinstance(c, PMCComponentCheck)


def test_build_component_checks_count():
    assert len(_build().component_checks) == 3


def test_build_cbr_check_artifact_id_stored():
    r = _build()
    cbr_check = next(c for c in r.component_checks if c.component_type == "CBR")
    assert cbr_check.artifact_id == "CBR-001"


def test_build_contributes_to_grade_true_for_superior():
    r = _build()
    cbr_check = next(c for c in r.component_checks if c.component_type == "CBR")
    assert cbr_check.contributes_to_grade is True


def test_build_contributes_to_grade_false_for_tied():
    r = _build(cbr_verdict="tied")
    cbr_check = next(c for c in r.component_checks if c.component_type == "CBR")
    assert cbr_check.contributes_to_grade is False


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_pmc_id_prefix():
    with pytest.raises(ValueError, match="PMC-"):
        _build(pmc_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_wrong_cbr_artifact_prefix():
    with pytest.raises(ValueError, match="CBR-"):
        _build(cbr_artifact_id="BAD-001")


def test_validate_rejects_wrong_fia_artifact_prefix():
    with pytest.raises(ValueError, match="FIA-"):
        _build(fia_artifact_id="BAD-001")


def test_validate_rejects_wrong_sda_artifact_prefix():
    with pytest.raises(ValueError, match="SDA-"):
        _build(sda_artifact_id="BAD-001")


def test_validate_rejects_n_components_mismatch():
    pmc = _build()
    pmc.n_components_assessed = 99
    with pytest.raises(ValueError, match="n_components_assessed"):
        validate_pipeline_maturity_certificate(pmc)


def test_validate_rejects_n_superior_mismatch():
    pmc = _build()
    pmc.n_superior_verdicts = 99
    with pytest.raises(ValueError, match="n_superior_verdicts"):
        validate_pipeline_maturity_certificate(pmc)


def test_validate_rejects_invalid_pmc_grade():
    pmc = _build()
    pmc.pmc_grade = "X"
    with pytest.raises(ValueError, match="pmc_grade"):
        validate_pipeline_maturity_certificate(pmc)


def test_validate_rejects_invalid_pmc_verdict():
    pmc = _build()
    pmc.pmc_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="pmc_verdict"):
        validate_pipeline_maturity_certificate(pmc)


def test_validate_rejects_dry_lab_only_false():
    pmc = _build()
    pmc.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_pipeline_maturity_certificate(pmc)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_pmc_id():
    assert "PMC-001" in format_pipeline_maturity_certificate(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_pipeline_maturity_certificate(_build())


def test_format_contains_grade():
    assert "A" in format_pipeline_maturity_certificate(_build())


def test_format_contains_verdict():
    assert "pipeline_validated" in format_pipeline_maturity_certificate(_build())


def test_format_contains_cbr():
    assert "CBR" in format_pipeline_maturity_certificate(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_pipeline_maturity_certificate(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_pipeline_maturity_certificate(_build())


def test_format_is_string():
    assert isinstance(format_pipeline_maturity_certificate(_build()), str)

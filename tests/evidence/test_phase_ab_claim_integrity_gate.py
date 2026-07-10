"""Tests for ABAG- Phase AB claim integrity gate schema."""

import pytest
from openamp_foundry.evidence.phase_ab_claim_integrity_gate import (
    PhaseAbClaimIntegrityGate,
    REQUIRED_AB_COMPONENTS,
    VALID_ABAG_VERDICTS,
    build_phase_ab_claim_integrity_gate,
    format_phase_ab_claim_integrity_gate,
    validate_phase_ab_claim_integrity_gate,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        abag_id="ABAG-001",
        pipeline_version="v1.0",
        components_present=["CSD", "RDR", "EGN", "EHP"],
        limitations=["dry-lab only; requires qualified human review"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_phase_ab_claim_integrity_gate(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants — 8 tests
# ---------------------------------------------------------------------------


def test_required_ab_components_is_tuple():
    assert isinstance(REQUIRED_AB_COMPONENTS, tuple)


def test_required_ab_components_has_four():
    assert len(REQUIRED_AB_COMPONENTS) == 4


def test_required_ab_components_contains_csd():
    assert "CSD" in REQUIRED_AB_COMPONENTS


def test_required_ab_components_contains_rdr():
    assert "RDR" in REQUIRED_AB_COMPONENTS


def test_required_ab_components_contains_egn():
    assert "EGN" in REQUIRED_AB_COMPONENTS


def test_required_ab_components_contains_ehp():
    assert "EHP" in REQUIRED_AB_COMPONENTS


def test_valid_abag_verdicts_is_frozenset():
    assert isinstance(VALID_ABAG_VERDICTS, frozenset)


def test_valid_abag_verdicts_has_three():
    assert len(VALID_ABAG_VERDICTS) == 3


# ---------------------------------------------------------------------------
# 2. Build happy paths — 16 tests
# ---------------------------------------------------------------------------


def test_build_returns_phase_ab_claim_integrity_gate():
    assert isinstance(_build(), PhaseAbClaimIntegrityGate)


def test_build_all_four_claim_integrity_verified():
    g = _build()
    assert g.verdict == "claim_integrity_verified"
    assert g.n_components_present == 4


def test_build_three_components_claim_integrity_partial():
    g = _build(components_present=["CSD", "RDR", "EGN"])
    assert g.verdict == "claim_integrity_partial"
    assert g.n_components_present == 3


def test_build_two_components_claim_integrity_partial():
    g = _build(components_present=["CSD", "RDR"])
    assert g.verdict == "claim_integrity_partial"
    assert g.n_components_present == 2


def test_build_one_component_claim_integrity_not_established():
    g = _build(components_present=["CSD"])
    assert g.verdict == "claim_integrity_not_established"
    assert g.n_components_present == 1


def test_build_zero_components_claim_integrity_not_established():
    g = _build(components_present=[])
    assert g.verdict == "claim_integrity_not_established"
    assert g.n_components_present == 0


def test_build_n_components_required_always_four():
    assert _build().n_components_required == 4


def test_build_missing_components_empty_when_all_present():
    assert _build().missing_components == []


def test_build_missing_contains_ehp_when_ehp_absent():
    g = _build(components_present=["CSD", "RDR", "EGN"])
    assert "EHP" in g.missing_components


def test_build_dry_lab_only_always_true():
    assert _build().dry_lab_only is True


def test_build_abag_id_stored():
    assert _build().abag_id == "ABAG-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_limitations_stored():
    g = _build()
    assert g.limitations == ["dry-lab only; requires qualified human review"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_duplicate_components_raises():
    with pytest.raises(ValueError, match="duplicate"):
        _build(components_present=["CSD", "CSD", "RDR", "EGN", "EHP"])


def test_build_unknown_extra_component_raises():
    with pytest.raises(ValueError, match="REQUIRED_AB_COMPONENTS"):
        _build(components_present=["CSD", "RDR", "EGN", "EHP", "UNKNOWN"])


# ---------------------------------------------------------------------------
# 3. Validate rejection — 18 tests
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_abag_id_prefix():
    with pytest.raises(ValueError, match="ABAG-"):
        _build(abag_id="BAD-001")


def test_validate_rejects_empty_abag_id():
    with pytest.raises(ValueError):
        _build(abag_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_component():
    with pytest.raises(ValueError, match="REQUIRED_AB_COMPONENTS"):
        _build(components_present=["CSD", "RDR", "INVALID"])


def test_validate_rejects_duplicate_components():
    with pytest.raises(ValueError, match="duplicate"):
        _build(components_present=["CSD", "CSD", "RDR", "EGN", "EHP"])


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_dry_lab_only_false():
    with pytest.raises(ValueError, match="dry_lab_only"):
        gate = _build()
        gate.dry_lab_only = False
        validate_phase_ab_claim_integrity_gate(gate)


def test_validate_all_four_verdict_verified():
    g = _build()
    assert g.verdict == "claim_integrity_verified"


def test_validate_exactly_three_verdict_partial():
    g = _build(components_present=["CSD", "RDR", "EGN"])
    assert g.verdict == "claim_integrity_partial"


def test_validate_exactly_two_verdict_partial():
    g = _build(components_present=["CSD", "RDR"])
    assert g.verdict == "claim_integrity_partial"


def test_validate_exactly_one_verdict_not_established():
    g = _build(components_present=["CSD"])
    assert g.verdict == "claim_integrity_not_established"


def test_validate_exactly_zero_verdict_not_established():
    g = _build(components_present=[])
    assert g.verdict == "claim_integrity_not_established"


def test_validate_rejects_verdict_mismatch_4_present():
    g = _build()
    g.verdict = "claim_integrity_partial"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_ab_claim_integrity_gate(g)


def test_validate_rejects_verdict_mismatch_3_present():
    g = _build(components_present=["CSD", "RDR", "EGN"])
    g.verdict = "claim_integrity_not_established"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_ab_claim_integrity_gate(g)


def test_validate_rejects_verdict_mismatch_2_present():
    g = _build(components_present=["CSD", "RDR"])
    g.verdict = "claim_integrity_not_established"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_ab_claim_integrity_gate(g)


def test_validate_rejects_verdict_mismatch_1_present():
    g = _build(components_present=["CSD"])
    g.verdict = "claim_integrity_verified"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_ab_claim_integrity_gate(g)


def test_validate_rejects_verdict_mismatch_0_present():
    g = _build(components_present=[])
    g.verdict = "claim_integrity_verified"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_phase_ab_claim_integrity_gate(g)


# ---------------------------------------------------------------------------
# 4. Format — 8 tests
# ---------------------------------------------------------------------------


def test_format_contains_abag_id():
    assert "ABAG-001" in format_phase_ab_claim_integrity_gate(_build())


def test_format_contains_verdict():
    assert "claim_integrity_verified" in format_phase_ab_claim_integrity_gate(_build())


def test_format_contains_n_components_present():
    assert "4/4" in format_phase_ab_claim_integrity_gate(_build())


def test_format_contains_n_components_required():
    assert "4" in format_phase_ab_claim_integrity_gate(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_phase_ab_claim_integrity_gate(_build())


def test_format_contains_limitation_text():
    assert "dry-lab only" in format_phase_ab_claim_integrity_gate(_build())


def test_format_contains_abag_prefix():
    assert "ABAG-" in format_phase_ab_claim_integrity_gate(_build())


def test_format_returns_str():
    assert isinstance(format_phase_ab_claim_integrity_gate(_build()), str)

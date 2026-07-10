"""Tests for DTR- disconfirming test record schema."""

import pytest
from openamp_foundry.evidence.disconfirming_test_record import (
    DisconfirmingTestRecord,
    VALID_DTR_TEST_TYPES,
    VALID_DTR_TEST_OUTCOMES,
    VALID_DTR_REQUIRED_ACTIONS,
    build_disconfirming_test_record,
    format_disconfirming_test_record,
    validate_disconfirming_test_record,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        dtr_id="DTR-001",
        pipeline_version="v1.0",
        claim_tested="The pipeline selects novel candidates beyond charge density.",
        test_type="cheapest_explanation_check",
        test_description="Compared pipeline AUROC against charge-only ranker.",
        test_outcome="not_refuted",
        evidence_summary="Pipeline AUROC 0.72 vs charge-only 0.61; gap 0.11 > 0.05 threshold.",
        limitations=["Only tested on one family."],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_disconfirming_test_record(**defaults)


def _make_dtr(**kwargs):
    defaults = dict(
        dtr_id="DTR-001",
        pipeline_version="v1.0",
        claim_tested="The pipeline selects novel candidates beyond charge density.",
        test_type="cheapest_explanation_check",
        test_description="Compared pipeline AUROC against charge-only ranker.",
        test_outcome="not_refuted",
        evidence_summary="Pipeline AUROC 0.72 vs charge-only 0.61; gap 0.11 > 0.05 threshold.",
        is_claim_affected=False,
        required_action="none",
        dry_lab_only=True,
        limitations=["Only tested on one family."],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return DisconfirmingTestRecord(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants (8 tests)
# ---------------------------------------------------------------------------


def test_valid_dtr_test_types_is_frozenset():
    assert isinstance(VALID_DTR_TEST_TYPES, frozenset)


def test_valid_dtr_test_types_has_seven():
    assert len(VALID_DTR_TEST_TYPES) == 7


def test_valid_dtr_test_types_contains_cheapest_explanation():
    assert "cheapest_explanation_check" in VALID_DTR_TEST_TYPES


def test_valid_dtr_test_types_contains_leakage():
    assert "leakage_check" in VALID_DTR_TEST_TYPES


def test_valid_dtr_test_outcomes_is_frozenset():
    assert isinstance(VALID_DTR_TEST_OUTCOMES, frozenset)


def test_valid_dtr_test_outcomes_has_four():
    assert len(VALID_DTR_TEST_OUTCOMES) == 4


def test_valid_dtr_required_actions_is_frozenset():
    assert isinstance(VALID_DTR_REQUIRED_ACTIONS, frozenset)


def test_valid_dtr_required_actions_has_four():
    assert len(VALID_DTR_REQUIRED_ACTIONS) == 4


# ---------------------------------------------------------------------------
# 2. Build happy paths (16 tests)
# ---------------------------------------------------------------------------


def test_build_returns_disconfirming_test_record():
    assert isinstance(_build(), DisconfirmingTestRecord)


def test_build_dtr_id_stored():
    rec = _build(dtr_id="DTR-099")
    assert rec.dtr_id == "DTR-099"


def test_build_test_type_stored():
    rec = _build(test_type="leakage_check")
    assert rec.test_type == "leakage_check"


def test_build_test_outcome_stored():
    rec = _build(test_outcome="refuted")
    assert rec.test_outcome == "refuted"


def test_build_is_claim_affected_true_for_refuted():
    rec = _build(test_outcome="refuted")
    assert rec.is_claim_affected is True


def test_build_is_claim_affected_false_for_not_refuted():
    rec = _build(test_outcome="not_refuted")
    assert rec.is_claim_affected is False


def test_build_is_claim_affected_false_for_inconclusive():
    rec = _build(test_outcome="inconclusive")
    assert rec.is_claim_affected is False


def test_build_is_claim_affected_false_for_skipped():
    rec = _build(test_outcome="skipped")
    assert rec.is_claim_affected is False


def test_build_required_action_downgrade_claim_for_refuted():
    rec = _build(test_outcome="refuted")
    assert rec.required_action == "downgrade_claim"


def test_build_required_action_investigate_for_inconclusive():
    rec = _build(test_outcome="inconclusive")
    assert rec.required_action == "investigate"


def test_build_required_action_none_for_not_refuted():
    rec = _build(test_outcome="not_refuted")
    assert rec.required_action == "none"


def test_build_required_action_none_for_skipped():
    rec = _build(test_outcome="skipped")
    assert rec.required_action == "none"


def test_build_dry_lab_only_always_true():
    rec = _build()
    assert rec.dry_lab_only is True


def test_build_limitations_stored():
    rec = _build(limitations=["No partner available.", "Expensive assay."])
    assert len(rec.limitations) == 2
    assert "No partner available." in rec.limitations


def test_build_accepts_all_seven_test_types():
    for tt in VALID_DTR_TEST_TYPES:
        rec = _build(test_type=tt)
        assert rec.test_type == tt


def test_build_claim_tested_400_chars():
    text = "x" * 400
    rec = _build(claim_tested=text)
    assert len(rec.claim_tested) == 400


# ---------------------------------------------------------------------------
# 3. Validate rejection (22 tests)
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_dtr_id_prefix():
    with pytest.raises(ValueError, match="DTR-"):
        _build(dtr_id="BAD-001")


def test_validate_rejects_empty_dtr_id():
    with pytest.raises(ValueError, match="DTR-"):
        _build(dtr_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_claim_tested():
    with pytest.raises(ValueError):
        _build(claim_tested="")


def test_validate_rejects_claim_tested_too_long():
    with pytest.raises(ValueError, match="claim_tested"):
        _build(claim_tested="x" * 401)


def test_validate_rejects_invalid_test_type():
    with pytest.raises(ValueError, match="test_type"):
        _build(test_type="not_a_valid_type")


def test_validate_rejects_empty_test_description():
    with pytest.raises(ValueError):
        _build(test_description="")


def test_validate_rejects_invalid_test_outcome():
    with pytest.raises(ValueError, match="test_outcome"):
        _build(test_outcome="not_a_valid_outcome")


def test_validate_rejects_empty_evidence_summary():
    with pytest.raises(ValueError):
        _build(evidence_summary="")


def test_validate_rejects_empty_limitations():
    dtr = _make_dtr()
    dtr.limitations = []
    with pytest.raises(ValueError, match="limitations"):
        validate_disconfirming_test_record(dtr)


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_dry_lab_only_false():
    dtr = _make_dtr()
    dtr.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_disconfirming_test_record(dtr)


def test_outcome_refuted_mapping():
    rec = _build(test_outcome="refuted")
    assert rec.required_action == "downgrade_claim"
    assert rec.is_claim_affected is True


def test_outcome_inconclusive_mapping():
    rec = _build(test_outcome="inconclusive")
    assert rec.required_action == "investigate"
    assert rec.is_claim_affected is False


def test_outcome_not_refuted_mapping():
    rec = _build(test_outcome="not_refuted")
    assert rec.required_action == "none"
    assert rec.is_claim_affected is False


def test_outcome_skipped_mapping():
    rec = _build(test_outcome="skipped")
    assert rec.required_action == "none"
    assert rec.is_claim_affected is False


def test_validate_rejects_dtr_id_lowercase():
    with pytest.raises(ValueError, match="DTR-"):
        _build(dtr_id="dtr-001")


def test_validate_rejects_dtr_id_no_dash():
    with pytest.raises(ValueError, match="DTR-"):
        _build(dtr_id="DTR001")


def test_validate_rejects_dtr_id_tricky_prefix():
    with pytest.raises(ValueError, match="DTR-"):
        _build(dtr_id="DTr-001")


def test_validate_rejects_limitations_with_none():
    dtr = _make_dtr()
    dtr.limitations = None
    with pytest.raises(ValueError, match="limitations"):
        validate_disconfirming_test_record(dtr)


def test_validate_rejects_test_type_empty():
    with pytest.raises(ValueError, match="test_type"):
        _build(test_type="")


def test_validate_rejects_test_outcome_empty():
    with pytest.raises(ValueError, match="test_outcome"):
        _build(test_outcome="")


# ---------------------------------------------------------------------------
# 4. Format (8 tests)
# ---------------------------------------------------------------------------


def test_format_contains_dtr_id():
    assert "DTR-001" in format_disconfirming_test_record(_build())


def test_format_contains_test_type():
    assert "cheapest_explanation_check" in format_disconfirming_test_record(_build())


def test_format_contains_test_outcome():
    assert "not_refuted" in format_disconfirming_test_record(_build())


def test_format_contains_required_action():
    assert "none" in format_disconfirming_test_record(_build())


def test_format_contains_is_claim_affected():
    assert "False" in format_disconfirming_test_record(_build())


def test_format_contains_limitation_text():
    text = format_disconfirming_test_record(_build())
    assert "Only tested on one family." in text


def test_format_contains_dtr_prefix():
    assert "DTR-" in format_disconfirming_test_record(_build())


def test_format_returns_string():
    assert isinstance(format_disconfirming_test_record(_build()), str)

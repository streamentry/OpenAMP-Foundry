"""Tests for ACDG- Phase AC disconfirming-evidence gate."""

import pytest

from openamp_foundry.evidence.disconfirming_test_record import (
    build_disconfirming_test_record,
)
from openamp_foundry.evidence.phase_ac_disconfirming_gate import (
    PhaseAcDisconfirmingGate,
    VALID_ACDG_VERDICTS,
    build_phase_ac_disconfirming_gate,
    format_phase_ac_disconfirming_gate,
    validate_phase_ac_disconfirming_gate,
)


def _record(*, dtr_id="DTR-001", outcome="not_refuted"):
    return build_disconfirming_test_record(
        dtr_id=dtr_id,
        pipeline_version="v1.0",
        claim_tested="The pipeline adds signal beyond a cheap enemy.",
        test_type="cheapest_explanation_check",
        test_description="Compared the pipeline against a charge-only baseline.",
        test_outcome=outcome,
        evidence_summary="The comparison was run on the frozen toy benchmark.",
        limitations=["Toy benchmark only."],
        created_at="2026-07-14",
    )


def _build(**kwargs):
    defaults = dict(
        acdg_id="ACDG-001",
        pipeline_version="v1.0",
        records=[_record()],
        resolved_dtr_ids=[],
        limitations=["A passing gate is not biological validation."],
        created_at="2026-07-14",
    )
    defaults.update(kwargs)
    return build_phase_ac_disconfirming_gate(**defaults)


def test_build_returns_gate_and_verifies_no_action_needed():
    gate = _build()
    assert isinstance(gate, PhaseAcDisconfirmingGate)
    assert gate.verdict == "disconfirming_evidence_verified"
    assert gate.n_records_present == 1
    assert gate.n_actions_required == 0


def test_refuted_record_remains_partial_until_resolved():
    gate = _build(records=[_record(outcome="refuted")])
    assert gate.verdict == "disconfirming_evidence_partial"
    assert gate.n_claims_affected == 1
    assert gate.unresolved_dtr_ids == ["DTR-001"]


def test_resolved_refuted_record_verifies():
    gate = _build(
        records=[_record(outcome="refuted")],
        resolved_dtr_ids=["DTR-001"],
    )
    assert gate.verdict == "disconfirming_evidence_verified"
    assert gate.n_actions_resolved == 1


def test_inconclusive_record_requires_investigation():
    gate = _build(records=[_record(outcome="inconclusive")])
    assert gate.verdict == "disconfirming_evidence_partial"
    assert gate.n_actions_required == 1


def test_empty_records_are_not_established():
    gate = _build(records=[])
    assert gate.verdict == "disconfirming_evidence_not_established"
    assert gate.n_records_present == 0


def test_valid_verdicts_has_three_members():
    assert len(VALID_ACDG_VERDICTS) == 3


def test_duplicate_records_are_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        _build(records=[_record(), _record()])


def test_duplicate_resolutions_are_rejected():
    with pytest.raises(ValueError, match="duplicates"):
        _build(
            records=[_record(outcome="refuted")],
            resolved_dtr_ids=["DTR-001", "DTR-001"],
        )


def test_unknown_resolution_is_rejected():
    with pytest.raises(ValueError, match="unknown"):
        _build(resolved_dtr_ids=["DTR-404"])


def test_resolution_of_no_action_record_is_rejected():
    with pytest.raises(ValueError, match="requiring action"):
        _build(resolved_dtr_ids=["DTR-001"])


def test_mismatched_pipeline_version_is_rejected():
    record = _record()
    record.pipeline_version = "v0.9"
    with pytest.raises(ValueError, match="pipeline_version"):
        _build(records=[record])


def test_inconsistent_dtr_action_is_rejected():
    record = _record(outcome="refuted")
    record.required_action = "none"
    with pytest.raises(ValueError, match="required_action"):
        _build(records=[record])


def test_inconsistent_dtr_claim_affected_is_rejected():
    record = _record(outcome="refuted")
    record.is_claim_affected = False
    with pytest.raises(ValueError, match="is_claim_affected"):
        _build(records=[record])


def test_bad_gate_id_is_rejected():
    with pytest.raises(ValueError, match="ACDG-"):
        _build(acdg_id="BAD-001")


def test_validate_rejects_non_dtr_id():
    gate = _build()
    gate.dtr_ids = ["BAD-001"]
    with pytest.raises(ValueError, match="DTR-"):
        validate_phase_ac_disconfirming_gate(gate)


def test_validate_rejects_count_mismatch():
    gate = _build()
    gate.n_records_present = 2
    with pytest.raises(ValueError, match="n_records_present"):
        validate_phase_ac_disconfirming_gate(gate)


def test_validate_rejects_missing_limitations():
    gate = _build()
    gate.limitations = []
    with pytest.raises(ValueError, match="limitations"):
        validate_phase_ac_disconfirming_gate(gate)


def test_validate_rejects_non_dry_lab_gate():
    gate = _build()
    gate.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_phase_ac_disconfirming_gate(gate)


def test_format_contains_verdict_and_unresolved_ids():
    text = format_phase_ac_disconfirming_gate(
        _build(records=[_record(outcome="refuted")])
    )
    assert "Phase AC Disconfirming Evidence Gate" in text
    assert "disconfirming_evidence_partial" in text
    assert "DTR-001" in text

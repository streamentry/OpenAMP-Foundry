"""Tests for ESC- external-simulator review checklist schema."""

import pytest
from openamp_foundry.simulation.external_simulator_checklist import (
    ExternalSimulatorChecklist,
    CHECKLIST_ITEMS,
    REQUIRED_ITEMS,
    VALID_ESC_VERDICTS,
    build_external_simulator_checklist,
    format_external_simulator_checklist,
    validate_external_simulator_checklist,
)

_ALL_ITEMS = list(CHECKLIST_ITEMS)
_REQUIRED = list(REQUIRED_ITEMS)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        esc_id="ESC-001",
        simulator_name="membrane-sim-v2",
        pipeline_version="v1.0",
        items_checked=_ALL_ITEMS,
        reviewer_notes="",
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_external_simulator_checklist(**defaults)


def _build_required_only(**kwargs):
    defaults = dict(
        esc_id="ESC-001",
        simulator_name="membrane-sim-v2",
        pipeline_version="v1.0",
        items_checked=_REQUIRED,
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_external_simulator_checklist(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_checklist_items_is_tuple():
    assert isinstance(CHECKLIST_ITEMS, tuple)


def test_checklist_items_contains_data_sent():
    assert "data_sent_to_service_documented" in CHECKLIST_ITEMS


def test_checklist_items_contains_sequence_not_transmitted():
    assert "sequence_data_not_transmitted" in CHECKLIST_ITEMS


def test_checklist_items_contains_tls_enforced():
    assert "tls_enforced" in CHECKLIST_ITEMS


def test_checklist_items_contains_license():
    assert "license_permits_research_use" in CHECKLIST_ITEMS


def test_checklist_items_contains_failure_mode():
    assert "failure_mode_documented" in CHECKLIST_ITEMS


def test_checklist_items_contains_nsn_policy():
    assert "network_call_declared_in_nsn_policy" in CHECKLIST_ITEMS


def test_checklist_items_has_twelve_items():
    assert len(CHECKLIST_ITEMS) == 12


def test_required_items_is_tuple():
    assert isinstance(REQUIRED_ITEMS, tuple)


def test_required_items_contains_sequence_not_transmitted():
    assert "sequence_data_not_transmitted" in REQUIRED_ITEMS


def test_required_items_contains_tls_enforced():
    assert "tls_enforced" in REQUIRED_ITEMS


def test_required_items_subset_of_checklist():
    assert set(REQUIRED_ITEMS) <= set(CHECKLIST_ITEMS)


def test_valid_esc_verdicts_is_frozenset():
    assert isinstance(VALID_ESC_VERDICTS, frozenset)


def test_valid_esc_verdicts_contains_approved():
    assert "approved" in VALID_ESC_VERDICTS


def test_valid_esc_verdicts_contains_conditional_approval():
    assert "conditional_approval" in VALID_ESC_VERDICTS


def test_valid_esc_verdicts_contains_not_approved():
    assert "not_approved" in VALID_ESC_VERDICTS


# ---------------------------------------------------------------------------
# 2. build happy paths
# ---------------------------------------------------------------------------


def test_build_returns_external_simulator_checklist():
    assert isinstance(_build(), ExternalSimulatorChecklist)


def test_build_esc_id_stored():
    assert _build().esc_id == "ESC-001"


def test_build_simulator_name_stored():
    assert _build().simulator_name == "membrane-sim-v2"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_all_items_gives_approved():
    assert _build().esc_verdict == "approved"


def test_build_required_only_gives_conditional_approval():
    r = _build_required_only()
    assert r.esc_verdict == "conditional_approval"


def test_build_no_items_gives_not_approved():
    r = _build(items_checked=[])
    assert r.esc_verdict == "not_approved"


def test_build_required_items_complete_true_when_all():
    assert _build().required_items_complete is True


def test_build_required_items_complete_true_when_required_only():
    assert _build_required_only().required_items_complete is True


def test_build_required_items_complete_false_when_none():
    r = _build(items_checked=[])
    assert r.required_items_complete is False


def test_build_n_items_checked_all():
    assert _build().n_items_checked == 12


def test_build_n_items_checked_required_only():
    assert _build_required_only().n_items_checked == 7


def test_build_n_items_checked_none():
    r = _build(items_checked=[])
    assert r.n_items_checked == 0


def test_build_items_unchecked_empty_when_all():
    assert _build().items_unchecked == []


def test_build_items_unchecked_populated_when_partial():
    r = _build_required_only()
    assert len(r.items_unchecked) == len(CHECKLIST_ITEMS) - len(REQUIRED_ITEMS)


def test_build_reviewer_notes_stored():
    r = _build(reviewer_notes="reviewed by safety team")
    assert r.reviewer_notes == "reviewed by safety team"


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_esc_id_prefix():
    with pytest.raises(ValueError, match="ESC-"):
        _build(esc_id="BAD-001")


def test_validate_rejects_empty_simulator_name():
    with pytest.raises(ValueError, match="simulator_name"):
        _build(simulator_name="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_checked_item():
    with pytest.raises(ValueError, match="checked item"):
        _build(items_checked=_ALL_ITEMS + ["UNKNOWN_ITEM"])


def test_validate_rejects_n_items_checked_mismatch():
    esc = _build()
    esc.n_items_checked = 99
    with pytest.raises(ValueError, match="n_items_checked"):
        validate_external_simulator_checklist(esc)


def test_validate_rejects_required_items_complete_mismatch():
    esc = _build()
    esc.required_items_complete = False
    with pytest.raises(ValueError, match="required_items_complete"):
        validate_external_simulator_checklist(esc)


def test_validate_rejects_invalid_esc_verdict():
    esc = _build()
    esc.esc_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="esc_verdict"):
        validate_external_simulator_checklist(esc)


def test_validate_rejects_approved_without_required_complete():
    esc = _build(items_checked=[])
    esc.esc_verdict = "approved"
    esc.required_items_complete = True
    with pytest.raises(ValueError):
        validate_external_simulator_checklist(esc)


def test_validate_rejects_dry_lab_only_false():
    esc = _build()
    esc.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_external_simulator_checklist(esc)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_esc_id():
    assert "ESC-001" in format_external_simulator_checklist(_build())


def test_format_contains_simulator_name():
    assert "membrane-sim-v2" in format_external_simulator_checklist(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_external_simulator_checklist(_build())


def test_format_contains_verdict():
    assert "approved" in format_external_simulator_checklist(_build())


def test_format_contains_items_checked_count():
    assert "12" in format_external_simulator_checklist(_build())


def test_format_contains_unchecked_item_when_partial():
    r = _build_required_only()
    output = format_external_simulator_checklist(r)
    assert any(item in output for item in r.items_unchecked)


def test_format_contains_limitations():
    assert "dry-lab only" in format_external_simulator_checklist(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_external_simulator_checklist(_build())


def test_format_is_string():
    assert isinstance(format_external_simulator_checklist(_build()), str)

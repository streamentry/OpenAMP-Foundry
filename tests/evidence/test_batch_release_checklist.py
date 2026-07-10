"""Tests for BRC- batch release checklist schema."""

import pytest
from openamp_foundry.evidence.batch_release_checklist import (
    BatchReleaseChecklist,
    ChecklistItem,
    VALID_PCC_GRADES,
    VALID_BEG_VERDICTS,
    VALID_RELEASE_VERDICTS,
    PASSING_PCC_GRADES,
    BLOCKING_BEG_VERDICTS,
    build_batch_release_checklist,
    format_batch_release_checklist,
    validate_batch_release_checklist,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        brc_id="BRC-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        pcc_id="PCC-001",
        pcc_grade="A",
        beg_id="BEG-001",
        beg_verdict="no_gaps",
        sat_id="SAT-001",
        n_sat_entries=3,
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_batch_release_checklist(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_pcc_grades_is_frozenset():
    assert isinstance(VALID_PCC_GRADES, frozenset)


def test_valid_pcc_grades_contains_a():
    assert "A" in VALID_PCC_GRADES


def test_valid_pcc_grades_contains_b():
    assert "B" in VALID_PCC_GRADES


def test_valid_pcc_grades_contains_c():
    assert "C" in VALID_PCC_GRADES


def test_valid_pcc_grades_contains_d():
    assert "D" in VALID_PCC_GRADES


def test_passing_pcc_grades_is_frozenset():
    assert isinstance(PASSING_PCC_GRADES, frozenset)


def test_passing_pcc_grades_contains_a_and_b():
    assert PASSING_PCC_GRADES == frozenset({"A", "B"})


def test_valid_beg_verdicts_is_frozenset():
    assert isinstance(VALID_BEG_VERDICTS, frozenset)


def test_blocking_beg_verdicts_includes_critical_gaps():
    assert "critical_gaps" in BLOCKING_BEG_VERDICTS


def test_blocking_beg_verdicts_includes_no_families():
    assert "no_families" in BLOCKING_BEG_VERDICTS


def test_valid_release_verdicts_is_frozenset():
    assert isinstance(VALID_RELEASE_VERDICTS, frozenset)


def test_valid_release_verdicts_contains_approved():
    assert "approved" in VALID_RELEASE_VERDICTS


def test_valid_release_verdicts_contains_blocked():
    assert "blocked" in VALID_RELEASE_VERDICTS


def test_valid_release_verdicts_contains_conditional():
    assert "conditional" in VALID_RELEASE_VERDICTS


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_batch_release_checklist():
    assert isinstance(_build(), BatchReleaseChecklist)


def test_build_brc_id_stored():
    assert _build().brc_id == "BRC-001"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_approved_when_all_pass():
    r = _build()
    assert r.release_verdict == "approved"


def test_build_blocked_when_pcc_grade_c():
    r = _build(pcc_grade="C")
    assert r.release_verdict == "blocked"


def test_build_blocked_when_pcc_grade_d():
    r = _build(pcc_grade="D")
    assert r.release_verdict == "blocked"


def test_build_blocked_when_critical_gaps():
    r = _build(beg_verdict="critical_gaps")
    assert r.release_verdict == "blocked"


def test_build_blocked_when_no_families():
    r = _build(beg_verdict="no_families")
    assert r.release_verdict == "blocked"


def test_build_blocked_when_no_sat_entries():
    r = _build(n_sat_entries=0)
    assert r.release_verdict == "blocked"


def test_build_n_items_total_is_3():
    assert _build().n_items_total == 3


def test_build_n_items_passed_3_when_all_pass():
    r = _build()
    assert r.n_items_passed == 3


def test_build_n_items_failed_0_when_all_pass():
    r = _build()
    assert r.n_items_failed == 0


def test_build_n_items_failed_1_on_bad_pcc():
    r = _build(pcc_grade="C")
    assert r.n_items_failed == 1


def test_build_checklist_items_are_checklist_item():
    for item in _build().checklist_items:
        assert isinstance(item, ChecklistItem)


def test_build_pcc_grade_item_passes_for_a():
    r = _build(pcc_grade="A")
    pcc_item = next(it for it in r.checklist_items if it.item_id == "PCC-GRADE")
    assert pcc_item.passed is True


def test_build_pcc_grade_item_passes_for_b():
    r = _build(pcc_grade="B")
    pcc_item = next(it for it in r.checklist_items if it.item_id == "PCC-GRADE")
    assert pcc_item.passed is True


def test_build_pcc_grade_item_fails_for_c():
    r = _build(pcc_grade="C")
    pcc_item = next(it for it in r.checklist_items if it.item_id == "PCC-GRADE")
    assert pcc_item.passed is False


def test_build_beg_verdict_item_passes_for_no_gaps():
    r = _build(beg_verdict="no_gaps")
    beg_item = next(it for it in r.checklist_items if it.item_id == "BEG-VERDICT")
    assert beg_item.passed is True


def test_build_beg_verdict_item_passes_for_partial_gaps():
    r = _build(beg_verdict="partial_gaps")
    beg_item = next(it for it in r.checklist_items if it.item_id == "BEG-VERDICT")
    assert beg_item.passed is True


def test_build_sat_entries_item_passes_when_positive():
    r = _build(n_sat_entries=1)
    sat_item = next(it for it in r.checklist_items if it.item_id == "SAT-ENTRIES")
    assert sat_item.passed is True


def test_build_sat_entries_item_fails_when_zero():
    r = _build(n_sat_entries=0)
    sat_item = next(it for it in r.checklist_items if it.item_id == "SAT-ENTRIES")
    assert sat_item.passed is False


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_brc_id_prefix():
    with pytest.raises(ValueError, match="BRC-"):
        _build(brc_id="BAD-001")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_bad_pcc_id_prefix():
    with pytest.raises(ValueError, match="PCC-"):
        _build(pcc_id="BAD-001")


def test_validate_rejects_invalid_pcc_grade():
    with pytest.raises(ValueError, match="pcc_grade"):
        _build(pcc_grade="Z")


def test_validate_rejects_bad_beg_id_prefix():
    with pytest.raises(ValueError, match="BEG-"):
        _build(beg_id="BAD-001")


def test_validate_rejects_invalid_beg_verdict():
    with pytest.raises(ValueError, match="beg_verdict"):
        _build(beg_verdict="UNKNOWN")


def test_validate_rejects_bad_sat_id_prefix():
    with pytest.raises(ValueError, match="SAT-"):
        _build(sat_id="BAD-001")


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_brc_id():
    assert "BRC-001" in format_batch_release_checklist(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_batch_release_checklist(_build())


def test_format_contains_verdict():
    assert "approved" in format_batch_release_checklist(_build())


def test_format_contains_pcc_grade():
    assert "grade=A" in format_batch_release_checklist(_build())


def test_format_contains_beg_verdict():
    assert "no_gaps" in format_batch_release_checklist(_build())


def test_format_contains_sat_entries():
    assert "entries=3" in format_batch_release_checklist(_build())


def test_format_contains_pass_markers():
    assert "[PASS]" in format_batch_release_checklist(_build())


def test_format_contains_fail_marker_on_blocked():
    r = _build(pcc_grade="D")
    assert "[FAIL]" in format_batch_release_checklist(r)


def test_format_contains_limitations():
    assert "dry-lab only" in format_batch_release_checklist(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_batch_release_checklist(_build())


def test_format_is_string():
    assert isinstance(format_batch_release_checklist(_build()), str)

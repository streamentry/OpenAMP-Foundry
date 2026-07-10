"""Tests for ECI- evidence completeness index schema."""

import pytest
from openamp_foundry.evidence.evidence_completeness_index import (
    EvidenceCompletenessIndex,
    BatchSchemaPresence,
    AGGREGATED_SCHEMA_TYPES,
    VALID_ECI_GRADES,
    build_evidence_completeness_index,
    format_evidence_completeness_index,
    validate_evidence_completeness_index,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BATCH_ALL_PRESENT = {
    "batch_id": "B1",
    "pcc_id": "P1",
    "cba2_id": "C1",
    "beg_id": "G1",
    "sat_id": "S1",
}
_BATCH_PARTIAL = {
    "batch_id": "B2",
    "pcc_id": "P2",
    "cba2_id": "",
    "beg_id": "G2",
    "sat_id": "",
}
_BATCH_EMPTY = {
    "batch_id": "B3",
    "pcc_id": "",
    "cba2_id": "",
    "beg_id": "",
    "sat_id": "",
}


def _build(**kwargs):
    defaults = dict(
        eci_id="ECI-001",
        pipeline_version="v1.0",
        batch_dicts=[_BATCH_ALL_PRESENT, _BATCH_PARTIAL],
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_evidence_completeness_index(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_aggregated_schema_types_is_frozenset():
    assert isinstance(AGGREGATED_SCHEMA_TYPES, frozenset)


def test_aggregated_schema_types_contains_pcc():
    assert "PCC" in AGGREGATED_SCHEMA_TYPES


def test_aggregated_schema_types_contains_cba2():
    assert "CBA2" in AGGREGATED_SCHEMA_TYPES


def test_aggregated_schema_types_contains_beg():
    assert "BEG" in AGGREGATED_SCHEMA_TYPES


def test_aggregated_schema_types_contains_sat():
    assert "SAT" in AGGREGATED_SCHEMA_TYPES


def test_aggregated_schema_types_count():
    assert len(AGGREGATED_SCHEMA_TYPES) == 4


def test_valid_eci_grades_is_frozenset():
    assert isinstance(VALID_ECI_GRADES, frozenset)


def test_valid_eci_grades_contains_a():
    assert "A" in VALID_ECI_GRADES


def test_valid_eci_grades_contains_b():
    assert "B" in VALID_ECI_GRADES


def test_valid_eci_grades_contains_c():
    assert "C" in VALID_ECI_GRADES


def test_valid_eci_grades_contains_d():
    assert "D" in VALID_ECI_GRADES


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_evidence_completeness_index():
    assert isinstance(_build(), EvidenceCompletenessIndex)


def test_build_eci_id_stored():
    assert _build().eci_id == "ECI-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_n_batches_matches_input():
    r = _build()
    assert r.n_batches == 2


def test_build_n_schemas_required_per_batch_is_4():
    assert _build().n_schemas_required_per_batch == 4


def test_build_total_schema_slots():
    r = _build()
    assert r.total_schema_slots == r.n_batches * 4


def test_build_total_schemas_present():
    r = _build()
    assert r.total_schemas_present == 4 + 2  # B1=4, B2=2


def test_build_grade_a_when_all_present():
    r = _build(batch_dicts=[_BATCH_ALL_PRESENT])
    assert r.completeness_grade == "A"


def test_build_grade_d_when_all_empty():
    r = _build(batch_dicts=[_BATCH_EMPTY])
    assert r.completeness_grade == "D"


def test_build_grade_c_when_half_present():
    r = _build(batch_dicts=[_BATCH_ALL_PRESENT, _BATCH_EMPTY])
    assert r.completeness_grade == "C"


def test_build_overall_fraction_1_when_all():
    r = _build(batch_dicts=[_BATCH_ALL_PRESENT])
    assert r.overall_completeness_fraction == 1.0


def test_build_overall_fraction_0_when_empty():
    r = _build(batch_dicts=[_BATCH_EMPTY])
    assert r.overall_completeness_fraction == 0.0


def test_build_empty_batch_list_fraction_zero():
    r = _build(batch_dicts=[])
    assert r.overall_completeness_fraction == 0.0


def test_build_empty_batch_list_grade_d():
    r = _build(batch_dicts=[])
    assert r.completeness_grade == "D"


def test_build_batch_entries_are_batch_schema_presence():
    r = _build()
    for entry in r.batch_entries:
        assert isinstance(entry, BatchSchemaPresence)


def test_build_batch_pcc_present_when_id_given():
    r = _build(batch_dicts=[_BATCH_ALL_PRESENT])
    assert r.batch_entries[0].pcc_present is True


def test_build_batch_cba2_absent_when_empty_id():
    r = _build(batch_dicts=[_BATCH_PARTIAL])
    assert r.batch_entries[0].cba2_present is False


def test_build_batch_sat_absent_when_empty_id():
    r = _build(batch_dicts=[_BATCH_PARTIAL])
    assert r.batch_entries[0].sat_present is False


def test_build_batch_grade_a_for_full_batch():
    r = _build(batch_dicts=[_BATCH_ALL_PRESENT])
    assert r.batch_entries[0].batch_grade == "A"


def test_build_batch_grade_d_for_empty_batch():
    r = _build(batch_dicts=[_BATCH_EMPTY])
    assert r.batch_entries[0].batch_grade == "D"


def test_build_batch_n_schemas_present():
    r = _build(batch_dicts=[_BATCH_ALL_PRESENT])
    assert r.batch_entries[0].n_schemas_present == 4


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_eci_id_prefix():
    with pytest.raises(ValueError, match="ECI-"):
        _build(eci_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_eci_id():
    assert "ECI-001" in format_evidence_completeness_index(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_evidence_completeness_index(_build())


def test_format_contains_grade():
    r = _build(batch_dicts=[_BATCH_ALL_PRESENT])
    assert "Grade: A" in format_evidence_completeness_index(r)


def test_format_contains_batch_id():
    assert "B1" in format_evidence_completeness_index(_build())


def test_format_contains_fraction():
    r = _build(batch_dicts=[_BATCH_ALL_PRESENT])
    assert "100.00%" in format_evidence_completeness_index(r)


def test_format_contains_limitations():
    assert "dry-lab only" in format_evidence_completeness_index(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_evidence_completeness_index(_build())


def test_format_is_string():
    assert isinstance(format_evidence_completeness_index(_build()), str)

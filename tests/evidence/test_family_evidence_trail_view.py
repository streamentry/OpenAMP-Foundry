"""Tests for FET- family evidence trail view schema."""

import pytest
from openamp_foundry.evidence.family_evidence_trail_view import (
    FamilyEvidenceTrailView,
    FamilySchemaEvent,
    REQUIRED_TRAIL_SCHEMA_TYPES,
    VALID_TRAIL_COMPLETENESS_GRADES,
    build_family_evidence_trail_view,
    format_family_evidence_trail_view,
    validate_family_evidence_trail_view,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALL_EVENTS = [
    {"schema_type": t, "artifact_id": f"ART-{t}", "created_at": "2026-07-10"}
    for t in sorted(REQUIRED_TRAIL_SCHEMA_TYPES)
]

_SOME_EVENTS = [
    {"schema_type": "BSP", "artifact_id": "ART-BSP", "created_at": "2026-07-01"},
    {"schema_type": "SEG", "artifact_id": "ART-SEG", "created_at": "2026-07-02"},
    {"schema_type": "BTI", "artifact_id": "ART-BTI", "created_at": "2026-07-03"},
]


def _build(**kwargs):
    defaults = dict(
        fet_id="FET-001",
        candidate_family_id="FAM-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        schema_event_dicts=_SOME_EVENTS,
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_family_evidence_trail_view(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_required_trail_schema_types_is_frozenset():
    assert isinstance(REQUIRED_TRAIL_SCHEMA_TYPES, frozenset)


def test_required_trail_schema_types_count():
    assert len(REQUIRED_TRAIL_SCHEMA_TYPES) == 9


def test_required_trail_schema_types_contains_bti():
    assert "BTI" in REQUIRED_TRAIL_SCHEMA_TYPES


def test_required_trail_schema_types_contains_beg():
    assert "BEG" in REQUIRED_TRAIL_SCHEMA_TYPES


def test_required_trail_schema_types_contains_sat():
    assert "SAT" in REQUIRED_TRAIL_SCHEMA_TYPES


def test_required_trail_schema_types_contains_pcc():
    assert "PCC" in REQUIRED_TRAIL_SCHEMA_TYPES


def test_required_trail_schema_types_contains_bsp():
    assert "BSP" in REQUIRED_TRAIL_SCHEMA_TYPES


def test_required_trail_schema_types_contains_seg():
    assert "SEG" in REQUIRED_TRAIL_SCHEMA_TYPES


def test_required_trail_schema_types_contains_ecc():
    assert "ECC" in REQUIRED_TRAIL_SCHEMA_TYPES


def test_required_trail_schema_types_contains_rsr():
    assert "RSR" in REQUIRED_TRAIL_SCHEMA_TYPES


def test_required_trail_schema_types_contains_pqt():
    assert "PQT" in REQUIRED_TRAIL_SCHEMA_TYPES


def test_valid_grades_is_frozenset():
    assert isinstance(VALID_TRAIL_COMPLETENESS_GRADES, frozenset)


def test_valid_grades_contains_complete():
    assert "complete" in VALID_TRAIL_COMPLETENESS_GRADES


def test_valid_grades_contains_partial():
    assert "partial" in VALID_TRAIL_COMPLETENESS_GRADES


def test_valid_grades_contains_empty():
    assert "empty" in VALID_TRAIL_COMPLETENESS_GRADES


def test_valid_grades_count():
    assert len(VALID_TRAIL_COMPLETENESS_GRADES) == 3


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_family_evidence_trail_view():
    assert isinstance(_build(), FamilyEvidenceTrailView)


def test_build_fet_id_stored():
    assert _build().fet_id == "FET-001"


def test_build_candidate_family_id_stored():
    assert _build().candidate_family_id == "FAM-001"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_n_schemas_required_is_9():
    assert _build().n_schemas_required == 9


def test_build_partial_grade_when_some_present():
    r = _build()
    assert r.trail_completeness_grade == "partial"


def test_build_complete_grade_when_all_present():
    r = _build(schema_event_dicts=_ALL_EVENTS)
    assert r.trail_completeness_grade == "complete"


def test_build_empty_grade_when_no_events():
    r = _build(schema_event_dicts=[])
    assert r.trail_completeness_grade == "empty"


def test_build_present_schema_types_sorted():
    r = _build()
    assert r.present_schema_types == sorted(r.present_schema_types)


def test_build_missing_schema_types_sorted():
    r = _build()
    assert r.missing_schema_types == sorted(r.missing_schema_types)


def test_build_present_plus_missing_equals_required():
    r = _build()
    assert set(r.present_schema_types) | set(r.missing_schema_types) == REQUIRED_TRAIL_SCHEMA_TYPES


def test_build_n_schemas_present_matches_present_list():
    r = _build()
    assert r.n_schemas_present == len(r.present_schema_types)


def test_build_schema_events_are_family_schema_event():
    r = _build()
    for e in r.schema_events:
        assert isinstance(e, FamilySchemaEvent)


def test_build_events_count_matches_input():
    r = _build()
    assert len(r.schema_events) == len(_SOME_EVENTS)


def test_build_limitations_stored():
    r = _build()
    assert r.limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_all_present_no_missing():
    r = _build(schema_event_dicts=_ALL_EVENTS)
    assert r.missing_schema_types == []


def test_build_all_present_n_present_is_9():
    r = _build(schema_event_dicts=_ALL_EVENTS)
    assert r.n_schemas_present == 9


def test_build_empty_events_all_missing():
    r = _build(schema_event_dicts=[])
    assert len(r.missing_schema_types) == 9


def test_build_deduplicates_duplicate_event_types():
    events = [
        {"schema_type": "BSP", "artifact_id": "A1", "created_at": "2026-07-01"},
        {"schema_type": "BSP", "artifact_id": "A2", "created_at": "2026-07-02"},
    ]
    r = _build(schema_event_dicts=events)
    assert r.present_schema_types == ["BSP"]
    assert len(r.schema_events) == 2


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_fet_id_prefix():
    with pytest.raises(ValueError, match="FET-"):
        _build(fet_id="BAD-001")


def test_validate_rejects_toy_family_id():
    with pytest.raises(ValueError, match="TOY-"):
        _build(candidate_family_id="TOY-001")


def test_validate_rejects_empty_family_id():
    with pytest.raises(ValueError):
        _build(candidate_family_id="")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_unknown_schema_type_in_event():
    with pytest.raises(ValueError, match="REQUIRED_TRAIL_SCHEMA_TYPES"):
        _build(schema_event_dicts=[{"schema_type": "UNKNOWN", "artifact_id": "x", "created_at": "2026-07-01"}])


def test_validate_rejects_empty_artifact_id_in_event():
    with pytest.raises(ValueError, match="artifact_id"):
        _build(schema_event_dicts=[{"schema_type": "BSP", "artifact_id": "", "created_at": "2026-07-01"}])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_fet_id():
    assert "FET-001" in format_family_evidence_trail_view(_build())


def test_format_contains_family_id():
    assert "FAM-001" in format_family_evidence_trail_view(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_family_evidence_trail_view(_build())


def test_format_contains_grade():
    assert "partial" in format_family_evidence_trail_view(_build())


def test_format_contains_present_count():
    r = _build()
    assert f"{r.n_schemas_present}/{r.n_schemas_required}" in format_family_evidence_trail_view(r)


def test_format_contains_limitations():
    assert "dry-lab only" in format_family_evidence_trail_view(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_family_evidence_trail_view(_build())


def test_format_contains_created_at():
    assert "2026-07-10" in format_family_evidence_trail_view(_build())


def test_format_complete_no_missing_line():
    r = _build(schema_event_dicts=_ALL_EVENTS)
    formatted = format_family_evidence_trail_view(r)
    assert "Missing:" not in formatted


def test_format_is_string():
    assert isinstance(format_family_evidence_trail_view(_build()), str)

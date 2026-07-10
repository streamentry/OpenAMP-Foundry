"""Tests for PTR- pipeline phase timeline report schema."""

import pytest
from openamp_foundry.evidence.pipeline_phase_timeline_report import (
    PipelinePhaseTimelineReport,
    TimelineEvent,
    VALID_PIPELINE_SCHEMA_TYPES,
    VALID_TIMELINE_VERDICTS,
    TERMINAL_SCHEMA_TYPES,
    build_pipeline_phase_timeline_report,
    format_pipeline_phase_timeline_report,
    validate_pipeline_phase_timeline_report,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EVENTS_COMPLETE = [
    {"schema_type": "BSP", "artifact_id": "A1", "created_at": "2026-07-01"},
    {"schema_type": "SAT", "artifact_id": "A2", "created_at": "2026-07-05"},
    {"schema_type": "PCC", "artifact_id": "A3", "created_at": "2026-07-10"},
]

_EVENTS_PARTIAL = [
    {"schema_type": "BSP", "artifact_id": "A1", "created_at": "2026-07-01"},
    {"schema_type": "RSR", "artifact_id": "A2", "created_at": "2026-07-03"},
]


def _build(**kwargs):
    defaults = dict(
        ptr_id="PTR-001",
        pipeline_run_id="RUN-001",
        pipeline_version="v1.0",
        batch_id="BATCH-01",
        event_dicts=_EVENTS_PARTIAL,
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_pipeline_phase_timeline_report(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_pipeline_schema_types_is_frozenset():
    assert isinstance(VALID_PIPELINE_SCHEMA_TYPES, frozenset)


def test_valid_pipeline_schema_types_contains_bsp():
    assert "BSP" in VALID_PIPELINE_SCHEMA_TYPES


def test_valid_pipeline_schema_types_contains_sat():
    assert "SAT" in VALID_PIPELINE_SCHEMA_TYPES


def test_valid_pipeline_schema_types_contains_pcc():
    assert "PCC" in VALID_PIPELINE_SCHEMA_TYPES


def test_valid_pipeline_schema_types_contains_fet():
    assert "FET" in VALID_PIPELINE_SCHEMA_TYPES


def test_valid_pipeline_schema_types_count():
    assert len(VALID_PIPELINE_SCHEMA_TYPES) == 16


def test_valid_timeline_verdicts_is_frozenset():
    assert isinstance(VALID_TIMELINE_VERDICTS, frozenset)


def test_valid_timeline_verdicts_contains_complete():
    assert "complete" in VALID_TIMELINE_VERDICTS


def test_valid_timeline_verdicts_contains_in_progress():
    assert "in_progress" in VALID_TIMELINE_VERDICTS


def test_valid_timeline_verdicts_contains_empty():
    assert "empty" in VALID_TIMELINE_VERDICTS


def test_terminal_schema_types_contains_sat():
    assert "SAT" in TERMINAL_SCHEMA_TYPES


def test_terminal_schema_types_contains_pcc():
    assert "PCC" in TERMINAL_SCHEMA_TYPES


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_pipeline_phase_timeline_report():
    assert isinstance(_build(), PipelinePhaseTimelineReport)


def test_build_ptr_id_stored():
    assert _build().ptr_id == "PTR-001"


def test_build_pipeline_run_id_stored():
    assert _build().pipeline_run_id == "RUN-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_complete_verdict_when_both_terminal_present():
    r = _build(event_dicts=_EVENTS_COMPLETE)
    assert r.timeline_verdict == "complete"


def test_build_in_progress_when_partial():
    r = _build()
    assert r.timeline_verdict == "in_progress"


def test_build_empty_verdict_when_no_events():
    r = _build(event_dicts=[])
    assert r.timeline_verdict == "empty"


def test_build_n_events_matches_input():
    r = _build()
    assert r.n_events == len(_EVENTS_PARTIAL)


def test_build_events_are_timeline_event():
    r = _build()
    for e in r.events:
        assert isinstance(e, TimelineEvent)


def test_build_events_sorted_by_created_at():
    events = [
        {"schema_type": "SAT", "artifact_id": "A2", "created_at": "2026-07-05"},
        {"schema_type": "BSP", "artifact_id": "A1", "created_at": "2026-07-01"},
    ]
    r = _build(event_dicts=events)
    assert r.events[0].created_at <= r.events[1].created_at


def test_build_schema_types_present_sorted():
    r = _build()
    assert r.schema_types_present == sorted(r.schema_types_present)


def test_build_terminal_schemas_present_empty_when_partial():
    r = _build()
    assert r.terminal_schemas_present == []


def test_build_terminal_schemas_present_when_complete():
    r = _build(event_dicts=_EVENTS_COMPLETE)
    assert set(r.terminal_schemas_present) == TERMINAL_SCHEMA_TYPES


def test_build_event_phase_nomination_for_bsp():
    events = [{"schema_type": "BSP", "artifact_id": "A1", "created_at": "2026-07-01"}]
    r = _build(event_dicts=events)
    assert r.events[0].phase == "nomination"


def test_build_event_phase_evidence_for_sat():
    events = [{"schema_type": "SAT", "artifact_id": "A1", "created_at": "2026-07-01"}]
    r = _build(event_dicts=events)
    assert r.events[0].phase == "evidence"


def test_build_event_phase_ranking_for_rsr():
    events = [{"schema_type": "RSR", "artifact_id": "A1", "created_at": "2026-07-01"}]
    r = _build(event_dicts=events)
    assert r.events[0].phase == "ranking"


def test_build_event_phase_integration_for_brc():
    events = [{"schema_type": "BRC", "artifact_id": "A1", "created_at": "2026-07-01"}]
    r = _build(event_dicts=events)
    assert r.events[0].phase == "integration"


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_ptr_id_prefix():
    with pytest.raises(ValueError, match="PTR-"):
        _build(ptr_id="BAD-001")


def test_validate_rejects_empty_pipeline_run_id():
    with pytest.raises(ValueError):
        _build(pipeline_run_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_unknown_schema_type():
    events = [{"schema_type": "UNKNOWN", "artifact_id": "A1", "created_at": "2026-07-01"}]
    with pytest.raises(ValueError, match="VALID_PIPELINE_SCHEMA_TYPES"):
        _build(event_dicts=events)


def test_validate_rejects_empty_artifact_id():
    events = [{"schema_type": "BSP", "artifact_id": "", "created_at": "2026-07-01"}]
    with pytest.raises(ValueError, match="artifact_id"):
        _build(event_dicts=events)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_ptr_id():
    assert "PTR-001" in format_pipeline_phase_timeline_report(_build())


def test_format_contains_pipeline_run_id():
    assert "RUN-001" in format_pipeline_phase_timeline_report(_build())


def test_format_contains_verdict():
    assert "in_progress" in format_pipeline_phase_timeline_report(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_pipeline_phase_timeline_report(_build())


def test_format_contains_event_schema_type():
    assert "BSP" in format_pipeline_phase_timeline_report(_build())


def test_format_contains_phase():
    assert "nomination" in format_pipeline_phase_timeline_report(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_pipeline_phase_timeline_report(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_pipeline_phase_timeline_report(_build())


def test_format_is_string():
    assert isinstance(format_pipeline_phase_timeline_report(_build()), str)

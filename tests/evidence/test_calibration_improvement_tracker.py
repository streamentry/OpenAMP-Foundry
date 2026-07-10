"""Tests for CIT- calibration improvement tracker schema."""

import pytest
from openamp_foundry.evidence.calibration_improvement_tracker import (
    CalibrationImprovementTracker,
    BatchHitRateEntry,
    VALID_CIT_TREND_DIRECTIONS,
    VALID_CIT_SUMMARY_GRADES,
    MIN_BATCHES_FOR_TREND,
    IMPROVEMENT_THRESHOLD,
    DEGRADATION_THRESHOLD,
    build_calibration_improvement_tracker,
    format_calibration_improvement_tracker,
    validate_calibration_improvement_tracker,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TWO_IMPROVING = [
    {"batch_id": "BATCH-01", "mbl_id": "MBL-001", "hit_rate": 0.20, "quality_grade": "C"},
    {"batch_id": "BATCH-02", "mbl_id": "MBL-002", "hit_rate": 0.35, "quality_grade": "B"},
]

_TWO_STABLE = [
    {"batch_id": "BATCH-01", "mbl_id": "MBL-001", "hit_rate": 0.20, "quality_grade": "C"},
    {"batch_id": "BATCH-02", "mbl_id": "MBL-002", "hit_rate": 0.22, "quality_grade": "C"},
]

_TWO_DEGRADING = [
    {"batch_id": "BATCH-01", "mbl_id": "MBL-001", "hit_rate": 0.30, "quality_grade": "B"},
    {"batch_id": "BATCH-02", "mbl_id": "MBL-002", "hit_rate": 0.10, "quality_grade": "C"},
]

_ONE_ENTRY = [
    {"batch_id": "BATCH-01", "mbl_id": "MBL-001", "hit_rate": 0.30, "quality_grade": "B"},
]


def _build(**kwargs):
    defaults = dict(
        cit_id="CIT-001",
        pipeline_version="v1.0",
        batch_entry_dicts=_TWO_IMPROVING,
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_calibration_improvement_tracker(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_cit_trend_directions_is_frozenset():
    assert isinstance(VALID_CIT_TREND_DIRECTIONS, frozenset)


def test_valid_cit_trend_directions_contains_improving():
    assert "improving" in VALID_CIT_TREND_DIRECTIONS


def test_valid_cit_trend_directions_contains_stable():
    assert "stable" in VALID_CIT_TREND_DIRECTIONS


def test_valid_cit_trend_directions_contains_degrading():
    assert "degrading" in VALID_CIT_TREND_DIRECTIONS


def test_valid_cit_trend_directions_contains_insufficient_data():
    assert "insufficient_data" in VALID_CIT_TREND_DIRECTIONS


def test_valid_cit_summary_grades_is_frozenset():
    assert isinstance(VALID_CIT_SUMMARY_GRADES, frozenset)


def test_valid_cit_summary_grades_contains_a():
    assert "A" in VALID_CIT_SUMMARY_GRADES


def test_valid_cit_summary_grades_contains_na():
    assert "N/A" in VALID_CIT_SUMMARY_GRADES


def test_min_batches_for_trend():
    assert MIN_BATCHES_FOR_TREND == 2


def test_improvement_threshold():
    assert IMPROVEMENT_THRESHOLD == 0.05


def test_degradation_threshold():
    assert DEGRADATION_THRESHOLD == -0.05


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_calibration_improvement_tracker():
    assert isinstance(_build(), CalibrationImprovementTracker)


def test_build_cit_id_stored():
    assert _build().cit_id == "CIT-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_improving_trend():
    r = _build(batch_entry_dicts=_TWO_IMPROVING)
    assert r.trend_direction == "improving"


def test_build_stable_trend():
    r = _build(batch_entry_dicts=_TWO_STABLE)
    assert r.trend_direction == "stable"


def test_build_degrading_trend():
    r = _build(batch_entry_dicts=_TWO_DEGRADING)
    assert r.trend_direction == "degrading"


def test_build_insufficient_data_with_one_entry():
    r = _build(batch_entry_dicts=_ONE_ENTRY)
    assert r.trend_direction == "insufficient_data"


def test_build_insufficient_data_grade_na():
    r = _build(batch_entry_dicts=_ONE_ENTRY)
    assert r.summary_grade == "N/A"


def test_build_n_batches_matches_input():
    r = _build(batch_entry_dicts=_TWO_IMPROVING)
    assert r.n_batches == 2


def test_build_n_batches_with_data_counts_non_na():
    entries = [
        {"batch_id": "B1", "mbl_id": "M1", "hit_rate": 0.30, "quality_grade": "B"},
        {"batch_id": "B2", "mbl_id": "M2", "hit_rate": 0.0, "quality_grade": "N/A"},
    ]
    r = _build(batch_entry_dicts=entries)
    assert r.n_batches_with_data == 1


def test_build_first_batch_hit_rate():
    r = _build(batch_entry_dicts=_TWO_IMPROVING)
    assert abs(r.first_batch_hit_rate - 0.20) < 1e-4


def test_build_latest_batch_hit_rate():
    r = _build(batch_entry_dicts=_TWO_IMPROVING)
    assert abs(r.latest_batch_hit_rate - 0.35) < 1e-4


def test_build_hit_rate_delta_improving():
    r = _build(batch_entry_dicts=_TWO_IMPROVING)
    assert abs(r.hit_rate_delta - 0.15) < 1e-4


def test_build_hit_rate_delta_degrading():
    r = _build(batch_entry_dicts=_TWO_DEGRADING)
    assert r.hit_rate_delta < 0


def test_build_batch_entries_are_batch_hit_rate_entry():
    for e in _build().batch_entries:
        assert isinstance(e, BatchHitRateEntry)


def test_build_empty_entries_insufficient_data():
    r = _build(batch_entry_dicts=[])
    assert r.trend_direction == "insufficient_data"


def test_build_improving_summary_grade_a():
    entries = [
        {"batch_id": "B1", "mbl_id": "M1", "hit_rate": 0.10, "quality_grade": "C"},
        {"batch_id": "B2", "mbl_id": "M2", "hit_rate": 0.30, "quality_grade": "B"},
    ]
    r = _build(batch_entry_dicts=entries)
    assert r.summary_grade == "A"


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_cit_id_prefix():
    with pytest.raises(ValueError, match="CIT-"):
        _build(cit_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_trend_direction():
    cit = _build()
    cit.trend_direction = "UNKNOWN"
    with pytest.raises(ValueError, match="trend_direction"):
        validate_calibration_improvement_tracker(cit)


def test_validate_rejects_invalid_summary_grade():
    cit = _build()
    cit.summary_grade = "X"
    with pytest.raises(ValueError, match="summary_grade"):
        validate_calibration_improvement_tracker(cit)


def test_validate_rejects_grade_not_na_when_insufficient_data():
    cit = _build(batch_entry_dicts=_ONE_ENTRY)
    cit.summary_grade = "A"
    with pytest.raises(ValueError, match="N/A"):
        validate_calibration_improvement_tracker(cit)


def test_validate_rejects_n_batches_mismatch():
    cit = _build()
    cit.n_batches = 99
    with pytest.raises(ValueError, match="n_batches"):
        validate_calibration_improvement_tracker(cit)


def test_validate_rejects_n_batches_with_data_mismatch():
    cit = _build()
    cit.n_batches_with_data = 99
    with pytest.raises(ValueError, match="n_batches_with_data"):
        validate_calibration_improvement_tracker(cit)


def test_validate_rejects_hit_rate_above_one_in_entry():
    entries = [
        {"batch_id": "B1", "mbl_id": "M1", "hit_rate": 1.5, "quality_grade": "A"},
        {"batch_id": "B2", "mbl_id": "M2", "hit_rate": 0.30, "quality_grade": "B"},
    ]
    with pytest.raises(ValueError, match="hit_rate"):
        _build(batch_entry_dicts=entries)


def test_validate_rejects_dry_lab_only_false():
    cit = _build()
    cit.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_calibration_improvement_tracker(cit)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_cit_id():
    assert "CIT-001" in format_calibration_improvement_tracker(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_calibration_improvement_tracker(_build())


def test_format_contains_trend_direction():
    assert "improving" in format_calibration_improvement_tracker(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_calibration_improvement_tracker(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_calibration_improvement_tracker(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_calibration_improvement_tracker(_build())


def test_format_is_string():
    assert isinstance(format_calibration_improvement_tracker(_build()), str)

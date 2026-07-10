"""Tests for MBL- multi-batch learning record schema."""

import pytest
from openamp_foundry.evidence.multi_batch_learning_record import (
    MultiBatchLearningRecord,
    VALID_MBL_QUALITY_GRADES,
    VALID_BATCH_LEARNING_STATUSES,
    GRADE_A_HIT_RATE,
    GRADE_B_HIT_RATE,
    GRADE_C_HIT_RATE,
    build_multi_batch_learning_record,
    format_multi_batch_learning_record,
    validate_multi_batch_learning_record,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        mbl_id="MBL-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        n_candidates_tested=20,
        n_confirmed_hits=8,
        auroc=0.78,
        batch_learning_status="data_complete",
        whr_ids=["WHR-001", "WHR-002"],
        pcu_id="PCU-001",
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_multi_batch_learning_record(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_mbl_quality_grades_is_frozenset():
    assert isinstance(VALID_MBL_QUALITY_GRADES, frozenset)


def test_valid_mbl_quality_grades_contains_a():
    assert "A" in VALID_MBL_QUALITY_GRADES


def test_valid_mbl_quality_grades_contains_b():
    assert "B" in VALID_MBL_QUALITY_GRADES


def test_valid_mbl_quality_grades_contains_c():
    assert "C" in VALID_MBL_QUALITY_GRADES


def test_valid_mbl_quality_grades_contains_d():
    assert "D" in VALID_MBL_QUALITY_GRADES


def test_valid_mbl_quality_grades_contains_na():
    assert "N/A" in VALID_MBL_QUALITY_GRADES


def test_valid_batch_learning_statuses_is_frozenset():
    assert isinstance(VALID_BATCH_LEARNING_STATUSES, frozenset)


def test_valid_batch_learning_statuses_contains_data_complete():
    assert "data_complete" in VALID_BATCH_LEARNING_STATUSES


def test_valid_batch_learning_statuses_contains_data_partial():
    assert "data_partial" in VALID_BATCH_LEARNING_STATUSES


def test_valid_batch_learning_statuses_contains_no_wet_lab_data():
    assert "no_wet_lab_data" in VALID_BATCH_LEARNING_STATUSES


def test_grade_a_hit_rate():
    assert GRADE_A_HIT_RATE == 0.40


def test_grade_b_hit_rate():
    assert GRADE_B_HIT_RATE == 0.25


def test_grade_c_hit_rate():
    assert GRADE_C_HIT_RATE == 0.10


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_multi_batch_learning_record():
    assert isinstance(_build(), MultiBatchLearningRecord)


def test_build_mbl_id_stored():
    assert _build().mbl_id == "MBL-001"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_n_candidates_tested_stored():
    assert _build().n_candidates_tested == 20


def test_build_n_confirmed_hits_stored():
    assert _build().n_confirmed_hits == 8


def test_build_hit_rate_computed():
    r = _build()
    assert abs(r.hit_rate - 8 / 20) < 1e-4


def test_build_auroc_stored():
    assert abs(_build().auroc - 0.78) < 1e-9


def test_build_grade_a_when_hit_rate_high():
    r = _build(n_candidates_tested=10, n_confirmed_hits=5)
    assert r.quality_grade == "A"


def test_build_grade_b_when_hit_rate_medium():
    r = _build(n_candidates_tested=10, n_confirmed_hits=3)
    assert r.quality_grade == "B"


def test_build_grade_c_when_hit_rate_low():
    r = _build(n_candidates_tested=10, n_confirmed_hits=1)
    assert r.quality_grade == "C"


def test_build_grade_d_when_hit_rate_zero():
    r = _build(n_candidates_tested=10, n_confirmed_hits=0)
    assert r.quality_grade == "D"


def test_build_grade_na_when_no_wet_lab_data():
    r = _build(n_candidates_tested=0, n_confirmed_hits=0, auroc=0.0, batch_learning_status="no_wet_lab_data")
    assert r.quality_grade == "N/A"


def test_build_status_data_complete_stored():
    assert _build().batch_learning_status == "data_complete"


def test_build_status_data_partial():
    r = _build(batch_learning_status="data_partial")
    assert r.batch_learning_status == "data_partial"


def test_build_no_wet_lab_data_hit_rate_zero():
    r = _build(n_candidates_tested=0, n_confirmed_hits=0, auroc=0.0, batch_learning_status="no_wet_lab_data")
    assert r.hit_rate == 0.0


def test_build_whr_ids_stored():
    assert _build().whr_ids == ["WHR-001", "WHR-002"]


def test_build_pcu_id_stored():
    assert _build().pcu_id == "PCU-001"


def test_build_pcu_id_defaults_empty():
    r = _build(pcu_id="")
    assert r.pcu_id == ""


def test_build_whr_ids_empty_list():
    r = _build(whr_ids=[])
    assert r.whr_ids == []


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_grade_a_at_boundary():
    r = _build(n_candidates_tested=10, n_confirmed_hits=4)
    assert r.quality_grade == "A"


def test_build_grade_b_at_boundary():
    r = _build(n_candidates_tested=20, n_confirmed_hits=5)
    assert r.quality_grade == "B"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_mbl_id_prefix():
    with pytest.raises(ValueError, match="MBL-"):
        _build(mbl_id="BAD-001")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_negative_n_candidates():
    mbl = _build()
    mbl.n_candidates_tested = -1
    with pytest.raises(ValueError, match="n_candidates_tested"):
        validate_multi_batch_learning_record(mbl)


def test_validate_rejects_negative_n_hits():
    mbl = _build()
    mbl.n_confirmed_hits = -1
    with pytest.raises(ValueError, match="n_confirmed_hits"):
        validate_multi_batch_learning_record(mbl)


def test_validate_rejects_hits_exceeding_tested():
    with pytest.raises(ValueError, match="n_confirmed_hits"):
        _build(n_candidates_tested=5, n_confirmed_hits=6)


def test_validate_rejects_invalid_quality_grade():
    mbl = _build()
    mbl.quality_grade = "X"
    with pytest.raises(ValueError, match="quality_grade"):
        validate_multi_batch_learning_record(mbl)


def test_validate_rejects_invalid_status():
    mbl = _build()
    mbl.batch_learning_status = "UNKNOWN"
    with pytest.raises(ValueError, match="batch_learning_status"):
        validate_multi_batch_learning_record(mbl)


def test_validate_rejects_grade_not_na_when_no_data():
    mbl = _build(n_candidates_tested=0, n_confirmed_hits=0, auroc=0.0, batch_learning_status="no_wet_lab_data")
    mbl.quality_grade = "A"
    with pytest.raises(ValueError, match="N/A"):
        validate_multi_batch_learning_record(mbl)


def test_validate_rejects_hit_rate_mismatch():
    mbl = _build()
    mbl.hit_rate = 0.99
    with pytest.raises(ValueError, match="hit_rate"):
        validate_multi_batch_learning_record(mbl)


def test_validate_rejects_dry_lab_only_false():
    mbl = _build()
    mbl.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_multi_batch_learning_record(mbl)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_auroc_above_one():
    with pytest.raises(ValueError, match="auroc"):
        _build(auroc=1.01)


def test_validate_rejects_auroc_below_zero():
    with pytest.raises(ValueError, match="auroc"):
        _build(auroc=-0.01)


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_mbl_id():
    assert "MBL-001" in format_multi_batch_learning_record(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_multi_batch_learning_record(_build())


def test_format_contains_status():
    assert "data_complete" in format_multi_batch_learning_record(_build())


def test_format_contains_grade():
    assert _build().quality_grade in format_multi_batch_learning_record(_build())


def test_format_contains_n_confirmed_hits():
    assert "8" in format_multi_batch_learning_record(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_multi_batch_learning_record(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_multi_batch_learning_record(_build())


def test_format_is_string():
    assert isinstance(format_multi_batch_learning_record(_build()), str)

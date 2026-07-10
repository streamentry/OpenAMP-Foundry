"""Tests for RCC- recalibration confidence certificate schema."""

import pytest
from openamp_foundry.evidence.recalibration_confidence_certificate import (
    RecalibrationConfidenceCertificate,
    BatchCohortEntry,
    VALID_RCC_GRADES,
    VALID_RCC_VERDICTS,
    VALID_CONSISTENCY_RATINGS,
    MIN_BATCHES_FOR_CONFIDENCE,
    HIGH_CONFIDENCE_MIN_BATCHES,
    MODERATE_CONFIDENCE_MIN_BATCHES,
    MIN_COHORT_SIZE_PER_BATCH,
    GRADE_A_MIN_BATCHES,
    GRADE_B_MIN_BATCHES,
    GRADE_C_MIN_BATCHES,
    build_recalibration_confidence_certificate,
    format_recalibration_confidence_certificate,
    validate_recalibration_confidence_certificate,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FOUR_CONSISTENT = [
    {"batch_id": "B1", "mbl_id": "M1", "cohort_size": 10, "quality_grade": "A"},
    {"batch_id": "B2", "mbl_id": "M2", "cohort_size": 12, "quality_grade": "A"},
    {"batch_id": "B3", "mbl_id": "M3", "cohort_size": 11, "quality_grade": "A"},
    {"batch_id": "B4", "mbl_id": "M4", "cohort_size": 9, "quality_grade": "A"},
]

_TWO_MODERATE = [
    {"batch_id": "B1", "mbl_id": "M1", "cohort_size": 8, "quality_grade": "A"},
    {"batch_id": "B2", "mbl_id": "M2", "cohort_size": 7, "quality_grade": "B"},
]

_TWO_INCONSISTENT = [
    {"batch_id": "B1", "mbl_id": "M1", "cohort_size": 8, "quality_grade": "A"},
    {"batch_id": "B2", "mbl_id": "M2", "cohort_size": 7, "quality_grade": "C"},
]

_ONE_ENTRY = [
    {"batch_id": "B1", "mbl_id": "M1", "cohort_size": 10, "quality_grade": "B"},
]


def _build(**kwargs):
    defaults = dict(
        rcc_id="RCC-001",
        pipeline_version="v1.0",
        cit_id="CIT-001",
        lpr_id="LPR-001",
        batch_cohort_entry_dicts=_FOUR_CONSISTENT,
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_recalibration_confidence_certificate(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_rcc_grades_is_frozenset():
    assert isinstance(VALID_RCC_GRADES, frozenset)


def test_valid_rcc_grades_contains_a():
    assert "A" in VALID_RCC_GRADES


def test_valid_rcc_grades_contains_b():
    assert "B" in VALID_RCC_GRADES


def test_valid_rcc_grades_contains_c():
    assert "C" in VALID_RCC_GRADES


def test_valid_rcc_grades_contains_d():
    assert "D" in VALID_RCC_GRADES


def test_valid_rcc_verdicts_is_frozenset():
    assert isinstance(VALID_RCC_VERDICTS, frozenset)


def test_valid_rcc_verdicts_contains_high_confidence():
    assert "high_confidence" in VALID_RCC_VERDICTS


def test_valid_rcc_verdicts_contains_moderate_confidence():
    assert "moderate_confidence" in VALID_RCC_VERDICTS


def test_valid_rcc_verdicts_contains_low_confidence():
    assert "low_confidence" in VALID_RCC_VERDICTS


def test_valid_rcc_verdicts_contains_insufficient_data():
    assert "insufficient_data" in VALID_RCC_VERDICTS


def test_valid_consistency_ratings_is_frozenset():
    assert isinstance(VALID_CONSISTENCY_RATINGS, frozenset)


def test_valid_consistency_ratings_contains_consistent():
    assert "consistent" in VALID_CONSISTENCY_RATINGS


def test_valid_consistency_ratings_contains_moderately_consistent():
    assert "moderately_consistent" in VALID_CONSISTENCY_RATINGS


def test_valid_consistency_ratings_contains_inconsistent():
    assert "inconsistent" in VALID_CONSISTENCY_RATINGS


def test_valid_consistency_ratings_contains_unknown():
    assert "unknown" in VALID_CONSISTENCY_RATINGS


def test_min_batches_for_confidence():
    assert MIN_BATCHES_FOR_CONFIDENCE == 2


def test_high_confidence_min_batches():
    assert HIGH_CONFIDENCE_MIN_BATCHES == 4


def test_moderate_confidence_min_batches():
    assert MODERATE_CONFIDENCE_MIN_BATCHES == 2


def test_min_cohort_size_per_batch():
    assert MIN_COHORT_SIZE_PER_BATCH == 5


def test_grade_a_min_batches():
    assert GRADE_A_MIN_BATCHES == 4


def test_grade_b_min_batches():
    assert GRADE_B_MIN_BATCHES == 2


def test_grade_c_min_batches():
    assert GRADE_C_MIN_BATCHES == 1


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_recalibration_confidence_certificate():
    assert isinstance(_build(), RecalibrationConfidenceCertificate)


def test_build_rcc_id_stored():
    assert _build().rcc_id == "RCC-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_cit_id_stored():
    assert _build().cit_id == "CIT-001"


def test_build_lpr_id_stored():
    assert _build().lpr_id == "LPR-001"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_four_consistent_gives_grade_a():
    assert _build(batch_cohort_entry_dicts=_FOUR_CONSISTENT).rcc_grade == "A"


def test_build_four_consistent_gives_high_confidence():
    assert _build(batch_cohort_entry_dicts=_FOUR_CONSISTENT).rcc_verdict == "high_confidence"


def test_build_two_moderate_gives_grade_b():
    assert _build(batch_cohort_entry_dicts=_TWO_MODERATE).rcc_grade == "B"


def test_build_two_moderate_gives_moderate_confidence():
    assert _build(batch_cohort_entry_dicts=_TWO_MODERATE).rcc_verdict == "moderate_confidence"


def test_build_one_entry_gives_grade_d():
    assert _build(batch_cohort_entry_dicts=_ONE_ENTRY).rcc_grade == "D"


def test_build_one_entry_gives_insufficient_data():
    assert _build(batch_cohort_entry_dicts=_ONE_ENTRY).rcc_verdict == "insufficient_data"


def test_build_empty_gives_grade_d():
    assert _build(batch_cohort_entry_dicts=[]).rcc_grade == "D"


def test_build_empty_gives_insufficient_data():
    assert _build(batch_cohort_entry_dicts=[]).rcc_verdict == "insufficient_data"


def test_build_n_batches_assessed_matches_input():
    assert _build(batch_cohort_entry_dicts=_FOUR_CONSISTENT).n_batches_assessed == 4


def test_build_total_cohort_size_summed():
    r = _build(batch_cohort_entry_dicts=_FOUR_CONSISTENT)
    assert r.total_cohort_size == 42


def test_build_cross_batch_consistency_consistent():
    assert _build(batch_cohort_entry_dicts=_FOUR_CONSISTENT).cross_batch_consistency == "consistent"


def test_build_cross_batch_consistency_moderately():
    assert _build(batch_cohort_entry_dicts=_TWO_MODERATE).cross_batch_consistency == "moderately_consistent"


def test_build_cross_batch_consistency_unknown_single():
    assert _build(batch_cohort_entry_dicts=_ONE_ENTRY).cross_batch_consistency == "unknown"


def test_build_batch_entries_are_batch_cohort_entry():
    for e in _build().batch_cohort_entries:
        assert isinstance(e, BatchCohortEntry)


def test_build_confidence_rationale_non_empty():
    assert _build().confidence_rationale != ""


def test_build_confidence_rationale_contains_grade():
    r = _build()
    assert r.rcc_grade in r.confidence_rationale


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_two_consistent_gives_grade_a():
    entries = [
        {"batch_id": "B1", "mbl_id": "M1", "cohort_size": 10, "quality_grade": "B"},
        {"batch_id": "B2", "mbl_id": "M2", "cohort_size": 10, "quality_grade": "B"},
    ]
    r = _build(batch_cohort_entry_dicts=entries)
    assert r.rcc_grade == "B"


def test_build_two_inconsistent_gives_grade_b():
    # 2 unique grades out of 2 entries → moderately_consistent → grade B
    assert _build(batch_cohort_entry_dicts=_TWO_INCONSISTENT).rcc_grade == "B"


def test_build_two_inconsistent_gives_moderate_confidence():
    assert _build(batch_cohort_entry_dicts=_TWO_INCONSISTENT).rcc_verdict == "moderate_confidence"


def test_build_three_unique_grades_inconsistent():
    entries = [
        {"batch_id": "B1", "mbl_id": "M1", "cohort_size": 5, "quality_grade": "A"},
        {"batch_id": "B2", "mbl_id": "M2", "cohort_size": 5, "quality_grade": "B"},
        {"batch_id": "B3", "mbl_id": "M3", "cohort_size": 5, "quality_grade": "C"},
    ]
    r = _build(batch_cohort_entry_dicts=entries)
    assert r.cross_batch_consistency == "inconsistent"


def test_build_na_grade_entries_excluded_from_consistency():
    entries = [
        {"batch_id": "B1", "mbl_id": "M1", "cohort_size": 5, "quality_grade": "N/A"},
        {"batch_id": "B2", "mbl_id": "M2", "cohort_size": 5, "quality_grade": "N/A"},
    ]
    r = _build(batch_cohort_entry_dicts=entries)
    assert r.cross_batch_consistency == "unknown"


def test_build_cohort_size_zero_allowed():
    entries = [
        {"batch_id": "B1", "mbl_id": "M1", "cohort_size": 0, "quality_grade": "C"},
        {"batch_id": "B2", "mbl_id": "M2", "cohort_size": 0, "quality_grade": "C"},
    ]
    r = _build(batch_cohort_entry_dicts=entries)
    assert r.total_cohort_size == 0


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_rcc_id_prefix():
    with pytest.raises(ValueError, match="RCC-"):
        _build(rcc_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_bad_cit_id_prefix():
    with pytest.raises(ValueError, match="CIT-"):
        _build(cit_id="BAD-001")


def test_validate_rejects_bad_lpr_id_prefix():
    with pytest.raises(ValueError, match="LPR-"):
        _build(lpr_id="BAD-001")


def test_validate_rejects_negative_cohort_size():
    entries = [
        {"batch_id": "B1", "mbl_id": "M1", "cohort_size": -1, "quality_grade": "A"},
        {"batch_id": "B2", "mbl_id": "M2", "cohort_size": 5, "quality_grade": "A"},
    ]
    with pytest.raises(ValueError, match="cohort_size"):
        _build(batch_cohort_entry_dicts=entries)


def test_validate_rejects_n_batches_mismatch():
    rcc = _build()
    rcc.n_batches_assessed = 99
    with pytest.raises(ValueError, match="n_batches_assessed"):
        validate_recalibration_confidence_certificate(rcc)


def test_validate_rejects_total_cohort_mismatch():
    rcc = _build()
    rcc.total_cohort_size = 999
    with pytest.raises(ValueError, match="total_cohort_size"):
        validate_recalibration_confidence_certificate(rcc)


def test_validate_rejects_invalid_consistency():
    rcc = _build()
    rcc.cross_batch_consistency = "UNKNOWN"
    with pytest.raises(ValueError, match="cross_batch_consistency"):
        validate_recalibration_confidence_certificate(rcc)


def test_validate_rejects_invalid_rcc_grade():
    rcc = _build()
    rcc.rcc_grade = "X"
    with pytest.raises(ValueError, match="rcc_grade"):
        validate_recalibration_confidence_certificate(rcc)


def test_validate_rejects_invalid_rcc_verdict():
    rcc = _build()
    rcc.rcc_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="rcc_verdict"):
        validate_recalibration_confidence_certificate(rcc)


def test_validate_rejects_empty_confidence_rationale():
    rcc = _build()
    rcc.confidence_rationale = ""
    with pytest.raises(ValueError, match="confidence_rationale"):
        validate_recalibration_confidence_certificate(rcc)


def test_validate_rejects_dry_lab_only_false():
    rcc = _build()
    rcc.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_recalibration_confidence_certificate(rcc)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_rcc_id():
    assert "RCC-001" in format_recalibration_confidence_certificate(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_recalibration_confidence_certificate(_build())


def test_format_contains_cit_id():
    assert "CIT-001" in format_recalibration_confidence_certificate(_build())


def test_format_contains_lpr_id():
    assert "LPR-001" in format_recalibration_confidence_certificate(_build())


def test_format_contains_grade():
    assert "A" in format_recalibration_confidence_certificate(_build())


def test_format_contains_verdict():
    assert "high_confidence" in format_recalibration_confidence_certificate(_build())


def test_format_contains_batch_id():
    assert "B1" in format_recalibration_confidence_certificate(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_recalibration_confidence_certificate(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_recalibration_confidence_certificate(_build())


def test_format_is_string():
    assert isinstance(format_recalibration_confidence_certificate(_build()), str)

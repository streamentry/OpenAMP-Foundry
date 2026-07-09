import pytest
from openamp_foundry.evidence.calibration_performance_summary import (
    CalibrationPerformanceEntry,
    CalibrationPerformanceResult,
    validate_calibration_performance,
    validate_calibration_performance_dict,
    MAX_CALIBRATION_NOTES_LENGTH,
    MIN_CANDIDATES_FOR_RELIABLE_ESTIMATE,
    HIGH_FP_RATE_THRESHOLD,
    LOW_RECALL_THRESHOLD,
    POOR_BRIER_SCORE_THRESHOLD,
)


def _valid_entry(**overrides) -> CalibrationPerformanceEntry:
    base = dict(
        summary_id="CPS-001",
        pipeline_version="0.9.9",
        evaluation_date="2026-07-10",
        batch_ids_evaluated=["BATCH-001", "BATCH-002"],
        total_candidates_evaluated=20,
        true_positive_count=10,
        false_positive_count=2,
        true_negative_count=6,
        false_negative_count=2,
        brier_score=0.12,
        calibration_notes="Calibration looks reasonable. TP rate is acceptable.",
        reviewer="reviewer@example.com",
        dry_lab_only=False,
    )
    base.update(overrides)
    return CalibrationPerformanceEntry(**base)


def _valid_dict(**overrides) -> dict:
    base = dict(
        summary_id="CPS-001",
        pipeline_version="0.9.9",
        evaluation_date="2026-07-10",
        batch_ids_evaluated=["BATCH-001", "BATCH-002"],
        total_candidates_evaluated=20,
        true_positive_count=10,
        false_positive_count=2,
        true_negative_count=6,
        false_negative_count=2,
        brier_score=0.12,
        calibration_notes="Calibration looks reasonable.",
        reviewer="reviewer@example.com",
        dry_lab_only=False,
    )
    base.update(overrides)
    return base


# --- Happy path ---

def test_valid_entry_passes():
    result = validate_calibration_performance(_valid_entry())
    assert result.passed
    assert result.errors == []
    assert result.warnings == []


def test_result_dry_lab_only_always_false():
    result = validate_calibration_performance(_valid_entry())
    assert result.dry_lab_only is False


def test_result_fields_populated():
    result = validate_calibration_performance(_valid_entry())
    assert result.summary_id == "CPS-001"
    assert result.pipeline_version == "0.9.9"
    assert result.total_candidates_evaluated == 20
    assert result.brier_score == 0.12


def test_single_batch_passes():
    result = validate_calibration_performance(
        _valid_entry(batch_ids_evaluated=["BATCH-001"])
    )
    assert result.passed


def test_brier_score_zero_passes():
    result = validate_calibration_performance(_valid_entry(brier_score=0.0))
    assert result.passed


def test_brier_score_one_passes_with_warning():
    result = validate_calibration_performance(_valid_entry(brier_score=1.0))
    assert result.passed
    assert any("brier" in w.lower() for w in result.warnings)


def test_empty_calibration_notes_passes():
    result = validate_calibration_performance(_valid_entry(calibration_notes=""))
    assert result.passed


def test_all_zeros_except_tp_passes():
    result = validate_calibration_performance(
        _valid_entry(
            total_candidates_evaluated=5,
            true_positive_count=5,
            false_positive_count=0,
            true_negative_count=0,
            false_negative_count=0,
        )
    )
    assert result.passed


# --- summary_id ---

def test_summary_id_must_start_with_cps():
    result = validate_calibration_performance(_valid_entry(summary_id="CAL-001"))
    assert not result.passed
    assert any("CPS-" in e for e in result.errors)


def test_summary_id_empty_fails():
    result = validate_calibration_performance(_valid_entry(summary_id=""))
    assert not result.passed


def test_summary_id_cps_prefix_valid():
    result = validate_calibration_performance(_valid_entry(summary_id="CPS-999"))
    assert result.passed


# --- batch_ids_evaluated ---

def test_empty_batch_ids_fails():
    result = validate_calibration_performance(_valid_entry(batch_ids_evaluated=[]))
    assert not result.passed
    assert any("batch_ids_evaluated" in e for e in result.errors)


# --- total_candidates_evaluated ---

def test_zero_candidates_fails():
    result = validate_calibration_performance(
        _valid_entry(
            total_candidates_evaluated=0,
            true_positive_count=0,
            false_positive_count=0,
            true_negative_count=0,
            false_negative_count=0,
        )
    )
    assert not result.passed


def test_negative_candidates_fails():
    result = validate_calibration_performance(
        _valid_entry(total_candidates_evaluated=-1)
    )
    assert not result.passed


def test_small_evaluation_window_warns():
    n = MIN_CANDIDATES_FOR_RELIABLE_ESTIMATE - 1
    result = validate_calibration_performance(
        _valid_entry(
            total_candidates_evaluated=n,
            true_positive_count=n,
            false_positive_count=0,
            true_negative_count=0,
            false_negative_count=0,
        )
    )
    assert result.passed
    assert any("small" in w.lower() or "too small" in w.lower() for w in result.warnings)


def test_adequate_window_no_size_warning():
    n = MIN_CANDIDATES_FOR_RELIABLE_ESTIMATE
    result = validate_calibration_performance(
        _valid_entry(
            total_candidates_evaluated=n,
            true_positive_count=n,
            false_positive_count=0,
            true_negative_count=0,
            false_negative_count=0,
        )
    )
    assert not any("too small" in w.lower() for w in result.warnings)


# --- confusion matrix counts ---

def test_negative_tp_fails():
    result = validate_calibration_performance(_valid_entry(true_positive_count=-1))
    assert not result.passed
    assert any("true_positive_count" in e for e in result.errors)


def test_negative_fp_fails():
    result = validate_calibration_performance(_valid_entry(false_positive_count=-1))
    assert not result.passed


def test_negative_tn_fails():
    result = validate_calibration_performance(_valid_entry(true_negative_count=-1))
    assert not result.passed


def test_negative_fn_fails():
    result = validate_calibration_performance(_valid_entry(false_negative_count=-1))
    assert not result.passed


def test_confusion_sum_mismatch_fails():
    result = validate_calibration_performance(
        _valid_entry(
            total_candidates_evaluated=25,
            true_positive_count=10,
            false_positive_count=2,
            true_negative_count=6,
            false_negative_count=2,
        )
    )
    assert not result.passed
    assert any("TP + FP + TN + FN" in e for e in result.errors)


def test_confusion_sum_matches_passes():
    result = validate_calibration_performance(
        _valid_entry(
            total_candidates_evaluated=20,
            true_positive_count=10,
            false_positive_count=2,
            true_negative_count=6,
            false_negative_count=2,
        )
    )
    assert result.passed


# --- brier_score ---

def test_brier_score_negative_fails():
    result = validate_calibration_performance(_valid_entry(brier_score=-0.01))
    assert not result.passed
    assert any("brier_score" in e for e in result.errors)


def test_brier_score_over_one_fails():
    result = validate_calibration_performance(_valid_entry(brier_score=1.01))
    assert not result.passed


def test_poor_brier_score_warns():
    result = validate_calibration_performance(
        _valid_entry(brier_score=POOR_BRIER_SCORE_THRESHOLD + 0.01)
    )
    assert result.passed
    assert any("brier" in w.lower() for w in result.warnings)


def test_good_brier_score_no_warn():
    result = validate_calibration_performance(
        _valid_entry(brier_score=POOR_BRIER_SCORE_THRESHOLD - 0.01)
    )
    assert not any("brier" in w.lower() for w in result.warnings)


# --- calibration_notes ---

def test_notes_at_max_length_passes():
    result = validate_calibration_performance(
        _valid_entry(calibration_notes="A" * MAX_CALIBRATION_NOTES_LENGTH)
    )
    assert result.passed


def test_notes_over_max_fails():
    result = validate_calibration_performance(
        _valid_entry(calibration_notes="A" * (MAX_CALIBRATION_NOTES_LENGTH + 1))
    )
    assert not result.passed


# --- reviewer ---

def test_empty_reviewer_fails():
    result = validate_calibration_performance(_valid_entry(reviewer=""))
    assert not result.passed
    assert any("reviewer" in e for e in result.errors)


# --- dry_lab_only must be False ---

def test_dry_lab_only_true_fails():
    result = validate_calibration_performance(_valid_entry(dry_lab_only=True))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


def test_dry_lab_only_false_passes():
    result = validate_calibration_performance(_valid_entry(dry_lab_only=False))
    assert result.passed


# --- warnings ---

def test_high_fp_rate_warns():
    result = validate_calibration_performance(
        _valid_entry(
            total_candidates_evaluated=20,
            true_positive_count=5,
            false_positive_count=11,
            true_negative_count=2,
            false_negative_count=2,
        )
    )
    assert result.passed
    assert any("over-predicting" in w.lower() or "false positive" in w.lower() for w in result.warnings)


def test_acceptable_fp_rate_no_warn():
    result = validate_calibration_performance(
        _valid_entry(
            total_candidates_evaluated=20,
            true_positive_count=10,
            false_positive_count=2,
            true_negative_count=6,
            false_negative_count=2,
        )
    )
    assert not any("over-predicting" in w.lower() for w in result.warnings)


def test_low_recall_warns():
    result = validate_calibration_performance(
        _valid_entry(
            total_candidates_evaluated=20,
            true_positive_count=2,
            false_positive_count=4,
            true_negative_count=4,
            false_negative_count=10,
        )
    )
    assert result.passed
    assert any("recall" in w.lower() or "missing many" in w.lower() for w in result.warnings)


def test_adequate_recall_no_warn():
    result = validate_calibration_performance(
        _valid_entry(
            total_candidates_evaluated=20,
            true_positive_count=10,
            false_positive_count=2,
            true_negative_count=6,
            false_negative_count=2,
        )
    )
    assert not any("recall" in w.lower() for w in result.warnings)


# --- dict interface ---

def test_valid_dict_passes():
    result = validate_calibration_performance_dict(_valid_dict())
    assert result.passed


def test_missing_summary_id_fails():
    d = _valid_dict()
    del d["summary_id"]
    result = validate_calibration_performance_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


def test_missing_brier_score_fails():
    d = _valid_dict()
    del d["brier_score"]
    result = validate_calibration_performance_dict(d)
    assert not result.passed


def test_missing_true_positive_count_fails():
    d = _valid_dict()
    del d["true_positive_count"]
    result = validate_calibration_performance_dict(d)
    assert not result.passed


def test_dict_dry_lab_only_defaults_false():
    d = _valid_dict()
    del d["dry_lab_only"]
    result = validate_calibration_performance_dict(d)
    assert result.passed
    assert result.dry_lab_only is False


def test_multiple_missing_fields():
    d = {}
    result = validate_calibration_performance_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


# --- constants ---

def test_max_calibration_notes_length_value():
    assert MAX_CALIBRATION_NOTES_LENGTH == 400


def test_min_candidates_value():
    assert MIN_CANDIDATES_FOR_RELIABLE_ESTIMATE == 10


def test_high_fp_rate_threshold_value():
    assert HIGH_FP_RATE_THRESHOLD == 0.5


def test_low_recall_threshold_value():
    assert LOW_RECALL_THRESHOLD == 0.3


def test_poor_brier_score_threshold_value():
    assert POOR_BRIER_SCORE_THRESHOLD == 0.25

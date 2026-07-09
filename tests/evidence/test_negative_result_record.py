import pytest
from openamp_foundry.evidence.negative_result_record import (
    NegativeResultEntry,
    NegativeResultResult,
    validate_negative_result,
    validate_negative_result_dict,
    VALID_FAILURE_CATEGORIES,
    VALID_ASSAY_TYPES,
    MAX_FAILURE_DESCRIPTION_LENGTH,
    MAX_HYPOTHESIS_IMPACT_LENGTH,
    LARGE_FAILURE_SET_THRESHOLD,
    RECALIBRATION_HINT,
)


def _valid_entry(**overrides) -> NegativeResultEntry:
    base = dict(
        record_id="NRR-001",
        batch_id="BATCH-001",
        pipeline_version="0.9.7",
        record_date="2026-07-10",
        failure_category="below_activity_threshold",
        failure_description=(
            "Candidate AMP-042 showed MIC of 128 ug/mL against E. coli, "
            "far above the expected 4 ug/mL threshold. The pipeline predicted "
            "high activity but the prediction was not confirmed by assay."
        ),
        candidate_ids=["AMP-042", "AMP-043"],
        assay_type="mic_assay",
        expected_outcome="MIC <= 4 ug/mL for both candidates",
        observed_outcome="MIC = 128 ug/mL for AMP-042; MIC = 64 ug/mL for AMP-043",
        hypothesis_impact=(
            "This result refutes the initial activity hypothesis for these candidates. "
            "The pipeline may be over-optimistic for this peptide family."
        ),
        will_be_reported=True,
        recorded_by="researcher@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return NegativeResultEntry(**base)


def _valid_dict(**overrides) -> dict:
    base = dict(
        record_id="NRR-001",
        batch_id="BATCH-001",
        pipeline_version="0.9.7",
        record_date="2026-07-10",
        failure_category="below_activity_threshold",
        failure_description=(
            "Candidates did not meet activity threshold in broth microdilution assay."
        ),
        candidate_ids=["AMP-042", "AMP-043"],
        assay_type="mic_assay",
        expected_outcome="MIC <= 4 ug/mL",
        observed_outcome="MIC = 128 ug/mL",
        hypothesis_impact="Activity hypothesis refuted for these candidates. Pipeline review needed.",
        will_be_reported=True,
        recorded_by="researcher@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return base


# --- Happy path ---

def test_valid_entry_passes():
    result = validate_negative_result(_valid_entry())
    assert result.passed
    assert result.errors == []
    assert result.warnings == []


def test_result_fields_populated():
    result = validate_negative_result(_valid_entry())
    assert result.record_id == "NRR-001"
    assert result.batch_id == "BATCH-001"
    assert result.failure_category == "below_activity_threshold"
    assert result.candidate_count == 2
    assert result.will_be_reported is True


def test_dry_lab_only_preserved():
    result = validate_negative_result(_valid_entry(dry_lab_only=False))
    assert result.passed
    assert result.dry_lab_only is False


def test_all_failure_categories_valid():
    for cat in VALID_FAILURE_CATEGORIES:
        e = _valid_entry(failure_category=cat)
        if cat == "model_overprediction":
            e = _valid_entry(
                failure_category=cat,
                hypothesis_impact="This result suggests recalibration of the model is needed.",
            )
        result = validate_negative_result(e)
        assert result.passed, f"failure_category={cat} should pass"


def test_all_assay_types_valid():
    for assay in VALID_ASSAY_TYPES:
        result = validate_negative_result(_valid_entry(assay_type=assay))
        assert result.passed, f"assay_type={assay} should pass"


def test_single_candidate_passes():
    result = validate_negative_result(_valid_entry(candidate_ids=["AMP-001"]))
    assert result.passed


# --- record_id ---

def test_record_id_must_start_with_nrr():
    result = validate_negative_result(_valid_entry(record_id="NEG-001"))
    assert not result.passed
    assert any("NRR-" in e for e in result.errors)


def test_record_id_empty_fails():
    result = validate_negative_result(_valid_entry(record_id=""))
    assert not result.passed


def test_record_id_nrr_prefix_valid():
    result = validate_negative_result(_valid_entry(record_id="NRR-999"))
    assert result.passed


# --- failure_category ---

def test_invalid_failure_category_fails():
    result = validate_negative_result(_valid_entry(failure_category="bad_category"))
    assert not result.passed
    assert any("failure_category" in e for e in result.errors)


def test_empty_failure_category_fails():
    result = validate_negative_result(_valid_entry(failure_category=""))
    assert not result.passed


# --- failure_description ---

def test_empty_failure_description_fails():
    result = validate_negative_result(_valid_entry(failure_description=""))
    assert not result.passed
    assert any("failure_description" in e for e in result.errors)


def test_failure_description_at_max_passes():
    result = validate_negative_result(
        _valid_entry(failure_description="A" * MAX_FAILURE_DESCRIPTION_LENGTH)
    )
    assert result.passed


def test_failure_description_over_max_fails():
    result = validate_negative_result(
        _valid_entry(failure_description="A" * (MAX_FAILURE_DESCRIPTION_LENGTH + 1))
    )
    assert not result.passed


# --- candidate_ids ---

def test_empty_candidate_ids_fails():
    result = validate_negative_result(_valid_entry(candidate_ids=[]))
    assert not result.passed
    assert any("candidate_ids" in e for e in result.errors)


def test_large_candidate_set_warns():
    ids = [f"AMP-{i:03d}" for i in range(LARGE_FAILURE_SET_THRESHOLD + 1)]
    result = validate_negative_result(_valid_entry(candidate_ids=ids))
    assert result.passed
    assert any("systematic" in w.lower() or "recalibration" in w.lower() for w in result.warnings)


def test_candidate_count_at_threshold_no_warn():
    ids = [f"AMP-{i:03d}" for i in range(LARGE_FAILURE_SET_THRESHOLD)]
    result = validate_negative_result(_valid_entry(candidate_ids=ids))
    assert not any("systematic" in w.lower() for w in result.warnings)


# --- assay_type ---

def test_invalid_assay_type_fails():
    result = validate_negative_result(_valid_entry(assay_type="unknown_assay"))
    assert not result.passed
    assert any("assay_type" in e for e in result.errors)


def test_empty_assay_type_fails():
    result = validate_negative_result(_valid_entry(assay_type=""))
    assert not result.passed


# --- expected_outcome ---

def test_empty_expected_outcome_fails():
    result = validate_negative_result(_valid_entry(expected_outcome=""))
    assert not result.passed
    assert any("expected_outcome" in e for e in result.errors)


# --- observed_outcome ---

def test_empty_observed_outcome_fails():
    result = validate_negative_result(_valid_entry(observed_outcome=""))
    assert not result.passed
    assert any("observed_outcome" in e for e in result.errors)


# --- hypothesis_impact ---

def test_empty_hypothesis_impact_fails():
    result = validate_negative_result(_valid_entry(hypothesis_impact=""))
    assert not result.passed
    assert any("hypothesis_impact" in e for e in result.errors)


def test_hypothesis_impact_at_max_passes():
    result = validate_negative_result(
        _valid_entry(hypothesis_impact="A" * MAX_HYPOTHESIS_IMPACT_LENGTH)
    )
    assert result.passed


def test_hypothesis_impact_over_max_fails():
    result = validate_negative_result(
        _valid_entry(hypothesis_impact="A" * (MAX_HYPOTHESIS_IMPACT_LENGTH + 1))
    )
    assert not result.passed


# --- recorded_by ---

def test_empty_recorded_by_fails():
    result = validate_negative_result(_valid_entry(recorded_by=""))
    assert not result.passed
    assert any("recorded_by" in e for e in result.errors)


# --- will_be_reported ---

def test_not_reported_warns():
    result = validate_negative_result(_valid_entry(will_be_reported=False))
    assert result.passed
    assert any("publication bias" in w.lower() or "suppressing" in w.lower() for w in result.warnings)


def test_will_be_reported_true_no_warn():
    result = validate_negative_result(_valid_entry(will_be_reported=True))
    assert not any("publication bias" in w.lower() for w in result.warnings)


# --- model_overprediction warning ---

def test_model_overprediction_no_calibration_warns():
    result = validate_negative_result(
        _valid_entry(
            failure_category="model_overprediction",
            hypothesis_impact="The model was wrong. This needs further investigation.",
        )
    )
    assert result.passed
    assert any("recalibration" in w.lower() or "calibration" in w.lower() for w in result.warnings)


def test_model_overprediction_with_calibration_no_warn():
    result = validate_negative_result(
        _valid_entry(
            failure_category="model_overprediction",
            hypothesis_impact="This result triggers a recalibration of the model's activity predictions.",
        )
    )
    assert result.passed
    assert not any("recalibration" in w.lower() and "should trigger" in w.lower() for w in result.warnings)


def test_below_threshold_no_calibration_warning():
    result = validate_negative_result(
        _valid_entry(failure_category="below_activity_threshold")
    )
    assert not any("recalibration" in w.lower() and "should trigger" in w.lower() for w in result.warnings)


# --- dict interface ---

def test_valid_dict_passes():
    result = validate_negative_result_dict(_valid_dict())
    assert result.passed


def test_missing_record_id_fails():
    d = _valid_dict()
    del d["record_id"]
    result = validate_negative_result_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


def test_missing_candidate_ids_fails():
    d = _valid_dict()
    del d["candidate_ids"]
    result = validate_negative_result_dict(d)
    assert not result.passed


def test_missing_will_be_reported_fails():
    d = _valid_dict()
    del d["will_be_reported"]
    result = validate_negative_result_dict(d)
    assert not result.passed


def test_dict_dry_lab_only_defaults_true():
    d = _valid_dict()
    del d["dry_lab_only"]
    result = validate_negative_result_dict(d)
    assert result.passed
    assert result.dry_lab_only is True


def test_dict_dry_lab_only_false_allowed():
    d = _valid_dict()
    d["dry_lab_only"] = False
    result = validate_negative_result_dict(d)
    assert result.passed
    assert result.dry_lab_only is False


def test_dict_candidate_count_populated():
    result = validate_negative_result_dict(_valid_dict())
    assert result.candidate_count == 2


def test_multiple_missing_fields():
    d = {}
    result = validate_negative_result_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


# --- constants ---

def test_valid_failure_categories_count():
    assert len(VALID_FAILURE_CATEGORIES) == 6


def test_valid_assay_types_count():
    assert len(VALID_ASSAY_TYPES) == 5


def test_max_failure_description_length_value():
    assert MAX_FAILURE_DESCRIPTION_LENGTH == 500


def test_max_hypothesis_impact_length_value():
    assert MAX_HYPOTHESIS_IMPACT_LENGTH == 300


def test_large_failure_set_threshold_value():
    assert LARGE_FAILURE_SET_THRESHOLD == 10


def test_recalibration_hint_value():
    assert RECALIBRATION_HINT == "calibrat"

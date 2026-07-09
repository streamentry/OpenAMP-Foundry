import math
import pytest
from openamp_foundry.evidence.pre_registration_form import (
    PreRegistrationEntry,
    PreRegistrationResult,
    validate_pre_registration,
    validate_pre_registration_dict,
    VALID_PRIMARY_OUTCOME_METRICS,
    VALID_ASSAY_TYPES,
    MAX_HYPOTHESIS_LENGTH,
    MIN_HYPOTHESIS_LENGTH,
    MAX_STATISTICAL_TEST_LENGTH,
    LARGE_CANDIDATE_SET_THRESHOLD,
    PLACEHOLDER_TEST_TOKENS,
    RANDOM_BASELINE_HINT,
)


def _valid_entry(**overrides) -> PreRegistrationEntry:
    base = dict(
        registration_id="PRE-001",
        batch_id="BATCH-001",
        pipeline_version="0.9.4",
        registration_date="2026-07-10",
        primary_hypothesis=(
            "Candidates selected by OpenAMP Foundry will show MIC values "
            "at least 2-fold lower than random peptides of matched length and charge, "
            "as measured by broth microdilution assay against E. coli ATCC 25922."
        ),
        primary_outcome_metric="mic_value",
        success_threshold=4.0,
        baseline_comparators=["random_selection", "charge_matched_random"],
        candidate_ids=["AMP-001", "AMP-002", "AMP-003"],
        assay_type="mic_assay",
        statistical_test="Mann-Whitney U test, two-sided, alpha=0.05",
        registered_by="researcher@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return PreRegistrationEntry(**base)


def _valid_dict(**overrides) -> dict:
    base = dict(
        registration_id="PRE-001",
        batch_id="BATCH-001",
        pipeline_version="0.9.4",
        registration_date="2026-07-10",
        primary_hypothesis=(
            "Candidates selected by OpenAMP Foundry will show MIC values "
            "at least 2-fold lower than random peptides of matched length and charge, "
            "as measured by broth microdilution assay against E. coli ATCC 25922."
        ),
        primary_outcome_metric="mic_value",
        success_threshold=4.0,
        baseline_comparators=["random_selection", "charge_matched_random"],
        candidate_ids=["AMP-001", "AMP-002", "AMP-003"],
        assay_type="mic_assay",
        statistical_test="Mann-Whitney U test, two-sided, alpha=0.05",
        registered_by="researcher@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return base


# --- Happy path ---

def test_valid_entry_passes():
    result = validate_pre_registration(_valid_entry())
    assert result.passed
    assert result.errors == []
    assert result.warnings == []


def test_result_dry_lab_only_always_true():
    result = validate_pre_registration(_valid_entry())
    assert result.dry_lab_only is True


def test_result_fields_populated():
    result = validate_pre_registration(_valid_entry())
    assert result.registration_id == "PRE-001"
    assert result.batch_id == "BATCH-001"
    assert result.primary_outcome_metric == "mic_value"
    assert result.candidate_count == 3


def test_all_outcome_metrics_valid():
    for metric in VALID_PRIMARY_OUTCOME_METRICS:
        result = validate_pre_registration(_valid_entry(primary_outcome_metric=metric))
        assert result.passed, f"metric={metric} should pass"


def test_all_assay_types_valid():
    for assay in VALID_ASSAY_TYPES:
        result = validate_pre_registration(_valid_entry(assay_type=assay))
        assert result.passed, f"assay_type={assay} should pass"


def test_negative_success_threshold_passes():
    result = validate_pre_registration(_valid_entry(success_threshold=-1.0))
    assert result.passed


def test_zero_success_threshold_passes():
    result = validate_pre_registration(_valid_entry(success_threshold=0.0))
    assert result.passed


# --- registration_id ---

def test_registration_id_must_start_with_pre():
    result = validate_pre_registration(_valid_entry(registration_id="REG-001"))
    assert not result.passed
    assert any("PRE-" in e for e in result.errors)


def test_registration_id_empty_fails():
    result = validate_pre_registration(_valid_entry(registration_id=""))
    assert not result.passed


def test_registration_id_pre_prefix_valid():
    result = validate_pre_registration(_valid_entry(registration_id="PRE-999"))
    assert result.passed


# --- primary_hypothesis ---

def test_empty_hypothesis_fails():
    result = validate_pre_registration(_valid_entry(primary_hypothesis=""))
    assert not result.passed
    assert any("primary_hypothesis" in e for e in result.errors)


def test_hypothesis_at_max_length_passes():
    h = "A" * MAX_HYPOTHESIS_LENGTH
    result = validate_pre_registration(_valid_entry(primary_hypothesis=h))
    assert result.passed


def test_hypothesis_over_max_fails():
    h = "A" * (MAX_HYPOTHESIS_LENGTH + 1)
    result = validate_pre_registration(_valid_entry(primary_hypothesis=h))
    assert not result.passed


def test_short_hypothesis_warns():
    h = "Short hypothesis."
    result = validate_pre_registration(_valid_entry(primary_hypothesis=h))
    assert result.passed
    assert any("underspecified" in w.lower() or "short" in w.lower() for w in result.warnings)


def test_hypothesis_at_min_length_no_warn():
    h = "A" * MIN_HYPOTHESIS_LENGTH
    result = validate_pre_registration(_valid_entry(primary_hypothesis=h))
    assert not any("underspecified" in w.lower() for w in result.warnings)


# --- primary_outcome_metric ---

def test_invalid_metric_fails():
    result = validate_pre_registration(_valid_entry(primary_outcome_metric="bad_metric"))
    assert not result.passed
    assert any("primary_outcome_metric" in e for e in result.errors)


def test_empty_metric_fails():
    result = validate_pre_registration(_valid_entry(primary_outcome_metric=""))
    assert not result.passed


# --- success_threshold ---

def test_nan_threshold_fails():
    result = validate_pre_registration(_valid_entry(success_threshold=float("nan")))
    assert not result.passed
    assert any("finite" in e for e in result.errors)


def test_inf_threshold_fails():
    result = validate_pre_registration(_valid_entry(success_threshold=float("inf")))
    assert not result.passed
    assert any("finite" in e for e in result.errors)


def test_negative_inf_threshold_fails():
    result = validate_pre_registration(_valid_entry(success_threshold=float("-inf")))
    assert not result.passed


# --- baseline_comparators ---

def test_empty_baseline_comparators_fails():
    result = validate_pre_registration(_valid_entry(baseline_comparators=[]))
    assert not result.passed
    assert any("baseline_comparators" in e for e in result.errors)


def test_no_random_baseline_warns():
    result = validate_pre_registration(
        _valid_entry(baseline_comparators=["charge_matched"])
    )
    assert result.passed
    assert any("random" in w.lower() for w in result.warnings)


def test_random_baseline_present_no_warn():
    result = validate_pre_registration(
        _valid_entry(baseline_comparators=["random_selection"])
    )
    assert not any("random" in w.lower() for w in result.warnings)


def test_random_in_uppercase_baseline_suppresses_warn():
    result = validate_pre_registration(
        _valid_entry(baseline_comparators=["RANDOM_baseline"])
    )
    assert not any("random" in w.lower() for w in result.warnings)


# --- candidate_ids ---

def test_empty_candidate_ids_fails():
    result = validate_pre_registration(_valid_entry(candidate_ids=[]))
    assert not result.passed
    assert any("candidate_ids" in e for e in result.errors)


def test_single_candidate_passes():
    result = validate_pre_registration(_valid_entry(candidate_ids=["AMP-001"]))
    assert result.passed


def test_large_candidate_set_warns():
    ids = [f"AMP-{i:03d}" for i in range(LARGE_CANDIDATE_SET_THRESHOLD + 1)]
    result = validate_pre_registration(_valid_entry(candidate_ids=ids))
    assert result.passed
    assert any("multiple-comparisons" in w.lower() or str(LARGE_CANDIDATE_SET_THRESHOLD) in w for w in result.warnings)


def test_candidate_count_at_threshold_no_warn():
    ids = [f"AMP-{i:03d}" for i in range(LARGE_CANDIDATE_SET_THRESHOLD)]
    result = validate_pre_registration(_valid_entry(candidate_ids=ids))
    assert not any("multiple-comparisons" in w.lower() for w in result.warnings)


# --- assay_type ---

def test_invalid_assay_type_fails():
    result = validate_pre_registration(_valid_entry(assay_type="blood_test"))
    assert not result.passed
    assert any("assay_type" in e for e in result.errors)


def test_empty_assay_type_fails():
    result = validate_pre_registration(_valid_entry(assay_type=""))
    assert not result.passed


# --- statistical_test ---

def test_empty_statistical_test_fails():
    result = validate_pre_registration(_valid_entry(statistical_test=""))
    assert not result.passed
    assert any("statistical_test" in e for e in result.errors)


def test_statistical_test_over_max_fails():
    result = validate_pre_registration(
        _valid_entry(statistical_test="A" * (MAX_STATISTICAL_TEST_LENGTH + 1))
    )
    assert not result.passed


def test_tbd_statistical_test_warns():
    result = validate_pre_registration(_valid_entry(statistical_test="TBD"))
    assert result.passed
    assert any("placeholder" in w.lower() for w in result.warnings)


def test_na_statistical_test_warns():
    result = validate_pre_registration(_valid_entry(statistical_test="N/A"))
    assert result.passed
    assert any("placeholder" in w.lower() for w in result.warnings)


def test_real_statistical_test_no_warn():
    result = validate_pre_registration(
        _valid_entry(statistical_test="Mann-Whitney U test, two-sided, alpha=0.05")
    )
    assert not any("placeholder" in w.lower() for w in result.warnings)


# --- registered_by ---

def test_empty_registered_by_fails():
    result = validate_pre_registration(_valid_entry(registered_by=""))
    assert not result.passed
    assert any("registered_by" in e for e in result.errors)


# --- dry_lab_only ---

def test_dry_lab_only_false_fails():
    result = validate_pre_registration(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# --- dict interface ---

def test_valid_dict_passes():
    result = validate_pre_registration_dict(_valid_dict())
    assert result.passed


def test_missing_registration_id_fails():
    d = _valid_dict()
    del d["registration_id"]
    result = validate_pre_registration_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


def test_missing_baseline_comparators_fails():
    d = _valid_dict()
    del d["baseline_comparators"]
    result = validate_pre_registration_dict(d)
    assert not result.passed


def test_missing_candidate_ids_fails():
    d = _valid_dict()
    del d["candidate_ids"]
    result = validate_pre_registration_dict(d)
    assert not result.passed


def test_dict_dry_lab_only_defaults_true():
    d = _valid_dict()
    del d["dry_lab_only"]
    result = validate_pre_registration_dict(d)
    assert result.passed
    assert result.dry_lab_only is True


def test_multiple_missing_fields():
    d = {}
    result = validate_pre_registration_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


def test_dict_candidate_count_populated():
    result = validate_pre_registration_dict(_valid_dict())
    assert result.candidate_count == 3


# --- constants ---

def test_valid_outcome_metrics_count():
    assert len(VALID_PRIMARY_OUTCOME_METRICS) == 6


def test_valid_assay_types_count():
    assert len(VALID_ASSAY_TYPES) == 5


def test_max_hypothesis_length_value():
    assert MAX_HYPOTHESIS_LENGTH == 500


def test_min_hypothesis_length_value():
    assert MIN_HYPOTHESIS_LENGTH == 50


def test_max_statistical_test_length_value():
    assert MAX_STATISTICAL_TEST_LENGTH == 200


def test_large_candidate_set_threshold_value():
    assert LARGE_CANDIDATE_SET_THRESHOLD == 20


def test_random_baseline_hint_value():
    assert RANDOM_BASELINE_HINT == "random"

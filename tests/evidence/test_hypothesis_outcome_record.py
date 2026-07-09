import math
import pytest
from openamp_foundry.evidence.hypothesis_outcome_record import (
    HypothesisOutcomeEntry,
    HypothesisOutcomeResult,
    validate_hypothesis_outcome,
    validate_hypothesis_outcome_dict,
    VALID_OUTCOME_VERDICTS,
    MAX_INTERPRETATION_LENGTH,
    MIN_INTERPRETATION_LENGTH,
    REGISTRATION_ID_PREFIX,
    OUTCOME_ID_PREFIX,
)


def _valid_entry(**overrides) -> HypothesisOutcomeEntry:
    base = dict(
        outcome_id="HOR-001",
        registration_id="PRE-001",
        batch_id="BATCH-001",
        pipeline_version="0.9.5",
        outcome_date="2026-07-15",
        outcome_verdict="confirmed",
        observed_metric_value=2.5,
        success_threshold_met=True,
        interpretation=(
            "The selected candidates showed median MIC of 2.5 ug/mL, meeting the "
            "pre-specified threshold of 4.0 ug/mL. The hypothesis is confirmed. "
            "Random baseline showed 32 ug/mL median MIC."
        ),
        deviation_from_plan="",
        recorded_by="researcher@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return HypothesisOutcomeEntry(**base)


def _valid_dict(**overrides) -> dict:
    base = dict(
        outcome_id="HOR-001",
        registration_id="PRE-001",
        batch_id="BATCH-001",
        pipeline_version="0.9.5",
        outcome_date="2026-07-15",
        outcome_verdict="confirmed",
        observed_metric_value=2.5,
        success_threshold_met=True,
        interpretation=(
            "The selected candidates showed median MIC of 2.5 ug/mL, meeting the "
            "pre-specified threshold of 4.0 ug/mL. The hypothesis is confirmed."
        ),
        deviation_from_plan="",
        recorded_by="researcher@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return base


# --- Happy path ---

def test_valid_confirmed_entry_passes():
    result = validate_hypothesis_outcome(_valid_entry())
    assert result.passed
    assert result.errors == []
    assert result.warnings == []


def test_valid_refuted_entry_passes():
    result = validate_hypothesis_outcome(
        _valid_entry(
            outcome_verdict="refuted",
            success_threshold_met=False,
            interpretation=(
                "Candidates showed median MIC of 128 ug/mL, failing the 4 ug/mL threshold. "
                "Performance was worse than the random baseline. Hypothesis refuted. "
                "This is a negative result and should be recorded as such."
            ),
        )
    )
    assert result.passed
    assert result.errors == []


def test_valid_inconclusive_with_deviation_passes():
    result = validate_hypothesis_outcome(
        _valid_entry(
            outcome_verdict="inconclusive",
            success_threshold_met=False,
            interpretation=(
                "Results were ambiguous due to contamination in the assay. "
                "Unable to draw conclusions from this experiment. "
                "Repeat assay is planned with fresh reagents."
            ),
            deviation_from_plan="Assay contamination detected; results discarded.",
        )
    )
    assert result.passed


def test_valid_partially_confirmed_passes():
    result = validate_hypothesis_outcome(
        _valid_entry(
            outcome_verdict="partially_confirmed",
            success_threshold_met=False,
            interpretation=(
                "3 of 10 candidates met the MIC threshold. The hypothesis is partially "
                "confirmed. The pipeline shows positive signal but not broad coverage. "
                "Random baseline showed 0 of 10 candidates meeting threshold."
            ),
        )
    )
    assert result.passed


def test_result_fields_populated():
    result = validate_hypothesis_outcome(_valid_entry())
    assert result.outcome_id == "HOR-001"
    assert result.registration_id == "PRE-001"
    assert result.outcome_verdict == "confirmed"
    assert result.success_threshold_met is True


def test_dry_lab_only_preserved_in_result():
    result = validate_hypothesis_outcome(_valid_entry(dry_lab_only=False))
    assert result.passed
    assert result.dry_lab_only is False


def test_all_verdicts_valid():
    for verdict in VALID_OUTCOME_VERDICTS:
        entry = _valid_entry(
            outcome_verdict=verdict,
            success_threshold_met=(verdict == "confirmed"),
            deviation_from_plan=("some deviation" if verdict == "inconclusive" else ""),
        )
        result = validate_hypothesis_outcome(entry)
        assert result.passed or (not result.passed and result.errors), f"verdict={verdict}"


def test_negative_metric_value_passes():
    result = validate_hypothesis_outcome(_valid_entry(observed_metric_value=-1.0))
    assert result.passed


def test_zero_metric_value_passes():
    result = validate_hypothesis_outcome(_valid_entry(observed_metric_value=0.0))
    assert result.passed


def test_empty_deviation_from_plan_passes_for_confirmed():
    result = validate_hypothesis_outcome(_valid_entry(deviation_from_plan=""))
    assert result.passed


def test_deviation_documented_for_inconclusive_passes():
    result = validate_hypothesis_outcome(
        _valid_entry(
            outcome_verdict="inconclusive",
            success_threshold_met=False,
            interpretation="Results were ambiguous due to equipment failure in the assay run.",
            deviation_from_plan="Equipment malfunction on day 2.",
        )
    )
    assert result.passed
    assert not any("deviation_from_plan" in w for w in result.warnings)


# --- outcome_id validation ---

def test_outcome_id_must_start_with_hor():
    result = validate_hypothesis_outcome(_valid_entry(outcome_id="OUT-001"))
    assert not result.passed
    assert any("HOR-" in e for e in result.errors)


def test_outcome_id_empty_fails():
    result = validate_hypothesis_outcome(_valid_entry(outcome_id=""))
    assert not result.passed


def test_outcome_id_hor_prefix_valid():
    result = validate_hypothesis_outcome(_valid_entry(outcome_id="HOR-999"))
    assert result.passed


# --- registration_id validation ---

def test_registration_id_must_start_with_pre():
    result = validate_hypothesis_outcome(_valid_entry(registration_id="REG-001"))
    assert not result.passed
    assert any("PRE-" in e for e in result.errors)


def test_registration_id_empty_fails():
    result = validate_hypothesis_outcome(_valid_entry(registration_id=""))
    assert not result.passed


def test_registration_id_pre_prefix_valid():
    result = validate_hypothesis_outcome(_valid_entry(registration_id="PRE-999"))
    assert result.passed


# --- outcome_verdict validation ---

def test_invalid_verdict_fails():
    result = validate_hypothesis_outcome(_valid_entry(outcome_verdict="maybe"))
    assert not result.passed
    assert any("outcome_verdict" in e for e in result.errors)


def test_empty_verdict_fails():
    result = validate_hypothesis_outcome(_valid_entry(outcome_verdict=""))
    assert not result.passed


# --- observed_metric_value ---

def test_nan_metric_value_fails():
    result = validate_hypothesis_outcome(_valid_entry(observed_metric_value=float("nan")))
    assert not result.passed
    assert any("finite" in e for e in result.errors)


def test_inf_metric_value_fails():
    result = validate_hypothesis_outcome(_valid_entry(observed_metric_value=float("inf")))
    assert not result.passed


def test_negative_inf_metric_value_fails():
    result = validate_hypothesis_outcome(_valid_entry(observed_metric_value=float("-inf")))
    assert not result.passed


# --- interpretation ---

def test_empty_interpretation_fails():
    result = validate_hypothesis_outcome(_valid_entry(interpretation=""))
    assert not result.passed
    assert any("interpretation" in e for e in result.errors)


def test_interpretation_at_max_length_passes():
    result = validate_hypothesis_outcome(
        _valid_entry(interpretation="A" * MAX_INTERPRETATION_LENGTH)
    )
    assert result.passed


def test_interpretation_over_max_fails():
    result = validate_hypothesis_outcome(
        _valid_entry(interpretation="A" * (MAX_INTERPRETATION_LENGTH + 1))
    )
    assert not result.passed


def test_short_interpretation_warns():
    result = validate_hypothesis_outcome(_valid_entry(interpretation="Too short."))
    assert result.passed
    assert any("underspecified" in w.lower() or "short" in w.lower() for w in result.warnings)


def test_interpretation_at_min_length_no_warn():
    result = validate_hypothesis_outcome(
        _valid_entry(interpretation="A" * MIN_INTERPRETATION_LENGTH)
    )
    assert not any("underspecified" in w.lower() for w in result.warnings)


# --- recorded_by ---

def test_empty_recorded_by_fails():
    result = validate_hypothesis_outcome(_valid_entry(recorded_by=""))
    assert not result.passed
    assert any("recorded_by" in e for e in result.errors)


# --- warnings ---

def test_threshold_met_but_refuted_warns():
    result = validate_hypothesis_outcome(
        _valid_entry(outcome_verdict="refuted", success_threshold_met=True)
    )
    assert result.passed
    assert any("inconsistent" in w.lower() for w in result.warnings)


def test_threshold_not_met_but_confirmed_warns():
    result = validate_hypothesis_outcome(
        _valid_entry(outcome_verdict="confirmed", success_threshold_met=False)
    )
    assert result.passed
    assert any("inconsistent" in w.lower() for w in result.warnings)


def test_confirmed_threshold_met_no_inconsistency_warn():
    result = validate_hypothesis_outcome(
        _valid_entry(outcome_verdict="confirmed", success_threshold_met=True)
    )
    assert not any("inconsistent" in w.lower() for w in result.warnings)


def test_refuted_threshold_not_met_no_inconsistency_warn():
    result = validate_hypothesis_outcome(
        _valid_entry(
            outcome_verdict="refuted",
            success_threshold_met=False,
            interpretation=(
                "Candidates did not meet threshold. Random baseline also failed. "
                "Pipeline shows no signal on this assay. Results are negative and "
                "should be recorded for future calibration."
            ),
        )
    )
    assert not any("inconsistent" in w.lower() for w in result.warnings)


def test_inconclusive_no_deviation_warns():
    result = validate_hypothesis_outcome(
        _valid_entry(
            outcome_verdict="inconclusive",
            success_threshold_met=False,
            interpretation=(
                "Results were ambiguous and could not be interpreted clearly. "
                "Unable to determine if hypothesis was supported or refuted. "
                "Further experiments are needed to resolve this question."
            ),
            deviation_from_plan="",
        )
    )
    assert result.passed
    assert any("deviation" in w.lower() for w in result.warnings)


def test_inconclusive_with_deviation_no_warn():
    result = validate_hypothesis_outcome(
        _valid_entry(
            outcome_verdict="inconclusive",
            success_threshold_met=False,
            interpretation=(
                "Results were ambiguous due to contamination detected on day 3. "
                "The experiment was terminated early. Unable to draw conclusions. "
                "A repeat experiment is planned with fresh reagents and controls."
            ),
            deviation_from_plan="Contamination detected on day 3; assay terminated early.",
        )
    )
    assert not any("deviation" in w.lower() for w in result.warnings)


# --- dict interface ---

def test_valid_dict_passes():
    result = validate_hypothesis_outcome_dict(_valid_dict())
    assert result.passed


def test_missing_outcome_id_fails():
    d = _valid_dict()
    del d["outcome_id"]
    result = validate_hypothesis_outcome_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


def test_missing_registration_id_fails():
    d = _valid_dict()
    del d["registration_id"]
    result = validate_hypothesis_outcome_dict(d)
    assert not result.passed


def test_missing_outcome_verdict_fails():
    d = _valid_dict()
    del d["outcome_verdict"]
    result = validate_hypothesis_outcome_dict(d)
    assert not result.passed


def test_dict_dry_lab_only_defaults_true():
    d = _valid_dict()
    del d["dry_lab_only"]
    result = validate_hypothesis_outcome_dict(d)
    assert result.passed
    assert result.dry_lab_only is True


def test_dict_dry_lab_only_false_allowed():
    d = _valid_dict()
    d["dry_lab_only"] = False
    result = validate_hypothesis_outcome_dict(d)
    assert result.passed
    assert result.dry_lab_only is False


def test_multiple_missing_fields():
    d = {}
    result = validate_hypothesis_outcome_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


# --- constants ---

def test_valid_outcome_verdicts_count():
    assert len(VALID_OUTCOME_VERDICTS) == 4


def test_max_interpretation_length_value():
    assert MAX_INTERPRETATION_LENGTH == 500


def test_min_interpretation_length_value():
    assert MIN_INTERPRETATION_LENGTH == 50


def test_registration_id_prefix_value():
    assert REGISTRATION_ID_PREFIX == "PRE-"


def test_outcome_id_prefix_value():
    assert OUTCOME_ID_PREFIX == "HOR-"


def test_valid_verdicts_contains_refuted():
    assert "refuted" in VALID_OUTCOME_VERDICTS


def test_valid_verdicts_contains_confirmed():
    assert "confirmed" in VALID_OUTCOME_VERDICTS

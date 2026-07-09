import math
import pytest
from openamp_foundry.evidence.baseline_comparison_manifest import (
    BaselineComparisonEntry,
    BaselineComparisonResult,
    validate_baseline_comparison,
    validate_baseline_comparison_dict,
    VALID_METRIC_NAMES,
    VALID_COMPARISON_DIRECTIONS,
    MAX_NOTES_LENGTH,
    P_VALUE_NOT_COMPUTED,
    LARGE_EFFECT_THRESHOLD,
)


def _valid_entry(**overrides) -> BaselineComparisonEntry:
    base = dict(
        manifest_id="BCM-001",
        batch_id="BATCH-001",
        pipeline_version="0.9.6",
        comparison_date="2026-07-10",
        metric_name="hit_rate",
        pipeline_score=0.7,
        baseline_scores={"random_selection": 0.1, "charge_matched": 0.15},
        pipeline_beats_all_baselines=True,
        effect_size=0.55,
        p_value=0.02,
        comparison_direction="higher_is_better",
        notes="Pipeline shows strong signal vs random and charge-matched baselines.",
        reviewer="reviewer@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return BaselineComparisonEntry(**base)


def _valid_dict(**overrides) -> dict:
    base = dict(
        manifest_id="BCM-001",
        batch_id="BATCH-001",
        pipeline_version="0.9.6",
        comparison_date="2026-07-10",
        metric_name="hit_rate",
        pipeline_score=0.7,
        baseline_scores={"random_selection": 0.1, "charge_matched": 0.15},
        pipeline_beats_all_baselines=True,
        effect_size=0.55,
        p_value=0.02,
        comparison_direction="higher_is_better",
        notes="Pipeline shows strong signal vs random and charge-matched baselines.",
        reviewer="reviewer@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return base


# --- Happy path ---

def test_valid_entry_passes():
    result = validate_baseline_comparison(_valid_entry())
    assert result.passed
    assert result.errors == []
    assert result.warnings == []


def test_result_dry_lab_only_always_true():
    result = validate_baseline_comparison(_valid_entry())
    assert result.dry_lab_only is True


def test_result_fields_populated():
    result = validate_baseline_comparison(_valid_entry())
    assert result.manifest_id == "BCM-001"
    assert result.batch_id == "BATCH-001"
    assert result.metric_name == "hit_rate"
    assert result.pipeline_beats_all_baselines is True
    assert result.baseline_count == 2


def test_all_metric_names_valid():
    for metric in VALID_METRIC_NAMES:
        result = validate_baseline_comparison(_valid_entry(metric_name=metric))
        assert result.passed, f"metric_name={metric} should pass"


def test_all_directions_valid():
    result_higher = validate_baseline_comparison(
        _valid_entry(comparison_direction="higher_is_better")
    )
    assert result_higher.passed

    result_lower = validate_baseline_comparison(
        _valid_entry(
            comparison_direction="lower_is_better",
            pipeline_score=2.0,
            baseline_scores={"random": 32.0, "charge_matched": 16.0},
        )
    )
    assert result_lower.passed


def test_p_value_zero_passes():
    result = validate_baseline_comparison(_valid_entry(p_value=0.0))
    assert result.passed


def test_p_value_one_passes():
    result = validate_baseline_comparison(_valid_entry(p_value=1.0))
    assert result.passed


def test_p_value_not_computed_passes_with_warning():
    result = validate_baseline_comparison(_valid_entry(p_value=P_VALUE_NOT_COMPUTED))
    assert result.passed
    assert any("p_value" in w for w in result.warnings)


def test_empty_notes_passes():
    result = validate_baseline_comparison(_valid_entry(notes=""))
    assert result.passed


def test_single_baseline_passes():
    result = validate_baseline_comparison(
        _valid_entry(baseline_scores={"random": 0.1})
    )
    assert result.passed


def test_negative_pipeline_score_passes():
    result = validate_baseline_comparison(
        _valid_entry(
            pipeline_score=-0.1,
            baseline_scores={"random": -0.5},
            comparison_direction="higher_is_better",
        )
    )
    assert result.passed


# --- manifest_id ---

def test_manifest_id_must_start_with_bcm():
    result = validate_baseline_comparison(_valid_entry(manifest_id="MAN-001"))
    assert not result.passed
    assert any("BCM-" in e for e in result.errors)


def test_manifest_id_empty_fails():
    result = validate_baseline_comparison(_valid_entry(manifest_id=""))
    assert not result.passed


def test_manifest_id_bcm_prefix_valid():
    result = validate_baseline_comparison(_valid_entry(manifest_id="BCM-999"))
    assert result.passed


# --- metric_name ---

def test_invalid_metric_name_fails():
    result = validate_baseline_comparison(_valid_entry(metric_name="fake_metric"))
    assert not result.passed
    assert any("metric_name" in e for e in result.errors)


def test_empty_metric_name_fails():
    result = validate_baseline_comparison(_valid_entry(metric_name=""))
    assert not result.passed


# --- pipeline_score ---

def test_nan_pipeline_score_fails():
    result = validate_baseline_comparison(_valid_entry(pipeline_score=float("nan")))
    assert not result.passed
    assert any("pipeline_score" in e for e in result.errors)


def test_inf_pipeline_score_fails():
    result = validate_baseline_comparison(_valid_entry(pipeline_score=float("inf")))
    assert not result.passed


# --- baseline_scores ---

def test_empty_baseline_scores_fails():
    result = validate_baseline_comparison(_valid_entry(baseline_scores={}))
    assert not result.passed
    assert any("baseline_scores" in e for e in result.errors)


def test_non_finite_baseline_score_fails():
    result = validate_baseline_comparison(
        _valid_entry(baseline_scores={"random": float("nan")})
    )
    assert not result.passed
    assert any("non-finite" in e for e in result.errors)


def test_inf_baseline_score_fails():
    result = validate_baseline_comparison(
        _valid_entry(baseline_scores={"random": float("inf")})
    )
    assert not result.passed


# --- effect_size ---

def test_nan_effect_size_fails():
    result = validate_baseline_comparison(_valid_entry(effect_size=float("nan")))
    assert not result.passed
    assert any("effect_size" in e for e in result.errors)


def test_inf_effect_size_fails():
    result = validate_baseline_comparison(_valid_entry(effect_size=float("inf")))
    assert not result.passed


def test_negative_effect_size_passes():
    result = validate_baseline_comparison(_valid_entry(effect_size=-2.5))
    assert result.passed


# --- p_value ---

def test_p_value_negative_not_sentinel_fails():
    result = validate_baseline_comparison(_valid_entry(p_value=-0.5))
    assert not result.passed
    assert any("p_value" in e for e in result.errors)


def test_p_value_over_one_fails():
    result = validate_baseline_comparison(_valid_entry(p_value=1.1))
    assert not result.passed


def test_p_value_sentinel_minus_one_passes():
    result = validate_baseline_comparison(_valid_entry(p_value=-1.0))
    assert result.passed


# --- comparison_direction ---

def test_invalid_direction_fails():
    result = validate_baseline_comparison(_valid_entry(comparison_direction="sideways"))
    assert not result.passed
    assert any("comparison_direction" in e for e in result.errors)


def test_empty_direction_fails():
    result = validate_baseline_comparison(_valid_entry(comparison_direction=""))
    assert not result.passed


# --- notes ---

def test_notes_at_max_length_passes():
    result = validate_baseline_comparison(_valid_entry(notes="A" * MAX_NOTES_LENGTH))
    assert result.passed


def test_notes_over_max_fails():
    result = validate_baseline_comparison(_valid_entry(notes="A" * (MAX_NOTES_LENGTH + 1)))
    assert not result.passed
    assert any("notes" in e for e in result.errors)


# --- reviewer ---

def test_empty_reviewer_fails():
    result = validate_baseline_comparison(_valid_entry(reviewer=""))
    assert not result.passed
    assert any("reviewer" in e for e in result.errors)


# --- dry_lab_only ---

def test_dry_lab_only_false_fails():
    result = validate_baseline_comparison(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# --- warnings ---

def test_pipeline_loses_warns():
    result = validate_baseline_comparison(
        _valid_entry(pipeline_beats_all_baselines=False)
    )
    assert result.passed
    assert any("underperforms" in w.lower() for w in result.warnings)


def test_pipeline_wins_no_loss_warning():
    result = validate_baseline_comparison(_valid_entry(pipeline_beats_all_baselines=True))
    assert not any("underperforms" in w.lower() for w in result.warnings)


def test_inconsistent_verdict_higher_is_better_warns():
    result = validate_baseline_comparison(
        _valid_entry(
            pipeline_score=0.05,
            baseline_scores={"random": 0.1},
            pipeline_beats_all_baselines=True,
            comparison_direction="higher_is_better",
        )
    )
    assert result.passed
    assert any("inconsistent" in w.lower() or "does not actually" in w.lower() for w in result.warnings)


def test_inconsistent_verdict_lower_is_better_warns():
    result = validate_baseline_comparison(
        _valid_entry(
            pipeline_score=32.0,
            baseline_scores={"random": 4.0},
            pipeline_beats_all_baselines=True,
            comparison_direction="lower_is_better",
        )
    )
    assert result.passed
    assert any("inconsistent" in w.lower() or "does not actually" in w.lower() for w in result.warnings)


def test_consistent_verdict_no_inconsistency_warn():
    result = validate_baseline_comparison(
        _valid_entry(
            pipeline_score=0.7,
            baseline_scores={"random": 0.1},
            pipeline_beats_all_baselines=True,
            comparison_direction="higher_is_better",
        )
    )
    assert not any("inconsistent" in w.lower() for w in result.warnings)


def test_large_effect_no_pvalue_warns():
    result = validate_baseline_comparison(
        _valid_entry(
            effect_size=15.0,
            p_value=P_VALUE_NOT_COMPUTED,
        )
    )
    assert result.passed
    assert any("large" in w.lower() for w in result.warnings)


def test_large_effect_with_pvalue_no_extra_warn():
    result = validate_baseline_comparison(
        _valid_entry(effect_size=15.0, p_value=0.001)
    )
    assert result.passed
    assert not any("large claimed" in w.lower() for w in result.warnings)


def test_small_effect_no_pvalue_only_pvalue_warn():
    result = validate_baseline_comparison(
        _valid_entry(effect_size=1.0, p_value=P_VALUE_NOT_COMPUTED)
    )
    assert result.passed
    assert any("p_value" in w for w in result.warnings)
    assert not any("large" in w.lower() for w in result.warnings)


# --- dict interface ---

def test_valid_dict_passes():
    result = validate_baseline_comparison_dict(_valid_dict())
    assert result.passed


def test_missing_manifest_id_fails():
    d = _valid_dict()
    del d["manifest_id"]
    result = validate_baseline_comparison_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


def test_missing_baseline_scores_fails():
    d = _valid_dict()
    del d["baseline_scores"]
    result = validate_baseline_comparison_dict(d)
    assert not result.passed


def test_missing_p_value_fails():
    d = _valid_dict()
    del d["p_value"]
    result = validate_baseline_comparison_dict(d)
    assert not result.passed


def test_dict_dry_lab_only_defaults_true():
    d = _valid_dict()
    del d["dry_lab_only"]
    result = validate_baseline_comparison_dict(d)
    assert result.passed
    assert result.dry_lab_only is True


def test_baseline_count_in_result():
    result = validate_baseline_comparison_dict(_valid_dict())
    assert result.baseline_count == 2


def test_multiple_missing_fields():
    d = {}
    result = validate_baseline_comparison_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


# --- constants ---

def test_valid_metric_names_count():
    assert len(VALID_METRIC_NAMES) == 6


def test_valid_comparison_directions_count():
    assert len(VALID_COMPARISON_DIRECTIONS) == 2


def test_max_notes_length_value():
    assert MAX_NOTES_LENGTH == 300


def test_p_value_not_computed_value():
    assert P_VALUE_NOT_COMPUTED == -1.0


def test_large_effect_threshold_value():
    assert LARGE_EFFECT_THRESHOLD == 10.0

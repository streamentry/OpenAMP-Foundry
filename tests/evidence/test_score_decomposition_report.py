import pytest
from openamp_foundry.evidence.score_decomposition_report import (
    ScoreDecompositionEntry,
    ScoreDecompositionResult,
    validate_score_decomposition,
    validate_score_decomposition_dict,
    VALID_SCORING_METHODS,
    MINIMUM_COMPONENTS,
    WEIGHT_SUM_TOLERANCE,
    DOMINANT_WEIGHT_THRESHOLD,
    UNBALANCED_RATIO_THRESHOLD,
    MAX_COMPONENTS_WARNING,
    LOW_SCORE_FRACTION,
)


def _valid_entry(**overrides) -> ScoreDecompositionEntry:
    base = dict(
        report_id="SDR-001",
        batch_id="BATCH-001",
        candidate_id="AMP-042",
        pipeline_version="0.9.1",
        composite_score=0.75,
        component_scores={"activity": 0.8, "safety": 0.7, "novelty": 0.75},
        component_weights={"activity": 0.5, "safety": 0.3, "novelty": 0.2},
        scoring_method="additive_weighted",
        score_range_min=0.0,
        score_range_max=1.0,
        reviewer="reviewer@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return ScoreDecompositionEntry(**base)


def _valid_dict(**overrides) -> dict:
    base = dict(
        report_id="SDR-001",
        batch_id="BATCH-001",
        candidate_id="AMP-042",
        pipeline_version="0.9.1",
        composite_score=0.75,
        component_scores={"activity": 0.8, "safety": 0.7, "novelty": 0.75},
        component_weights={"activity": 0.5, "safety": 0.3, "novelty": 0.2},
        scoring_method="additive_weighted",
        score_range_min=0.0,
        score_range_max=1.0,
        reviewer="reviewer@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return base


# --- Happy path ---

def test_valid_entry_passes():
    result = validate_score_decomposition(_valid_entry())
    assert result.passed
    assert result.errors == []
    assert result.warnings == []


def test_result_dry_lab_only_always_true():
    result = validate_score_decomposition(_valid_entry())
    assert result.dry_lab_only is True


def test_result_fields_populated():
    result = validate_score_decomposition(_valid_entry())
    assert result.report_id == "SDR-001"
    assert result.batch_id == "BATCH-001"
    assert result.candidate_id == "AMP-042"
    assert result.scoring_method == "additive_weighted"


def test_all_scoring_methods_valid():
    for method in VALID_SCORING_METHODS:
        result = validate_score_decomposition(_valid_entry(scoring_method=method))
        assert result.passed, f"scoring_method={method} should pass"


def test_exactly_two_components_passes():
    result = validate_score_decomposition(
        _valid_entry(
            component_scores={"a": 0.6, "b": 0.8},
            component_weights={"a": 0.5, "b": 0.5},
        )
    )
    assert result.passed


def test_composite_at_min_passes():
    result = validate_score_decomposition(_valid_entry(composite_score=0.0))
    assert result.passed


def test_composite_at_max_passes():
    result = validate_score_decomposition(_valid_entry(composite_score=1.0))
    assert result.passed


# --- report_id validation ---

def test_report_id_must_start_with_sdr():
    result = validate_score_decomposition(_valid_entry(report_id="RPT-001"))
    assert not result.passed
    assert any("SDR-" in e for e in result.errors)


def test_report_id_empty_fails():
    result = validate_score_decomposition(_valid_entry(report_id=""))
    assert not result.passed


def test_report_id_sdr_prefix_valid():
    result = validate_score_decomposition(_valid_entry(report_id="SDR-999"))
    assert result.passed


# --- score range validation ---

def test_score_range_min_equals_max_fails():
    result = validate_score_decomposition(
        _valid_entry(score_range_min=0.5, score_range_max=0.5)
    )
    assert not result.passed
    assert any("score_range_min" in e for e in result.errors)


def test_score_range_min_greater_than_max_fails():
    result = validate_score_decomposition(
        _valid_entry(score_range_min=1.0, score_range_max=0.0)
    )
    assert not result.passed


def test_composite_below_min_fails():
    result = validate_score_decomposition(
        _valid_entry(composite_score=-0.1, score_range_min=0.0, score_range_max=1.0)
    )
    assert not result.passed
    assert any("outside" in e for e in result.errors)


def test_composite_above_max_fails():
    result = validate_score_decomposition(
        _valid_entry(composite_score=1.1, score_range_min=0.0, score_range_max=1.0)
    )
    assert not result.passed


# --- component counts ---

def test_single_component_fails():
    result = validate_score_decomposition(
        _valid_entry(
            component_scores={"activity": 0.8},
            component_weights={"activity": 1.0},
        )
    )
    assert not result.passed
    assert any("at least" in e for e in result.errors)


def test_empty_components_fails():
    result = validate_score_decomposition(
        _valid_entry(component_scores={}, component_weights={})
    )
    assert not result.passed


def test_many_components_warns():
    scores = {f"comp_{i}": 0.5 for i in range(9)}
    weights = {k: 1.0 / 9 for k in scores}
    result = validate_score_decomposition(
        _valid_entry(component_scores=scores, component_weights=weights)
    )
    assert result.passed
    assert any("complex" in w.lower() or str(MAX_COMPONENTS_WARNING) in w for w in result.warnings)


# --- weight key matching ---

def test_weights_missing_key_fails():
    result = validate_score_decomposition(
        _valid_entry(
            component_scores={"activity": 0.8, "safety": 0.7},
            component_weights={"activity": 1.0},
        )
    )
    assert not result.passed
    assert any("missing" in e.lower() for e in result.errors)


def test_weights_extra_key_fails():
    result = validate_score_decomposition(
        _valid_entry(
            component_scores={"activity": 0.8, "safety": 0.7},
            component_weights={"activity": 0.5, "safety": 0.3, "extra": 0.2},
        )
    )
    assert not result.passed
    assert any("not in component_scores" in e for e in result.errors)


# --- weight sum validation ---

def test_weights_sum_to_one_passes():
    result = validate_score_decomposition(
        _valid_entry(
            component_scores={"a": 0.5, "b": 0.5},
            component_weights={"a": 0.5, "b": 0.5},
        )
    )
    assert result.passed


def test_weights_sum_to_0_992_passes():
    result = validate_score_decomposition(
        _valid_entry(
            component_scores={"a": 0.5, "b": 0.5},
            component_weights={"a": 0.496, "b": 0.496},
        )
    )
    assert result.passed


def test_weights_sum_to_0_98_fails():
    result = validate_score_decomposition(
        _valid_entry(
            component_scores={"a": 0.5, "b": 0.5},
            component_weights={"a": 0.49, "b": 0.49},
        )
    )
    assert not result.passed
    assert any("sum" in e for e in result.errors)


def test_weights_sum_over_1_01_fails():
    result = validate_score_decomposition(
        _valid_entry(
            component_scores={"a": 0.5, "b": 0.5},
            component_weights={"a": 0.51, "b": 0.51},
        )
    )
    assert not result.passed


# --- scoring method ---

def test_invalid_scoring_method_fails():
    result = validate_score_decomposition(_valid_entry(scoring_method="made_up_method"))
    assert not result.passed
    assert any("scoring_method" in e for e in result.errors)


def test_empty_scoring_method_fails():
    result = validate_score_decomposition(_valid_entry(scoring_method=""))
    assert not result.passed


# --- reviewer ---

def test_empty_reviewer_fails():
    result = validate_score_decomposition(_valid_entry(reviewer=""))
    assert not result.passed
    assert any("reviewer" in e for e in result.errors)


# --- dry_lab_only ---

def test_dry_lab_only_false_fails():
    result = validate_score_decomposition(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# --- warnings ---

def test_dominant_weight_warns():
    result = validate_score_decomposition(
        _valid_entry(
            component_scores={"activity": 0.8, "safety": 0.7},
            component_weights={"activity": 0.7, "safety": 0.3},
        )
    )
    assert result.passed
    assert any("dominated" in w.lower() or "dominant" in w.lower() or str(DOMINANT_WEIGHT_THRESHOLD) in w for w in result.warnings)


def test_unbalanced_weights_warn():
    result = validate_score_decomposition(
        _valid_entry(
            component_scores={"a": 0.5, "b": 0.5, "c": 0.5},
            component_weights={"a": 0.9, "b": 0.09, "c": 0.01},
        )
    )
    assert result.passed
    assert any("unbalanced" in w.lower() for w in result.warnings)


def test_low_score_warns():
    result = validate_score_decomposition(
        _valid_entry(composite_score=0.1, score_range_min=0.0, score_range_max=1.0)
    )
    assert result.passed
    assert any("weakly ranked" in w.lower() or "bottom" in w.lower() for w in result.warnings)


def test_score_above_low_threshold_no_low_warning():
    result = validate_score_decomposition(
        _valid_entry(composite_score=0.5, score_range_min=0.0, score_range_max=1.0)
    )
    assert not any("weakly ranked" in w.lower() for w in result.warnings)


# --- dict interface ---

def test_valid_dict_passes():
    result = validate_score_decomposition_dict(_valid_dict())
    assert result.passed


def test_missing_report_id_fails():
    d = _valid_dict()
    del d["report_id"]
    result = validate_score_decomposition_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


def test_missing_component_scores_fails():
    d = _valid_dict()
    del d["component_scores"]
    result = validate_score_decomposition_dict(d)
    assert not result.passed


def test_missing_reviewer_fails():
    d = _valid_dict()
    del d["reviewer"]
    result = validate_score_decomposition_dict(d)
    assert not result.passed


def test_dict_dry_lab_only_defaults_true():
    d = _valid_dict()
    del d["dry_lab_only"]
    result = validate_score_decomposition_dict(d)
    assert result.passed
    assert result.dry_lab_only is True


def test_multiple_missing_fields():
    d = {}
    result = validate_score_decomposition_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


# --- constants ---

def test_valid_scoring_methods_count():
    assert len(VALID_SCORING_METHODS) == 6


def test_minimum_components_value():
    assert MINIMUM_COMPONENTS == 2


def test_weight_sum_tolerance_value():
    assert WEIGHT_SUM_TOLERANCE == 0.01


def test_dominant_weight_threshold_value():
    assert DOMINANT_WEIGHT_THRESHOLD == 0.6


def test_unbalanced_ratio_threshold_value():
    assert UNBALANCED_RATIO_THRESHOLD == 5.0


def test_max_components_warning_value():
    assert MAX_COMPONENTS_WARNING == 8


def test_low_score_fraction_value():
    assert LOW_SCORE_FRACTION == 0.2


# --- Additional edge cases ---

def test_negative_score_range_min_passes():
    result = validate_score_decomposition(
        _valid_entry(score_range_min=-1.0, score_range_max=1.0, composite_score=0.0)
    )
    assert result.passed


def test_negative_composite_score_passes():
    result = validate_score_decomposition(
        _valid_entry(score_range_min=-1.0, score_range_max=1.0, composite_score=-0.5)
    )
    assert result.passed


def test_dict_missing_pipeline_version_fails():
    d = _valid_dict()
    del d["pipeline_version"]
    result = validate_score_decomposition_dict(d)
    assert not result.passed


def test_dict_missing_batch_id_fails():
    d = _valid_dict()
    del d["batch_id"]
    result = validate_score_decomposition_dict(d)
    assert not result.passed


def test_dict_empty_component_scores_fails():
    result = validate_score_decomposition_dict(_valid_dict(component_scores={}, component_weights={}))
    assert not result.passed


def test_result_fields_match():
    entry = _valid_entry(composite_score=0.5, scoring_method="harmonic_mean")
    result = validate_score_decomposition(entry)
    assert result.report_id == "SDR-001"
    assert result.scoring_method == "harmonic_mean"
    assert result.passed is True
    assert result.dry_lab_only is True


def test_dict_all_valid_methods():
    for method in VALID_SCORING_METHODS:
        d = _valid_dict(scoring_method=method)
        result = validate_score_decomposition_dict(d)
        assert result.passed, f"dict scoring_method={method} should pass"


def test_score_at_low_threshold_boundary_no_warning():
    result = validate_score_decomposition(
        _valid_entry(composite_score=0.2, score_range_min=0.0, score_range_max=1.0)
    )
    assert result.passed
    assert not any("weakly ranked" in w.lower() for w in result.warnings)


def test_no_warnings_on_balanced_weights():
    result = validate_score_decomposition(
        _valid_entry(
            component_scores={"a": 0.5, "b": 0.5},
            component_weights={"a": 0.5, "b": 0.5},
        )
    )
    assert result.passed
    assert len(result.warnings) == 0


def test_dict_float_conversion():
    d = _valid_dict(
        composite_score="0.75",
        component_scores={"a": "0.6", "b": "0.8"},
        component_weights={"a": "0.5", "b": "0.5"},
    )
    result = validate_score_decomposition_dict(d)
    assert result.passed

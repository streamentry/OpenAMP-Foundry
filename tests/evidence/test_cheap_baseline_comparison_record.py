"""Tests for CBR- cheap baseline comparison record schema."""

import pytest
from openamp_foundry.evidence.cheap_baseline_comparison_record import (
    CheapBaselineComparisonRecord,
    VALID_CBR_VERDICTS,
    VALID_BASELINE_METHODS,
    VALID_CBR_METRICS,
    SUPERIORITY_THRESHOLD,
    INFERIORITY_THRESHOLD,
    MIN_SAMPLE_SIZE,
    build_cheap_baseline_comparison_record,
    format_cheap_baseline_comparison_record,
    validate_cheap_baseline_comparison_record,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        cbr_id="CBR-001",
        pipeline_version="v1.0",
        baseline_method="charge_only_rank",
        metric_name="auroc",
        pipeline_metric_value=0.75,
        baseline_metric_value=0.60,
        n_candidates_evaluated=20,
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_cheap_baseline_comparison_record(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_cbr_verdicts_is_frozenset():
    assert isinstance(VALID_CBR_VERDICTS, frozenset)


def test_valid_cbr_verdicts_contains_pipeline_superior():
    assert "pipeline_superior" in VALID_CBR_VERDICTS


def test_valid_cbr_verdicts_contains_tied():
    assert "tied" in VALID_CBR_VERDICTS


def test_valid_cbr_verdicts_contains_baseline_superior():
    assert "baseline_superior" in VALID_CBR_VERDICTS


def test_valid_cbr_verdicts_contains_insufficient_data():
    assert "insufficient_data" in VALID_CBR_VERDICTS


def test_valid_baseline_methods_is_frozenset():
    assert isinstance(VALID_BASELINE_METHODS, frozenset)


def test_valid_baseline_methods_contains_charge_only():
    assert "charge_only_rank" in VALID_BASELINE_METHODS


def test_valid_baseline_methods_contains_length_only():
    assert "length_only_rank" in VALID_BASELINE_METHODS


def test_valid_baseline_methods_contains_random():
    assert "random_selection" in VALID_BASELINE_METHODS


def test_valid_cbr_metrics_is_frozenset():
    assert isinstance(VALID_CBR_METRICS, frozenset)


def test_valid_cbr_metrics_contains_auroc():
    assert "auroc" in VALID_CBR_METRICS


def test_valid_cbr_metrics_contains_hit_rate():
    assert "hit_rate" in VALID_CBR_METRICS


def test_superiority_threshold():
    assert SUPERIORITY_THRESHOLD == 0.05


def test_inferiority_threshold():
    assert INFERIORITY_THRESHOLD == -0.05


def test_min_sample_size():
    assert MIN_SAMPLE_SIZE == 5


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_cheap_baseline_comparison_record():
    assert isinstance(_build(), CheapBaselineComparisonRecord)


def test_build_cbr_id_stored():
    assert _build().cbr_id == "CBR-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_pipeline_superior_verdict():
    r = _build(pipeline_metric_value=0.75, baseline_metric_value=0.60)
    assert r.cbr_verdict == "pipeline_superior"


def test_build_baseline_superior_verdict():
    r = _build(pipeline_metric_value=0.50, baseline_metric_value=0.70)
    assert r.cbr_verdict == "baseline_superior"


def test_build_tied_verdict():
    r = _build(pipeline_metric_value=0.62, baseline_metric_value=0.60)
    assert r.cbr_verdict == "tied"


def test_build_insufficient_data_few_candidates():
    r = _build(n_candidates_evaluated=3)
    assert r.cbr_verdict == "insufficient_data"


def test_build_metric_delta_auto_computed():
    r = _build(pipeline_metric_value=0.75, baseline_metric_value=0.60)
    assert abs(r.metric_delta - 0.15) < 1e-5


def test_build_negative_delta():
    r = _build(pipeline_metric_value=0.50, baseline_metric_value=0.70)
    assert r.metric_delta < 0


def test_build_baseline_method_stored():
    assert _build().baseline_method == "charge_only_rank"


def test_build_metric_name_stored():
    assert _build().metric_name == "auroc"


def test_build_pipeline_metric_stored():
    assert abs(_build().pipeline_metric_value - 0.75) < 1e-6


def test_build_baseline_metric_stored():
    assert abs(_build().baseline_metric_value - 0.60) < 1e-6


def test_build_n_candidates_stored():
    assert _build().n_candidates_evaluated == 20


def test_build_pre_registered_threshold_default():
    assert abs(_build().pre_registered_threshold - SUPERIORITY_THRESHOLD) < 1e-6


def test_build_pre_registered_threshold_custom():
    r = _build(pre_registered_threshold=0.10)
    assert abs(r.pre_registered_threshold - 0.10) < 1e-6


def test_build_comparison_notes_stored():
    r = _build(comparison_notes="charge baseline used APD3")
    assert r.comparison_notes == "charge baseline used APD3"


def test_build_comparison_notes_default_empty():
    assert _build().comparison_notes == ""


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_pipeline_superior_at_exact_threshold():
    # delta == threshold → pipeline_superior (>= comparison)
    r = _build(pipeline_metric_value=0.65, baseline_metric_value=0.60)
    assert r.cbr_verdict == "pipeline_superior"


def test_build_pipeline_superior_just_over_threshold():
    r = _build(
        pipeline_metric_value=0.651,
        baseline_metric_value=0.60,
        pre_registered_threshold=0.05,
    )
    assert r.cbr_verdict == "pipeline_superior"


def test_build_random_selection_baseline():
    r = _build(baseline_method="random_selection")
    assert r.baseline_method == "random_selection"


def test_build_hit_rate_metric():
    r = _build(metric_name="hit_rate")
    assert r.metric_name == "hit_rate"


def test_build_five_candidates_is_not_insufficient():
    r = _build(n_candidates_evaluated=5)
    assert r.cbr_verdict != "insufficient_data"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_cbr_id_prefix():
    with pytest.raises(ValueError, match="CBR-"):
        _build(cbr_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_baseline_method():
    with pytest.raises(ValueError, match="baseline_method"):
        _build(baseline_method="UNKNOWN")


def test_validate_rejects_invalid_metric_name():
    with pytest.raises(ValueError, match="metric_name"):
        _build(metric_name="UNKNOWN")


def test_validate_rejects_pipeline_metric_above_one():
    with pytest.raises(ValueError, match="pipeline_metric_value"):
        _build(pipeline_metric_value=1.5)


def test_validate_rejects_pipeline_metric_below_zero():
    with pytest.raises(ValueError, match="pipeline_metric_value"):
        _build(pipeline_metric_value=-0.1)


def test_validate_rejects_baseline_metric_above_one():
    with pytest.raises(ValueError, match="baseline_metric_value"):
        _build(baseline_metric_value=1.5)


def test_validate_rejects_metric_delta_mismatch():
    cbr = _build()
    cbr.metric_delta = 99.0
    with pytest.raises(ValueError, match="metric_delta"):
        validate_cheap_baseline_comparison_record(cbr)


def test_validate_rejects_negative_n_candidates():
    with pytest.raises(ValueError, match="n_candidates_evaluated"):
        _build(n_candidates_evaluated=-1)


def test_validate_rejects_invalid_verdict():
    cbr = _build()
    cbr.cbr_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="cbr_verdict"):
        validate_cheap_baseline_comparison_record(cbr)


def test_validate_rejects_dry_lab_only_false():
    cbr = _build()
    cbr.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_cheap_baseline_comparison_record(cbr)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_cbr_id():
    assert "CBR-001" in format_cheap_baseline_comparison_record(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_cheap_baseline_comparison_record(_build())


def test_format_contains_baseline_method():
    assert "charge_only_rank" in format_cheap_baseline_comparison_record(_build())


def test_format_contains_metric_name():
    assert "auroc" in format_cheap_baseline_comparison_record(_build())


def test_format_contains_verdict():
    assert "pipeline_superior" in format_cheap_baseline_comparison_record(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_cheap_baseline_comparison_record(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_cheap_baseline_comparison_record(_build())


def test_format_is_string():
    assert isinstance(format_cheap_baseline_comparison_record(_build()), str)

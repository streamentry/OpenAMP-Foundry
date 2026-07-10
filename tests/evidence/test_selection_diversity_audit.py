"""Tests for SDA- selection diversity audit schema."""

import pytest
from openamp_foundry.evidence.selection_diversity_audit import (
    SelectionDiversityAudit,
    VALID_SDA_VERDICTS,
    VALID_DIVERSITY_METRICS,
    DIVERSE_PANEL_THRESHOLD,
    PROXIMITY_DRIVEN_THRESHOLD,
    MIN_PANEL_SIZE,
    build_selection_diversity_audit,
    format_selection_diversity_audit,
    validate_selection_diversity_audit,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        sda_id="SDA-001",
        pipeline_version="v1.0",
        diversity_metric="mean_pairwise_distance",
        n_selected=10,
        panel_diversity_score=0.70,
        random_baseline_diversity_score=0.55,
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_selection_diversity_audit(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_sda_verdicts_is_frozenset():
    assert isinstance(VALID_SDA_VERDICTS, frozenset)


def test_valid_sda_verdicts_contains_diverse_panel():
    assert "diverse_panel" in VALID_SDA_VERDICTS


def test_valid_sda_verdicts_contains_moderately_diverse():
    assert "moderately_diverse" in VALID_SDA_VERDICTS


def test_valid_sda_verdicts_contains_proximity_driven():
    assert "proximity_driven" in VALID_SDA_VERDICTS


def test_valid_sda_verdicts_contains_insufficient_data():
    assert "insufficient_data" in VALID_SDA_VERDICTS


def test_valid_diversity_metrics_is_frozenset():
    assert isinstance(VALID_DIVERSITY_METRICS, frozenset)


def test_valid_diversity_metrics_contains_mean_pairwise_identity():
    assert "mean_pairwise_identity" in VALID_DIVERSITY_METRICS


def test_valid_diversity_metrics_contains_mean_pairwise_distance():
    assert "mean_pairwise_distance" in VALID_DIVERSITY_METRICS


def test_diverse_panel_threshold():
    assert DIVERSE_PANEL_THRESHOLD == 0.10


def test_proximity_driven_threshold():
    assert PROXIMITY_DRIVEN_THRESHOLD == -0.05


def test_min_panel_size():
    assert MIN_PANEL_SIZE == 3


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_selection_diversity_audit():
    assert isinstance(_build(), SelectionDiversityAudit)


def test_build_sda_id_stored():
    assert _build().sda_id == "SDA-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_diverse_panel_verdict():
    r = _build(panel_diversity_score=0.70, random_baseline_diversity_score=0.55)
    assert r.sda_verdict == "diverse_panel"


def test_build_moderately_diverse_verdict():
    r = _build(panel_diversity_score=0.60, random_baseline_diversity_score=0.55)
    assert r.sda_verdict == "moderately_diverse"


def test_build_proximity_driven_verdict():
    r = _build(panel_diversity_score=0.40, random_baseline_diversity_score=0.50)
    assert r.sda_verdict == "proximity_driven"


def test_build_insufficient_data_small_panel():
    r = _build(n_selected=2)
    assert r.sda_verdict == "insufficient_data"


def test_build_diversity_delta_auto_computed():
    r = _build(panel_diversity_score=0.70, random_baseline_diversity_score=0.55)
    assert abs(r.diversity_delta - 0.15) < 1e-5


def test_build_negative_delta():
    r = _build(panel_diversity_score=0.40, random_baseline_diversity_score=0.50)
    assert r.diversity_delta < 0


def test_build_diversity_metric_stored():
    assert _build().diversity_metric == "mean_pairwise_distance"


def test_build_n_selected_stored():
    assert _build().n_selected == 10


def test_build_panel_score_stored():
    assert abs(_build().panel_diversity_score - 0.70) < 1e-6


def test_build_baseline_score_stored():
    assert abs(_build().random_baseline_diversity_score - 0.55) < 1e-6


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_three_candidates_is_not_insufficient():
    r = _build(n_selected=3)
    assert r.sda_verdict != "insufficient_data"


def test_build_mean_pairwise_identity_metric():
    r = _build(diversity_metric="mean_pairwise_identity")
    assert r.diversity_metric == "mean_pairwise_identity"


def test_build_diverse_panel_at_exact_threshold():
    # delta = 0.10 → diverse_panel (>= comparison)
    r = _build(panel_diversity_score=0.65, random_baseline_diversity_score=0.55)
    assert r.sda_verdict == "diverse_panel"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_sda_id_prefix():
    with pytest.raises(ValueError, match="SDA-"):
        _build(sda_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_diversity_metric():
    with pytest.raises(ValueError, match="diversity_metric"):
        _build(diversity_metric="UNKNOWN")


def test_validate_rejects_negative_n_selected():
    with pytest.raises(ValueError, match="n_selected"):
        _build(n_selected=-1)


def test_validate_rejects_diversity_delta_mismatch():
    sda = _build()
    sda.diversity_delta = 99.0
    with pytest.raises(ValueError, match="diversity_delta"):
        validate_selection_diversity_audit(sda)


def test_validate_rejects_invalid_sda_verdict():
    sda = _build()
    sda.sda_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="sda_verdict"):
        validate_selection_diversity_audit(sda)


def test_validate_rejects_dry_lab_only_false():
    sda = _build()
    sda.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_selection_diversity_audit(sda)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_sda_id():
    assert "SDA-001" in format_selection_diversity_audit(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_selection_diversity_audit(_build())


def test_format_contains_verdict():
    assert "diverse_panel" in format_selection_diversity_audit(_build())


def test_format_contains_metric():
    assert "mean_pairwise_distance" in format_selection_diversity_audit(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_selection_diversity_audit(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_selection_diversity_audit(_build())


def test_format_is_string():
    assert isinstance(format_selection_diversity_audit(_build()), str)

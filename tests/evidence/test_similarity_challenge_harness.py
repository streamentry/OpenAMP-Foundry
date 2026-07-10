"""Tests for SCH- similarity challenge harness schema."""

import pytest
from openamp_foundry.evidence.similarity_challenge_harness import (
    SimilarityChallengeHarness,
    SimilarityGroupStats,
    VALID_SCH_VERDICTS,
    VALID_SIMILARITY_METRICS,
    SELECTION_VALUE_GAP_THRESHOLD,
    MARGINAL_IMPROVEMENT_LOWER,
    build_similarity_challenge_harness,
    format_similarity_challenge_harness,
    validate_similarity_challenge_harness,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        sch_id="SCH-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        similarity_metric="sequence_identity",
        pipeline_mean_similarity=0.55,
        pipeline_n_sequences=50,
        random_mean_similarity=0.30,
        random_n_sequences=50,
        limitations=["dry-lab only", "similarity metric is approximate"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_similarity_challenge_harness(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_sch_verdicts_is_frozenset():
    assert isinstance(VALID_SCH_VERDICTS, frozenset)


def test_valid_sch_verdicts_contains_selection_adds_value():
    assert "selection_adds_value" in VALID_SCH_VERDICTS


def test_valid_sch_verdicts_contains_marginal_improvement():
    assert "marginal_improvement" in VALID_SCH_VERDICTS


def test_valid_sch_verdicts_contains_proximity_driven():
    assert "proximity_driven" in VALID_SCH_VERDICTS


def test_valid_sch_verdicts_contains_challenge_not_run():
    assert "challenge_not_run" in VALID_SCH_VERDICTS


def test_valid_similarity_metrics_is_frozenset():
    assert isinstance(VALID_SIMILARITY_METRICS, frozenset)


def test_valid_similarity_metrics_contains_sequence_identity():
    assert "sequence_identity" in VALID_SIMILARITY_METRICS


def test_valid_similarity_metrics_contains_blosum62():
    assert "blosum62_score" in VALID_SIMILARITY_METRICS


def test_valid_similarity_metrics_contains_edit_distance():
    assert "edit_distance" in VALID_SIMILARITY_METRICS


def test_valid_similarity_metrics_contains_physicochemical():
    assert "physicochemical_distance" in VALID_SIMILARITY_METRICS


def test_selection_value_gap_threshold():
    assert SELECTION_VALUE_GAP_THRESHOLD == 0.10


def test_marginal_improvement_lower():
    assert MARGINAL_IMPROVEMENT_LOWER == 0.03


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_similarity_challenge_harness():
    assert isinstance(_build(), SimilarityChallengeHarness)


def test_build_sch_id_stored():
    assert _build().sch_id == "SCH-001"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_similarity_metric_stored():
    assert _build().similarity_metric == "sequence_identity"


def test_build_pipeline_group_is_group_stats():
    assert isinstance(_build().pipeline_group, SimilarityGroupStats)


def test_build_random_group_is_group_stats():
    assert isinstance(_build().random_group, SimilarityGroupStats)


def test_build_pipeline_group_label():
    assert _build().pipeline_group.group_label == "pipeline_selected"


def test_build_random_group_label():
    assert _build().random_group.group_label == "random_draw"


def test_build_pipeline_mean_similarity_stored():
    assert abs(_build().pipeline_group.mean_similarity_to_known - 0.55) < 1e-9


def test_build_random_mean_similarity_stored():
    assert abs(_build().random_group.mean_similarity_to_known - 0.30) < 1e-9


def test_build_pipeline_n_sequences_stored():
    assert _build().pipeline_group.n_sequences == 50


def test_build_random_n_sequences_stored():
    assert _build().random_group.n_sequences == 50


def test_build_similarity_gap_computed():
    r = _build()
    assert abs(r.similarity_gap - (0.55 - 0.30)) < 1e-4


def test_build_selection_adds_value_verdict():
    r = _build(pipeline_mean_similarity=0.55, random_mean_similarity=0.30)
    assert r.sch_verdict == "selection_adds_value"


def test_build_marginal_improvement_verdict():
    r = _build(pipeline_mean_similarity=0.33, random_mean_similarity=0.30)
    assert r.sch_verdict == "marginal_improvement"


def test_build_proximity_driven_verdict():
    r = _build(pipeline_mean_similarity=0.30, random_mean_similarity=0.30)
    assert r.sch_verdict == "proximity_driven"


def test_build_challenge_not_run_when_pipeline_n_zero():
    r = _build(pipeline_n_sequences=0)
    assert r.sch_verdict == "challenge_not_run"


def test_build_challenge_not_run_when_random_n_zero():
    r = _build(random_n_sequences=0)
    assert r.sch_verdict == "challenge_not_run"


def test_build_proximity_driven_when_random_higher():
    r = _build(pipeline_mean_similarity=0.30, random_mean_similarity=0.35)
    assert r.sch_verdict == "proximity_driven"
    assert r.similarity_gap < 0


def test_build_blosum62_metric():
    r = _build(similarity_metric="blosum62_score")
    assert r.similarity_metric == "blosum62_score"


def test_build_edit_distance_metric():
    r = _build(similarity_metric="edit_distance")
    assert r.similarity_metric == "edit_distance"


def test_build_limitations_stored():
    assert "dry-lab only" in _build().limitations


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_sch_id_prefix():
    with pytest.raises(ValueError, match="SCH-"):
        _build(sch_id="BAD-001")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_similarity_metric():
    with pytest.raises(ValueError, match="VALID_SIMILARITY_METRICS"):
        _build(similarity_metric="UNKNOWN_METRIC")


def test_validate_rejects_pipeline_mean_above_one():
    with pytest.raises(ValueError, match="mean_similarity_to_known"):
        _build(pipeline_mean_similarity=1.1)


def test_validate_rejects_pipeline_mean_below_zero():
    with pytest.raises(ValueError, match="mean_similarity_to_known"):
        _build(pipeline_mean_similarity=-0.01)


def test_validate_rejects_random_mean_above_one():
    with pytest.raises(ValueError, match="mean_similarity_to_known"):
        _build(random_mean_similarity=1.1)


def test_validate_rejects_negative_pipeline_n():
    with pytest.raises(ValueError, match="n_sequences"):
        _build(pipeline_n_sequences=-1)


def test_validate_rejects_negative_random_n():
    with pytest.raises(ValueError, match="n_sequences"):
        _build(random_n_sequences=-1)


def test_validate_rejects_similarity_gap_mismatch():
    sch = _build()
    sch.similarity_gap = 0.999
    with pytest.raises(ValueError, match="similarity_gap"):
        validate_similarity_challenge_harness(sch)


def test_validate_rejects_invalid_verdict():
    sch = _build()
    sch.sch_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="sch_verdict"):
        validate_similarity_challenge_harness(sch)


def test_validate_rejects_dry_lab_only_false():
    sch = _build()
    sch.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_similarity_challenge_harness(sch)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_sch_id():
    assert "SCH-001" in format_similarity_challenge_harness(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_similarity_challenge_harness(_build())


def test_format_contains_similarity_metric():
    assert "sequence_identity" in format_similarity_challenge_harness(_build())


def test_format_contains_verdict():
    assert "selection_adds_value" in format_similarity_challenge_harness(_build())


def test_format_contains_pipeline_mean():
    assert "0.5500" in format_similarity_challenge_harness(_build())


def test_format_contains_random_mean():
    assert "0.3000" in format_similarity_challenge_harness(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_similarity_challenge_harness(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_similarity_challenge_harness(_build())


def test_format_is_string():
    assert isinstance(format_similarity_challenge_harness(_build()), str)

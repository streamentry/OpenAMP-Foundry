"""Tests for WEA- wet-lab evidence annotation schema."""

import pytest
from openamp_foundry.evidence.wetlab_evidence_annotation import (
    WetlabEvidenceAnnotation,
    VALID_PREDICTION_OUTCOMES,
    VALID_ACTIVITY_LABELS,
    INCONCLUSIVE_LABELS,
    build_wetlab_evidence_annotation,
    format_wetlab_evidence_annotation,
    validate_wetlab_evidence_annotation,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        wea_id="WEA-001",
        dry_lab_artifact_id="CERT-001",
        whr_id="WHR-001",
        pipeline_version="v1.0",
        dry_lab_predicted_activity="active",
        wetlab_observed_activity="active",
        is_preliminary_wet_lab=True,
        is_example_data=False,
        limitations=["single assay, preliminary wet-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_wetlab_evidence_annotation(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_prediction_outcomes_is_frozenset():
    assert isinstance(VALID_PREDICTION_OUTCOMES, frozenset)


def test_valid_prediction_outcomes_contains_confirmed():
    assert "prediction_confirmed" in VALID_PREDICTION_OUTCOMES


def test_valid_prediction_outcomes_contains_refuted():
    assert "prediction_refuted" in VALID_PREDICTION_OUTCOMES


def test_valid_prediction_outcomes_contains_inconclusive():
    assert "prediction_inconclusive" in VALID_PREDICTION_OUTCOMES


def test_valid_prediction_outcomes_contains_no_comparison():
    assert "no_wet_lab_comparison_possible" in VALID_PREDICTION_OUTCOMES


def test_valid_activity_labels_is_frozenset():
    assert isinstance(VALID_ACTIVITY_LABELS, frozenset)


def test_valid_activity_labels_contains_active():
    assert "active" in VALID_ACTIVITY_LABELS


def test_valid_activity_labels_contains_inactive():
    assert "inactive" in VALID_ACTIVITY_LABELS


def test_valid_activity_labels_contains_inconclusive():
    assert "inconclusive" in VALID_ACTIVITY_LABELS


def test_valid_activity_labels_contains_not_tested():
    assert "not_tested" in VALID_ACTIVITY_LABELS


def test_inconclusive_labels_is_frozenset():
    assert isinstance(INCONCLUSIVE_LABELS, frozenset)


def test_inconclusive_labels_contains_inconclusive():
    assert "inconclusive" in INCONCLUSIVE_LABELS


def test_inconclusive_labels_contains_not_tested():
    assert "not_tested" in INCONCLUSIVE_LABELS


# ---------------------------------------------------------------------------
# 2. build happy paths
# ---------------------------------------------------------------------------


def test_build_returns_wetlab_evidence_annotation():
    assert isinstance(_build(), WetlabEvidenceAnnotation)


def test_build_wea_id_stored():
    assert _build().wea_id == "WEA-001"


def test_build_dry_lab_artifact_id_stored():
    assert _build().dry_lab_artifact_id == "CERT-001"


def test_build_whr_id_stored():
    assert _build().whr_id == "WHR-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_active_active_gives_confirmed():
    r = _build(dry_lab_predicted_activity="active", wetlab_observed_activity="active")
    assert r.prediction_outcome == "prediction_confirmed"


def test_build_inactive_inactive_gives_confirmed():
    r = _build(dry_lab_predicted_activity="inactive", wetlab_observed_activity="inactive")
    assert r.prediction_outcome == "prediction_confirmed"


def test_build_active_inactive_gives_refuted():
    r = _build(dry_lab_predicted_activity="active", wetlab_observed_activity="inactive")
    assert r.prediction_outcome == "prediction_refuted"


def test_build_inactive_active_gives_refuted():
    r = _build(dry_lab_predicted_activity="inactive", wetlab_observed_activity="active")
    assert r.prediction_outcome == "prediction_refuted"


def test_build_active_inconclusive_gives_inconclusive():
    r = _build(dry_lab_predicted_activity="active", wetlab_observed_activity="inconclusive")
    assert r.prediction_outcome == "prediction_inconclusive"


def test_build_inconclusive_active_gives_inconclusive():
    r = _build(dry_lab_predicted_activity="inconclusive", wetlab_observed_activity="active")
    assert r.prediction_outcome == "prediction_inconclusive"


def test_build_not_tested_active_gives_inconclusive():
    r = _build(dry_lab_predicted_activity="not_tested", wetlab_observed_activity="active")
    assert r.prediction_outcome == "prediction_inconclusive"


def test_build_is_preliminary_wet_lab_default_true():
    assert _build().is_preliminary_wet_lab is True


def test_build_is_example_data_default_false():
    assert _build().is_example_data is False


def test_build_is_example_data_true():
    r = _build(is_example_data=True)
    assert r.is_example_data is True


def test_build_limitations_stored():
    assert "preliminary" in _build().limitations[0]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_predicted_activity_stored():
    assert _build().dry_lab_predicted_activity == "active"


def test_build_observed_activity_stored():
    assert _build().wetlab_observed_activity == "active"


# ---------------------------------------------------------------------------
# 3. validate rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_wea_id_prefix():
    with pytest.raises(ValueError, match="WEA-"):
        _build(wea_id="BAD-001")


def test_validate_rejects_empty_dry_lab_artifact_id():
    with pytest.raises(ValueError, match="dry_lab_artifact_id"):
        _build(dry_lab_artifact_id="")


def test_validate_rejects_bad_whr_id_prefix():
    with pytest.raises(ValueError, match="WHR-"):
        _build(whr_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_predicted_activity():
    with pytest.raises(ValueError, match="dry_lab_predicted_activity"):
        _build(dry_lab_predicted_activity="UNKNOWN")


def test_validate_rejects_invalid_observed_activity():
    with pytest.raises(ValueError, match="wetlab_observed_activity"):
        _build(wetlab_observed_activity="UNKNOWN")


def test_validate_rejects_invalid_prediction_outcome():
    wea = _build()
    wea.prediction_outcome = "UNKNOWN"
    with pytest.raises(ValueError, match="prediction_outcome"):
        validate_wetlab_evidence_annotation(wea)


def test_validate_rejects_prediction_outcome_mismatch():
    wea = _build(dry_lab_predicted_activity="active", wetlab_observed_activity="active")
    wea.prediction_outcome = "prediction_refuted"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_wetlab_evidence_annotation(wea)


def test_validate_rejects_dry_lab_only_false():
    wea = _build()
    wea.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_wetlab_evidence_annotation(wea)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_wea_id():
    assert "WEA-001" in format_wetlab_evidence_annotation(_build())


def test_format_contains_dry_lab_artifact_id():
    assert "CERT-001" in format_wetlab_evidence_annotation(_build())


def test_format_contains_whr_id():
    assert "WHR-001" in format_wetlab_evidence_annotation(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_wetlab_evidence_annotation(_build())


def test_format_contains_outcome():
    assert "prediction_confirmed" in format_wetlab_evidence_annotation(_build())


def test_format_contains_predicted_activity():
    assert "active" in format_wetlab_evidence_annotation(_build())


def test_format_contains_limitations():
    assert "preliminary" in format_wetlab_evidence_annotation(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_wetlab_evidence_annotation(_build())


def test_format_is_string():
    assert isinstance(format_wetlab_evidence_annotation(_build()), str)

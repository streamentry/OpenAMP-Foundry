"""Tests for LPR- learning progress report schema."""

import pytest
from openamp_foundry.evidence.learning_progress_report import (
    LearningProgressReport,
    FeatureLearningEntry,
    VALID_LPR_VERDICTS,
    VALID_FEATURE_PREDICTIVITY,
    VALID_FEATURE_CATEGORIES,
    build_learning_progress_report,
    format_learning_progress_report,
    validate_learning_progress_report,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PREDICTIVE_FEATURES = [
    {"feature_category": "charge", "predictivity": "predictive", "evidence_summary": "strong signal"},
    {"feature_category": "hydrophobicity", "predictivity": "predictive"},
    {"feature_category": "length", "predictivity": "not_predictive"},
]


def _build(**kwargs):
    defaults = dict(
        lpr_id="LPR-001",
        pipeline_version="v1.0",
        cit_id="CIT-001",
        n_batches_summarized=3,
        feature_entry_dicts=_PREDICTIVE_FEATURES,
        key_findings=["charge is the strongest predictor", "length not informative"],
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_learning_progress_report(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_lpr_verdicts_is_frozenset():
    assert isinstance(VALID_LPR_VERDICTS, frozenset)


def test_valid_lpr_verdicts_contains_learning_confirmed():
    assert "learning_confirmed" in VALID_LPR_VERDICTS


def test_valid_lpr_verdicts_contains_learning_inconclusive():
    assert "learning_inconclusive" in VALID_LPR_VERDICTS


def test_valid_lpr_verdicts_contains_no_learning_signal():
    assert "no_learning_signal" in VALID_LPR_VERDICTS


def test_valid_lpr_verdicts_contains_insufficient_data():
    assert "insufficient_data" in VALID_LPR_VERDICTS


def test_valid_feature_predictivity_is_frozenset():
    assert isinstance(VALID_FEATURE_PREDICTIVITY, frozenset)


def test_valid_feature_predictivity_contains_predictive():
    assert "predictive" in VALID_FEATURE_PREDICTIVITY


def test_valid_feature_predictivity_contains_not_predictive():
    assert "not_predictive" in VALID_FEATURE_PREDICTIVITY


def test_valid_feature_predictivity_contains_uncertain():
    assert "uncertain" in VALID_FEATURE_PREDICTIVITY


def test_valid_feature_categories_is_frozenset():
    assert isinstance(VALID_FEATURE_CATEGORIES, frozenset)


def test_valid_feature_categories_contains_charge():
    assert "charge" in VALID_FEATURE_CATEGORIES


def test_valid_feature_categories_contains_hydrophobicity():
    assert "hydrophobicity" in VALID_FEATURE_CATEGORIES


def test_valid_feature_categories_contains_length():
    assert "length" in VALID_FEATURE_CATEGORIES


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_learning_progress_report():
    assert isinstance(_build(), LearningProgressReport)


def test_build_lpr_id_stored():
    assert _build().lpr_id == "LPR-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_cit_id_stored():
    assert _build().cit_id == "CIT-001"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_n_batches_summarized_stored():
    assert _build().n_batches_summarized == 3


def test_build_n_predictive_features_counted():
    assert _build().n_predictive_features == 2


def test_build_n_non_predictive_features_counted():
    assert _build().n_non_predictive_features == 1


def test_build_learning_confirmed_when_more_predictive():
    assert _build().lpr_verdict == "learning_confirmed"


def test_build_no_learning_signal_when_more_non_predictive():
    features = [
        {"feature_category": "charge", "predictivity": "not_predictive"},
        {"feature_category": "hydrophobicity", "predictivity": "not_predictive"},
        {"feature_category": "length", "predictivity": "predictive"},
    ]
    r = _build(feature_entry_dicts=features)
    assert r.lpr_verdict == "no_learning_signal"


def test_build_learning_inconclusive_when_equal():
    features = [
        {"feature_category": "charge", "predictivity": "predictive"},
        {"feature_category": "length", "predictivity": "not_predictive"},
    ]
    r = _build(feature_entry_dicts=features)
    assert r.lpr_verdict == "learning_inconclusive"


def test_build_insufficient_data_when_n_batches_zero():
    r = _build(n_batches_summarized=0)
    assert r.lpr_verdict == "insufficient_data"


def test_build_insufficient_data_when_no_features():
    r = _build(feature_entry_dicts=[])
    assert r.lpr_verdict == "insufficient_data"


def test_build_feature_entries_are_feature_learning_entry():
    for e in _build().feature_entries:
        assert isinstance(e, FeatureLearningEntry)


def test_build_evidence_summary_stored():
    r = _build()
    assert r.feature_entries[0].evidence_summary == "strong signal"


def test_build_evidence_summary_defaults_empty():
    r = _build()
    assert r.feature_entries[1].evidence_summary == ""


def test_build_key_findings_stored():
    assert len(_build().key_findings) == 2


def test_build_all_features_uncertain_gives_insufficient():
    features = [
        {"feature_category": "charge", "predictivity": "uncertain"},
        {"feature_category": "length", "predictivity": "uncertain"},
    ]
    r = _build(feature_entry_dicts=features)
    assert r.lpr_verdict == "insufficient_data"


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_amphipathicity_feature():
    features = [{"feature_category": "amphipathicity", "predictivity": "predictive"}]
    r = _build(feature_entry_dicts=features)
    assert r.feature_entries[0].feature_category == "amphipathicity"


def test_build_helicity_feature():
    features = [{"feature_category": "helicity", "predictivity": "uncertain"}]
    r = _build(feature_entry_dicts=features)
    assert r.feature_entries[0].feature_category == "helicity"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_lpr_id_prefix():
    with pytest.raises(ValueError, match="LPR-"):
        _build(lpr_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_bad_cit_id_prefix():
    with pytest.raises(ValueError, match="CIT-"):
        _build(cit_id="BAD-001")


def test_validate_rejects_negative_n_batches():
    lpr = _build()
    lpr.n_batches_summarized = -1
    with pytest.raises(ValueError, match="n_batches_summarized"):
        validate_learning_progress_report(lpr)


def test_validate_rejects_invalid_feature_category():
    features = [{"feature_category": "UNKNOWN", "predictivity": "predictive"}]
    with pytest.raises(ValueError, match="feature_category"):
        _build(feature_entry_dicts=features)


def test_validate_rejects_invalid_predictivity():
    features = [{"feature_category": "charge", "predictivity": "UNKNOWN"}]
    with pytest.raises(ValueError, match="predictivity"):
        _build(feature_entry_dicts=features)


def test_validate_rejects_n_predictive_mismatch():
    lpr = _build()
    lpr.n_predictive_features = 99
    with pytest.raises(ValueError, match="n_predictive_features"):
        validate_learning_progress_report(lpr)


def test_validate_rejects_n_non_predictive_mismatch():
    lpr = _build()
    lpr.n_non_predictive_features = 99
    with pytest.raises(ValueError, match="n_non_predictive_features"):
        validate_learning_progress_report(lpr)


def test_validate_rejects_invalid_lpr_verdict():
    lpr = _build()
    lpr.lpr_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="lpr_verdict"):
        validate_learning_progress_report(lpr)


def test_validate_rejects_empty_key_findings():
    with pytest.raises(ValueError, match="key_findings"):
        _build(key_findings=[])


def test_validate_rejects_dry_lab_only_false():
    lpr = _build()
    lpr.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_learning_progress_report(lpr)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_lpr_id():
    assert "LPR-001" in format_learning_progress_report(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_learning_progress_report(_build())


def test_format_contains_cit_id():
    assert "CIT-001" in format_learning_progress_report(_build())


def test_format_contains_verdict():
    assert "learning_confirmed" in format_learning_progress_report(_build())


def test_format_contains_key_finding():
    assert "charge is the strongest predictor" in format_learning_progress_report(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_learning_progress_report(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_learning_progress_report(_build())


def test_format_is_string():
    assert isinstance(format_learning_progress_report(_build()), str)

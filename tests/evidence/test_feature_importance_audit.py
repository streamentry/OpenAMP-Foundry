"""Tests for FIA- feature importance audit schema."""

import pytest
from openamp_foundry.evidence.feature_importance_audit import (
    FeatureImportanceAudit,
    FeatureImportanceEntry,
    VALID_FIA_VERDICTS,
    VALID_FEATURE_IMPORTANCE_LEVELS,
    VALID_AUDIT_FEATURES,
    DOMINATION_THRESHOLD,
    MIN_FEATURES_FOR_AUDIT,
    build_feature_importance_audit,
    format_feature_importance_audit,
    validate_feature_importance_audit,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MULTI_FEATURES = [
    {"feature_name": "charge", "importance_score": 0.30},
    {"feature_name": "hydrophobicity", "importance_score": 0.25},
    {"feature_name": "length", "importance_score": 0.20},
    {"feature_name": "amphipathicity", "importance_score": 0.25},
]

_CHARGE_DOMINATED = [
    {"feature_name": "charge", "importance_score": 0.85},
    {"feature_name": "length", "importance_score": 0.15},
]


def _build(**kwargs):
    defaults = dict(
        fia_id="FIA-001",
        pipeline_version="v1.0",
        feature_importance_dicts=_MULTI_FEATURES,
        charge_explains_fraction=0.40,
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_feature_importance_audit(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_fia_verdicts_is_frozenset():
    assert isinstance(VALID_FIA_VERDICTS, frozenset)


def test_valid_fia_verdicts_contains_multi_feature_signal():
    assert "multi_feature_signal" in VALID_FIA_VERDICTS


def test_valid_fia_verdicts_contains_charge_dominated():
    assert "charge_dominated" in VALID_FIA_VERDICTS


def test_valid_fia_verdicts_contains_length_dominated():
    assert "length_dominated" in VALID_FIA_VERDICTS


def test_valid_fia_verdicts_contains_insufficient_data():
    assert "insufficient_data" in VALID_FIA_VERDICTS


def test_valid_feature_importance_levels_is_frozenset():
    assert isinstance(VALID_FEATURE_IMPORTANCE_LEVELS, frozenset)


def test_valid_feature_importance_levels_contains_high():
    assert "high" in VALID_FEATURE_IMPORTANCE_LEVELS


def test_valid_feature_importance_levels_contains_negligible():
    assert "negligible" in VALID_FEATURE_IMPORTANCE_LEVELS


def test_valid_audit_features_is_frozenset():
    assert isinstance(VALID_AUDIT_FEATURES, frozenset)


def test_valid_audit_features_contains_charge():
    assert "charge" in VALID_AUDIT_FEATURES


def test_valid_audit_features_contains_hydrophobicity():
    assert "hydrophobicity" in VALID_AUDIT_FEATURES


def test_domination_threshold():
    assert DOMINATION_THRESHOLD == 0.80


def test_min_features_for_audit():
    assert MIN_FEATURES_FOR_AUDIT == 2


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_feature_importance_audit():
    assert isinstance(_build(), FeatureImportanceAudit)


def test_build_fia_id_stored():
    assert _build().fia_id == "FIA-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_multi_feature_verdict():
    r = _build(feature_importance_dicts=_MULTI_FEATURES, charge_explains_fraction=0.40)
    assert r.fia_verdict == "multi_feature_signal"


def test_build_charge_dominated_verdict():
    r = _build(
        feature_importance_dicts=_CHARGE_DOMINATED,
        charge_explains_fraction=0.90,
    )
    assert r.fia_verdict == "charge_dominated"


def test_build_length_dominated_verdict():
    features = [
        {"feature_name": "length", "importance_score": 0.70},
        {"feature_name": "charge", "importance_score": 0.30},
    ]
    r = _build(feature_importance_dicts=features, charge_explains_fraction=0.30)
    assert r.fia_verdict == "length_dominated"


def test_build_insufficient_data_one_feature():
    features = [{"feature_name": "charge", "importance_score": 0.80}]
    r = _build(feature_importance_dicts=features, charge_explains_fraction=0.90)
    assert r.fia_verdict == "insufficient_data"


def test_build_insufficient_data_empty():
    r = _build(feature_importance_dicts=[], charge_explains_fraction=0.0)
    assert r.fia_verdict == "insufficient_data"


def test_build_feature_entries_are_entry_objects():
    for e in _build().feature_entries:
        assert isinstance(e, FeatureImportanceEntry)


def test_build_top_feature_identified():
    r = _build(feature_importance_dicts=_MULTI_FEATURES, charge_explains_fraction=0.40)
    assert r.top_feature == "charge"


def test_build_charge_score_extracted():
    r = _build(feature_importance_dicts=_MULTI_FEATURES)
    assert abs(r.charge_importance_score - 0.30) < 1e-6


def test_build_length_score_extracted():
    r = _build(feature_importance_dicts=_MULTI_FEATURES)
    assert abs(r.length_importance_score - 0.20) < 1e-6


def test_build_charge_explains_fraction_stored():
    r = _build(charge_explains_fraction=0.55)
    assert abs(r.charge_explains_fraction - 0.55) < 1e-6


def test_build_importance_level_auto_assigned_high():
    features = [
        {"feature_name": "charge", "importance_score": 0.60},
        {"feature_name": "length", "importance_score": 0.10},
    ]
    r = _build(feature_importance_dicts=features)
    charge_entry = next(e for e in r.feature_entries if e.feature_name == "charge")
    assert charge_entry.importance_level == "high"


def test_build_importance_level_auto_assigned_negligible():
    features = [
        {"feature_name": "charge", "importance_score": 0.02},
        {"feature_name": "length", "importance_score": 0.01},
    ]
    r = _build(feature_importance_dicts=features)
    charge_entry = next(e for e in r.feature_entries if e.feature_name == "charge")
    assert charge_entry.importance_level == "negligible"


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_no_charge_entry_gives_zero_charge_score():
    features = [
        {"feature_name": "length", "importance_score": 0.60},
        {"feature_name": "amphipathicity", "importance_score": 0.40},
    ]
    r = _build(feature_importance_dicts=features, charge_explains_fraction=0.10)
    assert r.charge_importance_score == 0.0


def test_build_hydrophobicity_dominated_verdict():
    features = [
        {"feature_name": "hydrophobicity", "importance_score": 0.80},
        {"feature_name": "length", "importance_score": 0.20},
    ]
    r = _build(feature_importance_dicts=features, charge_explains_fraction=0.10)
    assert r.fia_verdict == "hydrophobicity_dominated"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_fia_id_prefix():
    with pytest.raises(ValueError, match="FIA-"):
        _build(fia_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_feature_name():
    features = [{"feature_name": "UNKNOWN", "importance_score": 0.5}]
    with pytest.raises(ValueError, match="feature_name"):
        _build(feature_importance_dicts=features)


def test_validate_rejects_importance_score_above_one():
    features = [
        {"feature_name": "charge", "importance_score": 1.5},
        {"feature_name": "length", "importance_score": 0.5},
    ]
    with pytest.raises(ValueError, match="importance_score"):
        _build(feature_importance_dicts=features)


def test_validate_rejects_importance_score_below_zero():
    features = [
        {"feature_name": "charge", "importance_score": -0.1},
        {"feature_name": "length", "importance_score": 0.5},
    ]
    with pytest.raises(ValueError, match="importance_score"):
        _build(feature_importance_dicts=features)


def test_validate_rejects_charge_explains_fraction_above_one():
    with pytest.raises(ValueError, match="charge_explains_fraction"):
        _build(charge_explains_fraction=1.5)


def test_validate_rejects_invalid_fia_verdict():
    fia = _build()
    fia.fia_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="fia_verdict"):
        validate_feature_importance_audit(fia)


def test_validate_rejects_dry_lab_only_false():
    fia = _build()
    fia.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_feature_importance_audit(fia)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_fia_id():
    assert "FIA-001" in format_feature_importance_audit(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_feature_importance_audit(_build())


def test_format_contains_verdict():
    assert "multi_feature_signal" in format_feature_importance_audit(_build())


def test_format_contains_top_feature():
    assert "charge" in format_feature_importance_audit(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_feature_importance_audit(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_feature_importance_audit(_build())


def test_format_is_string():
    assert isinstance(format_feature_importance_audit(_build()), str)

"""Tests for FBH- family blindness challenge harness schema."""

import pytest
from openamp_foundry.evidence.family_blindness_challenge import (
    FamilyBlingnessChallenge,
    FamilyPerformanceEntry,
    VALID_FBH_VERDICTS,
    VALID_AUROC_GRADES,
    WEAK_FAMILY_AUROC_THRESHOLD,
    WEAK_FAMILY_PANEL_FLOOR,
    build_family_blindness_challenge,
    format_family_blindness_challenge,
    validate_family_blindness_challenge,
)

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

_ALL_REPRESENTED = [
    {"family_name": "defensin", "auroc": 0.85, "n_candidates": 100, "panel_count": 30},
    {"family_name": "cathelicidin", "auroc": 0.72, "n_candidates": 50, "panel_count": 15},
]

_WEAK_EXCLUDED = [
    {"family_name": "defensin", "auroc": 0.85, "n_candidates": 100, "panel_count": 30},
    {"family_name": "cathelicidin", "auroc": 0.72, "n_candidates": 50, "panel_count": 15},
    {"family_name": "bacteriocin", "auroc": 0.45, "n_candidates": 20, "panel_count": 1},
]

_WEAK_NOT_EXCLUDED = [
    {"family_name": "defensin", "auroc": 0.85, "n_candidates": 100, "panel_count": 30},
    {"family_name": "cathelicidin", "auroc": 0.72, "n_candidates": 50, "panel_count": 15},
    {"family_name": "bacteriocin", "auroc": 0.50, "n_candidates": 10, "panel_count": 3},
]


def _build(**kwargs):
    defaults = dict(
        fbh_id="FBH-001",
        pipeline_version="v1.0",
        family_entry_dicts=_ALL_REPRESENTED,
        limitations=["dry-lab only", "AUROC estimates are approximate"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_family_blindness_challenge(**defaults)


# ---------------------------------------------------------------------------
# Section 1: Constants
# ---------------------------------------------------------------------------


def test_valid_fbh_verdicts_is_frozenset():
    assert isinstance(VALID_FBH_VERDICTS, frozenset)


def test_valid_fbh_verdicts_contains_all_families_represented():
    assert "all_families_represented" in VALID_FBH_VERDICTS


def test_valid_fbh_verdicts_contains_weak_family_excluded():
    assert "weak_family_excluded" in VALID_FBH_VERDICTS


def test_valid_fbh_verdicts_contains_insufficient_data():
    assert "insufficient_data" in VALID_FBH_VERDICTS


def test_valid_auroc_grades_is_frozenset():
    assert isinstance(VALID_AUROC_GRADES, frozenset)


def test_valid_auroc_grades_contains_strong():
    assert "strong" in VALID_AUROC_GRADES


def test_valid_auroc_grades_contains_adequate():
    assert "adequate" in VALID_AUROC_GRADES


def test_valid_auroc_grades_contains_weak():
    assert "weak" in VALID_AUROC_GRADES


def test_valid_auroc_grades_contains_not_evaluated():
    assert "not_evaluated" in VALID_AUROC_GRADES


def test_weak_family_auroc_threshold():
    assert WEAK_FAMILY_AUROC_THRESHOLD == 0.55


def test_weak_family_panel_floor():
    assert WEAK_FAMILY_PANEL_FLOOR == 0.10


# ---------------------------------------------------------------------------
# Section 2: build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_fbh():
    assert isinstance(_build(), FamilyBlingnessChallenge)


def test_build_fbh_id_stored():
    assert _build().fbh_id == "FBH-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_all_families_represented_verdict():
    r = _build(family_entry_dicts=_ALL_REPRESENTED)
    assert r.verdict == "all_families_represented"


def test_build_n_families_total_auto_computed():
    r = _build(family_entry_dicts=_ALL_REPRESENTED)
    assert r.n_families_total == 2


def test_build_n_weak_families_zero_when_all_strong():
    r = _build(family_entry_dicts=_ALL_REPRESENTED)
    assert r.n_weak_families == 0


def test_build_weak_family_excluded_verdict():
    r = _build(family_entry_dicts=_WEAK_EXCLUDED)
    assert r.verdict == "weak_family_excluded"


def test_build_weak_family_excluded_counts_and_names():
    r = _build(family_entry_dicts=_WEAK_EXCLUDED)
    assert r.n_weak_families == 1
    assert r.n_excluded_weak_families == 1
    assert r.excluded_weak_family_names == ["bacteriocin"]


def test_build_insufficient_data_verdict():
    r = _build(family_entry_dicts=[])
    assert r.verdict == "insufficient_data"


def test_build_panel_fraction_auto_computed():
    r = _build(family_entry_dicts=_ALL_REPRESENTED)
    assert abs(r.family_entries[0].panel_fraction - 0.30) < 1e-4
    assert abs(r.family_entries[1].panel_fraction - 0.30) < 1e-4


def test_build_auroc_grade_strong():
    r = _build(family_entry_dicts=_ALL_REPRESENTED)
    assert r.family_entries[0].auroc_grade == "strong"
    assert r.family_entries[1].auroc_grade == "strong"


def test_build_auroc_grade_adequate():
    entries = [
        {"family_name": "test", "auroc": 0.60, "n_candidates": 10, "panel_count": 3},
    ]
    r = _build(family_entry_dicts=entries)
    assert r.family_entries[0].auroc_grade == "adequate"


def test_build_auroc_grade_weak():
    entries = [
        {"family_name": "test", "auroc": 0.45, "n_candidates": 10, "panel_count": 3},
    ]
    r = _build(family_entry_dicts=entries)
    assert r.family_entries[0].auroc_grade == "weak"


def test_build_auroc_grade_not_evaluated():
    entries = [
        {"family_name": "test", "auroc": -1.0, "n_candidates": 10, "panel_count": 0},
    ]
    r = _build(family_entry_dicts=entries)
    assert r.family_entries[0].auroc_grade == "not_evaluated"


def test_build_is_weak_class_true():
    entries = [
        {"family_name": "test", "auroc": 0.50, "n_candidates": 5, "panel_count": 1},
    ]
    r = _build(family_entry_dicts=entries)
    assert r.family_entries[0].is_weak_class is True


def test_build_is_weak_class_false_not_enough_candidates():
    entries = [
        {"family_name": "test", "auroc": 0.50, "n_candidates": 2, "panel_count": 0},
    ]
    r = _build(family_entry_dicts=entries)
    assert r.family_entries[0].is_weak_class is False


def test_build_limitations_and_created_at_stored():
    r = _build()
    assert "dry-lab only" in r.limitations
    assert r.created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# Section 3: validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_fbh_id_prefix():
    with pytest.raises(ValueError, match="FBH-"):
        _build(fbh_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_auroc_below_negative_one():
    entries = [
        {"family_name": "test", "auroc": -1.5, "n_candidates": 10, "panel_count": 3},
    ]
    with pytest.raises(ValueError, match="auroc"):
        _build(family_entry_dicts=entries)


def test_validate_rejects_auroc_above_one():
    entries = [
        {"family_name": "test", "auroc": 1.5, "n_candidates": 10, "panel_count": 3},
    ]
    with pytest.raises(ValueError, match="auroc"):
        _build(family_entry_dicts=entries)


def test_validate_rejects_n_candidates_zero():
    entries = [
        {"family_name": "test", "auroc": 0.5, "n_candidates": 0, "panel_count": 0},
    ]
    with pytest.raises(ValueError, match="n_candidates"):
        _build(family_entry_dicts=entries)


def test_validate_rejects_panel_count_exceeds_n_candidates():
    entries = [
        {"family_name": "test", "auroc": 0.5, "n_candidates": 5, "panel_count": 10},
    ]
    with pytest.raises(ValueError, match="panel_count"):
        _build(family_entry_dicts=entries)


def test_validate_rejects_negative_panel_count():
    entries = [
        {"family_name": "test", "auroc": 0.5, "n_candidates": 5, "panel_count": -1},
    ]
    with pytest.raises(ValueError, match="panel_count"):
        _build(family_entry_dicts=entries)


def test_validate_rejects_n_families_total_mismatch():
    r = _build()
    r.n_families_total = 999
    with pytest.raises(ValueError, match="n_families_total"):
        validate_family_blindness_challenge(r)


def test_validate_rejects_n_weak_families_mismatch():
    r = _build(family_entry_dicts=_WEAK_EXCLUDED)
    r.n_weak_families = 999
    with pytest.raises(ValueError, match="n_weak_families"):
        validate_family_blindness_challenge(r)


def test_validate_rejects_n_excluded_weak_families_mismatch():
    r = _build(family_entry_dicts=_WEAK_EXCLUDED)
    r.n_excluded_weak_families = 999
    with pytest.raises(ValueError, match="n_excluded_weak_families"):
        validate_family_blindness_challenge(r)


def test_validate_rejects_excluded_names_length_mismatch():
    r = _build(family_entry_dicts=_WEAK_EXCLUDED)
    r.excluded_weak_family_names = []
    with pytest.raises(ValueError, match="excluded_weak_family_names"):
        validate_family_blindness_challenge(r)


def test_validate_rejects_invalid_verdict():
    r = _build()
    r.verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="verdict"):
        validate_family_blindness_challenge(r)


def test_validate_rejects_weak_excluded_without_excluded():
    r = _build(family_entry_dicts=_ALL_REPRESENTED)
    r.verdict = "weak_family_excluded"
    with pytest.raises(ValueError, match="weak_family_excluded"):
        validate_family_blindness_challenge(r)


def test_validate_rejects_all_represented_with_excluded():
    r = _build(family_entry_dicts=_WEAK_EXCLUDED)
    r.verdict = "all_families_represented"
    with pytest.raises(ValueError, match="all_families_represented"):
        validate_family_blindness_challenge(r)


def test_validate_rejects_dry_lab_only_false():
    r = _build()
    r.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_family_blindness_challenge(r)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# Section 4: format
# ---------------------------------------------------------------------------


def test_format_contains_fbh_id():
    assert "FBH-001" in format_family_blindness_challenge(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_family_blindness_challenge(_build())


def test_format_contains_verdict():
    assert "all_families_represented" in format_family_blindness_challenge(_build())


def test_format_contains_weak_family_names():
    r = _build(family_entry_dicts=_WEAK_EXCLUDED)
    assert "bacteriocin" in format_family_blindness_challenge(r)


def test_format_contains_limitations():
    assert "dry-lab only" in format_family_blindness_challenge(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_family_blindness_challenge(_build())


def test_format_contains_n_families():
    text = format_family_blindness_challenge(_build())
    assert "2 total" in text


def test_format_is_string():
    assert isinstance(format_family_blindness_challenge(_build()), str)

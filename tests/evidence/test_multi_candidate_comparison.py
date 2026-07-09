"""Tests for multi-candidate comparison schema (Phase L L4)."""

import pytest
from openamp_foundry.evidence.multi_candidate_comparison import (
    LARGE_CANDIDATE_SET_THRESHOLD,
    MAX_RATIONALE_LENGTH,
    MINIMUM_CANDIDATES,
    MINIMUM_CRITERIA,
    RECOMMENDED_CRITERIA,
    VALID_EVIDENCE_LEVELS,
    MultiCandidateComparisonEntry,
    MultiCandidateComparisonResult,
    validate_multi_candidate_comparison,
    validate_multi_candidate_comparison_dict,
)


def _valid_entry(**kwargs) -> MultiCandidateComparisonEntry:
    defaults = dict(
        comparison_id="CMP-001",
        batch_id="BATCH-001",
        pipeline_version="0.8.7",
        comparison_date="2026-07-09",
        candidate_ids=["AMP-001", "AMP-002", "AMP-003"],
        comparison_criteria=["predicted_mic", "hemolysis_fraction", "selectivity_index"],
        top_candidate_id="AMP-001",
        top_candidate_rationale="Highest selectivity index with lowest hemolysis fraction.",
        evidence_level=4,
        reviewer="alice",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return MultiCandidateComparisonEntry(**defaults)


# ── Constants ────────────────────────────────────────────────────────────────


def test_minimum_candidates_is_two():
    assert MINIMUM_CANDIDATES == 2


def test_minimum_criteria_is_two():
    assert MINIMUM_CRITERIA == 2


def test_recommended_criteria_is_three():
    assert RECOMMENDED_CRITERIA == 3


def test_max_rationale_length_is_500():
    assert MAX_RATIONALE_LENGTH == 500


def test_large_candidate_set_threshold_is_ten():
    assert LARGE_CANDIDATE_SET_THRESHOLD == 10


# ── Valid entry ───────────────────────────────────────────────────────────────


def test_valid_entry_passes():
    result = validate_multi_candidate_comparison(_valid_entry())
    assert result.passed
    assert result.errors == []


def test_result_dry_lab_only_true():
    result = validate_multi_candidate_comparison(_valid_entry())
    assert result.dry_lab_only is True


def test_result_candidate_count():
    result = validate_multi_candidate_comparison(_valid_entry())
    assert result.candidate_count == 3


def test_result_fields_match():
    result = validate_multi_candidate_comparison(_valid_entry())
    assert result.comparison_id == "CMP-001"
    assert result.batch_id == "BATCH-001"


def test_valid_exactly_two_candidates():
    result = validate_multi_candidate_comparison(
        _valid_entry(
            candidate_ids=["AMP-001", "AMP-002"],
            top_candidate_id="AMP-001",
        )
    )
    assert result.passed


def test_valid_all_evidence_levels():
    for level in VALID_EVIDENCE_LEVELS - {1, 2}:
        result = validate_multi_candidate_comparison(_valid_entry(evidence_level=level))
        assert result.passed


# ── comparison_id validation ──────────────────────────────────────────────────


def test_comparison_id_missing_prefix_fails():
    result = validate_multi_candidate_comparison(_valid_entry(comparison_id="001"))
    assert not result.passed
    assert any("CMP-" in e for e in result.errors)


def test_comparison_id_wrong_prefix_fails():
    result = validate_multi_candidate_comparison(_valid_entry(comparison_id="BND-001"))
    assert not result.passed


def test_comparison_id_correct_prefix_passes():
    result = validate_multi_candidate_comparison(_valid_entry(comparison_id="CMP-XYZ-99"))
    assert result.passed


# ── date validation ───────────────────────────────────────────────────────────


def test_invalid_date_fails():
    result = validate_multi_candidate_comparison(_valid_entry(comparison_date="2026/07/09"))
    assert not result.passed
    assert any("YYYY-MM-DD" in e for e in result.errors)


# ── candidate_ids validation ──────────────────────────────────────────────────


def test_only_one_candidate_fails():
    result = validate_multi_candidate_comparison(
        _valid_entry(candidate_ids=["AMP-001"], top_candidate_id="AMP-001")
    )
    assert not result.passed
    assert any("at least" in e and "candidate" in e for e in result.errors)


def test_top_candidate_not_in_list_fails():
    result = validate_multi_candidate_comparison(
        _valid_entry(top_candidate_id="AMP-999")
    )
    assert not result.passed
    assert any("top_candidate_id" in e for e in result.errors)


# ── comparison_criteria validation ────────────────────────────────────────────


def test_only_one_criterion_fails():
    result = validate_multi_candidate_comparison(
        _valid_entry(comparison_criteria=["predicted_mic"])
    )
    assert not result.passed
    assert any("comparison_criteria" in e for e in result.errors)


# ── rationale validation ──────────────────────────────────────────────────────


def test_empty_rationale_fails():
    result = validate_multi_candidate_comparison(_valid_entry(top_candidate_rationale=""))
    assert not result.passed
    assert any("rationale" in e for e in result.errors)


def test_rationale_too_long_fails():
    result = validate_multi_candidate_comparison(
        _valid_entry(top_candidate_rationale="X" * 501)
    )
    assert not result.passed
    assert any("500" in e for e in result.errors)


def test_rationale_exactly_500_passes():
    result = validate_multi_candidate_comparison(
        _valid_entry(top_candidate_rationale="X" * 500)
    )
    assert result.passed


# ── dry_lab_only constraint ───────────────────────────────────────────────────


def test_dry_lab_only_false_fails():
    result = validate_multi_candidate_comparison(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# ── warnings ─────────────────────────────────────────────────────────────────


def test_low_evidence_level_warns():
    result = validate_multi_candidate_comparison(_valid_entry(evidence_level=2))
    assert result.passed
    assert any("low" in w or "reliable" in w for w in result.warnings)


def test_large_candidate_set_warns():
    result = validate_multi_candidate_comparison(
        _valid_entry(
            candidate_ids=[f"AMP-{i:03d}" for i in range(11)],
            top_candidate_id="AMP-000",
        )
    )
    assert result.passed
    assert any("Large" in w or "large" in w for w in result.warnings)


def test_few_criteria_warns():
    result = validate_multi_candidate_comparison(
        _valid_entry(comparison_criteria=["predicted_mic", "hemolysis_fraction"])
    )
    assert result.passed
    assert any("criteria" in w or "criterion" in w for w in result.warnings)


def test_full_comparison_no_warnings():
    result = validate_multi_candidate_comparison(_valid_entry())
    assert result.passed
    assert result.warnings == []


# ── dict interface ────────────────────────────────────────────────────────────


def test_dict_valid_passes():
    d = dict(
        comparison_id="CMP-D01",
        batch_id="BATCH-D01",
        pipeline_version="0.8.7",
        comparison_date="2026-07-09",
        candidate_ids=["AMP-001", "AMP-002"],
        comparison_criteria=["predicted_mic", "selectivity_index"],
        top_candidate_id="AMP-001",
        top_candidate_rationale="Better selectivity.",
        evidence_level=4,
        reviewer="alice",
        dry_lab_only=True,
    )
    result = validate_multi_candidate_comparison_dict(d)
    assert result.passed


def test_dict_missing_field_fails():
    d = dict(
        comparison_id="CMP-D02",
        batch_id="BATCH-D02",
        pipeline_version="0.8.7",
        comparison_date="2026-07-09",
        candidate_ids=["AMP-001", "AMP-002"],
        comparison_criteria=["predicted_mic", "selectivity_index"],
        top_candidate_id="AMP-001",
        top_candidate_rationale="Better.",
        evidence_level=4,
        # missing reviewer
    )
    result = validate_multi_candidate_comparison_dict(d)
    assert not result.passed
    assert any("reviewer" in e for e in result.errors)


def test_dict_dry_lab_only_defaults_true():
    d = dict(
        comparison_id="CMP-D03",
        batch_id="BATCH-D03",
        pipeline_version="0.8.7",
        comparison_date="2026-07-09",
        candidate_ids=["AMP-001", "AMP-002"],
        comparison_criteria=["predicted_mic", "selectivity_index"],
        top_candidate_id="AMP-001",
        top_candidate_rationale="Better.",
        evidence_level=4,
        reviewer="alice",
    )
    result = validate_multi_candidate_comparison_dict(d)
    assert result.passed
    assert result.dry_lab_only is True

"""Tests for candidate summary card schema (Phase L L3)."""

import pytest
from openamp_foundry.evidence.candidate_summary_card import (
    LONG_PEPTIDE_THRESHOLD,
    VALID_ACTIVITY_LABELS,
    VALID_AMINO_ACIDS,
    VALID_EVIDENCE_LEVELS,
    CandidateSummaryCardEntry,
    CandidateSummaryCardResult,
    validate_candidate_summary_card,
    validate_candidate_summary_card_dict,
)


def _valid_entry(**kwargs) -> CandidateSummaryCardEntry:
    defaults = dict(
        card_id="CRD-001",
        candidate_id="AMP-001",
        batch_id="BATCH-001",
        pipeline_version="0.8.6",
        sequence="KWKLFKKIEK",
        sequence_length=10,
        evidence_level=4,
        predicted_activity="high_activity",
        safety_flags=[],
        selection_rationale_id="SEL-001",
        reviewer="alice",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return CandidateSummaryCardEntry(**defaults)


# ── Constants ────────────────────────────────────────────────────────────────


def test_valid_activity_labels_count():
    assert len(VALID_ACTIVITY_LABELS) == 5


def test_valid_amino_acids_count():
    assert len(VALID_AMINO_ACIDS) == 20


def test_long_peptide_threshold_is_50():
    assert LONG_PEPTIDE_THRESHOLD == 50


def test_valid_evidence_levels():
    assert VALID_EVIDENCE_LEVELS == {1, 2, 3, 4, 5, 6}


# ── Valid entry ───────────────────────────────────────────────────────────────


def test_valid_entry_passes():
    result = validate_candidate_summary_card(_valid_entry())
    assert result.passed
    assert result.errors == []


def test_result_dry_lab_only_true():
    result = validate_candidate_summary_card(_valid_entry())
    assert result.dry_lab_only is True


def test_result_fields_match():
    result = validate_candidate_summary_card(_valid_entry())
    assert result.card_id == "CRD-001"
    assert result.candidate_id == "AMP-001"
    assert result.sequence_length == 10


def test_valid_all_activity_labels():
    for label in VALID_ACTIVITY_LABELS - {"uncertain"}:
        result = validate_candidate_summary_card(
            _valid_entry(predicted_activity=label)
        )
        assert result.passed, f"predicted_activity '{label}' should be valid"


def test_valid_all_evidence_levels():
    for level in VALID_EVIDENCE_LEVELS - {1, 2}:
        result = validate_candidate_summary_card(_valid_entry(evidence_level=level))
        assert result.passed, f"evidence_level {level} should be valid"


def test_valid_with_safety_flags():
    result = validate_candidate_summary_card(
        _valid_entry(safety_flags=["hemolysis_risk"])
    )
    assert result.passed


def test_valid_long_sequence():
    seq = "KWKLFKKIEK" * 6
    result = validate_candidate_summary_card(
        _valid_entry(sequence=seq, sequence_length=len(seq))
    )
    assert result.passed


# ── card_id validation ────────────────────────────────────────────────────────


def test_card_id_missing_prefix_fails():
    result = validate_candidate_summary_card(_valid_entry(card_id="001"))
    assert not result.passed
    assert any("CRD-" in e for e in result.errors)


def test_card_id_wrong_prefix_fails():
    result = validate_candidate_summary_card(_valid_entry(card_id="SEL-001"))
    assert not result.passed


# ── sequence validation ───────────────────────────────────────────────────────


def test_empty_sequence_fails():
    result = validate_candidate_summary_card(_valid_entry(sequence="", sequence_length=0))
    assert not result.passed
    assert any("sequence" in e for e in result.errors)


def test_invalid_amino_acid_fails():
    result = validate_candidate_summary_card(
        _valid_entry(sequence="KWKXLFKK", sequence_length=9)
    )
    assert not result.passed
    assert any("invalid" in e for e in result.errors)


def test_sequence_length_mismatch_fails():
    result = validate_candidate_summary_card(
        _valid_entry(sequence="KWKLFKKIEK", sequence_length=5)
    )
    assert not result.passed
    assert any("sequence_length" in e for e in result.errors)


def test_lowercase_sequence_fails():
    result = validate_candidate_summary_card(
        _valid_entry(sequence="kwklfkkiek", sequence_length=10)
    )
    assert not result.passed


# ── selection_rationale_id validation ────────────────────────────────────────


def test_sel_prefix_wrong_fails():
    result = validate_candidate_summary_card(
        _valid_entry(selection_rationale_id="CRD-001")
    )
    assert not result.passed
    assert any("SEL-" in e for e in result.errors)


def test_sel_prefix_correct_passes():
    result = validate_candidate_summary_card(
        _valid_entry(selection_rationale_id="SEL-XYZ-99")
    )
    assert result.passed


# ── dry_lab_only constraint ───────────────────────────────────────────────────


def test_dry_lab_only_false_fails():
    result = validate_candidate_summary_card(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# ── warnings ─────────────────────────────────────────────────────────────────


def test_low_evidence_level_warns():
    result = validate_candidate_summary_card(_valid_entry(evidence_level=2))
    assert result.passed
    assert any("low" in w or "scrutiny" in w for w in result.warnings)


def test_safety_flags_warn():
    result = validate_candidate_summary_card(
        _valid_entry(safety_flags=["hemolysis_risk", "toxicity_flag"])
    )
    assert result.passed
    assert any("Safety" in w or "safety" in w for w in result.warnings)


def test_uncertain_activity_warns():
    result = validate_candidate_summary_card(
        _valid_entry(predicted_activity="uncertain")
    )
    assert result.passed
    assert any("uncertain" in w for w in result.warnings)


def test_long_peptide_warns():
    seq = "A" * 51
    result = validate_candidate_summary_card(
        _valid_entry(sequence=seq, sequence_length=51)
    )
    assert result.passed
    assert any("synthesis cost" in w or str(51) in w for w in result.warnings)


def test_short_clean_card_no_warnings():
    result = validate_candidate_summary_card(_valid_entry())
    assert result.passed
    assert result.warnings == []


# ── dict interface ────────────────────────────────────────────────────────────


def test_dict_valid_passes():
    d = dict(
        card_id="CRD-D01",
        candidate_id="AMP-D01",
        batch_id="BATCH-D01",
        pipeline_version="0.8.6",
        sequence="KWKLFKKIEK",
        sequence_length=10,
        evidence_level=4,
        predicted_activity="high_activity",
        safety_flags=[],
        selection_rationale_id="SEL-D01",
        reviewer="alice",
        dry_lab_only=True,
    )
    result = validate_candidate_summary_card_dict(d)
    assert result.passed


def test_dict_missing_field_fails():
    d = dict(
        card_id="CRD-D02",
        candidate_id="AMP-D02",
        batch_id="BATCH-D02",
        pipeline_version="0.8.6",
        sequence="KWKLFKKIEK",
        sequence_length=10,
        evidence_level=4,
        predicted_activity="high_activity",
        safety_flags=[],
        # missing selection_rationale_id
        reviewer="alice",
    )
    result = validate_candidate_summary_card_dict(d)
    assert not result.passed
    assert any("selection_rationale_id" in e for e in result.errors)


def test_dict_dry_lab_only_defaults_true():
    d = dict(
        card_id="CRD-D03",
        candidate_id="AMP-D03",
        batch_id="BATCH-D03",
        pipeline_version="0.8.6",
        sequence="KWKLFKKIEK",
        sequence_length=10,
        evidence_level=4,
        predicted_activity="high_activity",
        safety_flags=[],
        selection_rationale_id="SEL-D03",
        reviewer="alice",
    )
    result = validate_candidate_summary_card_dict(d)
    assert result.passed
    assert result.dry_lab_only is True

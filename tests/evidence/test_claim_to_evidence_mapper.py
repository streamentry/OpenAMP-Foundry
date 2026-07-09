import pytest
from openamp_foundry.evidence.claim_to_evidence_mapper import (
    ClaimToEvidenceEntry,
    ClaimToEvidenceResult,
    validate_claim_to_evidence,
    validate_claim_to_evidence_dict,
    VALID_CLAIM_TYPES,
    VALID_EVIDENCE_LEVELS,
    MAX_CLAIM_TEXT_LENGTH,
    LONG_CLAIM_TEXT_THRESHOLD,
    WEAK_EVIDENCE_THRESHOLD,
)


def _valid_entry(**overrides) -> ClaimToEvidenceEntry:
    base = dict(
        mapping_id="CEM-001",
        batch_id="BATCH-001",
        pipeline_version="0.9.0",
        claim_text="Candidate AMP-042 shows predicted MIC of 4 ug/mL against E. coli.",
        claim_type="activity_prediction",
        supporting_artifact_ids=["CERT-001", "SEL-001"],
        evidence_level=3,
        pre_specified=True,
        reviewer="reviewer@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return ClaimToEvidenceEntry(**base)


def _valid_dict(**overrides) -> dict:
    base = dict(
        mapping_id="CEM-001",
        batch_id="BATCH-001",
        pipeline_version="0.9.0",
        claim_text="Candidate AMP-042 shows predicted MIC of 4 ug/mL against E. coli.",
        claim_type="activity_prediction",
        supporting_artifact_ids=["CERT-001", "SEL-001"],
        evidence_level=3,
        pre_specified=True,
        reviewer="reviewer@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return base


# --- Happy path ---

def test_valid_entry_passes():
    result = validate_claim_to_evidence(_valid_entry())
    assert result.passed
    assert result.errors == []
    assert result.warnings == []


def test_result_dry_lab_only_always_true():
    result = validate_claim_to_evidence(_valid_entry())
    assert result.dry_lab_only is True


def test_result_fields_populated():
    result = validate_claim_to_evidence(_valid_entry())
    assert result.mapping_id == "CEM-001"
    assert result.batch_id == "BATCH-001"
    assert result.claim_type == "activity_prediction"


def test_all_claim_types_valid():
    for ct in VALID_CLAIM_TYPES:
        result = validate_claim_to_evidence(_valid_entry(claim_type=ct))
        assert result.passed, f"claim_type={ct} should pass"


def test_all_evidence_levels_valid():
    for lvl in VALID_EVIDENCE_LEVELS:
        if lvl > WEAK_EVIDENCE_THRESHOLD:
            result = validate_claim_to_evidence(_valid_entry(evidence_level=lvl))
            assert result.passed


def test_many_supporting_artifacts():
    result = validate_claim_to_evidence(
        _valid_entry(supporting_artifact_ids=["A", "B", "C", "D", "E"])
    )
    assert result.passed


def test_single_artifact_warns():
    result = validate_claim_to_evidence(
        _valid_entry(supporting_artifact_ids=["CERT-001"])
    )
    assert result.passed
    assert any("one supporting artifact" in w for w in result.warnings)


# --- mapping_id validation ---

def test_mapping_id_must_start_with_cem():
    result = validate_claim_to_evidence(_valid_entry(mapping_id="MAP-001"))
    assert not result.passed
    assert any("CEM-" in e for e in result.errors)


def test_mapping_id_empty_fails():
    result = validate_claim_to_evidence(_valid_entry(mapping_id=""))
    assert not result.passed


def test_mapping_id_cem_prefix_valid():
    result = validate_claim_to_evidence(_valid_entry(mapping_id="CEM-999"))
    assert result.passed


# --- claim_text validation ---

def test_empty_claim_text_fails():
    result = validate_claim_to_evidence(_valid_entry(claim_text=""))
    assert not result.passed
    assert any("claim_text" in e for e in result.errors)


def test_claim_text_at_max_length_passes():
    text = "A" * MAX_CLAIM_TEXT_LENGTH
    result = validate_claim_to_evidence(_valid_entry(claim_text=text))
    assert result.passed


def test_claim_text_over_max_fails():
    text = "A" * (MAX_CLAIM_TEXT_LENGTH + 1)
    result = validate_claim_to_evidence(_valid_entry(claim_text=text))
    assert not result.passed


def test_long_claim_text_warns():
    text = "A" * (LONG_CLAIM_TEXT_THRESHOLD + 1)
    result = validate_claim_to_evidence(_valid_entry(claim_text=text))
    assert result.passed
    assert any("long" in w.lower() for w in result.warnings)


# --- claim_type validation ---

def test_invalid_claim_type_fails():
    result = validate_claim_to_evidence(_valid_entry(claim_type="made_up_type"))
    assert not result.passed
    assert any("claim_type" in e for e in result.errors)


def test_empty_claim_type_fails():
    result = validate_claim_to_evidence(_valid_entry(claim_type=""))
    assert not result.passed


# --- supporting_artifact_ids validation ---

def test_empty_artifact_ids_fails():
    result = validate_claim_to_evidence(_valid_entry(supporting_artifact_ids=[]))
    assert not result.passed
    assert any("supporting_artifact_ids" in e for e in result.errors)


# --- evidence_level validation ---

def test_evidence_level_zero_fails():
    result = validate_claim_to_evidence(_valid_entry(evidence_level=0))
    assert not result.passed


def test_evidence_level_seven_fails():
    result = validate_claim_to_evidence(_valid_entry(evidence_level=7))
    assert not result.passed


def test_evidence_level_1_warns():
    result = validate_claim_to_evidence(_valid_entry(evidence_level=1))
    assert result.passed
    assert any("weak" in w.lower() for w in result.warnings)


def test_evidence_level_2_warns():
    result = validate_claim_to_evidence(_valid_entry(evidence_level=2))
    assert result.passed
    assert any("weak" in w.lower() for w in result.warnings)


def test_evidence_level_3_no_weak_warning():
    result = validate_claim_to_evidence(_valid_entry(evidence_level=3))
    assert result.passed
    assert not any("weak" in w.lower() for w in result.warnings)


# --- reviewer validation ---

def test_empty_reviewer_fails():
    result = validate_claim_to_evidence(_valid_entry(reviewer=""))
    assert not result.passed
    assert any("reviewer" in e for e in result.errors)


# --- dry_lab_only validation ---

def test_dry_lab_only_false_fails():
    result = validate_claim_to_evidence(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# --- pre_specified warning ---

def test_post_hoc_claim_warns():
    result = validate_claim_to_evidence(_valid_entry(pre_specified=False))
    assert result.passed
    assert any("pre_specified" in w for w in result.warnings)


def test_pre_specified_true_no_posthoc_warning():
    result = validate_claim_to_evidence(_valid_entry(pre_specified=True))
    assert not any("pre_specified" in w for w in result.warnings)


# --- dict interface ---

def test_valid_dict_passes():
    result = validate_claim_to_evidence_dict(_valid_dict())
    assert result.passed


def test_missing_mapping_id_fails():
    d = _valid_dict()
    del d["mapping_id"]
    result = validate_claim_to_evidence_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


def test_missing_claim_text_fails():
    d = _valid_dict()
    del d["claim_text"]
    result = validate_claim_to_evidence_dict(d)
    assert not result.passed


def test_missing_supporting_artifacts_fails():
    d = _valid_dict()
    del d["supporting_artifact_ids"]
    result = validate_claim_to_evidence_dict(d)
    assert not result.passed


def test_dict_dry_lab_only_defaults_true():
    d = _valid_dict()
    del d["dry_lab_only"]
    result = validate_claim_to_evidence_dict(d)
    assert result.passed
    assert result.dry_lab_only is True


def test_multiple_missing_fields_reported():
    d = {}
    result = validate_claim_to_evidence_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


# --- constants ---

def test_valid_claim_types_count():
    assert len(VALID_CLAIM_TYPES) == 7


def test_valid_evidence_levels_count():
    assert len(VALID_EVIDENCE_LEVELS) == 6


def test_max_claim_text_length_value():
    assert MAX_CLAIM_TEXT_LENGTH == 500


def test_long_claim_text_threshold_value():
    assert LONG_CLAIM_TEXT_THRESHOLD == 300


def test_weak_evidence_threshold_value():
    assert WEAK_EVIDENCE_THRESHOLD == 2

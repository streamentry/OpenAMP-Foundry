import pytest
from openamp_foundry.evidence.reviewer_briefing_package import (
    ReviewerBriefingEntry,
    ReviewerBriefingResult,
    validate_reviewer_briefing,
    validate_reviewer_briefing_dict,
    MINIMUM_ARTIFACT_IDS,
    MAX_SCOPE_LENGTH,
    LONG_SCOPE_THRESHOLD,
    LARGE_BATCH_THRESHOLD,
    MAX_OPEN_QUESTIONS_WARNING,
    MINIMAL_ARTIFACT_WARNING_COUNT,
)


def _valid_entry(**overrides) -> ReviewerBriefingEntry:
    base = dict(
        briefing_id="RBP-001",
        batch_id="BATCH-001",
        pipeline_version="0.9.2",
        prepared_date="2026-07-10",
        reviewer_name="Dr. Jane Reviewer",
        candidate_count=10,
        artifact_ids=["CERT-001", "SEL-001", "SDR-001", "CEM-001"],
        open_questions=["Is the novelty filter sufficient?", "Are hemolysis flags conservative enough?"],
        scope_description="Review candidate selection rationale and evidence certificates for batch BATCH-001.",
        conflict_of_interest_declared=True,
        dry_lab_only=True,
    )
    base.update(overrides)
    return ReviewerBriefingEntry(**base)


def _valid_dict(**overrides) -> dict:
    base = dict(
        briefing_id="RBP-001",
        batch_id="BATCH-001",
        pipeline_version="0.9.2",
        prepared_date="2026-07-10",
        reviewer_name="Dr. Jane Reviewer",
        candidate_count=10,
        artifact_ids=["CERT-001", "SEL-001", "SDR-001", "CEM-001"],
        open_questions=["Is the novelty filter sufficient?"],
        scope_description="Review candidate selection rationale and evidence certificates.",
        conflict_of_interest_declared=True,
        dry_lab_only=True,
    )
    base.update(overrides)
    return base


# --- Happy path ---

def test_valid_entry_passes():
    result = validate_reviewer_briefing(_valid_entry())
    assert result.passed
    assert result.errors == []
    assert result.warnings == []


def test_result_dry_lab_only_always_true():
    result = validate_reviewer_briefing(_valid_entry())
    assert result.dry_lab_only is True


def test_result_fields_populated():
    result = validate_reviewer_briefing(_valid_entry())
    assert result.briefing_id == "RBP-001"
    assert result.batch_id == "BATCH-001"
    assert result.reviewer_name == "Dr. Jane Reviewer"


def test_empty_open_questions_passes():
    result = validate_reviewer_briefing(_valid_entry(open_questions=[]))
    assert result.passed
    assert result.warnings == []


def test_many_artifact_ids_passes():
    result = validate_reviewer_briefing(
        _valid_entry(artifact_ids=["A", "B", "C", "D", "E", "F"])
    )
    assert result.passed


def test_exactly_minimum_artifacts_warns():
    result = validate_reviewer_briefing(
        _valid_entry(artifact_ids=["CERT-001", "SEL-001", "SDR-001"])
    )
    assert result.passed
    assert any("only" in w.lower() and "3" in w for w in result.warnings)


# --- briefing_id validation ---

def test_briefing_id_must_start_with_rbp():
    result = validate_reviewer_briefing(_valid_entry(briefing_id="PKG-001"))
    assert not result.passed
    assert any("RBP-" in e for e in result.errors)


def test_briefing_id_empty_fails():
    result = validate_reviewer_briefing(_valid_entry(briefing_id=""))
    assert not result.passed


def test_briefing_id_rbp_prefix_valid():
    result = validate_reviewer_briefing(_valid_entry(briefing_id="RBP-999"))
    assert result.passed


# --- reviewer_name ---

def test_empty_reviewer_name_fails():
    result = validate_reviewer_briefing(_valid_entry(reviewer_name=""))
    assert not result.passed
    assert any("reviewer_name" in e for e in result.errors)


# --- candidate_count ---

def test_candidate_count_zero_fails():
    result = validate_reviewer_briefing(_valid_entry(candidate_count=0))
    assert not result.passed
    assert any("candidate_count" in e for e in result.errors)


def test_candidate_count_negative_fails():
    result = validate_reviewer_briefing(_valid_entry(candidate_count=-1))
    assert not result.passed


def test_candidate_count_one_passes():
    result = validate_reviewer_briefing(_valid_entry(candidate_count=1))
    assert result.passed


def test_large_candidate_count_warns():
    result = validate_reviewer_briefing(_valid_entry(candidate_count=51))
    assert result.passed
    assert any("large batch" in w.lower() or str(LARGE_BATCH_THRESHOLD) in w for w in result.warnings)


def test_candidate_count_at_threshold_no_warn():
    result = validate_reviewer_briefing(_valid_entry(candidate_count=LARGE_BATCH_THRESHOLD))
    assert not any("large batch" in w.lower() for w in result.warnings)


# --- artifact_ids ---

def test_empty_artifact_ids_fails():
    result = validate_reviewer_briefing(_valid_entry(artifact_ids=[]))
    assert not result.passed
    assert any("artifact_ids" in e for e in result.errors)


def test_two_artifact_ids_fails():
    result = validate_reviewer_briefing(_valid_entry(artifact_ids=["A", "B"]))
    assert not result.passed


def test_three_artifact_ids_passes_with_warning():
    result = validate_reviewer_briefing(_valid_entry(artifact_ids=["A", "B", "C"]))
    assert result.passed


# --- scope_description ---

def test_empty_scope_fails():
    result = validate_reviewer_briefing(_valid_entry(scope_description=""))
    assert not result.passed
    assert any("scope_description" in e for e in result.errors)


def test_scope_at_max_length_passes():
    result = validate_reviewer_briefing(_valid_entry(scope_description="X" * MAX_SCOPE_LENGTH))
    assert result.passed


def test_scope_over_max_fails():
    result = validate_reviewer_briefing(_valid_entry(scope_description="X" * (MAX_SCOPE_LENGTH + 1)))
    assert not result.passed
    assert any("scope_description" in e for e in result.errors)


def test_long_scope_warns():
    result = validate_reviewer_briefing(_valid_entry(scope_description="X" * (LONG_SCOPE_THRESHOLD + 1)))
    assert result.passed
    assert any("long" in w.lower() or "tighten" in w.lower() for w in result.warnings)


def test_scope_at_long_threshold_no_warn():
    result = validate_reviewer_briefing(_valid_entry(scope_description="X" * LONG_SCOPE_THRESHOLD))
    assert not any("tighten" in w.lower() for w in result.warnings)


# --- conflict_of_interest ---

def test_coi_not_declared_fails():
    result = validate_reviewer_briefing(_valid_entry(conflict_of_interest_declared=False))
    assert not result.passed
    assert any("conflict_of_interest" in e for e in result.errors)


def test_coi_declared_passes():
    result = validate_reviewer_briefing(_valid_entry(conflict_of_interest_declared=True))
    assert result.passed


# --- dry_lab_only ---

def test_dry_lab_only_false_fails():
    result = validate_reviewer_briefing(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# --- open_questions warning ---

def test_many_open_questions_warns():
    questions = [f"Question {i}?" for i in range(MAX_OPEN_QUESTIONS_WARNING + 1)]
    result = validate_reviewer_briefing(_valid_entry(open_questions=questions))
    assert result.passed
    assert any("underfocused" in w.lower() or str(MAX_OPEN_QUESTIONS_WARNING) in w for w in result.warnings)


def test_exactly_max_questions_no_warn():
    questions = [f"Question {i}?" for i in range(MAX_OPEN_QUESTIONS_WARNING)]
    result = validate_reviewer_briefing(_valid_entry(open_questions=questions))
    assert not any("underfocused" in w.lower() for w in result.warnings)


# --- dict interface ---

def test_valid_dict_passes():
    result = validate_reviewer_briefing_dict(_valid_dict())
    assert result.passed


def test_missing_briefing_id_fails():
    d = _valid_dict()
    del d["briefing_id"]
    result = validate_reviewer_briefing_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


def test_missing_reviewer_name_fails():
    d = _valid_dict()
    del d["reviewer_name"]
    result = validate_reviewer_briefing_dict(d)
    assert not result.passed


def test_missing_artifact_ids_fails():
    d = _valid_dict()
    del d["artifact_ids"]
    result = validate_reviewer_briefing_dict(d)
    assert not result.passed


def test_dict_dry_lab_only_defaults_true():
    d = _valid_dict()
    del d["dry_lab_only"]
    result = validate_reviewer_briefing_dict(d)
    assert result.passed
    assert result.dry_lab_only is True


def test_multiple_missing_fields():
    d = {}
    result = validate_reviewer_briefing_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


# --- constants ---

def test_minimum_artifact_ids_value():
    assert MINIMUM_ARTIFACT_IDS == 3


def test_max_scope_length_value():
    assert MAX_SCOPE_LENGTH == 500


def test_long_scope_threshold_value():
    assert LONG_SCOPE_THRESHOLD == 300


def test_large_batch_threshold_value():
    assert LARGE_BATCH_THRESHOLD == 50


def test_max_open_questions_warning_value():
    assert MAX_OPEN_QUESTIONS_WARNING == 5


def test_minimal_artifact_warning_count_value():
    assert MINIMAL_ARTIFACT_WARNING_COUNT == 3

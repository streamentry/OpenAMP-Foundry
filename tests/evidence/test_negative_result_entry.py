"""Tests for NegativeResultEntry (NRR-) schema — Phase F F1."""

import pytest
from openamp_foundry.evidence.negative_result_entry import (
    NOTES_MAX_LENGTH,
    NRR_PREFIX,
    OUTCOME_SUMMARY_MAX_LENGTH,
    VALID_REJECTION_CONFIDENCES,
    VALID_REJECTION_REASONS,
    VALID_REJECTION_STAGES,
    NegativeResultEntry,
    NegativeResultEntryResult,
    validate,
    validate_dict,
)


def _make(**kwargs) -> NegativeResultEntry:
    defaults = dict(
        nrr_id="NRR-001",
        pipeline_version="v0.10.14",
        candidate_id="CAND-042",
        batch_id="BATCH-007",
        experiment_date="2026-07-10",
        stage_at_rejection="toxicity_screen",
        rejection_reason="failed_toxicity",
        rejection_confidence="high",
        outcome_summary="Candidate failed ToxinPred screen with score 0.82, above 0.7 threshold.",
        rejection_is_final=True,
        notes="",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return NegativeResultEntry(**defaults)


# --- Baseline valid ---

class TestValidBaseline:
    def test_valid_entry_passes(self):
        r = validate(_make())
        assert r.valid
        assert r.errors == []

    def test_valid_returns_result_type(self):
        r = validate(_make())
        assert isinstance(r, NegativeResultEntryResult)

    def test_valid_with_notes(self):
        r = validate(_make(notes="Manual check confirmed toxicity concern."))
        assert r.valid

    def test_valid_not_final(self):
        r = validate(_make(rejection_is_final=False, rejection_confidence="low"))
        assert r.valid

    def test_valid_manual_exclusion_with_notes(self):
        r = validate(_make(
            stage_at_rejection="manual_review",
            rejection_reason="manual_exclusion",
            notes="Excluded by domain expert after safety panel review.",
        ))
        assert r.valid

    def test_valid_all_stages(self):
        for stage in VALID_REJECTION_STAGES:
            r = validate(_make(stage_at_rejection=stage))
            assert r.valid or len(r.errors) == 0 or all("stage" not in e for e in r.errors)

    def test_valid_all_reasons(self):
        for reason in VALID_REJECTION_REASONS:
            r = validate(_make(rejection_reason=reason))
            assert r.valid or all("reason" not in e for e in r.errors)

    def test_valid_all_confidences(self):
        for conf in VALID_REJECTION_CONFIDENCES:
            r = validate(_make(rejection_confidence=conf))
            assert r.valid or all("confidence" not in e for e in r.errors)


# --- nrr_id validation ---

class TestNrrIdValidation:
    def test_invalid_prefix(self):
        r = validate(_make(nrr_id="NAS-001"))
        assert not r.valid
        assert any("nrr_id" in e for e in r.errors)

    def test_empty_id(self):
        r = validate(_make(nrr_id=""))
        assert not r.valid

    def test_wrong_prefix_lowercase(self):
        r = validate(_make(nrr_id="nrr-001"))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(nrr_id="NRR-999"))
        assert r.valid


# --- pipeline_version validation ---

class TestPipelineVersionValidation:
    def test_empty_version_fails(self):
        r = validate(_make(pipeline_version=""))
        assert not r.valid
        assert any("pipeline_version" in e for e in r.errors)

    def test_whitespace_only_fails(self):
        r = validate(_make(pipeline_version="   "))
        assert not r.valid

    def test_valid_version(self):
        r = validate(_make(pipeline_version="v1.2.3"))
        assert r.valid


# --- candidate_id validation ---

class TestCandidateIdValidation:
    def test_empty_candidate_id_fails(self):
        r = validate(_make(candidate_id=""))
        assert not r.valid
        assert any("candidate_id" in e for e in r.errors)

    def test_whitespace_only_fails(self):
        r = validate(_make(candidate_id="  "))
        assert not r.valid

    def test_valid_candidate_id(self):
        r = validate(_make(candidate_id="SEQ-001"))
        assert r.valid


# --- batch_id validation ---

class TestBatchIdValidation:
    def test_empty_batch_id_fails(self):
        r = validate(_make(batch_id=""))
        assert not r.valid
        assert any("batch_id" in e for e in r.errors)

    def test_whitespace_only_fails(self):
        r = validate(_make(batch_id="  "))
        assert not r.valid

    def test_valid_batch_id(self):
        r = validate(_make(batch_id="BATCH-999"))
        assert r.valid


# --- experiment_date validation ---

class TestExperimentDateValidation:
    def test_valid_date(self):
        r = validate(_make(experiment_date="2026-01-15"))
        assert r.valid

    def test_invalid_date_format(self):
        r = validate(_make(experiment_date="15/01/2026"))
        assert not r.valid
        assert any("experiment_date" in e for e in r.errors)

    def test_empty_date(self):
        r = validate(_make(experiment_date=""))
        assert not r.valid

    def test_partial_date_fails(self):
        r = validate(_make(experiment_date="2026-07"))
        assert not r.valid

    def test_text_date_fails(self):
        r = validate(_make(experiment_date="July 10 2026"))
        assert not r.valid


# --- stage_at_rejection validation ---

class TestStageValidation:
    def test_invalid_stage(self):
        r = validate(_make(stage_at_rejection="unknown_stage"))
        assert not r.valid
        assert any("stage_at_rejection" in e for e in r.errors)

    def test_empty_stage(self):
        r = validate(_make(stage_at_rejection=""))
        assert not r.valid

    def test_all_valid_stages(self):
        for stage in VALID_REJECTION_STAGES:
            r = validate(_make(stage_at_rejection=stage))
            assert not any("stage_at_rejection" in e for e in r.errors)


# --- rejection_reason validation ---

class TestRejectionReasonValidation:
    def test_invalid_reason(self):
        r = validate(_make(rejection_reason="unknown_reason"))
        assert not r.valid
        assert any("rejection_reason" in e for e in r.errors)

    def test_empty_reason(self):
        r = validate(_make(rejection_reason=""))
        assert not r.valid

    def test_all_valid_reasons(self):
        for reason in VALID_REJECTION_REASONS:
            r = validate(_make(rejection_reason=reason))
            assert not any("rejection_reason" in e for e in r.errors)


# --- rejection_confidence validation ---

class TestRejectionConfidenceValidation:
    def test_invalid_confidence(self):
        r = validate(_make(rejection_confidence="very_high"))
        assert not r.valid
        assert any("rejection_confidence" in e for e in r.errors)

    def test_empty_confidence(self):
        r = validate(_make(rejection_confidence=""))
        assert not r.valid

    def test_all_valid_confidences(self):
        for conf in VALID_REJECTION_CONFIDENCES:
            r = validate(_make(rejection_confidence=conf))
            assert not any("rejection_confidence" in e for e in r.errors)


# --- outcome_summary validation ---

class TestOutcomeSummaryValidation:
    def test_empty_summary_fails(self):
        r = validate(_make(outcome_summary=""))
        assert not r.valid
        assert any("outcome_summary" in e for e in r.errors)

    def test_whitespace_only_fails(self):
        r = validate(_make(outcome_summary="   "))
        assert not r.valid

    def test_too_long_fails(self):
        r = validate(_make(outcome_summary="x" * (OUTCOME_SUMMARY_MAX_LENGTH + 1)))
        assert not r.valid
        assert any("outcome_summary" in e for e in r.errors)

    def test_at_max_length_passes(self):
        r = validate(_make(outcome_summary="x" * OUTCOME_SUMMARY_MAX_LENGTH))
        assert r.valid

    def test_short_summary_passes(self):
        r = validate(_make(outcome_summary="Failed toxicity screen."))
        assert r.valid


# --- notes validation ---

class TestNotesValidation:
    def test_empty_notes_passes(self):
        r = validate(_make(notes=""))
        assert r.valid

    def test_notes_too_long_fails(self):
        r = validate(_make(notes="x" * (NOTES_MAX_LENGTH + 1)))
        assert not r.valid
        assert any("notes" in e for e in r.errors)

    def test_notes_at_max_passes(self):
        r = validate(_make(notes="x" * NOTES_MAX_LENGTH))
        assert r.valid


# --- Warnings ---

class TestWarnings:
    def test_not_final_high_confidence_warns(self):
        r = validate(_make(rejection_is_final=False, rejection_confidence="high"))
        assert any("rejection_is_final" in w or "provisional" in w for w in r.warnings)

    def test_manual_review_wrong_reason_warns(self):
        r = validate(_make(
            stage_at_rejection="manual_review",
            rejection_reason="low_score",
        ))
        assert any("manual_review" in w or "manual_exclusion" in w for w in r.warnings)

    def test_uncertain_final_warns(self):
        r = validate(_make(rejection_confidence="uncertain", rejection_is_final=True))
        assert any("uncertain" in w for w in r.warnings)

    def test_manual_exclusion_no_notes_warns(self):
        r = validate(_make(
            rejection_reason="manual_exclusion",
            notes="",
        ))
        assert any("manual_exclusion" in w or "notes" in w for w in r.warnings)

    def test_no_warnings_in_clean_entry(self):
        r = validate(_make())
        assert r.warnings == []

    def test_manual_exclusion_with_notes_no_warn(self):
        r = validate(_make(
            stage_at_rejection="manual_review",
            rejection_reason="manual_exclusion",
            notes="Expert panel rejected due to structural instability.",
        ))
        assert not any("manual_exclusion" in w and "notes" in w for w in r.warnings)


# --- validate_dict ---

class TestValidateDict:
    def _valid_dict(self, **kwargs):
        d = dict(
            nrr_id="NRR-001",
            pipeline_version="v0.10.14",
            candidate_id="CAND-042",
            batch_id="BATCH-007",
            experiment_date="2026-07-10",
            stage_at_rejection="toxicity_screen",
            rejection_reason="failed_toxicity",
            rejection_confidence="high",
            outcome_summary="Candidate failed ToxinPred screen.",
            rejection_is_final=True,
            notes="",
            dry_lab_only=True,
        )
        d.update(kwargs)
        return d

    def test_valid_dict_passes(self):
        r = validate_dict(self._valid_dict())
        assert r.valid

    def test_invalid_dict_fails(self):
        r = validate_dict(self._valid_dict(nrr_id="BAD-001"))
        assert not r.valid

    def test_missing_key_defaults_gracefully(self):
        r = validate_dict({})
        assert not r.valid

    def test_dict_errors_match_object(self):
        obj_r = validate(_make(nrr_id="BAD-001"))
        dict_r = validate_dict(self._valid_dict(nrr_id="BAD-001"))
        assert obj_r.valid == dict_r.valid


# --- Constants ---

class TestConstants:
    def test_nrr_prefix(self):
        assert NRR_PREFIX == "NRR-"

    def test_valid_stages_count(self):
        assert len(VALID_REJECTION_STAGES) == 7

    def test_valid_reasons_count(self):
        assert len(VALID_REJECTION_REASONS) == 9

    def test_valid_confidences_count(self):
        assert len(VALID_REJECTION_CONFIDENCES) == 4

    def test_summary_max_length(self):
        assert OUTCOME_SUMMARY_MAX_LENGTH == 400

    def test_notes_max_length(self):
        assert NOTES_MAX_LENGTH == 300

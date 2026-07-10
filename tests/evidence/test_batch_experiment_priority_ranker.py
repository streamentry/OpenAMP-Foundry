"""Tests for BatchExperimentPriorityRanker (BPR-) schema — Phase K K2."""

import pytest
from openamp_foundry.evidence.batch_experiment_priority_ranker import (
    BPR_PREFIX,
    CSR_PREFIX,
    MAX_SYNTHESIS_WAVE_WARNING,
    NOTES_MAX_LENGTH,
    PRIORITY_RATIONALE_MAX_LENGTH,
    VALID_PRIORITY_METHODS,
    BatchExperimentPriorityRanker,
    BatchExperimentPriorityRankerResult,
    validate,
    validate_dict,
)


def _make(**kwargs) -> BatchExperimentPriorityRanker:
    defaults = dict(
        bpr_id="BPR-001",
        pipeline_version="v0.10.17",
        batch_id="BATCH-007",
        csr_id="CSR-001",
        ranking_date="2026-07-10",
        priority_method="predicted_activity",
        top_priority_candidates=["CAND-001", "CAND-003", "CAND-007"],
        priority_rationale="Ranked by predicted MIC against S. aureus, filtered for novelty.",
        synthesis_wave=1,
        resource_constraint_considered=True,
        notes="",
    )
    defaults.update(kwargs)
    return BatchExperimentPriorityRanker(**defaults)


# --- Baseline valid ---

class TestValidBaseline:
    def test_valid_entry_passes(self):
        r = validate(_make())
        assert r.valid
        assert r.errors == []

    def test_valid_returns_result_type(self):
        r = validate(_make())
        assert isinstance(r, BatchExperimentPriorityRankerResult)

    def test_valid_with_notes(self):
        r = validate(_make(notes="Priority reviewed by synthesis team."))
        assert r.valid

    def test_valid_single_candidate(self):
        r = validate(_make(top_priority_candidates=["CAND-001"]))
        assert r.valid

    def test_valid_all_priority_methods(self):
        for method in VALID_PRIORITY_METHODS:
            r = validate(_make(priority_method=method, notes="documented"))
            assert r.valid or all("priority_method" not in e for e in r.errors)

    def test_valid_wave_2(self):
        r = validate(_make(synthesis_wave=2))
        assert r.valid


# --- bpr_id validation ---

class TestBprIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(bpr_id="CSR-001"))
        assert not r.valid
        assert any("bpr_id" in e for e in r.errors)

    def test_empty_id(self):
        r = validate(_make(bpr_id=""))
        assert not r.valid

    def test_lowercase_prefix(self):
        r = validate(_make(bpr_id="bpr-001"))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(bpr_id="BPR-999"))
        assert r.valid


# --- pipeline_version validation ---

class TestPipelineVersionValidation:
    def test_empty_fails(self):
        r = validate(_make(pipeline_version=""))
        assert not r.valid
        assert any("pipeline_version" in e for e in r.errors)

    def test_whitespace_fails(self):
        r = validate(_make(pipeline_version="   "))
        assert not r.valid

    def test_valid(self):
        r = validate(_make(pipeline_version="v2.0.0"))
        assert r.valid


# --- batch_id validation ---

class TestBatchIdValidation:
    def test_empty_fails(self):
        r = validate(_make(batch_id=""))
        assert not r.valid
        assert any("batch_id" in e for e in r.errors)

    def test_whitespace_fails(self):
        r = validate(_make(batch_id="  "))
        assert not r.valid

    def test_valid(self):
        r = validate(_make(batch_id="BATCH-999"))
        assert r.valid


# --- csr_id validation ---

class TestCsrIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(csr_id="BPR-001"))
        assert not r.valid
        assert any("csr_id" in e for e in r.errors)

    def test_empty_fails(self):
        r = validate(_make(csr_id=""))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(csr_id="CSR-013"))
        assert r.valid


# --- ranking_date validation ---

class TestRankingDateValidation:
    def test_valid_date(self):
        r = validate(_make(ranking_date="2026-01-15"))
        assert r.valid

    def test_invalid_format(self):
        r = validate(_make(ranking_date="10/07/2026"))
        assert not r.valid
        assert any("ranking_date" in e for e in r.errors)

    def test_empty_fails(self):
        r = validate(_make(ranking_date=""))
        assert not r.valid

    def test_partial_date_fails(self):
        r = validate(_make(ranking_date="2026-07"))
        assert not r.valid

    def test_text_date_fails(self):
        r = validate(_make(ranking_date="July 10 2026"))
        assert not r.valid


# --- priority_method validation ---

class TestPriorityMethodValidation:
    def test_invalid_method(self):
        r = validate(_make(priority_method="unknown_method"))
        assert not r.valid
        assert any("priority_method" in e for e in r.errors)

    def test_empty_method(self):
        r = validate(_make(priority_method=""))
        assert not r.valid

    def test_all_valid_methods(self):
        for m in VALID_PRIORITY_METHODS:
            r = validate(_make(priority_method=m, notes="documented"))
            assert not any("priority_method" in e for e in r.errors)


# --- top_priority_candidates validation ---

class TestCandidatesValidation:
    def test_empty_list_fails(self):
        r = validate(_make(top_priority_candidates=[]))
        assert not r.valid
        assert any("top_priority_candidates" in e for e in r.errors)

    def test_single_candidate_passes(self):
        r = validate(_make(top_priority_candidates=["CAND-001"]))
        assert r.valid

    def test_multiple_candidates_pass(self):
        r = validate(_make(top_priority_candidates=["A", "B", "C", "D", "E"]))
        assert r.valid


# --- priority_rationale validation ---

class TestPriorityRationaleValidation:
    def test_empty_fails(self):
        r = validate(_make(priority_rationale=""))
        assert not r.valid
        assert any("priority_rationale" in e for e in r.errors)

    def test_whitespace_fails(self):
        r = validate(_make(priority_rationale="   "))
        assert not r.valid

    def test_too_long_fails(self):
        r = validate(_make(priority_rationale="x" * (PRIORITY_RATIONALE_MAX_LENGTH + 1)))
        assert not r.valid
        assert any("priority_rationale" in e for e in r.errors)

    def test_at_max_passes(self):
        r = validate(_make(priority_rationale="x" * PRIORITY_RATIONALE_MAX_LENGTH))
        assert r.valid

    def test_short_passes(self):
        r = validate(_make(priority_rationale="Ranked by predicted MIC."))
        assert r.valid


# --- synthesis_wave validation ---

class TestSynthesisWaveValidation:
    def test_zero_fails(self):
        r = validate(_make(synthesis_wave=0))
        assert not r.valid
        assert any("synthesis_wave" in e for e in r.errors)

    def test_negative_fails(self):
        r = validate(_make(synthesis_wave=-1))
        assert not r.valid

    def test_one_passes(self):
        r = validate(_make(synthesis_wave=1))
        assert r.valid

    def test_five_passes(self):
        r = validate(_make(synthesis_wave=5))
        assert r.valid


# --- notes validation ---

class TestNotesValidation:
    def test_empty_notes_valid(self):
        r = validate(_make(notes=""))
        assert r.valid

    def test_too_long_fails(self):
        r = validate(_make(notes="x" * (NOTES_MAX_LENGTH + 1)))
        assert not r.valid
        assert any("notes" in e for e in r.errors)

    def test_at_max_passes(self):
        r = validate(_make(notes="x" * NOTES_MAX_LENGTH))
        assert r.valid


# --- Warnings ---

class TestWarnings:
    def test_resource_constraint_false_warns(self):
        r = validate(_make(resource_constraint_considered=False))
        assert any("resource_constraint" in w for w in r.warnings)

    def test_expert_ranked_no_notes_warns(self):
        r = validate(_make(priority_method="expert_ranked", notes=""))
        assert any("expert" in w for w in r.warnings)

    def test_high_synthesis_wave_warns(self):
        r = validate(_make(synthesis_wave=MAX_SYNTHESIS_WAVE_WARNING + 1))
        assert any("synthesis_wave" in w or "unusually high" in w for w in r.warnings)

    def test_no_warnings_in_clean_entry(self):
        r = validate(_make(notes="clean"))
        assert r.warnings == []

    def test_expert_ranked_with_notes_no_warn(self):
        r = validate(_make(priority_method="expert_ranked", notes="Expert panel ranked by clinical relevance."))
        assert not any("expert" in w for w in r.warnings)


# --- validate_dict ---

class TestValidateDict:
    def _valid_dict(self, **kwargs):
        d = dict(
            bpr_id="BPR-001",
            pipeline_version="v0.10.17",
            batch_id="BATCH-007",
            csr_id="CSR-001",
            ranking_date="2026-07-10",
            priority_method="predicted_activity",
            top_priority_candidates=["CAND-001", "CAND-003"],
            priority_rationale="Ranked by predicted MIC.",
            synthesis_wave=1,
            resource_constraint_considered=True,
            notes="",
        )
        d.update(kwargs)
        return d

    def test_valid_dict_passes(self):
        r = validate_dict(self._valid_dict())
        assert r.valid

    def test_invalid_prefix_fails(self):
        r = validate_dict(self._valid_dict(bpr_id="CSR-001"))
        assert not r.valid

    def test_empty_dict_fails(self):
        r = validate_dict({})
        assert not r.valid

    def test_zero_wave_fails(self):
        r = validate_dict(self._valid_dict(synthesis_wave=0))
        assert not r.valid


# --- Constants ---

class TestConstants:
    def test_bpr_prefix(self):
        assert BPR_PREFIX == "BPR-"

    def test_csr_prefix(self):
        assert CSR_PREFIX == "CSR-"

    def test_priority_methods_count(self):
        assert len(VALID_PRIORITY_METHODS) == 6

    def test_rationale_max_length(self):
        assert PRIORITY_RATIONALE_MAX_LENGTH == 400

    def test_notes_max_length(self):
        assert NOTES_MAX_LENGTH == 300

    def test_max_wave_warning(self):
        assert MAX_SYNTHESIS_WAVE_WARNING == 5

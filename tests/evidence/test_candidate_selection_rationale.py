"""Tests for CandidateSelectionRationale (CSR-) schema — Phase K K1."""

import pytest
from openamp_foundry.evidence.candidate_selection_rationale import (
    BSP_PREFIX,
    CSR_PREFIX,
    MAX_CANDIDATE_COUNT_WARNING,
    NOTES_MAX_LENGTH,
    RATIONALE_MAX_LENGTH,
    VALID_RANKING_METHODS,
    VALID_SELECTION_STRATEGIES,
    CandidateSelectionRationale,
    CandidateSelectionRationaleResult,
    validate,
    validate_dict,
)


def _make(**kwargs) -> CandidateSelectionRationale:
    defaults = dict(
        csr_id="CSR-001",
        pipeline_version="v0.10.16",
        batch_id="BATCH-007",
        bsp_id="BSP-007",
        selection_date="2026-07-10",
        selection_strategy="mixed",
        candidate_count=5,
        candidate_ids=["CAND-001", "CAND-002", "CAND-003", "CAND-004", "CAND-005"],
        ranking_method="composite_score",
        calibration_gate_passed=True,
        selection_rationale="Selected top-5 candidates by composite score after diversity filter.",
        notes="",
    )
    defaults.update(kwargs)
    return CandidateSelectionRationale(**defaults)


# --- Baseline valid ---

class TestValidBaseline:
    def test_valid_entry_passes(self):
        r = validate(_make())
        assert r.valid
        assert r.errors == []

    def test_valid_returns_result_type(self):
        r = validate(_make())
        assert isinstance(r, CandidateSelectionRationaleResult)

    def test_valid_with_notes(self):
        r = validate(_make(notes="Strategy rationale documented by lead researcher."))
        assert r.valid

    def test_valid_single_candidate(self):
        r = validate(_make(candidate_count=1, candidate_ids=["CAND-001"]))
        assert r.valid

    def test_valid_all_strategies(self):
        for strategy in VALID_SELECTION_STRATEGIES:
            r = validate(_make(selection_strategy=strategy))
            assert r.valid or all("strategy" not in e for e in r.errors)

    def test_valid_all_ranking_methods(self):
        for method in VALID_RANKING_METHODS:
            r = validate(_make(ranking_method=method, notes="documented"))
            assert r.valid or all("ranking_method" not in e for e in r.errors)


# --- csr_id validation ---

class TestCsrIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(csr_id="BSP-001"))
        assert not r.valid
        assert any("csr_id" in e for e in r.errors)

    def test_empty_id(self):
        r = validate(_make(csr_id=""))
        assert not r.valid

    def test_lowercase_prefix(self):
        r = validate(_make(csr_id="csr-001"))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(csr_id="CSR-999"))
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


# --- bsp_id validation ---

class TestBspIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(bsp_id="CSR-001"))
        assert not r.valid
        assert any("bsp_id" in e for e in r.errors)

    def test_empty_fails(self):
        r = validate(_make(bsp_id=""))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(bsp_id="BSP-013"))
        assert r.valid


# --- selection_date validation ---

class TestSelectionDateValidation:
    def test_valid_date(self):
        r = validate(_make(selection_date="2026-01-15"))
        assert r.valid

    def test_invalid_format(self):
        r = validate(_make(selection_date="10/07/2026"))
        assert not r.valid
        assert any("selection_date" in e for e in r.errors)

    def test_empty_date_fails(self):
        r = validate(_make(selection_date=""))
        assert not r.valid

    def test_partial_date_fails(self):
        r = validate(_make(selection_date="2026-07"))
        assert not r.valid

    def test_text_date_fails(self):
        r = validate(_make(selection_date="July 2026"))
        assert not r.valid


# --- selection_strategy validation ---

class TestSelectionStrategyValidation:
    def test_invalid_strategy(self):
        r = validate(_make(selection_strategy="random"))
        assert not r.valid
        assert any("selection_strategy" in e for e in r.errors)

    def test_empty_strategy(self):
        r = validate(_make(selection_strategy=""))
        assert not r.valid

    def test_all_valid_strategies(self):
        for s in VALID_SELECTION_STRATEGIES:
            r = validate(_make(selection_strategy=s))
            assert not any("selection_strategy" in e for e in r.errors)


# --- candidate_count validation ---

class TestCandidateCountValidation:
    def test_zero_fails(self):
        r = validate(_make(candidate_count=0, candidate_ids=[]))
        assert not r.valid
        assert any("candidate_count" in e for e in r.errors)

    def test_negative_fails(self):
        r = validate(_make(candidate_count=-1, candidate_ids=[]))
        assert not r.valid

    def test_count_mismatch_fails(self):
        r = validate(_make(candidate_count=3, candidate_ids=["A", "B"]))
        assert not r.valid
        assert any("candidate_ids" in e or "candidate_count" in e for e in r.errors)

    def test_valid_count_matches(self):
        r = validate(_make(candidate_count=2, candidate_ids=["A", "B"]))
        assert r.valid


# --- ranking_method validation ---

class TestRankingMethodValidation:
    def test_invalid_method(self):
        r = validate(_make(ranking_method="unknown_method"))
        assert not r.valid
        assert any("ranking_method" in e for e in r.errors)

    def test_empty_method(self):
        r = validate(_make(ranking_method=""))
        assert not r.valid

    def test_all_valid_methods(self):
        for m in VALID_RANKING_METHODS:
            r = validate(_make(ranking_method=m, notes="documented"))
            assert not any("ranking_method" in e for e in r.errors)


# --- calibration_gate_passed validation ---

class TestCalibrationGateValidation:
    def test_false_fails(self):
        r = validate(_make(calibration_gate_passed=False))
        assert not r.valid
        assert any("calibration_gate_passed" in e for e in r.errors)

    def test_true_passes(self):
        r = validate(_make(calibration_gate_passed=True))
        assert r.valid or all("calibration" not in e for e in r.errors)


# --- selection_rationale validation ---

class TestSelectionRationaleValidation:
    def test_empty_fails(self):
        r = validate(_make(selection_rationale=""))
        assert not r.valid
        assert any("selection_rationale" in e for e in r.errors)

    def test_whitespace_fails(self):
        r = validate(_make(selection_rationale="   "))
        assert not r.valid

    def test_too_long_fails(self):
        r = validate(_make(selection_rationale="x" * (RATIONALE_MAX_LENGTH + 1)))
        assert not r.valid
        assert any("selection_rationale" in e for e in r.errors)

    def test_at_max_passes(self):
        r = validate(_make(selection_rationale="x" * RATIONALE_MAX_LENGTH))
        assert r.valid

    def test_short_rationale_passes(self):
        r = validate(_make(selection_rationale="Top-5 by composite score."))
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
    def test_large_batch_warns(self):
        n = MAX_CANDIDATE_COUNT_WARNING + 1
        r = validate(_make(
            candidate_count=n,
            candidate_ids=[f"CAND-{i:03d}" for i in range(n)],
        ))
        assert any("unusually large" in w or "candidate_count" in w for w in r.warnings)

    def test_random_balanced_no_notes_warns(self):
        r = validate(_make(ranking_method="random_balanced", notes=""))
        assert any("random" in w for w in r.warnings)

    def test_expert_review_no_notes_warns(self):
        r = validate(_make(ranking_method="expert_review", notes=""))
        assert any("expert" in w for w in r.warnings)

    def test_no_warnings_in_clean_entry(self):
        r = validate(_make(notes="clean"))
        assert r.warnings == []

    def test_random_balanced_with_notes_no_warn(self):
        r = validate(_make(ranking_method="random_balanced", notes="Balanced random selected for diversity."))
        assert not any("random" in w for w in r.warnings)


# --- validate_dict ---

class TestValidateDict:
    def _valid_dict(self, **kwargs):
        d = dict(
            csr_id="CSR-001",
            pipeline_version="v0.10.16",
            batch_id="BATCH-007",
            bsp_id="BSP-007",
            selection_date="2026-07-10",
            selection_strategy="mixed",
            candidate_count=3,
            candidate_ids=["CAND-001", "CAND-002", "CAND-003"],
            ranking_method="composite_score",
            calibration_gate_passed=True,
            selection_rationale="Top-3 by composite score after diversity filter.",
            notes="",
        )
        d.update(kwargs)
        return d

    def test_valid_dict_passes(self):
        r = validate_dict(self._valid_dict())
        assert r.valid

    def test_invalid_prefix_fails(self):
        r = validate_dict(self._valid_dict(csr_id="BSP-001"))
        assert not r.valid

    def test_empty_dict_fails(self):
        r = validate_dict({})
        assert not r.valid

    def test_false_gate_fails(self):
        r = validate_dict(self._valid_dict(calibration_gate_passed=False))
        assert not r.valid


# --- Constants ---

class TestConstants:
    def test_csr_prefix(self):
        assert CSR_PREFIX == "CSR-"

    def test_bsp_prefix(self):
        assert BSP_PREFIX == "BSP-"

    def test_strategies_count(self):
        assert len(VALID_SELECTION_STRATEGIES) == 4

    def test_ranking_methods_count(self):
        assert len(VALID_RANKING_METHODS) == 6

    def test_rationale_max_length(self):
        assert RATIONALE_MAX_LENGTH == 400

    def test_notes_max_length(self):
        assert NOTES_MAX_LENGTH == 300

    def test_max_candidate_count_warning(self):
        assert MAX_CANDIDATE_COUNT_WARNING == 20

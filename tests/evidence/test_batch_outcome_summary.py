"""Tests for batch outcome summary schema — Phase P P3."""

import pytest
from openamp_foundry.evidence.batch_outcome_summary import (
    BatchOutcomeSummaryEntry,
    validate_batch_outcome_summary,
    validate_batch_outcome_summary_dict,
    BOS_PREFIX,
    BSP_PREFIX,
    OUTCOME_NOTES_MAX_LENGTH,
    UNTESTED_WARNING_THRESHOLD,
)


def _valid_entry(**kwargs) -> BatchOutcomeSummaryEntry:
    defaults = dict(
        bos_id="BOS-001",
        pipeline_version="v1.0.0",
        bsp_id="BSP-001",
        batch_id="BATCH-001",
        candidates_proposed=10,
        candidates_tested=10,
        candidates_active=3,
        candidates_inactive=7,
        is_synthetic=True,
        outcome_notes="Synthetic batch for testing.",
        reviewer="reviewer@example.com",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return BatchOutcomeSummaryEntry(**defaults)


class TestValidEntry:
    def test_valid_passes(self):
        r = validate_batch_outcome_summary(_valid_entry())
        assert r.passed
        assert r.errors == []

    def test_result_fields(self):
        r = validate_batch_outcome_summary(_valid_entry())
        assert r.bos_id == "BOS-001"
        assert r.bsp_id == "BSP-001"
        assert r.candidates_proposed == 10
        assert r.candidates_tested == 10
        assert r.candidates_active == 3
        assert r.candidates_inactive == 7
        assert r.candidates_untested == 0
        assert r.is_synthetic is True
        assert r.dry_lab_only is True

    def test_no_warnings_fully_tested(self):
        r = validate_batch_outcome_summary(_valid_entry())
        assert r.warnings == []

    def test_real_results_dry_lab_false(self):
        r = validate_batch_outcome_summary(
            _valid_entry(is_synthetic=False, dry_lab_only=False)
        )
        assert r.passed
        assert r.warnings == []

    def test_all_active(self):
        r = validate_batch_outcome_summary(
            _valid_entry(candidates_active=10, candidates_inactive=0)
        )
        assert r.passed

    def test_all_inactive(self):
        r = validate_batch_outcome_summary(
            _valid_entry(candidates_active=0, candidates_inactive=10)
        )
        assert r.passed
        assert any("no active" in w for w in r.warnings)

    def test_zero_candidates_tested(self):
        r = validate_batch_outcome_summary(
            _valid_entry(
                candidates_tested=0,
                candidates_active=0,
                candidates_inactive=0,
            )
        )
        assert r.passed

    def test_partial_testing_small_fraction_warns(self):
        r = validate_batch_outcome_summary(
            _valid_entry(
                candidates_proposed=10,
                candidates_tested=9,
                candidates_active=3,
                candidates_inactive=6,
            )
        )
        assert r.passed
        # 1/10 = 10% < 25% threshold → generic warning
        assert any("not tested" in w for w in r.warnings)

    def test_partial_testing_large_fraction_warns(self):
        r = validate_batch_outcome_summary(
            _valid_entry(
                candidates_proposed=10,
                candidates_tested=6,
                candidates_active=2,
                candidates_inactive=4,
            )
        )
        assert r.passed
        # 4/10 = 40% >= 25% threshold → calibration coverage warning
        assert any("calibration coverage" in w or "not tested" in w for w in r.warnings)

    def test_real_results_dry_lab_true_warns(self):
        r = validate_batch_outcome_summary(
            _valid_entry(is_synthetic=False, dry_lab_only=True)
        )
        assert r.passed
        assert any("dry_lab_only=True" in w or "dry_lab_only=False" in w for w in r.warnings)

    def test_empty_notes(self):
        r = validate_batch_outcome_summary(_valid_entry(outcome_notes=""))
        assert r.passed

    def test_max_length_notes(self):
        notes = "x" * OUTCOME_NOTES_MAX_LENGTH
        r = validate_batch_outcome_summary(_valid_entry(outcome_notes=notes))
        assert r.passed

    def test_candidates_untested_computed(self):
        r = validate_batch_outcome_summary(
            _valid_entry(
                candidates_proposed=10,
                candidates_tested=7,
                candidates_active=2,
                candidates_inactive=5,
            )
        )
        assert r.passed
        assert r.candidates_untested == 3

    def test_one_candidate(self):
        r = validate_batch_outcome_summary(
            _valid_entry(
                candidates_proposed=1,
                candidates_tested=1,
                candidates_active=1,
                candidates_inactive=0,
            )
        )
        assert r.passed


class TestBosIdValidation:
    def test_missing_prefix_fails(self):
        r = validate_batch_outcome_summary(_valid_entry(bos_id="001"))
        assert not r.passed
        assert any("bos_id" in e for e in r.errors)

    def test_wrong_prefix_fails(self):
        r = validate_batch_outcome_summary(_valid_entry(bos_id="BSP-001"))
        assert not r.passed

    def test_lowercase_prefix_fails(self):
        r = validate_batch_outcome_summary(_valid_entry(bos_id="bos-001"))
        assert not r.passed

    def test_prefix_only_passes(self):
        r = validate_batch_outcome_summary(_valid_entry(bos_id="BOS-"))
        assert r.passed


class TestBspIdValidation:
    def test_missing_bsp_prefix_fails(self):
        r = validate_batch_outcome_summary(_valid_entry(bsp_id="001"))
        assert not r.passed
        assert any("bsp_id" in e for e in r.errors)

    def test_wrong_prefix_fails(self):
        r = validate_batch_outcome_summary(_valid_entry(bsp_id="BOS-001"))
        assert not r.passed

    def test_correct_prefix_passes(self):
        r = validate_batch_outcome_summary(_valid_entry(bsp_id="BSP-999"))
        assert r.passed


class TestCandidateCountsValidation:
    def test_zero_proposed_fails(self):
        r = validate_batch_outcome_summary(
            _valid_entry(candidates_proposed=0, candidates_tested=0, candidates_active=0, candidates_inactive=0)
        )
        assert not r.passed
        assert any("candidates_proposed" in e for e in r.errors)

    def test_negative_proposed_fails(self):
        r = validate_batch_outcome_summary(
            _valid_entry(candidates_proposed=-1, candidates_tested=0, candidates_active=0, candidates_inactive=0)
        )
        assert not r.passed

    def test_negative_tested_fails(self):
        r = validate_batch_outcome_summary(
            _valid_entry(candidates_tested=-1, candidates_active=0, candidates_inactive=0)
        )
        assert not r.passed
        assert any("candidates_tested" in e for e in r.errors)

    def test_negative_active_fails(self):
        r = validate_batch_outcome_summary(
            _valid_entry(candidates_active=-1, candidates_inactive=11)
        )
        assert not r.passed
        assert any("candidates_active" in e for e in r.errors)

    def test_negative_inactive_fails(self):
        r = validate_batch_outcome_summary(
            _valid_entry(candidates_active=11, candidates_inactive=-1)
        )
        assert not r.passed
        assert any("candidates_inactive" in e for e in r.errors)

    def test_active_plus_inactive_not_equal_tested_fails(self):
        r = validate_batch_outcome_summary(
            _valid_entry(candidates_tested=10, candidates_active=4, candidates_inactive=4)
        )
        assert not r.passed
        assert any("must equal" in e for e in r.errors)

    def test_tested_exceeds_proposed_fails(self):
        r = validate_batch_outcome_summary(
            _valid_entry(
                candidates_proposed=5,
                candidates_tested=6,
                candidates_active=3,
                candidates_inactive=3,
            )
        )
        assert not r.passed
        assert any("cannot exceed" in e for e in r.errors)


class TestSyntheticBoundaryValidation:
    def test_synthetic_true_dry_lab_true_passes(self):
        r = validate_batch_outcome_summary(
            _valid_entry(is_synthetic=True, dry_lab_only=True)
        )
        assert r.passed

    def test_synthetic_true_dry_lab_false_fails(self):
        r = validate_batch_outcome_summary(
            _valid_entry(is_synthetic=True, dry_lab_only=False)
        )
        assert not r.passed
        assert any("is_synthetic=True" in e for e in r.errors)

    def test_real_dry_lab_false_passes(self):
        r = validate_batch_outcome_summary(
            _valid_entry(is_synthetic=False, dry_lab_only=False)
        )
        assert r.passed

    def test_real_dry_lab_true_warns(self):
        r = validate_batch_outcome_summary(
            _valid_entry(is_synthetic=False, dry_lab_only=True)
        )
        assert r.passed
        assert r.warnings


class TestOutcomeNotesValidation:
    def test_notes_too_long_fails(self):
        notes = "n" * (OUTCOME_NOTES_MAX_LENGTH + 1)
        r = validate_batch_outcome_summary(_valid_entry(outcome_notes=notes))
        assert not r.passed
        assert any("outcome_notes" in e for e in r.errors)

    def test_notes_at_limit_passes(self):
        notes = "n" * OUTCOME_NOTES_MAX_LENGTH
        r = validate_batch_outcome_summary(_valid_entry(outcome_notes=notes))
        assert r.passed


class TestDictValidation:
    def _valid_dict(self, **kwargs):
        d = dict(
            bos_id="BOS-001",
            pipeline_version="v1.0.0",
            bsp_id="BSP-001",
            batch_id="BATCH-001",
            candidates_proposed=10,
            candidates_tested=10,
            candidates_active=3,
            candidates_inactive=7,
            is_synthetic=True,
            outcome_notes="note",
            reviewer="r@example.com",
            dry_lab_only=True,
        )
        d.update(kwargs)
        return d

    def test_valid_dict_passes(self):
        r = validate_batch_outcome_summary_dict(self._valid_dict())
        assert r.passed

    def test_missing_field_fails(self):
        d = self._valid_dict()
        del d["bsp_id"]
        r = validate_batch_outcome_summary_dict(d)
        assert not r.passed
        assert any("missing" in e for e in r.errors)

    def test_missing_multiple_fields(self):
        d = self._valid_dict()
        del d["bsp_id"]
        del d["is_synthetic"]
        r = validate_batch_outcome_summary_dict(d)
        assert not r.passed

    def test_dry_lab_only_defaults_to_true(self):
        d = self._valid_dict()
        del d["dry_lab_only"]
        r = validate_batch_outcome_summary_dict(d)
        assert r.passed
        assert r.dry_lab_only is True

    def test_synthetic_true_dry_lab_false_in_dict_fails(self):
        r = validate_batch_outcome_summary_dict(
            self._valid_dict(is_synthetic=True, dry_lab_only=False)
        )
        assert not r.passed

    def test_mismatch_counts_in_dict_fails(self):
        r = validate_batch_outcome_summary_dict(
            self._valid_dict(candidates_active=5, candidates_inactive=5, candidates_tested=8)
        )
        assert not r.passed


class TestMultipleErrors:
    def test_multiple_errors_accumulated(self):
        r = validate_batch_outcome_summary(
            _valid_entry(
                bos_id="wrong",
                bsp_id="wrong",
                candidates_proposed=0,
                candidates_tested=-1,
                candidates_active=0,
                candidates_inactive=0,
                is_synthetic=True,
                dry_lab_only=False,
            )
        )
        assert not r.passed
        assert len(r.errors) >= 4


class TestConstants:
    def test_bos_prefix(self):
        assert BOS_PREFIX == "BOS-"

    def test_bsp_prefix(self):
        assert BSP_PREFIX == "BSP-"

    def test_notes_max_length(self):
        assert OUTCOME_NOTES_MAX_LENGTH == 400

    def test_untested_threshold(self):
        assert UNTESTED_WARNING_THRESHOLD == 0.25

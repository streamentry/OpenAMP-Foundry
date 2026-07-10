"""Tests for F7 negative result calibration link schema."""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.negative_result_calibration_link import (
    CAL_ID_PREFIX,
    LINK_ID_PREFIX,
    MIN_LINK_RATIONALE_LENGTH,
    MIN_NRR_IDS,
    NRR_ID_PREFIX,
    VALID_LINK_STATUSES,
    VALID_LINK_TYPES,
    LinkValidationResult,
    NegativeResultCalibrationLink,
    format_negative_result_calibration_link,
    validate_negative_result_calibration_link,
)


def _make_link(**kwargs) -> NegativeResultCalibrationLink:
    defaults = dict(
        link_id="NCL-2026-001",
        nrr_ids=["NRR-001", "NRR-002"],
        intake_id="CAL-2026-001",
        linked_at="2026-01-01T00:00:00Z",
        link_type="batch_failure_feedback",
        link_rationale="Both candidates failed hemolysis screen; pattern indicates charge bias.",
        batch_coverage_fraction=1.0,
        all_nrrs_linked=True,
        link_status="submitted",
        notes="",
    )
    defaults.update(kwargs)
    return NegativeResultCalibrationLink(**defaults)


class TestLinkConstants:
    def test_link_id_prefix(self):
        assert LINK_ID_PREFIX == "NCL-"

    def test_nrr_id_prefix(self):
        assert NRR_ID_PREFIX == "NRR-"

    def test_cal_id_prefix(self):
        assert CAL_ID_PREFIX == "CAL-"

    def test_min_nrr_ids(self):
        assert MIN_NRR_IDS >= 1

    def test_min_rationale_length(self):
        assert MIN_LINK_RATIONALE_LENGTH >= 10

    def test_valid_statuses_is_frozenset(self):
        assert isinstance(VALID_LINK_STATUSES, frozenset)

    def test_valid_types_is_frozenset(self):
        assert isinstance(VALID_LINK_TYPES, frozenset)

    def test_pending_in_statuses(self):
        assert "pending" in VALID_LINK_STATUSES

    def test_submitted_in_statuses(self):
        assert "submitted" in VALID_LINK_STATUSES

    def test_accepted_in_statuses(self):
        assert "accepted" in VALID_LINK_STATUSES

    def test_rejected_in_statuses(self):
        assert "rejected" in VALID_LINK_STATUSES

    def test_superseded_in_statuses(self):
        assert "superseded" in VALID_LINK_STATUSES

    def test_batch_failure_in_types(self):
        assert "batch_failure_feedback" in VALID_LINK_TYPES

    def test_single_candidate_in_types(self):
        assert "single_candidate_rejection" in VALID_LINK_TYPES

    def test_systematic_in_types(self):
        assert "systematic_failure_pattern" in VALID_LINK_TYPES


class TestLinkDataclass:
    def test_creates_successfully(self):
        link = _make_link()
        assert link.link_id == "NCL-2026-001"

    def test_nrr_ids_stored(self):
        link = _make_link(nrr_ids=["NRR-A", "NRR-B"])
        assert link.nrr_ids == ["NRR-A", "NRR-B"]

    def test_intake_id_stored(self):
        link = _make_link()
        assert link.intake_id == "CAL-2026-001"

    def test_all_nrrs_linked_stored(self):
        link = _make_link()
        assert link.all_nrrs_linked is True

    def test_coverage_stored(self):
        link = _make_link(batch_coverage_fraction=0.75, all_nrrs_linked=False)
        assert link.batch_coverage_fraction == 0.75


class TestValidateLink:
    def test_valid_link_passes(self):
        link = _make_link()
        result = validate_negative_result_calibration_link(link)
        assert result.is_valid is True

    def test_valid_link_no_violations(self):
        link = _make_link()
        result = validate_negative_result_calibration_link(link)
        assert result.violations == []

    def test_result_type(self):
        link = _make_link()
        result = validate_negative_result_calibration_link(link)
        assert isinstance(result, LinkValidationResult)

    def test_link_id_in_result(self):
        link = _make_link()
        result = validate_negative_result_calibration_link(link)
        assert result.link_id == "NCL-2026-001"

    def test_summary_nonempty(self):
        link = _make_link()
        result = validate_negative_result_calibration_link(link)
        assert len(result.validation_summary) > 0

    def test_bad_link_prefix_fails(self):
        link = _make_link(link_id="BAD-001")
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_prefix_only_link_id_fails(self):
        link = _make_link(link_id="NCL-")
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_bad_intake_prefix_fails(self):
        link = _make_link(intake_id="INT-001")
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_empty_nrr_ids_fails(self):
        link = _make_link(nrr_ids=[], batch_coverage_fraction=0.0, all_nrrs_linked=False)
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_bad_nrr_prefix_fails(self):
        link = _make_link(nrr_ids=["BAD-001", "NRR-002"])
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_duplicate_nrr_ids_fails(self):
        link = _make_link(nrr_ids=["NRR-001", "NRR-001"])
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_empty_linked_at_fails(self):
        link = _make_link(linked_at="")
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_invalid_link_type_fails(self):
        link = _make_link(link_type="random_rejection")
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_short_rationale_fails(self):
        link = _make_link(link_rationale="short")
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_empty_rationale_fails(self):
        link = _make_link(link_rationale="")
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_coverage_below_zero_fails(self):
        link = _make_link(batch_coverage_fraction=-0.1, all_nrrs_linked=False)
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_coverage_above_one_fails(self):
        link = _make_link(batch_coverage_fraction=1.1, all_nrrs_linked=False)
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_invalid_status_fails(self):
        link = _make_link(link_status="approved_by_committee")
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_all_linked_true_but_coverage_not_one_fails(self):
        link = _make_link(all_nrrs_linked=True, batch_coverage_fraction=0.8)
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_coverage_one_but_all_linked_false_fails(self):
        link = _make_link(batch_coverage_fraction=1.0, all_nrrs_linked=False)
        result = validate_negative_result_calibration_link(link)
        assert not result.is_valid

    def test_partial_coverage_passes(self):
        link = _make_link(batch_coverage_fraction=0.6, all_nrrs_linked=False)
        result = validate_negative_result_calibration_link(link)
        assert result.is_valid

    def test_zero_coverage_passes(self):
        link = _make_link(batch_coverage_fraction=0.0, all_nrrs_linked=False)
        result = validate_negative_result_calibration_link(link)
        assert result.is_valid

    def test_all_link_types_pass(self):
        for lt in VALID_LINK_TYPES:
            link = _make_link(link_type=lt)
            result = validate_negative_result_calibration_link(link)
            assert result.is_valid, f"link_type {lt!r} should pass"

    def test_all_statuses_pass(self):
        for status in VALID_LINK_STATUSES:
            link = _make_link(link_status=status)
            result = validate_negative_result_calibration_link(link)
            assert result.is_valid, f"status {status!r} should pass"

    def test_rejected_status_empty_notes_warns(self):
        link = _make_link(link_status="rejected", notes="")
        result = validate_negative_result_calibration_link(link)
        assert result.is_valid
        assert len(result.warnings) > 0

    def test_rejected_status_with_notes_no_warning(self):
        link = _make_link(link_status="rejected", notes="Intake not open for this batch.")
        result = validate_negative_result_calibration_link(link)
        assert result.is_valid
        assert not any("rejected" in w for w in result.warnings)

    def test_many_nrr_ids_pass(self):
        ids = [f"NRR-{i:04d}" for i in range(20)]
        link = _make_link(nrr_ids=ids)
        result = validate_negative_result_calibration_link(link)
        assert result.is_valid

    def test_single_nrr_id_passes(self):
        link = _make_link(nrr_ids=["NRR-001"])
        result = validate_negative_result_calibration_link(link)
        assert result.is_valid

    def test_violations_is_list(self):
        result = validate_negative_result_calibration_link(_make_link(link_id="BAD"))
        assert isinstance(result.violations, list)

    def test_warnings_is_list(self):
        result = validate_negative_result_calibration_link(_make_link())
        assert isinstance(result.warnings, list)

    def test_valid_summary_contains_nrr_count(self):
        link = _make_link()
        result = validate_negative_result_calibration_link(link)
        assert "2" in result.validation_summary

    def test_invalid_summary_mentions_violations(self):
        link = _make_link(link_id="WRONG")
        result = validate_negative_result_calibration_link(link)
        assert "violation" in result.validation_summary.lower()


class TestFormatLink:
    def setup_method(self):
        self.link = _make_link()
        self.formatted = format_negative_result_calibration_link(self.link)

    def test_returns_string(self):
        assert isinstance(self.formatted, str)

    def test_contains_link_id(self):
        assert "NCL-2026-001" in self.formatted

    def test_contains_link_type(self):
        assert "batch_failure_feedback" in self.formatted

    def test_contains_status(self):
        assert "submitted" in self.formatted

    def test_contains_intake_id(self):
        assert "CAL-2026-001" in self.formatted

    def test_contains_nrr_ids(self):
        assert "NRR-001" in self.formatted
        assert "NRR-002" in self.formatted

    def test_contains_coverage(self):
        assert "100%" in self.formatted

    def test_contains_all_nrrs_linked(self):
        assert "True" in self.formatted

    def test_contains_rationale(self):
        assert "hemolysis" in self.formatted

    def test_notes_present_when_nonempty(self):
        link = _make_link(notes="See linked intake for context.")
        text = format_negative_result_calibration_link(link)
        assert "See linked intake" in text

    def test_notes_absent_when_empty(self):
        link = _make_link(notes="")
        text = format_negative_result_calibration_link(link)
        assert "Notes:" not in text

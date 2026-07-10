"""Tests for RecalibrationRejectionSummary schema — Phase G G2.

Exactly 63 tests: valid baseline + each validation rule + edge cases + warnings.
"""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.recalibration_rejection_summary import (
    NOTES_MAX_LENGTH,
    RRS_PREFIX,
    REFUSAL_RATE_TOLERANCE,
    SUMMARY_MAX_LENGTH,
    VALID_GATE_STATUSES,
    VALID_TOP_REFUSAL_REASONS,
    RecalibrationRejectionSummary,
    validate,
    validate_dict,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_summary(**overrides) -> RecalibrationRejectionSummary:
    defaults = dict(
        rrs_id="RRS-20240315-001",
        pipeline_version="v2.1.0",
        period_start="2024-01-01",
        period_end="2024-03-31",
        total_checkpoints_reviewed=10,
        total_refused=3,
        total_approved=7,
        refusal_rate=0.30,
        top_refusal_reason="effect_within_noise",
        gate_status="active",
        all_refusals_have_rrf=True,
        summary="3 of 10 checkpoints refused: noise-within-tolerance (2), insufficient data (1).",
        notes="",
    )
    defaults.update(overrides)
    return RecalibrationRejectionSummary(**defaults)


def _valid() -> RecalibrationRejectionSummary:
    return _valid_summary()


def _errors(s):
    return [e for e in validate(s) if not e.startswith("WARNING:")]


def _warns(s):
    return [e for e in validate(s) if e.startswith("WARNING:")]


# ---------------------------------------------------------------------------
# Group 1: Valid baseline (3 tests)
# ---------------------------------------------------------------------------

class TestValidBaseline:
    def test_valid_returns_no_errors(self):
        assert _errors(_valid()) == []

    def test_valid_with_notes(self):
        s = _valid_summary(notes="Safety officer reviewed.")
        assert _errors(s) == []

    def test_zero_refusals_valid_except_warning(self):
        s = _valid_summary(
            total_refused=0,
            total_approved=10,
            refusal_rate=0.0,
            top_refusal_reason="none_refused",
        )
        assert _errors(s) == []


# ---------------------------------------------------------------------------
# Group 2: Rule 1 — rrs_id prefix (4 tests)
# ---------------------------------------------------------------------------

class TestRrsIdPrefix:
    def test_wrong_prefix_rejected(self):
        s = _valid_summary(rrs_id="RRF-001")
        assert any("rrs_id" in e for e in _errors(s))

    def test_lowercase_prefix_rejected(self):
        s = _valid_summary(rrs_id="rrs-001")
        assert any("rrs_id" in e for e in _errors(s))

    def test_no_prefix_rejected(self):
        s = _valid_summary(rrs_id="001")
        assert any("rrs_id" in e for e in _errors(s))

    def test_correct_prefix_accepted(self):
        s = _valid_summary(rrs_id="RRS-2024-001")
        assert _errors(s) == []


# ---------------------------------------------------------------------------
# Group 3: Rule 2 — pipeline_version (3 tests)
# ---------------------------------------------------------------------------

class TestPipelineVersion:
    def test_empty_rejected(self):
        s = _valid_summary(pipeline_version="")
        assert any("pipeline_version" in e for e in _errors(s))

    def test_whitespace_only_rejected(self):
        s = _valid_summary(pipeline_version="   ")
        assert any("pipeline_version" in e for e in _errors(s))

    def test_valid_version(self):
        s = _valid_summary(pipeline_version="v3.0.1")
        assert _errors(s) == []


# ---------------------------------------------------------------------------
# Group 4: Rule 3 — period_start ISO format (3 tests)
# ---------------------------------------------------------------------------

class TestPeriodStart:
    def test_invalid_format_rejected(self):
        s = _valid_summary(period_start="Jan 2024")
        assert any("period_start" in e for e in _errors(s))

    def test_wrong_separator_rejected(self):
        s = _valid_summary(period_start="2024/01/01")
        assert any("period_start" in e for e in _errors(s))

    def test_valid_iso_date(self):
        s = _valid_summary(period_start="2024-01-15")
        assert _errors(s) == []


# ---------------------------------------------------------------------------
# Group 5: Rule 4 — period_end ISO format (3 tests)
# ---------------------------------------------------------------------------

class TestPeriodEnd:
    def test_invalid_format_rejected(self):
        s = _valid_summary(period_end="Q1 2024")
        assert any("period_end" in e for e in _errors(s))

    def test_empty_rejected(self):
        s = _valid_summary(period_end="")
        assert any("period_end" in e for e in _errors(s))

    def test_valid_iso_date(self):
        s = _valid_summary(period_end="2024-06-30")
        assert _errors(s) == []


# ---------------------------------------------------------------------------
# Group 6: Rule 5 — total_checkpoints_reviewed >= 1 (3 tests)
# ---------------------------------------------------------------------------

class TestTotalCheckpointsReviewed:
    def test_zero_rejected(self):
        s = _valid_summary(
            total_checkpoints_reviewed=0,
            total_refused=0,
            total_approved=0,
            refusal_rate=0.0,
        )
        assert any("total_checkpoints_reviewed" in e for e in _errors(s))

    def test_negative_rejected(self):
        s = _valid_summary(
            total_checkpoints_reviewed=-1,
            total_refused=0,
            total_approved=0,
            refusal_rate=0.0,
        )
        assert any("total_checkpoints_reviewed" in e for e in _errors(s))

    def test_one_accepted(self):
        s = _valid_summary(
            total_checkpoints_reviewed=1,
            total_refused=1,
            total_approved=0,
            refusal_rate=1.0,
        )
        assert _errors(s) == []


# ---------------------------------------------------------------------------
# Group 7: Rule 6 — total_refused bounds (3 tests)
# ---------------------------------------------------------------------------

class TestTotalRefused:
    def test_negative_rejected(self):
        s = _valid_summary(
            total_refused=-1,
            total_approved=11,
            refusal_rate=0.0,
        )
        assert any("total_refused" in e for e in _errors(s))

    def test_exceeds_total_rejected(self):
        s = _valid_summary(
            total_refused=11,
            total_approved=0,
            refusal_rate=1.1,
        )
        assert any("total_refused" in e for e in _errors(s))

    def test_exactly_total_accepted(self):
        s = _valid_summary(
            total_refused=10,
            total_approved=0,
            refusal_rate=1.0,
        )
        assert _errors(s) == []


# ---------------------------------------------------------------------------
# Group 8: Rule 7 — total_approved bounds (3 tests)
# ---------------------------------------------------------------------------

class TestTotalApproved:
    def test_negative_rejected(self):
        s = _valid_summary(
            total_refused=10,
            total_approved=-1,
            refusal_rate=1.0,
        )
        assert any("total_approved" in e for e in _errors(s))

    def test_exceeds_total_rejected(self):
        s = _valid_summary(
            total_refused=0,
            total_approved=11,
            refusal_rate=0.0,
        )
        assert any("total_approved" in e for e in _errors(s))

    def test_exactly_total_accepted(self):
        s = _valid_summary(
            total_refused=0,
            total_approved=10,
            refusal_rate=0.0,
            top_refusal_reason="none_refused",
        )
        assert _errors(s) == []


# ---------------------------------------------------------------------------
# Group 9: Rule 8 — refused + approved == total (3 tests)
# ---------------------------------------------------------------------------

class TestRefusedPlusApprovedEqualsTotal:
    def test_mismatch_rejected(self):
        s = _valid_summary(
            total_checkpoints_reviewed=10,
            total_refused=3,
            total_approved=6,
            refusal_rate=0.3,
        )
        assert any("must equal" in e for e in _errors(s))

    def test_exact_match_accepted(self):
        s = _valid_summary(
            total_checkpoints_reviewed=10,
            total_refused=4,
            total_approved=6,
            refusal_rate=0.4,
        )
        assert _errors(s) == []

    def test_all_refused_accepted(self):
        s = _valid_summary(
            total_checkpoints_reviewed=5,
            total_refused=5,
            total_approved=0,
            refusal_rate=1.0,
        )
        assert _errors(s) == []


# ---------------------------------------------------------------------------
# Group 10: Rule 9 — refusal_rate in [0, 1] (3 tests)
# ---------------------------------------------------------------------------

class TestRefusalRateRange:
    def test_negative_rejected(self):
        s = _valid_summary(refusal_rate=-0.1)
        assert any("refusal_rate" in e for e in _errors(s))

    def test_above_one_rejected(self):
        s = _valid_summary(refusal_rate=1.1)
        assert any("refusal_rate" in e for e in _errors(s))

    def test_zero_accepted(self):
        s = _valid_summary(
            total_refused=0,
            total_approved=10,
            refusal_rate=0.0,
            top_refusal_reason="none_refused",
        )
        assert _errors(s) == []


# ---------------------------------------------------------------------------
# Group 11: Rule 10 — refusal_rate consistency (4 tests)
# ---------------------------------------------------------------------------

class TestRefusalRateConsistency:
    def test_inconsistent_rate_rejected(self):
        s = _valid_summary(
            total_checkpoints_reviewed=10,
            total_refused=3,
            total_approved=7,
            refusal_rate=0.5,
        )
        assert any("inconsistent" in e for e in _errors(s))

    def test_within_tolerance_accepted(self):
        s = _valid_summary(
            total_checkpoints_reviewed=10,
            total_refused=3,
            total_approved=7,
            refusal_rate=0.305,
        )
        assert _errors(s) == []

    def test_exact_rate_accepted(self):
        s = _valid_summary(
            total_checkpoints_reviewed=10,
            total_refused=3,
            total_approved=7,
            refusal_rate=0.30,
        )
        assert _errors(s) == []

    def test_just_outside_tolerance_rejected(self):
        s = _valid_summary(
            total_checkpoints_reviewed=10,
            total_refused=3,
            total_approved=7,
            refusal_rate=0.315,
        )
        assert any("inconsistent" in e for e in _errors(s))


# ---------------------------------------------------------------------------
# Group 12: Rule 11 — top_refusal_reason vocabulary (4 tests)
# ---------------------------------------------------------------------------

class TestTopRefusalReason:
    def test_invalid_reason_rejected(self):
        s = _valid_summary(top_refusal_reason="made_up_reason")
        assert any("top_refusal_reason" in e for e in _errors(s))

    def test_empty_rejected(self):
        s = _valid_summary(top_refusal_reason="")
        assert any("top_refusal_reason" in e for e in _errors(s))

    @pytest.mark.parametrize("reason", sorted(VALID_TOP_REFUSAL_REASONS))
    def test_all_valid_reasons_accepted(self, reason):
        s = _valid_summary(top_refusal_reason=reason)
        assert _errors(s) == []


# ---------------------------------------------------------------------------
# Group 13: Rule 12 — gate_status vocabulary (4 tests)
# ---------------------------------------------------------------------------

class TestGateStatus:
    def test_invalid_status_rejected(self):
        s = _valid_summary(gate_status="offline")
        assert any("gate_status" in e for e in _errors(s))

    def test_empty_rejected(self):
        s = _valid_summary(gate_status="")
        assert any("gate_status" in e for e in _errors(s))

    @pytest.mark.parametrize("status", sorted(VALID_GATE_STATUSES))
    def test_all_valid_statuses_accepted(self, status):
        s = _valid_summary(gate_status=status)
        assert _errors(s) == []


# ---------------------------------------------------------------------------
# Group 14: Rule 13 — all_refusals_have_rrf=True (3 tests)
# ---------------------------------------------------------------------------

class TestAllRefusalsHaveRrf:
    def test_false_rejected(self):
        s = _valid_summary(all_refusals_have_rrf=False)
        assert any("all_refusals_have_rrf" in e for e in _errors(s))

    def test_true_accepted(self):
        s = _valid_summary(all_refusals_have_rrf=True)
        assert _errors(s) == []

    def test_zero_refusals_still_requires_true(self):
        s = _valid_summary(
            total_refused=0,
            total_approved=10,
            refusal_rate=0.0,
            top_refusal_reason="none_refused",
            all_refusals_have_rrf=False,
        )
        assert any("all_refusals_have_rrf" in e for e in _errors(s))


# ---------------------------------------------------------------------------
# Group 15: Rule 14 — summary (3 tests)
# ---------------------------------------------------------------------------

class TestSummary:
    def test_empty_rejected(self):
        s = _valid_summary(summary="")
        assert any("summary" in e for e in _errors(s))

    def test_too_long_rejected(self):
        s = _valid_summary(summary="x" * (SUMMARY_MAX_LENGTH + 1))
        assert any("summary" in e for e in _errors(s))

    def test_exactly_at_limit_accepted(self):
        s = _valid_summary(summary="x" * SUMMARY_MAX_LENGTH)
        assert _errors(s) == []


# ---------------------------------------------------------------------------
# Group 16: Rule 15 — notes length (3 tests)
# ---------------------------------------------------------------------------

class TestNotesLength:
    def test_too_long_rejected(self):
        s = _valid_summary(notes="n" * (NOTES_MAX_LENGTH + 1))
        assert any("notes" in e for e in _errors(s))

    def test_exactly_at_limit_accepted(self):
        s = _valid_summary(notes="n" * NOTES_MAX_LENGTH)
        assert _errors(s) == []

    def test_empty_notes_accepted(self):
        s = _valid_summary(notes="")
        assert _errors(s) == []


# ---------------------------------------------------------------------------
# Group 17: Warnings (6 tests)
# ---------------------------------------------------------------------------

class TestWarnings:
    def test_high_refusal_rate_triggers_warning(self):
        s = _valid_summary(
            total_refused=9,
            total_approved=1,
            refusal_rate=0.9,
        )
        warns = _warns(s)
        assert any("refusal_rate" in w for w in warns)

    def test_zero_refusals_triggers_warning(self):
        s = _valid_summary(
            total_refused=0,
            total_approved=10,
            refusal_rate=0.0,
            top_refusal_reason="none_refused",
        )
        warns = _warns(s)
        assert any("total_refused is 0" in w for w in warns)

    def test_empty_notes_triggers_warning(self):
        s = _valid_summary(notes="")
        warns = _warns(s)
        assert any("notes" in w.lower() for w in warns)

    def test_notes_present_suppresses_notes_warning(self):
        s = _valid_summary(notes="Reviewed by safety officer.")
        warns = _warns(s)
        assert not any("notes is empty" in w for w in warns)

    def test_moderate_refusal_rate_no_warning(self):
        s = _valid_summary(
            total_refused=5,
            total_approved=5,
            refusal_rate=0.5,
        )
        warns = _warns(s)
        assert not any("refusal_rate" in w for w in warns)

    def test_at_high_refusal_threshold_boundary(self):
        s = _valid_summary(
            total_refused=9,
            total_approved=1,
            refusal_rate=0.9,
        )
        warns = _warns(s)
        assert any("refusal_rate" in w for w in warns)


# ---------------------------------------------------------------------------
# Group 18: validate_dict (4 tests)
# ---------------------------------------------------------------------------

class TestValidateDict:
    def test_valid_dict_returns_no_errors(self):
        data = dict(
            rrs_id="RRS-20240315-001",
            pipeline_version="v2.1.0",
            period_start="2024-01-01",
            period_end="2024-03-31",
            total_checkpoints_reviewed=10,
            total_refused=3,
            total_approved=7,
            refusal_rate=0.30,
            top_refusal_reason="effect_within_noise",
            gate_status="active",
            all_refusals_have_rrf=True,
            summary="Gate active; 3/10 refused for valid documented reasons.",
        )
        errs = [e for e in validate_dict(data) if not e.startswith("WARNING:")]
        assert errs == []

    def test_missing_required_field_returns_error(self):
        data = dict(rrs_id="RRS-001", pipeline_version="v1.0")
        result = validate_dict(data)
        assert any("Schema construction error" in e for e in result)

    def test_invalid_field_caught_by_dict_validator(self):
        data = dict(
            rrs_id="WRONG-001",
            pipeline_version="v1.0",
            period_start="2024-01-01",
            period_end="2024-03-31",
            total_checkpoints_reviewed=5,
            total_refused=2,
            total_approved=3,
            refusal_rate=0.4,
            top_refusal_reason="effect_within_noise",
            gate_status="active",
            all_refusals_have_rrf=True,
            summary="Gate summary.",
        )
        result = validate_dict(data)
        assert any("rrs_id" in e for e in result)

    def test_extra_notes_in_dict(self):
        data = dict(
            rrs_id="RRS-20240315-002",
            pipeline_version="v2.1.0",
            period_start="2024-01-01",
            period_end="2024-03-31",
            total_checkpoints_reviewed=8,
            total_refused=2,
            total_approved=6,
            refusal_rate=0.25,
            top_refusal_reason="insufficient_data",
            gate_status="active",
            all_refusals_have_rrf=True,
            summary="Q1 review: 2 refusals for insufficient data.",
            notes="Committee reviewed all refusals.",
        )
        errs = [e for e in validate_dict(data) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 19: Edge cases (7 tests)
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_rrs_prefix_constant(self):
        assert RRS_PREFIX == "RRS-"

    def test_refusal_rate_tolerance_constant(self):
        assert REFUSAL_RATE_TOLERANCE == 0.01

    def test_all_valid_gate_statuses(self):
        for status in sorted(VALID_GATE_STATUSES):
            s = _valid_summary(gate_status=status)
            assert _errors(s) == [], f"Status {status} should be valid"

    def test_all_valid_refusal_reasons(self):
        for reason in sorted(VALID_TOP_REFUSAL_REASONS):
            s = _valid_summary(top_refusal_reason=reason)
            assert _errors(s) == [], f"Reason {reason} should be valid"

    def test_suspended_gate_still_valid(self):
        s = _valid_summary(gate_status="suspended")
        assert _errors(s) == []

    def test_summary_one_below_limit(self):
        s = _valid_summary(summary="s" * (SUMMARY_MAX_LENGTH - 1))
        assert _errors(s) == []

    def test_notes_one_below_limit(self):
        s = _valid_summary(notes="n" * (NOTES_MAX_LENGTH - 1))
        assert _errors(s) == []

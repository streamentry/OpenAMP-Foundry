"""Tests for RecalibrationDecisionLog schema — Phase G G1.

Exactly 63 tests: valid baseline + each validation rule + edge cases + warnings.
"""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.recalibration_decision_log import (
    NOTES_MAX_LENGTH,
    RATIONALE_MAX_LENGTH,
    RDL_PREFIX,
    VALID_DECISION_AUTHORITIES,
    VALID_DECISION_OUTCOMES,
    VALID_TRIGGER_ID_PREFIXES,
    VALID_TRIGGER_TYPES,
    RecalibrationDecisionLog,
    validate,
    validate_dict,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_log(**overrides) -> RecalibrationDecisionLog:
    defaults = dict(
        rdl_id="RDL-20240315-001",
        pipeline_version="v2.1.0",
        calibration_checkpoint="batch_3_review",
        decision_date="2024-03-15",
        trigger_type="batch_outcome",
        trigger_artifact_id="CPS-20240314-001",
        decision_outcome="approved",
        decision_authority="automated_gate",
        evidence_summary="Brier score improved from 0.28 to 0.21 after batch 3.",
        rationale="Metric improvement exceeds minimum threshold (0.005) and is "
                  "statistically consistent across 3 cohorts.",
        next_review_date="2024-06-15",
        conditions_if_deferred="",
        notes="",
    )
    defaults.update(overrides)
    return RecalibrationDecisionLog(**defaults)


def _valid() -> RecalibrationDecisionLog:
    return _valid_log()


# ---------------------------------------------------------------------------
# Group 1: Valid baseline (3 tests)
# ---------------------------------------------------------------------------

class TestValidBaseline:
    def test_valid_returns_no_errors(self):
        log = _valid_log(notes="Standard log entry.")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []

    def test_valid_with_notes(self):
        log = _valid_log(notes="Reviewed by safety officer.")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []

    def test_valid_deferred_with_conditions(self):
        log = _valid_log(
            decision_outcome="deferred",
            conditions_if_deferred="Await batch 4 results before deciding.",
            notes="Deferred pending further data.",
        )
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 2: Rule 1 — rdl_id prefix (4 tests)
# ---------------------------------------------------------------------------

class TestRdlIdPrefix:
    def test_wrong_prefix_rejected(self):
        log = _valid_log(rdl_id="CIR-001")
        assert any("rdl_id" in e for e in validate(log))

    def test_lowercase_prefix_rejected(self):
        log = _valid_log(rdl_id="rdl-001")
        assert any("rdl_id" in e for e in validate(log))

    def test_no_prefix_rejected(self):
        log = _valid_log(rdl_id="001")
        assert any("rdl_id" in e for e in validate(log))

    def test_correct_prefix_accepted(self):
        log = _valid_log(rdl_id="RDL-2024-001")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 3: Rule 2 — pipeline_version (3 tests)
# ---------------------------------------------------------------------------

class TestPipelineVersion:
    def test_empty_rejected(self):
        log = _valid_log(pipeline_version="")
        assert any("pipeline_version" in e for e in validate(log))

    def test_whitespace_only_rejected(self):
        log = _valid_log(pipeline_version="   ")
        assert any("pipeline_version" in e for e in validate(log))

    def test_valid_version(self):
        log = _valid_log(pipeline_version="v3.0.1")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 4: Rule 3 — calibration_checkpoint (3 tests)
# ---------------------------------------------------------------------------

class TestCalibrationCheckpoint:
    def test_empty_rejected(self):
        log = _valid_log(calibration_checkpoint="")
        assert any("calibration_checkpoint" in e for e in validate(log))

    def test_whitespace_only_rejected(self):
        log = _valid_log(calibration_checkpoint="   ")
        assert any("calibration_checkpoint" in e for e in validate(log))

    def test_valid_checkpoint(self):
        log = _valid_log(calibration_checkpoint="monthly_review_2024_03")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 5: Rule 4 — decision_date ISO format (4 tests)
# ---------------------------------------------------------------------------

class TestDecisionDate:
    def test_invalid_format_rejected(self):
        log = _valid_log(decision_date="March 15, 2024")
        assert any("decision_date" in e for e in validate(log))

    def test_wrong_separator_rejected(self):
        log = _valid_log(decision_date="2024/03/15")
        assert any("decision_date" in e for e in validate(log))

    def test_empty_rejected(self):
        log = _valid_log(decision_date="")
        assert any("decision_date" in e for e in validate(log))

    def test_valid_iso_date(self):
        log = _valid_log(decision_date="2025-01-01")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 6: Rule 5 — trigger_type vocabulary (4 tests)
# ---------------------------------------------------------------------------

class TestTriggerType:
    def test_invalid_trigger_type_rejected(self):
        log = _valid_log(trigger_type="unknown_trigger")
        assert any("trigger_type" in e for e in validate(log))

    def test_empty_trigger_type_rejected(self):
        log = _valid_log(trigger_type="")
        assert any("trigger_type" in e for e in validate(log))

    @pytest.mark.parametrize("tt", sorted(VALID_TRIGGER_TYPES))
    def test_all_valid_trigger_types_accepted(self, tt):
        log = _valid_log(trigger_type=tt)
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 7: Rule 6 — trigger_artifact_id prefix (4 tests)
# ---------------------------------------------------------------------------

class TestTriggerArtifactId:
    def test_unknown_prefix_rejected(self):
        log = _valid_log(trigger_artifact_id="XYZ-001")
        assert any("trigger_artifact_id" in e for e in validate(log))

    def test_empty_rejected(self):
        log = _valid_log(trigger_artifact_id="")
        assert any("trigger_artifact_id" in e for e in validate(log))

    @pytest.mark.parametrize("prefix", sorted(VALID_TRIGGER_ID_PREFIXES))
    def test_all_valid_prefixes_accepted(self, prefix):
        log = _valid_log(trigger_artifact_id=f"{prefix}001")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 8: Rule 7 — decision_outcome vocabulary (4 tests)
# ---------------------------------------------------------------------------

class TestDecisionOutcome:
    def test_invalid_outcome_rejected(self):
        log = _valid_log(decision_outcome="maybe")
        assert any("decision_outcome" in e for e in validate(log))

    def test_empty_outcome_rejected(self):
        log = _valid_log(decision_outcome="")
        assert any("decision_outcome" in e for e in validate(log))

    @pytest.mark.parametrize("outcome", sorted(VALID_DECISION_OUTCOMES))
    def test_all_valid_outcomes_accepted(self, outcome):
        extra = {}
        if outcome == "deferred":
            extra["conditions_if_deferred"] = "Pending batch 4 results."
        log = _valid_log(decision_outcome=outcome, **extra)
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 9: Rule 8 — decision_authority vocabulary (4 tests)
# ---------------------------------------------------------------------------

class TestDecisionAuthority:
    def test_invalid_authority_rejected(self):
        log = _valid_log(decision_authority="random_person")
        assert any("decision_authority" in e for e in validate(log))

    def test_empty_authority_rejected(self):
        log = _valid_log(decision_authority="")
        assert any("decision_authority" in e for e in validate(log))

    @pytest.mark.parametrize("auth", sorted(VALID_DECISION_AUTHORITIES))
    def test_all_valid_authorities_accepted(self, auth):
        log = _valid_log(decision_authority=auth)
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 10: Rule 9 — evidence_summary (3 tests)
# ---------------------------------------------------------------------------

class TestEvidenceSummary:
    def test_empty_rejected(self):
        log = _valid_log(evidence_summary="")
        assert any("evidence_summary" in e for e in validate(log))

    def test_whitespace_only_rejected(self):
        log = _valid_log(evidence_summary="   ")
        assert any("evidence_summary" in e for e in validate(log))

    def test_valid_summary(self):
        log = _valid_log(evidence_summary="AUROC improved from 0.72 to 0.78.")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 11: Rule 10 — rationale (4 tests)
# ---------------------------------------------------------------------------

class TestRationale:
    def test_empty_rejected(self):
        log = _valid_log(rationale="")
        assert any("rationale" in e for e in validate(log))

    def test_whitespace_only_rejected(self):
        log = _valid_log(rationale="   ")
        assert any("rationale" in e for e in validate(log))

    def test_too_long_rejected(self):
        log = _valid_log(rationale="x" * (RATIONALE_MAX_LENGTH + 1))
        assert any("rationale" in e for e in validate(log))

    def test_exactly_at_limit_accepted(self):
        log = _valid_log(rationale="x" * RATIONALE_MAX_LENGTH)
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 12: Rule 11 — next_review_date ISO format (3 tests)
# ---------------------------------------------------------------------------

class TestNextReviewDate:
    def test_invalid_format_rejected(self):
        log = _valid_log(next_review_date="Q2 2024")
        assert any("next_review_date" in e for e in validate(log))

    def test_empty_rejected(self):
        log = _valid_log(next_review_date="")
        assert any("next_review_date" in e for e in validate(log))

    def test_valid_iso_date(self):
        log = _valid_log(next_review_date="2025-06-30")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 13: Rule 12 — deferred requires conditions (3 tests)
# ---------------------------------------------------------------------------

class TestDeferredConditions:
    def test_deferred_without_conditions_rejected(self):
        log = _valid_log(decision_outcome="deferred", conditions_if_deferred="")
        assert any("conditions_if_deferred" in e for e in validate(log))

    def test_deferred_with_whitespace_conditions_rejected(self):
        log = _valid_log(decision_outcome="deferred", conditions_if_deferred="   ")
        assert any("conditions_if_deferred" in e for e in validate(log))

    def test_approved_without_conditions_accepted(self):
        log = _valid_log(decision_outcome="approved", conditions_if_deferred="")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 14: Rule 13 — notes length (3 tests)
# ---------------------------------------------------------------------------

class TestNotesLength:
    def test_too_long_rejected(self):
        log = _valid_log(notes="n" * (NOTES_MAX_LENGTH + 1))
        assert any("notes" in e for e in validate(log))

    def test_exactly_at_limit_accepted(self):
        log = _valid_log(notes="n" * NOTES_MAX_LENGTH)
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []

    def test_empty_notes_accepted(self):
        log = _valid_log(notes="")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 15: Warnings (6 tests)
# ---------------------------------------------------------------------------

class TestWarnings:
    def test_refused_outcome_triggers_warning(self):
        log = _valid_log(decision_outcome="refused")
        warns = [e for e in validate(log) if e.startswith("WARNING:")]
        assert any("refused" in w for w in warns)

    def test_deferred_no_notes_triggers_warning(self):
        log = _valid_log(
            decision_outcome="deferred",
            conditions_if_deferred="Await batch 4.",
            notes="",
        )
        warns = [e for e in validate(log) if e.startswith("WARNING:")]
        assert any("deferred" in w for w in warns)

    def test_empty_notes_triggers_warning(self):
        log = _valid_log(notes="")
        warns = [e for e in validate(log) if e.startswith("WARNING:")]
        assert any("notes" in w.lower() for w in warns)

    def test_notes_present_suppresses_notes_warning(self):
        log = _valid_log(notes="Full context provided.")
        warns = [e for e in validate(log) if e.startswith("WARNING:")]
        assert not any("notes is empty" in w for w in warns)

    def test_approved_has_no_refused_warning(self):
        log = _valid_log(decision_outcome="approved")
        warns = [e for e in validate(log) if e.startswith("WARNING:")]
        assert not any("refused" in w for w in warns)

    def test_deferred_with_notes_suppresses_deferred_warning(self):
        log = _valid_log(
            decision_outcome="deferred",
            conditions_if_deferred="Pending batch 5.",
            notes="Safety officer requested additional review.",
        )
        warns = [e for e in validate(log) if e.startswith("WARNING:")]
        assert not any("deferred decision has no notes" in w for w in warns)


# ---------------------------------------------------------------------------
# Group 16: validate_dict (4 tests)
# ---------------------------------------------------------------------------

class TestValidateDict:
    def test_valid_dict_returns_no_errors(self):
        data = dict(
            rdl_id="RDL-20240315-001",
            pipeline_version="v2.1.0",
            calibration_checkpoint="batch_3_review",
            decision_date="2024-03-15",
            trigger_type="batch_outcome",
            trigger_artifact_id="CPS-20240314-001",
            decision_outcome="approved",
            decision_authority="automated_gate",
            evidence_summary="Brier score improved from 0.28 to 0.21.",
            rationale="Improvement exceeds minimum threshold across 3 cohorts.",
            next_review_date="2024-06-15",
        )
        errs = [e for e in validate_dict(data) if not e.startswith("WARNING:")]
        assert errs == []

    def test_missing_required_field_returns_error(self):
        data = dict(
            rdl_id="RDL-001",
            pipeline_version="v1.0",
        )
        result = validate_dict(data)
        assert any("Schema construction error" in e for e in result)

    def test_invalid_field_caught_by_dict_validator(self):
        data = dict(
            rdl_id="WRONG-001",
            pipeline_version="v1.0",
            calibration_checkpoint="batch_1",
            decision_date="2024-01-01",
            trigger_type="batch_outcome",
            trigger_artifact_id="CPS-001",
            decision_outcome="approved",
            decision_authority="automated_gate",
            evidence_summary="Evidence here.",
            rationale="Rationale here.",
            next_review_date="2024-04-01",
        )
        result = validate_dict(data)
        assert any("rdl_id" in e for e in result)

    def test_extra_notes_in_dict(self):
        data = dict(
            rdl_id="RDL-20240315-002",
            pipeline_version="v2.1.0",
            calibration_checkpoint="quarterly_review",
            decision_date="2024-03-15",
            trigger_type="scheduled_review",
            trigger_artifact_id="DRM-20240314-001",
            decision_outcome="approved",
            decision_authority="pipeline_owner",
            evidence_summary="All metrics stable.",
            rationale="Quarterly check passed with no regressions.",
            next_review_date="2024-06-15",
            notes="Reviewed by J. Smith.",
        )
        errs = [e for e in validate_dict(data) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 17: Edge cases (8 tests)
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_partial_approved_no_conditions_accepted(self):
        log = _valid_log(decision_outcome="partial_approved", conditions_if_deferred="")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []

    def test_all_valid_trigger_prefixes_individually(self):
        for prefix in sorted(VALID_TRIGGER_ID_PREFIXES):
            log = _valid_log(trigger_artifact_id=f"{prefix}test-001")
            errs = [e for e in validate(log) if not e.startswith("WARNING:")]
            assert errs == [], f"Prefix {prefix} should be valid"

    def test_human_request_trigger_type(self):
        log = _valid_log(trigger_type="human_request")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []

    def test_committee_authority(self):
        log = _valid_log(decision_authority="committee")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []

    def test_safety_officer_authority(self):
        log = _valid_log(decision_authority="safety_officer")
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []

    def test_rationale_one_below_limit(self):
        log = _valid_log(rationale="r" * (RATIONALE_MAX_LENGTH - 1))
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []

    def test_notes_one_below_limit(self):
        log = _valid_log(notes="n" * (NOTES_MAX_LENGTH - 1))
        errs = [e for e in validate(log) if not e.startswith("WARNING:")]
        assert errs == []

    def test_rdl_prefix_constant(self):
        assert RDL_PREFIX == "RDL-"

"""Tests for SyntheticBoundaryAuditRecord schema — Phase G G8.

Exactly 63 tests: valid baseline + each validation rule + edge cases + warnings.
"""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.synthetic_boundary_audit_record import (
    NOTES_MAX_LENGTH,
    SBR_PREFIX,
    SUMMARY_MAX_LENGTH,
    VALID_ENFORCEMENT_OUTCOMES,
    VALID_EVIDENCE_SOURCES,
    VIOLATION_RATE_TOLERANCE,
    WET_LAB_REQUIRED_LEVEL,
    SyntheticBoundaryAuditRecord,
    validate,
    validate_dict,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_record(**overrides) -> SyntheticBoundaryAuditRecord:
    defaults = dict(
        sbr_id="SBR-20240315-001",
        pipeline_version="v2.1.0",
        batch_id="BATCH-003",
        audit_date="2024-03-15",
        evidence_source="synthetic",
        total_candidates_checked=20,
        total_violations=2,
        violation_rate=0.10,
        blocked_upgrades=2,
        max_proposed_ladder_level=3,
        policy_enforced=True,
        enforcement_outcome="violations_blocked",
        summary="2 of 20 candidates attempted level 4 upgrade; blocked by policy.",
        notes="",
    )
    defaults.update(overrides)
    return SyntheticBoundaryAuditRecord(**defaults)


def _valid() -> SyntheticBoundaryAuditRecord:
    return _valid_record()


def _errors(r):
    return [e for e in validate(r) if not e.startswith("WARNING:")]


def _warns(r):
    return [e for e in validate(r) if e.startswith("WARNING:")]


# ---------------------------------------------------------------------------
# Group 1: Valid baseline (3 tests)
# ---------------------------------------------------------------------------

class TestValidBaseline:
    def test_valid_returns_no_errors(self):
        assert _errors(_valid()) == []

    def test_valid_no_violations(self):
        r = _valid_record(
            total_violations=0,
            violation_rate=0.0,
            blocked_upgrades=0,
            enforcement_outcome="all_passed",
        )
        assert _errors(r) == []

    def test_valid_with_notes(self):
        r = _valid_record(notes="Reviewed by safety officer.")
        assert _errors(r) == []


# ---------------------------------------------------------------------------
# Group 2: Rule 1 — sbr_id prefix (4 tests)
# ---------------------------------------------------------------------------

class TestSbrIdPrefix:
    def test_wrong_prefix_rejected(self):
        r = _valid_record(sbr_id="CIR-001")
        assert any("sbr_id" in e for e in _errors(r))

    def test_lowercase_prefix_rejected(self):
        r = _valid_record(sbr_id="sbr-001")
        assert any("sbr_id" in e for e in _errors(r))

    def test_no_prefix_rejected(self):
        r = _valid_record(sbr_id="001")
        assert any("sbr_id" in e for e in _errors(r))

    def test_correct_prefix_accepted(self):
        r = _valid_record(sbr_id="SBR-2024-001")
        assert _errors(r) == []


# ---------------------------------------------------------------------------
# Group 3: Rule 2 — pipeline_version (3 tests)
# ---------------------------------------------------------------------------

class TestPipelineVersion:
    def test_empty_rejected(self):
        r = _valid_record(pipeline_version="")
        assert any("pipeline_version" in e for e in _errors(r))

    def test_whitespace_only_rejected(self):
        r = _valid_record(pipeline_version="   ")
        assert any("pipeline_version" in e for e in _errors(r))

    def test_valid_version(self):
        r = _valid_record(pipeline_version="v3.0.1")
        assert _errors(r) == []


# ---------------------------------------------------------------------------
# Group 4: Rule 3 — batch_id (3 tests)
# ---------------------------------------------------------------------------

class TestBatchId:
    def test_empty_rejected(self):
        r = _valid_record(batch_id="")
        assert any("batch_id" in e for e in _errors(r))

    def test_whitespace_only_rejected(self):
        r = _valid_record(batch_id="   ")
        assert any("batch_id" in e for e in _errors(r))

    def test_valid_batch_id(self):
        r = _valid_record(batch_id="BSP-20240101-001")
        assert _errors(r) == []


# ---------------------------------------------------------------------------
# Group 5: Rule 4 — audit_date ISO format (3 tests)
# ---------------------------------------------------------------------------

class TestAuditDate:
    def test_invalid_format_rejected(self):
        r = _valid_record(audit_date="March 15, 2024")
        assert any("audit_date" in e for e in _errors(r))

    def test_wrong_separator_rejected(self):
        r = _valid_record(audit_date="2024/03/15")
        assert any("audit_date" in e for e in _errors(r))

    def test_valid_iso_date(self):
        r = _valid_record(audit_date="2025-01-01")
        assert _errors(r) == []


# ---------------------------------------------------------------------------
# Group 6: Rule 5 — evidence_source vocabulary (4 tests)
# ---------------------------------------------------------------------------

class TestEvidenceSource:
    def test_invalid_source_rejected(self):
        r = _valid_record(evidence_source="wet_lab")
        assert any("evidence_source" in e for e in _errors(r))

    def test_empty_rejected(self):
        r = _valid_record(evidence_source="")
        assert any("evidence_source" in e for e in _errors(r))

    @pytest.mark.parametrize("src", sorted(VALID_EVIDENCE_SOURCES))
    def test_all_valid_sources_accepted(self, src):
        extra = {}
        if src == "mixed_synthetic_lab":
            extra["max_proposed_ladder_level"] = 3
        r = _valid_record(evidence_source=src, **extra)
        assert _errors(r) == []


# ---------------------------------------------------------------------------
# Group 7: Rule 6 — total_candidates_checked >= 1 (3 tests)
# ---------------------------------------------------------------------------

class TestTotalCandidatesChecked:
    def test_zero_rejected(self):
        r = _valid_record(
            total_candidates_checked=0,
            total_violations=0,
            violation_rate=0.0,
            blocked_upgrades=0,
        )
        assert any("total_candidates_checked" in e for e in _errors(r))

    def test_negative_rejected(self):
        r = _valid_record(
            total_candidates_checked=-5,
            total_violations=0,
            violation_rate=0.0,
            blocked_upgrades=0,
        )
        assert any("total_candidates_checked" in e for e in _errors(r))

    def test_one_accepted(self):
        r = _valid_record(
            total_candidates_checked=1,
            total_violations=0,
            violation_rate=0.0,
            blocked_upgrades=0,
            enforcement_outcome="all_passed",
        )
        assert _errors(r) == []


# ---------------------------------------------------------------------------
# Group 8: Rule 7 — total_violations bounds (3 tests)
# ---------------------------------------------------------------------------

class TestTotalViolations:
    def test_negative_rejected(self):
        r = _valid_record(
            total_violations=-1,
            violation_rate=0.0,
            blocked_upgrades=0,
        )
        assert any("total_violations" in e for e in _errors(r))

    def test_exceeds_total_rejected(self):
        r = _valid_record(
            total_violations=21,
            violation_rate=1.05,
            blocked_upgrades=21,
        )
        assert any("total_violations" in e for e in _errors(r))

    def test_exactly_total_accepted(self):
        r = _valid_record(
            total_violations=20,
            violation_rate=1.0,
            blocked_upgrades=20,
        )
        assert _errors(r) == []


# ---------------------------------------------------------------------------
# Group 9: Rule 8 — violation_rate range (3 tests)
# ---------------------------------------------------------------------------

class TestViolationRateRange:
    def test_negative_rejected(self):
        r = _valid_record(violation_rate=-0.1)
        assert any("violation_rate" in e for e in _errors(r))

    def test_above_one_rejected(self):
        r = _valid_record(violation_rate=1.1)
        assert any("violation_rate" in e for e in _errors(r))

    def test_zero_accepted(self):
        r = _valid_record(
            total_violations=0,
            violation_rate=0.0,
            blocked_upgrades=0,
            enforcement_outcome="all_passed",
        )
        assert _errors(r) == []


# ---------------------------------------------------------------------------
# Group 10: Rule 9 — violation_rate consistency (4 tests)
# ---------------------------------------------------------------------------

class TestViolationRateConsistency:
    def test_inconsistent_rate_rejected(self):
        r = _valid_record(
            total_candidates_checked=20,
            total_violations=2,
            violation_rate=0.5,
            blocked_upgrades=2,
        )
        assert any("inconsistent" in e for e in _errors(r))

    def test_exact_rate_accepted(self):
        r = _valid_record(
            total_candidates_checked=20,
            total_violations=2,
            violation_rate=0.10,
            blocked_upgrades=2,
        )
        assert _errors(r) == []

    def test_within_tolerance_accepted(self):
        r = _valid_record(
            total_candidates_checked=20,
            total_violations=2,
            violation_rate=0.105,
            blocked_upgrades=2,
        )
        assert _errors(r) == []

    def test_just_outside_tolerance_rejected(self):
        r = _valid_record(
            total_candidates_checked=20,
            total_violations=2,
            violation_rate=0.115,
            blocked_upgrades=2,
        )
        assert any("inconsistent" in e for e in _errors(r))


# ---------------------------------------------------------------------------
# Group 11: Rule 10 — blocked_upgrades bounds (3 tests)
# ---------------------------------------------------------------------------

class TestBlockedUpgrades:
    def test_negative_rejected(self):
        r = _valid_record(blocked_upgrades=-1)
        assert any("blocked_upgrades" in e for e in _errors(r))

    def test_exceeds_violations_rejected(self):
        r = _valid_record(
            total_violations=2,
            blocked_upgrades=3,
        )
        assert any("blocked_upgrades" in e for e in _errors(r))

    def test_zero_blocked_when_no_violations_accepted(self):
        r = _valid_record(
            total_violations=0,
            violation_rate=0.0,
            blocked_upgrades=0,
            enforcement_outcome="all_passed",
        )
        assert _errors(r) == []


# ---------------------------------------------------------------------------
# Group 12: Rule 11 — max_proposed_ladder_level range (3 tests)
# ---------------------------------------------------------------------------

class TestMaxProposedLadderLevel:
    def test_zero_rejected(self):
        r = _valid_record(max_proposed_ladder_level=0)
        assert any("max_proposed_ladder_level" in e for e in _errors(r))

    def test_seven_rejected(self):
        r = _valid_record(max_proposed_ladder_level=7)
        assert any("max_proposed_ladder_level" in e for e in _errors(r))

    def test_level_three_accepted(self):
        r = _valid_record(max_proposed_ladder_level=3)
        assert _errors(r) == []


# ---------------------------------------------------------------------------
# Group 13: Rule 12 — synthetic cannot propose level 4+ without violations (3 tests)
# ---------------------------------------------------------------------------

class TestSyntheticLevelBoundary:
    def test_synthetic_proposing_level4_without_violations_rejected(self):
        r = _valid_record(
            evidence_source="synthetic",
            max_proposed_ladder_level=4,
            total_violations=0,
            violation_rate=0.0,
            blocked_upgrades=0,
            enforcement_outcome="all_passed",
        )
        assert any(str(WET_LAB_REQUIRED_LEVEL) in e for e in _errors(r))

    def test_synthetic_proposing_level4_with_violations_accepted(self):
        r = _valid_record(
            evidence_source="synthetic",
            max_proposed_ladder_level=4,
            total_violations=1,
            violation_rate=0.05,
            blocked_upgrades=1,
        )
        assert _errors(r) == []

    def test_mixed_source_proposing_level4_accepted(self):
        r = _valid_record(
            evidence_source="mixed_synthetic_lab",
            max_proposed_ladder_level=4,
            total_violations=0,
            violation_rate=0.0,
            blocked_upgrades=0,
            enforcement_outcome="all_passed",
        )
        assert _errors(r) == []


# ---------------------------------------------------------------------------
# Group 14: Rule 13 — policy_enforced (3 tests)
# ---------------------------------------------------------------------------

class TestPolicyEnforced:
    def test_false_rejected(self):
        r = _valid_record(policy_enforced=False)
        assert any("policy_enforced" in e for e in _errors(r))

    def test_true_accepted(self):
        r = _valid_record(policy_enforced=True)
        assert _errors(r) == []

    def test_enforcement_constant_check(self):
        assert WET_LAB_REQUIRED_LEVEL == 4


# ---------------------------------------------------------------------------
# Group 15: Rule 14 — enforcement_outcome vocabulary (4 tests)
# ---------------------------------------------------------------------------

class TestEnforcementOutcome:
    def test_invalid_outcome_rejected(self):
        r = _valid_record(enforcement_outcome="partial")
        assert any("enforcement_outcome" in e for e in _errors(r))

    def test_empty_rejected(self):
        r = _valid_record(enforcement_outcome="")
        assert any("enforcement_outcome" in e for e in _errors(r))

    @pytest.mark.parametrize("outcome", sorted(VALID_ENFORCEMENT_OUTCOMES))
    def test_all_valid_outcomes_accepted(self, outcome):
        r = _valid_record(enforcement_outcome=outcome)
        assert _errors(r) == []


# ---------------------------------------------------------------------------
# Group 16: Rule 15+16 — summary and notes (4 tests)
# ---------------------------------------------------------------------------

class TestSummaryAndNotes:
    def test_empty_summary_rejected(self):
        r = _valid_record(summary="")
        assert any("summary" in e for e in _errors(r))

    def test_summary_too_long_rejected(self):
        r = _valid_record(summary="x" * (SUMMARY_MAX_LENGTH + 1))
        assert any("summary" in e for e in _errors(r))

    def test_notes_too_long_rejected(self):
        r = _valid_record(notes="n" * (NOTES_MAX_LENGTH + 1))
        assert any("notes" in e for e in _errors(r))

    def test_summary_at_limit_accepted(self):
        r = _valid_record(summary="x" * SUMMARY_MAX_LENGTH)
        assert _errors(r) == []


# ---------------------------------------------------------------------------
# Group 17: Warnings (6 tests)
# ---------------------------------------------------------------------------

class TestWarnings:
    def test_high_violation_rate_triggers_warning(self):
        r = _valid_record(
            total_violations=8,
            violation_rate=0.4,
            blocked_upgrades=8,
        )
        warns = _warns(r)
        assert any("violation_rate" in w for w in warns)

    def test_partial_block_triggers_warning(self):
        r = _valid_record(
            total_violations=2,
            violation_rate=0.10,
            blocked_upgrades=1,
            enforcement_outcome="violations_flagged",
        )
        warns = _warns(r)
        assert any("flagged but not blocked" in w for w in warns)

    def test_empty_notes_triggers_warning(self):
        r = _valid_record(notes="")
        warns = _warns(r)
        assert any("notes" in w.lower() for w in warns)

    def test_notes_present_suppresses_notes_warning(self):
        r = _valid_record(notes="Reviewed and signed off.")
        warns = _warns(r)
        assert not any("notes is empty" in w for w in warns)

    def test_low_violation_rate_no_high_rate_warning(self):
        r = _valid_record(
            total_violations=1,
            violation_rate=0.05,
            blocked_upgrades=1,
        )
        warns = _warns(r)
        assert not any("high overclaim" in w for w in warns)

    def test_all_blocked_no_partial_warning(self):
        r = _valid_record(
            total_violations=2,
            violation_rate=0.10,
            blocked_upgrades=2,
            enforcement_outcome="violations_blocked",
        )
        warns = _warns(r)
        assert not any("flagged but not blocked" in w for w in warns)


# ---------------------------------------------------------------------------
# Group 18: validate_dict (4 tests)
# ---------------------------------------------------------------------------

class TestValidateDict:
    def test_valid_dict_returns_no_errors(self):
        data = dict(
            sbr_id="SBR-20240315-001",
            pipeline_version="v2.1.0",
            batch_id="BATCH-003",
            audit_date="2024-03-15",
            evidence_source="synthetic",
            total_candidates_checked=20,
            total_violations=2,
            violation_rate=0.10,
            blocked_upgrades=2,
            max_proposed_ladder_level=3,
            policy_enforced=True,
            enforcement_outcome="violations_blocked",
            summary="2 of 20 candidates attempted invalid level upgrade; blocked.",
        )
        errs = [e for e in validate_dict(data) if not e.startswith("WARNING:")]
        assert errs == []

    def test_missing_required_field_returns_error(self):
        data = dict(sbr_id="SBR-001", pipeline_version="v1.0")
        result = validate_dict(data)
        assert any("Schema construction error" in e for e in result)

    def test_invalid_field_caught_by_dict_validator(self):
        data = dict(
            sbr_id="WRONG-001",
            pipeline_version="v1.0",
            batch_id="BATCH-001",
            audit_date="2024-01-01",
            evidence_source="synthetic",
            total_candidates_checked=10,
            total_violations=0,
            violation_rate=0.0,
            blocked_upgrades=0,
            max_proposed_ladder_level=3,
            policy_enforced=True,
            enforcement_outcome="all_passed",
            summary="No violations.",
        )
        result = validate_dict(data)
        assert any("sbr_id" in e for e in result)

    def test_extra_notes_in_dict(self):
        data = dict(
            sbr_id="SBR-20240315-002",
            pipeline_version="v2.1.0",
            batch_id="BATCH-004",
            audit_date="2024-03-15",
            evidence_source="simulation",
            total_candidates_checked=15,
            total_violations=0,
            violation_rate=0.0,
            blocked_upgrades=0,
            max_proposed_ladder_level=2,
            policy_enforced=True,
            enforcement_outcome="all_passed",
            summary="All 15 candidates within level 1-3 as expected.",
            notes="Clean batch, no interventions needed.",
        )
        errs = [e for e in validate_dict(data) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 19: Edge cases (7 tests)
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_sbr_prefix_constant(self):
        assert SBR_PREFIX == "SBR-"

    def test_violation_rate_tolerance_constant(self):
        assert VIOLATION_RATE_TOLERANCE == 0.01

    def test_all_valid_evidence_sources(self):
        for src in sorted(VALID_EVIDENCE_SOURCES):
            extra = {}
            if src == "mixed_synthetic_lab":
                extra["max_proposed_ladder_level"] = 3
            r = _valid_record(evidence_source=src, **extra)
            assert _errors(r) == [], f"Source {src} should be valid"

    def test_all_valid_enforcement_outcomes(self):
        for outcome in sorted(VALID_ENFORCEMENT_OUTCOMES):
            r = _valid_record(enforcement_outcome=outcome)
            assert _errors(r) == [], f"Outcome {outcome} should be valid"

    def test_simulation_source_valid(self):
        r = _valid_record(evidence_source="simulation")
        assert _errors(r) == []

    def test_summary_one_below_limit(self):
        r = _valid_record(summary="s" * (SUMMARY_MAX_LENGTH - 1))
        assert _errors(r) == []

    def test_notes_one_below_limit(self):
        r = _valid_record(notes="n" * (NOTES_MAX_LENGTH - 1))
        assert _errors(r) == []

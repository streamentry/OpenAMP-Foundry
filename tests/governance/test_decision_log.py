"""Tests for governance decision log validator."""
from __future__ import annotations
import pytest
from openamp_foundry.governance.decision_log import (
    GovernanceDecision,
    DecisionValidationResult,
    validate_governance_decision,
    validate_all_decisions,
    get_decisions_by_scope,
    get_decisions_by_status,
    GOVERNANCE_DECISIONS,
    VALID_SCOPES,
    VALID_STATUSES,
    VALID_REVIEW_CLASSES,
)


def test_gov_001_passes() -> None:
    decl = GOVERNANCE_DECISIONS[0]
    assert decl.decision_id == "GOV-001"
    result = validate_governance_decision(decl)
    assert result.passed is True
    assert result.errors == []


def test_gov_002_passes() -> None:
    decl = GOVERNANCE_DECISIONS[1]
    assert decl.decision_id == "GOV-002"
    result = validate_governance_decision(decl)
    assert result.passed is True
    assert result.errors == []


def test_gov_003_passes() -> None:
    decl = GOVERNANCE_DECISIONS[2]
    assert decl.decision_id == "GOV-003"
    result = validate_governance_decision(decl)
    assert result.passed is True
    assert result.errors == []


def test_gov_004_passes() -> None:
    decl = GOVERNANCE_DECISIONS[3]
    assert decl.decision_id == "GOV-004"
    result = validate_governance_decision(decl)
    assert result.passed is True
    assert result.errors == []


def test_empty_decision_id_fails() -> None:
    decl = GovernanceDecision(
        decision_id="",
        date="2026-07-09",
        scope="safety",
        decision="Some decision.",
        status="active",
        rationale="Because.",
        review_class="B",
    )
    result = validate_governance_decision(decl)
    assert result.passed is False
    assert any("decision_id" in e for e in result.errors)


def test_decision_id_not_starting_with_gov_fails() -> None:
    decl = GovernanceDecision(
        decision_id="XYZ-001",
        date="2026-07-09",
        scope="safety",
        decision="Some decision.",
        status="active",
        rationale="Because.",
        review_class="B",
    )
    result = validate_governance_decision(decl)
    assert result.passed is False
    assert any("must start with 'GOV-'" in e for e in result.errors)


def test_invalid_date_format_fails() -> None:
    decl = GovernanceDecision(
        decision_id="GOV-099",
        date="07-09-2026",
        scope="safety",
        decision="Some decision.",
        status="active",
        rationale="Because.",
        review_class="B",
    )
    result = validate_governance_decision(decl)
    assert result.passed is False
    assert any("date" in e for e in result.errors)


@pytest.mark.parametrize("bad_scope", ["invalid_scope", "biology", ""])
def test_invalid_scope_fails(bad_scope: str) -> None:
    decl = GovernanceDecision(
        decision_id="GOV-099",
        date="2026-07-09",
        scope=bad_scope,
        decision="Some decision.",
        status="active",
        rationale="Because.",
        review_class="B",
    )
    result = validate_governance_decision(decl)
    assert result.passed is False
    assert any("scope" in e for e in result.errors)


def test_empty_decision_text_fails() -> None:
    decl = GovernanceDecision(
        decision_id="GOV-099",
        date="2026-07-09",
        scope="safety",
        decision="",
        status="active",
        rationale="Because.",
        review_class="B",
    )
    result = validate_governance_decision(decl)
    assert result.passed is False
    assert any("decision must not be empty" in e for e in result.errors)


@pytest.mark.parametrize("bad_status", ["invalid", "done", ""])
def test_invalid_status_fails(bad_status: str) -> None:
    decl = GovernanceDecision(
        decision_id="GOV-099",
        date="2026-07-09",
        scope="safety",
        decision="Some decision.",
        status=bad_status,
        rationale="Because.",
        review_class="B",
    )
    result = validate_governance_decision(decl)
    assert result.passed is False
    assert any("status" in e for e in result.errors)


def test_empty_rationale_fails() -> None:
    decl = GovernanceDecision(
        decision_id="GOV-099",
        date="2026-07-09",
        scope="safety",
        decision="Some decision.",
        status="active",
        rationale="",
        review_class="B",
    )
    result = validate_governance_decision(decl)
    assert result.passed is False
    assert any("rationale" in e for e in result.errors)


@pytest.mark.parametrize("bad_review_class", ["E", "0", ""])
def test_invalid_review_class_fails(bad_review_class: str) -> None:
    decl = GovernanceDecision(
        decision_id="GOV-099",
        date="2026-07-09",
        scope="safety",
        decision="Some decision.",
        status="active",
        rationale="Because.",
        review_class=bad_review_class,
    )
    result = validate_governance_decision(decl)
    assert result.passed is False
    assert any("review_class" in e for e in result.errors)


def test_dry_lab_only_false_fails() -> None:
    decl = GovernanceDecision(
        decision_id="GOV-099",
        date="2026-07-09",
        scope="safety",
        decision="Some decision.",
        status="active",
        rationale="Because.",
        review_class="B",
        dry_lab_only=False,
    )
    result = validate_governance_decision(decl)
    assert result.passed is False
    assert any("dry_lab_only" in e for e in result.errors)


def test_superseded_status_has_warning() -> None:
    decl = GovernanceDecision(
        decision_id="GOV-099",
        date="2026-07-09",
        scope="safety",
        decision="Some old decision.",
        status="superseded",
        rationale="Superseded by GOV-100.",
        review_class="B",
    )
    result = validate_governance_decision(decl)
    assert result.passed is True
    assert any("superseded" in w for w in result.warnings)


def test_validate_all_decisions_passes() -> None:
    result = validate_all_decisions()
    assert result["all_passed"] is True
    assert result["total"] == 8
    assert result["passed"] == 8
    assert result["failed"] == 0


def test_get_decisions_by_scope_safety() -> None:
    decisions = get_decisions_by_scope("safety")
    ids = [d.decision_id for d in decisions]
    assert "GOV-001" in ids


def test_get_decisions_by_status_active() -> None:
    decisions = get_decisions_by_status("active")
    assert len(decisions) == 8


def test_governance_decisions_has_8_entries() -> None:
    assert len(GOVERNANCE_DECISIONS) == 8


def test_all_results_have_dry_lab_only_true() -> None:
    for d in GOVERNANCE_DECISIONS:
        result = validate_governance_decision(d)
        assert result.dry_lab_only is True


def test_valid_sets_have_expected_counts() -> None:
    assert len(VALID_SCOPES) == 8
    assert len(VALID_STATUSES) == 4
    assert len(VALID_REVIEW_CLASSES) == 4


def test_decision_validation_result_dataclass() -> None:
    result = DecisionValidationResult(
        decision_id="GOV-001",
        passed=True,
        errors=[],
        warnings=[],
    )
    assert result.decision_id == "GOV-001"
    assert result.passed is True
    assert result.errors == []
    assert result.warnings == []
    assert result.dry_lab_only is True

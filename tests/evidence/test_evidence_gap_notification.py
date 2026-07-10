"""Tests for EGN- evidence gap notification schema."""

import pytest
from openamp_foundry.evidence.evidence_gap_notification import (
    EvidenceGapNotification,
    VALID_EGN_GAP_TYPES,
    VALID_EGN_CLOSURE_ARTIFACT_TYPES,
    VALID_EGN_EFFORT_ESTIMATES,
    VALID_EGN_PRIORITIES,
    VALID_EGN_VERDICTS,
    build_evidence_gap_notification,
    format_evidence_gap_notification,
    validate_evidence_gap_notification,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        egn_id="EGN-001",
        pipeline_version="v1.0",
        artifact_id="fam-001",
        gap_type="missing_wet_lab_validation",
        gap_description="No WHR records exist for this candidate family.",
        closure_artifact_type="WHR",
        closure_description="Submit at least one WHR record for a member of this family.",
        effort_estimate="weeks",
        priority="high",
        verdict="actionable",
        is_blocking=True,
        limitations=["Requires wet-lab partner access."],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_evidence_gap_notification(**defaults)


def _make_egn(**kwargs):
    defaults = dict(
        egn_id="EGN-001",
        pipeline_version="v1.0",
        artifact_id="fam-001",
        gap_type="missing_wet_lab_validation",
        gap_description="No WHR records exist for this candidate family.",
        closure_artifact_type="WHR",
        closure_description="Submit at least one WHR record for a member of this family.",
        effort_estimate="weeks",
        priority="high",
        verdict="actionable",
        is_blocking=True,
        dry_lab_only=True,
        limitations=["Requires wet-lab partner access."],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return EvidenceGapNotification(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants (14 tests)
# ---------------------------------------------------------------------------


def test_valid_egn_gap_types_is_frozenset():
    assert isinstance(VALID_EGN_GAP_TYPES, frozenset)


def test_valid_egn_gap_types_has_nine():
    assert len(VALID_EGN_GAP_TYPES) == 9


def test_valid_egn_gap_types_contains_missing_wet_lab():
    assert "missing_wet_lab_validation" in VALID_EGN_GAP_TYPES


def test_valid_egn_gap_types_contains_missing_baseline():
    assert "missing_baseline_comparison" in VALID_EGN_GAP_TYPES


def test_valid_egn_gap_types_contains_claim_strength():
    assert "claim_strength_mismatch" in VALID_EGN_GAP_TYPES


def test_valid_egn_closure_artifact_types_is_frozenset():
    assert isinstance(VALID_EGN_CLOSURE_ARTIFACT_TYPES, frozenset)


def test_valid_egn_closure_artifact_types_has_fourteen():
    assert len(VALID_EGN_CLOSURE_ARTIFACT_TYPES) == 14


def test_valid_egn_closure_artifact_types_contains_whr():
    assert "WHR" in VALID_EGN_CLOSURE_ARTIFACT_TYPES


def test_valid_egn_closure_artifact_types_contains_arg():
    assert "ARG" in VALID_EGN_CLOSURE_ARTIFACT_TYPES


def test_valid_egn_effort_estimates_is_frozenset():
    assert isinstance(VALID_EGN_EFFORT_ESTIMATES, frozenset)


def test_valid_egn_effort_estimates_has_five():
    assert len(VALID_EGN_EFFORT_ESTIMATES) == 5


def test_valid_egn_priorities_is_frozenset():
    assert isinstance(VALID_EGN_PRIORITIES, frozenset)


def test_valid_egn_priorities_has_four():
    assert len(VALID_EGN_PRIORITIES) == 4


def test_valid_egn_verdicts_is_frozenset():
    assert isinstance(VALID_EGN_VERDICTS, frozenset)
    assert len(VALID_EGN_VERDICTS) == 4


# ---------------------------------------------------------------------------
# 2. build – happy paths (16 tests)
# ---------------------------------------------------------------------------


def test_build_returns_evidence_gap_notification():
    assert isinstance(_build(), EvidenceGapNotification)


def test_build_gap_type_stored():
    egn = _build(gap_type="missing_safety_clearance")
    assert egn.gap_type == "missing_safety_clearance"


def test_build_closure_artifact_type_stored():
    egn = _build(closure_artifact_type="CFC")
    assert egn.closure_artifact_type == "CFC"


def test_build_is_blocking_true():
    egn = _build(is_blocking=True)
    assert egn.is_blocking is True


def test_build_is_blocking_false():
    egn = _build(is_blocking=False)
    assert egn.is_blocking is False


def test_build_priority_critical():
    egn = _build(priority="critical")
    assert egn.priority == "critical"


def test_build_effort_weeks():
    egn = _build(effort_estimate="weeks")
    assert egn.effort_estimate == "weeks"


def test_build_verdict_actionable():
    egn = _build(verdict="actionable")
    assert egn.verdict == "actionable"


def test_build_verdict_blocked_on_resources():
    egn = _build(verdict="blocked_on_resources")
    assert egn.verdict == "blocked_on_resources"


def test_build_verdict_accepted_limitation():
    egn = _build(verdict="accepted_limitation")
    assert egn.verdict == "accepted_limitation"


def test_build_verdict_under_investigation():
    egn = _build(verdict="under_investigation")
    assert egn.verdict == "under_investigation"


def test_build_egn_id_stored():
    egn = _build(egn_id="EGN-099")
    assert egn.egn_id == "EGN-099"


def test_build_pipeline_version_stored():
    egn = _build(pipeline_version="v2.0")
    assert egn.pipeline_version == "v2.0"


def test_build_artifact_id_stored():
    egn = _build(artifact_id="fam-099")
    assert egn.artifact_id == "fam-099"


def test_build_closure_description_stored():
    egn = _build(closure_description="Run a charge-matched benchmark.")
    assert egn.closure_description == "Run a charge-matched benchmark."


def test_build_limitations_stored():
    egn = _build(limitations=["No partner available.", "Expensive assay."])
    assert len(egn.limitations) == 2
    assert "No partner available." in egn.limitations


# ---------------------------------------------------------------------------
# 3. validate – rejection cases (16 tests)
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_egn_id_prefix():
    with pytest.raises(ValueError, match="EGN-"):
        _build(egn_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_artifact_id():
    with pytest.raises(ValueError):
        _build(artifact_id="")


def test_validate_rejects_empty_gap_description():
    with pytest.raises(ValueError):
        _build(gap_description="")


def test_validate_rejects_gap_description_too_long():
    with pytest.raises(ValueError, match="gap_description"):
        _build(gap_description="x" * 401)


def test_validate_rejects_invalid_gap_type():
    with pytest.raises(ValueError, match="gap_type"):
        _build(gap_type="invalid_gap_type")


def test_validate_rejects_empty_closure_description():
    with pytest.raises(ValueError):
        _build(closure_description="")


def test_validate_rejects_invalid_closure_artifact_type():
    with pytest.raises(ValueError, match="closure_artifact_type"):
        _build(closure_artifact_type="INVALID")


def test_validate_rejects_invalid_effort_estimate():
    with pytest.raises(ValueError, match="effort_estimate"):
        _build(effort_estimate="years")


def test_validate_rejects_invalid_priority():
    with pytest.raises(ValueError, match="priority"):
        _build(priority="urgent")


def test_validate_rejects_invalid_verdict():
    with pytest.raises(ValueError, match="verdict"):
        _build(verdict="rejected")


def test_validate_rejects_dry_lab_only_false():
    egn = _make_egn()
    egn.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_evidence_gap_notification(egn)


def test_validate_rejects_empty_limitations():
    egn = _make_egn()
    egn.limitations = []
    with pytest.raises(ValueError, match="limitations"):
        validate_evidence_gap_notification(egn)


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_empty_egn_id():
    with pytest.raises(ValueError, match="EGN-"):
        _build(egn_id="")


def test_validate_rejects_gap_description_400_boundary():
    with pytest.raises(ValueError, match="gap_description"):
        _build(gap_description="x" * 401)


# ---------------------------------------------------------------------------
# 4. format (8 tests)
# ---------------------------------------------------------------------------


def test_format_contains_egn_id():
    assert "EGN-001" in format_evidence_gap_notification(_build())


def test_format_contains_gap_type():
    assert "missing_wet_lab_validation" in format_evidence_gap_notification(_build())


def test_format_contains_priority():
    assert "high" in format_evidence_gap_notification(_build())


def test_format_contains_effort():
    assert "weeks" in format_evidence_gap_notification(_build())


def test_format_contains_verdict():
    assert "actionable" in format_evidence_gap_notification(_build())


def test_format_contains_is_blocking():
    assert "True" in format_evidence_gap_notification(_build())


def test_format_contains_closure_artifact_type():
    assert "WHR" in format_evidence_gap_notification(_build())


def test_format_is_string():
    assert isinstance(format_evidence_gap_notification(_build()), str)

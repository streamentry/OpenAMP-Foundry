"""Tests for SRD- safety-release decision schema."""

import pytest
from openamp_foundry.evidence.safety_release_decision import (
    SafetyReleaseDecision,
    VALID_SRD_DECISIONS,
    VALID_RELEASE_SCOPES,
    VALID_SAFETY_CHECK_IDS,
    REQUIRED_SAFETY_CHECKS,
    build_safety_release_decision,
    format_safety_release_decision,
    validate_safety_release_decision,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALL_REQUIRED = list(REQUIRED_SAFETY_CHECKS)
_ALL_CHECKS = list(VALID_SAFETY_CHECK_IDS)


def _build(**kwargs):
    defaults = dict(
        srd_id="SRD-001",
        pipeline_version="v1.0",
        erp_id="ERP-001",
        release_decision="authorized",
        release_scope="academic_collaboration",
        safety_checks_passed=_ALL_REQUIRED,
        restrictions=["do not share sequence data publicly"],
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_safety_release_decision(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_srd_decisions_is_frozenset():
    assert isinstance(VALID_SRD_DECISIONS, frozenset)


def test_valid_srd_decisions_contains_authorized():
    assert "authorized" in VALID_SRD_DECISIONS


def test_valid_srd_decisions_contains_rejected():
    assert "rejected" in VALID_SRD_DECISIONS


def test_valid_srd_decisions_contains_pending_review():
    assert "pending_review" in VALID_SRD_DECISIONS


def test_valid_release_scopes_is_frozenset():
    assert isinstance(VALID_RELEASE_SCOPES, frozenset)


def test_valid_release_scopes_contains_academic_collaboration():
    assert "academic_collaboration" in VALID_RELEASE_SCOPES


def test_valid_release_scopes_contains_public_preprint():
    assert "public_preprint" in VALID_RELEASE_SCOPES


def test_valid_release_scopes_contains_internal_only():
    assert "internal_only" in VALID_RELEASE_SCOPES


def test_valid_release_scopes_contains_restricted_partner():
    assert "restricted_partner" in VALID_RELEASE_SCOPES


def test_valid_safety_check_ids_is_frozenset():
    assert isinstance(VALID_SAFETY_CHECK_IDS, frozenset)


def test_valid_safety_check_ids_contains_dual_use():
    assert "dual_use_screened" in VALID_SAFETY_CHECK_IDS


def test_valid_safety_check_ids_contains_dry_lab_label():
    assert "dry_lab_only_label_present" in VALID_SAFETY_CHECK_IDS


def test_valid_safety_check_ids_contains_novelty_bounded():
    assert "novelty_claims_bounded" in VALID_SAFETY_CHECK_IDS


def test_required_safety_checks_is_tuple():
    assert isinstance(REQUIRED_SAFETY_CHECKS, tuple)


def test_required_safety_checks_contains_dual_use():
    assert "dual_use_screened" in REQUIRED_SAFETY_CHECKS


def test_required_safety_checks_contains_dry_lab_label():
    assert "dry_lab_only_label_present" in REQUIRED_SAFETY_CHECKS


def test_required_safety_checks_contains_novelty_bounded():
    assert "novelty_claims_bounded" in REQUIRED_SAFETY_CHECKS


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_safety_release_decision():
    assert isinstance(_build(), SafetyReleaseDecision)


def test_build_srd_id_stored():
    assert _build().srd_id == "SRD-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_erp_id_stored():
    assert _build().erp_id == "ERP-001"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_authorized_with_all_required():
    r = _build(release_decision="authorized", safety_checks_passed=_ALL_REQUIRED)
    assert r.release_decision == "authorized"


def test_build_all_required_checks_passed_true():
    r = _build(safety_checks_passed=_ALL_REQUIRED)
    assert r.all_required_checks_passed is True


def test_build_all_required_checks_passed_false_when_missing():
    r = _build(
        release_decision="pending_review",
        safety_checks_passed=["dual_use_screened"],
    )
    assert r.all_required_checks_passed is False


def test_build_rejected_with_reason():
    r = _build(
        release_decision="rejected",
        safety_checks_passed=["dual_use_screened"],
        rejection_reason="toxicity flags not reviewed",
    )
    assert r.release_decision == "rejected"
    assert r.rejection_reason == "toxicity flags not reviewed"


def test_build_pending_review():
    r = _build(
        release_decision="pending_review",
        safety_checks_passed=_ALL_REQUIRED,
    )
    assert r.release_decision == "pending_review"


def test_build_release_scope_stored():
    assert _build().release_scope == "academic_collaboration"


def test_build_public_preprint_scope():
    r = _build(release_scope="public_preprint")
    assert r.release_scope == "public_preprint"


def test_build_restrictions_stored():
    assert _build().restrictions == ["do not share sequence data publicly"]


def test_build_rejection_reason_default_empty():
    assert _build().rejection_reason == ""


def test_build_safety_checks_stored():
    r = _build(safety_checks_passed=_ALL_REQUIRED)
    for check in _ALL_REQUIRED:
        assert check in r.safety_checks_passed


def test_build_all_checks_accepted():
    r = _build(safety_checks_passed=_ALL_CHECKS)
    assert len(r.safety_checks_passed) == len(_ALL_CHECKS)


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_internal_only_scope():
    r = _build(release_scope="internal_only")
    assert r.release_scope == "internal_only"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_srd_id_prefix():
    with pytest.raises(ValueError, match="SRD-"):
        _build(srd_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_bad_erp_id_prefix():
    with pytest.raises(ValueError, match="ERP-"):
        _build(erp_id="BAD-001")


def test_validate_rejects_invalid_release_decision():
    srd = _build()
    srd.release_decision = "UNKNOWN"
    with pytest.raises(ValueError, match="release_decision"):
        validate_safety_release_decision(srd)


def test_validate_rejects_invalid_release_scope():
    with pytest.raises(ValueError, match="release_scope"):
        _build(release_scope="UNKNOWN")


def test_validate_rejects_invalid_safety_check_id():
    with pytest.raises(ValueError, match="safety check"):
        _build(safety_checks_passed=["UNKNOWN_CHECK"])


def test_validate_rejects_authorized_without_required_checks():
    with pytest.raises(ValueError, match="authorized"):
        _build(
            release_decision="authorized",
            safety_checks_passed=["dual_use_screened"],
        )


def test_validate_rejects_rejected_without_reason():
    with pytest.raises(ValueError, match="rejection_reason"):
        _build(
            release_decision="rejected",
            safety_checks_passed=["dual_use_screened"],
            rejection_reason="",
        )


def test_validate_rejects_all_required_checks_mismatch():
    srd = _build()
    srd.all_required_checks_passed = False
    with pytest.raises(ValueError, match="all_required_checks_passed"):
        validate_safety_release_decision(srd)


def test_validate_rejects_dry_lab_only_false():
    srd = _build()
    srd.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_safety_release_decision(srd)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_srd_id():
    assert "SRD-001" in format_safety_release_decision(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_safety_release_decision(_build())


def test_format_contains_erp_id():
    assert "ERP-001" in format_safety_release_decision(_build())


def test_format_contains_decision():
    assert "authorized" in format_safety_release_decision(_build())


def test_format_contains_scope():
    assert "academic_collaboration" in format_safety_release_decision(_build())


def test_format_contains_safety_check():
    assert "dual_use_screened" in format_safety_release_decision(_build())


def test_format_contains_restrictions():
    assert "do not share sequence data publicly" in format_safety_release_decision(
        _build()
    )


def test_format_contains_limitations():
    assert "dry-lab only" in format_safety_release_decision(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_safety_release_decision(_build())


def test_format_is_string():
    assert isinstance(format_safety_release_decision(_build()), str)

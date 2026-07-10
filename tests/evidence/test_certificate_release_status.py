"""Tests for CRS- certificate release-status schema."""

import pytest
from openamp_foundry.evidence.certificate_release_status import (
    CertificateReleaseStatus,
    VALID_RELEASE_STATUSES,
    STAGED_RELEASE_ORDER,
    VALID_GATE_CONDITIONS,
    build_certificate_release_status,
    format_certificate_release_status,
    validate_certificate_release_status,
    can_advance_to,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        crs_id="CRS-001",
        cert_id="CERT-001",
        pipeline_version="v1.0",
        release_status="draft",
        gate_conditions_met=[],
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_certificate_release_status(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_release_statuses_is_frozenset():
    assert isinstance(VALID_RELEASE_STATUSES, frozenset)


def test_valid_release_statuses_contains_draft():
    assert "draft" in VALID_RELEASE_STATUSES


def test_valid_release_statuses_contains_internal_review():
    assert "internal_review" in VALID_RELEASE_STATUSES


def test_valid_release_statuses_contains_external_review_ready():
    assert "external_review_ready" in VALID_RELEASE_STATUSES


def test_valid_release_statuses_contains_released():
    assert "released" in VALID_RELEASE_STATUSES


def test_valid_release_statuses_contains_archived():
    assert "archived" in VALID_RELEASE_STATUSES


def test_staged_release_order_is_tuple():
    assert isinstance(STAGED_RELEASE_ORDER, tuple)


def test_staged_release_order_draft_first():
    assert STAGED_RELEASE_ORDER[0] == "draft"


def test_staged_release_order_released_before_archived():
    idx_released = STAGED_RELEASE_ORDER.index("released")
    idx_archived = STAGED_RELEASE_ORDER.index("archived")
    assert idx_released < idx_archived


def test_staged_release_order_internal_before_external():
    idx_internal = STAGED_RELEASE_ORDER.index("internal_review")
    idx_external = STAGED_RELEASE_ORDER.index("external_review_ready")
    assert idx_internal < idx_external


def test_valid_gate_conditions_is_frozenset():
    assert isinstance(VALID_GATE_CONDITIONS, frozenset)


def test_valid_gate_conditions_contains_safety_checks_passed():
    assert "safety_checks_passed" in VALID_GATE_CONDITIONS


def test_valid_gate_conditions_contains_srd_authorized():
    assert "srd_authorized" in VALID_GATE_CONDITIONS


def test_valid_gate_conditions_contains_dual_use_screened():
    assert "dual_use_screened" in VALID_GATE_CONDITIONS


def test_valid_gate_conditions_contains_novelty_claims_bounded():
    assert "novelty_claims_bounded" in VALID_GATE_CONDITIONS


# ---------------------------------------------------------------------------
# 2. build happy paths
# ---------------------------------------------------------------------------


def test_build_returns_certificate_release_status():
    assert isinstance(_build(), CertificateReleaseStatus)


def test_build_crs_id_stored():
    assert _build().crs_id == "CRS-001"


def test_build_cert_id_stored():
    assert _build().cert_id == "CERT-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_draft_status():
    r = _build(release_status="draft")
    assert r.release_status == "draft"


def test_build_draft_stage_index_is_zero():
    r = _build(release_status="draft")
    assert r.release_stage_index == 0


def test_build_internal_review_stage_index():
    r = _build(release_status="internal_review")
    assert r.release_stage_index == 1


def test_build_external_review_ready_stage_index():
    r = _build(release_status="external_review_ready")
    assert r.release_stage_index == 2


def test_build_released_with_srd_authorized():
    r = _build(
        release_status="released",
        gate_conditions_met=["srd_authorized"],
    )
    assert r.release_status == "released"


def test_build_archived_status():
    r = _build(release_status="archived")
    assert r.release_status == "archived"


def test_build_gate_conditions_stored():
    r = _build(gate_conditions_met=["dual_use_screened", "safety_checks_passed"])
    assert "dual_use_screened" in r.gate_conditions_met
    assert "safety_checks_passed" in r.gate_conditions_met


def test_build_empty_gate_conditions_default():
    assert _build().gate_conditions_met == []


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_multiple_gate_conditions():
    r = _build(gate_conditions_met=[
        "safety_checks_passed", "dual_use_screened", "novelty_claims_bounded"
    ])
    assert len(r.gate_conditions_met) == 3


# ---------------------------------------------------------------------------
# 3. validate rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_crs_id_prefix():
    with pytest.raises(ValueError, match="CRS-"):
        _build(crs_id="BAD-001")


def test_validate_rejects_empty_cert_id():
    with pytest.raises(ValueError, match="cert_id"):
        _build(cert_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_release_status():
    with pytest.raises(ValueError, match="release_status"):
        _build(release_status="UNKNOWN")


def test_validate_rejects_stage_index_mismatch():
    crs = _build()
    crs.release_stage_index = 99
    with pytest.raises(ValueError, match="release_stage_index"):
        validate_certificate_release_status(crs)


def test_validate_rejects_invalid_gate_condition():
    with pytest.raises(ValueError, match="gate condition"):
        _build(gate_conditions_met=["UNKNOWN_CONDITION"])


def test_validate_rejects_released_without_srd_authorized():
    with pytest.raises(ValueError, match="srd_authorized"):
        _build(
            release_status="released",
            gate_conditions_met=["safety_checks_passed"],
        )


def test_validate_rejects_dry_lab_only_false():
    crs = _build()
    crs.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_certificate_release_status(crs)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. can_advance_to
# ---------------------------------------------------------------------------


def test_draft_can_advance_to_internal_review():
    assert can_advance_to("draft", "internal_review") is True


def test_draft_can_advance_to_archived():
    assert can_advance_to("draft", "archived") is True


def test_draft_cannot_advance_to_released():
    assert can_advance_to("draft", "released") is False


def test_draft_cannot_advance_to_external_review_ready():
    assert can_advance_to("draft", "external_review_ready") is False


def test_internal_review_can_advance_to_external_review_ready():
    assert can_advance_to("internal_review", "external_review_ready") is True


def test_internal_review_can_go_back_to_draft():
    assert can_advance_to("internal_review", "draft") is True


def test_external_review_ready_can_advance_to_released():
    assert can_advance_to("external_review_ready", "released") is True


def test_external_review_ready_can_go_back_to_internal_review():
    assert can_advance_to("external_review_ready", "internal_review") is True


def test_released_can_only_advance_to_archived():
    assert can_advance_to("released", "archived") is True
    assert can_advance_to("released", "draft") is False


def test_archived_cannot_advance_anywhere():
    for status in VALID_RELEASE_STATUSES:
        assert can_advance_to("archived", status) is False


# ---------------------------------------------------------------------------
# 5. format
# ---------------------------------------------------------------------------


def test_format_contains_crs_id():
    assert "CRS-001" in format_certificate_release_status(_build())


def test_format_contains_cert_id():
    assert "CERT-001" in format_certificate_release_status(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_certificate_release_status(_build())


def test_format_contains_release_status():
    assert "draft" in format_certificate_release_status(_build())


def test_format_contains_stage_index():
    assert "0" in format_certificate_release_status(_build())


def test_format_contains_gate_condition():
    r = _build(gate_conditions_met=["dual_use_screened"])
    assert "dual_use_screened" in format_certificate_release_status(r)


def test_format_contains_limitations():
    assert "dry-lab only" in format_certificate_release_status(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_certificate_release_status(_build())


def test_format_is_string():
    assert isinstance(format_certificate_release_status(_build()), str)

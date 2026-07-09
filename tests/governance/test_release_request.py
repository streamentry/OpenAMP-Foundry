"""Tests for release request validator."""
from __future__ import annotations

from openamp_foundry.governance.release_request import (
    ReleaseRequest,
    ReleaseRequestValidationResult,
    VALID_RELEASE_TYPES,
    VALID_SAFETY_STATUSES,
    VALID_INTENDED_USES,
    VALID_APPROVAL_STATUSES,
    VALID_REVIEW_CLASSES,
    validate_release_request,
    validate_request_dict,
)


def _make_valid_req() -> ReleaseRequest:
    return ReleaseRequest(
        release_id="REL-2026-001",
        release_type="candidate",
        artifact_id="AMP-001",
        artifact_version="1.0.0",
        requestor_name="OpenAMP Team",
        requestor_institution="Open Problem Lab",
        request_date="2026-07-09",
        evidence_level=2,
        dry_lab_only=True,
        safety_review_status="approved",
        benchmark_summary="Passes all benchmark gates",
        known_limitations="Dry-lab only, not wet-lab validated",
        intended_use="research",
        data_license="CC-BY-4.0",
        human_reviewer="maintainer",
        review_class="B",
        approval_status="pending",
    )


def test_valid_candidate_release_request_passes():
    req = _make_valid_req()
    result = validate_release_request(req)
    assert result.passed
    assert result.errors == []


def test_release_id_not_starting_with_rel_fails():
    req = _make_valid_req()
    req.release_id = "REL-2026-001"
    result = validate_release_request(req)
    assert result.passed
    req.release_id = "INVALID-001"
    result = validate_release_request(req)
    assert not result.passed
    assert any("release_id" in e for e in result.errors)


def test_invalid_release_type_fails():
    req = _make_valid_req()
    req.release_type = "invalid_type"
    result = validate_release_request(req)
    assert not result.passed
    assert any("release_type" in e for e in result.errors)


def test_empty_artifact_id_fails():
    req = _make_valid_req()
    req.artifact_id = ""
    result = validate_release_request(req)
    assert not result.passed
    assert any("artifact_id" in e for e in result.errors)


def test_empty_requestor_name_fails():
    req = _make_valid_req()
    req.requestor_name = ""
    result = validate_release_request(req)
    assert not result.passed
    assert any("requestor_name" in e for e in result.errors)


def test_invalid_request_date_format_fails():
    req = _make_valid_req()
    req.request_date = "2026/07/09"
    result = validate_release_request(req)
    assert not result.passed
    assert any("request_date" in e for e in result.errors)


def test_evidence_level_zero_fails():
    req = _make_valid_req()
    req.evidence_level = 0
    result = validate_release_request(req)
    assert not result.passed
    assert any("evidence_level" in e for e in result.errors)


def test_evidence_level_seven_fails():
    req = _make_valid_req()
    req.evidence_level = 7
    result = validate_release_request(req)
    assert not result.passed
    assert any("evidence_level" in e for e in result.errors)


def test_dry_lab_only_false_fails():
    req = _make_valid_req()
    req.dry_lab_only = False
    result = validate_release_request(req)
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


def test_invalid_safety_review_status_fails():
    req = _make_valid_req()
    req.safety_review_status = "unknown"
    result = validate_release_request(req)
    assert not result.passed
    assert any("safety_review_status" in e for e in result.errors)


def test_empty_benchmark_summary_fails():
    req = _make_valid_req()
    req.benchmark_summary = ""
    result = validate_release_request(req)
    assert not result.passed
    assert any("benchmark_summary" in e for e in result.errors)


def test_empty_known_limitations_fails():
    req = _make_valid_req()
    req.known_limitations = ""
    result = validate_release_request(req)
    assert not result.passed
    assert any("known_limitations" in e for e in result.errors)


def test_invalid_intended_use_fails():
    req = _make_valid_req()
    req.intended_use = "commercial"
    result = validate_release_request(req)
    assert not result.passed
    assert any("intended_use" in e for e in result.errors)


def test_public_release_with_pending_safety_fails():
    req = _make_valid_req()
    req.intended_use = "public"
    req.safety_review_status = "pending"
    result = validate_release_request(req)
    assert not result.passed
    assert any("safety_review_status" in e for e in result.errors)


def test_dry_lab_only_true_with_evidence_level_5_fails():
    req = _make_valid_req()
    req.evidence_level = 5
    result = validate_release_request(req)
    assert not result.passed
    assert any("evidence_level" in e for e in result.errors)


def test_all_results_have_dry_lab_only_true():
    req = _make_valid_req()
    result = validate_release_request(req)
    assert result.dry_lab_only
    result2 = validate_release_request(req)
    assert result2.dry_lab_only


def test_validate_request_dict_passes_with_valid_dict():
    d = {
        "release_id": "REL-2026-001",
        "release_type": "schema",
        "artifact_id": "candidate_manifest",
        "artifact_version": "1.0.0",
        "requestor_name": "OpenAMP Team",
        "requestor_institution": "Open Problem Lab",
        "request_date": "2026-07-09",
        "evidence_level": 2,
        "dry_lab_only": True,
        "safety_review_status": "approved",
        "benchmark_summary": "Passes all schema compatibility checks",
        "known_limitations": "Dry-lab only, not wet-lab validated",
        "intended_use": "public",
        "data_license": "CC-BY-4.0",
        "human_reviewer": "maintainer",
        "review_class": "B",
        "approval_status": "pending",
    }
    result = validate_request_dict(d)
    assert result.passed


def test_valid_release_types_has_5_entries():
    assert len(VALID_RELEASE_TYPES) == 5
    assert sorted(VALID_RELEASE_TYPES) == ["candidate", "dataset", "evidence_packet", "model", "schema"]


def test_valid_safety_statuses_has_3_entries():
    assert len(VALID_SAFETY_STATUSES) == 3


def test_valid_intended_uses_has_4_entries():
    assert len(VALID_INTENDED_USES) == 4


def test_valid_approval_statuses_has_4_entries():
    assert len(VALID_APPROVAL_STATUSES) == 4


def test_valid_review_classes_has_4_entries():
    assert len(VALID_REVIEW_CLASSES) == 4


def test_model_release_warning_for_low_review_class():
    req = _make_valid_req()
    req.release_type = "model"
    req.review_class = "A"
    result = validate_release_request(req)
    assert result.passed
    assert any("review_class" in w for w in result.warnings)


def test_dict_missing_fields_fails():
    d = {"release_id": "REL-2026-001"}
    result = validate_request_dict(d)
    assert not result.passed
    assert any("Missing required fields" in e for e in result.errors)


def test_validate_request_dict_fails_with_invalid_type():
    d = {
        "release_id": "REL-2026-001",
        "release_type": "nope",
        "artifact_id": "test",
        "artifact_version": "1.0.0",
        "requestor_name": "Test",
        "requestor_institution": "Test",
        "request_date": "2026-07-09",
        "evidence_level": 2,
        "dry_lab_only": True,
        "safety_review_status": "approved",
        "benchmark_summary": "test",
        "known_limitations": "test",
        "intended_use": "research",
        "data_license": "MIT",
        "human_reviewer": "test",
        "review_class": "B",
        "approval_status": "pending",
    }
    result = validate_request_dict(d)
    assert not result.passed

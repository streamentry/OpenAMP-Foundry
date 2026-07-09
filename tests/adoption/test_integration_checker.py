from openamp_foundry.adoption.integration_checker import (
    REQUIRED_INTEGRATION_CHECKS,
    IntegrationCheckResult,
    run_integration_checks,
)


VALID_MANIFEST = {
    "candidate_id": "AMP-001",
    "sequence": "AKLWKR",
    "evidence_level": 2,
    "scopes": ["bacterial_binding"],
    "scores": {"binding_energy": 0.75},
    "uncertainty": 0.1,
    "source_modules": ["membrane_proxy"],
    "calibration_set": None,
    "safety_flags": [],
    "provenance_run_id": None,
    "dry_lab_only": True,
    "version": "1.0.0",
    "created_at": "2026-07-09T00:00:00Z",
    "notes": [],
}


def _result_dict(checks, check_name):
    for c in checks:
        if c["check_name"] == check_name:
            return c
    return None


class TestIntegrationChecker:

    def test_valid_manifest_all_passed(self):
        result = run_integration_checks(VALID_MANIFEST)
        assert result["all_passed"] is True

    def test_manifest_schema_valid_fails_when_candidate_id_missing(self):
        manifest = dict(VALID_MANIFEST)
        del manifest["candidate_id"]
        result = run_integration_checks(manifest)
        c = _result_dict(result["checks"], "manifest_schema_valid")
        assert c["passed"] is False
        assert "Missing" in c["detail"]

    def test_evidence_level_in_range_fails_when_level_zero(self):
        manifest = dict(VALID_MANIFEST)
        manifest["evidence_level"] = 0
        result = run_integration_checks(manifest)
        c = _result_dict(result["checks"], "evidence_level_in_range")
        assert c["passed"] is False
        assert "0" in c["detail"]

    def test_evidence_level_in_range_fails_when_level_seven(self):
        manifest = dict(VALID_MANIFEST)
        manifest["evidence_level"] = 7
        result = run_integration_checks(manifest)
        c = _result_dict(result["checks"], "evidence_level_in_range")
        assert c["passed"] is False
        assert "7" in c["detail"]

    def test_dry_lab_only_acknowledged_fails_when_false(self):
        manifest = dict(VALID_MANIFEST)
        manifest["dry_lab_only"] = False
        result = run_integration_checks(manifest)
        c = _result_dict(result["checks"], "dry_lab_only_acknowledged")
        assert c["passed"] is False
        assert "False" in c["detail"]

    def test_dry_lab_only_acknowledged_fails_when_key_missing(self):
        manifest = dict(VALID_MANIFEST)
        del manifest["dry_lab_only"]
        result = run_integration_checks(manifest)
        c = _result_dict(result["checks"], "dry_lab_only_acknowledged")
        assert c["passed"] is False

    def test_safety_flags_reviewed_fails_when_key_missing(self):
        manifest = dict(VALID_MANIFEST)
        del manifest["safety_flags"]
        result = run_integration_checks(manifest)
        c = _result_dict(result["checks"], "safety_flags_reviewed")
        assert c["passed"] is False

    def test_baseline_comparison_present_fails_when_scores_empty(self):
        manifest = dict(VALID_MANIFEST)
        manifest["scores"] = {}
        result = run_integration_checks(manifest)
        c = _result_dict(result["checks"], "baseline_comparison_present")
        assert c["passed"] is False

    def test_all_checks_return_dry_lab_only_true(self):
        result = run_integration_checks(VALID_MANIFEST)
        for c in result["checks"]:
            assert c["dry_lab_only"] is True

    def test_required_integration_checks_has_five_entries(self):
        assert len(REQUIRED_INTEGRATION_CHECKS) == 5

    def test_run_integration_checks_returns_dry_lab_only_true(self):
        result = run_integration_checks(VALID_MANIFEST)
        assert result["dry_lab_only"] is True

    def test_passed_count_plus_failed_count_equals_five(self):
        result = run_integration_checks(VALID_MANIFEST)
        assert result["passed_count"] + result["failed_count"] == 5

    def test_valid_manifest_failed_count_zero(self):
        result = run_integration_checks(VALID_MANIFEST)
        assert result["failed_count"] == 0

    def test_IntegrationCheckResult_dataclass(self):
        r = IntegrationCheckResult(
            check_name="test_check",
            passed=True,
            detail="test detail",
        )
        assert r.check_name == "test_check"
        assert r.passed is True
        assert r.detail == "test detail"
        assert r.dry_lab_only is True

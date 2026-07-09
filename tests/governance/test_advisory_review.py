"""Tests for external advisory review process validation."""
import pytest
from openamp_foundry.governance.advisory_review import (
    MINIMUM_REVIEWER_COUNTS,
    VALID_FINDING_SEVERITIES,
    VALID_REVIEW_STATUSES,
    VALID_REVIEW_TYPES,
    AdvisoryReview,
    AdvisoryReviewResult,
    validate_advisory_review,
    validate_advisory_review_dict,
)


def _valid_review(**kwargs) -> AdvisoryReview:
    defaults = dict(
        review_id="ADV-2026-001",
        review_type="candidate_review",
        artifact_id="OAMP-v0.7.6-candidates",
        reviewer_handle="external-advisor-1",
        assigned_date="2026-07-09",
        deadline_date="2026-07-23",
        status="pending",
        finding_severity=None,
        finding_summary="",
        resolved=False,
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return AdvisoryReview(**defaults)


class TestValidAdvisoryReview:
    def test_valid_review_passes(self):
        result = validate_advisory_review(_valid_review())
        assert result.passed is True
        assert result.errors == []

    def test_result_has_correct_review_id(self):
        result = validate_advisory_review(_valid_review())
        assert result.review_id == "ADV-2026-001"

    def test_result_has_correct_review_type(self):
        result = validate_advisory_review(_valid_review())
        assert result.review_type == "candidate_review"

    def test_all_review_types_accepted(self):
        for rt in VALID_REVIEW_TYPES:
            result = validate_advisory_review(_valid_review(review_type=rt))
            assert result.passed is True, f"Expected {rt} to pass"

    def test_all_statuses_accepted(self):
        for status in VALID_REVIEW_STATUSES:
            result = validate_advisory_review(_valid_review(status=status))
            assert result.passed is True, f"Expected status {status} to pass"

    def test_all_finding_severities_accepted(self):
        for sev in VALID_FINDING_SEVERITIES:
            result = validate_advisory_review(
                _valid_review(
                    status="completed",
                    finding_severity=sev,
                    finding_summary="Some finding.",
                )
            )
            assert result.passed is True, f"Expected severity {sev} to pass"

    def test_completed_with_summary_passes(self):
        result = validate_advisory_review(
            _valid_review(
                status="completed",
                finding_severity="minor",
                finding_summary="All looks reasonable.",
                resolved=True,
            )
        )
        assert result.passed is True


class TestInvalidAdvisoryReview:
    def test_empty_review_id_fails(self):
        result = validate_advisory_review(_valid_review(review_id=""))
        assert result.passed is False
        assert any("review_id" in e for e in result.errors)

    def test_review_id_without_adv_prefix_fails(self):
        result = validate_advisory_review(_valid_review(review_id="REV-2026-001"))
        assert result.passed is False
        assert any("ADV-" in e for e in result.errors)

    def test_invalid_review_type_fails(self):
        result = validate_advisory_review(_valid_review(review_type="informal_chat"))
        assert result.passed is False
        assert any("review_type" in e for e in result.errors)

    def test_empty_artifact_id_fails(self):
        result = validate_advisory_review(_valid_review(artifact_id=""))
        assert result.passed is False
        assert any("artifact_id" in e for e in result.errors)

    def test_empty_reviewer_handle_fails(self):
        result = validate_advisory_review(_valid_review(reviewer_handle=""))
        assert result.passed is False
        assert any("reviewer_handle" in e for e in result.errors)

    def test_invalid_assigned_date_fails(self):
        result = validate_advisory_review(_valid_review(assigned_date="09/07/2026"))
        assert result.passed is False
        assert any("assigned_date" in e for e in result.errors)

    def test_invalid_deadline_date_fails(self):
        result = validate_advisory_review(_valid_review(deadline_date="2026-7-23"))
        assert result.passed is False
        assert any("deadline_date" in e for e in result.errors)

    def test_invalid_status_fails(self):
        result = validate_advisory_review(_valid_review(status="cancelled"))
        assert result.passed is False
        assert any("status" in e for e in result.errors)

    def test_invalid_finding_severity_fails(self):
        result = validate_advisory_review(
            _valid_review(finding_severity="severe")
        )
        assert result.passed is False
        assert any("finding_severity" in e for e in result.errors)

    def test_dry_lab_only_false_fails(self):
        result = validate_advisory_review(_valid_review(dry_lab_only=False))
        assert result.passed is False
        assert any("dry_lab_only" in e for e in result.errors)


class TestAdvisoryReviewWarnings:
    def test_critical_unresolved_warns(self):
        result = validate_advisory_review(
            _valid_review(
                status="completed",
                finding_severity="critical",
                finding_summary="Critical issue found.",
                resolved=False,
            )
        )
        assert result.passed is True
        assert any("critical" in w for w in result.warnings)

    def test_completed_without_summary_warns(self):
        result = validate_advisory_review(
            _valid_review(status="completed", finding_summary="")
        )
        assert result.passed is True
        assert any("finding_summary" in w for w in result.warnings)

    def test_deferred_status_warns(self):
        result = validate_advisory_review(_valid_review(status="deferred"))
        assert result.passed is True
        assert any("deferred" in w for w in result.warnings)


class TestValidateAdvisoryReviewDict:
    def test_valid_dict_passes(self):
        d = {
            "review_id": "ADV-2026-001",
            "review_type": "candidate_review",
            "artifact_id": "OAMP-v0.7.6-candidates",
            "reviewer_handle": "external-advisor-1",
            "assigned_date": "2026-07-09",
            "deadline_date": "2026-07-23",
            "status": "pending",
        }
        result = validate_advisory_review_dict(d)
        assert result.passed is True

    def test_missing_fields_fails(self):
        result = validate_advisory_review_dict({"review_id": "ADV-2026-001"})
        assert result.passed is False
        assert any("Missing" in e for e in result.errors)


class TestConstants:
    def test_valid_review_types_has_5(self):
        assert len(VALID_REVIEW_TYPES) == 5

    def test_valid_review_statuses_has_5(self):
        assert len(VALID_REVIEW_STATUSES) == 5

    def test_valid_finding_severities_has_4(self):
        assert len(VALID_FINDING_SEVERITIES) == 4

    def test_minimum_reviewer_counts_has_5(self):
        assert len(MINIMUM_REVIEWER_COUNTS) == 5

    def test_safety_policy_review_requires_2(self):
        assert MINIMUM_REVIEWER_COUNTS["safety_policy_review"] == 2

    def test_candidate_review_requires_2(self):
        assert MINIMUM_REVIEWER_COUNTS["candidate_review"] == 2

    def test_all_results_dry_lab_only_true(self):
        result = validate_advisory_review(_valid_review())
        assert result.dry_lab_only is True

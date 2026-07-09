"""Tests for annual safety and benchmark review checklist validation."""
import pytest
from openamp_foundry.governance.annual_review import (
    VALID_ENTRY_STATUSES,
    VALID_REVIEW_SECTIONS,
    AnnualReviewEntry,
    AnnualReviewResult,
    validate_annual_review_entry,
    validate_annual_review_dict,
)


def _valid_entry(**kwargs) -> AnnualReviewEntry:
    defaults = dict(
        review_id="ANN-2026-001",
        year="2026",
        section="safety_policy",
        reviewer="maintainer-1",
        finding_count=0,
        action_items_count=0,
        status="completed",
        notes="All safety checks passed.",
        completion_date="2026-07-09",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return AnnualReviewEntry(**defaults)


class TestValidAnnualReview:
    def test_valid_entry_passes(self):
        result = validate_annual_review_entry(_valid_entry())
        assert result.passed is True
        assert result.errors == []

    def test_result_has_correct_review_id(self):
        result = validate_annual_review_entry(_valid_entry())
        assert result.review_id == "ANN-2026-001"

    def test_result_has_correct_year(self):
        result = validate_annual_review_entry(_valid_entry())
        assert result.year == "2026"

    def test_result_has_correct_section(self):
        result = validate_annual_review_entry(_valid_entry())
        assert result.section == "safety_policy"

    def test_all_sections_accepted(self):
        for section in VALID_REVIEW_SECTIONS:
            result = validate_annual_review_entry(_valid_entry(section=section))
            assert result.passed is True, f"Expected section {section!r} to pass"

    def test_all_statuses_accepted(self):
        for status in VALID_ENTRY_STATUSES:
            if status == "completed":
                result = validate_annual_review_entry(
                    _valid_entry(status=status, completion_date="2026-07-09", notes="done")
                )
            else:
                result = validate_annual_review_entry(
                    _valid_entry(status=status, completion_date="")
                )
            assert result.passed is True, f"Expected status {status!r} to pass"

    def test_pending_without_completion_date_passes(self):
        result = validate_annual_review_entry(
            _valid_entry(status="pending", completion_date="")
        )
        assert result.passed is True

    def test_dry_lab_only_is_true_in_result(self):
        result = validate_annual_review_entry(_valid_entry())
        assert result.dry_lab_only is True

    def test_findings_with_action_items_passes(self):
        result = validate_annual_review_entry(
            _valid_entry(finding_count=2, action_items_count=2)
        )
        assert result.passed is True
        assert result.warnings == []


class TestInvalidAnnualReview:
    def test_empty_review_id_fails(self):
        result = validate_annual_review_entry(_valid_entry(review_id=""))
        assert result.passed is False
        assert any("review_id" in e for e in result.errors)

    def test_review_id_without_ann_prefix_fails(self):
        result = validate_annual_review_entry(_valid_entry(review_id="REV-2026-001"))
        assert result.passed is False
        assert any("ANN-" in e for e in result.errors)

    def test_invalid_year_fails(self):
        result = validate_annual_review_entry(_valid_entry(year="26"))
        assert result.passed is False
        assert any("year" in e for e in result.errors)

    def test_invalid_section_fails(self):
        result = validate_annual_review_entry(_valid_entry(section="unknown_section"))
        assert result.passed is False
        assert any("section" in e for e in result.errors)

    def test_empty_reviewer_fails(self):
        result = validate_annual_review_entry(_valid_entry(reviewer=""))
        assert result.passed is False
        assert any("reviewer" in e for e in result.errors)

    def test_negative_finding_count_fails(self):
        result = validate_annual_review_entry(_valid_entry(finding_count=-1))
        assert result.passed is False
        assert any("finding_count" in e for e in result.errors)

    def test_negative_action_items_count_fails(self):
        result = validate_annual_review_entry(_valid_entry(action_items_count=-1))
        assert result.passed is False
        assert any("action_items_count" in e for e in result.errors)

    def test_invalid_status_fails(self):
        result = validate_annual_review_entry(_valid_entry(status="skipped"))
        assert result.passed is False
        assert any("status" in e for e in result.errors)

    def test_completed_without_completion_date_fails(self):
        result = validate_annual_review_entry(
            _valid_entry(status="completed", completion_date="")
        )
        assert result.passed is False
        assert any("completion_date" in e for e in result.errors)

    def test_completed_with_bad_date_format_fails(self):
        result = validate_annual_review_entry(
            _valid_entry(status="completed", completion_date="09-07-2026")
        )
        assert result.passed is False
        assert any("completion_date" in e for e in result.errors)

    def test_dry_lab_only_false_fails(self):
        result = validate_annual_review_entry(_valid_entry(dry_lab_only=False))
        assert result.passed is False
        assert any("dry_lab_only" in e for e in result.errors)


class TestAnnualReviewWarnings:
    def test_completed_no_notes_warns(self):
        result = validate_annual_review_entry(
            _valid_entry(status="completed", notes="", completion_date="2026-07-09")
        )
        assert result.passed is True
        assert any("notes" in w for w in result.warnings)

    def test_deferred_warns(self):
        result = validate_annual_review_entry(
            _valid_entry(status="deferred", completion_date="")
        )
        assert result.passed is True
        assert any("deferred" in w for w in result.warnings)

    def test_findings_without_action_items_warns(self):
        result = validate_annual_review_entry(
            _valid_entry(finding_count=3, action_items_count=0)
        )
        assert result.passed is True
        assert any("action_items" in w for w in result.warnings)

    def test_no_warning_when_findings_have_action_items(self):
        result = validate_annual_review_entry(
            _valid_entry(finding_count=1, action_items_count=1)
        )
        assert result.passed is True
        assert not any("action_items" in w for w in result.warnings)


class TestValidateAnnualReviewDict:
    def test_valid_dict_passes(self):
        d = {
            "review_id": "ANN-2026-002",
            "year": "2026",
            "section": "benchmark_thresholds",
            "reviewer": "maintainer-2",
            "finding_count": 0,
            "action_items_count": 0,
            "status": "completed",
            "notes": "Thresholds reviewed and unchanged.",
            "completion_date": "2026-07-09",
            "dry_lab_only": True,
        }
        result = validate_annual_review_dict(d)
        assert result.passed is True

    def test_missing_fields_fails(self):
        result = validate_annual_review_dict({"review_id": "ANN-2026-003"})
        assert result.passed is False
        assert any("Missing required fields" in e for e in result.errors)

    def test_empty_dict_fails(self):
        result = validate_annual_review_dict({})
        assert result.passed is False

    def test_dict_defaults_dry_lab_only_true(self):
        d = {
            "review_id": "ANN-2026-004",
            "year": "2026",
            "section": "calibration_status",
            "reviewer": "maintainer-1",
            "finding_count": 0,
            "action_items_count": 0,
            "status": "pending",
        }
        result = validate_annual_review_dict(d)
        assert result.dry_lab_only is True

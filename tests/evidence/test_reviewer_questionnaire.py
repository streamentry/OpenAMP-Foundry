"""Tests for ReviewerQuestionnaire schema — Phase E E3."""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.reviewer_questionnaire import (
    ReviewerQuestionnaire,
    ReviewerQuestionnaireResult,
    validate_reviewer_questionnaire,
    validate_reviewer_questionnaire_dict,
)


def _valid_entry(**overrides) -> ReviewerQuestionnaire:
    defaults = dict(
        rvq_id="RVQ-001",
        pipeline_version="v0.10.12",
        pep_id="PEP-001",
        reviewer_token="REV-TOKEN-A",
        review_date="2026-07-10",
        activity_prediction_clarity=4,
        safety_claim_clarity=4,
        novelty_claim_clarity=3,
        overall_package_quality=4,
        would_recommend_for_synthesis="yes",
        missing_information=[],
        reviewer_comments="Package is clear and well-documented.",
        dry_lab_only=True,
    )
    defaults.update(overrides)
    return ReviewerQuestionnaire(**defaults)


# ── 1. RVQ ID validation ──────────────────────────────────────────────────────

class TestRvqIdValidation:
    def test_valid_rvq_prefix(self):
        result = validate_reviewer_questionnaire(_valid_entry())
        assert result.passed

    def test_wrong_prefix_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(rvq_id="PEP-001"))
        assert not result.passed
        assert any("rvq_id must start with 'RVQ-'" in e for e in result.errors)

    def test_empty_rvq_id_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(rvq_id=""))
        assert not result.passed

    def test_lowercase_prefix_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(rvq_id="rvq-001"))
        assert not result.passed

    def test_rvq_long_id_passes(self):
        result = validate_reviewer_questionnaire(_valid_entry(rvq_id="RVQ-20260710-001"))
        assert result.passed

    def test_rvq_id_in_result(self):
        result = validate_reviewer_questionnaire(_valid_entry(rvq_id="RVQ-XYZ"))
        assert result.rvq_id == "RVQ-XYZ"

    def test_no_prefix_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(rvq_id="001"))
        assert not result.passed


# ── 2. PEP ID validation ──────────────────────────────────────────────────────

class TestPepIdValidation:
    def test_valid_pep_prefix(self):
        result = validate_reviewer_questionnaire(_valid_entry())
        assert result.passed

    def test_wrong_pep_prefix_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(pep_id="ESC-001"))
        assert not result.passed
        assert any("pep_id must start with 'PEP-'" in e for e in result.errors)

    def test_empty_pep_id_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(pep_id=""))
        assert not result.passed

    def test_pep_id_in_result(self):
        result = validate_reviewer_questionnaire(_valid_entry(pep_id="PEP-999"))
        assert result.pep_id == "PEP-999"

    def test_pep_long_id_passes(self):
        result = validate_reviewer_questionnaire(_valid_entry(pep_id="PEP-2026-001"))
        assert result.passed


# ── 3. Required fields ────────────────────────────────────────────────────────

class TestRequiredFields:
    def test_all_valid_passes(self):
        result = validate_reviewer_questionnaire(_valid_entry())
        assert result.passed

    def test_empty_pipeline_version_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(pipeline_version=""))
        assert not result.passed
        assert any("pipeline_version must not be empty" in e for e in result.errors)

    def test_whitespace_pipeline_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(pipeline_version="   "))
        assert not result.passed

    def test_empty_reviewer_token_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(reviewer_token=""))
        assert not result.passed
        assert any("reviewer_token must not be empty" in e for e in result.errors)

    def test_whitespace_reviewer_token_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(reviewer_token="  "))
        assert not result.passed

    def test_multiple_empty_fails_all_reported(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(pipeline_version="", reviewer_token="")
        )
        assert not result.passed
        assert len([e for e in result.errors if "must not be empty" in e]) == 2


# ── 4. Review date ────────────────────────────────────────────────────────────

class TestReviewDate:
    def test_valid_date(self):
        result = validate_reviewer_questionnaire(_valid_entry(review_date="2026-07-10"))
        assert result.passed

    def test_date_without_dashes_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(review_date="20260710"))
        assert not result.passed
        assert any("review_date must be ISO format" in e for e in result.errors)

    def test_slash_date_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(review_date="2026/07/10"))
        assert not result.passed

    def test_empty_date_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(review_date=""))
        assert not result.passed

    def test_another_valid_date(self):
        result = validate_reviewer_questionnaire(_valid_entry(review_date="2025-12-31"))
        assert result.passed


# ── 5. Likert scale validation ────────────────────────────────────────────────

class TestLikertScaleValidation:
    def test_all_scores_at_max(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(
                activity_prediction_clarity=5,
                safety_claim_clarity=5,
                novelty_claim_clarity=5,
                overall_package_quality=5,
            )
        )
        assert result.passed

    def test_all_scores_at_min(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(
                activity_prediction_clarity=1,
                safety_claim_clarity=1,
                novelty_claim_clarity=1,
                overall_package_quality=1,
            )
        )
        assert result.passed

    def test_activity_zero_fails(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(activity_prediction_clarity=0)
        )
        assert not result.passed
        assert any("activity_prediction_clarity must be in [1, 5]" in e
                   for e in result.errors)

    def test_activity_six_fails(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(activity_prediction_clarity=6)
        )
        assert not result.passed

    def test_safety_zero_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(safety_claim_clarity=0))
        assert not result.passed
        assert any("safety_claim_clarity must be in [1, 5]" in e for e in result.errors)

    def test_novelty_zero_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(novelty_claim_clarity=0))
        assert not result.passed
        assert any("novelty_claim_clarity must be in [1, 5]" in e for e in result.errors)

    def test_overall_zero_fails(self):
        result = validate_reviewer_questionnaire(_valid_entry(overall_package_quality=0))
        assert not result.passed
        assert any("overall_package_quality must be in [1, 5]" in e for e in result.errors)

    def test_overall_in_result(self):
        result = validate_reviewer_questionnaire(_valid_entry(overall_package_quality=3))
        assert result.overall_package_quality == 3

    def test_middle_scores_pass(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(
                activity_prediction_clarity=3,
                safety_claim_clarity=2,
                novelty_claim_clarity=4,
                overall_package_quality=3,
            )
        )
        assert result.passed


# ── 6. Recommendation validation ──────────────────────────────────────────────

class TestRecommendationValidation:
    def test_yes_passes(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(would_recommend_for_synthesis="yes")
        )
        assert result.passed

    def test_no_passes(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(
                would_recommend_for_synthesis="no",
                reviewer_comments="Not ready.",
            )
        )
        assert result.passed

    def test_conditional_passes(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(
                would_recommend_for_synthesis="conditional",
                reviewer_comments="Needs more baseline comparison.",
            )
        )
        assert result.passed

    def test_insufficient_information_passes(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(
                would_recommend_for_synthesis="insufficient_information",
                missing_information=["safety clearance missing"],
            )
        )
        assert result.passed

    def test_invalid_recommendation_fails(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(would_recommend_for_synthesis="maybe")
        )
        assert not result.passed
        assert any("would_recommend_for_synthesis must be one of" in e
                   for e in result.errors)

    def test_empty_recommendation_fails(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(would_recommend_for_synthesis="")
        )
        assert not result.passed

    def test_recommendation_in_result(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(would_recommend_for_synthesis="conditional",
                         reviewer_comments="Condition: add baseline comparison.")
        )
        assert result.would_recommend_for_synthesis == "conditional"


# ── 7. Reviewer comments ──────────────────────────────────────────────────────

class TestReviewerComments:
    def test_valid_comments_pass(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(reviewer_comments="Good package overall.")
        )
        assert result.passed

    def test_empty_comments_pass(self):
        # empty comments is OK unless conditional/no recommendation
        result = validate_reviewer_questionnaire(_valid_entry(reviewer_comments=""))
        assert result.passed

    def test_comments_at_limit_passes(self):
        comments = "x" * 600
        result = validate_reviewer_questionnaire(_valid_entry(reviewer_comments=comments))
        assert result.passed

    def test_comments_over_limit_fails(self):
        comments = "x" * 601
        result = validate_reviewer_questionnaire(_valid_entry(reviewer_comments=comments))
        assert not result.passed
        assert any("reviewer_comments must be at most 600" in e for e in result.errors)

    def test_comments_just_over_limit_fails(self):
        comments = "y" * 602
        result = validate_reviewer_questionnaire(_valid_entry(reviewer_comments=comments))
        assert not result.passed


# ── 8. Warnings ───────────────────────────────────────────────────────────────

class TestWarnings:
    def test_low_overall_quality_warns(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(overall_package_quality=2)
        )
        assert result.passed
        assert any("overall_package_quality" in w and "2/5" in w for w in result.warnings)

    def test_high_overall_quality_no_warning(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(overall_package_quality=4)
        )
        assert result.passed
        assert not any("overall_package_quality" in w for w in result.warnings)

    def test_conditional_no_comments_warns(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(
                would_recommend_for_synthesis="conditional",
                reviewer_comments="",
            )
        )
        assert result.passed
        assert any("conditional" in w for w in result.warnings)

    def test_no_recommendation_no_info_warns(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(
                would_recommend_for_synthesis="no",
                missing_information=[],
                reviewer_comments="",
            )
        )
        assert result.passed
        assert any("'no'" in w for w in result.warnings)

    def test_insufficient_info_no_list_warns(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(
                would_recommend_for_synthesis="insufficient_information",
                missing_information=[],
            )
        )
        assert result.passed
        assert any("insufficient_information" in w for w in result.warnings)

    def test_yes_recommendation_no_warnings(self):
        result = validate_reviewer_questionnaire(
            _valid_entry(
                would_recommend_for_synthesis="yes",
                overall_package_quality=4,
            )
        )
        assert result.passed
        assert len(result.warnings) == 0


# ── 9. Dict-based validator ───────────────────────────────────────────────────

class TestDictValidator:
    def test_valid_dict_passes(self):
        data = {
            "rvq_id": "RVQ-001",
            "pipeline_version": "v0.10.12",
            "pep_id": "PEP-001",
            "reviewer_token": "REV-A",
            "review_date": "2026-07-10",
            "activity_prediction_clarity": 4,
            "safety_claim_clarity": 4,
            "novelty_claim_clarity": 3,
            "overall_package_quality": 4,
            "would_recommend_for_synthesis": "yes",
            "missing_information": [],
            "reviewer_comments": "Good.",
            "dry_lab_only": True,
        }
        result = validate_reviewer_questionnaire_dict(data)
        assert result.passed

    def test_dict_wrong_rvq_prefix_fails(self):
        data = {
            "rvq_id": "BAD-001",
            "pipeline_version": "v0.10.12",
            "pep_id": "PEP-001",
            "reviewer_token": "REV-A",
            "review_date": "2026-07-10",
            "activity_prediction_clarity": 4,
            "safety_claim_clarity": 4,
            "novelty_claim_clarity": 3,
            "overall_package_quality": 4,
            "would_recommend_for_synthesis": "yes",
            "missing_information": [],
            "reviewer_comments": "ok",
        }
        result = validate_reviewer_questionnaire_dict(data)
        assert not result.passed

    def test_dict_out_of_range_likert_fails(self):
        data = {
            "rvq_id": "RVQ-001",
            "pipeline_version": "v0.10.12",
            "pep_id": "PEP-001",
            "reviewer_token": "REV-A",
            "review_date": "2026-07-10",
            "activity_prediction_clarity": 6,
            "safety_claim_clarity": 4,
            "novelty_claim_clarity": 3,
            "overall_package_quality": 4,
            "would_recommend_for_synthesis": "yes",
            "missing_information": [],
            "reviewer_comments": "ok",
        }
        result = validate_reviewer_questionnaire_dict(data)
        assert not result.passed

    def test_dict_defaults_dry_lab_true(self):
        data = {
            "rvq_id": "RVQ-001",
            "pipeline_version": "v0.10.12",
            "pep_id": "PEP-001",
            "reviewer_token": "REV-A",
            "review_date": "2026-07-10",
            "activity_prediction_clarity": 3,
            "safety_claim_clarity": 3,
            "novelty_claim_clarity": 3,
            "overall_package_quality": 3,
            "would_recommend_for_synthesis": "yes",
            "missing_information": [],
            "reviewer_comments": "ok",
        }
        result = validate_reviewer_questionnaire_dict(data)
        assert result.dry_lab_only is True

    def test_dict_multiple_errors_reported(self):
        data = {
            "rvq_id": "BAD",
            "pipeline_version": "",
            "pep_id": "WRONG",
            "reviewer_token": "",
            "review_date": "not-a-date",
            "activity_prediction_clarity": 0,
            "safety_claim_clarity": 6,
            "novelty_claim_clarity": -1,
            "overall_package_quality": 10,
            "would_recommend_for_synthesis": "invalid",
            "missing_information": [],
            "reviewer_comments": "x" * 700,
        }
        result = validate_reviewer_questionnaire_dict(data)
        assert not result.passed
        assert len(result.errors) >= 5

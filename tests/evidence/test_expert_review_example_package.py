"""Tests for ExpertReviewExamplePackage schema — Phase E E10.

Exactly 63 tests: valid baseline + each validation rule + edge cases + warnings.
"""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.expert_review_example_package import (
    ERP_PREFIX,
    MOCK_CANDIDATE_ID_PREFIXES,
    NOTES_MAX_LENGTH,
    REVIEWER_COMMENTS_MAX_LENGTH,
    SUMMARY_MAX_LENGTH,
    VALID_REVIEW_DOMAINS,
    VALID_SYNTHESIS_RECOMMENDATIONS,
    ExpertReviewExamplePackage,
    MockCandidateSummary,
    validate,
    validate_dict,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_candidate(
    candidate_id="MOCK-001",
    sequence_length=20,
    predicted_mic=2.0,
    predicted_toxicity="low",
    novelty_score=0.75,
    include_in_example=True,
) -> MockCandidateSummary:
    return MockCandidateSummary(
        candidate_id=candidate_id,
        sequence_length=sequence_length,
        predicted_mic=predicted_mic,
        predicted_toxicity=predicted_toxicity,
        novelty_score=novelty_score,
        include_in_example=include_in_example,
    )


def _valid_pkg(**overrides) -> ExpertReviewExamplePackage:
    defaults = dict(
        erp_id="ERP-20240315-001",
        pipeline_version="v2.1.0",
        example_version="v1.0",
        creation_date="2024-03-15",
        review_domain="antimicrobial_activity",
        mock_candidates=[
            _mock_candidate("MOCK-001"),
            _mock_candidate("MOCK-002", predicted_mic=4.0, novelty_score=0.6),
        ],
        overall_clarity_rating=4,
        synthesis_recommendation="proceed_with_conditions",
        reviewer_comments=(
            "Toy candidate MOCK-001 shows MIC 2 µg/mL and low toxicity. "
            "This example demonstrates the expected review format."
        ),
        dry_lab_only=True,
        is_example_data=True,
        example_use_case=(
            "Demonstrates the format for antimicrobial activity review "
            "with two toy candidates of varying MIC profiles."
        ),
        summary=(
            "Example review package: 2 mock candidates, "
            "one recommended for conditional synthesis."
        ),
        notes="",
    )
    defaults.update(overrides)
    return ExpertReviewExamplePackage(**defaults)


def _valid() -> ExpertReviewExamplePackage:
    return _valid_pkg()


def _errors(p):
    return [e for e in validate(p) if not e.startswith("WARNING:")]


def _warns(p):
    return [e for e in validate(p) if e.startswith("WARNING:")]


# ---------------------------------------------------------------------------
# Group 1: Valid baseline (3 tests)
# ---------------------------------------------------------------------------

class TestValidBaseline:
    def test_valid_returns_no_errors(self):
        assert _errors(_valid()) == []

    def test_valid_with_notes(self):
        p = _valid_pkg(notes="Used for onboarding new reviewers.")
        assert _errors(p) == []

    def test_valid_single_candidate(self):
        p = _valid_pkg(
            mock_candidates=[_mock_candidate("TOY-001")],
            summary="Single-candidate example.",
        )
        assert _errors(p) == []


# ---------------------------------------------------------------------------
# Group 2: Rule 1 — erp_id prefix (4 tests)
# ---------------------------------------------------------------------------

class TestErpIdPrefix:
    def test_wrong_prefix_rejected(self):
        p = _valid_pkg(erp_id="RVQ-001")
        assert any("erp_id" in e for e in _errors(p))

    def test_lowercase_prefix_rejected(self):
        p = _valid_pkg(erp_id="erp-001")
        assert any("erp_id" in e for e in _errors(p))

    def test_no_prefix_rejected(self):
        p = _valid_pkg(erp_id="001")
        assert any("erp_id" in e for e in _errors(p))

    def test_correct_prefix_accepted(self):
        p = _valid_pkg(erp_id="ERP-2024-001")
        assert _errors(p) == []


# ---------------------------------------------------------------------------
# Group 3: Rule 2+3 — pipeline_version and example_version (4 tests)
# ---------------------------------------------------------------------------

class TestVersionFields:
    def test_empty_pipeline_version_rejected(self):
        p = _valid_pkg(pipeline_version="")
        assert any("pipeline_version" in e for e in _errors(p))

    def test_whitespace_pipeline_version_rejected(self):
        p = _valid_pkg(pipeline_version="   ")
        assert any("pipeline_version" in e for e in _errors(p))

    def test_empty_example_version_rejected(self):
        p = _valid_pkg(example_version="")
        assert any("example_version" in e for e in _errors(p))

    def test_valid_versions(self):
        p = _valid_pkg(pipeline_version="v3.0.0", example_version="v2.1")
        assert _errors(p) == []


# ---------------------------------------------------------------------------
# Group 4: Rule 4 — creation_date ISO format (3 tests)
# ---------------------------------------------------------------------------

class TestCreationDate:
    def test_invalid_format_rejected(self):
        p = _valid_pkg(creation_date="March 15, 2024")
        assert any("creation_date" in e for e in _errors(p))

    def test_wrong_separator_rejected(self):
        p = _valid_pkg(creation_date="2024/03/15")
        assert any("creation_date" in e for e in _errors(p))

    def test_valid_iso_date(self):
        p = _valid_pkg(creation_date="2025-01-01")
        assert _errors(p) == []


# ---------------------------------------------------------------------------
# Group 5: Rule 5 — review_domain vocabulary (4 tests)
# ---------------------------------------------------------------------------

class TestReviewDomain:
    def test_invalid_domain_rejected(self):
        p = _valid_pkg(review_domain="random_domain")
        assert any("review_domain" in e for e in _errors(p))

    def test_empty_rejected(self):
        p = _valid_pkg(review_domain="")
        assert any("review_domain" in e for e in _errors(p))

    @pytest.mark.parametrize("domain", sorted(VALID_REVIEW_DOMAINS))
    def test_all_valid_domains_accepted(self, domain):
        p = _valid_pkg(review_domain=domain)
        assert _errors(p) == []


# ---------------------------------------------------------------------------
# Group 6: Rule 6 — mock_candidates count (4 tests)
# ---------------------------------------------------------------------------

class TestMockCandidatesCount:
    def test_empty_list_rejected(self):
        p = _valid_pkg(mock_candidates=[])
        assert any("mock_candidates" in e for e in _errors(p))

    def test_too_many_rejected(self):
        p = _valid_pkg(
            mock_candidates=[_mock_candidate(f"MOCK-{i:03d}") for i in range(11)]
        )
        assert any("mock_candidates" in e for e in _errors(p))

    def test_exactly_ten_accepted(self):
        p = _valid_pkg(
            mock_candidates=[_mock_candidate(f"MOCK-{i:03d}") for i in range(10)]
        )
        assert _errors(p) == []

    def test_one_candidate_accepted(self):
        p = _valid_pkg(
            mock_candidates=[_mock_candidate("DEMO-001")],
            summary="Single demo candidate.",
        )
        assert _errors(p) == []


# ---------------------------------------------------------------------------
# Group 7: Rule 7 — mock candidate ID prefixes (4 tests)
# ---------------------------------------------------------------------------

class TestMockCandidateId:
    def test_real_id_prefix_rejected(self):
        p = _valid_pkg(
            mock_candidates=[_mock_candidate("PEP-001")]
        )
        assert any("candidate_id" in e for e in _errors(p))

    @pytest.mark.parametrize("prefix", sorted(MOCK_CANDIDATE_ID_PREFIXES))
    def test_all_mock_prefixes_accepted(self, prefix):
        p = _valid_pkg(
            mock_candidates=[_mock_candidate(f"{prefix}001")]
        )
        assert _errors(p) == []


# ---------------------------------------------------------------------------
# Group 8: Rule 7 — mock candidate field validation (4 tests)
# ---------------------------------------------------------------------------

class TestMockCandidateFields:
    def test_zero_sequence_length_rejected(self):
        p = _valid_pkg(
            mock_candidates=[_mock_candidate("MOCK-001", sequence_length=0)]
        )
        assert any("sequence_length" in e for e in _errors(p))

    def test_zero_predicted_mic_rejected(self):
        p = _valid_pkg(
            mock_candidates=[_mock_candidate("MOCK-001", predicted_mic=0.0)]
        )
        assert any("predicted_mic" in e for e in _errors(p))

    def test_invalid_toxicity_rejected(self):
        p = _valid_pkg(
            mock_candidates=[_mock_candidate("MOCK-001", predicted_toxicity="unknown")]
        )
        assert any("predicted_toxicity" in e for e in _errors(p))

    def test_novelty_out_of_range_rejected(self):
        p = _valid_pkg(
            mock_candidates=[_mock_candidate("MOCK-001", novelty_score=1.5)]
        )
        assert any("novelty_score" in e for e in _errors(p))


# ---------------------------------------------------------------------------
# Group 9: Rule 8 — at least one included candidate (3 tests)
# ---------------------------------------------------------------------------

class TestIncludeInExample:
    def test_all_excluded_rejected(self):
        p = _valid_pkg(
            mock_candidates=[
                _mock_candidate("MOCK-001", include_in_example=False),
                _mock_candidate("MOCK-002", include_in_example=False),
            ]
        )
        assert any("include_in_example" in e for e in _errors(p))

    def test_one_included_accepted(self):
        p = _valid_pkg(
            mock_candidates=[
                _mock_candidate("MOCK-001", include_in_example=True),
                _mock_candidate("MOCK-002", include_in_example=False),
            ]
        )
        assert _errors(p) == []

    def test_all_included_accepted(self):
        p = _valid_pkg(
            mock_candidates=[
                _mock_candidate("MOCK-001", include_in_example=True),
                _mock_candidate("MOCK-002", include_in_example=True),
            ]
        )
        assert _errors(p) == []


# ---------------------------------------------------------------------------
# Group 10: Rule 9 — overall_clarity_rating Likert (3 tests)
# ---------------------------------------------------------------------------

class TestClarityRating:
    def test_zero_rejected(self):
        p = _valid_pkg(overall_clarity_rating=0)
        assert any("overall_clarity_rating" in e for e in _errors(p))

    def test_six_rejected(self):
        p = _valid_pkg(overall_clarity_rating=6)
        assert any("overall_clarity_rating" in e for e in _errors(p))

    def test_one_through_five_accepted(self):
        for rating in range(1, 6):
            p = _valid_pkg(overall_clarity_rating=rating)
            assert _errors(p) == [], f"Rating {rating} should be valid"


# ---------------------------------------------------------------------------
# Group 11: Rule 10 — synthesis_recommendation vocabulary (4 tests)
# ---------------------------------------------------------------------------

class TestSynthesisRecommendation:
    def test_invalid_recommendation_rejected(self):
        p = _valid_pkg(synthesis_recommendation="maybe")
        assert any("synthesis_recommendation" in e for e in _errors(p))

    def test_empty_rejected(self):
        p = _valid_pkg(synthesis_recommendation="")
        assert any("synthesis_recommendation" in e for e in _errors(p))

    @pytest.mark.parametrize("rec", sorted(VALID_SYNTHESIS_RECOMMENDATIONS))
    def test_all_valid_recommendations_accepted(self, rec):
        p = _valid_pkg(synthesis_recommendation=rec)
        assert _errors(p) == []


# ---------------------------------------------------------------------------
# Group 12: Rule 11 — reviewer_comments (3 tests)
# ---------------------------------------------------------------------------

class TestReviewerComments:
    def test_empty_rejected(self):
        p = _valid_pkg(reviewer_comments="")
        assert any("reviewer_comments" in e for e in _errors(p))

    def test_too_long_rejected(self):
        p = _valid_pkg(reviewer_comments="x" * (REVIEWER_COMMENTS_MAX_LENGTH + 1))
        assert any("reviewer_comments" in e for e in _errors(p))

    def test_at_limit_accepted(self):
        p = _valid_pkg(reviewer_comments="x" * REVIEWER_COMMENTS_MAX_LENGTH)
        assert _errors(p) == []


# ---------------------------------------------------------------------------
# Group 13: Rule 12+13 — dry_lab_only and is_example_data (3 tests)
# ---------------------------------------------------------------------------

class TestSafetyFlags:
    def test_dry_lab_only_false_rejected(self):
        p = _valid_pkg(dry_lab_only=False)
        assert any("dry_lab_only" in e for e in _errors(p))

    def test_is_example_data_false_rejected(self):
        p = _valid_pkg(is_example_data=False)
        assert any("is_example_data" in e for e in _errors(p))

    def test_both_true_accepted(self):
        p = _valid_pkg(dry_lab_only=True, is_example_data=True)
        assert _errors(p) == []


# ---------------------------------------------------------------------------
# Group 14: Rule 14+15+16 — example_use_case, summary, notes (4 tests)
# ---------------------------------------------------------------------------

class TestTextFields:
    def test_empty_example_use_case_rejected(self):
        p = _valid_pkg(example_use_case="")
        assert any("example_use_case" in e for e in _errors(p))

    def test_empty_summary_rejected(self):
        p = _valid_pkg(summary="")
        assert any("summary" in e for e in _errors(p))

    def test_summary_too_long_rejected(self):
        p = _valid_pkg(summary="x" * (SUMMARY_MAX_LENGTH + 1))
        assert any("summary" in e for e in _errors(p))

    def test_notes_too_long_rejected(self):
        p = _valid_pkg(notes="n" * (NOTES_MAX_LENGTH + 1))
        assert any("notes" in e for e in _errors(p))


# ---------------------------------------------------------------------------
# Group 15: Warnings (6 tests)
# ---------------------------------------------------------------------------

class TestWarnings:
    def test_low_clarity_rating_triggers_warning(self):
        p = _valid_pkg(overall_clarity_rating=2)
        warns = _warns(p)
        assert any("overall_clarity_rating" in w for w in warns)

    def test_excluded_candidates_triggers_warning(self):
        p = _valid_pkg(
            mock_candidates=[
                _mock_candidate("MOCK-001", include_in_example=True),
                _mock_candidate("MOCK-002", include_in_example=False),
            ]
        )
        warns = _warns(p)
        assert any("include_in_example=False" in w for w in warns)

    def test_empty_notes_triggers_warning(self):
        p = _valid_pkg(notes="")
        warns = _warns(p)
        assert any("notes" in w.lower() for w in warns)

    def test_notes_present_suppresses_notes_warning(self):
        p = _valid_pkg(notes="Used for partner onboarding.")
        warns = _warns(p)
        assert not any("notes is empty" in w for w in warns)

    def test_high_clarity_rating_no_warning(self):
        p = _valid_pkg(overall_clarity_rating=5)
        warns = _warns(p)
        assert not any("overall_clarity_rating" in w for w in warns)

    def test_all_included_no_exclusion_warning(self):
        p = _valid_pkg(
            mock_candidates=[
                _mock_candidate("MOCK-001", include_in_example=True),
                _mock_candidate("MOCK-002", include_in_example=True),
            ]
        )
        warns = _warns(p)
        assert not any("include_in_example=False" in w for w in warns)


# ---------------------------------------------------------------------------
# Group 16: validate_dict (4 tests)
# ---------------------------------------------------------------------------

class TestValidateDict:
    def test_valid_dict_returns_no_errors(self):
        data = dict(
            erp_id="ERP-20240315-001",
            pipeline_version="v2.1.0",
            example_version="v1.0",
            creation_date="2024-03-15",
            review_domain="antimicrobial_activity",
            mock_candidates=[
                dict(
                    candidate_id="MOCK-001",
                    sequence_length=20,
                    predicted_mic=2.0,
                    predicted_toxicity="low",
                    novelty_score=0.75,
                    include_in_example=True,
                )
            ],
            overall_clarity_rating=4,
            synthesis_recommendation="proceed",
            reviewer_comments="This is a toy example for reviewer onboarding.",
            dry_lab_only=True,
            is_example_data=True,
            example_use_case="Demonstrates antimicrobial activity review.",
            summary="One mock candidate, proceed recommendation.",
        )
        errs = [e for e in validate_dict(data) if not e.startswith("WARNING:")]
        assert errs == []

    def test_missing_required_field_returns_error(self):
        data = dict(erp_id="ERP-001", pipeline_version="v1.0")
        result = validate_dict(data)
        assert any("Schema construction error" in e for e in result)

    def test_invalid_field_caught_by_dict_validator(self):
        data = dict(
            erp_id="WRONG-001",
            pipeline_version="v1.0",
            example_version="v1.0",
            creation_date="2024-01-01",
            review_domain="antimicrobial_activity",
            mock_candidates=[
                dict(
                    candidate_id="MOCK-001",
                    sequence_length=20,
                    predicted_mic=2.0,
                    predicted_toxicity="low",
                    novelty_score=0.5,
                    include_in_example=True,
                )
            ],
            overall_clarity_rating=3,
            synthesis_recommendation="proceed",
            reviewer_comments="Test.",
            dry_lab_only=True,
            is_example_data=True,
            example_use_case="Test example.",
            summary="Test.",
        )
        result = validate_dict(data)
        assert any("erp_id" in e for e in result)

    def test_extra_notes_in_dict(self):
        data = dict(
            erp_id="ERP-20240315-002",
            pipeline_version="v2.1.0",
            example_version="v1.0",
            creation_date="2024-03-15",
            review_domain="toxicity_safety",
            mock_candidates=[
                dict(
                    candidate_id="TOY-001",
                    sequence_length=15,
                    predicted_mic=8.0,
                    predicted_toxicity="moderate",
                    novelty_score=0.4,
                    include_in_example=True,
                )
            ],
            overall_clarity_rating=5,
            synthesis_recommendation="reject",
            reviewer_comments="TOY-001 shows moderate toxicity; reject for synthesis.",
            dry_lab_only=True,
            is_example_data=True,
            example_use_case="Demonstrates rejection due to toxicity concerns.",
            summary="One toy candidate rejected for safety.",
            notes="Part of standard onboarding examples.",
        )
        errs = [e for e in validate_dict(data) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 17: Edge cases (7 tests)
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_erp_prefix_constant(self):
        assert ERP_PREFIX == "ERP-"

    def test_all_valid_review_domains(self):
        for domain in sorted(VALID_REVIEW_DOMAINS):
            p = _valid_pkg(review_domain=domain)
            assert _errors(p) == [], f"Domain {domain} should be valid"

    def test_all_valid_recommendations(self):
        for rec in sorted(VALID_SYNTHESIS_RECOMMENDATIONS):
            p = _valid_pkg(synthesis_recommendation=rec)
            assert _errors(p) == [], f"Recommendation {rec} should be valid"

    def test_all_mock_prefixes_accepted(self):
        for prefix in sorted(MOCK_CANDIDATE_ID_PREFIXES):
            p = _valid_pkg(
                mock_candidates=[_mock_candidate(f"{prefix}001")]
            )
            assert _errors(p) == [], f"Prefix {prefix} should be valid"

    def test_max_candidates_accepted(self):
        p = _valid_pkg(
            mock_candidates=[
                _mock_candidate(f"MOCK-{i:03d}") for i in range(10)
            ]
        )
        assert _errors(p) == []

    def test_summary_at_limit_accepted(self):
        p = _valid_pkg(summary="s" * SUMMARY_MAX_LENGTH)
        assert _errors(p) == []

    def test_negative_mic_rejected(self):
        p = _valid_pkg(
            mock_candidates=[_mock_candidate("MOCK-001", predicted_mic=-1.0)]
        )
        assert any("predicted_mic" in e for e in _errors(p))

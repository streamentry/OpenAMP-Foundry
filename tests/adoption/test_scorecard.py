"""Tests for adoption scorecard module."""
from __future__ import annotations

from openamp_foundry.adoption.scorecard import (
    SCORECARD_DIMENSIONS,
    ADOPTION_TIERS,
    DimensionScore,
    AdoptionScorecard,
    compute_adoption_tier,
    build_scorecard,
)


class TestScorecard:
    def test_perfect_scores_mature(self):
        inputs = {
            "integration_check": {"passed_checks": 5, "total_checks": 5},
            "license_compliance": {"passed_checks": 3, "total_checks": 3},
            "adapter_validation": {"passed_checks": 2, "total_checks": 2},
            "schema_compatibility": {"passed_checks": 4, "total_checks": 4},
            "contribution_readiness": {"passed_checks": 1, "total_checks": 1},
        }
        card = build_scorecard(inputs)
        assert card.adoption_tier == "mature"
        assert card.total_score == 1.0

    def test_all_zeros_not_ready(self):
        inputs = {
            "integration_check": {"passed_checks": 0, "total_checks": 5},
            "license_compliance": {"passed_checks": 0, "total_checks": 3},
            "adapter_validation": {"passed_checks": 0, "total_checks": 2},
            "schema_compatibility": {"passed_checks": 0, "total_checks": 4},
            "contribution_readiness": {"passed_checks": 0, "total_checks": 1},
        }
        card = build_scorecard(inputs)
        assert card.adoption_tier == "not_ready"
        assert card.total_score == 0.0

    def test_score_050_emerging(self):
        inputs = {
            "integration_check": {"passed_checks": 2, "total_checks": 5},
            "license_compliance": {"passed_checks": 2, "total_checks": 5},
            "adapter_validation": {"passed_checks": 2, "total_checks": 5},
            "schema_compatibility": {"passed_checks": 2, "total_checks": 5},
            "contribution_readiness": {"passed_checks": 2, "total_checks": 5},
        }
        card = build_scorecard(inputs)
        assert card.adoption_tier == "emerging"
        assert 0.40 <= card.total_score < 0.65

    def test_score_075_established(self):
        inputs = {
            "integration_check": {"passed_checks": 4, "total_checks": 5},
            "license_compliance": {"passed_checks": 3, "total_checks": 4},
            "adapter_validation": {"passed_checks": 3, "total_checks": 4},
            "schema_compatibility": {"passed_checks": 3, "total_checks": 4},
            "contribution_readiness": {"passed_checks": 3, "total_checks": 4},
        }
        card = build_scorecard(inputs)
        assert card.adoption_tier == "established"
        assert 0.65 <= card.total_score < 0.85

    def test_scorecard_dimensions_sum_to_one(self):
        total = sum(SCORECARD_DIMENSIONS.values())
        assert abs(total - 1.0) < 1e-9

    def test_scorecard_dimensions_has_5_entries(self):
        assert len(SCORECARD_DIMENSIONS) == 5

    def test_adoption_tiers_has_4_entries(self):
        assert len(ADOPTION_TIERS) == 4

    def test_dimensionscore_dry_lab_only_default(self):
        ds = DimensionScore(
            dimension="test", weight=0.5, raw_score=0.8,
            weighted_score=0.4, passed_checks=4, total_checks=5,
        )
        assert ds.dry_lab_only is True

    def test_adoption_scorecard_dry_lab_only_default(self):
        card = AdoptionScorecard(
            total_score=0.0, adoption_tier="not_ready",
            dimensions=[], summary="", recommendations=[],
        )
        assert card.dry_lab_only is True

    def test_recommendations_empty_when_all_pass(self):
        inputs = {
            "integration_check": {"passed_checks": 5, "total_checks": 5},
            "license_compliance": {"passed_checks": 3, "total_checks": 3},
            "adapter_validation": {"passed_checks": 2, "total_checks": 2},
            "schema_compatibility": {"passed_checks": 4, "total_checks": 4},
            "contribution_readiness": {"passed_checks": 1, "total_checks": 1},
        }
        card = build_scorecard(inputs)
        assert card.recommendations == []

    def test_recommendations_populated_on_failures(self):
        inputs = {
            "integration_check": {"passed_checks": 3, "total_checks": 5},
            "license_compliance": {"passed_checks": 3, "total_checks": 3},
            "adapter_validation": {"passed_checks": 2, "total_checks": 2},
            "schema_compatibility": {"passed_checks": 4, "total_checks": 4},
            "contribution_readiness": {"passed_checks": 1, "total_checks": 1},
        }
        card = build_scorecard(inputs)
        assert len(card.recommendations) == 1
        assert "integration_check" in card.recommendations[0]
        assert "2" in card.recommendations[0]

    def test_total_score_weighted_sum(self):
        inputs = {
            "integration_check": {"passed_checks": 5, "total_checks": 5},
            "license_compliance": {"passed_checks": 2, "total_checks": 4},
            "adapter_validation": {"passed_checks": 2, "total_checks": 2},
            "schema_compatibility": {"passed_checks": 4, "total_checks": 4},
            "contribution_readiness": {"passed_checks": 1, "total_checks": 1},
        }
        card = build_scorecard(inputs)
        expected = (
            1.0 * 0.25 +
            0.5 * 0.20 +
            1.0 * 0.20 +
            1.0 * 0.20 +
            1.0 * 0.15
        )
        assert abs(card.total_score - expected) < 1e-4

    def test_missing_dimension_defaults_to_zero(self):
        inputs = {}
        card = build_scorecard(inputs)
        assert card.total_score == 0.0
        for dim in card.dimensions:
            assert dim.raw_score == 0.0
            assert dim.total_checks == 0

    def test_compute_tier_zero(self):
        assert compute_adoption_tier(0.0) == "not_ready"

    def test_compute_tier_one(self):
        assert compute_adoption_tier(1.0) == "mature"

    def test_compute_tier_boundaries(self):
        assert compute_adoption_tier(0.39) == "not_ready"
        assert compute_adoption_tier(0.40) == "emerging"
        assert compute_adoption_tier(0.64) == "emerging"
        assert compute_adoption_tier(0.65) == "established"
        assert compute_adoption_tier(0.84) == "established"
        assert compute_adoption_tier(0.85) == "mature"

    def test_build_scorecard_returns_correct_fields(self):
        inputs = {
            "integration_check": {"passed_checks": 5, "total_checks": 5},
            "license_compliance": {"passed_checks": 3, "total_checks": 3},
            "adapter_validation": {"passed_checks": 2, "total_checks": 2},
            "schema_compatibility": {"passed_checks": 4, "total_checks": 4},
            "contribution_readiness": {"passed_checks": 1, "total_checks": 1},
        }
        card = build_scorecard(inputs)
        assert isinstance(card, AdoptionScorecard)
        assert isinstance(card.total_score, float)
        assert isinstance(card.adoption_tier, str)
        assert isinstance(card.dimensions, list)
        assert len(card.dimensions) == 5
        assert isinstance(card.summary, str)
        assert isinstance(card.recommendations, list)
        assert card.dry_lab_only is True

"""Tests for batch experiment priority ranker validation."""
import pytest
from openamp_foundry.evidence.batch_priority import (
    VALID_EVIDENCE_LEVELS,
    VALID_NOVELTY_TIERS,
    VALID_SYNTHESIS_COMPLEXITIES,
    BatchPriorityEntry,
    BatchPriorityResult,
    validate_batch_priority,
    validate_batch_priority_dict,
)


def _valid_entry(**kwargs) -> BatchPriorityEntry:
    defaults = dict(
        priority_id="PRI-2026-001",
        batch_id="batch-2026-001",
        candidate_id="OAMP-001",
        pipeline_version="v0.8.0",
        priority_rank=1,
        priority_score=0.87,
        evidence_level=3,
        synthesis_complexity="low",
        novelty_tier="high",
        primary_rationale="Top ensemble score with selectivity > 2, low synthesis risk.",
        disqualifying_concerns=[],
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return BatchPriorityEntry(**defaults)


class TestValidBatchPriority:
    def test_valid_entry_passes(self):
        result = validate_batch_priority(_valid_entry())
        assert result.passed is True
        assert result.errors == []

    def test_result_has_correct_priority_id(self):
        result = validate_batch_priority(_valid_entry())
        assert result.priority_id == "PRI-2026-001"

    def test_result_has_correct_candidate_id(self):
        result = validate_batch_priority(_valid_entry())
        assert result.candidate_id == "OAMP-001"

    def test_result_has_correct_priority_rank(self):
        result = validate_batch_priority(_valid_entry())
        assert result.priority_rank == 1

    def test_all_evidence_levels_accepted(self):
        for level in VALID_EVIDENCE_LEVELS:
            result = validate_batch_priority(_valid_entry(evidence_level=level))
            assert result.passed is True, f"Expected level {level} to pass"

    def test_all_synthesis_complexities_accepted(self):
        for sc in VALID_SYNTHESIS_COMPLEXITIES:
            result = validate_batch_priority(_valid_entry(synthesis_complexity=sc))
            assert result.passed is True, f"Expected complexity {sc!r} to pass"

    def test_all_novelty_tiers_accepted(self):
        for nt in VALID_NOVELTY_TIERS:
            result = validate_batch_priority(_valid_entry(novelty_tier=nt))
            assert result.passed is True, f"Expected novelty tier {nt!r} to pass"

    def test_dry_lab_only_is_true_in_result(self):
        result = validate_batch_priority(_valid_entry())
        assert result.dry_lab_only is True

    def test_priority_rank_10_passes(self):
        result = validate_batch_priority(_valid_entry(priority_rank=10))
        assert result.passed is True

    def test_priority_score_zero_passes(self):
        result = validate_batch_priority(_valid_entry(priority_score=0.0))
        assert result.passed is True

    def test_priority_score_one_passes(self):
        result = validate_batch_priority(_valid_entry(priority_score=1.0))
        assert result.passed is True

    def test_with_disqualifying_concerns_passes(self):
        result = validate_batch_priority(
            _valid_entry(disqualifying_concerns=["hemolysis risk at high dose, considered acceptable"])
        )
        assert result.passed is True


class TestInvalidBatchPriority:
    def test_empty_priority_id_fails(self):
        result = validate_batch_priority(_valid_entry(priority_id=""))
        assert result.passed is False
        assert any("priority_id" in e for e in result.errors)

    def test_priority_id_without_pri_prefix_fails(self):
        result = validate_batch_priority(_valid_entry(priority_id="CAND-2026-001"))
        assert result.passed is False
        assert any("PRI-" in e for e in result.errors)

    def test_empty_batch_id_fails(self):
        result = validate_batch_priority(_valid_entry(batch_id=""))
        assert result.passed is False
        assert any("batch_id" in e for e in result.errors)

    def test_empty_candidate_id_fails(self):
        result = validate_batch_priority(_valid_entry(candidate_id=""))
        assert result.passed is False
        assert any("candidate_id" in e for e in result.errors)

    def test_empty_pipeline_version_fails(self):
        result = validate_batch_priority(_valid_entry(pipeline_version=""))
        assert result.passed is False
        assert any("pipeline_version" in e for e in result.errors)

    def test_priority_rank_zero_fails(self):
        result = validate_batch_priority(_valid_entry(priority_rank=0))
        assert result.passed is False
        assert any("priority_rank" in e for e in result.errors)

    def test_priority_rank_negative_fails(self):
        result = validate_batch_priority(_valid_entry(priority_rank=-1))
        assert result.passed is False
        assert any("priority_rank" in e for e in result.errors)

    def test_priority_score_negative_fails(self):
        result = validate_batch_priority(_valid_entry(priority_score=-0.1))
        assert result.passed is False
        assert any("priority_score" in e for e in result.errors)

    def test_priority_score_above_one_fails(self):
        result = validate_batch_priority(_valid_entry(priority_score=1.1))
        assert result.passed is False
        assert any("priority_score" in e for e in result.errors)

    def test_invalid_evidence_level_fails(self):
        result = validate_batch_priority(_valid_entry(evidence_level=7))
        assert result.passed is False
        assert any("evidence_level" in e for e in result.errors)

    def test_invalid_synthesis_complexity_fails(self):
        result = validate_batch_priority(_valid_entry(synthesis_complexity="very_high"))
        assert result.passed is False
        assert any("synthesis_complexity" in e for e in result.errors)

    def test_invalid_novelty_tier_fails(self):
        result = validate_batch_priority(_valid_entry(novelty_tier="very_high"))
        assert result.passed is False
        assert any("novelty_tier" in e for e in result.errors)

    def test_empty_primary_rationale_fails(self):
        result = validate_batch_priority(_valid_entry(primary_rationale=""))
        assert result.passed is False
        assert any("primary_rationale" in e for e in result.errors)

    def test_dry_lab_only_false_fails(self):
        result = validate_batch_priority(_valid_entry(dry_lab_only=False))
        assert result.passed is False
        assert any("dry_lab_only" in e for e in result.errors)


class TestBatchPriorityWarnings:
    def test_low_evidence_level_warns(self):
        result = validate_batch_priority(_valid_entry(evidence_level=1))
        assert result.passed is True
        assert any("evidence_level" in w for w in result.warnings)

    def test_evidence_level_2_warns(self):
        result = validate_batch_priority(_valid_entry(evidence_level=2))
        assert result.passed is True
        assert any("evidence_level" in w for w in result.warnings)

    def test_evidence_level_3_no_warning(self):
        result = validate_batch_priority(_valid_entry(evidence_level=3))
        assert result.passed is True
        assert not any("evidence_level" in w for w in result.warnings)

    def test_top_rank_high_complexity_warns(self):
        result = validate_batch_priority(
            _valid_entry(priority_rank=1, synthesis_complexity="high")
        )
        assert result.passed is True
        assert any("synthesis" in w for w in result.warnings)

    def test_rank2_high_complexity_no_warn(self):
        result = validate_batch_priority(
            _valid_entry(priority_rank=2, synthesis_complexity="high")
        )
        assert result.passed is True
        assert not any("synthesis" in w for w in result.warnings)

    def test_low_priority_score_warns(self):
        result = validate_batch_priority(_valid_entry(priority_score=0.2))
        assert result.passed is True
        assert any("priority_score" in w for w in result.warnings)

    def test_score_0_3_no_warn(self):
        result = validate_batch_priority(_valid_entry(priority_score=0.3))
        assert result.passed is True
        assert not any("priority_score" in w for w in result.warnings)

    def test_no_warnings_for_clean_entry(self):
        result = validate_batch_priority(_valid_entry())
        assert result.warnings == []


class TestValidateBatchPriorityDict:
    def test_valid_dict_passes(self):
        d = {
            "priority_id": "PRI-2026-002",
            "batch_id": "batch-2026-001",
            "candidate_id": "OAMP-002",
            "pipeline_version": "v0.8.0",
            "priority_rank": 2,
            "priority_score": 0.75,
            "evidence_level": 4,
            "synthesis_complexity": "medium",
            "novelty_tier": "medium",
            "primary_rationale": "Strong calibrated score, medium synthesis complexity.",
            "dry_lab_only": True,
        }
        result = validate_batch_priority_dict(d)
        assert result.passed is True

    def test_missing_fields_fails(self):
        result = validate_batch_priority_dict({"priority_id": "PRI-2026-003"})
        assert result.passed is False
        assert any("Missing required fields" in e for e in result.errors)

    def test_empty_dict_fails(self):
        result = validate_batch_priority_dict({})
        assert result.passed is False

    def test_dict_defaults_dry_lab_only_true(self):
        d = {
            "priority_id": "PRI-2026-004",
            "batch_id": "batch-2026-002",
            "candidate_id": "OAMP-003",
            "pipeline_version": "v0.8.0",
            "priority_rank": 3,
            "priority_score": 0.65,
            "evidence_level": 3,
            "synthesis_complexity": "low",
            "novelty_tier": "high",
            "primary_rationale": "Novel scaffold with acceptable risk.",
        }
        result = validate_batch_priority_dict(d)
        assert result.dry_lab_only is True

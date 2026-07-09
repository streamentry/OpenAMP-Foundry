"""Tests for selection rationale schema validation."""
import pytest
from openamp_foundry.evidence.selection_rationale import (
    MINIMUM_SAFETY_FLAGS,
    VALID_EVIDENCE_LEVELS,
    SelectionRationaleEntry,
    SelectionRationaleResult,
    validate_selection_rationale,
    validate_selection_rationale_dict,
)


def _valid_entry(**kwargs) -> SelectionRationaleEntry:
    defaults = dict(
        selection_id="SEL-2026-001",
        batch_id="batch-2026-001",
        candidate_id="OAMP-001",
        pipeline_version="v0.7.9",
        selection_date="2026-07-09",
        evidence_level=3,
        baseline_comparison="Scored above random baseline (AUROC 0.83) and charge-matched baseline (AUROC 0.71).",
        primary_criterion="Top ensemble score with selectivity index > 2 and hemolysis < 10%.",
        safety_flags_checked=["hemolysis_checked", "toxicity_checked", "novelty_verified"],
        reviewer="maintainer-1",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return SelectionRationaleEntry(**defaults)


class TestValidSelectionRationale:
    def test_valid_entry_passes(self):
        result = validate_selection_rationale(_valid_entry())
        assert result.passed is True
        assert result.errors == []

    def test_result_has_correct_selection_id(self):
        result = validate_selection_rationale(_valid_entry())
        assert result.selection_id == "SEL-2026-001"

    def test_result_has_correct_candidate_id(self):
        result = validate_selection_rationale(_valid_entry())
        assert result.candidate_id == "OAMP-001"

    def test_all_evidence_levels_accepted(self):
        for level in VALID_EVIDENCE_LEVELS:
            result = validate_selection_rationale(_valid_entry(evidence_level=level))
            assert result.passed is True, f"Expected level {level} to pass"

    def test_dry_lab_only_is_true_in_result(self):
        result = validate_selection_rationale(_valid_entry())
        assert result.dry_lab_only is True

    def test_single_safety_flag_passes(self):
        result = validate_selection_rationale(
            _valid_entry(safety_flags_checked=["hemolysis_checked"])
        )
        assert result.passed is True

    def test_many_safety_flags_pass(self):
        flags = ["hemolysis_checked", "toxicity_checked", "novelty_verified", "dual_use_reviewed"]
        result = validate_selection_rationale(_valid_entry(safety_flags_checked=flags))
        assert result.passed is True

    def test_high_evidence_level_no_warning(self):
        result = validate_selection_rationale(_valid_entry(evidence_level=4))
        assert result.passed is True
        assert not any("evidence_level" in w for w in result.warnings)


class TestInvalidSelectionRationale:
    def test_empty_selection_id_fails(self):
        result = validate_selection_rationale(_valid_entry(selection_id=""))
        assert result.passed is False
        assert any("selection_id" in e for e in result.errors)

    def test_selection_id_without_sel_prefix_fails(self):
        result = validate_selection_rationale(_valid_entry(selection_id="CAND-2026-001"))
        assert result.passed is False
        assert any("SEL-" in e for e in result.errors)

    def test_empty_batch_id_fails(self):
        result = validate_selection_rationale(_valid_entry(batch_id=""))
        assert result.passed is False
        assert any("batch_id" in e for e in result.errors)

    def test_empty_candidate_id_fails(self):
        result = validate_selection_rationale(_valid_entry(candidate_id=""))
        assert result.passed is False
        assert any("candidate_id" in e for e in result.errors)

    def test_empty_pipeline_version_fails(self):
        result = validate_selection_rationale(_valid_entry(pipeline_version=""))
        assert result.passed is False
        assert any("pipeline_version" in e for e in result.errors)

    def test_invalid_date_format_fails(self):
        result = validate_selection_rationale(_valid_entry(selection_date="09/07/2026"))
        assert result.passed is False
        assert any("selection_date" in e for e in result.errors)

    def test_invalid_evidence_level_fails(self):
        result = validate_selection_rationale(_valid_entry(evidence_level=7))
        assert result.passed is False
        assert any("evidence_level" in e for e in result.errors)

    def test_zero_evidence_level_fails(self):
        result = validate_selection_rationale(_valid_entry(evidence_level=0))
        assert result.passed is False
        assert any("evidence_level" in e for e in result.errors)

    def test_empty_baseline_comparison_fails(self):
        result = validate_selection_rationale(_valid_entry(baseline_comparison=""))
        assert result.passed is False
        assert any("baseline_comparison" in e for e in result.errors)

    def test_empty_primary_criterion_fails(self):
        result = validate_selection_rationale(_valid_entry(primary_criterion=""))
        assert result.passed is False
        assert any("primary_criterion" in e for e in result.errors)

    def test_empty_safety_flags_fails(self):
        result = validate_selection_rationale(_valid_entry(safety_flags_checked=[]))
        assert result.passed is False
        assert any("safety_flags_checked" in e for e in result.errors)

    def test_safety_flags_not_list_fails(self):
        result = validate_selection_rationale(_valid_entry(safety_flags_checked="hemolysis"))
        assert result.passed is False
        assert any("safety_flags_checked" in e for e in result.errors)

    def test_empty_reviewer_fails(self):
        result = validate_selection_rationale(_valid_entry(reviewer=""))
        assert result.passed is False
        assert any("reviewer" in e for e in result.errors)

    def test_dry_lab_only_false_fails(self):
        result = validate_selection_rationale(_valid_entry(dry_lab_only=False))
        assert result.passed is False
        assert any("dry_lab_only" in e for e in result.errors)


class TestSelectionRationaleWarnings:
    def test_low_evidence_level_warns(self):
        result = validate_selection_rationale(_valid_entry(evidence_level=1))
        assert result.passed is True
        assert any("evidence_level" in w for w in result.warnings)

    def test_evidence_level_2_warns(self):
        result = validate_selection_rationale(_valid_entry(evidence_level=2))
        assert result.passed is True
        assert any("evidence_level" in w for w in result.warnings)

    def test_evidence_level_3_no_warning(self):
        result = validate_selection_rationale(_valid_entry(evidence_level=3))
        assert result.passed is True
        assert not any("evidence_level" in w for w in result.warnings)

    def test_no_warnings_for_clean_entry(self):
        result = validate_selection_rationale(_valid_entry())
        assert result.warnings == []


class TestValidateSelectionRationaleDict:
    def test_valid_dict_passes(self):
        d = {
            "selection_id": "SEL-2026-002",
            "batch_id": "batch-2026-001",
            "candidate_id": "OAMP-002",
            "pipeline_version": "v0.7.9",
            "selection_date": "2026-07-09",
            "evidence_level": 4,
            "baseline_comparison": "Outperforms charge-matched baseline by 12 AUROC points.",
            "primary_criterion": "High selectivity and novel scaffold.",
            "safety_flags_checked": ["hemolysis_checked", "dual_use_reviewed"],
            "reviewer": "maintainer-2",
            "dry_lab_only": True,
        }
        result = validate_selection_rationale_dict(d)
        assert result.passed is True

    def test_missing_fields_fails(self):
        result = validate_selection_rationale_dict({"selection_id": "SEL-2026-003"})
        assert result.passed is False
        assert any("Missing required fields" in e for e in result.errors)

    def test_empty_dict_fails(self):
        result = validate_selection_rationale_dict({})
        assert result.passed is False

    def test_dict_defaults_dry_lab_only_true(self):
        d = {
            "selection_id": "SEL-2026-004",
            "batch_id": "batch-2026-002",
            "candidate_id": "OAMP-003",
            "pipeline_version": "v0.7.9",
            "selection_date": "2026-07-09",
            "evidence_level": 3,
            "baseline_comparison": "Above random baseline.",
            "primary_criterion": "Novel scaffold.",
            "safety_flags_checked": ["hemolysis_checked"],
            "reviewer": "agent-1",
        }
        result = validate_selection_rationale_dict(d)
        assert result.dry_lab_only is True

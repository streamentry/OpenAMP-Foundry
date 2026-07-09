"""Tests for batch selection proposal schema — Phase P P1."""

import pytest
from openamp_foundry.evidence.batch_selection_proposal import (
    BatchSelectionProposalEntry,
    validate_batch_selection_proposal,
    validate_batch_selection_proposal_dict,
    BSP_PREFIX,
    CRG_PREFIX,
    VALID_SELECTION_STRATEGIES,
    PROPOSAL_NOTES_MAX_LENGTH,
    FRACTION_SUM_TOLERANCE,
    MIN_CANDIDATES,
    POOR_CALIBRATION_BRIER_THRESHOLD,
    PURE_EXPLOITATION_THRESHOLD,
)


def _valid_entry(**kwargs) -> BatchSelectionProposalEntry:
    defaults = dict(
        bsp_id="BSP-001",
        pipeline_version="v1.0.0",
        gate_id="CRG-001",
        gate_passed=True,
        candidate_ids=["CAND-001", "CAND-002", "CAND-003"],
        selection_strategy="hybrid",
        exploitation_fraction=0.6,
        exploration_fraction=0.4,
        max_brier_score_allowed=0.20,
        proposal_notes="Hybrid strategy for batch 2.",
        reviewer="reviewer@example.com",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return BatchSelectionProposalEntry(**defaults)


class TestValidEntry:
    def test_valid_passes(self):
        r = validate_batch_selection_proposal(_valid_entry())
        assert r.passed
        assert r.errors == []

    def test_result_fields(self):
        r = validate_batch_selection_proposal(_valid_entry())
        assert r.bsp_id == "BSP-001"
        assert r.pipeline_version == "v1.0.0"
        assert r.gate_id == "CRG-001"
        assert r.gate_passed is True
        assert r.candidate_count == 3
        assert r.selection_strategy == "hybrid"
        assert r.dry_lab_only is True

    def test_exploitation_strategy(self):
        r = validate_batch_selection_proposal(
            _valid_entry(selection_strategy="exploitation", exploitation_fraction=0.8, exploration_fraction=0.2)
        )
        assert r.passed

    def test_exploration_strategy(self):
        r = validate_batch_selection_proposal(
            _valid_entry(selection_strategy="exploration", exploitation_fraction=0.2, exploration_fraction=0.8)
        )
        assert r.passed

    def test_diversity_strategy(self):
        r = validate_batch_selection_proposal(
            _valid_entry(selection_strategy="diversity", exploitation_fraction=0.5, exploration_fraction=0.5)
        )
        assert r.passed

    def test_uncertainty_sampling_strategy(self):
        r = validate_batch_selection_proposal(
            _valid_entry(selection_strategy="uncertainty_sampling", exploitation_fraction=0.3, exploration_fraction=0.7)
        )
        assert r.passed

    def test_equal_split(self):
        r = validate_batch_selection_proposal(
            _valid_entry(exploitation_fraction=0.5, exploration_fraction=0.5)
        )
        assert r.passed

    def test_no_warnings_for_normal_entry(self):
        r = validate_batch_selection_proposal(_valid_entry())
        assert r.warnings == []

    def test_single_candidate_warning(self):
        r = validate_batch_selection_proposal(
            _valid_entry(candidate_ids=["CAND-001"])
        )
        assert r.passed
        assert any("single" in w or "one candidate" in w for w in r.warnings)

    def test_pure_exploitation_warning(self):
        r = validate_batch_selection_proposal(
            _valid_entry(exploitation_fraction=1.0, exploration_fraction=0.0)
        )
        assert r.passed
        assert any("exploitation" in w for w in r.warnings)

    def test_poor_calibration_brier_warning(self):
        r = validate_batch_selection_proposal(
            _valid_entry(max_brier_score_allowed=0.25)
        )
        assert r.passed
        assert any("poor-calibration" in w or "marginal" in w for w in r.warnings)

    def test_fraction_sum_within_tolerance(self):
        # 0.6 + 0.4 + tiny epsilon still within tolerance
        r = validate_batch_selection_proposal(
            _valid_entry(exploitation_fraction=0.6000001, exploration_fraction=0.4)
        )
        assert r.passed

    def test_multiple_candidates(self):
        r = validate_batch_selection_proposal(
            _valid_entry(candidate_ids=["A", "B", "C", "D", "E"])
        )
        assert r.passed
        assert r.candidate_count == 5

    def test_max_brier_at_zero(self):
        r = validate_batch_selection_proposal(
            _valid_entry(max_brier_score_allowed=0.0)
        )
        assert r.passed

    def test_max_brier_at_one(self):
        r = validate_batch_selection_proposal(
            _valid_entry(max_brier_score_allowed=1.0)
        )
        assert r.passed
        # max_brier >= POOR_CALIBRATION_BRIER_THRESHOLD → warning
        assert any("poor-calibration" in w or "marginal" in w for w in r.warnings)

    def test_empty_proposal_notes(self):
        r = validate_batch_selection_proposal(_valid_entry(proposal_notes=""))
        assert r.passed

    def test_max_length_notes(self):
        notes = "x" * PROPOSAL_NOTES_MAX_LENGTH
        r = validate_batch_selection_proposal(_valid_entry(proposal_notes=notes))
        assert r.passed

    def test_dry_lab_only_false_allowed(self):
        r = validate_batch_selection_proposal(_valid_entry(dry_lab_only=False))
        assert r.passed


class TestBspIdValidation:
    def test_missing_prefix_fails(self):
        r = validate_batch_selection_proposal(_valid_entry(bsp_id="001"))
        assert not r.passed
        assert any("bsp_id" in e for e in r.errors)

    def test_wrong_prefix_fails(self):
        r = validate_batch_selection_proposal(_valid_entry(bsp_id="CRG-001"))
        assert not r.passed
        assert any("bsp_id" in e for e in r.errors)

    def test_lowercase_prefix_fails(self):
        r = validate_batch_selection_proposal(_valid_entry(bsp_id="bsp-001"))
        assert not r.passed

    def test_prefix_only_passes(self):
        r = validate_batch_selection_proposal(_valid_entry(bsp_id="BSP-"))
        assert r.passed


class TestGateIdValidation:
    def test_missing_crg_prefix_fails(self):
        r = validate_batch_selection_proposal(_valid_entry(gate_id="001"))
        assert not r.passed
        assert any("gate_id" in e for e in r.errors)

    def test_wrong_prefix_fails(self):
        r = validate_batch_selection_proposal(_valid_entry(gate_id="BSP-001"))
        assert not r.passed
        assert any("gate_id" in e for e in r.errors)

    def test_correct_crg_prefix_passes(self):
        r = validate_batch_selection_proposal(_valid_entry(gate_id="CRG-999"))
        assert r.passed


class TestGatePassedValidation:
    def test_gate_not_passed_fails(self):
        r = validate_batch_selection_proposal(_valid_entry(gate_passed=False))
        assert not r.passed
        assert any("gate_passed" in e for e in r.errors)

    def test_gate_passed_true_is_required(self):
        entry = _valid_entry(gate_passed=False)
        r = validate_batch_selection_proposal(entry)
        assert not r.passed
        assert any("calibration readiness" in e or "gate_passed" in e for e in r.errors)


class TestCandidateIdsValidation:
    def test_empty_list_fails(self):
        r = validate_batch_selection_proposal(_valid_entry(candidate_ids=[]))
        assert not r.passed
        assert any("candidate_ids" in e for e in r.errors)

    def test_single_candidate_passes_with_warning(self):
        r = validate_batch_selection_proposal(_valid_entry(candidate_ids=["ONLY-ONE"]))
        assert r.passed
        assert r.warnings

    def test_many_candidates_passes(self):
        r = validate_batch_selection_proposal(
            _valid_entry(candidate_ids=[f"C-{i}" for i in range(20)])
        )
        assert r.passed
        assert r.candidate_count == 20


class TestSelectionStrategyValidation:
    def test_invalid_strategy_fails(self):
        r = validate_batch_selection_proposal(_valid_entry(selection_strategy="random"))
        assert not r.passed
        assert any("selection_strategy" in e for e in r.errors)

    def test_empty_strategy_fails(self):
        r = validate_batch_selection_proposal(_valid_entry(selection_strategy=""))
        assert not r.passed

    @pytest.mark.parametrize("strategy", sorted(VALID_SELECTION_STRATEGIES))
    def test_all_valid_strategies(self, strategy):
        r = validate_batch_selection_proposal(_valid_entry(selection_strategy=strategy))
        assert r.passed or all("selection_strategy" not in e for e in r.errors)


class TestFractionValidation:
    def test_exploitation_below_zero_fails(self):
        r = validate_batch_selection_proposal(
            _valid_entry(exploitation_fraction=-0.1, exploration_fraction=1.1)
        )
        assert not r.passed
        assert any("exploitation_fraction" in e for e in r.errors)

    def test_exploitation_above_one_fails(self):
        r = validate_batch_selection_proposal(
            _valid_entry(exploitation_fraction=1.1, exploration_fraction=-0.1)
        )
        assert not r.passed

    def test_exploration_below_zero_fails(self):
        r = validate_batch_selection_proposal(
            _valid_entry(exploitation_fraction=0.5, exploration_fraction=-0.5)
        )
        assert not r.passed
        assert any("exploration_fraction" in e for e in r.errors)

    def test_exploration_above_one_fails(self):
        r = validate_batch_selection_proposal(
            _valid_entry(exploitation_fraction=0.0, exploration_fraction=1.5)
        )
        assert not r.passed

    def test_fractions_not_summing_to_one_fails(self):
        r = validate_batch_selection_proposal(
            _valid_entry(exploitation_fraction=0.6, exploration_fraction=0.6)
        )
        assert not r.passed
        assert any("sum" in e or "1.0" in e for e in r.errors)

    def test_fractions_sum_zero_fails(self):
        r = validate_batch_selection_proposal(
            _valid_entry(exploitation_fraction=0.0, exploration_fraction=0.0)
        )
        assert not r.passed

    def test_fractions_sum_within_tolerance(self):
        # 0.5 + 0.5000005 slightly over 1.0 but within tolerance
        r = validate_batch_selection_proposal(
            _valid_entry(exploitation_fraction=0.5, exploration_fraction=0.5000005)
        )
        assert r.passed


class TestMaxBrierValidation:
    def test_below_zero_fails(self):
        r = validate_batch_selection_proposal(_valid_entry(max_brier_score_allowed=-0.01))
        assert not r.passed
        assert any("max_brier" in e for e in r.errors)

    def test_above_one_fails(self):
        r = validate_batch_selection_proposal(_valid_entry(max_brier_score_allowed=1.01))
        assert not r.passed
        assert any("max_brier" in e for e in r.errors)

    def test_exactly_zero_passes(self):
        r = validate_batch_selection_proposal(_valid_entry(max_brier_score_allowed=0.0))
        assert r.passed

    def test_exactly_one_passes(self):
        r = validate_batch_selection_proposal(_valid_entry(max_brier_score_allowed=1.0))
        assert r.passed


class TestProposalNotesValidation:
    def test_notes_too_long_fails(self):
        notes = "x" * (PROPOSAL_NOTES_MAX_LENGTH + 1)
        r = validate_batch_selection_proposal(_valid_entry(proposal_notes=notes))
        assert not r.passed
        assert any("proposal_notes" in e for e in r.errors)

    def test_notes_at_limit_passes(self):
        notes = "y" * PROPOSAL_NOTES_MAX_LENGTH
        r = validate_batch_selection_proposal(_valid_entry(proposal_notes=notes))
        assert r.passed


class TestDictValidation:
    def _valid_dict(self, **kwargs):
        d = dict(
            bsp_id="BSP-001",
            pipeline_version="v1.0.0",
            gate_id="CRG-001",
            gate_passed=True,
            candidate_ids=["CAND-001"],
            selection_strategy="hybrid",
            exploitation_fraction=0.6,
            exploration_fraction=0.4,
            max_brier_score_allowed=0.20,
            proposal_notes="note",
            reviewer="r@example.com",
            dry_lab_only=True,
        )
        d.update(kwargs)
        return d

    def test_valid_dict_passes(self):
        r = validate_batch_selection_proposal_dict(self._valid_dict())
        assert r.passed

    def test_missing_field_fails(self):
        d = self._valid_dict()
        del d["gate_id"]
        r = validate_batch_selection_proposal_dict(d)
        assert not r.passed
        assert any("missing" in e for e in r.errors)

    def test_missing_multiple_fields_fails(self):
        d = self._valid_dict()
        del d["gate_id"]
        del d["candidate_ids"]
        r = validate_batch_selection_proposal_dict(d)
        assert not r.passed

    def test_dry_lab_only_defaults_to_true(self):
        d = self._valid_dict()
        del d["dry_lab_only"]
        r = validate_batch_selection_proposal_dict(d)
        assert r.passed
        assert r.dry_lab_only is True

    def test_invalid_strategy_in_dict_fails(self):
        r = validate_batch_selection_proposal_dict(
            self._valid_dict(selection_strategy="bogus")
        )
        assert not r.passed

    def test_gate_not_passed_in_dict_fails(self):
        r = validate_batch_selection_proposal_dict(self._valid_dict(gate_passed=False))
        assert not r.passed


class TestMultipleErrors:
    def test_multiple_errors_accumulated(self):
        r = validate_batch_selection_proposal(
            _valid_entry(
                bsp_id="wrong",
                gate_id="wrong",
                gate_passed=False,
                candidate_ids=[],
            )
        )
        assert not r.passed
        assert len(r.errors) >= 4


class TestConstants:
    def test_bsp_prefix(self):
        assert BSP_PREFIX == "BSP-"

    def test_crg_prefix(self):
        assert CRG_PREFIX == "CRG-"

    def test_valid_strategies_count(self):
        assert len(VALID_SELECTION_STRATEGIES) == 5

    def test_notes_max_length(self):
        assert PROPOSAL_NOTES_MAX_LENGTH == 400

    def test_fraction_tolerance(self):
        assert FRACTION_SUM_TOLERANCE == 0.001

    def test_poor_brier_threshold(self):
        assert POOR_CALIBRATION_BRIER_THRESHOLD == 0.25

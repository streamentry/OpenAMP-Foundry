"""Tests for simulation ensemble agreement checker."""
from __future__ import annotations

import pytest

from openamp_foundry.simulation.ensemble_checker import (
    AGREEMENT_LEVELS,
    EnsembleAgreementResult,
    check_ensemble_agreement,
    run_ensemble_check_batch,
)
from openamp_foundry.simulation.interfaces import SimulationResult


def _make_result(
    module: str,
    score: float,
    score_key: str = "binding_energy",
) -> SimulationResult:
    return SimulationResult(
        module=module,
        version="0.1.0",
        scope=["bacterial_binding"],
        scores={score_key: score},
        uncertainty=0.1,
        calibration_set=None,
        validated_against=["APD3"],
        notes=[],
    )


class TestAgreementLevels:
    def test_sufficient_keys_present(self):
        expected_keys = {"strong", "moderate", "weak", "conflict", "insufficient"}
        assert set(AGREEMENT_LEVELS.keys()) == expected_keys

    def test_descriptions_non_empty(self):
        for desc in AGREEMENT_LEVELS.values():
            assert desc and isinstance(desc, str)


class TestCheckEnsembleAgreement:
    def test_empty_results_insufficient(self):
        result = check_ensemble_agreement("AKLWKR", [], score_key="binding_energy")
        assert result.agreement_level == "insufficient"
        assert result.mean_score is None
        assert result.score_range is None
        assert result.scores_by_module == {}

    def test_one_result_weak(self):
        results = [_make_result("membrane_proxy", 0.75)]
        result = check_ensemble_agreement("AKLWKR", results)
        assert result.agreement_level == "weak"
        assert result.mean_score == 0.75
        assert result.score_range == 0.0

    def test_two_results_within_threshold_moderate(self):
        results = [
            _make_result("membrane_proxy", 0.75),
            _make_result("structure_proxy", 0.80),
        ]
        result = check_ensemble_agreement("AKLWKR", results, threshold=0.2)
        assert result.agreement_level == "moderate"
        assert result.score_range <= 0.2

    def test_three_results_within_threshold_strong(self):
        results = [
            _make_result("membrane_proxy", 0.75),
            _make_result("structure_proxy", 0.80),
            _make_result("docking_proxy", 0.78),
        ]
        result = check_ensemble_agreement("AKLWKR", results, threshold=0.2)
        assert result.agreement_level == "strong"
        assert result.score_range <= 0.2

    def test_results_outside_threshold_conflict(self):
        results = [
            _make_result("membrane_proxy", 0.75),
            _make_result("structure_proxy", 0.99),
        ]
        result = check_ensemble_agreement("AKLWKR", results, threshold=0.2)
        assert result.agreement_level == "conflict"
        assert result.score_range > 0.2

    def test_missing_score_key_skipped_gracefully(self):
        results = [
            _make_result("membrane_proxy", 0.75),
            SimulationResult(
                module="structure_proxy",
                version="0.1.0",
                scope=["bacterial_binding"],
                scores={"other_key": 0.80},
                uncertainty=0.1,
                calibration_set=None,
                validated_against=["APD3"],
                notes=[],
            ),
        ]
        result = check_ensemble_agreement("AKLWKR", results, score_key="binding_energy")
        assert result.agreement_level == "weak"
        assert result.mean_score == 0.75
        assert "membrane_proxy" in result.scores_by_module
        assert "structure_proxy" not in result.scores_by_module

    def test_mean_score_correct_for_two_results(self):
        results = [
            _make_result("membrane_proxy", 0.70),
            _make_result("structure_proxy", 0.90),
        ]
        result = check_ensemble_agreement("AKLWKR", results, threshold=0.2)
        assert result.mean_score == 0.80

    def test_score_range_correct(self):
        results = [
            _make_result("membrane_proxy", 0.70),
            _make_result("structure_proxy", 0.90),
        ]
        result = check_ensemble_agreement("AKLWKR", results, threshold=0.2)
        assert result.score_range == pytest.approx(0.20)

    def test_dry_lab_only_always_true(self):
        results = [
            _make_result("membrane_proxy", 0.75),
            _make_result("structure_proxy", 0.80),
        ]
        result = check_ensemble_agreement("AKLWKR", results)
        assert result.dry_lab_only is True

    def test_scores_by_module_populated(self):
        results = [
            _make_result("membrane_proxy", 0.75),
            _make_result("structure_proxy", 0.80),
        ]
        result = check_ensemble_agreement("AKLWKR", results)
        assert result.scores_by_module == {
            "membrane_proxy": 0.75,
            "structure_proxy": 0.80,
        }

    def test_threshold_parameter_respected(self):
        results = [
            _make_result("membrane_proxy", 0.70),
            _make_result("structure_proxy", 0.85),
        ]
        wide = check_ensemble_agreement("AKLWKR", results, threshold=0.2)
        narrow = check_ensemble_agreement("AKLWKR", results, threshold=0.1)
        assert wide.agreement_level == "moderate"
        assert narrow.agreement_level == "conflict"

    def test_modules_checked_includes_all_modules(self):
        results = [
            _make_result("membrane_proxy", 0.75),
            _make_result("structure_proxy", 0.80),
        ]
        result = check_ensemble_agreement("AKLWKR", results)
        assert set(result.modules_checked) == {"membrane_proxy", "structure_proxy"}

    def test_agreement_description_matches_level(self):
        results = [
            _make_result("membrane_proxy", 0.75),
            _make_result("structure_proxy", 0.80),
        ]
        result = check_ensemble_agreement("AKLWKR", results, threshold=0.2)
        assert result.agreement_description == AGREEMENT_LEVELS[result.agreement_level]

    def test_to_dict_contains_all_fields(self):
        results = [
            _make_result("membrane_proxy", 0.75),
            _make_result("structure_proxy", 0.80),
        ]
        result = check_ensemble_agreement("AKLWKR", results)
        d = result.to_dict()
        assert d["sequence"] == "AKLWKR"
        assert d["agreement_level"] == "moderate"
        assert d["dry_lab_only"] is True


class TestRunEnsembleCheckBatch:
    def test_batch_counts_correct(self):
        calls = [
            {"sequence": "SEQ1", "results": [], "score_key": "binding_energy"},
            {
                "sequence": "SEQ2",
                "results": [_make_result("membrane_proxy", 0.75)],
                "score_key": "binding_energy",
            },
            {
                "sequence": "SEQ3",
                "results": [
                    _make_result("membrane_proxy", 0.75),
                    _make_result("structure_proxy", 0.80),
                ],
                "score_key": "binding_energy",
                "threshold": 0.2,
            },
        ]
        batch = run_ensemble_check_batch(calls)
        assert batch["total"] == 3
        assert batch["insufficient"] == 1
        assert batch["weak"] == 1
        assert batch["moderate"] == 1

    def test_batch_any_conflict_true_when_conflict(self):
        calls = [
            {
                "sequence": "SEQ1",
                "results": [
                    _make_result("membrane_proxy", 0.70),
                    _make_result("structure_proxy", 0.99),
                ],
                "score_key": "binding_energy",
                "threshold": 0.2,
            },
        ]
        batch = run_ensemble_check_batch(calls)
        assert batch["conflict"] == 1
        assert batch["any_conflict"] is True

    def test_batch_dry_lab_only_true(self):
        calls = [
            {"sequence": "SEQ1", "results": []},
        ]
        batch = run_ensemble_check_batch(calls)
        assert batch["dry_lab_only"] is True

    def test_batch_results_list_length_matches_total(self):
        calls = [
            {"sequence": "SEQ1", "results": []},
            {
                "sequence": "SEQ2",
                "results": [_make_result("membrane_proxy", 0.75)],
            },
        ]
        batch = run_ensemble_check_batch(calls)
        assert len(batch["results"]) == 2

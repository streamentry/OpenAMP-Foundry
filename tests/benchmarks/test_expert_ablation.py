"""Expert-vs-ensemble ablation benchmark tests — Phase 2 honesty requirement.

AGENTS.md §7.5: "No simulation theater — every proxy module must justify itself
against cheap heuristic baselines before it affects selection."

These tests verify that:
1. The ablation benchmark runs on the real validation set.
2. Both ensemble and expert AUROCs are in [0, 1].
3. Per-component AUROCs are reported for all 9 axes.
4. The delta and verdict are internally consistent.
5. The verdict does not overclaim when the expert composite underperforms.
6. The benchmark handles edge cases (empty sets, single-class).

All results are computational. No biological activity is implied.
"""
from __future__ import annotations

import pytest

from openamp_foundry.benchmark.retrospective import run_expert_ablation_benchmark


AMP_CSV = "examples/validation/known_amps.csv"
DECOY_CSV = "examples/validation/random_background.csv"

EXPECTED_COMPONENTS = [
    "activity", "safety", "synthesis", "novelty",
    "boman_activity", "serum_stability", "selectivity_proxy",
    "hinge_selectivity", "motif_novelty", "rich_selectivity",
]


class TestExpertAblationBenchmark:
    @pytest.fixture(scope="class")
    def result(self):
        return run_expert_ablation_benchmark(
            AMP_CSV, DECOY_CSV, n_bootstrap=200,
        )

    def test_benchmark_runs_on_real_data(self, result):
        assert result["benchmark"] == "expert_ablation"
        assert result["n_positives"] == 95
        assert result["n_negatives"] == 96
        assert result["n_total"] == 191

    def test_ensemble_auroc_in_valid_range(self, result):
        assert 0.0 <= result["ensemble_auroc"] <= 1.0
        # The ensemble should have signal (above 0.70 gate)
        assert result["ensemble_auroc"] >= 0.70

    def test_expert_auroc_in_valid_range(self, result):
        assert 0.0 <= result["expert_auroc"] <= 1.0

    def test_delta_is_consistent(self, result):
        delta = result["delta_auroc"]
        assert delta == pytest.approx(
            result["expert_auroc"] - result["ensemble_auroc"], abs=1e-4
        )

    def test_per_component_auroc_reported(self, result):
        per_comp = result["per_component_auroc"]
        for name in EXPECTED_COMPONENTS:
            assert name in per_comp
            assert 0.0 <= per_comp[name]["auroc"] <= 1.0

    def test_component_classification_is_consistent(self, result):
        """Signal-bearing, near-zero, and anti-signal partition should cover all 9."""
        all_classified = set(
            result["signal_bearing_components"]
            + result["near_zero_components"]
            + result["anti_signal_components"]
        )
        assert all_classified == set(EXPECTED_COMPONENTS)

    def test_verdict_matches_delta_direction(self, result):
        """The verdict text must be consistent with the delta sign."""
        verdict = result["verdict"]
        if result["delta_auroc"] < -0.02:
            assert "LOWER" in verdict or "degrade" in verdict
        elif abs(result["delta_auroc"]) <= 0.02:
            assert "within" in verdict or "NOT" in verdict
        else:
            assert "outperforms" in verdict

    def test_ci_bounds_are_ordered(self, result):
        assert result["ensemble_ci95_lo"] <= result["ensemble_ci95_hi"]
        assert result["expert_ci95_lo"] <= result["expert_ci95_hi"]

    def test_disclaimer_present(self, result):
        assert "wet-lab" in result["disclaimer"].lower()
        assert "computational" in result["disclaimer"].lower()

    def test_design_note_present(self, result):
        assert "k-mer index" in result["design_note"] or "motif" in result["design_note"]

    def test_expert_weights_reported(self, result):
        """Expert weights should be in the output for auditability."""
        assert "activity_consensus" in result["expert_weights"]
        assert "selectivity" in result["expert_weights"]
        assert "hinge_selectivity" in result["expert_weights"]
        assert "motif_novelty" in result["expert_weights"]


class TestExpertAblationEdgeCases:
    def test_empty_amp_set_returns_half_auroc(self, tmp_path):
        amp = tmp_path / "empty.csv"
        amp.write_text("id,sequence\n")
        decoy = tmp_path / "decoy.csv"
        decoy.write_text("id,sequence\nD1,KWKLFKKIGAVLKVL\n")
        result = run_expert_ablation_benchmark(amp, decoy, n_bootstrap=10)
        # No positives → AUROC = 0.5 by convention
        assert result["ensemble_auroc"] == 0.5
        assert result["expert_auroc"] == 0.5

    def test_single_class_returns_half(self, tmp_path):
        """If all sequences are positives (no decoys), AUROC = 0.5."""
        amp = tmp_path / "amp.csv"
        amp.write_text("id,sequence\nA1,KWKLFKKIGAVLKVL\nA2,GIGKFLHSAKKFGKAFVGEIMNS\n")
        decoy = tmp_path / "empty_decoy.csv"
        decoy.write_text("id,sequence\n")
        result = run_expert_ablation_benchmark(amp, decoy, n_bootstrap=10)
        assert result["ensemble_auroc"] == 0.5
        assert result["expert_auroc"] == 0.5

    def test_perfect_separation(self, tmp_path):
        """Two clearly separable sequences should give high AUROC for both scorers."""
        amp = tmp_path / "amp.csv"
        amp.write_text("id,sequence\nA1,KWKLFKKIGAVLKVL\n")
        decoy = tmp_path / "decoy.csv"
        decoy.write_text("id,sequence\nD1,DEDEDEDEDEDEDE\n")
        result = run_expert_ablation_benchmark(amp, decoy, n_bootstrap=10)
        assert result["ensemble_auroc"] >= 0.9
        assert result["expert_auroc"] >= 0.9

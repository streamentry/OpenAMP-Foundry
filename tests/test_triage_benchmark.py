"""Tests for the multi-class triage benchmark.

Tests the v1.1 ROADMAP item: "benchmark candidate triage against a reference
panel that includes selective AMPs, hemolytic positives, inactive peptides,
and random controls."

The benchmark assembles three classes:
  1. SELECTIVE — AMPs with HC50 >= 100 µg/mL (from hemolysis_reference.csv)
  2. HEMOLYTIC — AMPs with HC50 < 25 µg/mL (from hemolysis_reference.csv)
  3. DECOY    — random background peptides (from random_background.csv)

A scorer that triages correctly should rank:
  SELECTIVE > HEMOLYTIC > DECOY

All results are computational. No biological activity is implied.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from openamp_foundry.benchmark.triage import run_triage_benchmark


HEMOLYSIS_CSV = "examples/validation/hemolysis_reference.csv"
DECOY_CSV = "examples/validation/random_background.csv"


@pytest.fixture(scope="class")
def result():
    """Run the triage benchmark once for all tests in this class."""
    hemo = Path(HEMOLYSIS_CSV)
    decoy = Path(DECOY_CSV)
    if not hemo.exists() or not decoy.exists():
        pytest.skip("Triage benchmark data not found — run from project root")
    return run_triage_benchmark(hemo, decoy, n_bootstrap=200)


class TestTriageBenchmarkStructure:
    """Verify the benchmark returns well-formed results."""

    def test_returns_required_keys(self, result):
        for key in ["benchmark", "n_selective", "n_hemolytic", "n_decoy",
                     "n_total", "per_scorer", "best_scorer",
                     "top_20_by_ensemble", "top_20_by_triage_score",
                     "top_20_by_expert_composite",
                     "known_blind_spots", "disclaimer"]:
            assert key in result, f"Missing key: {key}"

    def test_benchmark_name(self, result):
        assert result["benchmark"] == "multi_class_triage"

    def test_class_counts_positive(self, result):
        assert result["n_selective"] > 0
        assert result["n_hemolytic"] > 0
        assert result["n_decoy"] > 0
        assert result["n_total"] == result["n_selective"] + result["n_hemolytic"] + result["n_decoy"]

    def test_per_scorer_has_all_scorers(self, result):
        expected = {
            "ensemble", "activity", "safety", "synthesis",
            "selectivity_proxy", "hemolysis_risk", "serum_stability",
            "expert_composite", "triage_score", "safe_weighted_ensemble",
        }
        assert expected.issubset(set(result["per_scorer"].keys()))

    def test_each_scorer_has_pairwise_aurocs(self, result):
        for scorer, info in result["per_scorer"].items():
            for pair in ["selective_vs_decoy", "hemolytic_vs_decoy", "selective_vs_hemolytic"]:
                assert pair in info, f"{scorer} missing {pair}"
                assert 0.0 <= info[pair]["auroc"] <= 1.0
                assert info[pair]["n_pos"] > 0
                assert info[pair]["n_neg"] > 0

    def test_disclaimer_present(self, result):
        assert "computational" in result["disclaimer"].lower()
        assert "wet-lab" in result["disclaimer"].lower() or "wet lab" in result["disclaimer"].lower()

    def test_known_blind_spots_documented(self, result):
        assert len(result["known_blind_spots"]) >= 3


class TestTriageBenchmarkFindings:
    """Test the key honest findings from the benchmark."""

    def test_ensemble_fails_selective_vs_hemolytic(self, result):
        """The ensemble should NOT rank selective above hemolytic.

        This is the documented anti-selective bias: the activity scorer
        rewards hemolytic AMPs for their strong amphipathic helices.
        The ensemble inherits this bias.
        """
        sel_vs_hemo = result["per_scorer"]["ensemble"]["selective_vs_hemolytic"]["auroc"]
        assert sel_vs_hemo < 0.55, (
            f"ensemble selective_vs_hemolytic AUROC={sel_vs_hemo:.4f}: "
            "expected < 0.55 (ensemble has anti-selective bias). "
            "If this has improved, update this test."
        )

    def test_ensemble_beats_decoy(self, result):
        """The ensemble should still rank both AMP classes above decoys."""
        sel_vs_dec = result["per_scorer"]["ensemble"]["selective_vs_decoy"]["auroc"]
        hemo_vs_dec = result["per_scorer"]["ensemble"]["hemolytic_vs_decoy"]["auroc"]
        assert sel_vs_dec > 0.70, (
            f"ensemble selective_vs_decoy AUROC={sel_vs_dec:.4f}: should be > 0.70"
        )
        assert hemo_vs_dec > 0.70, (
            f"ensemble hemolytic_vs_decoy AUROC={hemo_vs_dec:.4f}: should be > 0.70"
        )

    def test_ensemble_does_not_triage_correctly(self, result):
        """The ensemble should NOT triage all three classes correctly.

        It fails because selective_vs_hemolytic < 0.5.
        This is the key honest finding that motivates the virtual assay layer.
        """
        assert result["per_scorer"]["ensemble"]["triages_correctly"] is False, (
            "Ensemble should not triage correctly (anti-selective bias). "
            "If this has changed, the pipeline has improved and this test should be updated."
        )

    def test_selectivity_proxy_triages_correctly(self, result):
        """The selectivity_proxy should be the only scorer that triages correctly.

        It ranks selective > hemolytic because it penalizes high-GRAVY peptides.
        """
        triaging = [
            s for s, info in result["per_scorer"].items()
            if info["triages_correctly"]
        ]
        assert "selectivity_proxy" in triaging, (
            "selectivity_proxy should triage correctly (selective > hemolytic > decoy)"
        )

    def test_triage_score_does_not_fix_anti_selective_bias(self, result):
        """The simple triage_score (activity * (1 - hemolysis_risk)) should NOT fix
        the anti-selective bias because hemolysis_risk is too weak.

        This is an honest negative result: a naive virtual-assay composite
        does not outperform the ensemble on the hardest triage condition.
        """
        triage_sel_vs_hemo = result["per_scorer"]["triage_score"]["selective_vs_hemolytic"]["auroc"]
        ens_sel_vs_hemo = result["per_scorer"]["ensemble"]["selective_vs_hemolytic"]["auroc"]
        # triage_score may be slightly better or worse, but should not dramatically fix the bias
        assert triage_sel_vs_hemo < 0.55, (
            f"triage_score selective_vs_hemolytic AUROC={triage_sel_vs_hemo:.4f}: "
            "expected < 0.55 (hemolysis_risk too weak to fix anti-selective bias). "
            f"ensemble was {ens_sel_vs_hemo:.4f}. "
            "If this has improved, the triage composite is working and this test should be updated."
        )

    def test_top_20_by_ensemble_contains_no_decoys(self, result):
        """The ensemble top-20 should contain only AMPs (no decoys).

        This confirms the ensemble can distinguish AMPs from decoys even if
        it cannot distinguish selective from hemolytic.
        """
        assert result["top_20_by_ensemble"]["DECOY"] == 0, (
            "Ensemble top-20 should contain no decoys"
        )

    def test_top_20_by_triage_contains_no_decoys(self, result):
        """The triage_score top-20 should also contain no decoys."""
        assert result["top_20_by_triage_score"]["DECOY"] == 0, (
            "Triage score top-20 should contain no decoys"
        )

    def test_expert_composite_is_benchmarked_before_selection_authority(self, result):
        """The selectable expert ranking mode must face the mixed-panel benchmark."""
        expert = result["per_scorer"]["expert_composite"]
        assert "selective_vs_decoy" in expert
        assert "hemolytic_vs_decoy" in expert
        assert "selective_vs_hemolytic" in expert
        assert expert["triages_correctly"] is True
        assert result["top_20_by_expert_composite"]["DECOY"] > 0, (
            "Expert composite passes pairwise triage but admits decoys into top-k; "
            "do not treat it as a replacement for the ensemble activity gate."
        )

    def test_top_20_by_triage_has_more_selective_than_ensemble(self, result):
        """The triage_score should rank MORE selective AMPs in top-20 than the ensemble.

        This is the value proposition of the triage composite: even if the
        pairwise AUROC doesn't dramatically improve, the top-k distribution
        should shift toward selective candidates.
        """
        ens_sel = result["top_20_by_ensemble"]["SELECTIVE"]
        tri_sel = result["top_20_by_triage_score"]["SELECTIVE"]
        assert tri_sel >= ens_sel, (
            f"triage_score top-20 selective={tri_sel} should be >= "
            f"ensemble top-20 selective={ens_sel}"
        )

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

from openamp_foundry.benchmark.triage import run_strict_triage_benchmark, run_triage_benchmark


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
                     "top_20_by_expert_composite", "top_20_by_gate_triage",
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
            "gate_triage",
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


# ---------------------------------------------------------------------------
# Strict triage benchmark: composition-matched decoys
# ---------------------------------------------------------------------------


@pytest.fixture(scope="class")
def strict_result():
    """Run the strict triage benchmark once for all tests in this class."""
    hemo = Path(HEMOLYSIS_CSV)
    if not hemo.exists():
        pytest.skip("Hemolysis benchmark data not found — run from project root")
    return run_strict_triage_benchmark(hemo, n_bootstrap=200)


class TestStrictTriageBenchmarkStructure:
    """Verify the strict triage benchmark returns well-formed results."""

    def test_returns_required_keys(self, strict_result):
        for key in ["benchmark", "decoy_type", "n_selective", "n_hemolytic",
                     "n_decoy", "n_total", "per_scorer", "best_scorer",
                     "top_20_by_ensemble", "top_20_by_triage_score",
                     "top_20_by_expert_composite", "top_20_by_gate_triage",
                     "known_blind_spots", "disclaimer"]:
            assert key in strict_result, f"Missing key: {key}"

    def test_benchmark_name(self, strict_result):
        assert strict_result["benchmark"] == "strict_multi_class_triage"

    def test_decoy_type(self, strict_result):
        assert strict_result["decoy_type"] == "composition_matched_scrambled"

    def test_class_counts_positive(self, strict_result):
        assert strict_result["n_selective"] > 0
        assert strict_result["n_hemolytic"] > 0
        assert strict_result["n_decoy"] > 0
        assert strict_result["n_total"] == (
            strict_result["n_selective"]
            + strict_result["n_hemolytic"]
            + strict_result["n_decoy"]
        )

    def test_decoy_count_equals_selective_count(self, strict_result):
        """Each selective AMP generates exactly one scrambled decoy."""
        assert strict_result["n_decoy"] == strict_result["n_selective"]


class TestStrictTriageBenchmarkFindings:
    """Test the key honest findings from the strict triage benchmark."""

    def test_no_scorer_triages_correctly(self, strict_result):
        """With composition-matched decoys, no scorer should triage correctly.

        This is the central honest finding: the standard triage benchmark
        appears to show that selectivity_proxy and expert_composite triage
        correctly, but this is an illusion created by trivially distinguishable
        random decoys. When decoys have the same composition as selective AMPs,
        the apparent triage signal vanishes.
        """
        triaging = [
            s for s, info in strict_result["per_scorer"].items()
            if info["triages_correctly"]
        ]
        assert len(triaging) == 0, (
            f"Scorers that triage correctly with composition-matched decoys: {triaging}. "
            "Expected none — if any scorer now triages correctly, the pipeline "
            "has genuine order-dependent triage signal and this test should be updated."
        )

    def test_selectivity_proxy_collapses_on_selective_vs_decoy(self, strict_result):
        """The selectivity_proxy should be ~0.5 on selective vs scrambled decoys.

        This confirms it is purely composition-driven: charge and GRAVY are
        identical between a sequence and its scrambled version.
        """
        sel_vs_dec = strict_result["per_scorer"]["selectivity_proxy"]["selective_vs_decoy"]["auroc"]
        assert abs(sel_vs_dec - 0.5) < 0.02, (
            f"selectivity_proxy selective_vs_decoy={sel_vs_dec:.4f}: "
            "expected ~0.5 (composition-matched decoy has identical charge/GRAVY). "
            "If this has changed, selectivity_proxy may have order-dependent signal."
        )

    def test_ensemble_drops_on_selective_vs_decoy(self, strict_result):
        """The ensemble should drop dramatically vs standard triage on selective_vs_decoy.

        Standard triage: ensemble sel_vs_decoy ~0.85 (trivially distinguishes AMPs
        from random protein sequences).
        Strict triage: ensemble sel_vs_decoy should be near 0.5 because most
        ensemble signal is composition-based.
        """
        ens_sel_vs_dec = strict_result["per_scorer"]["ensemble"]["selective_vs_decoy"]["auroc"]
        assert ens_sel_vs_dec < 0.65, (
            f"ensemble selective_vs_decoy={ens_sel_vs_dec:.4f}: "
            "expected < 0.65 (composition-matched decoys remove most signal). "
            "If this has improved, the ensemble has order-dependent signal."
        )

    def test_selective_vs_hemolytic_unchanged(self, strict_result, result):
        """The selective_vs_hemolytic AUROC should be identical between standard and strict.

        Both selective and hemolytic are real AMP sequences in both benchmarks.
        Only the decoy class changes, so this pairwise comparison should be stable.
        """
        std_sv = result["per_scorer"]["ensemble"]["selective_vs_hemolytic"]["auroc"]
        strict_sv = strict_result["per_scorer"]["ensemble"]["selective_vs_hemolytic"]["auroc"]
        assert abs(std_sv - strict_sv) < 0.001, (
            f"standard sel_vs_hemo={std_sv:.4f} vs strict={strict_sv:.4f}: "
            "expected identical (same AMP sequences, only decoy class changes)."
        )

    def test_ensemble_admits_decoys_into_top_20(self, strict_result):
        """The ensemble should admit scrambled decoys into top-20.

        In standard triage, ensemble admits 0 decoys into top-20 because
        random background peptides are compositionally unlike AMPs. With
        composition-matched decoys, the ensemble cannot distinguish real AMPs
        from scrambled versions, so decoys leak into top-k.
        """
        n_decoys = strict_result["top_20_by_ensemble"]["DECOY"]
        assert n_decoys > 0, (
            "Ensemble should admit composition-matched decoys into top-20. "
            "If 0, the ensemble has strong order-dependent signal."
        )

    def test_disclaimer_present(self, strict_result):
        assert "composition-matched" in strict_result["disclaimer"].lower()
        assert "wet-lab" in strict_result["disclaimer"].lower()

    def test_known_blind_spots_documented(self, strict_result):
        assert len(strict_result["known_blind_spots"]) >= 3

class TestGateTriageFindings:
    """Test the two-gate triage composite: activity * rich_selectivity.

    This scorer combines two complementary signals:
    - activity: strong at AMP-vs-decoy (AUROC ~0.88-0.93) but anti-selective
    - rich_selectivity: strong at selective-vs-hemolytic (AUROC ~0.74, significant)
      but anti-AMP (penalizes AMP-like features vs decoys)

    Their product should pass all three triage conditions in the standard
    benchmark, which no previous scorer has achieved.
    """

    def test_gate_triage_is_present(self, result):
        assert "gate_triage" in result["per_scorer"]

    def test_gate_triage_triages_correctly(self, result):
        """The gate_triage scorer should pass all three pairwise AUROC > 0.5.

        This is the first scorer to achieve all-three-pass triage in the
        standard benchmark. It leverages activity (AMP detection) and
        rich_selectivity (hemolysis separation) as multiplicative gates.
        """
        info = result["per_scorer"]["gate_triage"]
        assert info["triages_correctly"] is True, (
            f"gate_triage should triage correctly. "
            f"sel_vs_dec={info['selective_vs_decoy']['auroc']:.4f}, "
            f"hem_vs_dec={info['hemolytic_vs_decoy']['auroc']:.4f}, "
            f"sel_vs_hem={info['selective_vs_hemolytic']['auroc']:.4f}"
        )

    def test_gate_triage_selective_vs_hemolytic_above_threshold(self, result):
        """gate_triage should achieve selective_vs_hemolytic > 0.60.

        The old triage_score (activity * (1 - hemolysis_risk)) fails this
        condition because hemolysis_risk is not significant. gate_triage
        uses rich_selectivity (AUROC=0.74, significant) instead.
        """
        svh = result["per_scorer"]["gate_triage"]["selective_vs_hemolytic"]["auroc"]
        assert svh > 0.60, (
            f"gate_triage selective_vs_hemolytic={svh:.4f}: expected > 0.60"
        )

    def test_gate_triage_beats_triage_score_on_selective_vs_hemolytic(self, result):
        """gate_triage should beat the old triage_score on selective_vs_hemolytic.

        This validates that rich_selectivity (significant) is a better
        hemolysis separator than hemolysis_risk (not significant).
        """
        gate_svh = result["per_scorer"]["gate_triage"]["selective_vs_hemolytic"]["auroc"]
        old_svh = result["per_scorer"]["triage_score"]["selective_vs_hemolytic"]["auroc"]
        assert gate_svh > old_svh, (
            f"gate_triage svh={gate_svh:.4f} should beat triage_score svh={old_svh:.4f}"
        )

    def test_gate_triage_top_20_majority_selective(self, result):
        """gate_triage top-20 should have majority selective AMPs."""
        dist = result["top_20_by_gate_triage"]
        assert dist["SELECTIVE"] > 10, (
            f"gate_triage top-20 selective={dist['SELECTIVE']}: expected > 10"
        )

    def test_gate_triage_fewer_hemolytic_than_ensemble(self, result):
        """gate_triage should rank fewer hemolytic AMPs in top-20 than ensemble.

        The ensemble has an anti-selective bias (ranks hemolytic AMPs highly).
        gate_triage should correct this by penalizing hemolytic candidates
        through the rich_selectivity gate.
        """
        gate_hem = result["top_20_by_gate_triage"]["HEMOLYTIC"]
        ens_hem = result["top_20_by_ensemble"]["HEMOLYTIC"]
        assert gate_hem <= ens_hem, (
            f"gate_triage hemolytic in top-20={gate_hem} should be <= "
            f"ensemble hemolytic in top-20={ens_hem}"
        )

    def test_gate_triage_is_best_scorer(self, result):
        """gate_triage should be the best scorer by the composite metric."""
        assert result["best_scorer"] == "gate_triage", (
            f"Expected gate_triage as best scorer, got {result['best_scorer']}"
        )

    def test_gate_triage_does_not_pass_strict(self, strict_result):
        """gate_triage should NOT pass strict triage (composition-matched decoys).

        In strict triage, hemolytic_vs_decoy drops below 0.5 because
        rich_selectivity penalizes the AMP-like composition that hemolytic
        AMPs share with their scrambled decoys. This is an honest limitation:
        the gate_triage has no order-dependent signal for the hemolytic-vs-decoy
        pair when composition is controlled.
        """
        info = strict_result["per_scorer"]["gate_triage"]
        assert info["triages_correctly"] is False, (
            "gate_triage should not pass strict triage. "
            "If it does, it has order-dependent signal beyond composition."
        )

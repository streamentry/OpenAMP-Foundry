"""Tests for aggregation propensity scoring and its synthesis score integration."""
from __future__ import annotations

import pytest

from openamp_foundry.features.physchem import aggregation_propensity, compute_features
from openamp_foundry.scoring.synthesis import synthesis_feasibility_score


class TestAggregationPropensityUnit:
    def test_empty_sequence_returns_zero(self):
        assert aggregation_propensity("") == 0.0

    def test_polar_sequence_no_aggregation(self):
        # All charged/polar residues — no hydrophobic run
        assert aggregation_propensity("KKKKKK") == 0.0
        assert aggregation_propensity("EEEEEE") == 0.0
        assert aggregation_propensity("RRRRRRR") == 0.0

    def test_single_hydrophobic_no_run(self):
        # Only one hydrophobic in a polar context — no run ≥ 4
        assert aggregation_propensity("KKVKK") == 0.0

    def test_short_run_below_threshold(self):
        # KKVLLK: run of 3 interior hydrophobics (V,L,L) — below ≥4 threshold → run_risk=0
        # beta_density: only V = 1/6 ≈ 0.167 < 0.20 → beta_risk=0
        assert aggregation_propensity("KKVLLK") == 0.0

    def test_run_of_4_triggers_run_risk(self):
        # "KKVILL": full-sequence run of 4 (VILL at pos 2-5) → run_risk = (4-3)/5 = 0.20
        # Combined with beta component → total > 0.14 (run_risk alone = 0.7 * 0.20 = 0.14)
        score = aggregation_propensity("KKVILL")
        assert score > 0.14

    def test_run_of_4_boundary_exact_run_component(self):
        # "KVLLLK": full-sequence run exactly 4 (VLLL) → run_risk = (4-3)/5 = 0.20
        # beta_density: V(1)/6 = 0.167 < 0.20 → beta_risk = 0
        # Total = 0.7 * 0.20 = 0.14
        score = aggregation_propensity("KVLLLK")
        assert score == pytest.approx(0.14, abs=0.01)

    def test_run_of_8_saturates_at_max_run_risk(self):
        # "KVLLLLLLLK": run of 8 (VLLLLLLL) → run_risk = (8-3)/5 = 1.0 (saturated)
        # beta_density: V(1)/10 = 0.10 < 0.20 → beta_risk = 0
        # Total = 0.7 * 1.0 = 0.70
        score = aggregation_propensity("KVLLLLLLLK")
        assert score == pytest.approx(0.70, abs=0.01)

    def test_long_hydrophobic_run_high_risk(self):
        # Run of 8 interior hydrophobics → max run_risk (capped at 1.0)
        score = aggregation_propensity("KVIIIIIIIK")
        assert score >= 0.6

    def test_beta_branched_density_alone(self):
        # High Val/Ile/Thr density without a long run
        # VIVTVITV: V,I,T at 8/8 positions but no consecutive run of 4 agg residues (T not in AGG_HYDROPHOBIC)
        # Actually VIT: V and I are in AGG_HYDROPHOBIC, T is not → runs are broken by T
        score = aggregation_propensity("VIVTVITV")
        # beta_density = 8/8 = 1.0 → beta_risk = max of (1.0-0.20)/0.30 capped at 1 = 1.0
        # run_risk = 0 (runs of V,I broken by T: max run = 2)
        # aggregation = 0.7*0 + 0.3*1.0 = 0.3
        assert score == pytest.approx(0.3, abs=0.05)

    def test_pure_ile_long_run_max_risk(self):
        # IIIIIIIIIII: all interior = run of 9
        # run_risk = min(1.0, (9-3)/5) = 1.0; beta_density = 1.0 → beta_risk = 1.0
        score = aggregation_propensity("IIIIIIIIIII")
        assert score == pytest.approx(1.0, abs=0.01)

    def test_returns_unit_interval(self):
        for seq in ["AAAAAAA", "KWKLFKKIGAVLKVL", "GIGKFLHSAKKFGKAFVGEIMNS",
                    "FLPLIGRVLSGIL", "IIIIIIII", "KKKKKKK"]:
            score = aggregation_propensity(seq)
            assert 0.0 <= score <= 1.0, f"score={score} out of [0,1] for {seq}"

    def test_compute_features_includes_key(self):
        feats = compute_features("KWKLFKKIGAVLKVL")
        assert "aggregation_propensity" in feats

    def test_temporin_like_seed004_no_run_only_beta(self):
        # FLPLIGRVLSGIL: longest interior hydrophobic run = 2 (FL or VL) — below ≥4 threshold
        # beta_density: I(4),V(7),I(11) = 3/13 = 0.231 → small beta_risk component
        score = aggregation_propensity("FLPLIGRVLSGIL")
        # run_risk = 0; small beta_risk → total < 0.1
        assert score < 0.1
        # And it's genuinely > 0 because of the beta-branched component
        assert score > 0.0


class TestSynthesisFeasibilityWithAggregation:
    def test_high_aggregation_penalises_synthesis(self):
        feats_high = compute_features("IIIIIIIIIIII")   # long Ile run → agg=1.0
        feats_low = compute_features("KWKLFKKIGAVLKVL")  # typical AMP, low agg
        assert synthesis_feasibility_score(feats_high) < synthesis_feasibility_score(feats_low)

    def test_zero_aggregation_no_penalty(self):
        # Synthesis score should only be affected by length/cys/repeat, not aggregation
        feats_no_agg = {
            "length": 8, "longest_repeat_run": 8, "cysteine_fraction": 0.0,
            "aggregation_propensity": 0.0,
        }
        score = synthesis_feasibility_score(feats_no_agg)
        assert score == pytest.approx(0.90, abs=0.01)  # only repeat_run≥5 penalty applies

    def test_aggregation_penalty_capped_at_0_20(self):
        # Max agg (1.0) → penalty = min(1.0 * 0.25, 0.20) = 0.20
        feats_max_agg = {
            "length": 10, "longest_repeat_run": 1, "cysteine_fraction": 0.0,
            "aggregation_propensity": 1.0,
        }
        score = synthesis_feasibility_score(feats_max_agg)
        assert score == pytest.approx(0.80, abs=0.01)

    def test_mild_aggregation_modest_penalty(self):
        feats_mild = {
            "length": 10, "longest_repeat_run": 1, "cysteine_fraction": 0.0,
            "aggregation_propensity": 0.4,
        }
        score = synthesis_feasibility_score(feats_mild)
        # penalty = 0.4 * 0.25 = 0.10
        assert score == pytest.approx(0.90, abs=0.01)

    def test_synthesis_score_unit_interval(self):
        for seq in ["IIIIIIIIIII", "KWKLFKKIGAVLKVL", "GIGKFLHSAKKFGKAFVGEIMNS", "KKKK"]:
            feats = compute_features(seq)
            s = synthesis_feasibility_score(feats)
            assert 0.0 <= s <= 1.0, f"score={s} out of [0,1] for {seq}"

    def test_backward_compat_without_aggregation_key(self):
        # Caller passes features dict without aggregation_propensity key (pre-this-PR dict)
        feats_old = {"length": 15, "longest_repeat_run": 1, "cysteine_fraction": 0.0}
        score = synthesis_feasibility_score(feats_old)
        assert score == 1.0

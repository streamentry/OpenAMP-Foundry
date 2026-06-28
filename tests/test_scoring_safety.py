"""Tests for scoring/safety.py — safety_score risk conditions.

safety_score = 1.0 - clamp01(risk), where risk accumulates from:
  - μH > 0.55: (μH - 0.55) * 1.5
  - hydrophobic_fraction > 0.65: (hf - 0.65) * 1.8
  - |charge_density| > 0.55: (cd - 0.55) * 1.2
  - length > 35: +0.25 flat
  - cysteine_fraction > 0.25: +0.20 flat
  - longest_repeat_run >= 6: +0.15 flat

All boundary conditions are tested with explicit arithmetic.
"""
from __future__ import annotations

from openamp_foundry.scoring.safety import safety_score


def _feat(
    length: int = 15,
    charge_density: float = 0.30,
    hydrophobic: float = 0.40,
    cys: float = 0.0,
    repeat_run: int = 1,
    mu_h: float = 0.0,
) -> dict:
    return {
        "length": length,
        "charge_density": charge_density,
        "hydrophobic_fraction": hydrophobic,
        "cysteine_fraction": cys,
        "longest_repeat_run": repeat_run,
        "hydrophobic_moment": mu_h,
    }


class TestSafetyScoreBaseline:
    def test_ideal_amp_scores_one(self):
        # No risk factor triggered: no penalties → score = 1.0
        assert safety_score(_feat()) == 1.0

    def test_returns_float(self):
        assert isinstance(safety_score(_feat()), float)

    def test_output_in_unit_interval(self):
        # Sweep several parameter combinations; score must stay in [0, 1]
        for mu_h in [0.0, 0.4, 0.6, 0.9]:
            for hf in [0.0, 0.4, 0.7, 1.0]:
                score = safety_score(_feat(mu_h=mu_h, hydrophobic=hf, length=40))
                assert 0.0 <= score <= 1.0, f"score={score} out of range"

    def test_result_rounded_to_4dp(self):
        s = safety_score(_feat(mu_h=0.6))
        assert s == round(s, 4)

    def test_no_hydrophobic_moment_feature_defaults_to_zero(self):
        feat = {
            "length": 15, "charge_density": 0.30,
            "hydrophobic_fraction": 0.40, "cysteine_fraction": 0.0,
            "longest_repeat_run": 1,
            # Note: hydrophobic_moment deliberately omitted
        }
        # Should default to mu_h=0.0, no crash
        score = safety_score(feat)
        assert score == 1.0


class TestHydrophobicMomentPenalty:
    def test_mu_h_at_threshold_no_penalty(self):
        # μH exactly 0.55 → no penalty (condition is > 0.55)
        assert safety_score(_feat(mu_h=0.55)) == 1.0

    def test_mu_h_just_above_threshold_penalised(self):
        # μH = 0.56 → risk = (0.56 - 0.55) * 1.5 = 0.015 → score = 0.985
        score = safety_score(_feat(mu_h=0.56))
        assert abs(score - 0.985) < 0.001

    def test_mu_h_0_7_penalty_correct(self):
        # μH = 0.70 → risk = (0.70 - 0.55) * 1.5 = 0.225 → score = 0.775
        score = safety_score(_feat(mu_h=0.70))
        assert abs(score - 0.775) < 0.001

    def test_mu_h_0_9_penalty_correct(self):
        # μH = 0.90 → risk = (0.90 - 0.55) * 1.5 = 0.525 → score = 0.475
        score = safety_score(_feat(mu_h=0.90))
        assert abs(score - 0.475) < 0.001

    def test_high_mu_h_below_low_mu_h(self):
        assert safety_score(_feat(mu_h=0.80)) < safety_score(_feat(mu_h=0.40))

    def test_mu_h_penalty_capped_at_zero_score(self):
        # μH = 1.22 → risk ≥ 1.0 → clamped to 1.0 → score = 0.0
        score = safety_score(_feat(mu_h=1.22))
        assert score == 0.0


class TestHydrophobicFractionPenalty:
    def test_hydrophobic_at_threshold_no_penalty(self):
        # hf exactly 0.65 → no penalty (condition is > 0.65)
        assert safety_score(_feat(hydrophobic=0.65)) == 1.0

    def test_hydrophobic_0_70_penalty_correct(self):
        # hf = 0.70 → risk = (0.70 - 0.65) * 1.8 = 0.09 → score = 0.91
        score = safety_score(_feat(hydrophobic=0.70))
        assert abs(score - 0.91) < 0.001

    def test_hydrophobic_0_80_penalty_correct(self):
        # hf = 0.80 → risk = (0.80 - 0.65) * 1.8 = 0.27 → score = 0.73
        score = safety_score(_feat(hydrophobic=0.80))
        assert abs(score - 0.73) < 0.001

    def test_very_high_hydrophobic_penalised_more(self):
        assert safety_score(_feat(hydrophobic=0.90)) < safety_score(_feat(hydrophobic=0.70))


class TestChargeDensityPenalty:
    def test_charge_density_at_threshold_no_penalty(self):
        # |cd| exactly 0.55 → no penalty (condition is > 0.55)
        assert safety_score(_feat(charge_density=0.55)) == 1.0

    def test_negative_charge_density_uses_abs(self):
        # charge_density = -0.60 → |cd| = 0.60 > 0.55 → penalty
        score_neg = safety_score(_feat(charge_density=-0.60))
        score_pos = safety_score(_feat(charge_density=0.60))
        assert score_neg == score_pos

    def test_charge_density_0_70_penalty_correct(self):
        # cd = 0.70 → risk = (0.70 - 0.55) * 1.2 = 0.18 → score = 0.82
        score = safety_score(_feat(charge_density=0.70))
        assert abs(score - 0.82) < 0.001

    def test_charge_density_below_threshold_no_penalty(self):
        assert safety_score(_feat(charge_density=0.30)) == 1.0


class TestLengthPenalty:
    def test_length_35_no_penalty(self):
        # exactly 35 → no penalty (condition is > 35)
        assert safety_score(_feat(length=35)) == 1.0

    def test_length_36_flat_penalty(self):
        # length > 35 → risk += 0.25 → score = 0.75
        score = safety_score(_feat(length=36))
        assert abs(score - 0.75) < 0.001

    def test_length_100_same_flat_penalty(self):
        # flat penalty regardless of how long (not graduated)
        assert abs(safety_score(_feat(length=100)) - safety_score(_feat(length=36))) < 0.001

    def test_short_sequence_no_length_penalty(self):
        # length=8 is short but below the length > 35 threshold
        assert safety_score(_feat(length=8)) == 1.0


class TestCysteinePenalty:
    def test_cysteine_at_threshold_no_penalty(self):
        # cys exactly 0.25 → no penalty (condition is > 0.25)
        assert safety_score(_feat(cys=0.25)) == 1.0

    def test_cysteine_0_26_penalty_applied(self):
        # cys = 0.26 → risk += 0.20 → score = 0.80
        score = safety_score(_feat(cys=0.26))
        assert abs(score - 0.80) < 0.001

    def test_cysteine_1_0_same_flat_penalty(self):
        # flat penalty regardless of fraction amount
        assert abs(safety_score(_feat(cys=1.0)) - safety_score(_feat(cys=0.26))) < 0.001


class TestRepeatRunPenalty:
    def test_repeat_run_5_no_penalty(self):
        # run = 5 → no penalty (condition is >= 6)
        assert safety_score(_feat(repeat_run=5)) == 1.0

    def test_repeat_run_6_penalty_applied(self):
        # run >= 6 → risk += 0.15 → score = 0.85
        score = safety_score(_feat(repeat_run=6))
        assert abs(score - 0.85) < 0.001

    def test_repeat_run_20_same_flat_penalty(self):
        # flat penalty regardless of run length
        assert abs(safety_score(_feat(repeat_run=20)) - safety_score(_feat(repeat_run=6))) < 0.001


class TestCumulativePenalties:
    def test_multiple_penalties_accumulate(self):
        # μH=0.70 (+0.225) + hf=0.80 (+0.27) = 0.495 → score = 0.505
        score = safety_score(_feat(mu_h=0.70, hydrophobic=0.80))
        assert abs(score - 0.505) < 0.001

    def test_all_penalties_clamp_to_zero(self):
        # All risk factors active at extremes → risk ≥ 1.0 → score = 0.0
        score = safety_score(_feat(
            mu_h=0.90, hydrophobic=0.90, charge_density=0.80,
            length=50, cys=0.50, repeat_run=8
        ))
        assert score == 0.0

    def test_two_penalties_add_correctly(self):
        # length > 35 (+0.25) + cysteine > 0.25 (+0.20) = 0.45 → score = 0.55
        score = safety_score(_feat(length=40, cys=0.30))
        assert abs(score - 0.55) < 0.001

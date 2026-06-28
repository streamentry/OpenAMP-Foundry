"""Tests for scoring/synthesis.py — synthesis_feasibility_score."""
from __future__ import annotations

from openamp_foundry.scoring.synthesis import synthesis_feasibility_score


def _feat(length: int = 15, repeat_run: int = 1, cys: float = 0.0) -> dict:
    return {"length": length, "longest_repeat_run": repeat_run, "cysteine_fraction": cys}


class TestSynthesisFeasibilityScore:
    def test_ideal_peptide_scores_one(self):
        # 15-mer, no repeats, no cysteine → no penalty
        assert synthesis_feasibility_score(_feat(15, 1, 0.0)) == 1.0

    def test_invalid_sequence_returns_zero(self):
        assert synthesis_feasibility_score(_feat(15), valid_sequence=False) == 0.0

    def test_long_peptide_penalised(self):
        # > 30 AA → length penalty
        score_normal = synthesis_feasibility_score(_feat(20))
        score_long = synthesis_feasibility_score(_feat(40))
        assert score_long < score_normal

    def test_length_31_small_penalty(self):
        # 31 residues: penalty = 1 * 0.04 = 0.04 → score = 0.96
        score = synthesis_feasibility_score(_feat(31))
        assert abs(score - 0.96) < 0.001

    def test_very_long_penalty_capped_at_0_40(self):
        # 40 residues → (40-30)*0.04 = 0.40 → score = 0.60
        score = synthesis_feasibility_score(_feat(40))
        assert abs(score - 0.60) < 0.001

    def test_extremely_long_penalty_still_capped(self):
        # 100 residues → penalty capped at 0.40 → score = 0.60 (not negative)
        score = synthesis_feasibility_score(_feat(100))
        assert score == 0.60

    def test_short_peptide_penalised(self):
        # < 8 AA → -0.30
        score = synthesis_feasibility_score(_feat(5))
        assert abs(score - 0.70) < 0.001

    def test_length_8_no_short_penalty(self):
        # exactly 8 residues: no short penalty, no long penalty
        assert synthesis_feasibility_score(_feat(8)) == 1.0

    def test_repeat_run_5_penalised(self):
        # repeat_run >= 5 → -0.10
        score_clean = synthesis_feasibility_score(_feat(15, repeat_run=4))
        score_repeat = synthesis_feasibility_score(_feat(15, repeat_run=5))
        assert score_repeat < score_clean

    def test_repeat_run_5_penalty_value(self):
        score = synthesis_feasibility_score(_feat(15, repeat_run=5))
        assert abs(score - 0.90) < 0.001

    def test_high_cysteine_penalised(self):
        # cys > 0.20 → -0.15
        score_nocys = synthesis_feasibility_score(_feat(15, cys=0.0))
        score_cys = synthesis_feasibility_score(_feat(15, cys=0.30))
        assert score_cys < score_nocys

    def test_cysteine_0_20_no_penalty(self):
        # exactly 0.20 → no penalty (condition is cys > 0.20)
        assert synthesis_feasibility_score(_feat(15, cys=0.20)) == 1.0

    def test_cysteine_0_21_penalty_applied(self):
        score = synthesis_feasibility_score(_feat(15, cys=0.21))
        assert abs(score - 0.85) < 0.001

    def test_cumulative_penalties_clamped_to_zero(self):
        # short + high_cys + repeat: 0.30 + 0.15 + 0.10 = 0.55 total → 0.45, not negative
        score = synthesis_feasibility_score(_feat(5, repeat_run=5, cys=0.30))
        assert score >= 0.0
        assert score == 0.45

    def test_returns_float(self):
        assert isinstance(synthesis_feasibility_score(_feat(15)), float)

    def test_output_in_unit_interval(self):
        for length in [5, 8, 15, 30, 40, 80]:
            score = synthesis_feasibility_score(_feat(length, repeat_run=6, cys=0.25))
            assert 0.0 <= score <= 1.0, f"score={score} out of range for length={length}"

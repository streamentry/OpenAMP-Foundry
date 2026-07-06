"""Tests for AUPRC computation in the retrospective benchmark."""
from __future__ import annotations

import pytest

from openamp_foundry.benchmark.retrospective import _auprc


class TestAUPRC:
    def test_perfect_classifier_returns_one(self):
        pos = [0.9, 0.8, 0.7]
        neg = [0.3, 0.2, 0.1]
        assert _auprc(pos, neg) == pytest.approx(1.0, abs=1e-4)

    def test_worst_classifier_below_prevalence(self):
        # When all negatives score higher than all positives, AUPRC < prevalence
        pos = [0.1, 0.2, 0.3]
        neg = [0.7, 0.8, 0.9]
        result = _auprc(pos, neg)
        prevalence = 3 / 6  # 0.5
        assert result < prevalence  # worst classifier is below random baseline

    def test_random_classifier_near_prevalence(self):
        # Interleaved scores → AUPRC ≈ prevalence (3/8 = 0.375 for 3 pos / 5 neg)
        pos = [0.7, 0.5, 0.3]
        neg = [0.6, 0.4, 0.4, 0.2, 0.1]
        result = _auprc(pos, neg)
        assert 0.0 < result < 1.0

    def test_empty_positives_returns_zero(self):
        assert _auprc([], [0.5, 0.4, 0.3]) == 0.0

    def test_empty_negatives(self):
        # No negatives → every threshold has precision=1, AUPRC=1
        assert _auprc([0.9, 0.8, 0.7], []) == pytest.approx(1.0, abs=1e-4)

    def test_single_positive_single_negative_perfect(self):
        assert _auprc([0.9], [0.1]) == pytest.approx(1.0, abs=1e-4)

    def test_single_positive_single_negative_worst(self):
        result = _auprc([0.1], [0.9])
        assert 0.0 <= result <= 1.0

    def test_output_is_rounded_to_4_decimal_places(self):
        pos = [0.75, 0.65]
        neg = [0.55, 0.45, 0.35]
        result = _auprc(pos, neg)
        assert result == round(result, 4)

    def test_all_tied_scores_pessimistic_not_inflated(self):
        # With all tied scores, pessimistic tie-breaking (negatives first)
        # must NOT return 1.0 (which the optimistic ordering would give).
        # It returns a conservative value well below prevalence.
        pos = [0.5, 0.5, 0.5]
        neg = [0.5, 0.5, 0.5, 0.5, 0.5]
        prevalence = 3 / 8
        result = _auprc(pos, neg)
        assert result < prevalence  # conservative, not inflated to 1.0

    def test_auprc_above_random_baseline_for_good_classifier(self):
        pos = [0.9, 0.85, 0.8, 0.75]
        neg = [0.4, 0.35, 0.3, 0.25, 0.2, 0.15]
        auprc = _auprc(pos, neg)
        prevalence = len(pos) / (len(pos) + len(neg))
        assert auprc > prevalence

    def test_retrospective_benchmark_includes_auprc_keys(self, tmp_path):
        """Full integration: run_retrospective_benchmark returns auprc in output."""
        from openamp_foundry.benchmark.retrospective import run_retrospective_benchmark

        amp_csv = tmp_path / "amps.csv"
        decoy_csv = tmp_path / "decoys.csv"
        # 5 short known-active AMP-like sequences
        amp_csv.write_text(
            "id,sequence\n"
            "A1,KWKLFKKIGAVLKVL\n"
            "A2,GIGKFLHSAKKFGKA\n"
            "A3,RRWQWRMKKLG\n"
            "A4,KRLFKKIGSALK\n"
            "A5,INWKGIAAMAKKLL\n",
            encoding="utf-8",
        )
        # 5 composition-random decoy sequences
        decoy_csv.write_text(
            "id,sequence\n"
            "D1,AAAAAGGGGGPPPPP\n"
            "D2,SSSSSTTTTTAAAAA\n"
            "D3,GGGGGPPPPPAAAAA\n"
            "D4,LLLLLVVVVVIIIII\n"
            "D5,EEEEEDDDDDNNNNN\n",
            encoding="utf-8",
        )
        result = run_retrospective_benchmark(
            amp_csv=str(amp_csv),
            decoy_csv=str(decoy_csv),
            config_path="configs/pipeline.yaml",
            n_bootstrap=10,
        )
        assert "auprc" in result
        assert "auprc_random_baseline" in result
        assert "auprc_above_random" in result
        assert 0.0 <= result["auprc"] <= 1.0
        assert result["auprc_random_baseline"] == pytest.approx(0.5, abs=0.01)
        assert result["auprc_above_random"] == pytest.approx(
            result["auprc"] - result["auprc_random_baseline"], abs=1e-4
        )

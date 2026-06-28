"""Tests for retrospective AUROC benchmark module."""
from __future__ import annotations

import csv

import pytest

from openamp_foundry.benchmark.retrospective import (
    _auc_wilcoxon,
    _recall_at_k,
    run_retrospective_benchmark,
)


class TestAucWilcoxon:
    def test_perfect_separation(self):
        pos = [0.9, 0.8, 0.7]
        neg = [0.4, 0.3, 0.2]
        assert _auc_wilcoxon(pos, neg) == pytest.approx(1.0)

    def test_worst_case(self):
        pos = [0.2, 0.3, 0.4]
        neg = [0.7, 0.8, 0.9]
        assert _auc_wilcoxon(pos, neg) == pytest.approx(0.0)

    def test_random_is_half(self):
        pos = [0.5, 0.5, 0.5]
        neg = [0.5, 0.5, 0.5]
        assert _auc_wilcoxon(pos, neg) == pytest.approx(0.5)

    def test_empty_pos_returns_half(self):
        assert _auc_wilcoxon([], [0.5, 0.6]) == pytest.approx(0.5)

    def test_ties_counted_as_half(self):
        pos = [0.6]
        neg = [0.6]
        assert _auc_wilcoxon(pos, neg) == pytest.approx(0.5)


class TestRecallAtK:
    def test_all_positives_at_top(self):
        labels = [1, 1, 1, 0, 0]
        assert _recall_at_k(labels, k=3) == pytest.approx(1.0)

    def test_no_positives_at_top(self):
        labels = [0, 0, 0, 1, 1]
        assert _recall_at_k(labels, k=3) == pytest.approx(0.0)

    def test_half_recall(self):
        labels = [1, 0, 1, 0, 0, 0]
        # 1 of 2 positives in top-2
        assert _recall_at_k(labels, k=2) == pytest.approx(0.5)

    def test_no_positives_returns_zero(self):
        assert _recall_at_k([0, 0, 0], k=2) == pytest.approx(0.0)


class TestRunRetrospectiveBenchmark:
    @pytest.fixture
    def mini_amp_csv(self, tmp_path):
        p = tmp_path / "amps.csv"
        rows = [
            {"id": "AMP-001", "sequence": "KWKLFKKIGAVLKVL", "family": "template", "reference": "test", "label": 1},
            {"id": "AMP-002", "sequence": "RRWQWRMKKLG", "family": "rrw", "reference": "test", "label": 1},
            {"id": "AMP-003", "sequence": "GIGKFLHSAKKFGKAFVGEIMNS", "family": "magainin", "reference": "test", "label": 1},
        ]
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "sequence", "family", "reference", "label"])
            w.writeheader()
            w.writerows(rows)
        return p

    @pytest.fixture
    def mini_decoy_csv(self, tmp_path):
        p = tmp_path / "decoys.csv"
        # These are composition-shuffled (all-G/all-A decoys that score low)
        rows = [
            {"id": "DECOY-001", "sequence": "GGGGGGGGGGGGGGG", "family": "shuffled", "source_id": "AMP-001", "label": 0},
            {"id": "DECOY-002", "sequence": "AAAAAAAAAAA", "family": "shuffled", "source_id": "AMP-002", "label": 0},
            {"id": "DECOY-003", "sequence": "GGGGGGGGGGGGGGGGGGGGGGG", "family": "shuffled", "source_id": "AMP-003", "label": 0},
        ]
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "sequence", "family", "source_id", "label"])
            w.writeheader()
            w.writerows(rows)
        return p

    def test_returns_required_keys(self, mini_amp_csv, mini_decoy_csv):
        result = run_retrospective_benchmark(mini_amp_csv, mini_decoy_csv)
        for key in ["auroc", "n_positives", "n_negatives", "interpretation", "top_ranked", "disclaimer"]:
            assert key in result, f"Missing key: {key}"

    def test_auroc_between_0_and_1(self, mini_amp_csv, mini_decoy_csv):
        result = run_retrospective_benchmark(mini_amp_csv, mini_decoy_csv)
        assert 0.0 <= result["auroc"] <= 1.0

    def test_amps_outrank_all_g_decoys(self, mini_amp_csv, mini_decoy_csv):
        # Known AMPs should clearly outrank all-G / all-A decoys
        result = run_retrospective_benchmark(mini_amp_csv, mini_decoy_csv)
        assert result["auroc"] > 0.7, (
            f"Known AMPs should strongly outrank degenerate decoys (AUROC={result['auroc']:.4f})"
        )

    def test_n_counts_correct(self, mini_amp_csv, mini_decoy_csv):
        result = run_retrospective_benchmark(mini_amp_csv, mini_decoy_csv)
        assert result["n_positives"] == 3
        assert result["n_negatives"] == 3
        assert result["n_total"] == 6

    def test_recall_keys_present(self, mini_amp_csv, mini_decoy_csv):
        result = run_retrospective_benchmark(mini_amp_csv, mini_decoy_csv)
        assert "recall_at_10" in result or "recall_at_3" in result or any(
            k.startswith("recall_at") for k in result
        )

    def test_interpretation_is_string(self, mini_amp_csv, mini_decoy_csv):
        result = run_retrospective_benchmark(mini_amp_csv, mini_decoy_csv)
        assert isinstance(result["interpretation"], str)
        assert len(result["interpretation"]) > 10

    def test_standard_benchmark_passes_gate(self):
        """Primary Gate 1: AMPs vs background-frequency random peptides, AUROC > 0.70."""
        from pathlib import Path
        amp_csv = Path("examples/validation/known_amps.csv")
        bg_csv = Path("examples/validation/random_background.csv")
        if not amp_csv.exists() or not bg_csv.exists():
            pytest.skip("Validation data not found — run from project root")
        result = run_retrospective_benchmark(
            amp_csv, bg_csv, benchmark_type="standard"
        )
        assert result["benchmark_type"] == "standard"
        assert 0.0 <= result["auroc"] <= 1.0
        # Gate: AUROC > 0.70 required to proceed to synthesis
        assert result["auroc"] > 0.70, (
            f"AUROC={result['auroc']:.4f}: model does not meet the 0.70 synthesis gate "
            "against background random peptides. Do not proceed to wet-lab synthesis."
        )
        print(f"\n[Standard benchmark] AUROC={result['auroc']:.4f}: {result['interpretation']}")
        print(f"Recall@20={result.get('recall_at_20', 'N/A')}")

    def test_phase3_benchmark_passes_gate(self):
        """Synthesis gate benchmark: phase3.yaml weights must produce AUROC > 0.70.

        phase3.yaml shifts more weight to safety (0.30 vs 0.25) and synthesis (0.20 vs 0.15),
        which down-ranks hemolytic AMPs — correct behaviour for a synthesis gate but lowers raw
        AUROC slightly vs pipeline.yaml. Gate is still AUROC > 0.70 (STRONG).
        Measured: AUROC=0.7936 (95% CI 0.6963-0.8827, n=2000 bootstrap).

        The upper-bound check (< 0.83) is a config-identity sentinel: pipeline.yaml scores
        0.8164 which would breach it, so a silent config fallback is detectable.
        """
        from pathlib import Path
        amp_csv = Path("examples/validation/known_amps.csv")
        bg_csv = Path("examples/validation/random_background.csv")
        phase3_config = Path("configs/phase3.yaml")
        if not amp_csv.exists() or not bg_csv.exists() or not phase3_config.exists():
            pytest.skip("Validation data or phase3 config not found — run from project root")
        result = run_retrospective_benchmark(
            amp_csv, bg_csv, config_path=phase3_config, benchmark_type="standard"
        )
        assert result["benchmark_type"] == "standard"
        assert 0.0 <= result["auroc"] <= 1.0
        # Primary synthesis gate (matches documented threshold in METHODS.md § 8 and retrospective.py)
        assert result["auroc"] > 0.70, (
            f"phase3.yaml AUROC={result['auroc']:.4f}: synthesis gate does not meet the 0.70 "
            "threshold. Do not proceed to wet-lab synthesis."
        )
        # Regression sentinel: measured AUROC=0.7936; alert if it drops below 0.75
        assert result["auroc"] >= 0.75, (
            f"phase3.yaml AUROC={result['auroc']:.4f} < 0.75: a regression has occurred "
            "(baseline 0.7936). Synthesis gate still valid at >0.70 but scoring may be degraded."
        )
        # Config-identity sentinel: pipeline.yaml AUROC=0.8164 > 0.83 would fail this,
        # so a silent config fallback is caught rather than silently passing with the wrong weights.
        assert result["auroc"] < 0.83, (
            f"phase3.yaml AUROC={result['auroc']:.4f} >= 0.83: this is higher than expected "
            "for phase3.yaml (0.7936). Check that phase3.yaml (not pipeline.yaml) was loaded."
        )
        print(f"\n[phase3 benchmark] AUROC={result['auroc']:.4f}: {result['interpretation']}")
        print(f"AUPRC={result.get('auprc', 'N/A')}, Recall@20={result.get('recall_at_20', 'N/A')}")

    def test_strict_benchmark_reports_honestly(self):
        """Secondary (order-sensitivity) benchmark: AMPs vs composition-matched shuffles.

        This tests order-dependent features only (μH). Expected AUROC 0.50-0.65
        for any composition-based scorer. Not a synthesis gate — reported for transparency.
        """
        from pathlib import Path
        amp_csv = Path("examples/validation/known_amps.csv")
        shuffle_csv = Path("examples/validation/scrambled_decoys.csv")
        if not amp_csv.exists() or not shuffle_csv.exists():
            pytest.skip("Validation data not found — run from project root")
        result = run_retrospective_benchmark(
            amp_csv, shuffle_csv, benchmark_type="strict"
        )
        assert result["benchmark_type"] == "strict"
        assert 0.0 <= result["auroc"] <= 1.0
        # Model must at least beat random (not broken)
        assert result["auroc"] > 0.50, (
            f"AUROC={result['auroc']:.4f}: model is BELOW random on composition-matched "
            "shuffles. The hydrophobic moment term may be miscalculated."
        )
        print(f"\n[Strict benchmark] AUROC={result['auroc']:.4f} (expected 0.50-0.65 for composition scorer)")

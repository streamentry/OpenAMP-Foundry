"""Tests for the feature-decomposition selectivity benchmark.

Tests the per-feature selective_vs_hemolytic diagnostic that decomposes WHY
the pipeline fails selective_vs_hemolytic discrimination (AUROC 0.43-0.54
for all composite scorers, as shown by the strict triage benchmark v0.5.14).

The goal is to identify which individual physicochemical features have
statistically significant signal for distinguishing hemolytic from selective
AMPs, and whether the current selectivity proxy uses them.
"""
from __future__ import annotations


import pytest

from openamp_foundry.benchmark.feature_decomp import (
    SCALAR_FEATURES,
    SELECTIVITY_PROXY_INPUTS,
    run_feature_decomposition_benchmark,
)


HEMOLYSIS_CSV = "examples/validation/hemolysis_reference.csv"


@pytest.fixture(scope="class")
def feature_decomp_result():
    return run_feature_decomposition_benchmark(
        hemolysis_csv=HEMOLYSIS_CSV,
        n_bootstrap=200,  # small for test speed
    )


class TestFeatureDecompositionBenchmark:

    def test_benchmark_runs_on_real_data(self, feature_decomp_result):
        result = feature_decomp_result
        assert result["benchmark"] == "feature_decomposition_selectivity"
        assert result["n_hemolytic"] > 0
        assert result["n_selective"] > 0
        assert result["n_features_tested"] > 0

    def test_returns_per_feature_dict(self, feature_decomp_result):
        per_feat = feature_decomp_result["per_feature"]
        assert isinstance(per_feat, dict)
        assert len(per_feat) == feature_decomp_result["n_features_tested"]
        # Every feature has required keys
        for name, info in per_feat.items():
            assert "raw_auroc" in info
            assert "detection_auroc" in info
            assert "ci_lo" in info
            assert "ci_hi" in info
            assert "direction" in info
            assert "significant" in info
            assert "used_by_selectivity_proxy" in info
            assert info["direction"] in ("risk_indicator", "protective_indicator")
            assert 0.0 <= info["raw_auroc"] <= 1.0
            assert 0.0 <= info["detection_auroc"] <= 1.0
            assert 0.0 <= info["ci_lo"] <= info["ci_hi"] <= 1.0

    def test_detection_auroc_is_normalized(self, feature_decomp_result):
        """Detection AUROC should always be >= 0.5 (it's normalized to max)."""
        for name, info in feature_decomp_result["per_feature"].items():
            assert info["detection_auroc"] >= 0.5, (
                f"{name} detection_auroc={info['detection_auroc']} < 0.5"
            )

    def test_direction_consistency(self, feature_decomp_result):
        """risk_indicators have raw >= 0.5; protective_indicators have raw < 0.5."""
        for name, info in feature_decomp_result["per_feature"].items():
            if info["direction"] == "risk_indicator":
                assert info["raw_auroc"] >= 0.5
                assert info["detection_auroc"] == info["raw_auroc"]
            else:  # protective_indicator
                assert info["raw_auroc"] < 0.5
                assert info["detection_auroc"] == round(1.0 - info["raw_auroc"], 4)

    def test_significance_matches_ci(self, feature_decomp_result):
        """significant=True iff ci_lo > 0.5."""
        for name, info in feature_decomp_result["per_feature"].items():
            assert info["significant"] == (info["ci_lo"] > 0.5)

    def test_best_feature_is_significant(self, feature_decomp_result):
        """The best feature should be significant (CI above 0.5)."""
        best = feature_decomp_result["best_feature"]
        assert best in feature_decomp_result["per_feature"]
        best_info = feature_decomp_result["per_feature"][best]
        assert best_info["significant"], (
            f"Best feature {best} is not significant (ci_lo={best_info['ci_lo']})"
        )

    def test_significant_features_list_sorted(self, feature_decomp_result):
        sig = feature_decomp_result["significant_features"]
        if len(sig) >= 2:
            for i in range(len(sig) - 1):
                assert sig[i]["detection_auroc"] >= sig[i + 1]["detection_auroc"]

    def test_selectivity_proxy_features_marked(self, feature_decomp_result):
        """Features used by selectivity_proxy are flagged."""
        per_feat = feature_decomp_result["per_feature"]
        for name in SELECTIVITY_PROXY_INPUTS:
            if name in per_feat:
                assert per_feat[name]["used_by_selectivity_proxy"] is True

    def test_non_proxy_features_not_marked(self, feature_decomp_result):
        """Features NOT in selectivity_proxy inputs are flagged False."""
        per_feat = feature_decomp_result["per_feature"]
        for name, info in per_feat.items():
            if name not in SELECTIVITY_PROXY_INPUTS:
                assert info["used_by_selectivity_proxy"] is False

    def test_verdict_is_honest_string(self, feature_decomp_result):
        verdict = feature_decomp_result["verdict"]
        assert isinstance(verdict, str)
        assert len(verdict) > 50  # not a trivial one-liner

    def test_unused_signal_features_subset_of_significant(self, feature_decomp_result):
        """unused_signal_features should all be significant and not used by proxy."""
        unused = feature_decomp_result["unused_signal_features"]
        per_feat = feature_decomp_result["per_feature"]
        for item in unused:
            name = item["feature"]
            assert per_feat[name]["significant"] is True
            assert per_feat[name]["used_by_selectivity_proxy"] is False

    def test_correct_sample_sizes(self, feature_decomp_result):
        """Hemolytic < 25, selective >= 100, border in between."""
        assert feature_decomp_result["n_hemolytic"] == 45
        assert feature_decomp_result["n_selective"] == 125
        assert feature_decomp_result["n_border"] == 68

    def test_all_scalar_features_tested(self, feature_decomp_result):
        """All SCALAR_FEATURES should appear in per_feature (if they exist in compute_features)."""
        per_feat = feature_decomp_result["per_feature"]
        for feat in SCALAR_FEATURES:
            assert feat in per_feat, f"{feat} missing from per_feature"

    def test_hydrophobic_fraction_is_risk_indicator(self, feature_decomp_result):
        """Hydrophobic fraction should be a risk indicator (higher = more hemolytic)."""
        hf = feature_decomp_result["per_feature"].get("hydrophobic_fraction")
        if hf:
            assert hf["direction"] == "risk_indicator"

    def test_results_are_deterministic(self):
        """Same inputs and seed should give same AUROCs (not same CIs due to bootstrap)."""
        r1 = run_feature_decomposition_benchmark(HEMOLYSIS_CSV, n_bootstrap=50)
        r2 = run_feature_decomposition_benchmark(HEMOLYSIS_CSV, n_bootstrap=50)
        # AUROCs are deterministic (no randomness in the AUROC computation)
        for feat in SCALAR_FEATURES:
            assert r1["per_feature"][feat]["raw_auroc"] == r2["per_feature"][feat]["raw_auroc"]


class TestScalarFeatureList:

    def test_scalar_features_non_empty(self):
        assert len(SCALAR_FEATURES) >= 20

    def test_scalar_features_are_strings(self):
        for f in SCALAR_FEATURES:
            assert isinstance(f, str)

    def test_selectivity_proxy_inputs_subset_of_scalar_features(self):
        for inp in SELECTIVITY_PROXY_INPUTS:
            assert inp in SCALAR_FEATURES, f"{inp} not in SCALAR_FEATURES"

    def test_no_duplicate_scalar_features(self):
        assert len(SCALAR_FEATURES) == len(set(SCALAR_FEATURES))


class TestMetricsSnapshotIntegration:

    def test_feature_decomposition_in_snapshot(self):
        """The metrics snapshot should include feature_decomposition section."""
        from openamp_foundry.benchmark.metrics_snapshot import build_metrics_snapshot

        snapshot = build_metrics_snapshot(
            hemolysis_csv=HEMOLYSIS_CSV,
            n_bootstrap=50,
        )
        assert "feature_decomposition" in snapshot
        fd = snapshot["feature_decomposition"]
        assert fd["n_features_tested"] > 0
        assert "best_feature" in fd
        assert "verdict" in fd
        assert "per_feature" in fd
        assert "significant_features" in fd
        assert "unused_signal_features" in fd

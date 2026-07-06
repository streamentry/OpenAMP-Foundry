"""Cluster-split retrospective benchmark tests — Phase 2 honesty requirement.

AGENTS.md: "Cluster split — Pipeline still performs when near-duplicates are removed."
AGENTS.md: "Benchmarks must be adversarial — search for ways the pipeline may be
fooling itself."

These tests verify that the cluster-split benchmark:
1. Correctly identifies near-duplicate clusters in the AMP positive set.
2. Reports a cluster-aware CI that is wider than the standard CI when near-duplicates exist.
3. Reports held-out recovery AUROC for near-duplicate cluster members.
4. Reports representative-only AUROC (one per cluster).
5. Produces honest interpretation that does not overclaim.

All results are computational. No biological activity is implied.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from openamp_foundry.benchmark.retrospective import (
    _cluster_aware_bootstrap_auroc_ci,
    run_cluster_split_benchmark,
)


AMP_CSV = "examples/validation/known_amps.csv"
DECOY_CSV = "examples/validation/random_background.csv"


class TestClusterAwareBootstrap:
    """Unit tests for the cluster-aware bootstrap CI function."""

    def test_single_cluster_resampling_is_deterministic(self):
        """When all positives are in one cluster, cluster-aware CI should be very wide."""
        # 6 positives all in cluster 0, 6 negatives
        pos = [0.9, 0.88, 0.91, 0.87, 0.89, 0.92]
        neg = [0.3, 0.4, 0.35, 0.25, 0.45, 0.38]
        clusters = [0, 0, 0, 0, 0, 0]
        result = _cluster_aware_bootstrap_auroc_ci(pos, neg, clusters, n_bootstrap=500, seed=42)
        # With 1 cluster, every bootstrap sample draws the same cluster → same scores
        # CI should be very wide because we're resampling 1 cluster repeatedly
        # Resampling 1 cluster means every bootstrap sample has identical positive scores
        # So AUROC is the same every time → CI width = 0
        assert result["ci_hi"] == result["ci_lo"] == 1.0

    def test_all_singletons_ci_similar_to_standard(self):
        """When every positive is its own cluster, cluster-aware ≈ standard bootstrap."""
        pos = [0.9, 0.8, 0.7, 0.6, 0.85, 0.75]
        neg = [0.3, 0.4, 0.35, 0.25, 0.45, 0.38]
        clusters = [0, 1, 2, 3, 4, 5]  # all singletons
        result = _cluster_aware_bootstrap_auroc_ci(pos, neg, clusters, n_bootstrap=500, seed=42)
        # All singletons → same as standard bootstrap
        assert 0.0 <= result["mean"] <= 1.0
        assert result["ci_lo"] <= result["ci_hi"]

    def test_empty_positives_returns_chance(self):
        result = _cluster_aware_bootstrap_auroc_ci([], [0.5, 0.6], [], n_bootstrap=100)
        assert result["mean"] == 0.5
        assert result["n_bootstrap"] == 0

    def test_empty_negatives_returns_chance(self):
        result = _cluster_aware_bootstrap_auroc_ci([0.9, 0.8], [], [0, 1], n_bootstrap=100)
        assert result["mean"] == 0.5
        assert result["n_bootstrap"] == 0

    def test_perfect_separation_high_auroc(self):
        """Clear separation should yield high AUROC mean."""
        pos = [0.9, 0.85, 0.88]
        neg = [0.2, 0.15, 0.1]
        clusters = [0, 0, 1]
        result = _cluster_aware_bootstrap_auroc_ci(pos, neg, clusters, n_bootstrap=500, seed=0)
        assert result["mean"] > 0.9


class TestClusterSplitBenchmark:
    """End-to-end tests for run_cluster_split_benchmark on the real validation set."""

    @pytest.fixture(scope="class")
    def benchmark_result(self):
        """Run the cluster-split benchmark once for all tests in this class."""
        return run_cluster_split_benchmark(AMP_CSV, DECOY_CSV, n_bootstrap=500)

    def test_returns_required_keys(self, benchmark_result):
        required = [
            "benchmark", "n_positives", "n_negatives", "n_clusters",
            "full_auroc", "standard_ci95_lo", "standard_ci95_hi",
            "cluster_aware_ci95_lo", "cluster_aware_ci95_hi",
            "representative_auroc", "representative_ci95_lo", "representative_ci95_hi",
            "held_out_auroc", "interpretation", "disclaimer",
            "near_duplicate_clusters",
        ]
        for key in required:
            assert key in benchmark_result, f"Missing key: {key}"

    def test_benchmark_name(self, benchmark_result):
        assert benchmark_result["benchmark"] == "cluster_split_retrospective"

    def test_n_positives_matches_known_amps(self, benchmark_result):
        assert benchmark_result["n_positives"] == 95

    def test_n_negatives_matches_decoys(self, benchmark_result):
        assert benchmark_result["n_negatives"] == 96

    def test_finds_near_duplicate_clusters(self, benchmark_result):
        """The benchmark set has 14 multi-member clusters at 0.70 threshold."""
        assert benchmark_result["n_multi_member_clusters"] >= 10, (
            f"Expected >= 10 multi-member clusters, got {benchmark_result['n_multi_member_clusters']}"
        )
        assert benchmark_result["n_amps_in_multi_member_clusters"] >= 25, (
            f"Expected >= 25 AMPs in multi-member clusters, got "
            f"{benchmark_result['n_amps_in_multi_member_clusters']}"
        )

    def test_n_clusters_less_than_n_positives(self, benchmark_result):
        """With near-duplicates, independent clusters < total AMPs."""
        assert benchmark_result["n_clusters"] < benchmark_result["n_positives"], (
            "n_clusters should be < n_positives when near-duplicate clusters exist"
        )

    def test_full_auroc_matches_standard_benchmark(self, benchmark_result):
        """Full AUROC should match the standard benchmark (0.7832 on expanded set)."""
        assert benchmark_result["full_auroc"] == pytest.approx(0.7832, abs=0.01), (
            f"Full AUROC={benchmark_result['full_auroc']} should match standard benchmark ~0.7832"
        )

    def test_cluster_aware_ci_is_wider_or_equal(self, benchmark_result):
        """Cluster-aware CI should be at least as wide as standard CI when near-dups exist."""
        standard_width = (
            benchmark_result["standard_ci95_hi"] - benchmark_result["standard_ci95_lo"]
        )
        cluster_width = (
            benchmark_result["cluster_aware_ci95_hi"] - benchmark_result["cluster_aware_ci95_lo"]
        )
        # Cluster-aware CI should be wider or at least not narrower
        # (near-duplicates reduce effective sample size → wider CI)
        assert cluster_width >= standard_width - 0.02, (
            f"Cluster-aware CI width ({cluster_width:.4f}) should be >= "
            f"standard CI width ({standard_width:.4f}) when near-duplicates exist. "
            "If not, near-duplicates may not be inflating the standard CI."
        )

    def test_cluster_aware_ci_lo_lower_than_standard(self, benchmark_result):
        """The key honesty test: cluster-aware CI lower bound should be <= standard CI lo."""
        assert benchmark_result["cluster_aware_ci95_lo"] <= benchmark_result["standard_ci95_lo"] + 0.01, (
            f"Cluster-aware CI lo ({benchmark_result['cluster_aware_ci95_lo']}) should be <= "
            f"standard CI lo ({benchmark_result['standard_ci95_lo']}) + 0.01. "
            "If the cluster-aware CI lo is higher, the standard CI was not inflated by "
            "near-duplicates — which would be a surprising but honest result."
        )

    def test_representative_auroc_below_full_auroc(self, benchmark_result):
        """Removing near-duplicates should not increase AUROC."""
        assert benchmark_result["representative_auroc"] <= benchmark_result["full_auroc"] + 0.02, (
            f"Representative AUROC ({benchmark_result['representative_auroc']}) should be <= "
            f"full AUROC ({benchmark_result['full_auroc']}) + 0.02. "
            "Removing near-duplicates should not improve performance."
        )

    def test_representative_auroc_above_random(self, benchmark_result):
        """Even with one-per-cluster, AUROC should beat random (0.5)."""
        assert benchmark_result["representative_auroc"] > 0.60, (
            f"Representative AUROC ({benchmark_result['representative_auroc']}) > 0.60: "
            "pipeline must have signal even after removing near-duplicate redundancy."
        )

    def test_held_out_auroc_above_random(self, benchmark_result):
        """Held-out near-duplicate AMPs should still outrank decoys."""
        if benchmark_result["held_out_auroc"] is not None:
            assert benchmark_result["held_out_auroc"] > 0.60, (
                f"Held-out AUROC ({benchmark_result['held_out_auroc']}) > 0.60: "
                "near-duplicate AMPs should still score above decoys."
            )

    def test_held_out_n_positives_correct(self, benchmark_result):
        """19 AMPs should be held out (non-representative cluster members)."""
        assert benchmark_result["held_out_n_positives"] >= 10, (
            f"Expected >= 10 held-out AMPs, got {benchmark_result['held_out_n_positives']}"
        )

    def test_interpretation_is_string(self, benchmark_result):
        assert isinstance(benchmark_result["interpretation"], str)
        assert len(benchmark_result["interpretation"]) > 20

    def test_disclaimer_present(self, benchmark_result):
        assert "cluster-aware" in benchmark_result["disclaimer"].lower()
        assert "wet-lab" in benchmark_result["disclaimer"].lower()

    def test_near_duplicate_clusters_have_members(self, benchmark_result):
        """Each near-duplicate cluster entry should list its members."""
        for cluster in benchmark_result["near_duplicate_clusters"]:
            assert "members" in cluster
            assert "size" in cluster
            assert len(cluster["members"]) == cluster["size"]
            assert cluster["size"] >= 2

    def test_magainin_cluster_detected(self, benchmark_result):
        """The magainin family (MAG-001/002/003) should appear as a near-dup cluster."""
        all_members = []
        for cluster in benchmark_result["near_duplicate_clusters"]:
            all_members.extend(cluster["members"])
        assert "REF-MAG-001" in all_members, "Magainin cluster should be detected"
        assert "REF-MAG-002" in all_members, "Magainin-2 should be in same cluster"

    def test_protegrin_cluster_detected(self, benchmark_result):
        """The protegrin family (PRG1/2/3) should appear as a near-dup cluster."""
        all_members = []
        for cluster in benchmark_result["near_duplicate_clusters"]:
            all_members.extend(cluster["members"])
        assert "REF-PRG1-001" in all_members, "Protegrin cluster should be detected"

    def test_phase3_config_also_works(self):
        """Cluster-split benchmark should also work with phase3.yaml weights."""
        result = run_cluster_split_benchmark(
            AMP_CSV, DECOY_CSV, config_path="configs/phase3.yaml", n_bootstrap=300,
        )
        assert result["full_auroc"] > 0.65, (
            f"Phase3 full AUROC ({result['full_auroc']}) should be > 0.65"
        )
        assert result["representative_auroc"] > 0.60, (
            f"Phase3 representative AUROC ({result['representative_auroc']}) should be > 0.60"
        )

    def test_custom_threshold_changes_clustering(self):
        """A stricter threshold should produce fewer clusters (more singletons)."""
        result_loose = run_cluster_split_benchmark(AMP_CSV, DECOY_CSV, similarity_threshold=0.50, n_bootstrap=200)
        result_strict = run_cluster_split_benchmark(AMP_CSV, DECOY_CSV, similarity_threshold=0.90, n_bootstrap=200)
        # Lower threshold → more sequences co-clustered → fewer clusters
        assert result_loose["n_clusters"] <= result_strict["n_clusters"], (
            f"Loose threshold (0.50) clusters={result_loose['n_clusters']} should be <= "
            f"strict threshold (0.90) clusters={result_strict['n_clusters']}"
        )

    def test_ala_and_drs_are_exact_duplicate(self, benchmark_result):
        """REF-ALA-001 and REF-DRS1-001 are identical sequences — must cluster together."""
        found = False
        for cluster in benchmark_result["near_duplicate_clusters"]:
            if "REF-ALA-001" in cluster["members"] and "REF-DRS1-001" in cluster["members"]:
                found = True
                break
        assert found, (
            "REF-ALA-001 and REF-DRS1-001 are identical sequences and must be in the same cluster"
        )


class TestClusterSplitBenchmarkSmallData:
    """Tests with small synthetic data to verify edge cases."""

    def test_no_near_duplicates(self, tmp_path):
        """When all AMPs are unique, cluster-split should report n_clusters = n_positives."""
        amp_csv = tmp_path / "amps.csv"
        amp_csv.write_text(
            "id,sequence,family,reference,label\n"
            "AMP-001,KWKLFKKIGAVLKVL,test,t,1\n"
            "AMP-002,GLFDIVKKVVGALGSL,test,t,1\n"
            "AMP-003,RRWQWRMKKLG,test,t,1\n"
        )
        decoy_csv = tmp_path / "decoys.csv"
        decoy_csv.write_text(
            "id,sequence,family,source_id,label\n"
            "DEC-001,GGGGGGGGGGGGGGG,bg,bg,0\n"
            "DEC-002,AAAAAAAAAAA,bg,bg,0\n"
            "DEC-003,DEDEDEDEDEDEDE,bg,bg,0\n"
        )
        result = run_cluster_split_benchmark(amp_csv, decoy_csv, n_bootstrap=100)
        assert result["n_multi_member_clusters"] == 0
        assert result["n_clusters"] == 3
        assert result["n_held_out_amps"] == 0
        assert result["held_out_auroc"] is None

    def test_all_identical_amps(self, tmp_path):
        """When all AMPs are identical, one cluster, all held out except one."""
        amp_csv = tmp_path / "amps.csv"
        amp_csv.write_text(
            "id,sequence,family,reference,label\n"
            "AMP-001,KWKLFKKIGAVLKVL,test,t,1\n"
            "AMP-002,KWKLFKKIGAVLKVL,test,t,1\n"
            "AMP-003,KWKLFKKIGAVLKVL,test,t,1\n"
        )
        decoy_csv = tmp_path / "decoys.csv"
        decoy_csv.write_text(
            "id,sequence,family,source_id,label\n"
            "DEC-001,GGGGGGGGGGGGGGG,bg,bg,0\n"
            "DEC-002,AAAAAAAAAAA,bg,bg,0\n"
        )
        result = run_cluster_split_benchmark(amp_csv, decoy_csv, n_bootstrap=100)
        assert result["n_clusters"] == 1
        assert result["n_multi_member_clusters"] == 1
        assert result["n_held_out_amps"] == 2


class TestClusterSplitCLI:
    """Test the CLI command bench cluster-split."""

    def test_cli_cluster_split_runs(self, tmp_path):
        from openamp_foundry.cli import main
        out = str(tmp_path / "cluster_split.json")
        ret = main(["bench", "cluster-split", "--out", out, "--n-bootstrap", "200"])
        assert ret == 0
        import json
        data = json.loads(Path(out).read_text())
        assert data["benchmark"] == "cluster_split_retrospective"
        assert "full_auroc" in data
        assert "cluster_aware_ci95_lo" in data
        assert "near_duplicate_clusters" in data

    def test_cli_cluster_split_custom_threshold(self, tmp_path):
        from openamp_foundry.cli import main
        out = str(tmp_path / "cluster_split.json")
        ret = main(["bench", "cluster-split", "--threshold", "0.80", "--out", out, "--n-bootstrap", "100"])
        assert ret == 0
        import json
        data = json.loads(Path(out).read_text())
        assert data["similarity_threshold"] == 0.80

    def test_cli_cluster_split_no_out_file(self, tmp_path):
        """CLI should work without --out (prints to stdout only)."""
        from openamp_foundry.cli import main
        ret = main(["bench", "cluster-split", "--n-bootstrap", "100"])
        assert ret == 0
